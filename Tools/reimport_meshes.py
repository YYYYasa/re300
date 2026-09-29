"""Replace generated mesh assets; preserve the existing map and its actors."""
import unreal as u
from pathlib import Path
root=Path('G:/Code/UE/EternalRebirth')
at=u.AssetToolsHelpers.get_asset_tools();el=u.EditorAssetLibrary
mesh_path=globals().get('mesh_path','/Game/Art/Meshes_Showcase')
for file in sorted((root/'SourceArt/Meshes').glob('*.fbx')):
    task=u.AssetImportTask();task.filename=str(file);task.destination_path=mesh_path;task.destination_name=file.stem.replace('-','n')
    task.automated=True;task.replace_existing=True;task.save=True
    opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.import_animations=False
    opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False
    opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.generate_lightmap_u_vs=False;opt.static_mesh_import_data.auto_generate_collision=False
    task.options=opt;task.factory=u.FbxFactory();at.import_asset_tasks([task])
    mesh=u.load_asset(mesh_path+'/'+task.destination_name)
    slots=mesh.get_editor_property('static_materials')
    for i,slot in enumerate(slots):
        name='M_LivingWater' if file.stem.startswith('SM_Water') else str(slot.material_slot_name)
        material=u.load_asset('/Game/Art/Materials/'+name)
        if material:slot.set_editor_property('material_interface',material);slots[i]=slot
    mesh.set_editor_property('static_materials',slots);el.save_loaded_asset(mesh,False)
u.log('REBIRTH: REIMPORT_COMPLETE')
exec(Path('G:/Code/UE/Tools/optimize_meshes.py').read_text())
