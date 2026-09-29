"""Import original weather ambience and make billboard rain/snow materials."""
from pathlib import Path
import runpy
import unreal as u

assets=u.EditorAssetLibrary
editing=u.MaterialEditingLibrary
tools=u.AssetToolsHelpers.get_asset_tools()
material_folder='/Game/Art/Materials'
runpy.run_path(str(Path(__file__).with_name('build_weather_audio.py')))


def make_material(name,color,opacity_code,weather_parameter):
    material=u.load_asset(material_folder+'/'+name) or tools.create_asset(
        name,material_folder,u.Material,u.MaterialFactoryNew())
    for old in list(editing.get_material_expressions(material)):
        editing.delete_material_expression(material,old)
    material.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property('two_sided',True)
    usage=getattr(u.MaterialUsage,'MATUSAGE_INSTANCED_STATIC_MESHES',None)
    if usage is not None:editing.set_material_usage(material,usage)
    tint=editing.create_material_expression(material,u.MaterialExpressionConstant3Vector,0,0)
    tint.set_editor_property('constant',u.LinearColor(*color))
    editing.connect_material_property(tint,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    uv=editing.create_material_expression(material,u.MaterialExpressionTextureCoordinate,0,200)
    collection=u.load_asset(material_folder+'/MPC_Weather')
    amount=editing.create_material_expression(material,u.MaterialExpressionCollectionParameter,0,400)
    amount.set_editor_property('collection',collection)
    amount.set_editor_property('parameter_name',weather_parameter)
    pins=[]
    for pin_name in ('UV','Amount'):
        pin=u.CustomInput()
        pin.set_editor_property('input_name',pin_name)
        pins.append(pin)
    alpha=editing.create_material_expression(material,u.MaterialExpressionCustom,300,200)
    alpha.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT1)
    alpha.set_editor_property('inputs',pins)
    alpha.set_editor_property('code',opacity_code)
    editing.connect_material_expressions(uv,'',alpha,'UV')
    editing.connect_material_expressions(amount,'',alpha,'Amount')
    editing.connect_material_property(alpha,'',u.MaterialProperty.MP_OPACITY)
    editing.layout_material_expressions(material)
    editing.recompile_material(material)
    if not assets.save_loaded_asset(material,False):
        raise RuntimeError('Weather material save failed: '+name)


make_material('M_RainStreak',(.58,.72,.83),'''
float x=abs(UV.x-.5)*2;
float y=abs(UV.y-.5)*2;
return (1-smoothstep(.35,1,x))*(1-smoothstep(.65,1,y))*.72*Amount;
''','RainAmount')
make_material('M_SnowFlake',(.78,.86,.96),'''
float2 centered=(UV-.5)*2;
float radius=length(centered);
return (1-smoothstep(.25,.92,radius))*.88*Amount;
''','SnowAmount')
u.log('REBIRTH: WEATHER_EFFECTS_COMPLETE audio=3 particle_materials=2')
