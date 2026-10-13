"""Build Paneb (mesh + rig, no clips) -> out/paneb_mesh.glb and out/paneb.blend.
   run:  python3 -I blender/build_paneb.py [--shots]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh, math
from mathutils import Vector
import common as C, body as B, parts as P

BODY_TRIS = 4600


def decimate(o, tris):
    cur = sum(len(p.vertices) - 2 for p in o.data.polygons)
    m = o.modifiers.new('dec', 'DECIMATE')
    m.decimate_type = 'COLLAPSE'; m.ratio = tris / cur; m.use_symmetry = True; m.symmetry_axis = 'X'
    m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = o
    for mm in list(o.modifiers):
        if mm.type == 'ARMATURE':
            o.modifiers.remove(mm)
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier='dec')


def smooth_normals(o, repeat=18):
    """cel shading wants simple forms: take the normals from a smoothed copy (hands/feet/face kept)"""
    gn = {g.index: g.name for g in o.vertex_groups}
    keep = ('hand', 'index', 'middle', 'ring', 'pinky', 'thumb', 'foot', 'ball')
    vg = o.vertex_groups.new(name='_smooth')
    for v in o.data.vertices:
        k = sum(g.weight for g in v.groups if any(x in gn.get(g.group, '') for x in keep))
        vg.add([v.index], max(0.0, 1.0 - k), 'REPLACE')
    dup = o.copy(); dup.data = o.data.copy(); bpy.context.scene.collection.objects.link(dup)
    for m in list(dup.modifiers): dup.modifiers.remove(m)
    sm = dup.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.9; sm.iterations = repeat; sm.vertex_group = '_smooth'
    dt = o.modifiers.new('dt', 'DATA_TRANSFER'); dt.object = dup; dt.use_loop_data = True; dt.data_types_loops = {'CUSTOM_NORMAL'}
    dt.loop_mapping = 'TOPOLOGY'
    for m in list(o.modifiers):
        if m.type == 'ARMATURE': o.modifiers.remove(m)
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier='dt')
    bpy.data.objects.remove(dup)
    o.vertex_groups.remove(o.vertex_groups['_smooth'])


def paint_body(o):
    me = o.data
    gn = {g.index: g.name for g in o.vertex_groups}
    def w(v, name):
        for g in v.groups:
            if gn[g.group] == name: return g.weight
        return 0.0
    head = {}
    for v in me.vertices:
        head[v.index] = w(v, 'Head')
    hand = {v.index: sum(g.weight for g in v.groups if any(k in gn[g.group] for k in ('hand', 'index', 'middle', 'ring', 'pinky', 'thumb'))) for v in me.vertices}

    def fx(i, co):
        if head[i] > 0.5 and co.y < -0.035 and 1.585 < co.z < 1.79 and abs(co.x) < 0.095:
            return (0.9, P.FX['face'])
        if hand[i] > 0.5:
            return (0.7, P.FX['skin'])
        return (1.0, P.FX['skin'])
    P.paint(o, lambda i, co: P.PAL['skin'], fx)


def build(shots=False):
    arm, body = B.load_base(C)
    B.slim(arm, body)
    B.smooth_face(arm, body)
    body.name = 'Paneb'
    F = P.Fit(body)
    wg = P.wig(F)
    parts = [wg[0], P.headband(wg)]
    kl = P.kilt(F)
    parts += [kl[0], P.belt(F, kl), P.collar(F), P.armband(F, 'l'), P.armband(F, 'r')]
    for o in parts:
        n = P.orient_out(o, F)
        print('part', o.name, 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons), 'flipped', n)
    # faces that are always under the kilt (hips/crotch) are never seen: drop them
    bm = bmesh.new(); bm.from_mesh(body.data)
    hid = [f for f in bm.faces if all(0.74 < v.co.z < 0.995 and abs(v.co.x) < 0.25 for v in f.verts)]
    bmesh.ops.delete(bm, geom=hid, context='FACES')
    bm.to_mesh(body.data); bm.free(); body.data.update()
    print('hidden faces removed', len(hid))
    decimate(body, BODY_TRIS)
    for p in body.data.polygons: p.use_smooth = True
    smooth_normals(body)
    paint_body(body)
    # join
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    with bpy.context.temp_override(active_object=body, selected_editable_objects=parts + [body], selected_objects=parts + [body]):
        bpy.ops.object.join()
    body.parent = arm
    body.matrix_parent_inverse.identity()
    m = body.modifiers.new('Armature', 'ARMATURE'); m.object = arm
    # limit to 4 influences, normalise
    bpy.context.view_layer.objects.active = body
    with bpy.context.temp_override(object=body, active_object=body):
        bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
        bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
    for p in body.data.polygons: p.use_smooth = True
    me = body.data
    me.color_attributes.active_color = me.color_attributes['Col']
    try: me.color_attributes.render_color_index = me.color_attributes.find('Col')
    except Exception: pass
    print('TOTAL tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(me.vertices))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, 'paneb.blend'))
    if shots:
        cam = C.render_setup((700, 700))
        bpy.context.scene.display.shading.color_type = 'VERTEX'
        o = C.WORK + '/s2_'
        C.shot(o + 'a.png', (1.2, -4.6, 1.0), (0, 0, 0.95), 50)
        C.shot(o + 'b.png', (-4.8, 0.4, 1.0), (0, 0, 0.95), 50)
        C.shot(o + 'c.png', (0.35, -1.25, 1.66), (0, 0, 1.62), 70)
        C.shot(o + 'd.png', (-0.9, 0.9, 1.7), (0, 0, 1.62), 70)
    return arm, body


if __name__ == '__main__':
    build('--shots' in sys.argv)
