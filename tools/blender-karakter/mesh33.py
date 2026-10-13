"""Meshing: distance field -> marching cubes -> voxel remesh -> QuadriFlow quads, and helpers to project
an existing topology onto another field (identity shape keys)."""
import bpy, bmesh, numpy as np
from skimage.measure import marching_cubes

def grid_eval(sdf, lo, hi, h, chunk=400000):
    lo = np.asarray(lo, float); hi = np.asarray(hi, float)
    n = np.maximum(2, np.ceil((hi - lo) / h).astype(int) + 1)
    axes = [np.linspace(lo[i], lo[i] + (n[i] - 1) * h, n[i]) for i in range(3)]
    X, Y, Z = np.meshgrid(*axes, indexing='ij'); P = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    out = np.empty(len(P))
    for i in range(0, len(P), chunk): out[i:i + chunk] = sdf(P[i:i + chunk])
    return out.reshape(n), lo

def sdf_mesh(name, sdf, lo, hi, h=0.0016, faces=1000, voxel=None, warp=None, unwarp=None, smooth=0, sym=True):
    """warp(p)->p' magnifies regions that need more quads before QuadriFlow; unwarp maps back (then re-projected)."""
    if not faces:
        F, o = grid_eval(sdf, lo, hi, h)
        F[0], F[-1], F[:, 0], F[:, -1], F[:, :, 0], F[:, :, -1] = 1, 1, 1, 1, 1, 1
        v, f, _, _ = marching_cubes(F, 0.0, spacing=(h, h, h)); v = v + o
        me = bpy.data.meshes.new(name); me.from_pydata(v.tolist(), [], f.tolist())
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        for p in me.polygons: p.use_smooth = True
        return ob
    ob = None; vs0 = voxel or max(0.004, h * 1.5)
    for k, (hh, vs) in enumerate([(h, vs0), (h, vs0 * 1.13), (h * 1.09, vs0), (h * 1.09, vs0 * 0.9), (h * 0.93, vs0 * 1.2), (h * 1.17, vs0 * 1.07), (h * 0.87, vs0), (h * 1.23, vs0 * 1.3)]):
        if k == 0 or hh != h_prev:
            F, o = grid_eval(sdf if warp is None else (lambda q: sdf(unwarp(q))), lo, hi, hh)
            F[0], F[-1], F[:, 0], F[:, -1], F[:, :, 0], F[:, :, -1] = 1, 1, 1, 1, 1, 1      # always a closed surface
            v, f, _, _ = marching_cubes(F, 0.0, spacing=(hh, hh, hh)); v = v + o
        h_prev = hh
        if ob is not None: bpy.data.objects.remove(ob)
        me = bpy.data.meshes.new(name); me.from_pydata((v * 100).tolist(), [], f.tolist())   # centimetres: QuadriFlow rejects edges < 1e-4
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        me.remesh_voxel_size = vs * 100
        for o2 in bpy.context.selected_objects: o2.select_set(False)
        bpy.context.view_layer.objects.active = ob; ob.select_set(True)
        bpy.ops.object.voxel_remesh()
        keep_largest(me)
        if not faces: break
        n0 = len(me.polygons)
        bpy.ops.object.quadriflow_remesh(target_faces=int(faces), mode='FACES', use_mesh_symmetry=sym, seed=3)
        if len(me.polygons) != n0 and len(me.polygons) < faces * 3: break
    else:
        raise RuntimeError('quadriflow failed for ' + name)
    ob.select_set(False)
    V = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3) / 100
    if unwarp is not None: V = unwarp(V)
    V = project(V, sdf)
    me.vertices.foreach_set('co', V.ravel()); me.update()
    for p in me.polygons: p.use_smooth = True
    if smooth: relax(me, sdf, smooth)
    return ob

def keep_largest(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    seen = np.zeros(len(bm.verts), bool); best = None
    for v0 in bm.verts:
        if seen[v0.index]: continue
        st = [v0]; mem = []
        while st:
            x = st.pop()
            if seen[x.index]: continue
            seen[x.index] = True; mem.append(x); st.extend(e.other_vert(x) for e in x.link_edges)
        if best is None or len(mem) > len(best): best = mem
    keep = set(v.index for v in best)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
    bm.to_mesh(me); bm.free(); me.update()

def grad(sdf, P, e=2e-4):
    g = np.zeros_like(P)
    for i in range(3):
        d = np.zeros(3); d[i] = e
        g[:, i] = (sdf(P + d) - sdf(P - d)) / (2 * e)
    return g

def project(P, sdf, it=6):
    P = P.copy()
    for _ in range(it):
        d = sdf(P); g = grad(sdf, P); n2 = (g * g).sum(1) + 1e-12
        P -= g * (d / n2)[:, None]
    return P

def neighbours(me):
    E = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', E); E = E.reshape(-1, 2)
    nb = [[] for _ in range(len(me.vertices))]
    for a, b in E: nb[a].append(b); nb[b].append(a)
    return nb

def relax(me, sdf, n=2, lam=0.5):
    """tangential relaxation (Laplacian then re-projection) for even quads"""
    nb = neighbours(me)
    V = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    for _ in range(n):
        A = np.array([V[l].mean(0) if l else V[i] for i, l in enumerate(nb)])
        V = project(V + (A - V) * lam, sdf, 3)
    me.vertices.foreach_set('co', V.ravel()); me.update()

def verts(ob):
    me = ob.data; V = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', V); return V.reshape(-1, 3)

def set_verts(ob, V):
    ob.data.vertices.foreach_set('co', np.asarray(V, float).ravel()); ob.data.update()

def morph_to(ob, sdf, smooth_disp=2):
    """project the object's vertices onto another field; the displacement is smoothed over the mesh so the quads stay even"""
    V0 = verts(ob); V1 = project(V0, sdf, 8)
    if smooth_disp:
        nb = neighbours(ob.data); D = V1 - V0
        for _ in range(smooth_disp):
            D = 0.5 * D + 0.5 * np.array([D[l].mean(0) if l else D[i] for i, l in enumerate(nb)])
        V1 = project(V0 + D, sdf, 4)
    return V1

def add_shape_key(ob, name, V):
    if not ob.data.shape_keys: ob.shape_key_add(name='Basis')
    k = ob.shape_key_add(name=name); k.data.foreach_set('co', np.asarray(V, float).ravel()); return k


# ------------------------------------------------------------------ caching of expensive meshes (QuadriFlow results)
import os, hashlib, json
CACHE = os.environ.get('C33CACHE', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cache'))
def cached_mesh(name, key, make):
    """make() -> object; the result's verts/faces are stored under CACHE keyed by key"""
    os.makedirs(CACHE, exist_ok=True)
    h = hashlib.md5(key.encode()).hexdigest()[:12]; fn = os.path.join(CACHE, '%s_%s.npz' % (name, h))
    if os.path.exists(fn):
        z = np.load(fn, allow_pickle=True); V = z['V']; Fl = z['F']; Fn = z['N']
        faces = np.split(Fl, np.cumsum(Fn)[:-1])
        me = bpy.data.meshes.new(name); me.from_pydata(V.tolist(), [], [f.tolist() for f in faces])
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        for p in me.polygons: p.use_smooth = True
        return ob
    ob = make(); me = ob.data
    V = verts(ob); F = [list(p.vertices) for p in me.polygons]
    np.savez(fn, V=V, F=np.concatenate(F), N=np.array([len(f) for f in F]))
    return ob

def cached_array(name, key, make):
    os.makedirs(CACHE, exist_ok=True)
    h = hashlib.md5(key.encode()).hexdigest()[:12]; fn = os.path.join(CACHE, '%s_%s.npy' % (name, h))
    if os.path.exists(fn): return np.load(fn)
    a = make(); np.save(fn, a); return a

def warp_fns(c, rad, M):
    c = np.asarray(c, float)
    def g(p): t = np.clip(1 - (((p - c) / rad) ** 2).sum(1), 0, 1); return t * t * (3 - 2 * t)
    def warp(p): return p + (M - 1) * g(p)[:, None] * (p - c)
    def unwarp(q):
        p = q.copy()
        for _ in range(30): p = (q + (M - 1) * g(p)[:, None] * c) / (1 + (M - 1) * g(p))[:, None]
        return p
    return warp, unwarp
