"""Export idle, run and first attack clips from JumpX bone tracks to FBX."""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from hero_jumpx import JumpXHero

ART = ROOT / 'EternalRebirth' / 'SourceArt' / 'Heroes'


def bone_order(bones):
    ready = []
    unseen = set(range(len(bones)))
    while unseen:
        found = [index for index in unseen if bones[index].parent < 0 or bones[index].parent in ready]
        if not found:
            raise ValueError('Bone hierarchy contains a cycle')
        ready.extend(sorted(found))
        unseen.difference_update(found)
    return ready


def select_clips(model, hero_id):
    result = []
    for label, predicate in (
        ('Idle', lambda name: name == 'bat_idle'),
        ('Run', lambda name: name == 'bat_run'),
        ('Attack', lambda name: name.startswith('single_attack_attcom')),
    ):
        match = next((action for action in model.actions if predicate(action['name'])), None)
        if match:
            result.append((label, match))
    if hero_id == '100':
        result.extend((action['name'], action) for action in model.actions)
    return result


def make_clip(hero_id, arm, model, label, clip, order, bone_names):
    first, last = clip['start'], clip['end']
    duration = last - first + 1
    export_frames = max(duration, 2)
    tracks = []
    for bone in model.bones:
        tracks.append((model.frames(bone, 'pos', first, last),
                       model.frames(bone, 'rot', first, last),
                       model.frames(bone, 'scale', first, last)))
    action = bpy.data.actions.new('AN_H' + hero_id + '_' + label)
    action.use_fake_user = True
    arm.animation_data_create()
    arm.animation_data.action = action
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = export_frames
    for frame in range(export_frames):
        source_frame = min(frame, duration - 1)
        scene.frame_set(frame + 1)
        worlds = {}
        for index in order:
            bone = model.bones[index]
            position, rotation, scaling = tracks[index]
            if position is None or rotation is None:
                world = arm.data.bones[bone_names[index]].matrix_local.copy()
            else:
                p = Vector([float(v) for v in position[source_frame]])
                x, y, z, w = [float(v) for v in rotation[source_frame]]
                q = Quaternion((w, x, y, z)).inverted()
                s = Vector([float(v) for v in scaling[source_frame]]) if scaling is not None else Vector((1, 1, 1))
                source_world = Matrix.Translation(p) @ q.to_matrix().to_4x4() @ Matrix.Diagonal((s.x, s.y, s.z, 1.))
                source_rest = Matrix(bone.inverse_bind.tolist()).inverted().transposed()
                blender_rest = arm.data.bones[bone_names[index]].matrix_local
                world = source_world @ source_rest.inverted() @ blender_rest
            worlds[index] = world
        for index in order:
            bone = model.bones[index]
            pose = arm.pose.bones[bone_names[index]]
            rest = arm.data.bones[bone_names[index]].matrix_local
            world = worlds[index]
            if bone.parent >= 0:
                parent_rest = arm.data.bones[bone_names[bone.parent]].matrix_local
                parent_world = worlds[bone.parent]
                basis = rest.inverted() @ parent_rest @ parent_world.inverted() @ world
            else:
                basis = rest.inverted() @ world
            pose.rotation_mode = 'QUATERNION'
            pose.matrix_basis = basis
        bpy.context.view_layer.update()
        if frame == 0:
            error = max((arm.pose.bones[bone_names[index]].matrix.translation - worlds[index].translation).length
                        for index in order)
            if error > 1.0:
                raise RuntimeError(f'{hero_id} {label}: bone pose mismatch {error:.2f} cm')
        for pose in arm.pose.bones:
            pose.keyframe_insert(data_path='location', frame=frame + 1, group=pose.name)
            pose.keyframe_insert(data_path='rotation_quaternion', frame=frame + 1, group=pose.name)
            pose.keyframe_insert(data_path='scale', frame=frame + 1, group=pose.name)
    scene.frame_set(1)
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    out = ART / hero_id / ('AN_H' + hero_id + '_' + label + '.fbx')
    bpy.ops.export_scene.fbx(filepath=str(out), use_selection=True,
                             object_types={'ARMATURE'}, add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_actions=False,
                             bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.,
                             axis_forward='-Y', axis_up='Z', use_space_transform=True,
                             apply_unit_scale=True)
    print('HERO_ANIMATION', hero_id, label, clip['name'], duration,
          out.stat().st_size, flush=True)


def convert(hero_id, only_action=None):
    folder = ART / hero_id
    bpy.ops.wm.open_mainfile(filepath=str(folder / ('H' + hero_id + '.blend')))
    arm = bpy.data.objects['SK_H' + hero_id]
    model = JumpXHero((folder / (hero_id + '.x')).read_bytes())
    if len(arm.pose.bones) != len(model.bones):
        raise RuntimeError('Bone count changed since mesh export')
    bone_names = json.loads((folder / 'rig.json').read_text(encoding='utf8'))['bone_names']
    order = bone_order(model.bones)
    for label, clip in select_clips(model, hero_id):
        if only_action and label != only_action:
            continue
        make_clip(hero_id, arm, model, label, clip, order, bone_names)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder / ('H' + hero_id + '_Animated.blend')))


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['013', '100', '101']
    if len(args) == 2 and args[1].startswith('only='):
        convert(args[0], args[1][5:])
    else:
        for selected in args:
            convert(selected)
