"""Build reflective river water and restrained wind for the imported vegetation."""
import unreal as u

assets = u.EditorAssetLibrary
editing = u.MaterialEditingLibrary
tools = u.AssetToolsHelpers.get_asset_tools()
folder = '/Game/Art/Materials'


def expression(material, cls, **properties):
    result = editing.create_material_expression(material, cls, 0, 0)
    for name, value in properties.items():
        result.set_editor_property(name, value)
    return result


def custom(material, code, inputs, output=u.CustomMaterialOutputType.CMOT_FLOAT3):
    pins = []
    for name in inputs:
        pin = u.CustomInput()
        pin.set_editor_property('input_name', name)
        pins.append(pin)
    result = expression(material, u.MaterialExpressionCustom,
                        code=code, output_type=output, inputs=pins)
    for name, source in inputs.items():
        editing.connect_material_expressions(source, '', result, name)
    return result


def connect(source, material, prop):
    editing.connect_material_property(source, '', prop)


def save(material):
    editing.layout_material_expressions(material)
    editing.recompile_material(material)
    if not assets.save_loaded_asset(material, False):
        raise RuntimeError('Could not save ' + material.get_path_name())


# Single Layer Water keeps the surface in the opaque pipeline while using the
# rendered scene beneath it for transmission and Lumen / screen-space reflection.
water = u.load_asset(folder + '/M_ClearRiver') or tools.create_asset(
    'M_ClearRiver', folder, u.Material, u.MaterialFactoryNew())
# UE 5.8's delete_all_material_expressions mutates its array while iterating;
# deleting a snapshot also removes CustomOutput nodes on repeated rebuilds.
for old in list(editing.get_material_expressions(water)):
    editing.delete_material_expression(water, old)
water.set_editor_property('blend_mode', u.BlendMode.BLEND_OPAQUE)
water.set_editor_property('shading_model', u.MaterialShadingModel.MSM_SINGLE_LAYER_WATER)
water.set_editor_property('two_sided', True)
position = expression(water, u.MaterialExpressionWorldPosition)
time = expression(water, u.MaterialExpressionTime)
connect(expression(water, u.MaterialExpressionConstant3Vector,
                   constant=u.LinearColor(.012, .045, .058)),
        water, u.MaterialProperty.MP_BASE_COLOR)

# Broad water displacement is deliberately much smaller than the banks. Finer
# ripples belong in the normal, where they move the reflected image without
# pulling the shoreline mesh apart.
wave = custom(water, '''
float2 xy = P.xy;
float a = dot(xy,float2(.0041,.0038)) + Time*.55;
float b = dot(xy,float2(-.0062,.0029)) - Time*.73;
float height = 2.5*sin(a) + 1.2*sin(b);
return float3(0,0,height);
''', {'P': position, 'Time': time})
connect(wave, water, u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
ripples = custom(water, '''
float2 xy=P.xy;
float a=dot(xy,float2(.0068,.0051))+Time*.48;
float b=dot(xy,float2(-.011,.0072))-Time*.69;
float c=dot(xy,float2(.022,-.017))+Time*1.04;
float d=dot(xy,float2(.041,.026))-Time*1.39;
float e=dot(xy,float2(-.073,.052))+Time*1.95;
float2 slope =
    .75*cos(a)*float2(.0068,.0051)*18.0 +
    .65*cos(b)*float2(-.011,.0072)*8.0 +
    .55*cos(c)*float2(.022,-.017)*3.0 +
    .35*cos(d)*float2(.041,.026)*1.3 +
    .20*cos(e)*float2(-.073,.052)*.5;
return normalize(float3(-slope.x,-slope.y,1));
''', {'P': position, 'Time': time})
connect(ripples, water, u.MaterialProperty.MP_NORMAL)
for prop, value in [(u.MaterialProperty.MP_ROUGHNESS, .07),
                    (u.MaterialProperty.MP_METALLIC, 0),
                    (u.MaterialProperty.MP_SPECULAR, .55),
                    (u.MaterialProperty.MP_OPACITY, .68)]:
    connect(expression(water, u.MaterialExpressionConstant, r=value), water, prop)
volume = expression(water, u.MaterialExpressionSingleLayerWaterMaterialOutput)
scattering = expression(water, u.MaterialExpressionConstant3Vector,
                        constant=u.LinearColor(.0014, .0045, .0055))
absorption = expression(water, u.MaterialExpressionConstant3Vector,
                        constant=u.LinearColor(.0040, .0014, .0009))
phase = expression(water, u.MaterialExpressionConstant, r=.2)
behind = expression(water, u.MaterialExpressionConstant, r=1)
for source, pin in [(scattering, 'ScatteringCoefficients'),
                    (absorption, 'AbsorptionCoefficients'),
                    (phase, 'PhaseG'), (behind, 'ColorScaleBehindWater')]:
    if not editing.connect_material_expressions(source, '', volume, pin):
        raise RuntimeError('Water volume pin unavailable: ' + pin)
save(water)

water_meshes = 0
for path in assets.list_assets('/Game/Art/Meshes_Showcase', True, False):
    mesh = u.load_asset(path)
    if not isinstance(mesh, u.StaticMesh) or not mesh.get_name().startswith('SM_Water'):
        continue
    slots = mesh.get_editor_property('static_materials')
    for index, slot in enumerate(slots):
        slot.set_editor_property('material_interface', water)
        slots[index] = slot
    mesh.set_editor_property('static_materials', slots)
    if not assets.save_loaded_asset(mesh, False):
        raise RuntimeError('Could not save water mesh ' + path)
    water_meshes += 1
if not water_meshes:
    raise RuntimeError('No showcase water meshes found')

# The imported grass is in several masked texture atlases. Move their vertices
# only a few centimetres, with two asynchronous gusts so the vegetation does
# not sway as a single rigid block. This also gives leaves a subtle flutter.
foliage = u.load_asset(folder + '/M_WindFoliage') or tools.create_asset(
    'M_WindFoliage', folder, u.Material, u.MaterialFactoryNew())
for old in list(editing.get_material_expressions(foliage)):
    editing.delete_material_expression(foliage, old)
foliage.set_editor_property('blend_mode', u.BlendMode.BLEND_MASKED)
foliage.set_editor_property('two_sided', True)
editing.set_material_usage(foliage, u.MaterialUsage.MATUSAGE_NANITE)
texture = expression(foliage, u.MaterialExpressionTextureSampleParameter2D,
                     parameter_name='Albedo')
texture.set_editor_property('texture', u.load_asset('/Engine/EngineResources/DefaultTexture'))
collection = u.load_asset(folder + '/MPC_Style')
style = expression(foliage, u.MaterialExpressionCollectionParameter,
                   collection=collection, parameter_name='AnimeMix')
color = custom(foliage, 'return C.rgb*lerp(1.02,.55,Style);',
               {'C': texture, 'Style': style})
connect(color, foliage, u.MaterialProperty.MP_BASE_COLOR)
editing.connect_material_property(texture, 'A', u.MaterialProperty.MP_OPACITY_MASK)
connect(custom(foliage, 'return C.rgb*Style*.16;', {'C': texture, 'Style': style}),
        foliage, u.MaterialProperty.MP_EMISSIVE_COLOR)
connect(expression(foliage, u.MaterialExpressionConstant, r=.82),
        foliage, u.MaterialProperty.MP_ROUGHNESS)
connect(expression(foliage, u.MaterialExpressionConstant, r=.14),
        foliage, u.MaterialProperty.MP_SPECULAR)
wind_position = expression(foliage, u.MaterialExpressionWorldPosition)
wind_time = expression(foliage, u.MaterialExpressionTime)
wind = custom(foliage, '''
float phase = P.x*.0057 + P.y*.0083;
float slow = sin(Time*.95 + phase);
float gust = sin(Time*.31 + P.x*.0012 - P.y*.0008);
float flutter = sin(Time*2.1 + phase*2.3);
float strength = 1.8 + 1.1*gust;
return float3((slow*.7+flutter*.3)*strength,
              (sin(Time*.78-phase*.73)*.65+flutter*.18)*strength,0);
''', {'P': wind_position, 'Time': wind_time})
connect(wind, foliage, u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
save(foliage)

vegetation = ('M_stex_cl_15_b', 'M_stex_clb_08',
              'M_stex_cl_jnglingcao', 'M_stex_cl_cao')
for name in vegetation:
    instance = u.load_asset(folder + '/' + name)
    if not isinstance(instance, u.MaterialInstanceConstant):
        raise RuntimeError('Vegetation material missing: ' + name)
    editing.set_material_instance_parent(instance, foliage)
    editing.set_material_usage_override(instance, u.MaterialUsage.MATUSAGE_NANITE,
                                         True, True)
    editing.update_material_instance(instance)
    if not assets.save_loaded_asset(instance, False):
        raise RuntimeError('Could not save vegetation material ' + name)

u.log('REBIRTH: ANIMATED_ENVIRONMENT_COMPLETE water_meshes=%d vegetation=%d' %
      (water_meshes, len(vegetation)))
