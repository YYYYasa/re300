"""Import the 64 client walk surfaces as one collision-only static mesh."""
import unreal as u

source = 'G:/Code/UE/EternalRebirth/SourceArt/Collision/SM_Arena_Walkable.fbx'
package = '/Game/Art/Collision'
u.EditorAssetLibrary.make_directory(package)
task = u.AssetImportTask()
task.filename = source
task.destination_path = package
task.destination_name = 'SM_Arena_Walkable'
task.automated = True
task.save = True
task.replace_existing = True
options = u.FbxImportUI()
options.automated_import_should_detect_type = False
options.mesh_type_to_import = u.FBXImportType.FBXIT_STATIC_MESH
options.import_mesh = True
options.import_as_skeletal = False
options.import_materials = False
options.import_textures = False
options.import_animations = False
options.static_mesh_import_data.combine_meshes = True
options.static_mesh_import_data.auto_generate_collision = False
task.options = options
task.factory = u.FbxFactory()
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
mesh = u.load_asset(package + '/SM_Arena_Walkable')
if not isinstance(mesh, u.StaticMesh):
    raise RuntimeError('Walkable mesh import failed: ' + str(task.imported_object_paths))
body = mesh.get_editor_property('body_setup')
if body is None:
    raise RuntimeError('Walkable mesh has no body setup')
body.set_editor_property('collision_trace_flag', u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
body.set_editor_property('double_sided_geometry', True)
editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem) or u.StaticMeshEditorSubsystem()
for section in range(mesh.get_num_sections(0)):
    editor.enable_section_collision(mesh, True, 0, section)
settings = editor.get_lod_build_settings(mesh, 0)
editor.set_lod_build_settings(mesh, 0, settings)
if not u.EditorAssetLibrary.save_loaded_asset(mesh, False):
    raise RuntimeError('Could not save walkable mesh')
u.log('REBIRTH: ARENA_WALKABLE_IMPORTED ' + mesh.get_path_name())
