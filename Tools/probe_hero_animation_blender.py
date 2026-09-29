"""Report animated geometry extents in Blender before UE import."""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Tools'))
from hero_jumpx import JumpXHero
for hero_id in ('013', '100', '101'):
    path = ROOT / 'EternalRebirth' / 'SourceArt' / 'Heroes' / hero_id / ('H' + hero_id + '_Animated.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path))
    arm = bpy.data.objects['SK_H' + hero_id]
    model = JumpXHero((path.parent / (hero_id + '.x')).read_bytes())
    bone_names = json.loads((path.parent / 'rig.json').read_text(encoding='utf8'))['bone_names']
    action = bpy.data.actions['AN_H' + hero_id + '_Idle']
    arm.animation_data.action = action
    for mode in ('POSE', 'REST'):
        arm.data.pose_position = mode
        bpy.context.scene.frame_set(1)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        points = []
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            evaluated = obj.evaluated_get(depsgraph)
            mesh = evaluated.to_mesh()
            points.extend((evaluated.matrix_world @ vertex.co)[:] for vertex in mesh.vertices)
            evaluated.to_mesh_clear()
        mins = [min(point[axis] for point in points) for axis in range(3)]
        maxs = [max(point[axis] for point in points) for axis in range(3)]
        print('HERO_ANIM_BOUNDS', hero_id, mode, mins, maxs,
              'root', list(arm.pose.bones[0].matrix.translation), flush=True)
        if mode == 'POSE':
            for index in (0, 1, 2, 10):
                rest = arm.data.bones[bone_names[index]].matrix_local
                pose = arm.pose.bones[bone_names[index]].matrix
                print('HERO_BONE_DELTA', hero_id, index, bone_names[index],
                      'rest', list(rest.translation), 'pose', list(pose.translation),
                      'dot', rest.to_quaternion().dot(pose.to_quaternion()), flush=True)
                if index == 0:
                    print('HERO_ROT', hero_id, 'rest', list(rest.to_quaternion()),
                          'pose', list(pose.to_quaternion()),
                          'source', model.frames(model.bones[0], 'rot',
                                                 model.actions[0]['start'], model.actions[0]['start']).tolist(),
                          flush=True)
