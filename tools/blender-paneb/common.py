"""Shared helpers for the Paneb build (Blender 5.x, run with: python3 -I script.py)."""
import bpy, os, math
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
ASSETS = os.path.join(WORK, 'assets')
BASE_MALE = os.path.join(ASSETS, 'base/Universal Base Characters[Standard]/Base Characters/Godot - UE/Superhero_Male_FullBody.gltf')
UAL1 = os.path.join(ASSETS, 'ual1/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb')
UAL2 = os.path.join(ASSETS, 'ual2/Universal Animation Library 2[Standard]/Unreal-Godot/UAL2_Standard.glb')
OUT = os.path.join(WORK, 'out')
os.makedirs(OUT, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_gltf(p):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=p)
    return [o for o in bpy.data.objects if o not in before]


def fcurves_of(act):
    """Blender 4.4+/5.x layered actions vs legacy."""
    try:
        return list(act.fcurves)
    except Exception:
        out = []
        for l in act.layers:
            for s in l.strips:
                for cb in s.channelbags:
                    out.extend(cb.fcurves)
        return out


def render_setup(res=(800, 800)):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'VERTEX'
    sc.render.film_transparent = False
    cam = bpy.data.objects.get('cam')
    if not cam:
        cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
        sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def shot(path, loc, target, lens=50):
    sc = bpy.context.scene
    cam = sc.camera
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
