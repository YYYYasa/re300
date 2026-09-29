"""Import every named animation clip from H100's base JumpX action table."""
from pathlib import Path
import json
import unreal as u

root = Path('G:/Code/UE/EternalRebirth/SourceArt/Heroes/100')
package = '/Game/Art/Heroes/H100'
actions = json.loads((root / 'source.json').read_text(encoding='utf8'))['actions']
skeleton = u.load_asset(package + '/SK_H100_Skeleton')
if not isinstance(skeleton, u.Skeleton):
    raise RuntimeError('H100 skeleton missing')
tools = u.AssetToolsHelpers.get_asset_tools()
tasks = []
for action in actions:
    name = 'AN_H100_' + action['name']
    if isinstance(u.load_asset(package + '/' + name), u.AnimSequence):
        continue
    source = root / (name + '.fbx')
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
    options.mesh_type_to_import = getattr(u.FBXImportType, 'FBXIT_ANIMATION', u.FBXImportType.FBXIT_SKELETAL_MESH)
    options.import_mesh = False
    options.import_as_skeletal = True
    options.import_animations = True
    options.import_materials = False
    options.import_textures = False
    options.skeleton = skeleton
    task.options = options
    task.factory = u.FbxFactory()
    tasks.append((name, task))
for name, task in tasks:
    tools.import_asset_tasks([task])
    asset = u.load_asset(package + '/' + name)
    if not isinstance(asset, u.AnimSequence):
        raise RuntimeError('Import failed for ' + name + ': ' + str(task.imported_object_paths))
    if not u.EditorAssetLibrary.save_loaded_asset(asset, False):
        raise RuntimeError('Save failed for ' + name)
    u.log('REBIRTH_H100_ACTION ' + name)
available = sum(isinstance(u.load_asset(package + '/AN_H100_' + action['name']), u.AnimSequence)
                for action in actions)
if available != len(actions):
    raise RuntimeError('Only {} of {} action assets are available'.format(available, len(actions)))
u.log('REBIRTH: H100_ACTIONS_COMPLETE count=' + str(available) + ' imported=' + str(len(tasks)))
