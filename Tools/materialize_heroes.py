"""Import original hero textures, build lit materials and bind skeletal slots."""
from pathlib import Path
import json
import unreal as u

ROOT = Path('G:/Code/UE/EternalRebirth')
ART = ROOT / 'SourceArt' / 'Heroes'
EL = u.EditorAssetLibrary
AT = u.AssetToolsHelpers.get_asset_tools()
ML = u.MaterialEditingLibrary
BASE = '/Game/Art/Heroes/Materials'
EL.make_directory(BASE)


def master(name, masked):
    path = BASE + '/' + name
    material = u.load_asset(path) or AT.create_asset(name, BASE, u.Material, u.MaterialFactoryNew())
    ML.delete_all_material_expressions(material)
    material.set_editor_property('two_sided', True)
    if masked:
        material.set_editor_property('blend_mode', u.BlendMode.BLEND_MASKED)
    texture = ML.create_material_expression(material, u.MaterialExpressionTextureSampleParameter2D, 0, 0)
    texture.set_editor_property('parameter_name', 'Albedo')
    texture.set_editor_property('texture', u.load_asset('/Engine/EngineResources/DefaultTexture'))
    ML.connect_material_property(texture, '', u.MaterialProperty.MP_BASE_COLOR)
    roughness = ML.create_material_expression(material, u.MaterialExpressionConstant, 0, 240)
    roughness.set_editor_property('r', .62 if not masked else .78)
    ML.connect_material_property(roughness, '', u.MaterialProperty.MP_ROUGHNESS)
    specular = ML.create_material_expression(material, u.MaterialExpressionConstant, 0, 420)
    specular.set_editor_property('r', .32)
    ML.connect_material_property(specular, '', u.MaterialProperty.MP_SPECULAR)
    if masked:
        ML.connect_material_property(texture, 'A', u.MaterialProperty.MP_OPACITY_MASK)
    usage = getattr(u.MaterialUsage, 'MATUSAGE_SKELETAL_MESH', None)
    if usage is not None:
        ML.set_material_usage(material, usage)
    ML.layout_material_expressions(material)
    ML.recompile_material(material)
    if not EL.save_loaded_asset(material, False):
        raise RuntimeError('Could not save ' + path)
    return material


opaque = master('M_HeroSkin', False)
cutout = master('M_HeroCutout', True)

for hero_id in ('013', '100', '101'):
    folder = ART / hero_id
    report = json.loads((folder / 'source.json').read_text(encoding='utf8'))
    package = '/Game/Art/Heroes/H' + hero_id
    texture_package = package + '/Textures'
    EL.make_directory(texture_package)
    tasks = []
    unique = {meta['file']: meta for meta in report['textures'].values()}
    for file in unique:
        task = u.AssetImportTask()
        task.filename = str(folder / file)
        task.destination_path = texture_package
        task.destination_name = 'T_' + Path(file).stem
        task.automated = True
        task.save = True
        task.replace_existing = True
        tasks.append(task)
    AT.import_asset_tasks(tasks)
    for file in unique:
        if not isinstance(u.load_asset(texture_package + '/T_' + Path(file).stem), u.Texture2D):
            raise RuntimeError(f'Texture import failed for {hero_id}/{file}')

    mesh = u.load_asset(package + '/SK_H' + hero_id)
    if not isinstance(mesh, u.SkeletalMesh):
        raise RuntimeError(f'Skeletal mesh missing for {hero_id}')
    slots = list(mesh.get_editor_property('materials'))
    for slot in slots:
        slot_name = str(slot.get_editor_property('material_slot_name'))
        prefix = 'M_H' + hero_id + '_'
        if not slot_name.startswith(prefix):
            raise RuntimeError(f'Unexpected slot {slot_name} on {hero_id}')
        texture_stem = slot_name[len(prefix):].lower()
        texture_meta = next((meta for meta in report['textures'].values()
                             if Path(meta['file']).stem.lower() == texture_stem), None)
        if not texture_meta:
            raise RuntimeError(f'No source texture for {hero_id}/{slot_name}')
        texture = u.load_asset(texture_package + '/T_' + texture_stem)
        instance_name = 'MI_H' + hero_id + '_' + texture_stem
        instance = u.load_asset(package + '/' + instance_name) or AT.create_asset(
            instance_name, package, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        ML.set_material_instance_parent(instance, cutout if texture_meta['masked'] else opaque)
        ML.set_material_instance_texture_parameter_value(instance, 'Albedo', texture)
        if not EL.save_loaded_asset(instance, False):
            raise RuntimeError(f'Material instance save failed: {instance_name}')
        slot.set_editor_property('material_interface', instance)
    mesh.set_editor_property('materials', slots)
    if not EL.save_loaded_asset(mesh, False):
        raise RuntimeError(f'Mesh material save failed: {hero_id}')
    u.log(f'REBIRTH_HERO_MATERIALS id={hero_id} textures={len(unique)} slots={len(slots)}')

u.log('REBIRTH: HERO_MATERIALS_COMPLETE count=3')
