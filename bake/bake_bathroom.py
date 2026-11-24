"""Bake bathroom lighting for the web 3D view (prototype).

Run:  blender -b --factory-startup -P bake/bake_bathroom.py -- <in.glb> <out_dir> [size] [samples]
In:   bathroom_src.glb exported from plan3d.html (meshes named/materials named b0..bN, world coordinates).
Out:  <out_dir>/bathroom_baked.glb  (same meshes + 2nd UV set "lm")
      <out_dir>/lightmap.hdr        (irradiance only: light + shadows, no surface colour)
Coordinates: the glTF importer turns three.js (x, up, z) into Blender (x, -z, up).
"""
import sys, time, bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
SIZE = int(argv[2]) if len(argv) > 2 else 2048
SAMPLES = int(argv[3]) if len(argv) > 3 else 256
CEIL = 2.70
t0 = time.time()

# --- scene --------------------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
print(f"[bake] imported {len(meshes)} meshes")

bpy.ops.object.select_all(action="DESELECT")
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = "bathroom"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def b(x, plan_y, z):            # plan metres (x east, y south) + height -> Blender coords
    return (x, -plan_y, z)

# ceiling over the bathroom (not exported; only bounces light and blocks the "sky")
bpy.ops.mesh.primitive_plane_add(size=1, location=b(5.17, 6.74, CEIL))
ceil = bpy.context.active_object; ceil.scale = (2.8, 2.5, 1)
cm = bpy.data.materials.new("ceiling"); cm.use_nodes = True
cm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.85, 0.84, 0.82, 1)
ceil.data.materials.append(cm)

# lights: three warm recessed downlights + the LED strip in the vanity plinth
def warm(w, rgb=(1.0, 0.80, 0.60)):
    return w, rgb
for (lx, ly) in [(4.32, 6.25), (5.15, 6.95), (6.09, 6.40)]:
    ld = bpy.data.lights.new("downlight", type="SPOT")
    ld.energy, ld.color = warm(45)
    ld.spot_size = 2.1; ld.spot_blend = 0.6; ld.shadow_soft_size = 0.04
    lo = bpy.data.objects.new("downlight", ld); lo.location = b(lx, ly, CEIL - 0.03)
    bpy.context.collection.objects.link(lo)                       # spot points straight down by default
la = bpy.data.lights.new("vanity_led", type="AREA"); la.energy, la.color = warm(6, (1.0, 0.72, 0.45))
la.shape = "RECTANGLE"; la.size = 0.82; la.size_y = 0.02
lo = bpy.data.objects.new("vanity_led", la); lo.location = b(4.32, 6.005, 0.015)
lo.rotation_euler = (3.14159, 0, 0)                              # facing down onto the floor
bpy.context.collection.objects.link(lo)

world = bpy.data.worlds.new("world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.03, 0.03, 1)
bpy.context.scene.world = world

# --- lightmap UVs -----------------------------------------------------------------------------------
me = obj.data
base_uv = me.uv_layers[0].name
lm = me.uv_layers.new(name="lm")
me.uv_layers.active = lm
bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
# island-based layout: every flat face of a box / wall panel stays one connected island (lightmap_pack would
# split each triangle separately -> checkerboard + wasted space)
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.003, rotate=True)
bpy.ops.object.mode_set(mode="OBJECT")
me.uv_layers[base_uv].active_render = True
print(f"[bake] lightmap UVs ready ({time.time() - t0:.1f}s)")

# --- bake target ----------------------------------------------------------------------------------
img = bpy.data.images.new("lightmap", SIZE, SIZE, float_buffer=True)
for mat in me.materials:
    mat.use_nodes = True
    nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    uv = nt.nodes.new("ShaderNodeUVMap"); uv.uv_map = "lm"
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    nt.nodes.active = tex

# --- render settings (GPU if available) --------------------------------------------------------------------
sc = bpy.context.scene
sc.render.engine = "CYCLES"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind; prefs.get_devices()
            if any(d.type == kind for d in prefs.devices):
                for d in prefs.devices: d.use = d.type == kind
                sc.cycles.device = "GPU"; print(f"[bake] using {kind}"); break
        except Exception as e:
            print(f"[bake] {kind} unavailable: {e}")
except Exception as e:
    print(f"[bake] GPU setup failed, CPU: {e}")
sc.cycles.samples = SAMPLES
sc.render.bake.use_pass_direct = True
sc.render.bake.use_pass_indirect = True
sc.render.bake.use_pass_color = False
sc.render.bake.margin = 6

bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); bpy.context.view_layer.objects.active = obj
print(f"[bake] baking {SIZE}px, {SAMPLES} samples …")
bpy.ops.object.bake(type="DIFFUSE")
print(f"[bake] baked ({time.time() - t0:.1f}s)")

img.filepath_raw = OUT + "/lightmap.hdr"; img.file_format = "HDR"; img.save()

# --- export the meshes with both UV sets -------------------------------------------------------------
for mat in me.materials:                                         # remove the helper nodes before export
    nt = mat.node_tree
    for n in [n for n in nt.nodes if n.type in ("TEX_IMAGE", "UVMAP")]: nt.nodes.remove(n)
bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT + "/bathroom_baked.glb", export_format="GLB", use_selection=True,
                          export_texcoords=True, export_normals=True, export_materials="EXPORT", export_apply=True)
print(f"[bake] done in {time.time() - t0:.1f}s")
