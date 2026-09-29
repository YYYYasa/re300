"""Import H100 effect geometry, original textures and portraits, with UE additive materials."""
from pathlib import Path
import json
import unreal as u

root = Path('G:/Code/UE/EternalRebirth/SourceArt/Effects/H100')
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf8'))
base = '/Game/Art/Heroes/H100/Effects'
assets = u.EditorAssetLibrary
tools = u.AssetToolsHelpers.get_asset_tools()
ml = u.MaterialEditingLibrary

def import_file(filename, package, name, static_mesh=False):
    assets.make_directory(package)
    task = u.AssetImportTask()
    task.filename = str(filename)
    task.destination_path = package
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    if not static_mesh:
        factory = u.TextureFactory()
        factory.set_editor_property('udim_regex_pattern', r'^(DISABLED_UDIM)([0-9]{4})$')
        task.factory = factory
        task.replace_existing_settings = True
    if static_mesh:
        options = u.FbxImportUI()
        options.automated_import_should_detect_type = False
        options.mesh_type_to_import = u.FBXImportType.FBXIT_STATIC_MESH
        options.import_as_skeletal = False
        options.import_animations = False
        options.import_materials = False
        options.import_textures = False
        options.static_mesh_import_data.combine_meshes = True
        options.static_mesh_import_data.auto_generate_collision = False
        task.options = options
        task.factory = u.FbxFactory()
    tools.import_asset_tasks([task])
    result = u.load_asset(package + '/' + name)
    if not result:
        raise RuntimeError('Failed to import ' + str(filename))
    if isinstance(result, u.Texture2D):
        result.set_editor_property('virtual_texture_streaming', False)
        assets.save_loaded_asset(result, False)
    return result

materials = {}
for stem, info in manifest['textures'].items():
    texture = import_file(root / info['file'], base + '/Textures', 'T_' + stem)
    package = base + '/Materials'
    assets.make_directory(package)
    name = 'M_' + stem
    mat = u.load_asset(package + '/' + name) or tools.create_asset(name, package, u.Material, u.MaterialFactoryNew())
    ml.delete_all_material_expressions(mat)
    mat.set_editor_property('blend_mode', u.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided', True)
    sample = ml.create_material_expression(mat, u.MaterialExpressionTextureSample, -650, 0)
    sample.set_editor_property('texture', texture)
    tint = ml.create_material_expression(mat, u.MaterialExpressionVectorParameter, -650, 230)
    tint.set_editor_property('parameter_name', 'Tint')
    tint.set_editor_property('default_value', u.LinearColor(1, 1, 1, 1))
    color = ml.create_material_expression(mat, u.MaterialExpressionMultiply, -350, 0)
    ml.connect_material_expressions(sample, 'RGB', color, 'A')
    ml.connect_material_expressions(tint, '', color, 'B')
    brightness = ml.create_material_expression(mat, u.MaterialExpressionScalarParameter, -350, 230)
    brightness.set_editor_property('parameter_name', 'Brightness')
    brightness.set_editor_property('default_value', 2.)
    emission = ml.create_material_expression(mat, u.MaterialExpressionMultiply, -100, 0)
    ml.connect_material_expressions(color, '', emission, 'A')
    ml.connect_material_expressions(brightness, '', emission, 'B')
    opacity = ml.create_material_expression(mat, u.MaterialExpressionScalarParameter, -350, 420)
    opacity.set_editor_property('parameter_name', 'Opacity')
    opacity.set_editor_property('default_value', 1.)
    alpha = ml.create_material_expression(mat, u.MaterialExpressionMultiply, -100, 350)
    ml.connect_material_expressions(sample, 'A', alpha, 'A')
    ml.connect_material_expressions(opacity, '', alpha, 'B')
    ml.connect_material_property(emission, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    ml.connect_material_property(alpha, '', u.MaterialProperty.MP_OPACITY)
    ml.recompile_material(mat)
    assets.save_loaded_asset(mat, False)
    materials[stem] = mat

mesh_count = 0
for entry in manifest['source_effects']:
    if 'fbx' not in entry:
        continue
    mesh = import_file(root / entry['fbx'], base + '/Meshes', 'SM_' + entry['name'], True)
    slots = mesh.get_editor_property('static_materials')
    for index, slot in enumerate(slots):
        key = str(slot.material_slot_name).removeprefix('FX_').split('.')[0]
        if key in materials:
            slot.set_editor_property('material_interface', materials[key])
            slots[index] = slot
    mesh.set_editor_property('static_materials', slots)
    assets.save_loaded_asset(mesh, False)
    mesh_count += 1

for key, info in manifest['ui'].items():
    name = 'T_H100_Portrait' if key == 'chara_0100' else 'T_H100_' + key
    tex = import_file(root / info['file'], '/Game/Art/Heroes/H100/UI', name)
    tex.set_editor_property('never_stream', True)
    assets.save_loaded_asset(tex, False)

report = dict(effect_sources=len(manifest['source_effects']), static_meshes=mesh_count,
              textures=len(materials), ui_images=len(manifest['ui']),
              particle_only_sources=[x['name'] for x in manifest['source_effects'] if not x['meshes']],
              source_config_files=len(manifest['source_configs']))
(root / 'ue_import_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
u.log('REBIRTH: H100_EFFECTS_IMPORTED ' + json.dumps(report))
