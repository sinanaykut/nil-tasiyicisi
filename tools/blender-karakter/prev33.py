"""Quick Cycles cel previews for modelling iterations (not part of the export)."""
import bpy, math, os
from mathutils import Vector

def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c)

KEY = Vector((-0.45, -0.8, 0.55)).normalized()
_m = {}
def toon(name, hexcol=None, attr=None):
    if name in _m: return _m[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N): N.remove(n)
    out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); L.new(em.outputs[0], out.inputs[0])
    geo = N.new('ShaderNodeNewGeometry'); dot = N.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; dot.inputs[1].default_value = KEY
    L.new(geo.outputs['Normal'], dot.inputs[0])
    ramp = N.new('ShaderNodeValToRGB'); cr = ramp.color_ramp; cr.interpolation = 'CONSTANT'
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.62, 0.5, 0.55, 1)
    cr.elements[1].position = 0.52; cr.elements[1].color = (1, 0.97, 0.93, 1)
    e = cr.elements.new(0.36); e.color = (0.82, 0.74, 0.74, 1)
    mr = N.new('ShaderNodeMapRange'); mr.inputs[1].default_value = -1; mr.inputs[2].default_value = 1
    L.new(dot.outputs['Value'], mr.inputs[0]); L.new(mr.outputs[0], ramp.inputs[0])
    if attr:
        bc = N.new('ShaderNodeVertexColor'); bc.layer_name = attr; co = bc.outputs[0]
    else:
        bc = N.new('ShaderNodeRGB'); bc.outputs[0].default_value = (*lin(hexcol or '#C98E62'), 1); co = bc.outputs[0]
    mul = N.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
    L.new(co, mul.inputs[6]); L.new(ramp.outputs[0], mul.inputs[7]); L.new(mul.outputs[2], em.inputs['Color'])
    _m[name] = m; return m

def setup(res=(360, 360), lines=True, bg='#E9DCC2'):
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 6; sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.film_transparent = False
    w = sc.world or bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (*lin(bg), 1)
    sc.view_settings.view_transform = 'Standard'
    sc.render.use_freestyle = lines
    if lines:
        vl = sc.view_layers[0]; fs = vl.freestyle_settings
        ls = fs.linesets[0] if fs.linesets else fs.linesets.new('L')
        ls.select_by_visibility = True; ls.select_silhouette = True; ls.select_border = True; ls.select_crease = False
        ls.linestyle.color = (0.17, 0.11, 0.08); ls.linestyle.thickness = 1.6
    return sc

def camera(loc, look, lens=85, ortho=None):
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None:
        cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = lens
    if ortho: cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    cam.location = loc
    d = Vector(look) - Vector(loc); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return cam

def render(path):
    sc = bpy.context.scene; sc.render.filepath = path; bpy.ops.render.render(write_still=True)

def wb(res=(900, 330), outline=True):
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x, sc.render.resolution_y = res
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_cavity = True; sh.cavity_type = 'BOTH'
    sh.show_object_outline = outline; sh.show_shadows = False; sh.background_type = 'VIEWPORT'
    sc.display.shading.background_color = (0.85, 0.8, 0.72)
    sc.render.film_transparent = False
    return sc
