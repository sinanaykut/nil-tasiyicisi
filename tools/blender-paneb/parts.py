"""Step 2: Paneb's costume, fitted to the shaped body by ray casts.
   wig (short black Egyptian bob with a straight fringe), red headband with two tails at the back,
   white linen shendyt kilt with pleated front apron, red/gold belt, bead-band usekh collar, gold armbands.
   Every part is a plain mesh with point-domain colour attributes 'Col' (albedo) and '_FX' (r = ink width, g = fx code)."""
import bpy, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

# fx codes understood by the runtime shader (stored as code/16 in _FX.g)
FX = dict(none=0, hair=1, pleat=2, bead=3, gold=4, face=5, cloth=6, skin=7)

PAL = dict(skin='#B97C4E', hair='#211A2A', band='#C8402C', linen='#F3EEDF', linen2='#FAF7EE', belt='#B7412E',
           gold='#E2A93A', turq='#2BA59A', red='#C2452F', blue='#2C5FA6', white='#F1ECE0')


def hexc(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x ** 2.2 for x in c] + [1.0]   # stored linear (Blender colour attrs are linear; exporter writes linear)


def new_obj(name, verts, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate(); me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def paint(o, col_fn, fx_fn):
    """col_fn(vi, co) -> hex, fx_fn(vi, co) -> (ink, code)"""
    me = o.data
    ca = me.color_attributes.get('Col') or me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    fa = me.attributes.get('_FX') or me.attributes.new('_FX', 'FLOAT_COLOR', 'POINT')
    cache = {}
    for v in me.vertices:
        h = col_fn(v.index, v.co)
        if h not in cache: cache[h] = hexc(h)
        ca.data[v.index].color = cache[h]
        ink, code = fx_fn(v.index, v.co)
        fa.data[v.index].color = (ink / 2.0, code / 16.0, 0.0, 1.0)


def set_weights(o, wfn):
    """wfn(co) -> {bone: w}"""
    vg = {}
    for v in o.data.vertices:
        for b, w in wfn(v.co).items():
            if w <= 0: continue
            if b not in vg: vg[b] = o.vertex_groups.new(name=b)
            vg[b].add([v.index], w, 'REPLACE')


def grid_faces(cols, rows, wrap=True):
    F = []
    nc = cols if wrap else cols - 1
    for r in range(rows - 1):
        for c in range(nc):
            a = r * cols + c; b = r * cols + (c + 1) % cols
            F.append((a, b, b + cols, a + cols))
    return F


class Fit:
    def __init__(self, body):
        dg = bpy.context.evaluated_depsgraph_get()
        self.bvh = BVHTree.FromObject(body, dg)
        me = body.data
        self.kd = KDTree(len(me.vertices))
        for v in me.vertices: self.kd.insert(v.co, v.index)
        self.kd.balance()
        self.body = body
        gn = {g.index: g.name for g in body.vertex_groups}
        self.w = [{gn[g.group]: g.weight for g in v.groups if g.weight > 0.01} for v in me.vertices]
        self.co = [v.co.copy() for v in me.vertices]

    def ray(self, o, d, maxd=1.0):
        loc, nrm, idx, dist = self.bvh.ray_cast(Vector(o), Vector(d).normalized(), maxd)
        return loc, nrm, dist

    def near_weights(self, co, k=4):
        """inverse-distance blend of the k nearest body vertices' weights"""
        acc = {}; tot = 0
        for (c, i, d) in self.kd.find_n(co, k):
            f = 1.0 / (d + 0.004)
            tot += f
            for b, w in self.w[i].items(): acc[b] = acc.get(b, 0) + w * f
        acc = {b: w / tot for b, w in acc.items()}
        s = sum(acc.values()) or 1
        top = sorted(acc.items(), key=lambda t: -t[1])[:4]
        s = sum(w for _, w in top) or 1
        return {b: w / s for b, w in top}


# ------------------------------------------------------------------ wig
def wig(F, z_f=1.748, z_b=1.612, th_face=60.0, cols=44, dome_rows=10, cur_rows=7):
    c = Vector((0, 0.004, 1.708))
    thetas = [-180 + 360 * i / cols for i in range(cols)]

    def hdir(t):
        t = math.radians(t); return Vector((math.sin(t), -math.cos(t), 0))
    # envelope of the head below the dome (ears, jaw) for a straight curtain
    env = []
    for t in thetas:
        m = 0
        z = z_b - 0.01
        while z <= c.z + 0.001:
            loc, n, d = F.ray(Vector((0, c.y, z)), hdir(t), 0.4)
            if loc: m = max(m, d)
            z += 0.008
        env.append(m)
    # symmetric + smooth
    for _ in range(3):
        env = [(env[i - 1] + 2 * env[i] + env[(i + 1) % cols]) / 4 for i in range(cols)]
    env = [max(env[i], env[(cols - i) % cols]) for i in range(cols)]
    cur = [e + 0.016 for e in env]
    columns = []
    for ci, t in enumerate(thetas):
        prof = []
        for r in range(dome_rows + 1):
            ph = math.radians(90 - 90 * r / dome_rows)
            d = hdir(t) * math.cos(ph) + Vector((0, 0, math.sin(ph)))
            if r == 0: d = Vector((0, 0.0001, 1))
            loc, n, dist = F.ray(c, d, 0.5)
            rr = (dist if loc else 0.12) + 0.013 + 0.007 * (1 - math.sin(ph))
            p = c + d.normalized() * rr
            s = max(0.0, 1 - math.degrees(ph) / 40.0); s = s * s * (3 - 2 * s)
            h = Vector((p.x, p.y - c.y, 0)); hl = h.length
            if hl > 1e-6 and hl < cur[ci]:
                h2 = h * (1 + (cur[ci] / hl - 1) * s)
                p = Vector((h2.x, h2.y + c.y, p.z))
            prof.append(p)
        last = prof[-1]
        hv = Vector((last.x, last.y - c.y, 0)).normalized() * max(cur[ci], Vector((last.x, last.y - c.y, 0)).length)
        for k in range(1, cur_rows + 1):
            z = c.z - (c.z - z_b) * k / cur_rows
            tuck = 0.008 if k == cur_rows else 0.0
            hh = hv * (1 - tuck / max(hv.length, 1e-6))
            prof.append(Vector((hh.x, hh.y + c.y, z)))
        # front columns stop at the fringe: resample the part of the profile above z_f
        front = abs(t) < th_face
        if front:
            # cut polyline at z_f
            pts = [prof[0]]
            for a, b in zip(prof, prof[1:]):
                if b.z >= z_f: pts.append(b); continue
                if a.z > z_f:
                    u = (a.z - z_f) / (a.z - b.z); pts.append(a.lerp(b, u))
                break
            prof = pts
        # resample by arc length to a fixed count
        n = dome_rows + cur_rows + 1
        L = [0]
        for a, b in zip(prof, prof[1:]): L.append(L[-1] + (b - a).length)
        out = []
        for k in range(n):
            s = L[-1] * k / (n - 1)
            j = max(0, min(len(L) - 2, next((i for i in range(len(L) - 1) if L[i + 1] >= s), len(L) - 2)))
            u = (s - L[j]) / max(L[j + 1] - L[j], 1e-9)
            out.append(prof[j].lerp(prof[j + 1], u))
        columns.append(out)
    rows = dome_rows + cur_rows + 1
    V = [columns[ci][r] for r in range(rows) for ci in range(cols)]
    # collapse the pole row to one point each (keep the grid; tiny faces are removed by merge)
    Fc = grid_faces(cols, rows)
    o = new_obj('Wig', V, Fc)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm.to_mesh(o.data); bm.free()
    o.data.update()
    paint(o, lambda i, co: PAL['hair'], lambda i, co: (1.0, FX['hair']))
    set_weights(o, lambda co: {'Head': 1.0})
    o['cur'] = cur
    return o, columns, thetas, c


def wig_radius_at(columns, c, ci, z):
    col = columns[ci]
    for a, b in zip(col, col[1:]):
        if (a.z - z) * (b.z - z) <= 0 and a.z != b.z:
            u = (a.z - z) / (a.z - b.z); p = a.lerp(b, u)
            return Vector((p.x, p.y - c.y, 0)).length
    return None


def headband(wg, z0=1.751, z1=1.771):
    o_wig, columns, thetas, c = wg
    cols = len(thetas)
    V = []
    prof = [(z0, 0.0), (z0, 0.006), (z1, 0.006), (z1, 0.0)]
    for (z, off) in prof:
        for ci, t in enumerate(thetas):
            r = wig_radius_at(columns, c, ci, z) or wig_radius_at(columns, c, ci, z + 0.004) or 0.12
            tr = math.radians(t)
            rr = r + 0.002 + off
            V.append(Vector((math.sin(tr) * rr, c.y - math.cos(tr) * rr, z)))
    Fc = grid_faces(cols, len(prof))
    # two tails at the back
    bi = cols // 2 - cols // 2  # theta = -180 is index 0 (back)
    base = V[0]
    tails = []
    for sgn in (-1, 1):
        x0 = base.x + sgn * 0.012
        y0 = base.y + 0.004
        pts = []
        for k in range(5):
            dz = 0.02 + k * 0.03
            w = 0.009 + 0.002 * k
            dx = sgn * (0.006 + 0.012 * k)
            pts.append((Vector((x0 + dx - w, y0 + 0.006 + 0.004 * k, z0 - dz + 0.02)), Vector((x0 + dx + w, y0 + 0.006 + 0.004 * k, z0 - dz + 0.02))))
        s = len(V)
        for a, b in pts: V.extend([a, b])
        for k in range(4):
            Fc.append((s + 2 * k, s + 2 * k + 1, s + 2 * k + 3, s + 2 * k + 2))
    o = new_obj('Band', V, Fc)
    paint(o, lambda i, co: PAL['band'], lambda i, co: (1.0, FX['cloth']))
    set_weights(o, lambda co: {'Head': 1.0})
    return o


# ------------------------------------------------------------------ kilt
def hull2d(pts):
    pts = sorted(set(pts))
    if len(pts) < 3: return pts
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cr(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def ray_poly(poly, cx, cy, ang):
    dx, dy = math.sin(ang), -math.cos(ang)
    best = 0
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]; bx, by = poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        if abs(den) < 1e-12: continue
        t = ((ax - cx) * ey - (ay - cy) * ex) / den
        u = ((ax - cx) * dy - (ay - cy) * dx) / den
        if t > 0 and -1e-6 <= u <= 1 + 1e-6: best = max(best, t)
    return best


def kilt(F, z_top=1.035, z_bot=0.615, cols=40, rows=8):
    cx, cy = 0.0, 0.03
    angs = [math.radians(-180 + 360 * i / cols) for i in range(cols)]
    rad = []
    prev = None
    for r in range(rows):
        z = z_top - (z_top - z_bot) * r / (rows - 1)
        pts = [(co.x, co.y) for co in F.co if abs(co.z - z) < 0.014 and abs(co.x) < 0.3]
        hull = hull2d(pts)
        rr = [ray_poly(hull, cx, cy, a) for a in angs]
        s = r / (rows - 1)
        rr = [x + 0.009 + 0.03 * s + 0.04 * s * s + s * (0.04 * max(0.0, math.cos(a)) ** 2 + 0.025 * max(0.0, -math.cos(a)) ** 2) for x, a in zip(rr, angs)]
        if prev: rr = [max(a, b + 0.004) for a, b in zip(rr, prev)]
        rr = [(rr[i] + rr[(cols - i) % cols]) / 2 for i in range(cols)]
        prev = rr; rad.append((z, rr))
    V = []
    for z, rr in rad:
        for a, r_ in zip(angs, rr):
            V.append(Vector((cx + math.sin(a) * r_, cy - math.cos(a) * r_, z)))
    Fc = grid_faces(cols, rows)
    # front apron (pleated panel), a little proud of the kilt
    z0, rr0 = rad[0]; zN, rrN = rad[-1]
    i0 = cols // 2   # angle 0 = front (-Y)
    def front_y(rr): return cy - rr[i0]
    s = len(V)
    AR = 6
    for k in range(AR):
        u = k / (AR - 1)
        z = z0 - 0.03 - (z0 - zN - 0.03) * u - 0.006 * u
        zz, rr = rad[min(rows - 1, int(round(u * (rows - 1))))]
        w = 0.06 + 0.06 * u
        y = cy - max(rr[i0 - 2:i0 + 3]) - 0.008 - 0.01 * u
        V.append(Vector((-w, y + 0.012 * (w / 0.12) ** 2, z))); V.append(Vector((0, y - 0.004, z))); V.append(Vector((w, y + 0.012 * (w / 0.12) ** 2, z)))
    for k in range(AR - 1):
        a = s + 3 * k
        Fc.append((a, a + 1, a + 4, a + 3)); Fc.append((a + 1, a + 2, a + 5, a + 4))
    o = new_obj('Kilt', V, Fc)
    nk = rows * cols
    paint(o, lambda i, co: PAL['linen'] if i < nk else PAL['linen2'], lambda i, co: (1.0 if i < nk else 0.8, FX['pleat']))

    def kw(co):
        s = max(0.0, min(1.0, (z_top - co.z) / (z_top - z_bot)))
        t = min(0.95, 1.25 * s ** 0.85)
        lt = max(0.0, min(1.0, (co.x + 0.06) / 0.12))
        return {'pelvis': 1 - t, 'thigh_l': t * lt, 'thigh_r': t * (1 - lt)}
    set_weights(o, kw)
    return o, rad, angs, (cx, cy)


def belt(F, kl, z0=1.012, z1=1.05):
    o_k, rad, angs, (cx, cy) = kl
    cols = len(angs)
    rr = rad[0][1]
    V = []
    prof = [(z1, -0.002), (z1, 0.007), (z0, 0.009), (z0, -0.001)]
    for (z, off) in prof:
        for a, r_ in zip(angs, rr):
            r2 = r_ + off
            V.append(Vector((cx + math.sin(a) * r2, cy - math.cos(a) * r2, z)))
    Fc = grid_faces(cols, len(prof))
    # gold knot plate in front
    i0 = cols // 2
    yf = cy - rr[i0] - 0.011
    s = len(V)
    for (x, z) in [(-0.022, z1 + 0.004), (0.022, z1 + 0.004), (0.022, z0 - 0.006), (-0.022, z0 - 0.006)]:
        V.append(Vector((x, yf, z)))
    Fc.append((s, s + 1, s + 2, s + 3))
    o = new_obj('Belt', V, Fc)
    nb = len(prof) * cols
    paint(o, lambda i, co: PAL['belt'] if i < nb else PAL['gold'], lambda i, co: (1.0, FX['gold'] if i >= nb else FX['cloth']))
    set_weights(o, lambda co: {'pelvis': 1.0})
    return o


# ------------------------------------------------------------------ usekh collar
def collar(F, cols=40, r_in=0.082, r_out=0.17):
    c = Vector((0, 0.028, 0))
    bands = [r_in, 0.098, 0.116, 0.134, 0.152, r_out]
    angs = [math.radians(-180 + 360 * i / cols) for i in range(cols)]
    V = []
    for ri, rho in enumerate(bands):
        for a in angs:
            ca, sa = math.cos(a), math.sin(a)
            k = 1.0 + 0.22 * sa * sa * (rho - r_in) / (r_out - r_in)       # wider over the shoulders
            x = sa * rho * k; y = c.y - ca * rho * (0.92 if ca > 0 else 0.86)
            drop = (rho - r_in) * (0.55 + 0.75 * ca * ca)                      # chest/back fall away more than shoulders
            V.append(Vector((x, y, 1.525 - drop)))
    def snap(V, off):
        out = []
        for ri in range(len(bands)):
            for i in range(cols):
                p = V[ri * cols + i]
                loc, n, idx, d = F.bvh.find_nearest(p)
                out.append(loc + n * (off + 0.0015 * ri))
        return out
    V = snap(V, 0.006)
    for _ in range(3):
        W = [v.copy() for v in V]
        for ri in range(len(bands)):
            for i in range(cols):
                nb = [W[ri * cols + (i - 1) % cols], W[ri * cols + (i + 1) % cols]]
                if ri > 0: nb.append(W[(ri - 1) * cols + i])
                if ri < len(bands) - 1: nb.append(W[(ri + 1) * cols + i])
                avg = sum(nb, Vector()) / len(nb)
                V[ri * cols + i] = W[ri * cols + i].lerp(avg, 0.5)
        V = snap(V, 0.006)
    bc = [PAL['gold'], PAL['turq'], PAL['red'], PAL['blue'], PAL['turq']]
    fxc = [FX['gold'], FX['bead'], FX['bead'], FX['bead'], FX['bead']]
    VV, Fc, cols_of = [], [], []
    for b in range(len(bands) - 1):
        s0 = len(VV)
        VV.extend(V[b * cols:(b + 2) * cols])
        cols_of.extend([b] * (2 * cols))
        for i in range(cols):
            a = s0 + i; bb = s0 + (i + 1) % cols
            Fc.append((a, bb, bb + cols, a + cols))
    o = new_obj('Collar', VV, Fc)
    paint(o, lambda i, co: bc[cols_of[i]], lambda i, co: (0.7 if cols_of[i] < 4 else 1.0, fxc[cols_of[i]]))
    set_weights(o, lambda co: F.near_weights(co))
    o['bands'] = len(bands)
    return o


def armband(F, side='l', x0=0.315, w=0.026):
    sg = 1 if side == 'l' else -1
    axis_y, axis_z = 0.068, 1.456
    V = []
    n = 16
    rings = [(x0 - w / 2, 0.0), (x0 - w / 2, 0.005), (x0 + w / 2, 0.005), (x0 + w / 2, 0.0)]
    rad = []
    for k in range(n):
        a = 2 * math.pi * k / n
        d = Vector((0, math.cos(a), math.sin(a)))
        loc, nn, dist = F.ray(Vector((sg * x0, axis_y, axis_z)), d, 0.2)
        rad.append((dist or 0.045) + 0.003)
    for (x, off) in rings:
        for k in range(n):
            a = 2 * math.pi * k / n
            r = rad[k] + off
            V.append(Vector((sg * x, axis_y + math.cos(a) * r, axis_z + math.sin(a) * r)))
    Fc = grid_faces(n, len(rings))
    if sg < 0: Fc = [tuple(reversed(f)) for f in Fc]
    o = new_obj('Arm_' + side, V, Fc)
    paint(o, lambda i, co: PAL['gold'], lambda i, co: (1.0, FX['gold']))
    set_weights(o, lambda co: {'upperarm_' + side: 1.0})
    return o


def orient_out(o, F):
    """flip faces so normals point away from the body surface"""
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    flip = []
    for f in bm.faces:
        c = f.calc_center_median()
        loc, n, idx, d = F.bvh.find_nearest(c)
        if loc is None: continue
        out = c - loc
        if out.length < 1e-6: out = n
        if f.normal.dot(out) < 0: flip.append(f)
    for f in flip: f.normal_flip()
    bm.to_mesh(me); bm.free(); me.update()
    return len(flip)
