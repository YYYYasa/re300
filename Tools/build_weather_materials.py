"""Author gradual rain puddles and snow accumulation on terrain and hard surfaces."""
import unreal as u

assets=u.EditorAssetLibrary
editing=u.MaterialEditingLibrary
tools=u.AssetToolsHelpers.get_asset_tools()
folder='/Game/Art/Materials'

collection=u.load_asset(folder+'/MPC_Weather') or tools.create_asset(
    'MPC_Weather',folder,u.MaterialParameterCollection,u.MaterialParameterCollectionFactoryNew())
parameters=list(collection.get_editor_property('scalar_parameters'))
existing={parameter.get_editor_property('parameter_name') for parameter in parameters}
missing=False
for name in ('Wetness','SnowCover','RainAmount','SnowAmount'):
    if name not in existing:
        parameter=u.CollectionScalarParameter()
        parameter.set_editor_property('parameter_name',name)
        parameter.set_editor_property('default_value',0.0)
        parameters.append(parameter)
        missing=True
if missing:
    collection.set_editor_property('scalar_parameters',parameters)
    if not assets.save_loaded_asset(collection,False):
        raise RuntimeError('Failed to save weather parameter collection')
style_collection=u.load_asset(folder+'/MPC_Style')


def node(material,cls,**properties):
    result=editing.create_material_expression(material,cls,0,0)
    for key,value in properties.items():result.set_editor_property(key,value)
    return result


def custom(material,code,inputs,output=u.CustomMaterialOutputType.CMOT_FLOAT3):
    pins=[]
    for key in inputs:
        pin=u.CustomInput()
        pin.set_editor_property('input_name',key)
        pins.append(pin)
    result=node(material,u.MaterialExpressionCustom,code=code,output_type=output,inputs=pins)
    for key,source in inputs.items():editing.connect_material_expressions(source,'',result,key)
    return result


def connect(source,material,prop,output=''):
    editing.connect_material_property(source,output,prop)


def parameter(material,collection,name):
    return node(material,u.MaterialExpressionCollectionParameter,
                collection=collection,parameter_name=name)


def finish(material):
    editing.layout_material_expressions(material)
    editing.recompile_material(material)
    if not assets.save_loaded_asset(material,False):
        raise RuntimeError('Material save failed: '+material.get_path_name())


pool_code='''
float2 g=P.xy/430.0;
float2 cell=floor(g);
float2 local=frac(g)-.5;
float h=frac(sin(dot(cell,float2(127.1,311.7)))*43758.5453);
float2 shift=float2(frac(h*17.31),frac(h*31.17))*.30-.15;
float radius=length((local-shift)*float2(1,1.32));
radius+=.065*sin(P.x*.032+sin(P.y*.022))+.055*cos(P.y*.039-P.x*.014);
float shape=1-smoothstep(.16,.36,radius);
return shape*smoothstep(.58,.78,h)*smoothstep(.14,.85,Wet);
'''
snow_code='''
float total=0;
for(int octave=0;octave<2;octave++) {
    float scale=octave==0?275.0:85.0;
    float2 g=P.xy/scale;
    float2 cell=floor(g);
    float2 f=frac(g);
    f=f*f*(3-2*f);
    float h00=frac(sin(dot(cell,float2(127.1,311.7)))*43758.5453);
    float h10=frac(sin(dot(cell+float2(1,0),float2(127.1,311.7)))*43758.5453);
    float h01=frac(sin(dot(cell+float2(0,1),float2(127.1,311.7)))*43758.5453);
    float h11=frac(sin(dot(cell+float2(1,1),float2(127.1,311.7)))*43758.5453);
    float n=lerp(lerp(h00,h10,f.x),lerp(h01,h11,f.x),f.y);
    total+=n*(octave==0?.76:.24);
}
float threshold=lerp(.95,.31,Snow);
float mask=Snow*smoothstep(threshold-.14,threshold+.14,total);
return mask;
'''

terrain=u.load_asset(folder+'/M_Terrain')
for old in list(editing.get_material_expressions(terrain)):
    editing.delete_material_expression(terrain,old)
terrain.set_editor_property('two_sided',True)
editing.set_material_usage(terrain,u.MaterialUsage.MATUSAGE_NANITE)
texture=node(terrain,u.MaterialExpressionTextureSampleParameter2D,parameter_name='Albedo')
texture.set_editor_property('texture',u.load_asset('/Engine/EngineResources/DefaultTexture'))
position=node(terrain,u.MaterialExpressionWorldPosition)
style=parameter(terrain,style_collection,'AnimeMix')
wet=parameter(terrain,collection,'Wetness')
snow=parameter(terrain,collection,'SnowCover')
pool=custom(terrain,pool_code,{'P':position,'Wet':wet},u.CustomMaterialOutputType.CMOT_FLOAT1)
snow_mask=custom(terrain,snow_code,{'P':position,'Snow':snow},u.CustomMaterialOutputType.CMOT_FLOAT1)
color=custom(terrain,'''
float3 c=C.rgb*lerp(1.04,.60,Style)*(1-.34*Wet);
c=lerp(c,float3(.030,.061,.076),Pool*.67);
c=lerp(c,float3(.62,.69,.75),SnowMask*.84);
return c;
''',{'C':texture,'Style':style,'Wet':wet,'Pool':pool,'SnowMask':snow_mask})
connect(color,terrain,u.MaterialProperty.MP_BASE_COLOR)
connect(custom(terrain,'return C.rgb*lerp(.18,.30,Style)*(1-.85*Wet)*(1-.65*SnowMask);',
               {'C':texture,'Style':style,'Wet':wet,'SnowMask':snow_mask}),
        terrain,u.MaterialProperty.MP_EMISSIVE_COLOR)
connect(custom(terrain,'float r=lerp(.92,.48,Wet);r=lerp(r,.19,Pool);return lerp(r,.96,SnowMask);',
               {'Wet':wet,'Pool':pool,'SnowMask':snow_mask},u.CustomMaterialOutputType.CMOT_FLOAT1),
        terrain,u.MaterialProperty.MP_ROUGHNESS)
connect(custom(terrain,'return lerp(lerp(.10,.35,Wet),.20,SnowMask);',
               {'Wet':wet,'SnowMask':snow_mask},u.CustomMaterialOutputType.CMOT_FLOAT1),
        terrain,u.MaterialProperty.MP_SPECULAR)
finish(terrain)

surface=u.load_asset(folder+'/M_Surface')
for old in list(editing.get_material_expressions(surface)):
    editing.delete_material_expression(surface,old)
surface.set_editor_property('two_sided',True)
editing.set_material_usage(surface,u.MaterialUsage.MATUSAGE_NANITE)
texture=node(surface,u.MaterialExpressionTextureSampleParameter2D,parameter_name='Albedo')
texture.set_editor_property('texture',u.load_asset('/Engine/EngineResources/DefaultTexture'))
position=node(surface,u.MaterialExpressionWorldPosition)
normal=node(surface,u.MaterialExpressionVertexNormalWS)
style=parameter(surface,style_collection,'AnimeMix')
wet=parameter(surface,collection,'Wetness')
snow=parameter(surface,collection,'SnowCover')
surface_snow_code=snow_code.replace('return mask;','return mask*smoothstep(.30,.78,normalize(N).z);')
snow_mask=custom(surface,surface_snow_code,
                 {'P':position,'N':normal,'Snow':snow},u.CustomMaterialOutputType.CMOT_FLOAT1)
connect(custom(surface,'''
float3 c=C.rgb;
float l=dot(c,float3(.2126,.7152,.0722));
c=lerp(l.xxx,c,1.06)*lerp(1.0,.32,Style)*(1-.29*Wet);
return lerp(c,float3(.58,.65,.71),SnowMask*.72);
''',{'C':texture,'Style':style,'Wet':wet,'SnowMask':snow_mask}),
        surface,u.MaterialProperty.MP_BASE_COLOR)
connect(custom(surface,'''
float d=dot(normalize(N),normalize(float3(.48,-.55,.68)));
float band=d>.55?1.0:(d>.05?.77:.52);
float3 tint=d>.05?float3(1.04,1.03,1):float3(.65,.78,1);
return C.rgb*band*tint*Style*.75*(1-.75*Wet)*(1-SnowMask);
''',{'C':texture,'N':normal,'Style':style,'Wet':wet,'SnowMask':snow_mask}),
        surface,u.MaterialProperty.MP_EMISSIVE_COLOR)
connect(custom(surface,'''
float a=(1-Style)*.085;
float x=sin(P.x*.065+sin(P.y*.023))*cos(P.y*.17);
float y=cos(P.y*.071+sin(P.x*.031))*sin(P.x*.19);
return normalize(float3(x*a,y*a,1));
''',{'P':position,'Style':style}),surface,u.MaterialProperty.MP_NORMAL)
connect(custom(surface,'return lerp(lerp(.72,.96,Style),.41,Wet)*(1-SnowMask)+.95*SnowMask;',
               {'Style':style,'Wet':wet,'SnowMask':snow_mask},u.CustomMaterialOutputType.CMOT_FLOAT1),
        surface,u.MaterialProperty.MP_ROUGHNESS)
connect(node(surface,u.MaterialExpressionConstant,r=.24),surface,u.MaterialProperty.MP_SPECULAR)
finish(surface)

terrain_count=0
for path in assets.list_assets(folder,True,False):
    if '/M_stex_sterrain' not in path:continue
    instance=u.load_asset(path)
    if not isinstance(instance,u.MaterialInstanceConstant):continue
    editing.set_material_instance_parent(instance,terrain)
    editing.set_material_usage_override(instance,u.MaterialUsage.MATUSAGE_NANITE,True,True)
    editing.update_material_instance(instance)
    if not assets.save_loaded_asset(instance,False):
        raise RuntimeError('Terrain instance save failed: '+path)
    terrain_count+=1
if terrain_count!=64:
    raise RuntimeError('Expected 64 terrain instances; found %d' % terrain_count)
u.log('REBIRTH: WEATHER_MATERIALS_COMPLETE terrain_instances=%d' % terrain_count)
