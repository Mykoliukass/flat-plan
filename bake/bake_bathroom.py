"""Make the bathroom in the web 3D view more realistic with Blender (prototype, v2).

Run:  blender -b --factory-startup -P bake/bake_bathroom.py -- <in.glb> <out_dir> [lightmap_size] [samples]
In:   bathroom_src.glb exported from plan3d.html: meshes with materials b0..bN (world coords), node extras {label, plane}.
Out:  <out_dir>/bathroom_baked.glb  meshes with a 2nd UV set (lightmap). Replaced objects keep the material name
                                   of what they replace (so the web re-uses its live textures); props use x_* materials.
      <out_dir>/lightmap.hdr        baked light (irradiance only)
      <out_dir>/probe.hdr           360° reflection probe rendered from the middle of the bathroom
Steps: 1) real fixture shapes (bath, wall-hung WC, basin carved into the stone top)  2) soft bevelled edges
       3) props (towels, bottles, vase)  4) lights + lightmap bake  5) reflection probe.
Coordinates: Blender (x, y, z) = three.js (x, -z, y) = plan (x, -plan_y, height).
"""
import sys, time, math, bpy, bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
SIZE = int(argv[2]) if len(argv) > 2 else 2048
SAMPLES = int(argv[3]) if len(argv) > 3 else 384
CEIL = 2.70
t0 = time.time()
log = lambda *a: print("[bake]", *a, f"({time.time() - t0:.1f}s)")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
col = bpy.context.scene.collection
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
log(f"imported {len(meshes)} meshes")

# ---------------------------------------------------------------- helpers
def label(o): return str(o.get("label", ""))
def find(pred): return [o for o in bpy.context.scene.objects if o.type == "MESH" and pred(label(o))]
def bbox(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return Vector((min(v.x for v in ws), min(v.y for v in ws), min(v.z for v in ws))), \
           Vector((max(v.x for v in ws), max(v.y for v in ws), max(v.z for v in ws)))
def mat_of(o): return o.data.materials[0] if o.data.materials else None
def remove(o): bpy.data.objects.remove(o, do_unlink=True)

def box_uv(bm, lo, hi):
    """UV0: per face, planar projection on the dominant axis, normalised to the object's size (matches the web's
    0..1-per-face box UVs, so the live texture repeat stays right)."""
    uvl = bm.loops.layers.uv.verify(); d = hi - lo
    for f in bm.faces:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            c = l.vert.co - lo
            if ax == 2: u, v = c.x / max(d.x, 1e-4), c.y / max(d.y, 1e-4)
            elif ax == 0: u, v = c.y / max(d.y, 1e-4), c.z / max(d.z, 1e-4)
            else: u, v = c.x / max(d.x, 1e-4), c.z / max(d.z, 1e-4)
            l[uvl].uv = (u, v)

def finish_obj(name, bm, mat, lo, hi, smooth_angle=40):
    box_uv(bm, lo, hi)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.uv_layers[0].name = "UVMap"
    for p in me.polygons: p.use_smooth = True
    try: me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    except Exception: pass
    if mat: me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); col.objects.link(ob)
    return ob

def rbox(name, lo, hi, r, seg, mat, taper=None):
    """rounded box between corners lo/hi; taper(v) may move verts after bevelling"""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((lo.x + (v.co.x + 0.5) * (hi.x - lo.x), lo.y + (v.co.y + 0.5) * (hi.y - lo.y), lo.z + (v.co.z + 0.5) * (hi.z - lo.z)))
    if r > 0:
        bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=r, offset_type="OFFSET", segments=seg,
                        profile=0.5, affect="EDGES", clamp_overlap=True)
    if taper:
        for v in bm.verts: taper(v)
    bm.normal_update()
    return finish_obj(name, bm, mat, lo, hi)

def cylinder(name, x, y, z0, z1, r, mat, seg=32):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=z1 - z0)
    for v in bm.verts: v.co += Vector((x, y, (z0 + z1) / 2))
    return finish_obj(name, bm, mat, Vector((x - r, y - r, z0)), Vector((x + r, y + r, z1)), 30)

def carve(target, cutter):
    m = target.modifiers.new("cut", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = cutter; m.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=m.name)
    remove(cutter)

def new_mat(name, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

# ---------------------------------------------------------------- 1) real fixtures
# Bathtub: rounded ceramic tub with a deep sloped basin + thin tiled front panel (replaces rim box, inner plate, apron box)
rims = find(lambda l: l == "bath 180×80"); apron = find(lambda l: l == "bath, front panel tiled")
if rims and apron:
    rims.sort(key=lambda o: bbox(o)[0].z)
    rim, inner = rims[0], rims[1:]
    lo, hi = bbox(rim); alo, ahi = bbox(apron[0])
    tub_mat, apron_mat = mat_of(rim), mat_of(apron[0])
    # tub body sits just behind the tiled front panel (no overlapping faces), a ceramic lip covers the panel top
    tub = rbox("tub", Vector((lo.x + 0.024, lo.y, 0.30)), Vector((hi.x, hi.y, 0.585)), 0.012, 3, tub_mat)
    cut = rbox("tubcut", Vector((lo.x + 0.085, lo.y + 0.085, 0.345)), Vector((hi.x - 0.06, hi.y - 0.085, 0.80)), 0.13, 8, None)
    carve(tub, cut)
    rbox("apron", Vector((alo.x, alo.y, 0.0)), Vector((alo.x + 0.022, ahi.y, 0.562)), 0.003, 2, apron_mat)   # tiled front only
    rbox("tub_lip", Vector((lo.x - 0.006, lo.y, 0.562)), Vector((lo.x + 0.03, hi.y, 0.585)), 0.008, 3, tub_mat)
    for o in rims + apron: remove(o)
    log("bath rebuilt")

# Wall-hung toilet: rounded bowl tapering to the front + seat (replaces two boxes)
bowl = find(lambda l: l == "wall-hung WC"); seat = find(lambda l: l.startswith("WC seat"))
if bowl and seat:
    lo, hi = bbox(bowl[0]); slo, shi = bbox(seat[0]); cx = (lo.x + hi.x) / 2
    front = hi.y                                                        # front = towards the room (larger Blender y)
    def taper(v, lo=lo, hi=hi, cx=cx):
        t = max(0.0, min(1.0, (v.co.y - lo.y) / (hi.y - lo.y)))
        v.co.x = cx + (v.co.x - cx) * (1 - 0.28 * t ** 1.6)
        if v.co.z < lo.z + 0.05: v.co.y = lo.y + (v.co.y - lo.y) * 0.88    # slightly undercut bottom
    rbox("wc_bowl", Vector((lo.x, lo.y, 0.27)), Vector((hi.x, front, 0.425)), 0.07, 6, mat_of(bowl[0]), taper)
    rbox("wc_seat", Vector((lo.x + 0.005, lo.y + 0.04, 0.425)), Vector((hi.x - 0.005, front + 0.005, 0.447)), 0.010, 3,
         mat_of(seat[0]), taper)
    for o in bowl + seat: remove(o)
    log("toilet rebuilt")

# Stone top with the basin carved in + drain (replaces top slab, basin plate, drain disc)
top = find(lambda l: "stone top" in l); basin = find(lambda l: l == "integrated basin"); drain = find(lambda l: l == "drain")
if top and basin:
    lo, hi = bbox(top[0]); blo, bhi = bbox(basin[0]); tz = hi.z
    newtop = rbox("stone_top", lo, hi, 0.004, 2, mat_of(top[0]))
    cut = rbox("basincut", Vector((blo.x, blo.y, tz - 0.115)), Vector((bhi.x, bhi.y, tz + 0.2)), 0.045, 8, None)
    carve(newtop, cut)
    if drain:
        dlo, dhi = bbox(drain[0])
        cylinder("drain", (dlo.x + dhi.x) / 2, (dlo.y + dhi.y) / 2, tz - 0.116, tz - 0.112, 0.021, mat_of(drain[0]))
    for o in top + basin + drain: remove(o)
    log("basin carved")

# ---------------------------------------------------------------- 2) soft bevelled edges on every remaining box
n_bev = 0
for o in [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.get("plane") and o.name not in
          ("tub", "tub_lip", "apron", "wc_bowl", "wc_seat", "stone_top", "drain")]:
    me = o.data
    if len(me.vertices) != 24: continue                                # only simple boxes
    lo, hi = bbox(o); dmin = min(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
    r = min(0.005, dmin * 0.3)
    if r < 0.0015: continue
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=r, offset_type="OFFSET", segments=2,
                    profile=0.5, affect="EDGES", clamp_overlap=True)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    try: me.set_sharp_from_angle(angle=math.radians(40))
    except Exception: pass
    n_bev += 1
log(f"bevelled {n_bev} boxes")

# ---------------------------------------------------------------- 3) props
rail = find(lambda l: l.startswith("heated towel rail"))
if rail:
    los = [bbox(o)[0] for o in rail]; his = [bbox(o)[1] for o in rail]
    rx0, rx1 = min(v.x for v in los), max(v.x for v in his)
    ry_front = min(v.y for v in los)                                    # room side of the rail (Blender y smaller)
    cream = new_mat("x_towel_cream", (0.80, 0.76, 0.68), 0.95)
    rbox("towel_front", Vector((rx0 + 0.05, ry_front - 0.035, 0.78)), Vector((rx1 - 0.05, ry_front - 0.012, 1.31)), 0.010, 4, cream)
    rbox("towel_fold", Vector((rx0 + 0.05, ry_front - 0.035, 1.29)), Vector((rx1 - 0.05, ry_front + 0.06, 1.335)), 0.016, 4, cream)
if top:
    amber = new_mat("x_amber_glass", (0.32, 0.10, 0.02), 0.12)
    black = new_mat("x_pump_black", (0.02, 0.02, 0.02), 0.4)
    vase = new_mat("x_vase_clay", (0.62, 0.55, 0.47), 0.85)
    lo, hi = bbox(newtop); tz = hi.z
    bx, by = hi.x - 0.09, hi.y - 0.07
    cylinder("bottle1", bx, by, tz, tz + 0.17, 0.031, amber); cylinder("pump1", bx, by, tz + 0.17, tz + 0.215, 0.009, black)
    cylinder("bottle2", bx - 0.075, by + 0.005, tz, tz + 0.14, 0.027, amber); cylinder("pump2", bx - 0.075, by + 0.005, tz + 0.14, tz + 0.18, 0.008, black)
    cylinder("vase", lo.x + 0.11, hi.y - 0.07, tz, tz + 0.12, 0.045, vase, 40)
log("props added")

# ---------------------------------------------------------------- 4) lights, ceiling, lightmap bake
def b(x, plan_y, z): return (x, -plan_y, z)
bpy.ops.mesh.primitive_plane_add(size=1, location=b(5.17, 6.74, CEIL))
ceil = bpy.context.active_object; ceil.scale = (2.8, 2.5, 1)
ceil.data.materials.append(new_mat("ceiling", (0.85, 0.84, 0.82), 0.9))
for (lx, ly) in [(4.32, 6.25), (5.15, 6.95), (6.09, 6.40)]:
    ld = bpy.data.lights.new("downlight", type="SPOT"); ld.energy = 55; ld.color = (1.0, 0.80, 0.60)
    ld.spot_size = 2.0; ld.spot_blend = 0.55; ld.shadow_soft_size = 0.03
    lo_ = bpy.data.objects.new("downlight", ld); lo_.location = b(lx, ly, CEIL - 0.03); col.objects.link(lo_)
la = bpy.data.lights.new("vanity_led", type="AREA"); la.energy = 8; la.color = (1.0, 0.72, 0.45)
la.shape = "RECTANGLE"; la.size = 0.82; la.size_y = 0.02
lo_ = bpy.data.objects.new("vanity_led", la); lo_.location = b(4.32, 6.005, 0.015); lo_.rotation_euler = (math.pi, 0, 0)
col.objects.link(lo_)
world = bpy.data.worlds.new("world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.025, 0.025, 0.025, 1)
bpy.context.scene.world = world

parts = [o for o in bpy.context.scene.objects if o.type == "MESH" and o is not ceil]
bpy.ops.object.select_all(action="DESELECT")
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active; obj.name = "bathroom"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = obj.data
base_uv = me.uv_layers[0].name
lm = me.uv_layers.new(name="lm"); me.uv_layers.active = lm
bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.002, rotate=True)
bpy.ops.object.mode_set(mode="OBJECT")
me.uv_layers[base_uv].active_render = True
log("lightmap UVs ready")

img = bpy.data.images.new("lightmap", SIZE, SIZE, float_buffer=True)
empty = [i for i, m in enumerate(me.materials) if m is None]
if empty:                                                       # faces without a material can't be baked: give them one
    fallback = new_mat("x_fallback", (0.7, 0.7, 0.7), 0.8)
    for i in empty: me.materials[i] = fallback
    log(f"{len(empty)} empty material slot(s) filled")
for mat in me.materials:
    mat.use_nodes = True; nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    uv = nt.nodes.new("ShaderNodeUVMap"); uv.uv_map = "lm"
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"]); nt.nodes.active = tex

sc = bpy.context.scene; sc.render.engine = "CYCLES"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind; prefs.get_devices()
            if any(d.type == kind for d in prefs.devices):
                for d in prefs.devices: d.use = d.type == kind
                sc.cycles.device = "GPU"; log(f"using {kind}"); break
        except Exception as e: log(f"{kind} unavailable: {e}")
except Exception as e: log(f"GPU setup failed: {e}")
sc.cycles.samples = SAMPLES
sc.render.bake.use_pass_direct = True; sc.render.bake.use_pass_indirect = True; sc.render.bake.use_pass_color = False
sc.render.bake.margin = 6
bpy.ops.object.bake(type="DIFFUSE")
img.filepath_raw = OUT + "/lightmap.hdr"; img.file_format = "HDR"; img.save()
log(f"lightmap baked ({SIZE}px, {SAMPLES} samples)")

# ---------------------------------------------------------------- 5) 360° reflection probe from the middle of the room
cam_data = bpy.data.cameras.new("probe"); cam_data.type = "PANO"
try: cam_data.panorama_type = "EQUIRECTANGULAR"
except Exception: cam_data.cycles.panorama_type = "EQUIRECTANGULAR"
cam = bpy.data.objects.new("probe", cam_data); col.objects.link(cam)
cam.location = b(5.10, 6.70, 1.35)
cam.rotation_euler = (math.pi / 2, 0, -math.pi / 2)      # image centre = +X, like three.js equirect maps
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1536, 768, 100
sc.cycles.samples = 160; sc.cycles.use_denoising = True
sc.render.image_settings.file_format = "HDR"
sc.render.filepath = OUT + "/probe.hdr"
bpy.ops.render.render(write_still=True)
log("reflection probe rendered")

# ---------------------------------------------------------------- export
for mat in me.materials:
    nt = mat.node_tree
    for n in [n for n in nt.nodes if n.type in ("TEX_IMAGE", "UVMAP")]: nt.nodes.remove(n)
bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT + "/bathroom_baked.glb", export_format="GLB", use_selection=True,
                          export_texcoords=True, export_normals=True, export_materials="EXPORT", export_apply=True)
log("done")
