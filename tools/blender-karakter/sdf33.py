"""Nil Kervancisi v33 - signed distance sculpting helpers and the head/body fields.
Units: metres. Blender frame: Z up, the character faces -Y, x = lateral.
Head-local frame: origin at eye level on the mid line (head bone space offset), face toward -Y."""
import numpy as np
from mathutils import Euler

def rotm(rx=0, ry=0, rz=0): return np.array(Euler((rx, ry, rz)).to_matrix())

def ell(p, c, r, R=None):
    q = p - np.asarray(c, float)
    if R is not None: q = q @ R
    r = np.asarray(r, float)
    k0 = np.linalg.norm(q / r, axis=1); k1 = np.linalg.norm(q / (r * r), axis=1) + 1e-9
    return k0 * (k0 - 1.0) / k1

def cap(p, a, b, r, r2=None):
    a = np.asarray(a, float); b = np.asarray(b, float); pa = p - a; ba = b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    rr = r if r2 is None else r + (r2 - r) * h
    return np.linalg.norm(pa - ba[None, :] * h[:, None], axis=1) - rr

def box(p, c, hs, R=None, rad=0.0):
    q = p - np.asarray(c, float)
    if R is not None: q = q @ R
    q = np.abs(q) - (np.asarray(hs, float) - rad)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(np.max(q, axis=1), 0) - rad

def smin(a, b, k):
    if k <= 0: return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)

def smax(a, b, k): return -smin(-a, -b, k)

def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

# ------------------------------------------------------------------ the head
MOUTH_Z = -0.058          # mouth line (fixed for every identity: the mouth plate sits here)
MOUTH_Y = -0.1005
EYE = (0.0318, -0.0722, 0.002)   # eyeball centre (x mirrored); fixed for every identity
EYE_R = 0.0134

BASE_ID = dict(f=0.0, facew=1.0, facel=1.0, jaw=1.0, chin=0.0, chinw=1.0, cheek=0.0, fat=0.0, age=0.0, nl=1.0, nw=1.0,
               nb=0.0, nh=0.0, ntip=0.0, brow=1.0, fh=0.0, lu=1.0, ll=1.0, mw=1.0, ears=1.0, crown=1.0, neck=1.0, musc=0.0)

def plane(p, n, o):
    n = np.asarray(n, float); n = n / np.linalg.norm(n); return (p - np.asarray(o, float)) @ n

def bump(p, c, r, R=None):
    """smooth compact bump (1 at the centre, 0 outside the ellipsoid of radii r)"""
    q = p - np.asarray(c, float)
    if R is not None: q = q @ R
    t = np.clip(1 - ((q / np.asarray(r, float)) ** 2).sum(1), 0, 1)
    return t * t * (3 - 2 * t)

def nose_sdf(p, g, f):
    nl = g['nl'] * (1 - 0.14 * f); nw = g['nw'] * (1 - 0.12 * f); nb = g['nb']
    tz = -0.031 * nl ** 0.7 - 0.0025 * g['ntip']; ty = -0.1055 - 0.0035 * nb - 0.006 * (nl - 1)
    top = np.array([0, -0.083, 0.008]); tip = np.array([0, ty, tz])
    ax_ = tip - top; L = np.linalg.norm(ax_); u = ax_ / L
    q = p - top; t = np.clip(q @ u, 0, L) / L
    wid = (0.0042 + 0.0066 * t ** 1.4) * nw
    perp = q - np.outer(q @ u, u)
    side = np.abs(perp[:, 0]) - wid
    nn = np.array([0, -u[2], u[1]])
    if nn[1] > 0: nn = -nn
    fr = perp @ nn - (0.0048 + 0.0026 * t) * (1 + 0.12 * nb)
    nose = smax(smax(side, fr, 0.0045), smax(-(q @ u) - 0.004, (q @ u) - L + 0.003, 0.004), 0.004)
    nose = smin(nose, ell(p, tip + np.array([0, 0.0042, 0.0012]), (0.0068 * nw, 0.0066, 0.0062)), 0.0045)
    for s in (-1, 1): nose = smin(nose, ell(p, (s * 0.0092 * nw, ty + 0.0125, tz - 0.0005), (0.0062 * nw, 0.006, 0.0052)), 0.005)
    if g['nh'] > 0: nose = smin(nose, ell(p, (0, -0.0955 - 0.0022 * g['nh'], -0.012), (0.0045, 0.005, 0.008)), 0.004 * g['nh'] + 1e-4)
    nose = smax(nose, ell(p, (0, -0.09, -0.012), (0.03, 0.04, 0.04)), 0.004)
    return nose

def head_sdf(p, I, ears=True):
    g = dict(BASE_ID); g.update(I or {})
    f = g['f']; fw = g['facew'] * (1 - 0.04 * f); ly = g['facel'] * (1 - 0.06 * f); jw = g['jaw'] * (1 - 0.2 * f); age = g['age']; fat = g['fat']; cw = g['crown']; mu = g['musc']
    # ---- base volumes (silhouette)
    d = ell(p, (0, 0.012, 0.026), (0.0735 * cw * (1 - 0.03 * f), 0.093 * cw, 0.086 * cw))
    fm = ell(p, (0, -0.02, 0.008 + 0.003 * g['fh']), (0.0655 * fw, 0.064, 0.07))
    fm = smax(fm, plane(p, (0, -1, 0.1), (0, -0.0845, 0)), 0.022)
    d = smin(d, fm, 0.025)
    jx = 0.047 * jw * fw + 0.006 * fat; cz = -0.097 * ly
    lw = ell(p, (0, -0.028, -0.062 * ly), (jx, 0.058, 0.044 * ly))
    for s in (-1, 1): lw = smin(lw, cap(p, (s * jx * 0.95, -0.004, -0.07 * ly), (s * 0.013 * g['chinw'], -0.072, cz), 0.012 + 0.002 * mu), 0.024)
    lw = smin(lw, ell(p, (0, -0.074, cz + 0.006), (0.022 * g['chinw'] * (1 - 0.2 * f), 0.018, 0.016)), 0.02)
    lw = smax(lw, plane(p, (0, 0.25, -1), (0, 0, cz - 0.01)), 0.012)
    d = smin(d, lw, 0.03)
    d = smin(d, ell(p, (0, -0.064, -0.054), (0.03 * g['mw'] ** 0.5, 0.027, 0.028)), 0.022)       # tooth barrel
    if fat > 0:
        for s in (-1, 1): d = smin(d, ell(p, (s * 0.042, -0.05, -0.05), (0.024, 0.026, 0.028)), 0.02 * fat + 1e-4)
        d = smin(d, ell(p, (0, -0.05, -0.11 * ly), (0.042, 0.04, 0.022)), 0.03 * fat + 1e-4)
    if ears:
        es = g['ears']
        for s in (-1, 1): d = smin(d, ell(p, (s * 0.0725, 0.012, -0.006), (0.0085 * es, 0.0155 * es, 0.026 * es), rotm(0, s * 0.28, 0)), 0.006)
    nk = g['neck'] * (1 - 0.18 * f) * (1 + 0.15 * mu) + 0.12 * fat
    d = smin(d, cap(p, (0, 0.014, -0.075), (0, 0.026, -0.26), 0.054 * nk), 0.018)
    # ---- features as surface offsets (metres outward)
    off = np.zeros(len(p))
    br = (0.0042 - 0.0026 * f) * g['brow']
    for s in (-1, 1):
        off += br * bump(p, (s * 0.03, -0.085, 0.021), (0.026, 0.02, 0.009), rotm(0, s * 0.12, 0))
        off += (0.0022 + 0.0025 * g['cheek']) * bump(p, (s * 0.054 * fw, -0.05, -0.018 + 0.004 * g['cheek']), (0.02, 0.03, 0.014))
        off -= 0.0062 * bump(p, (s * EYE[0], EYE[1] - 0.014, EYE[2] + 0.001), (0.019, 0.02, 0.0135))       # sockets
    lu = g['lu'] * (1 + 0.25 * f); ll = g['ll'] * (1 + 0.25 * f); mw = g['mw']
    off += 0.0017 * lu * bump(p, (0, MOUTH_Y, MOUTH_Z + 0.0055), (0.026 * mw, 0.02, 0.0065))
    off += 0.0022 * ll * bump(p, (0, MOUTH_Y, MOUTH_Z - 0.0066), (0.023 * mw, 0.02, 0.0075))
    off += 0.0025 * f * bump(p, (0, -0.06, -0.04), (0.06, 0.04, 0.03))
    off -= 0.0022 * bump(p, (0, MOUTH_Y, MOUTH_Z - 0.0145), (0.016, 0.02, 0.004))                       # under the lower lip
    off += (0.0018 + 0.003 * g['chin']) * bump(p, (0, -0.088, cz + 0.008), (0.024 * g['chinw'], 0.02, 0.016))
    if age > 0:
        for s in (-1, 1):
            off += 0.004 * age * bump(p, (s * 0.04, -0.056, -0.084 * ly), (0.018, 0.03, 0.016))        # jowls
            off += 0.0025 * age * bump(p, (s * 0.024, -0.09, -0.046), (0.008, 0.02, 0.014))           # nasolabial pads
            off -= 0.004 * age * bump(p, (s * 0.075, -0.045, 0.03), (0.014, 0.03, 0.02))              # temples
    d = d - off
    d = smin(d, nose_sdf(p, g, f), 0.006)
    return d


# ------------------------------------------------------------------ the body (world frame, feet on z = 0, facing -Y)
HEAD_O = np.array([0.0, 0.0, 1.632])      # head-local origin (eye level) in the world
BASE_B = dict(f=0.0, musc=0.0, fat=0.0, thin=0.0, old=0.0)

def joints(B=None):
    """joint positions for a body variant (metres, world). Arms in a 45 degree A pose."""
    b = dict(BASE_B); b.update(B or {})
    f, mu, fat, th = b['f'], b['musc'], b['fat'], b['thin']
    J = {}
    J['hips'] = np.array([0, 0.005, 0.95 - 0.02 * f]); J['spine'] = np.array([0, 0.01, 1.08]); J['chest'] = np.array([0, 0.015, 1.25])
    J['neck'] = np.array([0, 0.02, 1.47 - 0.01 * f]); J['head'] = np.array([0, 0.018, 1.56])
    sx = 0.19 - 0.03 * f + 0.01 * mu + 0.004 * fat - 0.006 * th
    for s, k in ((1, 'L'), (-1, 'R')):
        J['clav' + k] = np.array([s * 0.03, 0.0, 1.435 - 0.01 * f])
        sh = np.array([s * sx, 0.02, 1.41 - 0.015 * f]); J['uarm' + k] = sh
        dr = np.array([s * 0.64, -0.06, -0.766]); dr /= np.linalg.norm(dr)
        J['farm' + k] = sh + dr * (0.29 - 0.012 * f); J['hand' + k] = J['farm' + k] + dr * (0.255 - 0.01 * f)
        J['tip' + k] = J['hand' + k] + dr * 0.17
        hx = 0.088 + 0.012 * f + 0.008 * fat
        J['thigh' + k] = np.array([s * hx, 0.01, 0.92 - 0.02 * f]); J['shin' + k] = np.array([s * (hx + 0.005), 0.0, 0.49])
        J['foot' + k] = np.array([s * (hx + 0.012), 0.03, 0.085]); J['toe' + k] = np.array([s * (hx + 0.02), -0.12, 0.02])
    return J

def limb(p, a, b, r1, r2, k=0.0):
    return cap(p, a, b, r1, r2)

def body_sdf(p, B=None, head=True, hands=True):
    b = dict(BASE_B); b.update(B or {})
    f, mu, fat, th = b['f'], b['musc'], b['fat'], b['thin']
    J = joints(b)
    m = 1 + 0.12 * mu - 0.08 * th
    # torso: rib cage, abdomen, pelvis, chest, back
    rib = ell(p, (0, 0.012, 1.28), ((0.152 - 0.03 * f) * m + 0.01 * fat, 0.102 - 0.008 * f + 0.006 * mu, 0.16))
    ab = ell(p, (0, 0.006 - 0.012 * fat, 1.08), ((0.122 - 0.022 * f) + 0.035 * fat - 0.006 * th, 0.086 + 0.045 * fat - 0.006 * f, 0.13))
    pel = ell(p, (0, 0.012, 0.95), ((0.132 + 0.036 * f) + 0.02 * fat, 0.095 + 0.008 * f + 0.015 * fat, 0.1))
    d = smin(smin(rib, ab, 0.06), pel, 0.06)
    # shoulders: trapezius slope and deltoids
    for s, k in ((1, 'L'), (-1, 'R')):
        sh = J['uarm' + k]
        d = smin(d, cap(p, (s * 0.03, 0.03, 1.44), sh + np.array([-s * 0.01, 0.005, 0.02]), 0.05 * m, 0.045 * m), 0.04)
        d = smin(d, ell(p, sh + np.array([s * 0.008, 0, -0.02]), (0.052 * m, 0.055 * m, 0.07)), 0.03)
        # pecs / bust
        if f > 0: d = smin(d, ell(p, (s * 0.06, -0.07, 1.265), (0.05, 0.042, 0.048)), 0.035)
        if f < 1: d = smin(d, ell(p, (s * 0.07, -0.062, 1.3), (0.078 * m, 0.04 + 0.01 * mu, 0.058)), 0.035)
        # glutes
        d = smin(d, ell(p, (s * 0.068, 0.068 + 0.01 * f, 0.885), (0.07 + 0.016 * f, 0.058 + 0.012 * f, 0.085)), 0.04)
        # arms
        a, e, w = J['uarm' + k], J['farm' + k], J['hand' + k]
        d = smin(d, cap(p, a, e, (0.05 - 0.008 * f) * m + 0.01 * fat, (0.04 - 0.006 * f) * m + 0.006 * fat), 0.03)
        d = smin(d, cap(p, e, w, (0.04 - 0.006 * f) * m + 0.005 * fat, 0.028 - 0.004 * f), 0.02)
        if mu > 0: d = smin(d, ell(p, e + (w - e) * 0.25 + np.array([0, -0.01, 0]), (0.03, 0.03, 0.05)), 0.02 * mu + 1e-4)
        if hands:
            dr = (w - e) / np.linalg.norm(w - e)
            side = np.cross(dr, np.array([0, 1.0, 0])); side /= np.linalg.norm(side)
            nrm = np.cross(side, dr)
            hs = 1 - 0.08 * f
            palm = w + dr * 0.05 * hs
            d = smin(d, ell(p, palm, (0.045 * hs, 0.045 * hs, 0.06 * hs), np.stack([side, nrm, dr], 1)), 0.015)
            d = smin(d, ell(p, palm + dr * 0.065 * hs + nrm * 0.004, (0.04 * hs, 0.016 * hs, 0.045 * hs), np.stack([side, nrm, dr], 1)), 0.012)
            tb = w + dr * 0.03 - s * side * 0.0 + nrm * -0.03
            d = smin(d, cap(p, w + dr * 0.025 - nrm * 0.012, w + dr * 0.075 - nrm * 0.042, 0.012 * hs, 0.01 * hs), 0.01)
        # legs
        h, kn, an, to = J['thigh' + k], J['shin' + k], J['foot' + k], J['toe' + k]
        d = smin(d, cap(p, h + np.array([s * 0.008, 0, 0.0]), kn, (0.088 + 0.006 * f) * m + 0.02 * fat, 0.054 * m + 0.006 * fat), 0.04)
        d = smin(d, cap(p, kn, an, 0.05 * m + 0.004 * fat, 0.033), 0.025)
        d = smin(d, ell(p, kn + (an - kn) * 0.28 + np.array([0, 0.03, 0]), (0.045 * m, 0.045 * m, 0.09)), 0.03)      # calf
        ft = box(p, (an[0], -0.045, 0.035), (0.042 - 0.004 * f, 0.12 - 0.008 * f, 0.034), rad=0.03)
        ft = smax(ft, plane(p, (0, -0.35, 1), (0, -0.16, 0.045)), 0.02)
        d = smin(d, ft, 0.03)
    # neck stub (the head mesh brings its own neck)
    d = smin(d, cap(p, (0, 0.02, 1.4), (0, 0.022, 1.52), (0.056 - 0.01 * f) * (1 + 0.15 * mu) + 0.008 * fat), 0.03)
    if head:
        d = smin(d, head_sdf(p - HEAD_O, {'f': f}), 0.01)
    return d
