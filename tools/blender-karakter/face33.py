"""Nil Kervancisi v33 - the face kit: eyeballs (sclera, iris, pupil, highlight), thick upper/lower lids with kohl lash
bands, kohl wings, brows, the mouth plate (dark lens that opens with the jaw) and teeth strips.
Every builder returns (verts world, faces, per-vertex slot, outline flag, tone, fx, weights dict{bone: array})."""
import numpy as np, math
from sdf33 import EYE, EYE_R, MOUTH_Y, MOUTH_Z, HEAD_O, head_sdf
import mesh33 as M

class Part:
    def __init__(self, name):
        self.name = name; self.V = []; self.F = []; self.S = []; self.O = []; self.T = []; self.X = []; self.W = []
    def add(self, V, F, slot, out=0, tone=1.0, fx=0, w=None):
        n = sum(len(v) for v in self.V); V = np.asarray(V, float)
        self.V.append(V); self.F += [[i + n for i in f] for f in F]
        k = len(V); self.S.append(np.full(k, slot) if np.isscalar(slot) else np.asarray(slot)); self.O.append(np.full(k, out) if np.isscalar(out) else np.asarray(out))
        self.T.append(np.full(k, tone) if np.isscalar(tone) else np.asarray(tone)); self.X.append(np.full(k, fx) if np.isscalar(fx) else np.asarray(fx))
        self.W.append(w if w is not None else {})
        return self
    def arrays(self):
        V = np.concatenate(self.V); n = len(V)
        names = sorted(set(k for w in self.W for k in w))
        W = np.zeros((n, len(names))); o = 0
        for V0, w in zip(self.V, self.W):
            for k, a in w.items(): W[o:o + len(V0), names.index(k)] = a
            o += len(V0)
        return V, self.F, np.concatenate(self.S), np.concatenate(self.O), np.concatenate(self.T), np.concatenate(self.X), W, names

def grid_faces(nu, nv, closed_u=False, flip=False):
    F = []
    for j in range(nv - 1):
        for i in range(nu if closed_u else nu - 1):
            a = j * nu + i; b = j * nu + (i + 1) % nu; c = b + nu; d = a + nu
            F.append([a, d, c, b] if flip else [a, b, c, d])
    return F

def frame(side):
    """eye-local axes in the world: X lateral (+outwards), F forward (-Y), U up"""
    X = np.array([side, 0, 0.0]); F = np.array([0, -1.0, 0]); U = np.array([0, 0, 1.0])
    return X, F, U

def eye_center(side): return HEAD_O + np.array([side * EYE[0], EYE[1], EYE[2]])

# ------------------------------------------------------------------ eyeball with rings (crisp iris/pupil as separate islands)
def eyeball(side, r=EYE_R):
    X, F, U = frame(side); c = eye_center(side); bone = 'eye.' + ('L' if side > 0 else 'R')
    P = Part('eye'); seg = 12
    def cap(th0, th1, rr, nr, slot, tone=1.0, off=(0, 0), fx=0):
        V = []
        for j in range(nr):
            th = th0 + (th1 - th0) * j / (nr - 1)
            for i in range(seg):
                ph = 2 * math.pi * i / seg
                d = math.cos(th) * F + math.sin(th) * (math.cos(ph) * X + math.sin(ph) * U)
                V.append(c + rr * d)
        V = np.array(V)
        if off != (0, 0):
            V = V + (off[0] * X + off[1] * U) * r
        Fc = grid_faces(seg, nr, True, flip=False)
        if th0 == 0: Fc = Fc[seg:] + [[0, i, (i + 1) % seg] for i in range(seg)] if False else Fc
        if side > 0: Fc = [f[::-1] for f in Fc]
        P.add(V, Fc, slot, 0, tone, fx, {bone: np.ones(len(V))})
    th_i = math.asin(0.66); th_p = math.asin(0.3)
    cap(th_i, math.pi * 0.85, r, 6, 'white')
    cap(0.0005, th_i, r * 1.004, 3, 'iris', 1.0)
    cap(th_i * 0.78, th_i, r * 1.006, 2, 'iris', 0.55)
    cap(0.0005, th_p, r * 1.008, 3, 'ink')
    # highlight: a small disc up and toward the nose-side light
    hl = []
    for i in range(10):
        ph = 2 * math.pi * i / 10
        a = 0.11
        d = math.cos(a) * F + math.sin(a) * (math.cos(ph) * X + math.sin(ph) * U)
        hl.append(d)
    hl = np.array(hl); rot = rot_about(np.cross(F, U), 0.32) @ rot_about(U, -side * 0.28)
    hl = c + r * 1.012 * (hl @ rot.T)
    Fh = [[10, i, (i + 1) % 10] for i in range(10)]
    if side > 0: Fh = [f[::-1] for f in Fh]
    P.add(np.vstack([hl, [c + r * 1.012 * (rot @ F)]]), Fh, 'hl', 0, 1.0, 0, {bone: np.ones(11)})
    return P

def rot_about(axis, ang):
    a = np.asarray(axis, float); a = a / np.linalg.norm(a); x, y, z = a; c = math.cos(ang); s = math.sin(ang); C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s], [y * x * C + z * s, c + y * y * C, y * z * C - x * s], [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])

# ------------------------------------------------------------------ lids: thick shells whose front edge is a great circle
def lid(side, upper=True, r=EYE_R, alpha=None, span=1.6, nt=11, na=4, t_out=1.13, t_in=1.02):
    X, F, U = frame(side); c = eye_center(side); k = 'L' if side > 0 else 'R'
    bone = ('lid.' if upper else 'lidlo.') + k
    al = alpha if alpha is not None else (math.radians(31) if upper else math.radians(21))
    sg = 1 if upper else -1
    P = Part('lid')
    def surf(rr, a0, a1):
        V = []
        for j in range(na):
            a = a0 + (a1 - a0) * j / (na - 1)
            for i in range(nt):
                t = math.pi * (0.02 + 0.96 * i / (nt - 1))
                d = math.cos(t) * X + math.sin(t) * (math.cos(al + a) * F + sg * math.sin(al + a) * U)
                # a little extra thickness in the middle of the lid
                V.append(c + rr * d * (1 + 0.025 * math.sin(t) * (1 - j / (na - 1))))
        return np.array(V)
    Vo = surf(r * t_out, 0, span); Vi = surf(r * t_in, 0, span)
    n = nt * na
    Fo = grid_faces(nt, na, False, flip=not upper)
    Fi = [[q + n for q in f[::-1]] for f in Fo]
    # rim (front edge, a = 0) and back edge closures
    rim = []; back = []
    for i in range(nt - 1):
        a, b = i, i + 1
        rim.append([a + n, b + n, b, a] if upper else [a, b, b + n, a + n])
        a2, b2 = (na - 1) * nt + i, (na - 1) * nt + i + 1
        back.append([a2, b2, b2 + n, a2 + n] if upper else [a2 + n, b2 + n, b2, a2])
    V = np.vstack([Vo, Vi])
    w = {bone: np.ones(len(V))}
    # skin outside, the rim and the inner face carry the kohl/lash colour
    slot = np.array(['skin'] * n + ['skin'] * n, dtype=object)
    FF = Fo + Fi + back + rim
    if side > 0: FF = [f[::-1] for f in FF]
    P.add(V, FF, 'skin', 0, 1.0, 0, w)
    # lash band: a separate island hugging the edge so the colour edge is crisp
    lw = (0.13 if upper else 0.06)
    Vl_o = []; Vl_i = []
    nl = 3
    for j in range(nl):
        a = -0.02 + (lw + 0.02) * j / (nl - 1)
        for i in range(nt):
            t = math.pi * (0.02 + 0.96 * i / (nt - 1))
            tw = math.sin(t) ** 0.5
            # thicker towards the outer corner (t near 0 is lateral)
            outer = math.exp(-((t - 0.25) / 0.6) ** 2) * (0.6 if upper else 0.3)
            aa = a * (tw + outer)
            d = math.cos(t) * X + math.sin(t) * (math.cos(al + aa) * F + sg * math.sin(al + aa) * U)
            Vl_o.append(c + r * (t_out + 0.012) * d)
            Vl_i.append(c + r * (t_in - 0.004) * d)
    Vl = np.vstack([Vl_o, Vl_i]); m = nt * nl
    Fl = grid_faces(nt, nl, False, flip=not upper)
    Fl2 = [[q + m for q in f[::-1]] for f in Fl]
    rimf = []
    for i in range(nt - 1):
        a, b = i, i + 1
        rimf.append([a + m, b + m, b, a] if upper else [a, b, b + m, a + m])
    FL = Fl + Fl2 + rimf
    if side > 0: FL = [f[::-1] for f in FL]
    P.add(Vl, FL, 'ink', 0, 1.0, 0, {bone: np.ones(len(Vl))})
    return P

# ------------------------------------------------------------------ surface strips projected onto the base head
def on_head(pts_local, off, I=None):
    sdf = lambda p: head_sdf(p, I or {})
    P = M.project(np.asarray(pts_local, float), sdf, 8)
    g = M.grad(sdf, P); g /= np.linalg.norm(g, axis=1)[:, None]
    return P + g * off, g

def strip(curve_local, width, up_dir, off, slot, bone_w, thick=0.0006, out=0, I=None, n=None):
    """a ribbon along a curve on the head surface; width per point; 'up_dir' = direction across the ribbon (local)"""
    C = np.asarray(curve_local, float); W = np.asarray(width, float)
    A = C + np.asarray(up_dir, float)[None, :] * W[:, None] * 0.5
    B = C - np.asarray(up_dir, float)[None, :] * W[:, None] * 0.5
    Ao, na_ = on_head(A, off + thick, I); Bo, _ = on_head(B, off + thick, I)
    Ai, _ = on_head(A, off, I); Bi, _ = on_head(B, off, I)
    m = len(C)
    V = np.vstack([Ao, Bo, Ai, Bi]) + HEAD_O
    F = []
    for i in range(m - 1):
        F.append([i, m + i, m + i + 1, i + 1])                                       # front
        F.append([2 * m + i, 2 * m + i + 1, 3 * m + i + 1, 3 * m + i])               # back
        F.append([i, i + 1, 2 * m + i + 1, 2 * m + i])                              # top edge
        F.append([m + i, 3 * m + i, 3 * m + i + 1, m + i + 1])                      # bottom edge
    F.append([0, 2 * m, 3 * m, m]); F.append([m - 1, 2 * m - 1, 4 * m - 1, 3 * m - 1])
    P = Part('strip'); P.add(V, F, slot, out, 1.0, 0, {k: (v(V) if callable(v) else np.full(len(V), v)) for k, v in bone_w.items()})
    return P

BROWS = {
    # inner -> outer: (x, z) and thickness
    'm': ([(0.011, 0.018), (0.022, 0.0215), (0.034, 0.0235), (0.046, 0.022), (0.055, 0.0175)], [0.0052, 0.0052, 0.0046, 0.0036, 0.0022]),
    'f': ([(0.012, 0.0195), (0.022, 0.0245), (0.034, 0.0285), (0.046, 0.0268), (0.056, 0.0195)], [0.003, 0.0029, 0.0025, 0.0018, 0.001]),
    'old': ([(0.011, 0.0175), (0.022, 0.0225), (0.034, 0.024), (0.046, 0.021), (0.056, 0.0145)], [0.0072, 0.0078, 0.0072, 0.006, 0.0048]),
    'flat': ([(0.011, 0.0175), (0.023, 0.0195), (0.035, 0.0205), (0.047, 0.0195), (0.055, 0.017)], [0.007, 0.0068, 0.006, 0.0048, 0.003]),
}
def smooth_curve(pts, n):
    pts = np.asarray(pts, float); t = np.linspace(0, 1, len(pts)); tt = np.linspace(0, 1, n)
    from scipy.interpolate import CubicSpline
    return CubicSpline(t, pts, axis=0)(tt)

def brow(side, kind='m'):
    k = 'L' if side > 0 else 'R'
    xz, th = BROWS[kind]
    n = 9
    C = smooth_curve([(side * x, -0.1, z) for x, z in xz], n)
    W = smooth_curve(np.array(th)[:, None], n)[:, 0]
    return strip(C, W, (0, 0, 1), 0.0009, 'brow', {'brow.' + k: 1.0}, thick=0.0012)

def wing(side):
    """the kohl wing at the outer eye corner (on the skin, moves with the head)"""
    k = 'L' if side > 0 else 'R'
    ex = EYE[0] + EYE_R * 1.1
    C = np.array([(side * (ex - 0.002), -0.1, EYE[2] + 0.0005), (side * (ex + 0.003), -0.1, EYE[2] + 0.0018), (side * (ex + 0.0075), -0.1, EYE[2] + 0.0042)])
    return strip(C, np.array([0.0022, 0.0016, 0.0005]), (0, 0, 1), 0.0006, 'ink', {'head': 1.0}, thick=0.0004)

# ------------------------------------------------------------------ the mouth: a dark lens + teeth that appear as the jaw opens
def mouth(width=0.0245, cols=11):
    xs = np.linspace(-width, width, cols)
    lens = lambda x: (1 - (x / width) ** 2)
    top = [(x, -0.11, MOUTH_Z + 0.00045 * lens(x)) for x in xs]
    bot = [(x, -0.11, MOUTH_Z - 0.00045 * lens(x)) for x in xs]
    mid = [(x, -0.11, MOUTH_Z) for x in xs]
    T, _ = on_head(top, 0.0007); B, _ = on_head(bot, 0.0007); Mi, _ = on_head(mid, 0.0007)
    # the lens surface: rows top, mid, bottom
    V = np.vstack([T, Mi, B]) + HEAD_O
    F = grid_faces(cols, 3, False, flip=True)
    ux = np.abs(xs) / width
    corner = np.clip((ux - 0.55) / 0.45, 0, 1) ** 1.5
    side = np.sign(xs)
    def w_rows(jaw_frac):
        out = {}
        for j, jf in enumerate(jaw_frac):
            pass
        return out
    n = cols
    W = {'head': np.zeros(3 * n), 'jaw': np.zeros(3 * n), 'mouth.L': np.zeros(3 * n), 'mouth.R': np.zeros(3 * n)}
    for j, jf in enumerate([0.0, 0.5, 1.0]):
        for i in range(n):
            c = corner[i]; rest = 1 - c
            W['jaw'][j * n + i] = rest * jf; W['head'][j * n + i] = rest * (1 - jf)
            W['mouth.L' if side[i] > 0 else 'mouth.R'][j * n + i] += c
    P = Part('mouth'); P.add(V, F, 'mouth', 0, 1.0, 0, W)
    # teeth: upper strip (degenerate at rest: bottom edge sits on the top edge, follows 35% of the jaw)
    T2, _ = on_head([(x * 0.86, -0.11, MOUTH_Z + 0.0006 * lens(x)) for x in xs], 0.001)
    V2 = np.vstack([T2, T2]) + HEAD_O
    W2 = {'head': np.zeros(2 * n), 'jaw': np.zeros(2 * n), 'mouth.L': np.zeros(2 * n), 'mouth.R': np.zeros(2 * n)}
    for j, jf in enumerate([0.0, 0.33]):
        for i in range(n):
            c = corner[i] * 0.8; rest = 1 - c
            W2['jaw'][j * n + i] = rest * jf; W2['head'][j * n + i] = rest * (1 - jf)
            W2['mouth.L' if side[i] > 0 else 'mouth.R'][j * n + i] += c
    P.add(V2, grid_faces(n, 2, False, flip=True), 'teeth', 0, 1.0, 0, W2)
    return P
