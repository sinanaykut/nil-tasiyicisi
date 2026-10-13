"""Step 3: retarget UAL1/UAL2 clips onto Paneb's (base-character) skeleton in world space, add three
   keyframed clips built with 2-bone IK on top of the idle (wave, think, shrug), bake at 20 fps, export GLB.
   run:  python3 -I blender/anims.py      (needs out/paneb.blend from build_paneb.py)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, math
from mathutils import Vector, Matrix, Quaternion
import common as C

FPS = 20
SRC_FPS = 24.0          # the glTF importer lays the UAL keys out at 24 fps
# name: (source action, loop, trim seconds (start, end) or None)
CLIPS = {
    'idle':  ('Idle_Loop', True, None),
    'talk':  ('Idle_Talking_Loop', True, None),
    'angry': ('Idle_FoldArms_Loop', True, None),
    'cheer': ('Yes', False, None),
    'happy': ('Dance_Loop', True, None),
    'walk':  ('Walk_Loop', True, None),
    'carry': ('Walk_Carry_Loop', True, None),
}
SKIP = lambda n: n.endswith('_leaf_l') or n.endswith('_leaf_r')


def order(arm):
    out = []
    def rec(b):
        out.append(b)
        for c in b.children: rec(c)
    for b in arm.data.bones:
        if not b.parent: rec(b)
    return out


class Retarget:
    def __init__(self, src, tgt):
        self.src, self.tgt = src, tgt
        self.bones = order(tgt)
        sb, tb = src.data.bones, tgt.data.bones
        self.O = {b.name: sb[b.name].matrix_local.to_quaternion().inverted() @ b.matrix_local.to_quaternion() for b in self.bones}
        self.restT = {b.name: b.matrix_local.copy() for b in self.bones}
        self.off = {b.name: (b.parent.matrix_local.inverted() @ b.matrix_local) if b.parent else b.matrix_local.copy() for b in self.bones}
        self.hip_ratio = tb['pelvis'].head_local.z / sb['pelvis'].head_local.z
        self.hipS = sb['pelvis'].head_local.copy(); self.hipT = tb['pelvis'].head_local.copy()

    def src_pose(self, act, t):
        sc = bpy.context.scene
        self.src.animation_data.action = act
        try:
            if act.slots: self.src.animation_data.action_slot = act.slots[0]
        except Exception: pass
        f = act.frame_range[0] + t * SRC_FPS
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        return {pb.name: pb.matrix.copy() for pb in self.src.pose.bones}

    def solve(self, S, override=None, t=0.0):
        """S: source armature-space matrices -> target armature-space M and local bases"""
        M, R, basis = {}, {}, {}
        for b in self.bones:
            n = b.name
            Rs = S[n].to_quaternion()
            if b.parent:
                p = b.parent.name
                Rsp = S[p].to_quaternion()
                rel = self.O[p].inverted() @ Rsp.inverted() @ Rs @ self.O[n]
                Rt = R[p] @ rel
                pos = M[p] @ self.off[n].translation
            else:
                Rt = Rs @ self.O[n]
                pos = self.restT[n].translation.copy()
            if n == 'pelvis':
                pos = self.hipT + (S[n].translation - self.hipS) * self.hip_ratio
            if override:
                r2 = override(n, pos, Rt, M, t)
                if r2 is not None: Rt = r2
            R[n] = Rt
            M[n] = Matrix.Translation(pos) @ Rt.to_matrix().to_4x4()
            if b.parent:
                basis[n] = self.off[n].inverted() @ M[b.parent.name].inverted() @ M[n]
            else:
                basis[n] = self.restT[n].inverted() @ M[n]
        return M, R, basis


# ---------- IK helpers (armature space, Blender bones point along +Y) ----------
def aim(Rt, d):
    y = Rt @ Vector((0, 1, 0))
    return y.rotation_difference(d.normalized()) @ Rt


def two_bone(S, T, a, b, pole):
    d = T - S; L = d.length
    L = min(L, (a + b) * 0.999); u = d.normalized()
    ca = (a * a + L * L - b * b) / (2 * a * L); sa = math.sqrt(max(0.0, 1 - ca * ca))
    v = (pole - u * pole.dot(u)).normalized()
    E = S + (u * ca + v * sa) * a
    return E, S + u * L


def smooth(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def make_ik_clip(rt, idle_act, dur, arms_fn, extra_fn=None, open_hand=False):
    """arms_fn(t) -> {side: (target, pole, weight, hand_twist_deg)};  extra_fn(name, Rt, t) -> Rt or None"""
    tgt = rt.tgt
    L = {s: (tgt.data.bones['upperarm_' + s].length, tgt.data.bones['lowerarm_' + s].length) for s in 'lr'}
    idle_dur = (idle_act.frame_range[1] - idle_act.frame_range[0]) / SRC_FPS
    st = {}

    def ov(n, pos, Rt, M, t):
        A = st['arms']
        for s, (T, pole, w, tw) in A.items():
            if w <= 0: continue
            if n == 'upperarm_' + s:
                E, Tc = two_bone(pos, T, L[s][0], L[s][1], pole)
                st['E' + s] = E; st['T' + s] = Tc
                R2 = aim(Rt, E - pos)
                return R2 if w >= 1 else Rt.slerp(R2, w)
            if n == 'lowerarm_' + s and ('E' + s) in st:
                R2 = aim(Rt, st['T' + s] - pos)
                return R2 if w >= 1 else Rt.slerp(R2, w)
            if n == 'hand_' + s and tw:
                ax = Rt @ Vector((0, 1, 0))
                return Quaternion(ax, math.radians(tw) * w) @ Rt
        if st.get('open') and n[-1] in st['open'] and n.split('_')[0] in ('index', 'middle', 'ring', 'pinky', 'thumb'):
            p = tgt.data.bones[n].parent.name
            Rr = M[p].to_quaternion() @ rt.off[n].to_quaternion()
            return Rt.slerp(Rr, st['openw'][n[-1]])
        if extra_fn:
            return extra_fn(n, Rt, t)
        return None
    frames = []
    nf = int(round(dur * FPS)) + 1
    for k in range(nf):
        t = k / FPS
        S = rt.src_pose(idle_act, t % idle_dur)
        st.clear(); st['arms'] = arms_fn(t)
        for sd, (T_, pl, w_, tw) in st['arms'].items():
            if open_hand: st.setdefault('open', set()).add(sd); st.setdefault('openw', {})[sd] = w_
        frames.append(rt.solve(S, ov, t)[2])
    return frames


def bake(rt, name, frames):
    tgt = rt.tgt
    act = bpy.data.actions.new(name)
    tgt.animation_data_create(); tgt.animation_data.action = act
    for pb in tgt.pose.bones: pb.rotation_mode = 'QUATERNION'
    for k, B in enumerate(frames):
        for b in rt.bones:
            n = b.name
            if SKIP(n): continue
            pb = tgt.pose.bones[n]
            pb.rotation_quaternion = B[n].to_quaternion()
            pb.keyframe_insert('rotation_quaternion', frame=k)
            if n == 'pelvis':
                pb.location = B[n].translation
                pb.keyframe_insert('location', frame=k)
    act.use_fake_user = True
    print('baked', name, len(frames), 'frames')
    return act


def main():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(C.OUT, 'paneb.blend'))
    tgt = bpy.data.objects['Armature']
    keep = set(bpy.data.objects)
    o1 = C.import_gltf(C.UAL1)
    src = [o for o in o1 if o.type == 'ARMATURE'][0]
    C.import_gltf(C.UAL2)
    for o in list(bpy.data.objects):
        if o not in keep and o != src: bpy.data.objects.remove(o)
    src.animation_data_create()
    ual = {a.name: a for a in bpy.data.actions}
    rt = Retarget(src, tgt)
    made = []
    for name, (an, loop, trim) in CLIPS.items():
        act = ual.get(an) or ual.get(an + '.001')
        dur = (act.frame_range[1] - act.frame_range[0]) / SRC_FPS
        nf = int(round(dur * FPS)) + 1
        frames = [rt.solve(rt.src_pose(act, min(dur, k / FPS)))[2] for k in range(nf)]
        made.append(bake(rt, name, frames))
    idle = ual['Idle_Loop']
    tb = tgt.data.bones
    shR = tb['upperarm_r'].head_local; shL = tb['upperarm_l'].head_local

    # wave: right hand up beside the head, forearm swinging, 1.9 s one-shot
    def wave_arms(t):
        w = smooth(t / 0.35) * smooth((1.9 - t) / 0.4)
        sw = math.sin((t - 0.3) * 2 * math.pi * 2.0) if t > 0.3 else 0
        T = Vector((-0.40 + 0.055 * sw, -0.06, 1.74 + 0.012 * abs(sw)))
        return {'r': (T, Vector((-0.6, 0.3, -1.0)), w, -25 * sw)}

    def wave_x(n, Rt, t):
        w = smooth(t / 0.35) * smooth((1.9 - t) / 0.4)
        if n == 'Head':
            return Quaternion(Vector((0, 1, 0)), math.radians(-6) * w) @ Rt
        if n == 'spine_03':
            return Quaternion(Vector((0, 1, 0)), math.radians(-4) * w) @ Rt
        return None
    made.append(bake(rt, 'wave', make_ik_clip(rt, idle, 1.9, wave_arms, wave_x, open_hand=True)))

    # think: right hand to the chin, head tilted, slow loop 3 s
    def think_arms(t):
        k = math.sin(t / 3.0 * 2 * math.pi)
        T = Vector((-0.07 + 0.004 * k, -0.21, 1.40 + 0.006 * k))
        T2 = Vector((0.03, -0.12, 1.20))
        return {'r': (T, Vector((-0.5, 0.1, -1.0)), 1.0, 0), 'l': (T2, Vector((0.7, 0.4, -0.6)), 1.0, 0)}

    def think_x(n, Rt, t):
        k = math.sin(t / 3.0 * 2 * math.pi)
        if n == 'Head':
            return Quaternion(Vector((0, 1, 0)), math.radians(9 + 2 * k)) @ Quaternion(Vector((1, 0, 0)), math.radians(7)) @ Rt
        return None
    made.append(bake(rt, 'think', make_ik_clip(rt, idle, 3.0, think_arms, think_x)))

    # shrug: both forearms out, palms up, shoulders up, 1.5 s one-shot
    def shrug_w(t): return smooth(t / 0.3) * smooth((1.5 - t) / 0.35)

    def shrug_arms(t):
        w = shrug_w(t)
        return {'r': (Vector((-0.36, -0.2, 1.12)), Vector((-0.3, 0.8, -0.6)), w, 70),
                'l': (Vector((0.36, -0.2, 1.12)), Vector((0.3, 0.8, -0.6)), w, -70)}

    def shrug_x(n, Rt, t):
        w = shrug_w(t)
        if n == 'clavicle_l': return Quaternion(Vector((0, 1, 0)), math.radians(-10) * w) @ Rt
        if n == 'clavicle_r': return Quaternion(Vector((0, 1, 0)), math.radians(10) * w) @ Rt
        if n == 'Head': return Quaternion(Vector((0, 1, 0)), math.radians(10) * w) @ Rt
        return None
    made.append(bake(rt, 'shrug', make_ik_clip(rt, idle, 1.5, shrug_arms, shrug_x, open_hand=True)))

    # clean up: only our actions, only Paneb's rig
    bpy.data.objects.remove(src)
    for a in list(bpy.data.actions):
        if a not in made: bpy.data.actions.remove(a)
    tgt.animation_data.action = None
    for pb in tgt.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    sc = bpy.context.scene
    sc.render.fps = FPS; sc.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, 'paneb_anim.blend'))
    me = bpy.data.objects['Paneb'].data
    for uv in list(me.uv_layers): me.uv_layers.remove(uv)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['Paneb'].select_set(True); tgt.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(C.OUT, 'paneb_raw.glb'), export_format='GLB', use_selection=True,
                              export_texcoords=False, export_normals=True, export_tangents=False, export_materials='NONE',
                              export_vertex_color='NAME', export_vertex_color_name='Col', export_all_vertex_colors=False,
                              export_attributes=True, export_extras=False, export_yup=True, export_skins=True,
                              export_influence_nb=4, export_animations=True, export_animation_mode='ACTIONS',
                              export_force_sampling=True, export_frame_step=1, export_optimize_animation_size=True,
                              export_anim_single_armature=True, export_reset_pose_bones=True, export_morph=False,
                              export_def_bones=False, export_leaf_bone=False)
    print('exported', os.path.getsize(os.path.join(C.OUT, 'paneb_raw.glb')))


if __name__ == '__main__':
    main()
