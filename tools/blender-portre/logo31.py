"""Nil Kervancısı v31 — logo emblem and app icon, modelled and rendered in Blender (same cel material + Freestyle ink).
A small Nile boat (papyrus-bundle hull, steering oars, a square sail with the eye of Horus) sailing over a cartouche
plaque on stylised water. usage: python3 logo31.py [logo|icon] out.png [res]"""
import bpy, math, sys, os
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import char31 as C

def boat():
    tm = lambda n, c, **k: C.toon(n, C.hexc(c), **k)
    # hull: a curved papyrus bundle (a bent, tapered tube), raised stern and prow
    pts = [(-0.62, 0, 0.22), (-0.5, 0, 0.05), (-0.25, 0, -0.03), (0.0, 0, -0.05), (0.25, 0, -0.03), (0.5, 0, 0.06), (0.62, 0, 0.26)]
    cu = bpy.data.curves.new('hull', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.085; cu.bevel_resolution = 6; cu.resolution_u = 24
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1); sp.use_endpoint_u = True; sp.order_u = 4
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1); sp.points[i].radius = [0.25, 0.7, 1.0, 1.05, 1.0, 0.7, 0.25][i]
    h = bpy.data.objects.new('hull', cu); bpy.context.scene.collection.objects.link(h); h.scale = (1, 1.55, 1); cu.materials.append(tm('hullc', '#C9873E', strands=2.0, rim=0.5))
    # deck house
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.22, 0, 0.09)); d = bpy.context.object; d.scale = (0.22, 0.17, 0.1)
    C.add_mod(d, 'BEVEL', width=0.02, segments=2); d.data.materials.append(tm('cabin', '#F1E2BC'))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.22, 0, 0.15)); r = bpy.context.object; r.scale = (0.26, 0.2, 0.025)
    C.add_mod(r, 'BEVEL', width=0.01, segments=2); r.data.materials.append(tm('stripe', '#2BA59A'))
    # mast, yard, boom, sail
    C_cyl = lambda a, b, rr, m: _cyl(a, b, rr, m)
    _cyl((0.06, 0, 0.0), (0.06, 0, 1.02), 0.022, tm('wood', '#8E5A33'))
    SA = -0.85; cs, sn = math.cos(SA), math.sin(SA); R = lambda y, z: (0.06 - y * sn, y * cs, z)
    _cyl(R(-0.36, 0.97), R(0.36, 0.97), 0.018, tm('wood', '#8E5A33'))
    _cyl(R(-0.33, 0.33), R(0.33, 0.33), 0.015, tm('wood', '#8E5A33'))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=16, y_subdivisions=16, size=1, location=(0.06 + 0.02 * cs, 0.02 * sn, 0.65), rotation=(math.pi / 2, 0, math.pi / 2 + SA)); s = bpy.context.object
    s.scale = (0.66, 0.62, 1)
    for v in s.data.vertices: v.co.z = 0.07 * (1 - (2 * v.co.x) ** 2) * (1 - 0.3 * (2 * v.co.y) ** 2)   # billow toward +x
    s.data.uv_layers[0].name = 'UV'; s.data.materials.append(sail_mat()); C.add_mod(s, 'SOLIDIFY', thickness=0.006); bpy.ops.object.shade_smooth()
    uv = s.data.uv_layers.active
    # rigging lines
    for a, b in (((0.06, 0, 1.02), (0.6, 0, 0.26)), ((0.06, 0, 1.02), (-0.6, 0, 0.22))):
        _cyl(a, b, 0.004, tm('rope', '#5A3B22'))
    # steering oars at the stern
    for y in (-0.14, 0.14):
        _cyl((-0.5, y, 0.35), (-0.68, y * 1.5, -0.02), 0.012, tm('wood', '#8E5A33'))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(-0.69, y * 1.55, -0.04), segments=16, ring_count=8); o = bpy.context.object
        o.scale = (0.5, 0.12, 0.9); o.rotation_euler = (0, 0.4, 0); bpy.ops.object.shade_smooth(); o.data.materials.append(tm('blade', '#D8B57A'))
    # pennant
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0.14, 0, 1.06)); fl = bpy.context.object; fl.scale = (0.08, 0.035, 1); fl.rotation_euler = (math.pi / 2, 0, 0)
    fl.data.materials.append(tm('pen', '#B7412E'))

def _cyl(a, b, r, m):
    a = Vector(a); b = Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(a + b) / 2, vertices=12)
    o = bpy.context.object; o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); bpy.ops.object.shade_smooth(); o.data.materials.append(m); return o

def sail_mat():
    """sail: cream linen with red/blue border stripes and a painted eye of Horus (image texture)"""
    from PIL import Image, ImageDraw
    N = 1024; im = Image.new('RGBA', (N, N), (246, 236, 212, 255)); g = ImageDraw.Draw(im)
    for i, c in enumerate(((183, 65, 46), (31, 95, 168))):
        w = 34; o = 26 + i * (w + 10); g.rectangle([o, o, N - o, N - o], outline=c, width=w)
    ink = (43, 29, 20, 255); blue = (31, 95, 168, 255)
    cx, cy = N * 0.5, N * 0.47
    # wedjat: tapered brow, almond eye with a big iris, kohl line, the falcon-cheek drop and the spiral
    def bez(pts, n=40):
        out = []
        for i in range(n + 1):
            t = i / n; q = list(pts)
            while len(q) > 1: q = [((1 - t) * q[j][0] + t * q[j + 1][0], (1 - t) * q[j][1] + t * q[j + 1][1]) for j in range(len(q) - 1)]
            out.append(q[0])
        return out
    up = bez([(cx - 250, cy + 10), (cx - 120, cy - 150), (cx + 120, cy - 140), (cx + 250, cy - 20)])
    lo = bez([(cx + 250, cy - 20), (cx + 100, cy + 95), (cx - 120, cy + 95), (cx - 250, cy + 10)])
    g.polygon(up + lo, fill=(255, 252, 240, 255))
    g.ellipse([cx - 80, cy - 105, cx + 70, cy + 70], fill=blue); g.ellipse([cx - 38, cy - 58, cx + 28, cy + 22], fill=ink); g.ellipse([cx - 28, cy - 50, cx - 2, cy - 24], fill=(255, 255, 255, 255))
    g.polygon(up + lo, outline=ink); g.line(up, fill=ink, width=26, joint='curve'); g.line(lo, fill=ink, width=16, joint='curve')
    g.line(bez([(cx + 250, cy - 20), (cx + 300, cy - 30), (cx + 360, cy - 34)]), fill=ink, width=26, joint='curve')
    brow = bez([(cx - 260, cy - 150), (cx - 60, cy - 235), (cx + 160, cy - 220), (cx + 330, cy - 160)])
    for i in range(len(brow) - 1): g.line([brow[i], brow[i + 1]], fill=ink, width=int(18 + 26 * math.sin(math.pi * i / len(brow))))
    g.line(bez([(cx - 40, cy + 95), (cx - 50, cy + 190), (cx - 30, cy + 300)]), fill=ink, width=30, joint='curve')
    g.ellipse([cx - 52, cy + 280, cx - 8, cy + 324], fill=ink)
    sp = bez([(cx + 40, cy + 95), (cx + 150, cy + 200), (cx + 280, cy + 240), (cx + 300, cy + 160), (cx + 220, cy + 150), (cx + 230, cy + 200)])
    g.line(sp, fill=ink, width=26, joint='curve')
    im = im.transpose(Image.FLIP_LEFT_RIGHT)
    path = os.path.join('/tmp', 'sail31.png'); im.save(path)
    m = C.toon('sail', (1, 1, 1), rim=0.3, ao=0.2, img=bpy.data.images.load(path))
    return m

def plaque(w=1.9, h=0.62):
    """the cartouche: a rounded slab on a rope base line, gold rim"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.2, -0.42)); p = bpy.context.object; p.scale = (w, 0.12, h)
    C.add_mod(p, 'BEVEL', width=h * 0.48, segments=12, limit_method='NONE'); p.data.materials.append(C.toon('plaque', C.hexc('#F4E7C6'), rim=0.4, ao=0.3))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.17, -0.42)); r = bpy.context.object; r.scale = (w + 0.08, 0.1, h + 0.08)
    C.add_mod(r, 'BEVEL', width=h * 0.5, segments=12, limit_method='NONE'); r.data.materials.append(C.toon('rim', C.hexc('#D9A43A'), rim=0.5, ao=0.2, gloss=0.4))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.2, -0.42 - h / 2 - 0.1)); b = bpy.context.object; b.scale = (w * 0.9, 0.1, 0.05)
    C.add_mod(b, 'BEVEL', width=0.02, segments=2); b.data.materials.append(C.toon('rim', C.hexc('#D9A43A')))

def water(rx=1.25, ry=0.55):
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.06, location=(0, 0, -0.12), vertices=64); w = bpy.context.object; w.scale = (rx, ry, 1)
    w.data.materials.append(C.toon('water', C.hexc('#2F7FC0'), rim=0.2, ao=0.0))
    for k in range(9):
        x = -0.9 + k * 0.22; y = ((k * 37) % 7 - 3) * 0.08
        bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.012, location=(x, y, -0.085), major_segments=16, minor_segments=4)
        o = bpy.context.object; o.scale = (1.4, 0.4, 0.3); o.data.materials.append(C.flat('foam', C.hexc('#E8FAFC'))); C.no_lines(o)

def run(kind, out, res):
    """renders the boat on its water disc, square and transparent"""
    bpy.ops.wm.read_factory_settings(use_empty=True); C._mats.clear()
    boat(); water()
    for k, (x, y) in enumerate(((-0.95, 0.25), (0.9, -0.3), (-0.7, -0.4))):   # papyrus clumps on the water's edge
        for j in range(5):
            a = (j - 2) * 0.18; h = 0.32 + 0.08 * ((j * 7 + k) % 3)
            _cyl((x, y, -0.1), (x + math.sin(a) * h * 0.5, y, -0.1 + h), 0.008, C.toon('reed', C.hexc('#3E8E5A'), rim=0.3))
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(x + math.sin(a) * h * 0.5, y, -0.1 + h + 0.005), segments=12, ring_count=6); bpy.context.object.scale = (1, 1, 0.55); bpy.ops.object.shade_smooth()
            bpy.context.object.data.materials.append(C.toon('umbel', C.hexc('#9CC45A'), rim=0.3))
    cam = C.setup(res); sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = res; sc.render.line_thickness = res / 260
    sc.cycles.samples = 24
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.55
    yaw, pitch = 0.55, 0.38; t = Vector((0.0, 0, 0.36))
    d = Vector((math.sin(yaw), -math.cos(yaw), math.sin(pitch))).normalized(); cam.location = t + d * 6; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)

if __name__ == '__main__':
    a = sys.argv[1:]
    run('boat', a[0] if a else '/tmp/boat.png', int(a[1]) if len(a) > 1 else 1024)
