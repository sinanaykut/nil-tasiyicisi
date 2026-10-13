"""Nil Kervancisi v33 - the shared humanoid armature (31 bones), weights and helpers to pose bones in world axes."""
import bpy, numpy as np, math
from mathutils import Vector, Matrix, Quaternion
from sdf33 import joints, HEAD_O, EYE, MOUTH_Y, MOUTH_Z

FACE = ['jaw', 'eye.L', 'eye.R', 'lid.L', 'lid.R', 'lidlo.L', 'lidlo.R', 'brow.L', 'brow.R', 'mouth.L', 'mouth.R']
BODY = ['root', 'hips', 'spine', 'chest', 'neck', 'head', 'clav.L', 'clav.R', 'uarm.L', 'uarm.R', 'farm.L', 'farm.R', 'hand.L', 'hand.R',
        'thigh.L', 'thigh.R', 'shin.L', 'shin.R', 'foot.L', 'foot.R']
BONES = BODY + FACE
PARENT = {'root': None, 'hips': 'root', 'spine': 'hips', 'chest': 'spine', 'neck': 'chest', 'head': 'neck', 'jaw': 'head',
          'clav.L': 'chest', 'clav.R': 'chest', 'uarm.L': 'clav.L', 'uarm.R': 'clav.R', 'farm.L': 'uarm.L', 'farm.R': 'uarm.R',
          'hand.L': 'farm.L', 'hand.R': 'farm.R', 'thigh.L': 'hips', 'thigh.R': 'hips', 'shin.L': 'thigh.L', 'shin.R': 'thigh.R',
          'foot.L': 'shin.L', 'foot.R': 'shin.R'}
for k in FACE: PARENT.setdefault(k, 'head')

def face_points():
    H = HEAD_O
    P = {'jaw': (H + np.array([0, 0.006, -0.03]), H + np.array([0, -0.07, -0.1]))}
    for s, k in ((1, 'L'), (-1, 'R')):
        e = H + np.array([s * EYE[0], EYE[1], EYE[2]])
        P['eye.' + k] = (e, e + np.array([0, -0.03, 0]))
        P['lid.' + k] = (e, e + np.array([0, -0.025, 0]))
        P['lidlo.' + k] = (e, e + np.array([0, -0.02, 0]))
        b = H + np.array([s * 0.031, -0.091, 0.022])
        P['brow.' + k] = (b, b + np.array([0, -0.02, 0]))
        m = H + np.array([s * 0.021, MOUTH_Y + 0.006, MOUTH_Z])
        P['mouth.' + k] = (m, m + np.array([0, -0.015, 0]))
    return P

def bone_points(B=None):
    J = joints(B); P = {}
    P['root'] = (np.array([0, 0, 0.0]), np.array([0, 0, 0.12]))
    P['hips'] = (J['hips'], J['spine']); P['spine'] = (J['spine'], J['chest']); P['chest'] = (J['chest'], J['neck'])
    P['neck'] = (J['neck'], J['head']); P['head'] = (J['head'], J['head'] + np.array([0, 0, 0.2]))
    for k in 'LR':
        P['clav.' + k] = (J['clav' + k], J['uarm' + k]); P['uarm.' + k] = (J['uarm' + k], J['farm' + k]); P['farm.' + k] = (J['farm' + k], J['hand' + k])
        P['hand.' + k] = (J['hand' + k], J['tip' + k]); P['thigh.' + k] = (J['thigh' + k], J['shin' + k]); P['shin.' + k] = (J['shin' + k], J['foot' + k])
        P['foot.' + k] = (J['foot' + k], J['toe' + k])
    P.update(face_points())
    return P

def make_armature(name='Rig'):
    ad = bpy.data.armatures.new(name); ob = bpy.data.objects.new(name, ad); bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    P = bone_points()
    for n in BONES:
        eb = ad.edit_bones.new(n); h, t = P[n]; eb.head = Vector(h); eb.tail = Vector(t)
        # roll: x axis points to the character's left for the spine and legs, forward-facing bones keep z up
        eb.align_roll(Vector((0, 0, 1)) if abs(t[2] - h[2]) < 0.6 * np.linalg.norm(np.array(t) - np.array(h)) else Vector((0, -1, 0)))
    for n in BONES:
        if PARENT[n]: ad.edit_bones[n].parent = ad.edit_bones[PARENT[n]]
        ad.edit_bones[n].use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob

# --------------------------------------------------------------- posing in armature (world) axes
def set_rot_world(arm, bone, axis, angle, base=None):
    """rotate a pose bone about a world-space axis (through its head); returns the local quaternion"""
    b = arm.data.bones[bone]
    R = b.matrix_local.to_3x3()              # rest orientation in armature space
    qw = Quaternion(Vector(axis).normalized(), angle)
    ql = (R.inverted() @ qw.to_matrix() @ R).to_quaternion()
    if base is not None: ql = base @ ql
    return ql

# --------------------------------------------------------------- weights
def seg_dist(P, a, b):
    a = np.asarray(a); b = np.asarray(b); ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + np.outer(t, ab)), axis=1), t

def set_weights(ob, W, names):
    """W: (n_verts, n_bones) dense weights in the order of names; keeps the 4 largest per vertex."""
    W = np.asarray(W, float).copy()
    idx = np.argsort(-W, axis=1)[:, :4]
    keep = np.zeros_like(W); rows = np.arange(len(W))[:, None]; keep[rows, idx] = W[rows, idx]
    keep[keep < 0.02] = 0
    s = keep.sum(1, keepdims=True); s[s == 0] = 1; keep /= s
    for g in list(ob.vertex_groups): ob.vertex_groups.remove(g)
    for j, n in enumerate(names):
        col = keep[:, j]; nz = np.nonzero(col)[0]
        if not len(nz): continue
        vg = ob.vertex_groups.new(name=n)
        for i in nz: vg.add([int(i)], float(col[i]), 'REPLACE')

def skin_to(ob, arm):
    for m in [m for m in ob.modifiers if m.type == 'ARMATURE']: ob.modifiers.remove(m)
    md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = arm
    ob.parent = arm

def body_weights(V, B=None):
    """nearest bone segment with anatomical gates (hard), the caller blurs the result over the mesh."""
    P = bone_points(B); names = [n for n in BODY if n not in ('root', 'head')]
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    D = np.full((len(V), len(names)), 9.0)
    for j, n in enumerate(names):
        a, b = P[n]; a = np.asarray(a); b = np.asarray(b); ab = b - a; L = np.linalg.norm(ab)
        u = ((V - a) @ ab) / (L * L); s_ = u * L
        d = np.linalg.norm(V - (a + np.outer(np.clip(u, 0, 1), ab)), axis=1)
        ok = np.ones(len(V), bool)
        if n.endswith('.L'): ok &= x > 0.0
        if n.endswith('.R'): ok &= x < 0.0
        if n.startswith(('uarm', 'farm', 'hand', 'thigh', 'shin', 'foot')): ok &= s_ > -0.012
        if n.startswith('uarm'): ok &= d < 0.11
        if n.startswith('clav'): ok &= (z > 1.33) & (np.abs(x) < 0.2)
        if n.startswith(('thigh', 'shin', 'foot')): ok &= z < 0.98
        if n.startswith('thigh'): ok &= (z < 0.9) | (np.abs(x) > 0.1) | (y > 0.03)
        if n == 'neck': ok &= z > 1.42
        if n == 'chest': ok &= z > 1.16
        if n == 'spine': ok &= (z > 0.98) & (z < 1.3)
        if n == 'hips': ok &= z < 1.12
        bias = {'hips': 0.02, 'spine': 0.02, 'chest': 0.02, 'clav.L': 0.015, 'clav.R': 0.015}.get(n, 0.0)
        D[:, j] = np.where(ok, d + bias, 9.0)
    W = np.zeros_like(D); W[np.arange(len(V)), np.argmin(D, axis=1)] = 1.0
    return W, names

def smooth_weights(me, W, it=3, lam=0.5, nb=None):
    from mesh33 import neighbours
    nb = nb or neighbours(me)
    for _ in range(it):
        A = np.array([W[l].mean(0) if l else W[i] for i, l in enumerate(nb)])
        W = W * (1 - lam) + A * lam
    return W
