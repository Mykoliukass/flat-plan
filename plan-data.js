/* Shared plan data for plan.html (2D) and plan3d.html (3D). All units metres.
   Origin = inner top-left corner of room 60-1; x → east, y → south. */
window.PLAN = {
  balcony: { x:-0.16, y:-1.90, w:7.13, h:1.40, label:"Balcony 7.13 × 1.40" },

  // ===== GEOMETRY FROM ON-SITE MEASUREMENTS (2026-11-22). Codes refer to measure.html. =====
  // Interior faces: partition 3.72|3.85 (L1, 0.13 thick) · east wall 6.49 (R1/B1) · bedroom|bath wall 5.45|5.59 (R2)
  //                 shaft face 7.395 (B2) · corridor wall 7.88 (B3; derived L3) · kitchen wall 6.005 (L2)
  // Ceiling 2.70 everywhere (Z1–Z4, provisional). Doorways 2.115 high (Z12). Windows/balcony door go down to the floor.
  heights: { ceiling:2.70, doorway:2.115, windowTop:2.335 },   // windowTop measured on the east window (Z10), assumed for all

  // Solid walls: rectangles [x, y, w, h]
  walls: [
    // outer (north) facade wall, 0.50 thick, with openings left out
    [-0.42,-0.50, 1.325,0.50],  // pier left of balcony glazing (O1 = 0.905)
    [ 3.105,-0.50, 1.59,0.50],  // pier between balcony glazing and bedroom window (O4 0.615 + partition + R3 0.845)
    [ 5.905,-0.50, 1.085,0.50], // NE corner pier
    [ 6.49, 0.00, 0.50,0.99],   // east wall north of bedroom side window (R5 = 0.99)
    [ 6.49, 2.19, 0.50,5.89],   // east wall south of window (R6 = 1.20) down to corridor
    // west wall (party wall)
    [-0.23, 0.00, 0.23,7.88],
    // south wall to stair corridor, 0.20 thick (entrance opening 2.35–3.40: O5 0.32, O6 1.05)
    [-0.23, 7.88, 2.58,0.20],
    [ 3.40, 7.88, 3.59,0.20],
    // partition living | bedroom & bath, 0.13 thick, doorways left out (O7/O8, O9/O10)
    [ 3.72, 0.00, 0.13,3.005],
    [ 3.72, 3.905,0.13,2.275],
    [ 3.72, 7.08, 0.13,0.80],
    // bedroom | bathroom
    [ 3.85, 5.45, 2.64,0.14],
    // living room south (kitchen) wall + short return stub (L4 2.095, L5 0.635)
    [ 0.00, 6.005,2.225,0.13],
    [ 2.095,5.37, 0.13,0.765],
    // hall west side: wall in front of the narrow shaft (H1 → face at 0.24, H3 1.035)
    [ 0.13, 6.135,0.11,1.035],
    // big shaft box walls (H4 0.81 → right face 1.05, front face 7.17; depth derived 0.71)
    [ 0.91, 7.17, 0.14,0.71],
    [ 0.00, 7.17, 0.91,0.14],
  ],

  // Ventilation / service shafts (not usable): polygons
  shafts: [
    [[0,6.16],[0.13,6.16],[0.13,7.15],[0,7.15]],
    [[0,7.31],[0.91,7.31],[0.91,7.88],[0,7.88]],
    // bathroom shaft: recess 4.87–5.42 × 12.5 cm deep (B4/B5/B6), front face 5.42–6.49 (B7)
    [[4.87,7.88],[4.87,7.52],[5.42,7.52],[5.42,7.395],[6.49,7.395],[6.49,7.88]],
  ],

  // Windows / glazed doors: [x1,y1,x2,y2,wallThickness,label] — all go down to the floor
  windows: [
    [0.905,-0.25, 3.105,-0.25, 0.50, "balcony door + window 2.20", { split:2.055, transom:1.05 }],   // photo: left = fixed glass with cross bar ~1.05 m, right = door ~1.05 wide
    [4.695,-0.25, 5.905,-0.25, 0.50, "window 1.21", { transom:1.05 }],   // bedroom north: same cross bar as the balcony glazing (owner)
    [6.74, 0.99, 6.74, 2.19, 0.50, "window 1.20", { transom:1.05 }],       // bedroom east: same cross bar (owner)
  ],

  // Wall openings WITHOUT a door leaf (currently no interior doors): [x1,y1,x2,y2,label]
  openings: [
    [3.785,3.005, 3.785,3.905, "0.90"],
    [3.785,6.18,  3.785,7.08,  "0.90"],
  ],

  // Hinged doors: hinge point, leaf length, closed-leaf direction & swing direction (deg, 0=east, 90=south)
  // Both open INTO the flat. Hinge side is an assumption — flip `hinge`/`closed` to mirror.
  doorLeaves: [
    { name:"entrance",     hinge:[3.40,7.88], len:1.05, closed:180, open:270 }, // opens north into hall
    { name:"balcony door", hinge:[3.105,0.00], len:1.05, closed:180, open: 90 }, // RIGHT part of the glazing, hinged at the right, opens inward; ~1.05 wide (from photo)
  ],

  // Recuperation (MVHR) duct along the bedroom east wall just under the ceiling (owner, 2026-11-22):
  // Ø ~15 cm, 1–2 cm off the wall, bottom at 2.44 (balcony end) → 2.47 (bathroom end).
  pipes: [
    { x1:6.40, y1:0.00, x2:6.40, y2:5.45, zBottom1:2.44, zBottom2:2.47, d:0.15, label:"recuperation duct Ø15 (bottom 244→247 cm)" },
  ],

  // Existing service points (marked by owner on site)
  services: [
    { x:5.145,y:7.40, label:"WC drain", kind:"wcDrain" },        // in the shaft recess; exact spot flexible (owner)
    { x:1.25, y:5.93, label:"Kitchen drain + water", kind:"kitchen" },   // photo: hot+cold+drain from the floor ~1.1–1.4 m from the west wall (confirm K1)
    { x:1.37, y:7.75, label:"Heating & electricity boxes", kind:"boxes" },
  ],

  // Electrical points seen in site photos (2026-11-22). Positions/heights are ESTIMATES from photos (±20 cm) —
  // confirm with measure.html codes E1–E9. wall: "W" = west concrete wall (x=0), "E" = bedroom east wall (x=6.49),
  // "P" = partition living/hall side (x=3.72), "C" = ceiling. z = height of box centre above floor.
  electrical: [
    { id:"E1", wall:"W", x:0.00, y:5.30, z:1.70, label:"wall box, upper (kitchen corner)" },
    { id:"E2", wall:"W", x:0.00, y:5.30, z:0.45, label:"wall box, low (kitchen corner)" },
    { id:"E3", wall:"W", x:0.00, y:4.80, z:0.50, label:"wall box, low" },
    { id:"E4", wall:"W", x:0.00, y:3.00, z:0.35, label:"wall box, low (living room)" },
    { id:"E5", wall:"W", x:0.00, y:0.70, z:2.25, label:"red junction boxes, high" },
    { id:"E6", wall:"C", x:0.10, y:0.10, z:2.70, label:"balcony cable (coiled at ceiling)" },
    { id:"E7", wall:"E", x:6.49, y:3.30, z:1.00, label:"3-box group (sockets/switches?)", n:3 },
    { id:"E8", wall:"P", x:3.72, y:5.30, z:1.00, label:"filled patch — hidden box? (check)" },
    { id:"E9", wall:"C", x:2.90, y:7.30, z:2.70, label:"hall ceiling light point" },
  ],

  // Notes: floor heating throughout (no radiators to plan around). Screed + heating pipes ARE ALREADY LAID (owner, 2026-11-22):
  //        all heights were measured from this floor; only the floor finish (~1–2 cm tiles/laminate) will still be added.
  //        → never drill into the floor without locating the heating pipes first (WC frame feet, door stops, anything bolted down).
  //        Hot water from the building (district heating); water meters are in the stair corridor — no access hatch needed in the flat.
  //        Heated towel rail: electric, hard-wired (no socket), switch/timer outside zone 2 (>0.6 m from bath).
  // Points you mark with the "Mark" tool are stored here (paste them back to Claude):
  marks: [],

  /* Design options. Each layout is a list of items {k:kind, x,y,w,h (m), label}
     kinds: wc, basin, shower, bath, washer, box (cabinet/boxing), glass (line x,y→x2,y2), slider */
  layouts: {
    bathroom: {
      "C — bath on east wall (current proposal)": [
        // Measured: alcove 180.5 (181 at floor) bedroom wall → shaft face (B2). Bath 180×80 fits with ~5 mm to spare.
        { k:"bath",   x:5.69, y:5.59, w:0.80, h:1.805, label:"bath 180×80" },
        { k:"glass",  x:5.69, y:6.595, x2:5.69, y2:7.395 },                        // fixed screen at shower end (no swing)
        { k:"note",   x:6.09, y:7.20, label:"mixer + shower" },
        // ONE FLUSH BACK WALL at y = 7.395 (the shaft's own front face, where the bath ends).
        // Everything is built back to that plane — nothing projects except the washer/dryer.
        // z0/z1 = bottom/top height above floor (m), used by the 3D view; z1:"ceiling" = full height (owner: walnut runs to the ceiling)
        // WC frame sits in the 12.5 cm × 55 cm recess of the shaft (x 4.87–5.42) → needs a slim 8 cm concealed cistern
        { k:"box",    x:4.87, y:7.395,w:0.55, h:0.125,z0:0,    z1:1.20, label:"", role:"frame" },
        { k:"wc",     x:4.965,y:6.875,w:0.36, h:0.52, label:"wall-hung WC" },
        // cabinet in the same recess, above the cistern, flush with the wall (12.5 cm deep)
        { k:"upper",  x:4.87, y:7.395,w:0.55, h:0.125,z0:1.20, z1:"ceiling", label:"recessed cabinet above WC" },
        // Laundry corner: standard 60 cm machines stick out ~11.5 cm past the wall plane
        { k:"washer", x:3.86, y:7.28, w:0.60, h:0.60, stacked:true, label:"washer + dryer" },
        // walnut laundry bay: cabinet above comes forward to the machine fronts + side panel on the open side
        { k:"upper",  x:3.85, y:7.28, w:0.62, h:0.60, z0:1.75, z1:"ceiling", label:"cabinet above dryer" },
        { k:"trim",   x:4.46, y:7.28, w:0.02, h:0.115,z0:0,    z1:"ceiling", label:"walnut side panel (laundry bay)" },
        // Service column fills x 4.47–4.87 (40 cm) back to the corridor wall, front flush at 7.395
        { k:"box",    x:4.47, y:7.395,w:0.40, h:0.485,z0:0, z1:"ceiling", label:"service", role:"service" },
        // Vanity, towel rail between vanity and bath
        { k:"basin",  x:3.87, y:5.59, w:0.90, h:0.48, label:"vanity 0.90" },
        { k:"mirror", x:3.87, y:5.59, w:0.90, h:0.14, z0:1.10, z1:1.85, label:"mirror cabinet" },
        { k:"towel",  x:4.98, y:5.59, w:0.50, h:0.08, z0:0.30, z1:1.50, label:"heated towel rail" },
        { k:"slider", x:3.65, y:5.19, w:0.05, h:0.99, label:"sliding door (hall side)" },
      ],
      "A — walk-in shower": [
        { k:"box",    x:4.90, y:7.33, w:0.54, h:0.20, label:"WC frame boxing" },
        { k:"wc",     x:4.95, y:6.79, w:0.36, h:0.54, label:"wall-hung WC" },
        { k:"shower", x:5.60, y:5.59, w:0.90, h:1.80, label:"walk-in shower 0.90×1.80" },
        { k:"glass",  x:5.60, y:6.40, x2:5.60, y2:7.39 },
        { k:"basin",  x:3.92, y:5.59, w:0.90, h:0.48, label:"vanity 0.90" },
        { k:"washer", x:3.86, y:7.27, w:0.60, h:0.60, label:"washer/dryer" },
        { k:"slider", x:3.66, y:5.17, w:0.05, h:0.99, label:"sliding door (hall side)" },
      ],
      "B — bath + washer": [
        { k:"box",    x:4.90, y:7.33, w:0.54, h:0.20, label:"WC frame boxing" },
        { k:"wc",     x:4.95, y:6.79, w:0.36, h:0.54, label:"wall-hung WC" },
        { k:"bath",   x:4.80, y:5.59, w:1.70, h:0.75, label:"bath 1.70×0.75" },
        { k:"glass",  x:5.60, y:5.59, x2:5.60, y2:6.34 },
        { k:"basin",  x:3.92, y:5.59, w:0.80, h:0.46, label:"vanity 0.80" },
        { k:"washer", x:5.90, y:6.74, w:0.60, h:0.60, label:"washer" },
        { k:"box",    x:3.86, y:7.32, w:0.80, h:0.55, label:"tall cabinet" },
        { k:"slider", x:3.66, y:5.17, w:0.05, h:0.99, label:"sliding door (hall side)" },
      ],
      "none (empty)": [],
    },
  },

  rooms: [
    { id:"60-1", name:"Living / kitchen / hall", area:28.57, at:[1.85,3.0] },
    { id:"60-2", name:"Bedroom",                 area:14.41, at:[5.18,2.9] },
    { id:"60-3", name:"Bathroom",                area: 5.32, at:[4.38,6.48], small:true },
  ],

  // Dimension labels (measured on site 2026-11-22 where available): [x, y, text, rotateDeg]
  dims: [
    [1.86,0.25,"3.72",0],[5.17,0.25,"2.64",0],[0.25,3.0,"6.005",-90],
    [3.55,4.6,"7.88",-90],[6.34,3.2,"5.45",-90],[5.17,5.85,"2.635",0,"bath"],
    [6.34,6.5,"1.805",-90,"bath"],[4.04,6.6,"2.29",-90,"bath"],[1.05,5.85,"2.095",0],
    [1.2,6.4,"1.985",0],[2.4,7.75,"2.67",0],[3.1,-1.70,"7.13",0],
  ],

  // Overlay of the original drawing (for checking alignment)
  overlay: { href:"original-flat.png", x:-0.8467, y:-2.3144, w:8.2019, h:10.9283 },
};
