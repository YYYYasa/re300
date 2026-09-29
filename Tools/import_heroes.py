"""Import prepared skinned hero FBXs into the UE content browser."""
from pathlib import Path
import json
import unreal as u

ROOT = Path('G:/Code/UE/EternalRebirth')
ART = ROOT / 'SourceArt' / 'Heroes'
EL = u.EditorAssetLibrary
AT = u.AssetToolsHelpers.get_asset_tools()

for hero_id in ('013', '100', '101'):
    folder = ART / hero_id
    fbx = folder / ('SK_H' + hero_id + '.fbx')
    if not fbx.is_file():
        raise FileNotFoundError(fbx)
    package = '/Game/Art/Heroes/H' + hero_id
    EL.make_directory(package)
    task = u.AssetImportTask()
    task.filename = str(fbx)
    task.destination_path = package
    task.destination_name = 'SK_H' + hero_id
    task.automated = True
    task.save = True
    task.replace_existing = True
    options = u.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.mesh_type_to_import = u.FBXImportType.FBXIT_SKELETAL_MESH
    options.import_mesh = True
    options.import_as_skeletal = True
    options.import_animations = False
    options.import_materials = True
    options.import_textures = True
    options.create_physics_asset = False
    task.options = options
    task.factory = u.FbxFactory()
    AT.import_asset_tasks([task])
    paths = [str(path) for path in task.imported_object_paths]
    meshes = [u.load_asset(path) for path in paths]
    meshes = [mesh for mesh in meshes if isinstance(mesh, u.SkeletalMesh)]
    if not meshes:
        candidate = u.load_asset(package + '/SK_H' + hero_id)
        if isinstance(candidate, u.SkeletalMesh):
            meshes = [candidate]
    if not meshes:
        raise RuntimeError(f'No skeletal mesh imported for {hero_id}: {paths}')
    mesh = meshes[0]
    skeleton = mesh.get_editor_property('skeleton')
    if skeleton is None:
        raise RuntimeError(f'No skeleton for {hero_id}')
    if not EL.save_loaded_asset(skeleton, False):
        raise RuntimeError(f'Could not save skeleton for {hero_id}')
    material_names = []
    for slot in mesh.get_editor_property('materials'):
        material = slot.get_editor_property('material_interface')
        if material:
            material_names.append(material.get_path_name())
            EL.save_loaded_asset(material, False)
    if not EL.save_loaded_asset(mesh, False):
        raise RuntimeError(f'Could not save mesh for {hero_id}')
    EL.save_directory(package, only_if_is_dirty=False, recursive=True)
    report = json.loads((folder / 'source.json').read_text(encoding='utf8'))
    u.log(f"REBIRTH_HERO_IMPORTED id={hero_id} mesh={mesh.get_path_name()} "
          f"skeleton={skeleton.get_path_name()} parts={report['meshes']} "
          f"bones={report['bones']} actions={len(report['actions'])} materials={material_names}")

u.log('REBIRTH: HERO_IMPORT_COMPLETE count=3')
