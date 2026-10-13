"""Step 1: load the Quaternius male base, tone down the superhero bulk, bigger head, smooth stylised face."""
import bpy, bmesh, math
from mathutils import Vector
from mathutils.geometry import intersect_point_line

# per bone: radial factor around the bone segment (1 = unchanged)
SLIM = {
    'upperarm_l': 0.78, 'upperarm_r': 0.78, 'lowerarm_l': 0.86, 'lowerarm_r': 0.86, 'hand_l': 0.96, 'hand_r': 0.96,
    'clavicle_l': 0.72, 'clavicle_r': 0.72, 'neck_01': 0.78, 'spine_03': 0.86, 'spine_02': 0.89, 'spine_01': 0.92,
    'pelvis': 0.95, 'thigh_l': 0.9, 'thigh_r': 0.9, 'calf_l': 0.92, 'calf_r': 0.92,
}
HEAD_SCALE = 1.16


def load_base(C):
    C.reset()
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=C.BASE_MALE, merge_vertices=True)
    objs = [o for o in bpy.data.objects if o not in before]
    for o in objs:
        if o.type == 'MESH' and o.name != 'SuperHero_Male':
            bpy.data.objects.remove(o)
    arm = bpy.data.objects['Armature']
    body = bpy.data.objects['SuperHero_Male']
    for m in list(body.data.materials):
        pass
    body.data.materials.clear()
    return arm, body


def slim(arm, body):
    me = body.data
    bones = arm.data.bones
    gidx = {g.index: g.name for g in body.vertex_groups}
    seg = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in bones}
    headb = bones['Head']
    hc = headb.head_local.copy() + Vector((0, 0, 0.02))
    new = []
    for v in me.vertices:
        p = v.co.copy()
        acc = Vector((0, 0, 0)); ws = 0.0; hw = 0.0
        for g in v.groups:
            n = gidx.get(g.group); w = g.weight
            if w <= 0 or n not in seg:
                continue
            if n == 'Head':
                hw += w
            k = SLIM.get(n, 1.0)
            if k != 1.0:
                a, b = seg[n]
                q, t = intersect_point_line(p, a, b)
                t = max(0.0, min(1.0, t)); q = a.lerp(b, t)
                acc += (q + (p - q) * k) * w
            else:
                acc += p * w
            ws += w
        if ws > 0:
            p = acc / ws
        # bigger head (smooth through the neck weights)
        if hw > 0:
            p = p + (p - hc) * (HEAD_SCALE - 1.0) * hw
        new.append(p)
    for v, p in zip(me.vertices, new):
        v.co = p
    me.update()


# authored mid-line profile of the face (z, y); front is -Y
PROFILE = [(1.80, -0.090), (1.76, -0.106), (1.72, -0.1115), (1.69, -0.1135), (1.665, -0.1125), (1.64, -0.1085),
           (1.62, -0.1025), (1.60, -0.0925), (1.585, -0.074), (1.57, -0.05)]
NOSE = dict(h=0.0105, z=1.664, sx=0.0095, sup=0.016, sdn=0.0075)


def _prof(z):
    P = PROFILE
    if z >= P[0][0]: return P[0][1]
    if z <= P[-1][0]: return P[-1][1]
    for k in range(len(P) - 1):
        z0, y0 = P[k]; z1, y1 = P[k + 1]
        if z1 <= z <= z0:
            ym = P[k - 1][1] if k > 0 else y0; yp = P[k + 2][1] if k + 2 < len(P) else y1
            t = (z0 - z) / (z0 - z1)
            m0 = (y1 - ym) / 2; m1 = (yp - y0) / 2
            t2, t3 = t * t, t * t * t
            return (2*t3 - 3*t2 + 1)*y0 + (t3 - 2*t2 + t)*m0 + (-2*t3 + 3*t2)*y1 + (t3 - t2)*m1
    return P[-1][1]


XS = 0.074
SIDE = []


def _side(z):
    S = SIDE
    if not S: return _prof(z) + 0.05
    if z <= S[0][0]: return S[0][1]
    if z >= S[-1][0]: return S[-1][1]
    for k in range(len(S) - 1):
        if S[k][0] <= z <= S[k + 1][0]:
            t = (z - S[k][0]) / (S[k + 1][0] - S[k][0] + 1e-9)
            return S[k][1] + (S[k + 1][1] - S[k][1]) * t
    return S[-1][1]


def face_depth(x, z):
    u = min(1.0, abs(x) / XS)
    y0 = _prof(z); y = y0 + (_side(z) - y0) * (u * u * (0.6 + 0.4 * u * u))
    n = NOSE
    dz = z - n['z']
    sz = n['sup'] if dz > 0 else n['sdn']
    y -= n['h'] * math.exp(-(x / n['sx']) ** 2 - (dz / sz) ** 2)
    return y


def smooth_face(arm, body):
    """Close the mouth cavity, melt sockets/lips/nostrils into a smooth stylised mask, keep a short soft nose."""
    me = body.data
    gi = body.vertex_groups['Head'].index
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    dl = bm.verts.layers.deform.active
    # 1. mouth cavity: faces between the lips that sit deeper than the lip line
    kill = [f for f in bm.faces if abs(f.calc_center_median().x) < 0.04 and 1.612 < f.calc_center_median().z < 1.648 and f.calc_center_median().y > -0.096]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    # 2. fill every hole in the head (mouth, eye sockets)
    bnd = [e for e in bm.edges if e.is_boundary and all(v[dl].get(gi, 0) > 0.3 for v in e.verts)]
    print('boundary edges in head', len(bnd))
    if bnd:
        r = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
        bmesh.ops.triangulate(bm, faces=r['faces'])
    bm.verts.ensure_lookup_table()
    dl = bm.verts.layers.deform.active
    # 3. face region weights
    # side reference: the real head surface just outside the eye sockets, binned by height
    global SIDE
    bins = {}
    for v in bm.verts:
        if v[dl].get(gi, 0) > 0.5 and XS - 0.004 < abs(v.co.x) < XS + 0.004 and v.co.y < -0.02:
            bins.setdefault(round(v.co.z * 200), []).append(v.co.y)
    SIDE = sorted((k / 200.0, min(ys)) for k, ys in bins.items())
    zone = {}
    for v in bm.verts:
        w = v[dl].get(gi, 0)
        if w < 0.5 or v.co.y > -0.03:
            continue
        x, y, z = v.co
        fz = 1.0 - max(0.0, (abs(z - 1.668) - 0.052)) / 0.03       # 1.616..1.72 full, fades over 3 cm
        fx = 1.0 - max(0.0, (abs(x) - XS)) / 0.014
        fy = 1.0 - max(0.0, (y + 0.085)) / 0.04                     # only the front
        f = max(0.0, min(1.0, fz)) * max(0.0, min(1.0, fx)) * max(0.0, min(1.0, fy))
        if f > 0:
            zone[v] = f
    for it in range(80):
        nc = {}
        for v, f in zone.items():
            nb = [e.other_vert(v).co for e in v.link_edges]
            ax = sum(c.x for c in nb) / len(nb); az = sum(c.z for c in nb) / len(nb)
            k = 0.6 * min(1.0, f * 1.5)
            nc[v] = (v.co.x + (ax - v.co.x) * k, v.co.z + (az - v.co.z) * k)
        for v, (x, z) in nc.items():
            v.co.x = x; v.co.z = z
            f = zone[v]
            v.co.y = v.co.y + (face_depth(x, z) - v.co.y) * f
    bm.normal_update()
    bm.to_mesh(me); bm.free(); me.update()
