"""Inspect animation data available for investigating an FBX retarget offset."""
import json
from pathlib import Path
import unreal as u

for name in ('AnimationBlueprintLibrary', 'AnimationLibrary', 'AnimDataModel'):
    cls = getattr(u, name, None)
    if cls:
        u.log('HERO_UE_API ' + name + ' ' + str([method for method in dir(cls)
                                              if any(word in method.lower() for word in ('bone', 'pose', 'transform', 'frame'))]))
u.log('HERO_UE_DOC ' + str(u.AnimationLibrary.get_bone_pose_for_frame.__doc__)[:1800])
u.log('HERO_UE_ROOT_DOC ' + str(u.AnimationLibrary.extract_root_track_transform.__doc__)[:1200])
for hero_id in ('013', '100', '101'):
    base = f'/Game/Art/Heroes/H{hero_id}/'
    mesh = u.load_asset(base + 'SK_H' + hero_id)
    clip = u.load_asset(base + 'AN_H' + hero_id + '_Idle')
    if not mesh or not clip:
        raise RuntimeError('Missing hero or idle clip ' + hero_id)
    u.log(f'HERO_UE_ANIM id={hero_id} length={clip.get_play_length()} frames={u.AnimationLibrary.get_num_frames(clip)} '
          f'skeleton={clip.get_editor_property("skeleton")} mesh_skeleton={mesh.get_editor_property("skeleton")}')
    names = json.loads((Path('G:/Code/UE/EternalRebirth/SourceArt/Heroes') / hero_id / 'rig.json').read_text(encoding='utf8'))['bone_names']
    for index in (0, 1, 2, 10):
        name = names[index]
        pose = u.AnimationLibrary.get_bone_pose_for_frame(clip, name, 0, False)
        u.log(f'HERO_UE_POSE id={hero_id} bone={name} transform={pose}')
