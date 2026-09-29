"""Import the nine extracted hero clips against their saved UE skeletons."""
from pathlib import Path
import unreal as u

ROOT = Path('G:/Code/UE/EternalRebirth/SourceArt/Heroes')
EL = u.EditorAssetLibrary
AT = u.AssetToolsHelpers.get_asset_tools()
count = 0

for hero_id in ('013', '100', '101'):
    package = '/Game/Art/Heroes/H' + hero_id
    skeleton = u.load_asset(package + '/SK_H' + hero_id + '_Skeleton')
    if not isinstance(skeleton, u.Skeleton):
        raise RuntimeError(f'Missing saved hero skeleton {hero_id}')
    for label in ('Idle', 'Run', 'Attack'):
        name = 'AN_H' + hero_id + '_' + label
        source = ROOT / hero_id / (name + '.fbx')
        if not source.is_file():
            raise FileNotFoundError(source)
        task = u.AssetImportTask()
        task.filename = str(source)
        task.destination_path = package
        task.destination_name = name
        task.automated = True
        task.save = True
        task.replace_existing = True
        options = u.FbxImportUI()
        options.automated_import_should_detect_type = False
        options.mesh_type_to_import = getattr(u.FBXImportType, 'FBXIT_ANIMATION',
                                               u.FBXImportType.FBXIT_SKELETAL_MESH)
        options.import_mesh = False
        options.import_as_skeletal = True
        options.import_animations = True
        options.import_materials = False
        options.import_textures = False
        options.skeleton = skeleton
        task.options = options
        task.factory = u.FbxFactory()
        AT.import_asset_tasks([task])
        paths = [str(path) for path in task.imported_object_paths]
        sequence = u.load_asset(package + '/' + name)
        if not isinstance(sequence, u.AnimSequence):
            sequence = next((u.load_asset(path) for path in paths
                             if isinstance(u.load_asset(path), u.AnimSequence)), None)
        if not isinstance(sequence, u.AnimSequence):
            raise RuntimeError(f'Clip import failed for {name}: {paths}')
        if not EL.save_loaded_asset(sequence, False):
            raise RuntimeError(f'Clip save failed for {name}')
        u.log(f'REBIRTH_HERO_ANIM id={hero_id} clip={label} asset={sequence.get_path_name()}')
        count += 1

u.log(f'REBIRTH: HERO_ANIMATIONS_COMPLETE count={count}')
