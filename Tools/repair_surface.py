"""Correct terrain shading, calm water reflections, and soften the saved look."""
import unreal as u
from pathlib import Path
el=u.EditorAssetLibrary;ml=u.MaterialEditingLibrary
tools=u.AssetToolsHelpers.get_asset_tools()
folder='/Game/Art/Materials'
terrain=u.load_asset(folder+'/M_Terrain') or tools.create_asset('M_Terrain',folder,u.Material,u.MaterialFactoryNew())
ml.delete_all_material_expressions(terrain)
terrain.set_editor_property('two_sided',True)
ml.set_material_usage(terrain,u.MaterialUsage.MATUSAGE_NANITE)
def node(m,cls,**properties):
    n=ml.create_material_expression(m,cls,0,0)
    for key,value in properties.items():n.set_editor_property(key,value)
    return n
def custom(m,code,inputs,kind=u.CustomMaterialOutputType.CMOT_FLOAT3):
    pins=[]
    for key in inputs:
        pin=u.CustomInput();pin.set_editor_property('input_name',key);pins.append(pin)
    n=node(m,u.MaterialExpressionCustom,code=code,output_type=kind,inputs=pins)
    for key,source in inputs.items():ml.connect_material_expressions(source,'',n,key)
    return n
def connect(n,m,property):ml.connect_material_property(n,'',property)
def finish(m):
    ml.layout_material_expressions(m);ml.recompile_material(m)
    if not el.save_loaded_asset(m,False):raise RuntimeError('Material save failed: '+m.get_name())
tex=node(terrain,u.MaterialExpressionTextureSampleParameter2D,parameter_name='Albedo')
tex.set_editor_property('texture',u.load_asset('/Engine/EngineResources/DefaultTexture'))
collection=u.load_asset(folder+'/MPC_Style')
style=node(terrain,u.MaterialExpressionCollectionParameter,collection=collection,parameter_name='AnimeMix')
connect(custom(terrain,'return C.rgb*lerp(1.04,.60,Style);',{'C':tex,'Style':style}),terrain,u.MaterialProperty.MP_BASE_COLOR)
connect(custom(terrain,'return C.rgb*lerp(.18,.30,Style);',{'C':tex,'Style':style}),terrain,u.MaterialProperty.MP_EMISSIVE_COLOR)
connect(node(terrain,u.MaterialExpressionConstant,r=.92),terrain,u.MaterialProperty.MP_ROUGHNESS)
connect(node(terrain,u.MaterialExpressionConstant,r=.10),terrain,u.MaterialProperty.MP_SPECULAR)
finish(terrain)
changed=0
for path in el.list_assets(folder,True,False):
    if '/M_stex_sterrain' not in path:continue
    mi=u.load_asset(path)
    if not isinstance(mi,u.MaterialInstanceConstant):continue
    ml.set_material_instance_parent(mi,terrain)
    ml.set_material_usage_override(mi,u.MaterialUsage.MATUSAGE_NANITE,True,True)
    ml.update_material_instance(mi)
    if not el.save_loaded_asset(mi,False):raise RuntimeError('Terrain instance save failed: '+path)
    changed+=1
if changed!=64:raise RuntimeError('Expected 64 terrain textures, got '+str(changed))
water=u.load_asset(folder+'/M_LivingWater');ml.delete_all_material_expressions(water)
p=node(water,u.MaterialExpressionWorldPosition);time=node(water,u.MaterialExpressionTime)
color=custom(water,'float w=sin(P.x*.003+P.y*.004+Time*.45)*sin(P.y*.008-P.x*.003-Time*.28);return lerp(float3(.013,.090,.11),float3(.035,.23,.26),w*.5+.5);',{'P':p,'Time':time})
connect(color,water,u.MaterialProperty.MP_BASE_COLOR)
normal=custom(water,'float x=sin(P.x*.007+P.y*.002+Time*.65)*.055;float y=cos(P.y*.008-P.x*.003-Time*.42)*.055;return normalize(float3(x,y,1));',{'P':p,'Time':time})
connect(normal,water,u.MaterialProperty.MP_NORMAL)
connect(node(water,u.MaterialExpressionConstant,r=.38),water,u.MaterialProperty.MP_ROUGHNESS)
connect(node(water,u.MaterialExpressionConstant,r=.02),water,u.MaterialProperty.MP_METALLIC)
connect(node(water,u.MaterialExpressionConstant,r=.50),water,u.MaterialProperty.MP_SPECULAR)
connect(custom(water,'return C*.13;',{'C':color}),water,u.MaterialProperty.MP_EMISSIVE_COLOR)
finish(water)
ls=u.get_editor_subsystem(u.LevelEditorSubsystem);es=u.get_editor_subsystem(u.EditorActorSubsystem)
if not ls.load_level('/Game/Maps/EternalShowcase'):raise RuntimeError('Showcase level missing')
for actor in es.get_all_level_actors():
    name=actor.get_class().get_name()
    if name=='DirectionalLight':
        component=actor.get_component_by_class(u.DirectionalLightComponent)
        component.set_intensity(4.7);component.set_light_color(u.LinearColor(1,.92,.80))
        component.set_editor_property('light_source_angle',8.)
        component.set_editor_property('shadow_amount',.58)
        actor.set_actor_rotation(u.Rotator(-49,-32,0),False)
    elif name=='SkyLight':
        component=actor.get_component_by_class(u.SkyLightComponent)
        component.set_intensity(2.0);component.set_light_color(u.LinearColor(.85,.91,1))
    elif name=='ExponentialHeightFog':
        component=actor.get_component_by_class(u.ExponentialHeightFogComponent)
        component.set_fog_density(.006);component.set_fog_inscattering_color(u.LinearColor(.45,.54,.60))
    elif name=='PostProcessVolume':
        settings=actor.get_editor_property('settings')
        for key,value in [('ambient_occlusion_intensity',.20),('bloom_intensity',.32),('vignette_intensity',.13)]:
            settings.set_editor_property('override_'+key,True);settings.set_editor_property(key,value)
        actor.set_editor_property('settings',settings)
if not ls.save_current_level():raise RuntimeError('Showcase level save failed')
u.log('REBIRTH: SURFACE_REPAIRED terrain_instances='+str(changed))
