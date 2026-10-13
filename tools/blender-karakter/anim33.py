"""Nil Kervancisi v33 - body actions for the shared armature (the face is driven live by the game).
Poses are written in world axes of the rest pose (Blender: X = the character's left, -Y = forward, Z = up) and
converted to bone-local quaternions, so the clips read like stage directions. All clips loop unless noted."""
import bpy, math, numpy as np
from mathutils import Quaternion, Matrix, Vector, Euler
import rig33 as R

FPS = 24
D2R = math.pi / 180

def qw(axis, deg): return Quaternion(Vector(axis).normalized(), deg * D2R)

class Pose(dict):
    """bone -> world-axis rotation (Quaternion, applied in the bone's rest frame); '_hips' -> (dx, dy, dz) metres"""
    def rot(self, bone, q):
        self[bone] = q @ self.get(bone, Quaternion()); return self

def base(arm_down=34, elbow=10):
    p = Pose()
    for s, k in ((1, 'L'), (-1, 'R')):
        arm(p, s, down=arm_down, elbow=elbow, fwd=4)
    return p

FOREARM = {}
def hinge(armo, side):
    k = 'L' if side > 0 else 'R'
    b = armo.data.bones['farm.' + k]; d = (b.tail_local - b.head_local).normalized()
    ax = d.cross(Vector((0, -1, 0))).normalized()
    # positive must move the hand forward (-Y)
    test = Quaternion(ax, 0.5) @ d
    if test.y > d.y: ax = -ax
    return ax

ARMO = None
def arm(p, side, down=0, fwd=0, twist=0, elbow=0, wrist=0, out=0, ftwist=0):
    """down: from the 45 degree A pose toward the body; fwd: swing forward; out: away from the body (negative down)
    elbow: bend (hand comes forward/up); wrist: bend the hand up; twist: roll of the upper arm (positive = palm forward)"""
    k = 'L' if side > 0 else 'R'
    # lower the arm toward the body = rotate about the forward axis
    q = qw((0, 1, 0), side * (down - out))
    q = qw((1, 0, 0), -fwd) @ q
    if twist:
        b = ARMO.data.bones['uarm.' + k]; d = (b.tail_local - b.head_local).normalized()
        q = q @ qw(d, -twist * side)
    p['uarm.' + k] = q
    p.pop('farm.' + k, None); p.pop('hand.' + k, None)
    if elbow or ftwist:
        qq = Quaternion(hinge(ARMO, side), elbow * D2R)
        if ftwist:
            b = ARMO.data.bones['farm.' + k]; d = (b.tail_local - b.head_local).normalized(); qq = qq @ qw(d, -ftwist * side)
        p.rot('farm.' + k, qq)
    if wrist: p.rot('hand.' + k, Quaternion(hinge(ARMO, side), wrist * D2R))
    return p

def leg(p, side, fwd=0, knee=0, ankle=0, out=0):
    k = 'L' if side > 0 else 'R'
    q = qw((1, 0, 0), -fwd)
    if out: q = qw((0, 1, 0), -side * out) @ q
    p['thigh.' + k] = q; p.pop('shin.' + k, None); p.pop('foot.' + k, None)
    if knee: p.rot('shin.' + k, qw((1, 0, 0), knee))
    if ankle: p.rot('foot.' + k, qw((1, 0, 0), -ankle))
    return p

def spine(p, bone, fwd=0, side=0, turn=0):
    q = Quaternion()
    if turn: q = qw((0, 0, 1), turn) @ q
    if side: q = qw((0, 1, 0), side) @ q
    if fwd: q = qw((1, 0, 0), fwd) @ q
    return p.rot(bone, q)

def hips(p, dx=0, dy=0, dz=0): p['_hips'] = (dx, dy, dz); return p

# ------------------------------------------------------------------ writing actions
def write_action(armo, name, frames, loop=True):
    """frames: list of (time_seconds, Pose). Keys every bone that any pose touches, with smooth interpolation."""
    act = bpy.data.actions.new(name); act.use_fake_user = True
    armo.animation_data_create(); armo.animation_data.action = act
    touched = sorted(set(b for _, p in frames for b in p if not b.startswith('_')) | set(R.BODY) - {'root'})
    pbs = armo.pose.bones
    for t, p in frames:
        f = 1 + round(t * FPS)
        for b in touched:
            pb = pbs[b]; bone = armo.data.bones[b]
            qw_ = p.get(b, Quaternion())
            Rm = bone.matrix_local.to_3x3()
            ql = (Rm.inverted() @ qw_.to_matrix() @ Rm).to_quaternion()
            pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = ql
            pb.keyframe_insert('rotation_quaternion', frame=f)
        h = p.get('_hips', (0, 0, 0))
        pbh = pbs['hips']; bh = armo.data.bones['hips']
        loc = bh.matrix_local.to_3x3().inverted() @ Vector(h)
        pbh.location = loc; pbh.keyframe_insert('location', frame=f)
    # NLA track so the exporter writes every action
    tr = armo.animation_data.nla_tracks.new(); tr.name = name; st = tr.strips.new(name, 1, act); st.action_frame_end = 1 + round(frames[-1][0] * FPS)
    armo.animation_data.action = None
    act['loop'] = 1 if loop else 0
    return act

def lerp_pose(a, b, t):
    p = Pose()
    for k in set(a) | set(b):
        if k.startswith('_'):
            va = np.array(a.get(k, (0, 0, 0))); vb = np.array(b.get(k, (0, 0, 0))); p[k] = tuple(va + (vb - va) * t)
        else: p[k] = a.get(k, Quaternion()).slerp(b.get(k, Quaternion()), t)
    return p

def cycle(fn, dur, n=None):
    n = n or max(4, round(dur * 8))
    return [(dur * i / n, fn(i / n)) for i in range(n + 1)]

# ------------------------------------------------------------------ the clips
S = math.sin; C = math.cos; TAU = 2 * math.pi

def idle(u, k=1.0):
    w = S(TAU * u)                          # weight shift once per loop
    b = S(TAU * u * 2)                      # two breaths
    p = base()
    hips(p, 0.012 * w * k, 0, -0.002 * abs(w))
    spine(p, 'hips', side=-2.2 * w * k)
    spine(p, 'spine', fwd=1.2 * b, side=1.2 * w * k)
    spine(p, 'chest', fwd=-1.6 * b, side=1.0 * w * k)
    spine(p, 'neck', fwd=1 + 0.8 * b)
    spine(p, 'head', fwd=-1, turn=3 * S(TAU * u + 1) * k, side=1.2 * w)
    for s in (1, -1):
        arm(p, s, down=34 + 1.5 * b, elbow=10 + 2 * b, fwd=4)
        leg(p, s, fwd=0, knee=4 + (3 if s * w < 0 else 0) * abs(w), out=-1.5 * s * w * k)
    return p

def talk(u):
    p = idle(u, 0.4)
    g = S(TAU * u * 2); g2 = S(TAU * u * 3 + 1)
    arm(p, -1, down=12 + 6 * g, fwd=30 + 8 * g2, elbow=72 + 14 * g, twist=-26 + 10 * g2, wrist=-12 + 10 * g2)
    arm(p, 1, down=28 + 3 * g2, fwd=8, elbow=26 + 8 * g)
    spine(p, 'head', fwd=3 * S(TAU * u * 4), turn=5 * S(TAU * u * 1.5))
    spine(p, 'chest', turn=4 * g)
    return p

def happy(u):
    p = idle(u, 0.3)
    j = abs(S(TAU * u * 2))
    hips(p, 0, 0, 0.006 * j)
    spine(p, 'chest', fwd=-6 - 3 * j)
    spine(p, 'head', fwd=-9 - 4 * j, side=4 * S(TAU * u))
    spine(p, 'neck', fwd=-3)
    for s in (1, -1): arm(p, s, down=8 - 4 * j, fwd=24, elbow=58 + 10 * j, twist=-6)
    return p

def angry(u):
    p = idle(u, 0.2)
    sh = S(TAU * u * 2)
    spine(p, 'spine', fwd=6); spine(p, 'chest', fwd=5)
    spine(p, 'head', fwd=6, turn=12 * sh)
    spine(p, 'neck', fwd=4)
    arm(p, -1, down=8, fwd=42 + 10 * abs(sh), elbow=78 - 22 * abs(S(TAU * u * 2)), twist=-18)
    arm(p, 1, down=26, fwd=-2, elbow=26)
    return p

def think(u):
    p = idle(u, 0.3)
    b = S(TAU * u)
    arm(p, -1, down=10, fwd=30, elbow=122 + 3 * b, twist=-12, wrist=-15)     # hand to chin
    arm(p, 1, down=16, fwd=22, elbow=98, twist=-62)                           # across the waist, supporting the elbow
    spine(p, 'head', fwd=6, side=-7 + 2 * b, turn=-6)
    spine(p, 'chest', fwd=2)
    return p

def wave(u):
    p = idle(u, 0.3)
    w = S(TAU * u * 2)
    arm(p, -1, down=-48, fwd=16, elbow=82 + 12 * w, twist=68 + 14 * w)
    spine(p, 'head', side=4, turn=-4)
    spine(p, 'chest', side=3)
    return p

def bow(u):
    t = min(1, u / 0.35) if u < 0.6 else max(0, 1 - (u - 0.6) / 0.4)
    t = t * t * (3 - 2 * t)
    p = base()
    spine(p, 'hips', fwd=10 * t); spine(p, 'spine', fwd=14 * t); spine(p, 'chest', fwd=10 * t); spine(p, 'head', fwd=10 * t)
    arm(p, -1, down=34 - 16 * t, fwd=4 + 22 * t, elbow=10 + 92 * t, twist=-56 * t)     # hand on the chest
    arm(p, 1, down=34, fwd=4 + 8 * t, elbow=10)
    for s in (1, -1): leg(p, s, fwd=-6 * t, knee=4)
    return p

def walk(u, carry=False):
    a = TAU * u
    p = base()
    sw = S(a)
    hips(p, 0.008 * S(a), 0, 0.012 * abs(C(a)) - 0.008)
    spine(p, 'hips', turn=5 * sw, side=-2 * C(a))
    spine(p, 'spine', fwd=3, turn=-3 * sw); spine(p, 'chest', turn=-4 * sw, fwd=-1)
    spine(p, 'head', turn=2 * sw, fwd=-2)
    for s in (1, -1):
        ph = a if s > 0 else a + math.pi
        th = 24 * S(ph)
        kn = 6 + 42 * max(0, -C(ph)) ** 1.3 + 8 * max(0, S(ph))
        leg(p, s, fwd=th, knee=kn, ankle=-12 * C(ph) + 6)
        if not carry: arm(p, s, down=36, fwd=-20 * S(ph) + 4, elbow=16 + 12 * max(0, -S(ph)))
    if carry:
        arm(p, 1, down=-112, fwd=6, elbow=64, twist=62)
        arm(p, -1, down=34, fwd=6 - 10 * sw, elbow=16)
    return p

def sit(u):
    b = S(TAU * u * 2)
    p = base()
    hips(p, 0, 0.0, -0.4)
    spine(p, 'spine', fwd=4 + b); spine(p, 'chest', fwd=-1 - b)
    spine(p, 'head', turn=6 * S(TAU * u), fwd=2)
    for s in (1, -1):
        leg(p, s, fwd=88, knee=92, ankle=4, out=4)
        arm(p, s, down=26, fwd=34, elbow=48)
    return p

def cheer(u):
    j = abs(S(TAU * u))
    p = base()
    hips(p, 0, 0, 0.03 * j)
    spine(p, 'chest', fwd=-6); spine(p, 'head', fwd=-8)
    for s in (1, -1):
        arm(p, s, down=-104 - 8 * j, fwd=12, elbow=22 + 10 * j, twist=30)
        leg(p, s, knee=8 * (1 - j), ankle=-6 * j)
    return p

def cross(u):
    p = idle(u, 0.4)
    arm(p, 1, down=18, fwd=24, elbow=104, twist=-64)
    arm(p, -1, down=16, fwd=28, elbow=100, twist=-58)
    spine(p, 'head', fwd=-3, side=3 * S(TAU * u)); spine(p, 'chest', fwd=-3)
    return p

def shrug(u):
    t = S(math.pi * min(1, u / 0.8)); t = max(0, t)
    p = idle(u, 0.2)
    for s in (1, -1):
        p.rot('clav.' + ('L' if s > 0 else 'R'), qw((0, 1, 0), -s * 10 * t))
        arm(p, s, down=34 - 14 * t, fwd=8 + 14 * t, elbow=12 + 70 * t, twist=40 * t, wrist=20 * t)
    spine(p, 'head', side=8 * t, fwd=-2 * t)
    return p

def point(u):
    p = idle(u, 0.3)
    b = S(TAU * u)
    arm(p, -1, down=-30, fwd=62 + 2 * b, elbow=12, twist=-10)
    spine(p, 'head', turn=-6, fwd=2); spine(p, 'chest', turn=-6)
    return p

def greet(u):
    """hand to the heart and a small nod (one shot)"""
    t = min(1, u / 0.3) if u < 0.7 else max(0, 1 - (u - 0.7) / 0.3); t = t * t * (3 - 2 * t)
    p = idle(u, 0.2)
    arm(p, -1, down=34 - 16 * t, fwd=4 + 22 * t, elbow=10 + 92 * t, twist=-56 * t)
    spine(p, 'chest', fwd=4 * t); spine(p, 'head', fwd=10 * t * (0.6 + 0.4 * S(math.pi * min(1, u / 0.6))))
    return p

def laugh(u):
    j = abs(S(TAU * u * 3))
    p = happy(u)
    spine(p, 'chest', fwd=4 * j); spine(p, 'head', fwd=6 * j)
    arm(p, 1, down=18, fwd=18, elbow=96, twist=-58)        # a hand to the belly
    return p

def wipe(u):
    t = S(math.pi * u) ** 0.6
    p = idle(u, 0.2)
    arm(p, -1, down=8 - 8 * t, fwd=12 + 30 * t, elbow=20 + 120 * t, twist=-26 * t, wrist=-10 * t)
    spine(p, 'head', fwd=4 * t, side=-5 * t)
    return p

def tap(u):
    p = idle(u, 0.2)
    k = abs(S(TAU * u * 4))
    arm(p, -1, down=16, fwd=34, elbow=74, twist=-30, wrist=24 * k)
    spine(p, 'head', fwd=4, turn=-6)
    return p

def lean(u):
    b = S(TAU * u)
    p = base()
    spine(p, 'hips', fwd=4); spine(p, 'spine', fwd=10 + b); spine(p, 'chest', fwd=6); spine(p, 'head', fwd=-10)
    for s in (1, -1):
        arm(p, s, down=20, fwd=52, elbow=58, twist=-22)
        leg(p, s, fwd=-4, knee=6)
    return p

def scratch(u):
    k = S(TAU * u * 3)
    p = idle(u, 0.2)
    arm(p, -1, down=-40, fwd=34, elbow=136 + 6 * k, twist=26)
    spine(p, 'head', side=-8, fwd=4)
    return p

CLIPS = [
    ('idle', idle, 4.0, True), ('talk', talk, 4.0, True), ('happy', happy, 2.0, True), ('laugh', laugh, 2.0, True), ('angry', angry, 2.0, True),
    ('think', think, 4.0, True), ('wave', wave, 2.0, True), ('bow', bow, 2.4, False), ('greet', greet, 2.0, False), ('walk', walk, 1.0, True),
    ('carry', lambda u: walk(u, True), 1.0, True), ('sit', sit, 4.0, True), ('cheer', cheer, 1.0, True), ('cross', cross, 4.0, True),
    ('shrug', shrug, 1.6, False), ('point', point, 2.0, True), ('wipe', wipe, 2.0, True), ('tap', tap, 2.0, True), ('lean', lean, 3.0, True), ('scratch', scratch, 2.0, True),
]

def make_actions(armo, only=None):
    global ARMO
    ARMO = armo
    for name, fn, dur, loop in CLIPS:
        if only and name not in only: continue
        n = max(8, round(dur * 12))
        frames = [(dur * i / n, fn(i / n)) for i in range(n + 1)]
        write_action(armo, name, frames, loop)
