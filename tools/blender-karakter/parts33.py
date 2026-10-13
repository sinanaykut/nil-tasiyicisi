"""Nil Kervancisi v33 - hair, headwear, clothes, jewellery and props.
Organic pieces (wigs, kilts, dresses, robes, collars) are distance fields meshed with QuadriFlow (cached); small hard
pieces (bands, rings, props) are built directly from tubes, lathes and boxes. Every builder returns a Mesh-like dict:
V (world, Blender axes), F, slot, out, tone, fx, and a weight rule. Props are designed in the IDLE pose (arms down)
and moved back to the rest (A) pose with the inverse of the idle hand transform, so they hang right in the game."""
import numpy as np, math
from sdf33 import *
import mesh33 as M

# ------------------------------------------------------------------ primitive builders (numpy)
def rotm_to(z_dir):
    z = np.asarray(z_dir, float); z = z / np.linalg.norm(z)
    a = np.array([1.0, 0, 0]) if abs(z[0]) < 0.9 else np.array([0, 1.0, 0])
    x = np.cross(a, z); x /= np.linalg.norm(x); y = np.cross(z, x)
    return np.stack([x, y, z], 1)

def tube(pts, radii, seg=8, closed=True, ring=False):
    """a tube along a polyline; radii per point (scalar or (rx, ry)); caps when closed"""
    P = np.asarray(pts, float); n = len(P); ra = np.asarray(radii, float)
    if ra.ndim == 0: R = np.full((n, 2), float(ra))
    elif ra.ndim == 1 and len(ra) == 2 and n != 2: R = np.tile(ra, (n, 1))
    elif ra.ndim == 1: R = np.stack([ra, ra], 1)
    else: R = ra
    V = []; F = []
    prevx = None
    for i in range(n):
        t = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]
        if ring: t = P[(i + 1) % n] - P[(i - 1) % n]
        t /= np.linalg.norm(t) + 1e-12
        if prevx is None:
            a = np.array([0, 0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0]); x = np.cross(t, a); x /= np.linalg.norm(x)
        else:
            x = prevx - t * (prevx @ t); x /= np.linalg.norm(x) + 1e-12
        prevx = x; y = np.cross(t, x)
        for k in range(seg):
            a = 2 * math.pi * k / seg
            V.append(P[i] + x * math.cos(a) * R[i, 0] + y * math.sin(a) * R[i, 1])
    rows = n if not ring else n + 1
    for i in range(n - 1 + (1 if ring else 0)):
        for k in range(seg):
            a = i * seg + k; b = i * seg + (k + 1) % seg; i2 = (i + 1) % n
            c = i2 * seg + (k + 1) % seg; d = i2 * seg + k
            F.append([a, b, c, d])
    V = np.array(V)
    if closed and not ring:
        c0 = len(V); V = np.vstack([V, P[0], P[-1]])
        for k in range(seg):
            F.append([c0, (k + 1) % seg, k]); F.append([c0 + 1, (n - 1) * seg + k, (n - 1) * seg + (k + 1) % seg])
    return V, F

def lathe(profile, seg=12, base=(0, 0, 0), axis=(0, 0, 1)):
    """profile: list of (r, h) from bottom to top; capped"""
    Rm = rotm_to(axis); b = np.asarray(base, float); pr = np.asarray(profile, float); n = len(pr)
    V = []
    for r, h in pr:
        for k in range(seg):
            a = 2 * math.pi * k / seg
            V.append(b + Rm @ np.array([r * math.cos(a), r * math.sin(a), h]))
    F = []
    for i in range(n - 1):
        for k in range(seg):
            a = i * seg + k; bb = i * seg + (k + 1) % seg; F.append([a, bb, bb + seg, a + seg])
    c0 = len(V); V += [b + Rm @ np.array([0, 0, pr[0, 1]]), b + Rm @ np.array([0, 0, pr[-1, 1]])]
    for k in range(seg):
        F.append([c0, (k + 1) % seg, k]); F.append([c0 + 1, (n - 1) * seg + k, (n - 1) * seg + (k + 1) % seg])
    return np.array(V), F

def boxm(c, hs, Rm=None, bevel=0.0):
    hs = np.asarray(hs, float)
    s = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float) * hs
    if Rm is not None: s = s @ np.asarray(Rm).T
    V = s + np.asarray(c, float)
    F = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    return V, F

def sphere(c, r, seg=10, rings=6):
    pr = [(r * math.sin(math.pi * i / rings) + 1e-5, -r * math.cos(math.pi * i / rings)) for i in range(rings + 1)]
    return lathe(pr, seg, c)

class Piece:
    """vertices, faces, per-vertex slot/out/tone/fx; rule = how the build assigns weights"""
    def __init__(self, name, rule='body', **kw):
        self.name = name; self.rule = rule; self.V = []; self.F = []; self.S = []; self.O = []; self.T = []; self.X = []; self.kw = kw
    def add(self, VF, slot, out=1, tone=1.0, fx=0):
        V, F = VF; n = sum(len(v) for v in self.V)
        self.V.append(np.asarray(V, float)); self.F += [[i + n for i in f] for f in F]
        k = len(V)
        self.S += [slot] * k if isinstance(slot, str) else list(slot); self.O += [out] * k; self.T += [tone] * k if np.isscalar(tone) else list(tone); self.X += [fx] * k
        return self
    def arrays(self):
        return np.concatenate(self.V), self.F, np.array(self.S, dtype=object), np.array(self.O, float), np.array(self.T, float), np.array(self.X, float)

def sdf_piece(name, sdf, lo, hi, faces, h=0.005, voxel=None, key=''):
    ob = M.cached_mesh(name, key, lambda: M.sdf_mesh(name, sdf, lo, hi, h=h, voxel=voxel, faces=faces))
    import bpy
    V = M.verts(ob); F = [list(p.vertices) for p in ob.data.polygons]; bpy.data.objects.remove(ob)
    return V, F

# ------------------------------------------------------------------ hair (head-local fields, then moved to the world)
CR_C = np.array([0, 0.012, 0.026]); CR_R = np.array([0.0735, 0.093, 0.086])
def hairline(y, front=0.034, back=-0.068):
    t = np.clip((y + 0.085) / 0.18, 0, 1); return front + (back - front) * (t * t * (3 - 2 * t))

def no_face(p, d, zcut=0.028, wx=0.064, k=0.006):
    """remove the hair volume in front of the face below the fringe"""
    face = np.maximum(np.maximum(p[:, 2] - zcut, np.abs(p[:, 0]) - wx), p[:, 1] + 0.035)
    return smax(d, -face, k)

def hair_cap(p):
    d = ell(p, CR_C + np.array([0, 0.004, 0.004]), CR_R + 0.0115)
    d = smax(d, hairline(p[:, 1]) - p[:, 2], 0.004)
    return no_face(p, d, 0.031)

def hair_bob(p):
    d = ell(p, CR_C + np.array([0, 0.004, 0.006]), CR_R + 0.012)
    cur = smax(ell(p, (0, 0.012, -0.02), (0.088, 0.1, 0.11)), -0.088 - p[:, 2], 0.006)
    d = smin(d, cur, 0.02)
    d = smax(d, -0.088 - p[:, 2], 0.004)
    return no_face(p, d, 0.028, 0.066)

def hair_long(p):
    d = ell(p, CR_C + np.array([0, 0.006, 0.008]), CR_R + 0.013)
    back = smax(ell(p, (0, 0.04, -0.07), (0.088, 0.07, 0.2)), -0.24 - p[:, 2], 0.01)
    d = smin(d, back, 0.02)
    for s in (-1, 1):   # lappets in front of the shoulders
        lp = box(p, (s * 0.074, -0.006, -0.13), (0.022, 0.028, 0.125), rad=0.012)
        d = smin(d, lp, 0.018)
    d = smax(d, -0.255 - p[:, 2], 0.004)
    d = no_face(p, d, 0.027, 0.064)
    # keep the throat free
    d = smax(d, -box(p, (0, -0.04, -0.17), (0.045, 0.05, 0.12), rad=0.02), 0.01)
    return d

def hair_puff(p):
    d = ell(p, (0, 0.016, 0.03), (0.097, 0.108, 0.104))
    d = smax(d, -0.045 - p[:, 2], 0.01)
    return no_face(p, d, 0.032, 0.066, 0.01)

def hood(p):
    d = ell(p, CR_C + np.array([0, 0.006, 0.006]), CR_R + 0.017)
    d = smin(d, smax(ell(p, (0, 0.015, -0.11), (0.1, 0.11, 0.16)), -0.24 - p[:, 2], 0.01), 0.03)
    face = np.maximum(np.maximum(p[:, 2] - 0.05, np.abs(p[:, 0]) - 0.068), p[:, 1] + 0.02)
    d = smax(d, -face, 0.01)
    d = smax(d, -cap(p, (0, 0.012, -0.1), (0, 0.02, -0.3), 0.06), 0.01)   # the neck goes through
    return d

HAIR = {'hair_cap': (hair_cap, 340), 'hair_bob': (hair_bob, 420), 'hair_long': (hair_long, 560), 'hair_puff': (hair_puff, 380), 'hood': (hood, 420)}

def hair_piece(name):
    fn, faces = HAIR[name]
    import inspect
    V, F = sdf_piece(name, fn, (-0.13, -0.14, -0.3), (0.13, 0.15, 0.16), faces, h=0.0035, voxel=0.006, key=inspect.getsource(fn) + inspect.getsource(no_face) + 'h1' + str(faces))
    pc = Piece(name, 'head')
    slot = 'cloth' if name == 'hood' else 'hair'
    pc.add((V + HEAD_O, F), slot, 1, 1.0, 0 if name == 'hood' else 1)
    return pc

def band(name, h_front=0.042, h_back=0.02, grow=0.0125, r=0.0042, scale=1.0):
    pts = []
    for i in range(40):
        a = 2 * math.pi * i / 40; y = -math.cos(a); x = math.sin(a)
        z = h_front + (h_back - h_front) * (0.5 + 0.5 * math.cos(a + math.pi))
        q = np.array([x * (CR_R[0] + grow) * scale, CR_C[1] + y * (CR_R[1] + grow) * scale, z])
        # push onto the inflated ellipsoid at that height
        rr = np.sqrt(max(1e-6, 1 - ((z - CR_C[2]) / (CR_R[2] + grow)) ** 2))
        q[0] *= rr; q[1] = CR_C[1] + (q[1] - CR_C[1]) * rr
        pts.append(q)
    pc = Piece(name, 'head')
    pc.add(tube(np.array(pts) + HEAD_O, (r, r * 1.6), 6, ring=True), 'band', 1)
    return pc

def tails():
    pc = Piece('tails', 'head')
    for s in (-1, 1):
        pts = [np.array([s * 0.012, 0.1, 0.018]), np.array([s * 0.022, 0.112, -0.03]), np.array([s * 0.032, 0.12, -0.09])]
        pc.add(tube(np.array(pts) + HEAD_O, [(0.0035, 0.012), (0.003, 0.011), (0.0025, 0.01)], 4), 'band', 1)
    return pc

def lotus():
    pc = Piece('lotus', 'head'); c = HEAD_O + np.array([0, -0.098, 0.05])
    pc.add(lathe([(0.004, 0), (0.012, 0.01), (0.017, 0.022), (0.004, 0.02)], 8, c, (0, -0.3, 1)), 'p2', 1, 1.0)
    pc.add(lathe([(0.003, 0), (0.008, 0.012), (0.0, 0.024)], 6, c + np.array([0, -0.004, 0.006]), (0, -0.3, 1)), 'p1', 1)
    return pc

def cone():
    pc = Piece('cone', 'head'); c = HEAD_O + np.array([0, 0.02, 0.118])
    pc.add(lathe([(0.03, 0), (0.026, 0.02), (0.012, 0.05), (0.002, 0.062)], 10, c), 'linen', 1, 0.95)
    return pc

def beard_point():
    pc = Piece('beard_point', 'jaw')
    pts = [np.array([0, -0.086, -0.112]), np.array([0, -0.09, -0.14]), np.array([0, -0.088, -0.17]), np.array([0, -0.08, -0.188])]
    pc.add(tube(np.array(pts) + HEAD_O, [(0.012, 0.007), (0.011, 0.007), (0.01, 0.0065), (0.008, 0.006)], 6), 'beard', 1, 1.0, 1)
    return pc

def beard_long():
    import inspect
    def f(p):
        d = ell(p, (0, -0.07, -0.135), (0.042, 0.03, 0.055))
        d = smin(d, ell(p, (0, -0.072, -0.2), (0.024, 0.02, 0.05)), 0.02)
        for s in (-1, 1): d = smin(d, ell(p, (s * 0.04, -0.045, -0.085), (0.016, 0.03, 0.04)), 0.02)
        d = smax(d, -ell(p, (0, -0.085, MOUTH_Z - 0.008), (0.02, 0.03, 0.008)), 0.004)   # leave the mouth
        d = smax(d, -(p[:, 2] - (MOUTH_Z - 0.004)), 0.004)
        return d
    V, F = sdf_piece('beard_long', f, (-0.08, -0.12, -0.27), (0.08, 0.0, -0.03), 420, h=0.003, voxel=0.005, key=inspect.getsource(f) + 'b1')
    pc = Piece('beard_long', 'jaw'); pc.add((V + HEAD_O, F), 'beard', 1, 1.0, 1)
    return pc

# ------------------------------------------------------------------ clothes (world fields around the base body)
def torso_shell(p, inflate, zlo, zhi, arms=0.0):
    d = body_sdf(p, {}, head=False, hands=False) - inflate
    lim = np.maximum(zlo - p[:, 2], p[:, 2] - zhi)
    if arms <= 0: lim = np.maximum(lim, np.abs(p[:, 0]) - 0.205)
    else:
        J = joints({})
        for s, k in ((1, 'L'), (-1, 'R')):
            a, e = J['uarm' + k], J['farm' + k]; u = (p - a) @ (e - a) / np.linalg.norm(e - a) ** 2
            lim = np.where((s * p[:, 0] > 0.15) & (u > arms), np.maximum(lim, (u - arms) * 0.3), lim)
    return np.maximum(d, lim)

def skirt(p, ztop, zbot, flare=0.1, rx=0.165, ry=0.122):
    t = np.clip((ztop - p[:, 2]) / max(1e-3, ztop - zbot), 0, 1)
    sx = rx + flare * t; sy = ry + flare * 0.6 * t
    q = np.stack([p[:, 0] / sx, (p[:, 1] - 0.012) / sy], 1)
    d = (np.linalg.norm(q, axis=1) - 1) * np.minimum(sx, sy)
    return np.maximum(d, np.maximum(zbot - p[:, 2], p[:, 2] - ztop))

def cloth_kilt(p):
    d = smin(skirt(p, 1.03, 0.6, 0.07, 0.158, 0.118), torso_shell(p, 0.009, 0.9, 1.05), 0.02)
    apron = box(p, (0, -0.118, 0.8), (0.07, 0.012, 0.19), rad=0.006)
    return smin(d, apron, 0.006)

def cloth_kilt_long(p):
    d = smin(skirt(p, 1.04, 0.42, 0.08, 0.158, 0.118), torso_shell(p, 0.009, 0.9, 1.06), 0.02)
    return smin(d, box(p, (0, -0.122, 0.74), (0.06, 0.012, 0.27), rad=0.006), 0.006)

def cloth_dress(p):
    up = torso_shell(p, 0.012, 0.9, 1.335)
    sk = skirt(p, 0.98, 0.1, 0.07, 0.165, 0.122)
    d = smin(up, sk, 0.04)
    for s in (-1, 1):   # straps
        d = smin(d, cap(p, (s * 0.075, -0.1, 1.31), (s * 0.095, -0.02, 1.47), 0.011) if False else cap(p, (s * 0.07, -0.098, 1.32), (s * 0.1, 0.0, 1.455), 0.012), 0.004)
        d = smin(d, cap(p, (s * 0.1, 0.0, 1.455), (s * 0.075, 0.1, 1.32), 0.012), 0.004)
    return d

def cloth_robe(p, sleeve=0.35):
    up = torso_shell(p, 0.01, 0.9, 1.6, arms=sleeve)
    up = smax(up, -cap(p, (0, 0.015, 1.4), (0, 0.02, 1.7), 0.064), 0.01)       # neck opening
    sk = skirt(p, 1.0, 0.09, 0.09, 0.168, 0.125)
    return smin(up, sk, 0.05)

def cloth_robe_s(p): return cloth_robe(p, 0.8)

def diag_band(p, a, b, half, inflate, width_dir=None):
    d = body_sdf(p, {}, head=False, hands=False) - inflate
    a = np.asarray(a, float); b = np.asarray(b, float); n = np.cross(b - a, np.array([0, 1.0, 0])); n /= np.linalg.norm(n)
    slab = np.abs((p - a) @ n) - half
    return np.maximum(d, np.maximum(slab, np.maximum(np.abs(p[:, 0]) - 0.21, np.maximum(0.86 - p[:, 2], p[:, 2] - 1.52))))

def cloth_sash(p): return diag_band(p, (0.17, 0, 1.42), (-0.13, 0, 0.98), 0.032, 0.027)
def cloth_wrap(p): return diag_band(p, (0.16, 0, 1.44), (-0.15, 0, 0.94), 0.085, 0.021)
def cloth_hide(p): return diag_band(p, (0.15, 0, 1.45), (-0.12, 0, 0.92), 0.11, 0.022)
def cloth_straps(p): return np.minimum(diag_band(p, (0.17, 0, 1.42), (-0.13, 0, 1.0), 0.02, 0.018), diag_band(p, (-0.17, 0, 1.42), (0.13, 0, 1.0), 0.02, 0.018))

def collar_field(p):
    d = body_sdf(p, {}, head=False, hands=False) - 0.007
    c = np.array([0, 0.012, 1.47]); r = np.linalg.norm((p - c) * np.array([1, 1.15, 1.6]), axis=1)
    return np.maximum(np.maximum(d, np.maximum(0.078 - r, r - 0.175)), p[:, 2] - 1.462)

CLOTH = {'kilt': (cloth_kilt, 380, 'cloth', 4), 'kilt_long': (cloth_kilt_long, 440, 'cloth', 4), 'dress': (cloth_dress, 560, 'cloth', 0),
         'robe': (cloth_robe, 680, 'cloth', 0), 'sash': (cloth_sash, 200, 'trim', 0),
         'wrap': (cloth_wrap, 300, 'cloth', 0), 'hide': (cloth_hide, 360, 'hide', 3), 'straps': (cloth_straps, 280, 'leather', 0),
         'collar': (collar_field, 420, 'c1', 0)}

def cloth_piece(name):
    import inspect
    fn, faces, slot, fx = CLOTH[name]
    src = inspect.getsource(fn) + inspect.getsource(body_sdf) + inspect.getsource(torso_shell) + inspect.getsource(skirt) + inspect.getsource(diag_band) + 'c1' + str(faces)
    lo, hi = (-0.42, -0.3, 0.02), (0.42, 0.3, 1.68)
    V, F = sdf_piece('cl_' + (name if name != 'collar5' else 'collar'), fn, lo, hi, faces, h=0.006, voxel=0.009, key=src)
    pc = Piece(name, 'skirt' if name in ('kilt', 'kilt_long', 'dress', 'robe', 'robe_s') else 'body')
    S = [slot] * len(V); T = np.ones(len(V))
    if name.startswith('collar'):
        S = ['gold'] * len(V)
    if name in ('robe', 'robe_s', 'kilt', 'kilt_long', 'dress'):
        z = V[:, 2]; T = np.where(z < 0.14, 0.88, 1.0)       # a faint hem
    if name.startswith('collar'):
        # crisp bead bands: every face takes the band of its centre, vertices are split per band
        c = np.array([0, 0.012, 1.47]); sc = np.array([1, 1.15, 1.6])
        edges = np.linspace(0.078, 0.178, 6); cols = ['c1', 'c2', 'c3', 'c2', 'gold']
        V2 = []; F2 = []; S2 = []; key = {}
        for f in F:
            r = np.linalg.norm((V[f].mean(0) - c) * sc); b = int(np.clip(np.searchsorted(edges, r) - 1, 0, 4))
            ff = []
            for v in f:
                k = (v, b)
                if k not in key: key[k] = len(V2); V2.append(V[v]); S2.append(cols[b])
                ff.append(key[k])
            F2.append(ff)
        pc.add((np.array(V2), F2), S2, 1, 1.0, 0)
        return pc
    pc.add((V, F), S, 1, T, fx)
    return pc

def collar_bands(pc, nb=4):
    """crisp concentric bead bands laid over the collar (separate ribbons, no ink)"""
    c = np.array([0, 0.012, 1.47]); sc = np.array([1, 1.15, 1.6])
    edges = np.linspace(0.08, 0.16, nb + 1); cols = ['c1', 'c2', 'c3', 'c1']
    sdf = lambda p: collar_field(p) - 0.0012
    na = 48
    for k in range(nb):
        rows = []
        for rr in (edges[k] + 0.002, edges[k + 1] - 0.002):
            pts = []
            for a in np.linspace(0, 2 * math.pi, na, endpoint=False):
                d = np.array([math.sin(a), -math.cos(a), 0.0]); q = c + d * rr / sc
                q[2] = c[2] - 0.25 * (rr - 0.07) * (1 + 0.5 * max(0, -math.cos(a)))
                pts.append(q)
            P0 = np.array(pts); P0[:, 2] = 1.6
            # drop straight down on the collar's top surface
            for _ in range(40):
                dd = sdf(P0); P0[:, 2] -= np.maximum(dd, 0.0005)
                if (dd < 0.0006).all(): break
            rows.append(P0)
        V = np.vstack(rows); F = [[i, (i + 1) % na, na + (i + 1) % na, na + i] for i in range(na)]
        pc.add((V, F), cols[k % len(cols)], 0, 1.0, 2 if k % 2 else 0)

def rings(name):
    J = joints({}); pc = Piece(name, 'body')
    def ring_at(a, b, t, r, w, slot='gold'):
        c = a + (b - a) * t; ax = (b - a) / np.linalg.norm(b - a); Rm = rotm_to(ax)
        pts = [c + Rm @ np.array([math.cos(q) * r, math.sin(q) * r, 0]) for q in np.linspace(0, 2 * math.pi, 14, endpoint=False)]
        pc.add(tube(np.array(pts), (0.006, w), 5, ring=True), slot, 1, 1.0, 5)
    for k in 'LR':
        if name == 'armband': ring_at(J['uarm' + k], J['farm' + k], 0.45, 0.043, 0.012)
        if name == 'bracelet': ring_at(J['farm' + k], J['hand' + k], 0.88, 0.034, 0.011)
    return pc

def amulet():
    pc = Piece('amulet', 'body'); c = np.array([0, -0.1, 1.33])
    pts = [np.array([math.sin(a) * 0.068, 0.012 - math.cos(a) * 0.085, 1.44 - 0.1 * max(0, -math.cos(a)) ** 2]) for a in np.linspace(0, 2 * math.pi, 18, endpoint=False)]
    pc.add(tube(np.array(pts), 0.0022, 4, ring=True), 'leather', 1)
    pc.add(boxm(c + np.array([0, -0.006, 0]), (0.012, 0.004, 0.016)), 'c1', 1, 1.0, 5)
    return pc

def earrings(kind):
    pc = Piece('ear_' + kind, 'head')
    for s in (-1, 1):
        c = HEAD_O + np.array([s * 0.077, 0.006, -0.034])
        if kind == 'stud': pc.add(sphere(c, 0.0042, 6, 4), 'gold', 1, 1.0, 5)
        else:
            pts = [c + np.array([s * 0.002, math.cos(a) * 0.009, -0.009 + math.sin(a) * 0.009]) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
            pc.add(tube(np.array(pts), 0.0017, 4, ring=True), 'gold', 1, 1.0, 5)
    return pc

# ------------------------------------------------------------------ props (idle-pose design; 'hand.R' / 'hand.L' / 'chest' / 'head')
def prop(name, G):
    """G: dict of idle-pose grip points: G['R'], G['L'] (palm centres), G['dirR'] hand axis (down) ..."""
    R_, L_ = G['R'], G['L']; up = np.array([0, 0, 1.0]); fw = np.array([0, -1.0, 0])
    pc = Piece('p_' + name, 'hand.R'); A = pc.add
    if name == 'spear':
        A(tube([R_ - up * 0.75, R_ + up * 1.05], 0.011, 6), 'wood'); A(lathe([(0.016, 0), (0.02, 0.05), (0.0, 0.17)], 6, R_ + up * 1.05), 'metal', 1, 1.0, 5)
    elif name == 'paddle':
        A(tube([R_ + up * 0.45, R_ - up * 0.55], 0.012, 6), 'wood'); A(boxm(R_ - up * 0.74, (0.06, 0.012, 0.2)), 'wood', 1, 0.9)
    elif name in ('staff', 'ramstaff'):
        A(tube([R_ - up * 0.82, R_ + up * 0.8], 0.012, 6), 'wood')
        if name == 'ramstaff':
            top = R_ + up * 0.8; pts = [top + np.array([0, -math.sin(a) * 0.05, math.cos(a) * 0.05 - 0.05 + a * 0.004]) for a in np.linspace(0, 4.5, 10)]
            A(tube(pts, 0.009, 5), 'gold', 1, 1.0, 5)
    elif name == 'khopesh':
        A(tube([R_ + up * 0.05, R_ - up * 0.06], 0.012, 6), 'leather')
        b0 = R_ - up * 0.06; pts = [b0 - up * 0.17 + fw * 0.0, b0 - up * 0.26 - fw * 0.02]
        arc = [b0 - up * 0.17 + (np.array([0, -math.sin(a), -math.cos(a)]) * 0.09 + np.array([0, 0, 0.09])) for a in np.linspace(0, 2.4, 7)]
        A(tube([b0] + [b0 - up * 0.17] + arc, [(0.004, 0.016)] * 9, 4), 'metal', 1, 1.0, 5)
    elif name == 'shield':
        pc.rule = 'hand.L'; c = L_ + np.array([0.055, -0.02, 0.06])
        V, F = lathe([(0.0, -0.02), (0.15, -0.012), (0.16, 0.0), (0.15, 0.012), (0.0, 0.016)], 14, c, (1, 0, 0))
        V = c + (V - c) * np.array([1, 0.8, 1.4]); A((V, F), 'leather', 1, 1.0, 3); A(sphere(c + np.array([0.02, 0, 0]), 0.028, 8, 5), 'metal', 1, 1.0, 5)
    elif name == 'shieldBack':
        pc.rule = 'chest'; c = np.array([0.02, 0.17, 1.2])
        V, F = lathe([(0.0, -0.02), (0.15, -0.012), (0.16, 0.0), (0.15, 0.012), (0.0, 0.016)], 14, c, (0.1, 1, 0))
        V = c + (V - c) * np.array([1, 1, 1.45]); A((V, F), 'leather', 1, 1.0, 3)
    elif name == 'scale':
        pc.rule = 'hand.L'; t = L_ + up * 0.02
        A(tube([t, t + up * 0.16], 0.005, 5), 'gold', 1, 1.0, 5); bm = t + up * 0.16
        A(tube([bm - np.array([0.11, 0, 0]), bm + np.array([0.11, 0, 0])], 0.005, 5), 'gold', 1, 1.0, 5)
        for s in (-1, 1):
            e = bm + np.array([s * 0.11, 0, 0]); A(tube([e, e - up * 0.12], 0.0015, 3), 'ink', 1)
            A(lathe([(0.0, 0), (0.04, 0.008), (0.042, 0.014)], 10, e - up * 0.13), 'gold', 1, 1.0, 5)
    elif name == 'purse':
        A(lathe([(0.0, -0.1), (0.04, -0.09), (0.05, -0.06), (0.03, -0.025), (0.012, -0.012), (0.018, 0.0)], 9, R_ - up * 0.02), 'leather', 1, 1.0)
    elif name == 'palette':
        pc.rule = 'hand.L'; c = L_ - up * 0.06
        A(boxm(c, (0.012, 0.03, 0.12)), 'wood', 1, 1.0); A(boxm(c + np.array([0, -0.031, 0.08]), (0.006, 0.002, 0.008)), 'ink', 1); A(boxm(c + np.array([0, -0.031, 0.06]), (0.006, 0.002, 0.008)), 'p2', 1)
    elif name == 'scroll':
        A(tube([R_ - up * 0.1, R_ + up * 0.1], 0.022, 8), 'linen', 1, 1.0)
    elif name == 'rope':
        pc.rule = 'chest'
        pts = [np.array([math.sin(a) * 0.15, 0.012 - math.cos(a) * 0.115, 1.2 + 0.2 * math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 22, endpoint=False)]
        A(tube(np.array(pts), 0.016, 6, ring=True), 'p1', 1, 1.0, 1)
    elif name == 'chisel':
        A(tube([R_ + up * 0.04, R_ - up * 0.16], 0.008, 5), 'metal', 1, 1.0, 5)
    elif name == 'mallet':
        pc.rule = 'hand.L'; A(tube([L_ + up * 0.04, L_ - up * 0.14], 0.01, 5), 'wood'); A(tube([L_ - up * 0.14 - fw * 0.06, L_ - up * 0.14 + fw * 0.06], 0.035, 8), 'wood', 1, 0.85)
    elif name == 'ingot':
        pc.rule = 'hand.L'; c = L_ - up * 0.05 - fw * 0.03; V, F = boxm(c, (0.012, 0.1, 0.07))
        V[:, 1] = c[1] + (V[:, 1] - c[1]) * 1.0; A((V, F), 'metal', 1, 1.0, 5)
    elif name == 'gem':
        A(sphere(R_ - fw * 0.03, 0.03, 6, 4), 'p1', 1, 1.0, 5)
    elif name == 'dates':
        pc.rule = 'hand.L'; c = L_ - up * 0.02 - fw * 0.06
        A(lathe([(0.05, 0), (0.1, 0.06), (0.105, 0.07)], 12, c), 'p1', 1, 0.9)
        for i in range(7): A(sphere(c + np.array([math.cos(i) * 0.05, math.sin(i) * 0.05, 0.075]), 0.02, 6, 4), 'leather', 1, 0.8)
    elif name == 'incense':
        A(lathe([(0.0, 0), (0.05, 0.02), (0.06, 0.045), (0.05, 0.05)], 10, R_ - fw * 0.07 - up * 0.02), 'gold', 1, 1.0, 5)
        A(tube([R_, R_ - fw * 0.07 - up * 0.01], 0.006, 4), 'gold', 1, 1.0, 5)
    elif name == 'cup':
        A(lathe([(0.03, 0), (0.008, 0.02), (0.008, 0.05), (0.04, 0.08), (0.045, 0.11)], 10, R_ - fw * 0.03 - up * 0.04), 'gold', 1, 1.0, 5)
    elif name == 'ledger':
        pc.rule = 'hand.L'; A(boxm(L_ - up * 0.04 - fw * 0.03, (0.01, 0.1, 0.13)), 'linen', 1, 0.95); A(boxm(L_ - up * 0.04 - fw * 0.03 + np.array([0.011, 0, 0]), (0.001, 0.08, 0.11)), 'ink', 0, 0.7)
    elif name == 'jug':
        A(lathe([(0.04, 0), (0.07, 0.06), (0.065, 0.13), (0.03, 0.17), (0.035, 0.2)], 12, R_ - up * 0.2 - fw * 0.07), 'p2', 1, 0.95)
        A(tube([R_ - up * 0.03, R_ - fw * 0.07 - up * 0.05], 0.008, 4), 'p2', 1, 0.9)
    elif name == 'censer':
        A(tube([R_ - up * 0.04 + fw * 0.02, R_ - fw * 0.4 - up * 0.02], 0.009, 5), 'gold', 1, 1.0, 5)
        A(lathe([(0.0, 0), (0.03, 0.02), (0.035, 0.04)], 8, R_ - fw * 0.42 - up * 0.03), 'gold', 1, 1.0, 5)
    elif name == 'sticks':
        for i in range(4): A(boxm(R_ - up * 0.04 + np.array([0, (i - 1.5) * 0.012, 0]), (0.004, 0.005, 0.12)), 'linen', 1, 0.95)
    elif name == 'basket':
        pc.rule = 'hand.L'; c = L_ - up * 0.2
        A(lathe([(0.07, 0), (0.1, 0.1), (0.1, 0.12)], 12, c), 'p1', 1, 0.9, 1)
        pts = [c + np.array([math.cos(a) * 0.095, 0, 0.12 + math.sin(a) * 0.12]) for a in np.linspace(0, math.pi, 9)]
        A(tube(pts, 0.007, 4), 'p1', 1, 0.8)
    elif name in ('jarHead', 'basketHead'):
        pc.rule = 'head'; c = HEAD_O + np.array([0, 0.012, 0.115])
        if name == 'jarHead': A(lathe([(0.04, 0), (0.09, 0.07), (0.08, 0.15), (0.04, 0.2), (0.045, 0.22)], 12, c), 'p2', 1, 0.95)
        else: A(lathe([(0.08, 0), (0.15, 0.07), (0.16, 0.09)], 14, c), 'p1', 1, 0.9, 1); A(sphere(c + up * 0.1, 0.07, 10, 5), 'p2', 1, 0.95)
    elif name == 'jarHip':
        pc.rule = 'hand.L'; A(lathe([(0.03, 0), (0.08, 0.06), (0.07, 0.14), (0.03, 0.18), (0.035, 0.2)], 12, L_ - up * 0.04 + np.array([0.05, -0.04, 0])), 'p2', 1, 0.95)
    elif name == 'jarShoulder':
        pc.rule = 'chest'; c = np.array([0.15, 0.05, 1.46]); A(lathe([(0.03, 0), (0.08, 0.06), (0.07, 0.15), (0.03, 0.2)], 12, c, (-0.3, 0.2, 1)), 'p2', 1, 0.95)
    elif name == 'flowers':
        for i in range(5):
            tip = R_ + up * (0.18 + 0.03 * i) + np.array([(i - 2) * 0.02, -0.02, 0])
            A(tube([R_, tip], 0.003, 3), 'leather', 0); A(sphere(tip, 0.016, 6, 4), 'p1', 1)
    elif name == 'fish':
        A(lathe([(0.0, 0), (0.03, 0.05), (0.035, 0.12), (0.0, 0.22), (0.03, 0.26)], 8, R_ - up * 0.3, (0, 0, 1)), 'metal', 1, 0.85)
    elif name == 'hoe':
        A(tube([R_ - up * 0.4, R_ + up * 0.6], 0.012, 5), 'wood'); A(boxm(R_ + up * 0.62 - fw * 0.07, (0.03, 0.08, 0.012)), 'wood', 1, 0.8)
    elif name == 'sack':
        pc.rule = 'chest'; A(sphere(np.array([-0.13, 0.08, 1.5]), 0.13, 10, 6), 'linen', 1, 0.9)
    elif name == 'net':
        A(sphere(R_ - up * 0.12, 0.08, 8, 5), 'p1', 1, 0.85, 1)
    elif name == 'oarpin':
        pc.rule = 'chest'; A(boxm(np.array([-0.07, -0.13, 1.36]), (0.014, 0.004, 0.014)), 'gold', 1, 1.0, 5)
    else:
        return None
    return pc

PROPS = ['spear', 'paddle', 'staff', 'ramstaff', 'khopesh', 'shield', 'shieldBack', 'scale', 'purse', 'palette', 'scroll', 'rope', 'chisel', 'mallet',
         'ingot', 'gem', 'dates', 'incense', 'cup', 'ledger', 'jug', 'censer', 'sticks', 'basket', 'jarHead', 'basketHead', 'jarHip', 'jarShoulder',
         'flowers', 'fish', 'hoe', 'sack', 'net', 'oarpin']
