"""Nil Kervancisi v33 - build the whole character kit and export one GLB.
usage:  python3 build33.py OUT.glb [--quick]
Everything is generated: distance-field sculpts -> QuadriFlow quads (cached) -> trait shape keys (identities and body
types, baked by the game at load) -> one shared armature with procedural weights -> parts (face kit, hair, clothes,
props) -> actions -> glTF. Colours are palette slots (COLOR_0: r = slot/31, g = ink outline, b = tone, a = fx/7)."""
import sys, os, time, math, json, inspect
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np
from sdf33 import *
import mesh33 as M, rig33 as R, face33 as FK

T0 = time.time()
def log(*a): print('[%6.1fs]' % (time.time() - T0), *a, flush=True)

SLOTS = ['skin', 'lips', 'hair', 'brow', 'white', 'iris', 'ink', 'mouth', 'teeth', 'hl', 'cloth', 'trim', 'c1', 'c2', 'c3', 'c4',
         'gold', 'band', 'leather', 'wood', 'metal', 'p1', 'p2', 'linen', 'hide', 'beard', 'skin2']
FX = {'none': 0, 'hair': 1, 'beads': 2, 'spots': 3, 'pleat': 4, 'grain': 5}

def clean():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    for c in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions, bpy.data.materials): [c.remove(x) for x in list(c)]

# ------------------------------------------------------------------ trait tables
HEAD_TRAITS = {
    'f': dict(f=1), 'jaw': dict(jaw=1.22, musc=0.6), 'jawn': dict(jaw=0.84, chinw=0.82), 'chin': dict(chin=1.2), 'chinr': dict(chin=-1.0),
    'cheek': dict(cheek=1.3), 'fat': dict(fat=1), 'age': dict(age=1), 'nl': dict(nl=1.3), 'ns': dict(nl=0.76, nw=0.86), 'nw': dict(nw=1.35),
    'nh': dict(nh=1.2), 'nb': dict(nb=1.3), 'long': dict(facel=1.12, facew=0.94), 'round': dict(facel=0.92, facew=1.08), 'lips': dict(lu=1.45, ll=1.4),
    'lipt': dict(lu=0.55, ll=0.62), 'brow': dict(brow=1.9), 'crown': dict(crown=1.06), 'ears': dict(ears=1.28),
}
BODY_TRAITS = {'f': dict(f=1), 'musc': dict(musc=1), 'fat': dict(fat=1), 'thin': dict(thin=1)}

def src(*fns): return ''.join(inspect.getsource(f) for f in fns)

# ------------------------------------------------------------------ meshes as plain arrays
class Mesh:
    """V (n,3) world, F list of polys, per-vertex slot/out/tone/fx, weights (n, len(bones)), shape keys {name: V}, masks"""
    def __init__(self, name, V, F, slot, out=1, tone=1.0, fx=0):
        self.name = name; self.V = np.asarray(V, float); self.F = [list(f) for f in F]; n = len(self.V)
        self.slot = self._arr(slot, n, object); self.out = self._arr(out, n, float); self.tone = self._arr(tone, n, float); self.fx = self._arr(fx, n, float)
        self.W = None; self.keys = {}; self.attrs = {}; self.extras = {}
    @staticmethod
    def _arr(v, n, dt):
        if isinstance(v, (str, int, float, np.floating)): return np.array([v] * n, dtype=dt)
        return np.asarray(v, dtype=dt)
    def weights(self, W, names):
        full = np.zeros((len(self.V), len(R.BONES)))
        for j, nme in enumerate(names): full[:, R.BONES.index(nme)] += W[:, j]
        self.W = full; return self
    @staticmethod
    def from_part(name, P):
        V, F, S, O, T, X, W, names = P.arrays()
        m = Mesh(name, V, F, S, O, T, X); m.weights(W, names); return m

def ob_arrays(ob):
    return M.verts(ob), [list(p.vertices) for p in ob.data.polygons]

def neighbours_arr(n, F):
    nb = [set() for _ in range(n)]
    for f in F:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]; nb[a].add(b); nb[b].add(a)
    return [list(s) for s in nb]

def smoothW(W, nb, it=3, lam=0.5):
    for _ in range(it):
        A = np.array([W[l].mean(0) if l else W[i] for i, l in enumerate(nb)]); W = W * (1 - lam) + A * lam
    return W

# ------------------------------------------------------------------ the head
HEAD_LO, HEAD_HI = (-0.1, -0.15, -0.28), (0.1, 0.125, 0.135)
def build_head():
    warp, unwarp = M.warp_fns((0, -0.075, -0.02), 0.075, 1.55)
    key = src(head_sdf, nose_sdf, bump) + 'v3f1050'
    ob = M.cached_mesh('head', key, lambda: M.sdf_mesh('head', lambda p: head_sdf(p, {}), (-0.11, -0.17, -0.29), (0.11, 0.13, 0.14), h=0.0022, faces=1050, unwarp=unwarp))
    V, F = ob_arrays(ob); bpy.data.objects.remove(ob)
    log('head base', len(V), 'verts', len(F), 'faces')
    m = Mesh('head', V + HEAD_O, F, 'skin', out=0.62)
    nb = neighbours_arr(len(V), F)
    for k, I in HEAD_TRAITS.items():
        Vt = M.cached_array('head_' + k, key + json.dumps(I), lambda I=I: morph_arr(V, nb, lambda p: head_sdf(p, I)))
        m.keys['h_' + k] = Vt + HEAD_O
    # colours: lips
    p = V; x, y, z = p.T
    lipm = (np.abs(z - MOUTH_Z) < 0.0105 - 0.25 * np.abs(x)) & (y < -0.088) & (np.abs(x) < 0.023)
    m.slot[lipm] = 'lips'
    # masks for beards and cropped hair (shells built by the game on the baked head)
    face_front = y < 0.035
    beard = np.clip(sstep(-0.02, -0.04, z) * sstep(0.06, 0.03, y) * (1 - sstep(MOUTH_Z + 0.004, MOUTH_Z - 0.004, z) * sstep(0.015, 0.009, np.abs(x)) * (y < -0.07)), 0, 1)
    beard *= (1 - sstep(-0.13, -0.15, z))                                       # not on the neck
    must = sstep(MOUTH_Z + 0.004, MOUTH_Z + 0.009, z) * sstep(MOUTH_Z + 0.02, MOUTH_Z + 0.015, z) * (y < -0.08) * sstep(0.028, 0.022, np.abs(x))
    beard = np.maximum(beard * (1 - lipm), must)
    m.attrs['_BEARD'] = beard.astype(np.float32)
    hl = 0.045 - 0.04 * sstep(-0.02, 0.06, y)       # hair line height (front high, sides lower)
    crop = sstep(hl - 0.004, hl + 0.006, z) * (1 - sstep(0.07, 0.085, np.abs(x)) * sstep(0.0, -0.03, y)) * (np.abs(x) < 0.081)
    crop = np.maximum(crop, sstep(-0.05, -0.03, z) * sstep(0.02, 0.05, y))      # the back of the head down to the nape
    crop *= sstep(-0.075, -0.06, z)
    ears = (np.abs(x) > 0.064) & (np.abs(y - 0.012) < 0.02) & (np.abs(z + 0.006) < 0.03)
    crop[ears] = 0
    m.attrs['_HAIR'] = crop.astype(np.float32)
    # weights
    W, names = head_weights(V)
    W = smoothW(W, nb, 2, 0.4)
    m.weights(W, names)
    m.nb = nb
    return m

def morph_arr(V0, nb, sdf, smooth=3):
    V1 = M.project(V0, sdf, 8); D = V1 - V0
    for _ in range(smooth):
        D = 0.5 * D + 0.5 * np.array([D[l].mean(0) if l else D[i] for i, l in enumerate(nb)])
    return M.project(V0 + D, sdf, 5)

def head_weights(p):
    x, y, z = p.T
    names = ['chest', 'neck', 'head', 'jaw', 'mouth.L', 'mouth.R', 'brow.L', 'brow.R']
    W = np.zeros((len(p), len(names)))
    hd = np.where(y < -0.02, sstep(-0.17, -0.1, z), sstep(-0.13, -0.06, z))
    ch = sstep(-0.21, -0.27, z)
    # jaw: below the line from the mouth to the jaw hinge, in front of the neck
    zsep = MOUTH_Z + (y - MOUTH_Y) * ((-0.03 - MOUTH_Z) / (0.004 - MOUTH_Y))
    jw = sstep(zsep + 0.0025, zsep - 0.0045, z) * sstep(0.03, 0.005, y) * hd
    jw *= 1 - sstep(-0.118, -0.14, z) * sstep(-0.05, -0.02, y)
    mL = 0.8 * FK_bump(p, (0.0215, MOUTH_Y, MOUTH_Z), (0.011, 0.03, 0.0105)); mR = 0.8 * FK_bump(p, (-0.0215, MOUTH_Y, MOUTH_Z), (0.011, 0.03, 0.0105))
    bL = 0.55 * FK_bump(p, (0.031, -0.09, 0.024), (0.022, 0.03, 0.014)); bR = 0.55 * FK_bump(p, (-0.031, -0.09, 0.024), (0.022, 0.03, 0.014))
    rest = np.clip(1 - mL - mR - bL - bR, 0, 1)
    W[:, 3] = jw * rest; W[:, 2] = (hd - jw).clip(0) * rest; W[:, 1] = (1 - hd) * (1 - ch) * rest; W[:, 0] = (1 - hd) * ch * rest
    W[:, 4] = mL; W[:, 5] = mR; W[:, 6] = bL; W[:, 7] = bR
    return W, names

def FK_bump(p, c, r):
    q = (p - np.asarray(c)) / np.asarray(r); t = np.clip(1 - (q * q).sum(1), 0, 1); return t * t * (3 - 2 * t)

# ------------------------------------------------------------------ the body
def build_body():
    key = src(body_sdf, joints) + 'b800'
    ob = M.cached_mesh('body', key, lambda: M.sdf_mesh('body', lambda p: body_sdf(p, {}, head=False), (-0.62, -0.32, -0.03), (0.62, 0.26, 1.62), h=0.006, voxel=0.012, faces=800))
    V, F = ob_arrays(ob); bpy.data.objects.remove(ob)
    log('body base', len(V), 'verts', len(F), 'faces')
    m = Mesh('body', V, F, 'skin'); nb = neighbours_arr(len(V), F)
    W, names = R.body_weights(V)
    W = smoothW(W, nb, 6, 0.5)
    m.weights(W, names); m.nb = nb
    # trait keys: pre-move by the joint changes (linear blend), then project on the variant's field
    P0 = R.bone_points({})
    for k, B in BODY_TRAITS.items():
        def mk(B=B):
            P1 = R.bone_points(B); D = np.zeros_like(V)
            for j, nme in enumerate(names):
                if nme in P1: D += W[:, j:j + 1] * (P1[nme][0] - P0[nme][0])[None, :]
            return morph_arr(V + D, nb, lambda p: body_sdf(p, B, head=False), 2)
        m.keys['b_' + k] = M.cached_array('body_' + k, key + json.dumps(B), mk)
    return m

# ------------------------------------------------------------------ assemble Blender objects
MAT = None
def to_object(m, arm):
    me = bpy.data.meshes.new(m.name); me.from_pydata(m.V.tolist(), [], m.F); me.update()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(m.name, me); bpy.context.scene.collection.objects.link(ob)
    n = len(m.V)
    col = np.zeros((n, 4), np.float32)
    col[:, 0] = [SLOTS.index(s) / 31.0 for s in m.slot]; col[:, 1] = m.out; col[:, 2] = m.tone; col[:, 3] = m.fx / 7.0
    at = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT'); at.data.foreach_set('color', col.ravel())
    me.color_attributes.active_color = at
    try: me.color_attributes.render_color_index = me.color_attributes.active_color_index
    except Exception: pass
    for k, a in m.attrs.items():
        aa = me.attributes.new(k, 'FLOAT', 'POINT'); aa.data.foreach_set('value', np.asarray(a, np.float32))
    # weights
    if m.W is not None:
        W = m.W.copy(); W /= np.maximum(W.sum(1, keepdims=True), 1e-12); idx = np.argsort(-W, axis=1)[:, :4]; keep = np.zeros_like(W); rows = np.arange(n)[:, None]
        keep[rows, idx] = W[rows, idx]; keep[keep < 0.015] = 0; s = keep.sum(1, keepdims=True); s[s == 0] = 1; keep /= s
        for j, nme in enumerate(R.BONES):
            nz = np.nonzero(keep[:, j])[0]
            if not len(nz): continue
            vg = ob.vertex_groups.new(name=nme)
            for v in nz: vg.add([int(v)], float(keep[v, j]), 'REPLACE')
    if m.keys:
        ob.shape_key_add(name='Basis')
        for k, V in m.keys.items():
            sk = ob.shape_key_add(name=k); sk.data.foreach_set('co', np.asarray(V, float).ravel()); sk.value = 0
    me.materials.append(MAT)
    R.skin_to(ob, arm)
    ob['c33'] = json.dumps(m.extras)
    return ob

def main():
    global MAT
    out = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith('.glb') else os.path.join(HERE, '..', 'chars33.glb')
    clean()
    MAT = bpy.data.materials.new('c33')
    arm = R.make_armature('Rig')
    meshes = []
    head = build_head(); meshes.append(head)
    body = build_body(); meshes.append(body)
    meshes.append(lod_mesh('head_lo', head, lambda p: head_sdf(p - HEAD_O, {}), (np.array(HEAD_LO) + HEAD_O, np.array(HEAD_HI) + HEAD_O), 380, h=0.003))
    meshes.append(lod_mesh('body_lo', body, lambda p: body_sdf(p, {}, head=False), ((-0.62, -0.32, -0.03), (0.62, 0.26, 1.62)), 330, h=0.008))
    for s in (1, -1):
        meshes.append(Mesh.from_part('eyeball' + ('L' if s > 0 else 'R'), FK.eyeball(s)))
        meshes.append(Mesh.from_part('uplid' + ('L' if s > 0 else 'R'), FK.lid(s, True)))
        meshes.append(Mesh.from_part('lowlid' + ('L' if s > 0 else 'R'), FK.lid(s, False)))
    meshes.append(merge_parts('brow_m', [FK.brow(1, 'm'), FK.brow(-1, 'm')]))
    meshes.append(merge_parts('brow_f', [FK.brow(1, 'f'), FK.brow(-1, 'f')]))
    meshes.append(merge_parts('wing', [FK.wing(1), FK.wing(-1)]))
    meshes.append(Mesh.from_part('mouth', FK.mouth()))
    follow([m for m in meshes[2:] if not m.name.startswith(('eyeball', 'uplid', 'lowlid'))], head)
    import anim33, parts33 as PT
    anim33.make_actions(arm)
    G, Mx = idle_frames(arm)
    extra = []
    for nm in PT.HAIR: extra.append(piece_mesh(PT.hair_piece(nm), head, body, Mx))
    extra.append(piece_mesh(PT.band('band'), head, body, Mx)); extra.append(piece_mesh(PT.band('band_low', 0.036, 0.012, 0.002, 0.004), head, body, Mx))
    extra.append(piece_mesh(PT.band('band_puff', 0.05, 0.035, 0.03, 0.0045), head, body, Mx))
    for f in (PT.tails, PT.lotus, PT.cone, PT.beard_point, PT.beard_long, PT.amulet): extra.append(piece_mesh(f(), head, body, Mx))
    extra.append(piece_mesh(PT.earrings('stud'), head, body, Mx)); extra.append(piece_mesh(PT.earrings('hoop'), head, body, Mx))
    body_lo = next(m for m in meshes if m.name == 'body_lo')
    for nm in PT.CLOTH:
        cm = piece_mesh(PT.cloth_piece(nm), head, body, Mx)
        # body skin that this piece covers is not drawn (no poke-through): deep inside the cloth volume, above the legs
        fn = PT.CLOTH[nm][0]; hide = {}
        for bm in (body, body_lo):
            d = fn(bm.V); z = bm.V[:, 2]
            thr = -0.004 if nm in ('collar', 'sash', 'straps') else -0.006
            hide[bm.name] = np.nonzero((d < thr) & (z > 0.97))[0].tolist()
        cm.extras['hide'] = hide
        extra.append(cm)
    for nm in ('armband', 'bracelet'): extra.append(piece_mesh(PT.rings(nm), head, body, Mx))
    for nm in PT.PROPS:
        pc = PT.prop(nm, G)
        if pc is not None: extra.append(piece_mesh(pc, head, body, Mx))
    meshes += [m for m in extra if m is not None]
    meshes.append(merge_parts('brow_old', [FK.brow(1, 'old'), FK.brow(-1, 'old')]))
    meshes.append(merge_parts('brow_flat', [FK.brow(1, 'flat'), FK.brow(-1, 'flat')]))
    follow([meshes[-1], meshes[-2]], head)
    log('meshes ready', len(meshes))
    obs = [to_object(m, arm) for m in meshes]
    bpy.context.scene['c33'] = json.dumps(kit_meta())
    export(out)
    log('exported', out, os.path.getsize(out))

def lod_mesh(name, hi, sdf, box, faces, h):
    """a low-detail copy for the town: own QuadriFlow topology, weights/colours/traits/masks from the detailed mesh"""
    from scipy.spatial import cKDTree
    lo, hh = box
    ob = M.cached_mesh(name, name + str(faces) + src(head_sdf, nose_sdf, bump, body_sdf), lambda: M.sdf_mesh(name, sdf, lo, hh, h=h, faces=faces))
    V, F = ob_arrays(ob); bpy.data.objects.remove(ob)
    d, idx = cKDTree(hi.V).query(V, k=4); w = 1 / (d + 1e-4); w /= w.sum(1, keepdims=True)
    m = Mesh(name, V, F, hi.slot[idx[:, 0]], hi.out[idx[:, 0]], hi.tone[idx[:, 0]], hi.fx[idx[:, 0]])
    m.W = (hi.W[idx] * w[:, :, None]).sum(1)
    for k, a in hi.attrs.items(): m.attrs[k] = (np.asarray(a)[idx] * w).sum(1).astype(np.float32)
    for k, Vk in hi.keys.items(): m.keys[k] = V + ((Vk - hi.V)[idx] * w[:, :, None]).sum(1)
    log(name, len(V), 'verts')
    return m

def idle_frames(arm):
    """grip points and rest<-idle matrices for the hands (props are designed hanging in the idle pose)"""
    from mathutils import Matrix
    arm.animation_data.action = bpy.data.actions['idle']; bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
    G = {}; Mx = {}
    for k in 'LR':
        pb = arm.pose.bones['hand.' + k]; b = arm.data.bones['hand.' + k]
        h = np.array(pb.head); t = np.array(pb.tail); G[k] = h + (t - h) / np.linalg.norm(t - h) * 0.07
        Mx['hand.' + k] = np.array(b.matrix_local @ pb.matrix.inverted())
    arm.animation_data.action = None; bpy.context.scene.frame_set(1)
    for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    bpy.context.view_layer.update()
    return G, Mx

def transfer(V, src, k=4):
    from scipy.spatial import cKDTree
    d, idx = cKDTree(src.V).query(V, k=k); w = 1 / (d + 1e-4); w /= w.sum(1, keepdims=True)
    return (src.W[idx] * w[:, :, None]).sum(1)

def piece_mesh(pc, head, body, Mx):
    if pc is None or not pc.V: return None
    V, F, S, O, T, X = pc.arrays()
    rule = pc.rule
    if rule in Mx:
        Mm = Mx[rule]; V = (np.c_[V, np.ones(len(V))] @ Mm.T)[:, :3]
    m = Mesh(pc.name, V, F, S, O, T, X)
    W = np.zeros((len(V), len(R.BONES)))
    if rule.startswith('hand') or rule == 'chest' and pc.name.startswith('p_'):
        W[:, R.BONES.index(rule)] = 1
    elif rule in ('head', 'jaw'):
        Wh = transfer(V, head)
        if rule == 'jaw' or pc.name.startswith(('beard', 'hood', 'hair_long')): W = Wh
        else: W[:, R.BONES.index('head')] = 1
        if pc.name == 'hair_long':
            zl = V[:, 2] - HEAD_O[2]; t = np.clip((-0.07 - zl) / 0.12, 0, 1)
            W = W * (1 - t[:, None]); W[:, R.BONES.index('neck')] += t * 0.4; W[:, R.BONES.index('chest')] += t * 0.6
        if pc.name.startswith(('beard', 'hood')): W = transfer(V, head, 6)
        if pc.name == 'hood':
            zl = V[:, 2] - HEAD_O[2]; t = np.clip((-0.1 - zl) / 0.1, 0, 1)
            W = W * (1 - t[:, None]); W[:, R.BONES.index('chest')] += t
    else:
        W = transfer(V, body, 5)
        if rule == 'skirt':
            z = V[:, 2]; sk = z < 0.98
            for k in 'LR':
                th, sh, ft = R.BONES.index('thigh.' + k), R.BONES.index('shin.' + k), R.BONES.index('foot.' + k)
                W[sk, th] += W[sk, sh] + W[sk, ft]; W[sk, sh] = 0; W[sk, ft] = 0
                mv = W[sk, th] * 0.45; W[sk, th] -= mv; W[sk, R.BONES.index('hips')] += mv
    m.W = W
    follow([m], head if rule in ('head', 'jaw') else body, traits=None if rule not in ('head',) else ['h_f', 'h_crown', 'h_round', 'h_long', 'h_fat', 'h_age', 'h_ears'])
    if rule.startswith('hand'): m.keys = {}
    return m

def kit_meta():
    """bone head deltas per body trait (glTF axes, three's sanitized bone names)"""
    P0 = R.bone_points({}); bd = {}
    for k, B in BODY_TRAITS.items():
        P1 = R.bone_points(B); d = {}
        for n in R.BONES:
            dv = P1[n][0] - P0[n][0]
            if np.abs(dv).max() > 1e-5: d[n.replace('.', '')] = [round(float(dv[0]), 5), round(float(dv[2]), 5), round(float(-dv[1]), 5)]
        bd[k] = d
    return {'bd': bd, 'v': 33}

def merge_parts(name, parts):
    P = FK.Part(name)
    for q in parts:
        for V, F, S, O, T, X, W in zip(q.V, [None] * len(q.V), q.S, q.O, q.T, q.X, q.W): pass
        V, F, S, O, T, X, W, names = q.arrays()
        P.add(V, F, S, O, T, X, {nme: W[:, j] for j, nme in enumerate(names)})
    return Mesh.from_part(name, P)

def follow(meshes, src_mesh, k=4, traits=None):
    """give parts the shape keys of the nearest surface of src (head or body): displacement copied from neighbours"""
    from scipy.spatial import cKDTree
    tree = cKDTree(src_mesh.V)
    for m in meshes:
        d, idx = tree.query(m.V, k=k); w = 1 / (d + 1e-4); w /= w.sum(1, keepdims=True)
        for kname, Vk in src_mesh.keys.items():
            D = Vk - src_mesh.V; Dm = (D[idx] * w[:, :, None]).sum(1)
            if np.abs(Dm).max() < (0.0004 if traits is None else 0.0008): continue
            if traits is not None and kname not in traits: continue
            m.keys[kname] = m.V + Dm

def export(path):
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_skins=True, export_morph=True, export_morph_normal=False,
                              export_animations=True, export_animation_mode='ACTIONS', export_vertex_color='ACTIVE', export_all_vertex_colors=False,
                              export_attributes=True, export_materials='NONE', export_yup=True, export_apply=False, export_def_bones=False,
                              export_optimize_animation_size=True, export_extras=True, export_texcoords=False, export_normals=True,
                              export_force_sampling=True, export_frame_step=1)

if __name__ == '__main__':
    main()
