"""Nil Kervancısı v31 — character portraits modelled and rendered in Blender (bpy, Cycles CPU, Freestyle ink).
Heads, torsos and arms are signed-distance sculptures (smooth unions of ellipsoids/capsules, carved sockets and
mouth) projected onto clean UV-sphere topology, so every mood is the same mesh re-sculpted. Wigs, beards, collars,
clothes and jewellery are shells built on the same distance fields. Shading is a cel emission material
(3 bands + warm rim + soft AO) so the look matches the game's isometric town; Freestyle draws the ink.
usage: python3 char31.py KEY[,KEY…] [mood,mood…] [outdir] [res]
"""
import bpy, bmesh, math, os, sys, time, warnings
warnings.filterwarnings('ignore')
import numpy as np
from mathutils import Vector, Matrix, Euler

INK = (0x2B / 255, 0x1D / 255, 0x14 / 255)
def hexc(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def lin(c):  # sRGB -> linear (vertex colours and node colours are linear in Blender)
    return tuple(((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c)
def mixc(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

# ---------------------------------------------------------------- looks (same identities as the SVG busts / FIG)
LOOKS = {
  'h_ahmose': dict(facew=1.07, nose=1.12, eyes=0.93, rest=dict(lidU=0.18), sex='m', skin='#9C643E', hair='#1B1420', wig='cap', band='#1F5FA8', collar=['#C9862E', '#1F5FA8', '#F1ECE0', '#C9862E'], cloth='bare', cc='#F4EEDD', acc='#C9862E', age=42, jaw=1.12, brow=1.25, beard='stub', scar=1, sash=1, props=['khopesh', 'shield'], bg='#E6CFA2'),
  'h_neferet': dict(eyes=1.06, facew=0.97, sex='f', skin='#C98E62', hair='#1B1420', wig='long', braids=1, band='#D9A43A', collar=['#E5B93F', '#B7412E', '#E5B93F', '#2BA59A', '#E5B93F'], cloth='dress', cc='#C8402C', acc='#B7412E', ear='hoop', lips='#9C3F33', props=['purse'], bg='#F2C9B4', smile=0.25),
  'h_sitre': dict(facew=1.0, nose=0.95, sex='f', skin='#B97C4E', hair='#1F1A2E', wig='bob', band='#2BA59A', lotus=1, collar=['#3E8E5A', '#2BA59A', '#E5B93F', '#2BA59A'], cloth='dress', cc='#F6F1E4', acc='#2BA59A', ear='stud', lips='#8E4A3A', props=['pen', 'scroll'], bg='#BFE0D4', calm=1, age=34),
  'h_bakenre': dict(facew=1.02, eyes=1.05, nose=0.95, sex='m', skin='#9A5A32', hair='#1F1826', wig='crop', collar=None, cloth='bare', acc='#2C6BA6', age=22, amulet=1, props=['rope', 'paddle'], bg='#BFD9EC', smile=0.35, jaw=1.0),
  'paneb': dict(facew=0.97, nose=1.06, sex='m', skin='#B97C4E', hair='#1F1826', wig='short', band='#C8402C', tails=1, collar=['#B7412E', '#2BA59A', '#F1ECE0'], cloth='bare', acc='#B7412E', age=25, props=['oarpin'], bg='#F2D2B0', smile=0.4),
  'sethi': dict(facew=0.94, nose=1.18, sex='m', skin='#C98E62', hair='#15121E', wig='long', band='#D9A43A', beads=1, collar=['#D9A43A', '#2E7D4F', '#E9D58A', '#2E7D4F', '#D9A43A'], cloth='robe', cc='#2E7D4F', trim='#D9A43A', acc='#2E7D4F', ear='stud', props=['cup'], bg='#C9E2C2', sly=1, age=35, jaw=1.05),
  'hapu': dict(facew=1.12, nose=1.15, eyes=0.92, sex='m', skin='#B57A50', hair='#2B2340', wig='bald', band='#8F2F21', collar=['#D9A43A', '#8F2F21', '#5B3B6E'], cloth='robe', cc='#5B3B6E', trim='#D9A43A', acc='#5B3B6E', ear='hoop', age=50, fat=1, props=['ledger'], bg='#E2C2C8', sly=1, jaw=1.15),
  '0': dict(sex='f', skin='#C98E62', hair='#2B2340', wig='bob', band='#2C6BA6', collar=['#E5B93F', '#2BA59A', '#2C6BA6'], cloth='dress', cc='#F4EEDD', acc='#2C6BA6', ear='stud', props=['cat'], bg='#C8DDF0', age=30),
  '1': dict(facew=0.95, nose=1.22, eyes=0.95, sex='m', skin='#B57A50', hair='#2B2340', wig='bald', band='#F3EEE2', collar=['#4E9A6B', '#E5B93F'], cloth='bare', acc='#C97B4A', age=68, beard='short', beardc='#CFC6B6', browc='#E8E1D3', props=['chisel'], bg='#EFD9AE', jaw=1.08),
  '2': dict(sex='f', skin='#D9A577', hair='#1F1A2E', wig='long', band='#E5B93F', lotus=1, collar=['#E5B93F', '#4E9A6B', '#B7412E'], cloth='dress', cc='#F6F1E4', acc='#4E9A6B', ear='stud', props=['pen', 'palette'], bg='#CFE6D3', age=28),
  '3': dict(facew=1.18, nose=1.15, eyes=0.95, sex='m', skin='#A86E47', hair='#2B2340', wig='cap', band='#C97B4A', collar=['#2C6BA6', '#C97B4A', '#E5B93F'], cloth='bare', acc='#C97B4A', age=45, fat=1, props=['ingot'], bg='#F2CDBE', smile=0.5, jaw=1.2),
  '4': dict(facew=1.02, nose=0.9, lipf=1.2, sex='f', skin='#7A4A2E', hair='#1B1420', wig='puff', band='#2F5FB3', collar=['#E5B93F', '#2BA59A', '#2F5FB3'], cloth='dress', cc='#F3EBDA', acc='#2F5FB3', ear='hoop', lips='#5A2A22', props=['gem'], bg='#D8D0EE', age=32),
  '5': dict(facew=0.92, nose=1.28, eyes=0.92, sex='m', skin='#C08A5E', hair='#E3DCCD', wig='cap', band='#B7412E', collar=['#F1ECE0', '#B7412E', '#E5B93F'], cloth='robe', cc='#2F5E7A', trim='#B7412E', acc='#2F5E7A', ear='stud', age=72, beard='long', beardc='#E3DCCD', browc='#E8E1D3', props=['ramstaff'], bg='#BFD6E4'),
  '6': dict(facew=1.1, eyes=1.0, sex='f', skin='#A8754D', hair='#1F1A2E', wig='bob', band='#3E8E5A', collar=['#B5622F', '#3E8E5A', '#E5B93F'], cloth='dress', cc='#EFE3C8', acc='#3E8E5A', ear='hoop', age=55, fat=1, props=['dates'], bg='#F0D2B0', smile=0.45),
  '7': dict(facew=1.05, nose=1.08, sex='m', skin='#8E5236', hair='#1B1420', wig='cap', band='#2BA59A', collar=['#2BA59A', '#D9A43A', '#B7412E'], cloth='bare', acc='#2BA59A', ear='hoop', age=38, beard='point', props=['baboon'], bg='#BFE3E0', smile=0.3),
  'tv0': dict(facew=0.98, nose=1.1, sex='m', skin='#C08A5E', hair='#2B2340', wig='cap', band='#7A5A9A', collar=['#E5B93F', '#7A5A9A'], cloth='bare', acc='#7A5A9A', age=40, beard='stub', props=['cat2'], bg='#E0D6EE'),
  'tv1': dict(facew=1.16, nose=1.2, eyes=0.9, sex='m', skin='#B07A55', hair='#2B2340', wig='bald', band='#8E6A4A', collar=['#D9C9A8', '#8E6A4A'], cloth='bare', acc='#8E6A4A', age=48, beard='short', beardc='#3A2C2A', fat=1, bg='#EFE2CC', jaw=1.18),
  'tv3': dict(facew=0.95, nose=1.2, sex='m', skin='#C49166', hair='#EDE7DA', wig='cap', band='#4E6E8E', collar=['#E5B93F', '#4E6E8E'], cloth='robe', cc='#E9E1CF', trim='#4E6E8E', acc='#4E6E8E', age=75, blind=1, beard='long', beardc='#EDE7DA', browc='#F1ECE0', bg='#DCE6EE'),
  'tv4': dict(facew=1.0, lipf=1.2, sex='f', skin='#6E4129', hair='#16111C', wig='puff', band='#B7412E', collar=['#E5B93F', '#2BA59A', '#B7412E'], cloth='dress', cc='#F3EBDA', acc='#B7412E', ear='hoop', lips='#4E241E', bg='#F3DCD6', age=30),
  'tv7': dict(facew=1.1, nose=1.1, sex='m', skin='#9C643E', hair='#1B1420', wig='cap', band='#1F5FA8', collar=['#F1ECE0', '#1F5FA8'], cloth='bare', acc='#1F5FA8', ear='hoop', age=50, beard='full', beardc='#2B2028', bg='#D5E4EE', jaw=1.15),
  'priest': dict(facew=1.0, nose=1.1, sex='m', skin='#B57A50', hair='#2B2340', wig='bald', band=None, collar=['#E5B93F', '#F1ECE0'], cloth='robe', cc='#F6F1E4', trim='#E5B93F', acc='#E5B93F', age=55, sash=1, bg='#F2E6C6', calm=1),
  'guard': dict(facew=1.04, nose=1.05, eyes=0.95, sex='m', skin='#A86E47', hair='#1A1424', wig='bob', band='#E5B93F', collar=['#1F5FA8', '#F1ECE0'], cloth='bare', acc='#1F5FA8', age=30, straps=1, props=['spear'], bg='#DCE8F0', jaw=1.12, brow=1.2),
  'scribe': dict(facew=0.96, nose=1.05, sex='m', skin='#C98E62', hair='#2B2340', wig='cap', band='#2C6BA6', collar=['#2C6BA6', '#F1ECE0'], cloth='robe', cc='#F6F1E4', trim='#2C6BA6', acc='#2C6BA6', age=40, props=['pen'], bg='#DDEAF2', calm=1),
}

# ---------------------------------------------------------------- signed distance helpers (numpy, vectorised)
def rotm(rx=0, ry=0, rz=0): return np.array(Euler((rx, ry, rz)).to_matrix())
def ell(p, c, r, R=None):
    q = p - np.asarray(c)
    if R is not None: q = q @ R          # into the ellipsoid's frame
    q = q / np.asarray(r)
    k0 = np.linalg.norm(q, axis=1); k1 = np.linalg.norm(q / np.asarray(r), axis=1) + 1e-9
    return k0 * (k0 - 1.0) / k1
def cap(p, a, b, r, r2=None):
    a = np.asarray(a, float); b = np.asarray(b, float); pa = p - a; ba = b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    rr = r if r2 is None else r + (r2 - r) * h
    return np.linalg.norm(pa - ba[None, :] * h[:, None], axis=1) - rr
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)
def smax(a, b, k): return -smin(-a, -b, k)

# ---------------------------------------------------------------- the head as a distance field (eye level z=0, face -Y)
def head_params(L, mood):
    m = dict(teeth=0, smile=L.get('smile', 0.0) * 0.6, open=0.0, oround=0.0, browL=0.0, browR=0.0, browIn=0.0, lidU=0.0, lidL=0.0, gaze=(0.0, 0.0), smirk=0.0, cheek=0.0, purse=0.0)
    if L.get('calm'): m['lidU'] = 0.25
    for k_, v_ in (L.get('rest') or {}).items(): m[k_] = v_
    if L.get('sly') and mood == 'neutral': m.update(smirk=0.5, lidU=0.3, browR=0.3)
    if mood == 'happy': m.update(smile=1.0, open=0.75, cheek=1.0, lidL=0.75, lidU=0.15, browL=0.35, browR=0.35, teeth=1)
    if mood == 'angry': m.update(smile=-0.7, browIn=1.0, browL=-0.7, browR=-0.7, lidU=0.4, open=0.25, teeth=2)
    if mood == 'sly': m.update(smirk=1.0, smile=0.15, lidU=0.45, browR=0.6, browL=-0.2, gaze=(0.35, 0.0))
    if mood == 'surprised': m.update(oround=1.0, browL=1.0, browR=1.0, lidU=-0.6, smile=0.0)
    if mood == 'thinking': m.update(purse=1.0, browR=0.55, browL=-0.15, gaze=(0.35, 0.4), smile=0.0)
    if mood == 'sad': m.update(smile=-0.5, browIn=-0.8, lidU=0.3)
    return m

MW = 1.3
MZ = -0.06
def head_sdf(p, L, M):
    """anatomical landmarks (m, eye level z=0, face -Y): nasion y-.083, nose tip -.121, lips -.104, chin -.094/z-.118"""
    f = L['sex'] == 'f'; jw = L.get('jaw', 1.0) * (0.9 if f else 1.0); age = L.get('age', 30); fat = L.get('fat', 0)
    op = M['open']; orr = M['oround']
    d = ell(p, (0, 0.015, 0.03), (0.071 if not f else 0.068, 0.098, 0.088))                                   # cranium
    d = smin(d, ell(p, (0, -0.03, -0.03), ((0.059 if f else 0.064) * L.get('facew', 1.0) + 0.004 * fat, 0.065, 0.07 if not f else 0.066)), 0.03)                          # face oval
    d = smin(d, ell(p, (0, -0.025, -0.08 - 0.004 * op - 0.004 * orr), (0.054 * jw + 0.006 * fat, 0.055, 0.033)), 0.03)   # mandible
    d = smin(d, ell(p, (0, -0.074, (-0.091 if f else -0.095) - 0.006 * op - 0.006 * orr), (0.019 * jw, 0.015, 0.016 if not f else 0.014)), 0.02)      # chin
    for s in (-1, 1):
        d = smin(d, ell(p, (s * 0.048, -0.062 - 0.002 * M['cheek'], -0.008 + 0.005 * M['cheek']), (0.018, 0.012, 0.012)), 0.02)   # cheekbones
        if fat or age > 48: d = smin(d, ell(p, (s * 0.04, -0.045, -0.07), (0.02, 0.022, 0.022)), 0.025)      # jowls
    br = (0.008 if not f else 0.006) * L.get('brow', 1.0)
    d = smin(d, cap(p, (-0.038, -0.084, 0.025 + 0.002 * M['browL']), (0.038, -0.084, 0.025 + 0.002 * M['browR']), br), 0.02)   # brow ridge
    if M['browIn'] > 0: d = smax(d, -ell(p, (0, -0.098, 0.02), (0.003, 0.02, 0.01)), 0.003)
    nl = (0.72 if f else 1.0) * L.get('nose', 1.0); nt = 0.8 if f else 1.0
    # nose: one soft wedge (bridge to tip) with gentle wings
    d = smin(d, cap(p, (0, -0.087, 0.008), (0, -0.09 - 0.017 * nl, -0.03), 0.0062 * nt, 0.0095 * nt), 0.008)
    for s in (-1, 1): d = smin(d, ell(p, (s * 0.011, -0.093, -0.036), (0.008, 0.007, 0.0065)), 0.01)
    for s in (-1, 1): d = smax(d, -ell(p, (s * 0.033, -0.091, 0.003), (0.021, 0.019, 0.0145)), 0.011)        # eye sockets
    mz = MZ; th = (1.6 if f else 1.05) * L.get('lipf', 1.0); mw = MW
    for s in (-1, 1):
        up = 0.011 * M['smile'] + (0.011 * M['smirk'] if s > 0 else 0) - 0.002 * M['purse']
        tilt = -s * (0.42 * M['smile'] + (0.55 * M['smirk'] if s > 0 else 0))
        lx = (0.008 * (1 - 0.35 * M['purse']) + 0.002 * M['smile']) * mw
        d = smin(d, ell(p, (s * lx, -0.091, mz + 0.0052 + up * 0.5), ((0.012 + 0.002 * M['smile']) * mw, 0.0048 * th, 0.0046 * th), rotm(0, tilt, 0)), 0.005)      # upper lip
        d = smin(d, ell(p, (s * lx * 0.85, -0.0895, mz - 0.0058 + up * 0.35 - 0.004 * op - 0.005 * orr), (0.0115 * mw, 0.0058 * th, 0.0052 * th), rotm(0, tilt * 0.6, 0)), 0.005)   # lower lip
    for s in (-1, 1): d = smin(d, ell(p, (s * 0.072, 0.008, -0.012), (0.011, 0.018, 0.028), rotm(0, 0, s * 0.25)), 0.007)   # ears
    d = smin(d, cap(p, (0, 0.02, -0.075), (0, 0.024, -0.25), 0.049 if not f else 0.038), 0.016)               # neck
    return d

def mouth_masks(p, L, M):
    """vertex colour masks: lips, mouth cavity, teeth area"""
    f = L['sex'] == 'f'; my = -0.0655
    lip = np.minimum(ell(p, (0, -0.093, MZ - 0.0005 + 0.002 * M['smile'] - 0.004 * M['open'] - 0.005 * M['oround']), (0.026 * MW, 0.012, 0.0125 + 0.006 * M['open'] + 0.008 * M['oround'])), 1)
    return lip

# ---------------------------------------------------------------- star-shaped projection onto a distance field
def project(dirs, center, sdf, tmax=0.35, it=30):
    c = np.asarray(center, float); lo = np.zeros(len(dirs)); hi = np.full(len(dirs), tmax)
    for _ in range(it):
        mid = (lo + hi) * 0.5; v = sdf(c + dirs * mid[:, None])
        inside = v < 0; lo = np.where(inside, mid, lo); hi = np.where(inside, hi, mid)
    return c + dirs * ((lo + hi) * 0.5)[:, None]

def sphere_grid(nu, nv, th0=0.02, th1=math.pi - 0.02):
    th = np.linspace(th0, th1, nv); ph = np.linspace(0, 2 * math.pi, nu, endpoint=False)
    T, P = np.meshgrid(th, ph, indexing='ij')
    d = np.stack([np.sin(T) * np.sin(P), -np.sin(T) * np.cos(P), np.cos(T)], -1).reshape(-1, 3)   # phi=0 faces -Y (front)
    faces = []
    for i in range(nv - 1):
        for j in range(nu):
            a = i * nu + j; b = i * nu + (j + 1) % nu; faces.append((a, b, b + nu, a + nu))
    return d, faces, T.reshape(-1), P.reshape(-1)

def mesh_obj(name, verts, faces, cols=None, mat=None, keep=None, smooth=True, uv=None):
    if keep is not None:
        idx = np.where(keep)[0]; remap = -np.ones(len(verts), int); remap[idx] = np.arange(len(idx))
        faces = [tuple(remap[list(fc)]) for fc in faces if all(keep[v] for v in fc)]
        verts = verts[idx]
        if cols is not None: cols = cols[idx]
        if uv is not None: uv = uv[idx]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], [tuple(int(x) for x in fc) for fc in faces]); me.update()
    if smooth:
        for poly in me.polygons: poly.use_smooth = True
    if cols is not None:
        at = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
        at.data.foreach_set('color', np.hstack([cols, np.ones((len(cols), 1))]).astype(np.float32).ravel())
    if uv is not None:
        ul = me.uv_layers.new(name='UV'); li = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', li)
        ul.data.foreach_set('uv', uv[li].astype(np.float32).ravel())
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    if mat: me.materials.append(mat)
    return ob

# ---------------------------------------------------------------- cel material (emission: 3 bands from a fixed key light, warm rim, AO)
KEY = Vector((-0.55, -0.75, 0.6)).normalized()      # from the camera's left, above, in front
RIM = Vector((0.75, 0.55, 0.35)).normalized()       # from behind-right
_mats = {}
def toon(name, base=None, attr=False, strands=0.0, rim=0.6, ao=0.45, gloss=0.0, img=None):
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; Lk = nt.links
    for n in list(N): N.remove(n)
    out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); Lk.new(em.outputs[0], out.inputs[0])
    geo = N.new('ShaderNodeNewGeometry')
    dot = N.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; dot.inputs[1].default_value = KEY
    Lk.new(geo.outputs['Normal'], dot.inputs[0])
    ramp = N.new('ShaderNodeValToRGB'); cr = ramp.color_ramp; cr.interpolation = 'CONSTANT'
    stops = [(0.0, (0.58, 0.47, 0.52)), (0.3, (0.62, 0.5, 0.54)), (0.32, (0.84, 0.77, 0.75)), (0.5, (0.87, 0.8, 0.77)), (0.52, (1.0, 0.97, 0.92)), (1.0, (1.0, 0.98, 0.94))]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, c in stops[1:-1]: e = cr.elements.new(pos); e.color = (*c, 1)
    mr = N.new('ShaderNodeMapRange'); mr.inputs[1].default_value = -1; mr.inputs[2].default_value = 1
    Lk.new(dot.outputs['Value'], mr.inputs[0]); Lk.new(mr.outputs[0], ramp.inputs[0])
    if attr: bc = N.new('ShaderNodeVertexColor'); bc.layer_name = 'Col'; col_out = bc.outputs[0]
    else: bc = N.new('ShaderNodeRGB'); bc.outputs[0].default_value = (*lin(base), 1); col_out = bc.outputs[0]
    if img is not None:
        uvn = N.new('ShaderNodeUVMap'); uvn.uv_map = 'UV'; ti = N.new('ShaderNodeTexImage'); ti.image = img; ti.interpolation = 'Cubic'; ti.extension = 'CLIP'
        Lk.new(uvn.outputs[0], ti.inputs[0]); mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        Lk.new(ti.outputs['Alpha'], mx.inputs[0]); Lk.new(col_out, mx.inputs[6]); Lk.new(ti.outputs['Color'], mx.inputs[7]); col_out = mx.outputs[2]
    mul = N.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
    Lk.new(col_out, mul.inputs[6]); Lk.new(ramp.outputs[0], mul.inputs[7]); cur = mul.outputs[2]
    if strands > 0:   # wig strands: wave bands around the head, darkening thin lines
        tc = N.new('ShaderNodeTexCoord'); wv = N.new('ShaderNodeTexWave'); wv.wave_type = 'RINGS'; wv.rings_direction = 'Z' if strands < 1.5 else 'SPHERICAL'
        wv.inputs['Scale'].default_value = 9.0; wv.inputs['Distortion'].default_value = 1.2; wv.inputs['Detail'].default_value = 0.5
        if strands >= 2: wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs['Scale'].default_value = 14
        Lk.new(tc.outputs['Object'], wv.inputs['Vector'])
        sr = N.new('ShaderNodeValToRGB'); sr.color_ramp.elements[0].position = 0.0; sr.color_ramp.elements[0].color = (0.7, 0.68, 0.74, 1); sr.color_ramp.elements[1].position = 0.16
        Lk.new(wv.outputs['Fac'], sr.inputs[0])
        m2 = N.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs[0].default_value = 1
        Lk.new(cur, m2.inputs[6]); Lk.new(sr.outputs[0], m2.inputs[7]); cur = m2.outputs[2]
    if ao > 0:
        a = N.new('ShaderNodeAmbientOcclusion'); a.inputs['Distance'].default_value = 0.02; a.samples = 8
        ar = N.new('ShaderNodeValToRGB'); ar.color_ramp.elements[0].position = 0.25; ar.color_ramp.elements[0].color = (1 - ao, 1 - ao * 1.1, 1 - ao * 0.9, 1); ar.color_ramp.elements[1].position = 0.8
        Lk.new(a.outputs['AO'], ar.inputs[0])
        m3 = N.new('ShaderNodeMix'); m3.data_type = 'RGBA'; m3.blend_type = 'MULTIPLY'; m3.inputs[0].default_value = 1
        Lk.new(cur, m3.inputs[6]); Lk.new(ar.outputs[0], m3.inputs[7]); cur = m3.outputs[2]
    if rim > 0:
        lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
        rr = N.new('ShaderNodeValToRGB'); rr.color_ramp.interpolation = 'EASE'; rr.color_ramp.elements[0].position = 0.55; rr.color_ramp.elements[1].position = 0.7
        Lk.new(lw.outputs['Facing'], rr.inputs[0])
        d2 = N.new('ShaderNodeVectorMath'); d2.operation = 'DOT_PRODUCT'; d2.inputs[1].default_value = RIM; Lk.new(geo.outputs['Normal'], d2.inputs[0])
        cl = N.new('ShaderNodeMath'); cl.operation = 'MULTIPLY'; cl.use_clamp = True; Lk.new(rr.outputs[0], cl.inputs[0]); Lk.new(d2.outputs['Value'], cl.inputs[1])
        k2 = N.new('ShaderNodeMath'); k2.operation = 'MULTIPLY'; k2.inputs[1].default_value = rim; Lk.new(cl.outputs[0], k2.inputs[0])
        m4 = N.new('ShaderNodeMix'); m4.data_type = 'RGBA'; m4.blend_type = 'SCREEN'; m4.inputs[7].default_value = (*lin(hexc('#FFD9A0')), 1)
        Lk.new(k2.outputs[0], m4.inputs[0]); Lk.new(cur, m4.inputs[6]); cur = m4.outputs[2]
    if gloss > 0:   # a hard specular dot for eyes, gold and lips
        lw2 = N.new('ShaderNodeVectorMath'); lw2.operation = 'REFLECT'
        cam = N.new('ShaderNodeNewGeometry'); Lk.new(cam.outputs['Incoming'], lw2.inputs[0]); Lk.new(cam.outputs['Normal'], lw2.inputs[1])
        d3 = N.new('ShaderNodeVectorMath'); d3.operation = 'DOT_PRODUCT'; d3.inputs[1].default_value = -KEY; Lk.new(lw2.outputs[0], d3.inputs[0])
        sp = N.new('ShaderNodeValToRGB'); sp.color_ramp.elements[0].position = 0.9; sp.color_ramp.elements[1].position = 0.93
        Lk.new(d3.outputs['Value'], sp.inputs[0])
        m5 = N.new('ShaderNodeMix'); m5.data_type = 'RGBA'; m5.blend_type = 'MIX'; m5.inputs[7].default_value = (1, 0.98, 0.9, 1)
        k3 = N.new('ShaderNodeMath'); k3.operation = 'MULTIPLY'; k3.inputs[1].default_value = gloss; Lk.new(sp.outputs[0], k3.inputs[0])
        Lk.new(k3.outputs[0], m5.inputs[0]); Lk.new(cur, m5.inputs[6]); cur = m5.outputs[2]
    Lk.new(cur, em.inputs['Color'])
    _mats[name] = m
    return m

def flat(name, rgb, strength=1.0):
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*lin(rgb), 1); e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0]); _mats[name] = m; return m

def no_lines(ob):
    """keep Freestyle off fine detail: put the object in a collection the line set excludes"""
    col = bpy.data.collections.get('noline') or bpy.data.collections.new('noline')
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    for c in ob.users_collection: c.objects.unlink(ob)
    col.objects.link(ob)

def add_mod(ob, kind, **kw):
    m = ob.modifiers.new(kind, kind)
    for k, v in kw.items(): setattr(m, k, v)
    return m

# ---------------------------------------------------------------- building blocks
HEAD_C = np.array([0, 0.0, -0.01])
FX0, FX1, FZ0, FZ1 = -0.065, 0.065, -0.11, 0.02     # painted mouth area (front projection, metres)
def paint_face(L, M, N=768):
    from PIL import Image, ImageDraw
    SS = 3; W = N * SS; im = Image.new('RGBA', (W, W), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    P = lambda x, z: ((x - FX0) / (FX1 - FX0) * W, (1 - (z - FZ0) / (FZ1 - FZ0)) * W)
    f = L['sex'] == 'f'; ink = (43, 29, 20, 255); dark = (74, 26, 22, 255); teeth = (246, 240, 226, 255); tongue = (196, 96, 86, 255)
    lw = lambda mm: max(1, int(mm / 1000 / (FX1 - FX0) * W))
    mw = 0.0215 * MW * (1 - 0.3 * M['purse'] - 0.35 * M['oround']) * (1.12 if M['open'] > 0 else 1); mz = MZ
    sm, sk, op = M['smile'], M['smirk'], M['open']
    def curve(pts, width, col):
        pts = [P(*q) for q in pts]; g.line(pts, fill=col, width=width, joint='curve')
        r = width / 2
        for q in (pts[0], pts[-1]): g.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)
    def bez(a, c, b, n=24): return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]) for t in (i / n for i in range(n + 1))]
    nl = (0.72 if f else 1.0) * L.get('nose', 1.0)
    import random; rnd = random.Random(7)
    if L.get('beard') == 'stub' or (not f and L.get('age', 30) > 35 and not L.get('beard')):   # stubble on the jaw and upper lip
        a = 70 if L.get('beard') == 'stub' else 25
        for _ in range(2600):
            x = rnd.uniform(-0.06, 0.06); z = rnd.uniform(-0.11, -0.04)
            inside = (abs(x) > 0.024 or z < mz - 0.012 or (z > mz + 0.004 and z < mz + 0.014)) and (x * x / 0.06 ** 2 + (z + 0.11) ** 2 / 0.075 ** 2) < 1 and z < -0.042 + abs(x) * 0.2
            if inside:
                q = P(x, z); r = lw(0.35); g.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=(40, 26, 24, a))
    if L.get('scar'):
        curve([(0.03, -0.012), (0.038, -0.024), (0.044, -0.04)], lw(0.9), (122, 59, 46, 220)); curve([(0.033, -0.03), (0.043, -0.026)], lw(0.7), (122, 59, 46, 200))
    if L.get('age', 30) > 55:   # crow's feet
        for s_ in (-1, 1):
            for dz in (-0.004, 0.0, 0.004): curve([(s_ * 0.053, 0.004 + dz * 0.6), (s_ * 0.06, 0.004 + dz * 1.6)], lw(0.5), (90, 45, 30, 120))
    if L.get('age', 30) > 45:   # nasolabial folds
        for s_ in (-1, 1): curve(bez((s_ * 0.014, -0.033), (s_ * 0.024, -0.046), (s_ * 0.027, -0.062)), lw(0.7), (90, 45, 30, 110))
    ty = -0.03; nx = -0.0085 * (0.85 if f else 1)
    curve(bez((-0.0045, -0.006), (-0.0065, -0.017), (nx, ty - 0.001)), lw(0.9), (60, 30, 20, 150))
    curve(bez((nx - 0.002, ty - 0.004), (-0.001, ty - 0.009), (0.007, ty - 0.005)), lw(1.0), (60, 30, 20, 210))
    for x in (-0.0055, 0.0055): g.ellipse([P(x - 0.002, ty - 0.0055), P(x + 0.002, ty - 0.0078)], fill=(70, 30, 20, 150))
    yl = mz + 0.007 * sm + 0.002; yr = mz + 0.007 * sm + 0.009 * sk + 0.002 - (0.004 if M.get('teeth') == 2 else 0)
    if M.get('teeth') == 2: yl -= 0.004
    if M['oround'] > 0:
        h = 0.011 * M['oround']; w2 = 0.009
        box = [P(-w2, mz + 0.004), P(w2, mz - 0.004 - h * 1.2)]; g.ellipse(box, fill=dark, outline=ink, width=lw(1.0))
        return _img(im, N, L, M)
    if op > 0:
        top = bez((-mw, yl), (0, mz + 0.002 - 0.002 * sm), (mw, yr))
        bot = bez((mw, yr), (0, mz - 0.034 * op - 0.008 * sm), (-mw, yl))
        poly = [P(*q) for q in top + bot]; g.polygon(poly, fill=dark)
        # teeth: a band under the upper edge (both rows when angry), tongue at the bottom
        tb = bez((-mw * 0.85, yl - 0.0004), (0, mz + 0.002 - 0.004 * sm), (mw * 0.85, yr - 0.0004)); tb2 = bez((mw * 0.85, yr - 0.004), (0, mz - 0.006 - 0.004 * sm), (-mw * 0.85, yl - 0.004))
        mask = Image.new('L', (W, W), 0); ImageDraw.Draw(mask).polygon(poly, fill=255)
        lay = Image.new('RGBA', (W, W), (0, 0, 0, 0)); gl = ImageDraw.Draw(lay)
        gl.polygon([P(*q) for q in tb + tb2], fill=teeth)
        if M.get('teeth') == 2: gl.polygon([P(*q) for q in bez((-mw, mz - 0.012 * op), (0, mz - 0.006), (mw, mz - 0.012 * op)) + bez((mw, mz - 0.03), (0, mz - 0.03), (-mw, mz - 0.03))], fill=teeth)
        else: gl.ellipse([P(-0.011, mz - 0.008 * op - 0.005 * sm), P(0.011, mz - 0.024 * op - 0.005 * sm)], fill=tongue)
        im.paste(lay, (0, 0), Image.composite(lay, Image.new('RGBA', (W, W), (0, 0, 0, 0)), mask).split()[3])
        g.line(poly + [poly[0]], fill=ink, width=lw(0.9), joint='curve')
        # dimples at the corners
        for x, y in ((-mw, yl), (mw, yr)):
            s_ = 1 if x > 0 else -1; curve(bez((x + s_ * 0.001, y + 0.003), (x + s_ * 0.0035, y), (x + s_ * 0.001, y - 0.004)), lw(0.6), (90, 45, 30, 160))
        return _img(im, N, L, M)
    # closed mouths: the lip line, a soft lower lip shadow, corners
    mid = mz + 0.0007 - 0.0035 * sm - 0.002 * (1 if M['purse'] else 0)
    if sm < 0: mid = mz + 0.003 * -sm
    pts = bez((-mw, yl - 0.001 + (0.006 * sm if sm < 0 else 0)), (0, mid), (mw, yr - 0.001 + (0.006 * sm if sm < 0 else 0)))
    curve(pts, lw(1.1), ink)
    if f:  # painted lips
        lc = hexc(L.get('lips', '#9A4A3C')); lc = tuple(int(c * 255) for c in lc) + (200,)
        up = bez((-mw * 0.92, yl - 0.0008), (0, mz + 0.0075), (mw * 0.92, yr - 0.0008)); g.polygon([P(*q) for q in up + pts[::-1]], fill=lc)
        lo = bez((mw * 0.85, yr - 0.0015), (0, mz - 0.0105), (-mw * 0.85, yl - 0.0015)); g.polygon([P(*q) for q in pts + lo], fill=lc)
        g.line([P(*q) for q in pts], fill=ink, width=lw(1.1), joint='curve')
    curve(bez((-0.008, mz - 0.0075), (0, mz - 0.0092), (0.008, mz - 0.0075)), lw(0.7), (110, 55, 40, 110))
    if M['purse']: g.ellipse([P(mw + 0.001, mz + 0.001), P(mw + 0.0035, mz - 0.0015)], fill=ink)
    for x, y in ((-mw, yl - 0.001), (mw, yr - 0.001)):
        s_ = 1 if x > 0 else -1
        if sm > 0.2 or (sk > 0.3 and s_ > 0): curve(bez((x + s_ * 0.0005, y + 0.002), (x + s_ * 0.0028, y - 0.0005), (x + s_ * 0.0008, y - 0.003)), lw(0.7), (90, 45, 30, 200))
    return _img(im, N, L, M)
_imgn = [0]
def _img(im, N, L, M):
    from PIL import Image
    im = im.resize((N, N), Image.LANCZOS); _imgn[0] += 1
    path = os.path.join(bpy.app.tempdir or '/tmp', 'face_%s_%d.png' % (L['key'], _imgn[0])); im.save(path)
    img = bpy.data.images.load(path); img.colorspace_settings.name = 'sRGB'; img.alpha_mode = 'STRAIGHT'
    return img

def build_head(L, M, res=1.0):
    nu, nv = int(220 * res), int(150 * res)
    dirs, faces, TH, PH = sphere_grid(nu, nv)
    sdf = lambda p: head_sdf(p, L, M)
    V = project(dirs, HEAD_C, sdf, 0.32)
    sk = lin(hexc(L['skin'])); cols = np.tile(np.array(sk), (len(V), 1))
    f = L['sex'] == 'f'
    # lips
    lipc = lin(hexc(L.get('lips', '#9A4A3C' if f else '#8E4A3A')))
    lm = mouth_masks(V, L, M)
    w = np.clip(-lm * 5, 0, 1) ** 0.6 * (1.0 if f else 0.5)
    cols = cols * (1 - w[:, None]) + np.array(lipc)[None, :] * w[:, None]
    # cheeks, eye socket shading, stubble, scar
    for s in (-1, 1):
        bl = np.exp(-(((V[:, 0] - s * 0.045) / 0.018) ** 2 + ((V[:, 2] + 0.03) / 0.014) ** 2)) * (V[:, 1] < -0.05)
        cols = cols * (1 - 0.18 * bl[:, None]) + np.array(lin(hexc('#E0786A')))[None, :] * 0.18 * bl[:, None] * (0.8 if f else 0.3)
        so = np.exp(-(((V[:, 0] - s * 0.032) / 0.02) ** 2 + ((V[:, 2] - 0.012) / 0.01) ** 2)) * (V[:, 1] < -0.06)
        cols = cols * (1 - 0.1 * so[:, None]) + np.array(lin(hexc('#6A3A3A')))[None, :] * 0.1 * so[:, None]
    if L.get('beard') in ('stub',) or L.get('stubble'):
        jaw = ((V[:, 2] < -0.06) & (V[:, 1] < 0.02)) & (lm > 0.15)
        cols[jaw] = cols[jaw] * 0.82 + np.array(lin(hexc('#2A1E1E'))) * 0.18
    if L.get('scar'):
        sc = np.exp(-((((V[:, 0] + 0.042) + (V[:, 2] + 0.02) * 0.6) / 0.0025) ** 2) - ((V[:, 2] + 0.02) / 0.016) ** 2) * (V[:, 1] < -0.04)
        cols = cols * (1 - 0.6 * sc[:, None]) + np.array(lin(hexc('#7A3B2E')))[None, :] * 0.6 * sc[:, None]
    keep = V[:, 2] > -0.245
    uv = np.stack([(V[:, 0] - FX0) / (FX1 - FX0), (V[:, 2] - FZ0) / (FZ1 - FZ0)], -1)
    uv[V[:, 1] > -0.02] = -1                                        # only the front of the head takes the paint
    img = paint_face(L, M)
    ob = mesh_obj('head', V, faces, cols, toon('skin_' + L['key'] + str(id(M)), attr=True, rim=0.7, ao=0.5, img=img), keep, uv=uv)
    add_mod(ob, 'SMOOTH', factor=0.4, iterations=2)
    return ob, sdf

def build_torso(L, M):
    f = L['sex'] == 'f'; fat = L.get('fat', 0); sw = 0.17 if f else 0.2
    if fat: sw += 0.012
    def sdf(p0):
        p = p0 - np.array([0, 0, 0.03])
        d = cap(p, (0, 0.02, -0.075), (0, 0.024, -0.26), 0.049 if not f else 0.038)
        d = smin(d, ell(p, (0, 0.03, -0.27), (sw * 0.78, 0.075, 0.05)), 0.05)                   # trapezius
        d = smin(d, ell(p, (0, 0.0, -0.45), (sw * 0.88 + 0.01 * fat, 0.115 + 0.02 * fat, 0.22)), 0.05)   # ribcage
        for s in (-1, 1):
            d = smin(d, ell(p, (s * (sw - 0.005), 0.012, -0.33), (0.06, 0.062, 0.075)), 0.04)      # deltoids
            d = smin(d, cap(p, (s * (sw - 0.002), 0.012, -0.34), (s * (sw + 0.02), 0.03, -0.62), 0.05, 0.042), 0.03)   # upper arms
            if not f: d = smin(d, ell(p, (s * 0.075, -0.075 - 0.01 * fat, -0.37), (0.075, 0.04, 0.055)), 0.03)  # pectorals
            else: d = smin(d, ell(p, (s * 0.06, -0.085, -0.415), (0.058, 0.052, 0.055)), 0.03)
            d = smin(d, cap(p, (s * 0.02, -0.052, -0.265), (s * 0.15, -0.02, -0.285), 0.011), 0.02)   # clavicles
        return d
    dirs, faces, TH, PH = sphere_grid(200, 140)
    C = np.array([0, 0.012, -0.37])
    V = project(dirs, C, sdf, 0.6)
    sk = lin(hexc(L['skin'])); cols = np.tile(np.array(sk), (len(V), 1))
    cl = L.get('cloth', 'bare')
    clothm = np.zeros(len(V), bool)
    if cl == 'dress': clothm = (V[:, 2] < -0.37 - 0.02 * np.abs(V[:, 0]) * 0) & (np.abs(V[:, 0]) < sw - 0.02)
    if cl == 'robe': clothm = V[:, 2] < -0.24
    if clothm.any():
        cc = lin(hexc(L['cc']))
        # folds: displace along the normal-ish radial direction with soft waves, darken the valleys
        r = V - C; ang = np.arctan2(r[:, 0], -r[:, 1])
        fold = np.sin(ang * 14 + V[:, 2] * 18) * np.clip((-V[:, 2] - 0.3) / 0.15, 0, 1)
        V[clothm] += (r[clothm] / np.linalg.norm(r[clothm], axis=1)[:, None]) * (0.006 + 0.0025 * fold[clothm])[:, None]
        sh = np.clip(0.9 + 0.1 * fold, 0.78, 1.0)
        cols[clothm] = np.array(cc)[None, :] * sh[clothm][:, None]
        if L.get('trim'):
            tm = clothm & (np.abs(V[:, 0] + (V[:, 2] + 0.3) * 0.6) < 0.018)       # diagonal trim/sash stripe of the robe
            cols[tm] = lin(hexc(L['trim']))
    keep = (V[:, 2] < -0.08) & (V[:, 2] > -0.66)
    ob = mesh_obj('torso', V, faces, cols, toon('body_' + L['key'], attr=True, rim=0.5, ao=0.4), keep)
    return ob, sdf

def build_collar(L, torso_sdf):
    rows = L.get('collar')
    if not rows: return None
    f = L['sex'] == 'f'; n = len(rows)
    NU, NV = 160, n * 4 + 1
    th = np.linspace(-0.92 * math.pi, 0.92 * math.pi, NU)     # around the neck, 0 = front
    s = np.linspace(0, 1, NV)
    T_, S_ = np.meshgrid(th, s, indexing='ij')
    rx = 0.055 + S_ * (0.115 if not f else 0.1); rz = 0.05 + S_ * (0.09 if not f else 0.08)
    P0 = np.stack([np.sin(T_) * rx, -np.cos(T_) * rz * 0.95 + 0.015, -0.225 - S_ * 0.03 - 0.06 * S_ * np.cos(T_) ** 2], -1).reshape(-1, 3)
    C = np.array([0, 0.015, -0.30]); dirs = P0 - C; dirs /= np.linalg.norm(dirs, axis=1)[:, None]
    V = project(dirs, C, torso_sdf, 0.5) + dirs * 0.006
    # one strip per bead row: crisp colour edges and an ink line between rows, like the painted collars
    Vg = V.reshape(NU, NV, 3); per = NV // n; ob = None
    for i, c in enumerate(rows):
        j0, j1 = i * per, min(NV - 1, (i + 1) * per)
        sub = Vg[:, j0:j1 + 1].reshape(-1, 3); m = j1 - j0 + 1
        faces = [(u * m + j, u * m + j + 1, (u + 1) * m + j + 1, (u + 1) * m + j) for u in range(NU - 1) for j in range(m - 1)]
        st = mesh_obj('collar%d' % i, sub, faces, None, toon('row' + c, hexc(c), rim=0.25, ao=0.3))
        add_mod(st, 'SOLIDIFY', thickness=0.004 + 0.0015 * (i % 2), offset=1)
        ob = ob or st
    # drop beads along the rim
    for k in range(-13, 14):
        a = k / 13 * 0.9 * math.pi
        p0 = np.array([[math.sin(a) * (0.055 + (0.115 if not f else 0.1)), -math.cos(a) * (0.05 + (0.09 if not f else 0.08)) * 0.95 + 0.015, -0.255 - 0.06 * math.cos(a) ** 2]])
        dd = p0 - C; dd /= np.linalg.norm(dd); q = project(dd, C, torso_sdf, 0.5)[0] + dd[0] * 0.007
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.007, location=tuple(q + np.array([0, 0, -0.006])), segments=10, ring_count=6)
        b = bpy.context.object; b.scale = (0.8, 0.6, 1.3); b.data.materials.append(toon('bead_' + rows[k % len(rows)], hexc(rows[(k + 1) % len(rows)]), rim=0.3, ao=0, gloss=0.4))
        bpy.ops.object.shade_smooth()
    return ob

def build_eyes(L, M):
    f = L['sex'] == 'f'; objs = []
    white = toon('eyewhite', hexc('#F4EEE2'), rim=0, ao=0.3)
    iris_c = hexc('#C9CCD2') if L.get('blind') else hexc(L.get('iris', '#4A2C1A'))
    for s in (-1, 1):
        r = 0.0136 * (1.06 if f else 1.0) * L.get('eyes', 1.0); c = Vector((s * 0.033, -0.0705 + (r - 0.0118) * 0.4, 0.003))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=c, segments=32, ring_count=16); e = bpy.context.object; bpy.ops.object.shade_smooth()
        e.data.materials.append(white); objs.append(e)
        # iris + pupil as shallow caps on the eyeball, aimed by the gaze
        gx, gz = M['gaze']
        aim = Euler((-(0.12 + gz * 0.25), 0, -(gx * 0.45) + s * 0.04))
        for rr, col, dz, nm in ((0.7, iris_c, 0.0008, 'iris'), (0.36, hexc('#120C08') if not L.get('blind') else hexc('#B2B7C0'), 0.0012, 'pupil')):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r + dz, location=c, segments=32, ring_count=16); ir = bpy.context.object
            bm = bmesh.new(); bm.from_mesh(ir.data)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > -r * math.cos(math.asin(rr))], context='VERTS')
            bm.to_mesh(ir.data); bm.free(); ir.rotation_euler = aim; bpy.ops.object.shade_smooth()
            ir.data.materials.append(flat(nm + str(col), col) if nm == 'pupil' else toon('iris' + str(col), col, rim=0, ao=0, gloss=0.9)); no_lines(ir); objs.append(ir)
        # catch light
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0018, location=c + Vector((-0.004 + s * 0.0005, -r - 0.0005, 0.004)), segments=8, ring_count=6)
        hl = bpy.context.object; hl.data.materials.append(flat('catch', (1, 1, 1))); no_lines(hl)
        # lids: skin shells cut by a tilted plane; their open edge is the lash line (Freestyle border + a kohl tube)
        up = 0.52 - 0.7 * M['lidU']
        lo = -0.72 + 0.5 * M['lidL']
        for which in ('up', 'lo'):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 1.1, location=c, segments=40, ring_count=20); lid = bpy.context.object
            bm = bmesh.new(); bm.from_mesh(lid.data)
            tilt = 0.25 * s  # outer corner lower on the upper lid (almond shape)
            def keepv(v):
                z = v.co.z + v.co.x * tilt * 0.6 * (1 if which == 'up' else -0.4)
                return (z > r * up) if which == 'up' else (z < r * lo)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keepv(v) or v.co.y > r * 0.35], context='VERTS')
            bm.to_mesh(lid.data); bm.free(); bpy.ops.object.shade_smooth()
            lid.data.materials.append(toon('lid_' + L['key'], mixc(hexc(L['skin']), hexc('#5A3A3A'), 0.12 if which == 'up' else 0.0), rim=0.2, ao=0.3))
            objs.append(lid)
            # kohl tube along the lid edge (+ the Egyptian wing on the upper lid)
            pts = []
            for k in range(13):
                a = -0.95 * math.pi / 2 + k / 12 * 0.95 * math.pi   # across the front
                x = math.sin(a) * r * 1.1; y = -math.cos(a) * r * 1.1
                z = (r * up if which == 'up' else r * lo) - x * tilt * 0.6 * (1 if which == 'up' else -0.4)
                rr = math.sqrt(max(1e-8, (r * 1.1) ** 2 - z * z)); x = math.sin(a) * rr; y = -math.cos(a) * rr
                if y < r * 0.3: pts.append(c + Vector((x, y, z)))
            if which == 'up':
                o = pts[0] if s < 0 else pts[-1]
                wing = o + Vector((s * 0.011 * (1.25 if f else 1), 0.004, 0.0035 + 0.0025 * (1 if M['browIn'] else 0)))
                pts = ([wing] + pts) if s < 0 else (pts + [wing])
            cu = bpy.data.curves.new('kohl', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = (0.0014 if f else 0.0011) if which == 'up' else 0.0005; cu.bevel_resolution = 2
            sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
            for i, q in enumerate(pts): sp.points[i].co = (q.x, q.y, q.z, 1)
            ko = bpy.data.objects.new('kohl', cu); bpy.context.scene.collection.objects.link(ko); cu.materials.append(flat('ink', INK)); no_lines(ko)
    return objs

def project_pts(pts, sdf, C, off):
    P = np.array(pts, float); D = P - C; D /= np.linalg.norm(D, axis=1)[:, None]
    return project(D, C, sdf, 0.4) + D * off

def build_brows(L, M, head_sdf_f):
    f = L['sex'] == 'f'; col = hexc(L.get('browc', L['hair'] if L['hair'] not in ('#E3DCCD', '#EDE7DA') else '#E8E1D3'))
    if L['hair'] in ('#E3DCCD', '#EDE7DA'): col = hexc('#E8E1D3')
    C = np.array([0, 0.0, 0.0])
    for s in (-1, 1):
        lift = M['browR'] if s > 0 else M['browL']
        inn = M['browIn']
        pts = []
        for k, (x, z) in enumerate(((0.013, 0.022), (0.025, 0.027), (0.038, 0.029), (0.05, 0.025), (0.058, 0.017))):
            dz = 0.009 * lift * (0.6 + 0.4 * k / 4) - 0.008 * inn * (1 - k / 4) + (0.003 * inn * k / 4)
            if f: dz += 0.002 * (1 - abs(k - 2) / 2)
            pts.append((s * x, -0.1, z + dz))
        P = project_pts(pts, head_sdf_f, C, 0.0032)
        cu = bpy.data.curves.new('brow', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.003 if not f else 0.002; cu.bevel_resolution = 3
        sp = cu.splines.new('NURBS'); sp.points.add(len(P) - 1); sp.use_endpoint_u = True; sp.order_u = 3
        for i, q in enumerate(P):
            sp.points[i].co = (*q, 1); sp.points[i].radius = 1.15 - 0.6 * i / (len(P) - 1)
        ob = bpy.data.objects.new('brow', cu); bpy.context.scene.collection.objects.link(ob)
        cu.materials.append(toon('brow' + str(col), col, rim=0.2, ao=0)); no_lines(ob)

def build_hair(L, head_sdf_f):
    wig = L.get('wig'); H = hexc(L['hair']); objs = []
    if sum(H) < 0.5: H = mixc(H, hexc('#5A4A6A'), 0.35)
    if wig in (None, 'bald'):
        if L.get('band'): objs.append(headband(L, head_sdf_f, 0.0))
        return objs
    th_off = {'cap': 0.006, 'crop': 0.005, 'short': 0.007, 'bob': 0.013, 'long': 0.014, 'puff': 0.03}[wig]
    def wsdf(p):
        d = head_sdf_f(p) - th_off
        if wig == 'bob': d = smin(d, smax(ell(p, (0, 0.012, -0.0), (0.088, 0.1, 0.13)), -(p[:, 2] + 0.095), 0.01), 0.02)
        if wig == 'long': d = smin(d, smax(ell(p, (0, 0.03, -0.06), (0.092, 0.095, 0.2)), -(p[:, 2] + 0.26), 0.01), 0.02)
        if wig == 'puff':
            for c, r in (((0, 0.01, 0.07), 0.085), ((0.065, 0.02, 0.02), 0.05), ((-0.065, 0.02, 0.02), 0.05), ((0, 0.06, 0.02), 0.07)): d = smin(d, ell(p, c, (r, r, r)), 0.02)
        return d
    dirs, faces, TH, PH = sphere_grid(200, 140)
    C = np.array([0, 0.0, 0.0])
    V = project(dirs, C, wsdf, 0.5)
    # hairline: forehead line in front, around the ears, nape at the back
    az = np.arctan2(dirs[:, 0], -dirs[:, 1])          # 0 = front
    el = np.arcsin(np.clip(dirs[:, 2], -1, 1))
    front = np.abs(az) < (1.05 if wig in ('bob', 'long') else 1.25)
    hl = {'cap': 0.47, 'crop': 0.5, 'short': 0.5, 'bob': 0.42, 'long': 0.42, 'puff': 0.45}[wig]
    if wig in ('cap', 'crop', 'short'): keep = np.where(front, el > hl, el > (0.15 if np.any(True) else 0) - 0.5 * (np.abs(az) > 2.2))
    else: keep = np.where(front, el > hl, True)
    if wig in ('cap', 'crop', 'short'): keep &= ~((np.abs(np.abs(az) - math.pi / 2) < 0.5) & (el < 0.2))      # clear the ears
    if wig == 'bob': keep &= V[:, 2] > -0.098
    if wig == 'long': keep &= ~(front & (el < hl)) & (V[:, 2] > -0.27)
    if wig == 'puff': keep &= ~((np.abs(az) < 1.25) & (el < 0.45))
    # strands: real grooves in the surface
    grooves = np.sin(az * (60 if wig != 'puff' else 30)) * (0.0004 if wig not in ('crop', 'cap') else 0.0003)
    if wig == 'crop' or wig == 'short': grooves += 0.002 * np.sin(az * 23 + el * 17) * np.sin(az * 7 - el * 29)
    V = V + dirs * grooves[:, None]
    ob = mesh_obj('hair', V, faces, None, toon('hair_' + L['key'], H, strands=1.0 if wig != 'puff' else 1.6, rim=0.3, ao=0.45), keep)
    add_mod(ob, 'SOLIDIFY', thickness=0.004, offset=-1)
    objs.append(ob)
    if wig == 'long':   # front lappets: bundles of braids/strands falling in front of the shoulders
        braid = toon('braid_' + L['key'], H, strands=2.0, rim=0.35, ao=0.35)
        nb = 4 if L.get('braids') else 6
        for sd in (-1, 1):
            for j in range(nb):
                t = (j - (nb - 1) / 2) / max(1, nb - 1)
                top = Vector((sd * (0.066 + 0.006 * abs(t)), 0.012 + t * 0.03, 0.0))
                mid = Vector((sd * (0.083 + 0.004 * t), -0.012 + t * 0.026, -0.11))
                bot = Vector((sd * (0.09 + 0.006 * t), -0.03 + t * 0.03, -0.235 - 0.01 * abs(t)))
                cu = bpy.data.curves.new('br', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0075 if L.get('braids') else 0.0055; cu.bevel_resolution = 3
                sp = cu.splines.new('NURBS'); sp.points.add(2); sp.use_endpoint_u = True; sp.order_u = 3
                for i, q in enumerate((top, mid, bot)): sp.points[i].co = (*q, 1)
                br = bpy.data.objects.new('braid', cu); bpy.context.scene.collection.objects.link(br); cu.materials.append(braid); objs.append(br)
                if L.get('braids') or (L.get('beads') and j % 2 == 0):
                    bpy.ops.mesh.primitive_cylinder_add(radius=0.0085 if L.get('braids') else 0.0065, depth=0.012, location=bot, vertices=12)
                    b2 = bpy.context.object; b2.data.materials.append(toon('gold', hexc('#E5B93F'), rim=0.4, ao=0, gloss=0.6)); bpy.ops.object.shade_smooth()
    if L.get('band'): objs.append(headband(L, wsdf, 0.0))
    if L.get('tails'):
        for k in range(2):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0.06 - k * 0.012, 0.085, -0.02 - k * 0.03)); t = bpy.context.object
            t.scale = (0.014, 0.004, 0.05); t.rotation_euler = (0.5, 0.4 + k * 0.3, 0.2); add_mod(t, 'SUBSURF', levels=2, render_levels=2)
            t.data.materials.append(toon('band_' + L['band'], hexc(L['band']), rim=0.4, ao=0.2))
    if L.get('lotus'):
        for k, (dx, rz) in enumerate(((-0.012, 0.6), (0.0, 0.0), (0.012, -0.6))):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.019, location=(dx * 1.5, -0.07, 0.1 + (0.008 if dx == 0 else 0)), segments=16, ring_count=8)
            pe = bpy.context.object; pe.scale = (0.45, 0.35, 1.25); pe.rotation_euler = (0.2, rz, 0); bpy.ops.object.shade_smooth()
            pe.data.materials.append(toon('petal' + str(k), hexc('#F2A7B8' if dx == 0 else '#F7C6D0'), rim=0.3, ao=0))
    return objs

def headband(L, sdf, _):
    n = 120; a = np.linspace(-math.pi, math.pi, n, endpoint=False)
    rows = []
    for h in (0.042, 0.054):
        D = np.stack([np.sin(a), -np.cos(a), np.full(n, h * 6.5)], -1); D /= np.linalg.norm(D, axis=1)[:, None]
        rows.append(project(D, np.array([0, 0.0, 0.0]), sdf, 0.5) + D * 0.0005)
    V = np.vstack(rows); faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    ob = mesh_obj('band', V, faces, None, toon('band_' + L['band'], hexc(L['band']), rim=0.4, ao=0.2, gloss=0.2))
    add_mod(ob, 'SOLIDIFY', thickness=0.004, offset=1)
    return ob

def build_beard(L, M, head_sdf_f):
    """a beard is its own soft solid around the jaw; only the part outside the face is kept, so its edge follows the cheeks"""
    kind = L.get('beard')
    if kind in (None, 'stub'): return None
    bc = hexc(L.get('beardc', L['hair']))
    jd = 0.006 * M['open'] + 0.012 * M['oround']
    def bsdf(p):
        d = ell(p, (0, -0.035, -0.088 - jd), (0.062, 0.064, 0.042))
        d = smin(d, ell(p, (0, -0.077, -0.106 - jd), (0.03, 0.022, 0.026)), 0.02)
        if kind == 'long': d = smin(d, ell(p, (0, -0.07, -0.15 - jd), (0.034, 0.028, 0.065)), 0.025)
        if kind == 'full': d = smin(smin(d, ell(p, (0, -0.06, -0.11 - jd), (0.064, 0.05, 0.04)), 0.02), ell(p, (0, -0.1, MZ + 0.009), (0.026, 0.012, 0.0055)), 0.006)
        if kind == 'point': d = cap(p, (0, -0.083, -0.1 - jd), (0, -0.075, -0.165 - jd), 0.012, 0.007)
        d = smax(d, -ell(p, (0, -0.105, MZ - 0.002), (0.028 * MW, 0.035, 0.0115 + 0.01 * M['open'] + 0.012 * M['oround'])), 0.006)   # keep the mouth free
        return d
    both = lambda p: np.minimum(bsdf(p), head_sdf_f(p))
    dirs, faces, TH, PH = sphere_grid(220, 160)
    C = np.array([0, 0.0, -0.06])
    V = project(dirs, C, both, 0.4)
    region = (bsdf(V) < 0.0012) & (head_sdf_f(V) > 0.0015) & (V[:, 1] < 0.03)
    az = np.arctan2(dirs[:, 0], -dirs[:, 1])
    V = V + dirs * (0.0009 * np.sin(az * 70))[:, None]
    ob = mesh_obj('beard', V, faces, None, toon('beard_' + L['key'], bc, strands=1.0, rim=0.5, ao=0.4), region)
    add_mod(ob, 'SMOOTH', factor=0.5, iterations=2)
    return ob

def build_ears_jewel(L):
    e = L.get('ear')
    if not e: return
    for s in (-1, 1):
        loc = (s * 0.079, -0.002, -0.04)
        if e == 'hoop':
            bpy.ops.mesh.primitive_torus_add(major_radius=0.012, minor_radius=0.0022, location=(loc[0], loc[1], loc[2] - 0.01), rotation=(0, math.pi / 2, 0), major_segments=24, minor_segments=8)
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0045, location=loc, segments=12, ring_count=8)
        o = bpy.context.object; bpy.ops.object.shade_smooth(); o.data.materials.append(toon('gold', hexc('#E5B93F'), rim=0.4, ao=0, gloss=0.6))

def build_props(L, torso_sdf):
    P = L.get('props', []); g = toon('gold', hexc('#E5B93F'), rim=0.4, ao=0, gloss=0.6)
    def mat(n, c, **k): return toon(n, hexc(c), **k)
    def sph(loc, r, sc, m, seg=24):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2); o = bpy.context.object; o.scale = sc; bpy.ops.object.shade_smooth(); o.data.materials.append(m); return o
    def cyl(a, b, r, m, seg=16, r2=None):
        a = Vector(a); b = Vector(b); d = b - a
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r if r2 is None else r2, depth=d.length, location=(a + b) / 2, vertices=seg)
        o = bpy.context.object; o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); bpy.ops.object.shade_smooth(); o.data.materials.append(m); return o
    if L.get('amulet'):
        cyl((-0.035, -0.04, -0.235), (0, -0.098, -0.33), 0.0016, mat('cord', '#C9A262')); cyl((0.035, -0.04, -0.235), (0, -0.098, -0.33), 0.0016, mat('cord', '#C9A262'))
        sph((0, -0.104, -0.345), 0.016, (1, 0.5, 1.2), mat('turq', '#2BA59A', gloss=0.5)); sph((0, -0.1, -0.327), 0.007, (1.4, 0.6, 0.6), g)
    if 'oarpin' in P:
        cyl((-0.15, -0.02, -0.29), (0.05, -0.11, -0.55), 0.007, mat('strap', '#8E5A33'))
        o = cyl((-0.025, -0.118, -0.34), (0.03, -0.112, -0.4), 0.0035, g); sph((0.034, -0.111, -0.405), 0.01, (0.5, 0.35, 1.3), g)
    if 'khopesh' in P and os.environ.get('KHOPESH'):   # hilt over the right shoulder, a sickle blade behind it
        cyl((-0.21, 0.07, -0.3), (-0.17, 0.065, -0.17), 0.011, mat('wood', '#5A3B22')); sph((-0.17, 0.065, -0.17), 0.014, (1, 1, 0.5), toon('gold', hexc('#E5B93F'), rim=0.4, ao=0, gloss=0.6))
        cyl((-0.17, 0.065, -0.17), (-0.155, 0.07, -0.06), 0.007, mat('bronze', '#C98A3E', gloss=0.5), r2=0.009)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.008, location=(-0.115, 0.075, -0.06), rotation=(math.pi / 2, 0, 0), major_segments=40, minor_segments=8)
        o = bpy.context.object; bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < 0.0 or v.co.x > 0.03], context='VERTS'); bm.to_mesh(o.data); bm.free()
        o.scale = (1, 1, 1.0); bpy.ops.object.shade_smooth(); o.data.materials.append(mat('bronze', '#C98A3E', gloss=0.5))
    if 'shield' in P:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.17, depth=0.02, location=(0.2, 0.2, -0.36), rotation=(math.pi / 2, 0, -0.45), vertices=48); s = bpy.context.object
        s.data.materials.append(mat('hide', '#8E5A33')); add_mod(s, 'BEVEL', width=0.006, segments=2)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.011, location=(0.2, 0.19, -0.36), rotation=(math.pi / 2, 0, -0.45), major_segments=48, minor_segments=8)
        bpy.context.object.data.materials.append(mat('bronze', '#B9853A', gloss=0.4)); bpy.ops.object.shade_smooth()
    if 'rope' in P:
        for k in range(3):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.085 - k * 0.006, minor_radius=0.0085, location=(0.18 + k * 0.003, -0.01, -0.29 - k * 0.012), rotation=(1.2, 0.3, 0.2), major_segments=48, minor_segments=10)
            r = bpy.context.object; bpy.ops.object.shade_smooth(); r.data.materials.append(mat('rope', '#D8B57A', strands=1.6))
    if 'paddle' in P:
        cyl((-0.25, 0.09, -0.65), (-0.2, 0.1, 0.05), 0.011, mat('wood2', '#B98654'))
        sph((-0.195, 0.1, 0.16), 0.05, (0.5, 0.12, 2.4), mat('blade', '#D8B57A'))
    if 'purse' in P:
        pass
    if 'scroll' in P:
        cyl((0.12, -0.13, -0.5), (0.22, -0.08, -0.46), 0.022, mat('papyrus', '#F3E6C2'))
    if 'pen' in P:
        cyl((0.07, 0.04, 0.09), (0.095, -0.035, -0.05), 0.0035, mat('reed', '#D8C27A'))
    if 'palette' in P:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.17, -0.12, -0.48)); p = bpy.context.object; p.scale = (0.035, 0.012, 0.22); p.rotation_euler = (0.2, 0.5, 0.1)
        add_mod(p, 'BEVEL', width=0.005, segments=2); p.data.materials.append(mat('palette', '#D8B57A'))
        sph((-0.12, -0.14, -0.4), 0.008, (1, 0.5, 1), mat('inkb', '#1A1210')); sph((-0.135, -0.135, -0.38), 0.008, (1, 0.5, 1), mat('inkr', '#B7412E'))
    if 'cat' in P or 'cat2' in P:   # a cat on the left shoulder
        fur = '#2E2A38' if 'cat' in P else '#D98A3A'; m = mat('fur' + fur, fur, strands=0, rim=0.7)
        x = 0.21; sph((x, 0.03, -0.26), 0.06, (1, 1.3, 0.8), m); h = sph((x + 0.01, -0.03, -0.17), 0.045, (1.05, 0.95, 0.9), m)
        for s in (-1, 1):
            bpy.ops.mesh.primitive_cone_add(radius1=0.018, radius2=0.002, depth=0.04, location=(x + 0.01 + s * 0.026, -0.03, -0.125), rotation=(0, s * 0.35, 0), vertices=12)
            bpy.context.object.data.materials.append(m); bpy.ops.object.shade_smooth()
            sph((x + 0.01 + s * 0.017, -0.071, -0.165), 0.008, (1, 0.5, 0.75), mat('cateye', '#E9C46A', gloss=0.8))
            sph((x + 0.01 + s * 0.017, -0.075, -0.165), 0.003, (0.5, 0.4, 1.2), flat('pupil0', (0.05, 0.03, 0.02)))
        sph((x + 0.01, -0.077, -0.185), 0.005, (1, 0.6, 0.7), mat('catnose', '#E58A9A'))
        if 'cat' in P:
            bpy.ops.mesh.primitive_torus_add(major_radius=0.008, minor_radius=0.0015, location=(x + 0.04, -0.03, -0.14), rotation=(0, math.pi / 2, 0)); bpy.context.object.data.materials.append(g)
    if 'baboon' in P:
        m = mat('baboon', '#A8A28A', strands=1.6, rim=0.7); x = 0.22
        sph((x, 0.04, -0.25), 0.065, (1, 1.1, 0.9), m); sph((x - 0.005, -0.01, -0.15), 0.06, (1.1, 1, 1), mat('mane', '#CFC8AE', strands=1.6, rim=0.7))
        sph((x - 0.01, -0.06, -0.165), 0.025, (0.9, 1.4, 0.8), mat('muzzle', '#DE9686'))
        for s in (-1, 1): sph((x - 0.01 + s * 0.016, -0.06, -0.135), 0.005, (1, 0.6, 1), flat('pupil0', (0.05, 0.03, 0.02)))
    if 'ingot' in P:   # an oxhide ingot carried on the shoulder
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.2, 0.0, -0.22)); o = bpy.context.object; o.scale = (0.17, 0.12, 0.022); o.rotation_euler = (0.25, -0.35, 0.2)
        add_mod(o, 'SIMPLE_DEFORM', deform_method='TAPER', factor=-0.25); add_mod(o, 'BEVEL', width=0.006, segments=3)
        o.data.materials.append(mat('copper', '#C66A36', gloss=0.6))
    if 'gem' in P:
        cyl((-0.06, -0.06, -0.24), (0, -0.115, -0.33), 0.0018, g); cyl((0.06, -0.06, -0.24), (0, -0.115, -0.33), 0.0018, g)
        sph((0, -0.118, -0.35), 0.022, (1, 0.45, 1.25), g); sph((0, -0.124, -0.35), 0.016, (1, 0.45, 1.2), mat('lapis', '#2350A8', gloss=0.8))
    if 'ramstaff' in P:
        cyl((-0.24, 0.0, -0.7), (-0.24, 0.0, 0.08), 0.012, mat('wood3', '#9A6A3E'))
        sph((-0.24, -0.01, 0.13), 0.04, (0.85, 1.1, 1), mat('ram', '#E9DFC8')); sph((-0.24, 0.0, 0.2), 0.03, (1, 0.4, 1), g)
        for s in (-1, 1):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.022, minor_radius=0.008, location=(-0.24 + s * 0.035, 0.0, 0.13), rotation=(0, math.pi / 2, 0)); bpy.context.object.data.materials.append(mat('horn', '#C9A262'))
    if 'dates' in P:
        for k in range(9):
            sph((0.2 + (k % 3) * 0.022, -0.1, -0.35 - (k // 3) * 0.03 + (k % 2) * 0.01), 0.016, (0.8, 0.8, 1.15), mat('date', '#8A2E1A', gloss=0.5))
        cyl((0.222, -0.1, -0.33), (0.21, -0.08, -0.24), 0.003, mat('stem', '#7A5434'))
    if 'cup' in P:
        cyl((0.17, -0.13, -0.52), (0.17, -0.13, -0.44), 0.012, g); cyl((0.17, -0.13, -0.44), (0.17, -0.13, -0.39), 0.04, g, r2=0.05)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.046, depth=0.004, location=(0.17, -0.13, -0.392), vertices=32); bpy.context.object.data.materials.append(mat('wine', '#5A1A2A'))
    if 'ledger' in P:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.12, -0.14, -0.52)); p = bpy.context.object; p.scale = (0.16, 0.012, 0.2); p.rotation_euler = (0.25, 0.25, 0.15)
        add_mod(p, 'BEVEL', width=0.006, segments=2); p.data.materials.append(mat('tablet', '#D8B57A'))
    if 'chisel' in P:
        cyl((-0.25, 0.06, -0.38), (-0.2, 0.05, -0.18), 0.012, mat('wood', '#8E5A33')); cyl((-0.2, 0.05, -0.18), (-0.18, 0.05, -0.04), 0.008, mat('copper', '#C66A36', gloss=0.6), r2=0.004)
    if 'spear' in P:
        cyl((-0.26, 0.06, -0.8), (-0.26, 0.06, 0.25), 0.01, mat('wood3', '#9A6A3E'))
        bpy.ops.mesh.primitive_cone_add(radius1=0.025, radius2=0, depth=0.12, location=(-0.26, 0.06, 0.31), vertices=4); bpy.context.object.data.materials.append(mat('copper', '#C66A36', gloss=0.6))
    if L.get('sash'):
        cyl((-0.17, -0.05, -0.28), (0.06, -0.135, -0.62), 0.026, mat('leopard', '#D9A447', strands=0, rim=0.4))
        for k in range(7):
            t = k / 6; sph((-0.17 + 0.23 * t + 0.01 * ((k % 2) * 2 - 1), -0.07 - 0.07 * t, -0.29 - 0.33 * t), 0.008, (1, 0.5, 0.8), flat('spot', hexc('#3A2414')))
    if L.get('straps'):
        for s in (-1, 1): cyl((s * 0.15, -0.03, -0.28), (-s * 0.06, -0.135, -0.6), 0.012, mat('strap', '#8E5A33'))

# ---------------------------------------------------------------- scene, camera, ink, render
def setup(res):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24; sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 2; sc.cycles.diffuse_bounces = 0; sc.cycles.glossy_bounces = 0; sc.cycles.transparent_max_bounces = 2
    sc.render.resolution_x = sc.render.resolution_y = res; sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.render.use_freestyle = True; sc.render.line_thickness_mode = 'ABSOLUTE'; sc.render.line_thickness = res / 125.0
    vl = sc.view_layers[0]; fs = vl.freestyle_settings; fs.crease_angle = math.radians(118)
    ls = fs.linesets[0] if fs.linesets else fs.linesets.new('ink')
    ls.select_by_visibility = True; ls.select_by_edge_types = True; ls.select_silhouette = True; ls.select_border = True; ls.select_crease = False; ls.select_contour = False; ls.select_external_contour = True
    ls.select_by_collection = True; ls.collection = bpy.data.collections.get('noline') or bpy.data.collections.new('noline'); ls.collection_negation = 'EXCLUSIVE'
    if ls.collection.name not in sc.collection.children: sc.collection.children.link(ls.collection)
    if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new('ink')
    st = ls.linestyle; st.color = lin(INK); st.thickness = 1.0
    # taper the strokes a little so they look inked
    if not any(m.type == 'ALONG_STROKE' for m in st.thickness_modifiers):
        tm = st.thickness_modifiers.new('taper', 'ALONG_STROKE'); tm.mapping = 'CURVE'; tm.invert = False
        cm = tm.curve.curves[0]; cm.points[0].location = (0, 0.55); cm.points[1].location = (1, 0.55); cm.points.new(0.5, 1.0); tm.curve.update()
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 0
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 85; cam.data.sensor_width = 36
    return cam

def aim_camera(cam, yaw=0.42, pitch=0.08, target=(0, -0.01, -0.06), dist=1.05):
    t = Vector(target); d = Vector((math.sin(yaw), -math.cos(yaw), math.sin(pitch))).normalized()
    cam.location = t + d * dist; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()

def build_char(key, mood):
    bpy.ops.wm.read_factory_settings(use_empty=True); _mats.clear()
    L = dict(LOOKS[key]); L['key'] = key
    M = head_params(L, mood)
    t0 = time.time()
    torso, ts = build_torso(L, M)
    build_collar(L, ts)
    build_props(L, ts)
    body = set(bpy.context.scene.objects)
    head, hs = build_head(L, M)
    build_eyes(L, M)
    build_brows(L, M, hs)
    build_hair(L, hs)
    build_beard(L, M, hs)
    build_ears_jewel(L)
    # mood acting: a small head tilt about the neck
    tilt = {'happy': (0.04, 0, -0.06), 'angry': (0.1, 0, 0), 'sly': (0.0, 0, 0.07), 'surprised': (-0.08, 0, 0), 'thinking': (-0.04, 0, 0.08), 'sad': (0.14, 0, 0)}.get(mood, (0, 0, 0))
    root = bpy.data.objects.new('headroot', None); bpy.context.scene.collection.objects.link(root); root.location = (0, 0.02, -0.12)
    bpy.context.view_layer.update()
    for ob in list(bpy.context.scene.objects):
        if ob not in body and ob is not root and ob.parent is None:
            mw = ob.matrix_world.copy(); ob.parent = root; ob.matrix_parent_inverse = root.matrix_world.inverted(); ob.matrix_world = mw
    root.rotation_euler = (-tilt[0], tilt[1], tilt[2])
    return L, time.time() - t0

def render(key, moods, outdir, res=640):
    os.makedirs(outdir, exist_ok=True)
    for mood in moods:
        L, tb = build_char(key, mood)
        cam = setup(res); yaw = float(os.environ.get('YAW', '0.42'))
        aim_camera(cam, yaw=yaw, pitch=0.12, target=(0, -0.0, -0.075 if L.get('wig') != 'puff' else -0.062), dist=1.04)
        sc = bpy.context.scene; sc.render.filepath = os.path.join(outdir, '%s_%s%s.png' % (key, mood, os.environ.get('TAG', '')))
        if os.environ.get('SAMPLES'): sc.cycles.samples = int(os.environ['SAMPLES'])
        t = time.time(); bpy.ops.render.render(write_still=True)
        print('RENDER', key, mood, 'build %.1fs render %.1fs' % (tb, time.time() - t), flush=True)

if __name__ == '__main__':
    a = sys.argv[1:]
    keys = a[0].split(',') if a else ['h_ahmose']
    moods = a[1].split(',') if len(a) > 1 else ['neutral']
    out = a[2] if len(a) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
    res = int(a[3]) if len(a) > 3 else 640
    for k in keys: render(k, moods, out, res)
