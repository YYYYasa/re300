"""UE 5.8 editor Python: build the actual reconstructed battlefield and paired looks."""
import unreal as u
import json,math,random,traceback
from pathlib import Path
ROOT=Path('G:/Code/UE/EternalRebirth')
ART=ROOT/'SourceArt'
AT=u.AssetToolsHelpers.get_asset_tools(); ML=u.MaterialEditingLibrary; EL=u.EditorAssetLibrary
ES=u.get_editor_subsystem(u.EditorActorSubsystem)
LS=u.get_editor_subsystem(u.LevelEditorSubsystem)
SM=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
MAT='/Game/Art/Materials'
report=json.loads((ART/'conversion_report.json').read_text())
def log(s):u.log('REBIRTH: '+str(s))
def save(a):EL.save_loaded_asset(a,False)
def asset(name,cls,factory,path=MAT):
    old=u.load_asset(path+'/'+name)
    return old or AT.create_asset(name,path,cls,factory)
def node(m,cls,**props):
    n=ML.create_material_expression(m,cls,-500,0)
    for k,v in props.items():n.set_editor_property(k,v)
    return n
def link(a,b,pin='',out=''):ML.connect_material_expressions(a,out,b,pin)
def prop(a,m,p,out=''):ML.connect_material_property(a,out,p)
def custom(m,code,inputs,kind=u.CustomMaterialOutputType.CMOT_FLOAT3):
    pins=[]
    for k in inputs:
        pin=u.CustomInput();pin.set_editor_property('input_name',k);pins.append(pin)
    n=node(m,u.MaterialExpressionCustom,code=code,output_type=kind,inputs=pins)
    for k,v in inputs.items():link(v,n,k)
    return n
def scalar(m,name,value):return node(m,u.MaterialExpressionScalarParameter,parameter_name=name,default_value=value)
def vec(m,name,value):return node(m,u.MaterialExpressionVectorParameter,parameter_name=name,default_value=u.LinearColor(*value))
def finish(m):ML.layout_material_expressions(m);ML.recompile_material(m);save(m);return m

for p in ['/Game/Maps',MAT,'/Game/Art/Textures','/Game/Art/Meshes']:EL.make_directory(p)
collection=asset('MPC_Style',u.MaterialParameterCollection,u.MaterialParameterCollectionFactoryNew())
parameter=u.CollectionScalarParameter();parameter.set_editor_property('parameter_name','AnimeMix');parameter.set_editor_property('default_value',0)
collection.set_editor_property('scalar_parameters',[parameter])
save(collection)
def style(m):return node(m,u.MaterialExpressionCollectionParameter,collection=collection,parameter_name='AnimeMix')

def master(name,masked=False):
    m=asset(name,u.Material,u.MaterialFactoryNew());ML.delete_all_material_expressions(m)
    m.set_editor_property('two_sided',True)
    ML.set_material_usage(m,u.MaterialUsage.MATUSAGE_NANITE)
    if masked:m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED)
    tex=node(m,u.MaterialExpressionTextureSampleParameter2D,parameter_name='Albedo')
    tex.set_editor_property('texture',u.load_asset('/Engine/EngineResources/DefaultTexture'))
    s=style(m);p=node(m,u.MaterialExpressionWorldPosition);n=node(m,u.MaterialExpressionVertexNormalWS)
    base=custom(m,'float3 c=C.rgb; float l=dot(c,float3(.2126,.7152,.0722)); c=lerp(l.xxx,c,1.06); return c*lerp(1.0,.32,Style);',{'C':tex,'Style':s})
    prop(base,m,u.MaterialProperty.MP_BASE_COLOR)
    emi=custom(m,'float d=dot(normalize(N),normalize(float3(.48,-.55,.68))); float band=d>.55?1.0:(d>.05?.77:.52); float3 tint=d>.05?float3(1.04,1.03,1):float3(.65,.78,1); return C.rgb*band*tint*Style*.75;',{'C':tex,'N':n,'Style':s})
    prop(emi,m,u.MaterialProperty.MP_EMISSIVE_COLOR)
    detail=custom(m,'float a=(1-Style)*.085; float x=sin(P.x*.065+sin(P.y*.023))*cos(P.y*.17);float y=cos(P.y*.071+sin(P.x*.031))*sin(P.x*.19);return normalize(float3(x*a,y*a,1));',{'P':p,'Style':s})
    prop(detail,m,u.MaterialProperty.MP_NORMAL)
    rough=custom(m,'return lerp(.72,.96,Style);',{'Style':s},u.CustomMaterialOutputType.CMOT_FLOAT1)
    prop(rough,m,u.MaterialProperty.MP_ROUGHNESS)
    spec=scalar(m,'Specular',.24);prop(spec,m,u.MaterialProperty.MP_SPECULAR)
    if masked:prop(tex,m,u.MaterialProperty.MP_OPACITY_MASK,'A')
    return finish(m)
opaque=master('M_Surface');masked=master('M_Foliage',True)
neutral=asset('M_neutral',u.Material,u.MaterialFactoryNew());ML.delete_all_material_expressions(neutral)
prop(vec(neutral,'Stone',(.16,.21,.23,1)),neutral,u.MaterialProperty.MP_BASE_COLOR)
prop(scalar(neutral,'Roughness',.8),neutral,u.MaterialProperty.MP_ROUGHNESS);finish(neutral)

m=asset('M_AnimePost',u.Material,u.MaterialFactoryNew());ML.delete_all_material_expressions(m)
m.set_editor_property('material_domain',u.MaterialDomain.MD_POST_PROCESS)
m.set_editor_property('blendable_location',u.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)
scene=node(m,u.MaterialExpressionSceneTexture,scene_texture_id=u.SceneTextureId.PPI_POST_PROCESS_INPUT0)
normal=node(m,u.MaterialExpressionSceneTexture,scene_texture_id=u.SceneTextureId.PPI_WORLD_NORMAL)
depth=node(m,u.MaterialExpressionSceneTexture,scene_texture_id=u.SceneTextureId.PPI_SCENE_DEPTH)
s=scalar(m,'AnimeMix',0)
code='''
float2 uv=GetDefaultSceneTextureUV(Parameters,14);
float2 stepUV=View.BufferSizeAndInvSize.zw*1.2;
float z=SceneTextureLookup(uv,1,false).r;
float3 n=SceneTextureLookup(uv,8,false).rgb;
float edge=0;
for(int i=0;i<4;i++){
 float2 off=(i==0?float2(1,0):i==1?float2(-1,0):i==2?float2(0,1):float2(0,-1))*stepUV;
 float dz=abs(SceneTextureLookup(uv+off,1,false).r-z)/max(z,1);
 float dn=length(SceneTextureLookup(uv+off,8,false).rgb-n);
 edge=max(edge,max(smoothstep(.006,.02,dz),smoothstep(.35,.7,dn)*.45));
}
float3 c=Color.rgb;
float l=max(dot(c,float3(.2126,.7152,.0722)),.001);
float q=floor(l*10+.5)/10;
float3 toon=c*lerp(1,q/l,.20);
toon=lerp(toon,float3(.045,.065,.10),edge*.66);
return lerp(c,toon,AnimeMix)+Normal.rgb*0+Depth.rgb*0;
'''
out=custom(m,code,{'Color':scene,'Normal':normal,'Depth':depth,'AnimeMix':s})
prop(out,m,u.MaterialProperty.MP_EMISSIVE_COLOR);finish(m)

water=asset('M_LivingWater',u.Material,u.MaterialFactoryNew());ML.delete_all_material_expressions(water)
p=node(water,u.MaterialExpressionWorldPosition);t=node(water,u.MaterialExpressionTime);s=style(water)
c=custom(water,'float a=sin(P.x*.004+P.y*.005+Time*.7)*sin(P.y*.011-P.x*.003-Time*.42);return lerp(float3(.008,.075,.09),float3(.025,.24,.25),a*.5+.5);',{'P':p,'Time':t})
prop(c,water,u.MaterialProperty.MP_BASE_COLOR)
norm=custom(water,'float x=sin(P.x*.008+P.y*.003+Time*.7)*.18+sin(P.y*.031-Time)*.055;float y=cos(P.y*.009-P.x*.004-Time*.5)*.18;return normalize(float3(x,y,1));',{'P':p,'Time':t})
prop(norm,water,u.MaterialProperty.MP_NORMAL)
prop(scalar(water,'Roughness',.15),water,u.MaterialProperty.MP_ROUGHNESS)
prop(scalar(water,'Metallic',.48),water,u.MaterialProperty.MP_METALLIC)
prop(scalar(water,'Specular',.65),water,u.MaterialProperty.MP_SPECULAR)
finish(water)

glow=asset('M_Aether',u.Material,u.MaterialFactoryNew());ML.delete_all_material_expressions(glow)
glow.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
c=vec(glow,'Color',(0.12,.80,1,1));power=scalar(glow,'Power',4)
o=node(glow,u.MaterialExpressionMultiply);link(c,o,'A');link(power,o,'B');prop(o,glow,u.MaterialProperty.MP_EMISSIVE_COLOR);finish(glow)

tasks=[]
for key,meta in report['textures'].items():
    if EL.does_asset_exist('/Game/Art/Textures/T_'+key):continue
    task=u.AssetImportTask();task.filename=str(ART/'Textures'/meta['file']);task.destination_path='/Game/Art/Textures';task.automated=True;task.save=True;task.replace_existing=True;tasks.append(task)
AT.import_asset_tasks(tasks);log('Imported textures '+str(len(tasks)))
mats={'M_neutral':neutral}
for key,meta in report['textures'].items():
    tex=u.load_asset('/Game/Art/Textures/T_'+key)
    mi=asset('M_'+key,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
    ML.set_material_instance_parent(mi,masked if meta['masked'] else opaque)
    ML.set_material_usage_override(mi,u.MaterialUsage.MATUSAGE_NANITE,True,True)
    ML.set_material_instance_texture_parameter_value(mi,'Albedo',tex);save(mi);mats['M_'+key]=mi

tasks=[]
for file in sorted((ART/'Meshes').glob('*.fbx')):
    # Minus signs in package names are normalized by the importer.
    name=file.stem.replace('-','n')
    if EL.does_asset_exist('/Game/Art/Meshes/'+name) and '-ReimportMeshes' not in u.SystemLibrary.get_command_line():continue
    task=u.AssetImportTask();task.filename=str(file);task.destination_path='/Game/Art/Meshes';task.destination_name=name;task.automated=True;task.replace_existing=True;task.save=True
    opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.import_animations=False
    opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False
    opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.generate_lightmap_u_vs=False
    opt.static_mesh_import_data.auto_generate_collision=False
    task.options=opt;task.factory=u.FbxFactory();tasks.append(task)
AT.import_asset_tasks(tasks);log('Imported meshes '+str(len(tasks)))

if EL.does_asset_exist('/Game/Maps/EternalGrounds'):
    if not LS.load_level('/Game/Maps/EternalGrounds'):raise RuntimeError('Cannot load generated map')
    for old_actor in ES.get_all_level_actors():
        if old_actor.get_class().get_name() not in ('WorldSettings','DefaultPhysicsVolume','Brush'):
            ES.destroy_actor(old_actor)
else:
    if not LS.new_level('/Game/Maps/EternalGrounds'):raise RuntimeError('Cannot create generated map')
def actor(cls,name,pos=(0,0,0),rot=(0,0,0)):
    a=ES.spawn_actor_from_class(cls,u.Vector(*pos),u.Rotator(*rot));a.set_actor_label(name);return a
def mesh_actor(mesh,name,pos=(0,0,0),scale=(1,1,1),material=None):
    a=actor(u.StaticMeshActor,name,pos);a.static_mesh_component.set_static_mesh(mesh);a.set_actor_scale3d(u.Vector(*scale))
    if material:a.static_mesh_component.set_material(0,material)
    return a

meshes=[]
for path in EL.list_assets('/Game/Art/Meshes',True,False):
    mesh=u.load_asset(path)
    if not isinstance(mesh,u.StaticMesh):continue
    slots=mesh.get_editor_property('static_materials')
    changed=False
    for i,slot in enumerate(slots):
        slotname=str(slot.material_slot_name)
        mat=mats.get(slotname)
        if mesh.get_name().startswith('SM_Water'):mat=water
        if mat and slot.material_interface != mat:
            slot.set_editor_property('material_interface',mat);slots[i]=slot;changed=True
        elif mat:pass
        else:log('MISSING MATERIAL '+mesh.get_name()+' '+slotname)
    if changed:mesh.set_editor_property('static_materials',slots)
    save(mesh)
    a=mesh_actor(mesh,mesh.get_name());a.set_folder_path('01 / Reconstructed Arena')
    a.static_mesh_component.set_editor_property('cast_shadow',not mesh.get_name().startswith('SM_Water'))
    meshes.append(mesh.get_name())

sky=actor(u.SkyAtmosphere,'Atmosphere')
sun=actor(u.DirectionalLight,'Sun | soft daylight',rot=(-49,-32,0));lc=sun.get_component_by_class(u.DirectionalLightComponent);lc.set_mobility(u.ComponentMobility.MOVABLE)
lc.set_intensity(4.7);lc.set_light_color(u.LinearColor(1,.92,.80))
lc.set_editor_property('atmosphere_sun_light',True)
lc.set_editor_property('light_source_angle',8.0);lc.set_editor_property('shadow_amount',.58)
skyLight=actor(u.SkyLight,'Sky | cool fill');sc=skyLight.get_component_by_class(u.SkyLightComponent);sc.set_mobility(u.ComponentMobility.MOVABLE)
sc.set_editor_property('real_time_capture',True);sc.set_intensity(2.0)
fog=actor(u.ExponentialHeightFog,'River haze',(0,0,-350));fc=fog.get_component_by_class(u.ExponentialHeightFogComponent)
fc.set_fog_density(.006);fc.set_fog_height_falloff(.18);fc.set_volumetric_fog(True);fc.set_volumetric_fog_distance(22000)
fc.set_fog_inscattering_color(u.LinearColor(.45,.54,.60))
pp=actor(u.PostProcessVolume,'Look development');pp.set_editor_property('unbound',True)
settings=pp.get_editor_property('settings')
for name,value in [('bloom_intensity',.40),('vignette_intensity',.21),('auto_exposure_bias',.3),('auto_exposure_min_brightness',1.),('auto_exposure_max_brightness',1.),('motion_blur_amount',0.),('ambient_occlusion_intensity',.65)]:
    settings.set_editor_property('override_'+name,True);settings.set_editor_property(name,value)
pp.set_editor_property('settings',settings)

# Viewpoints use the original map's centered coordinates. FBX Y is mirrored in UE.
views=[((-9400,10700,9000),(0,0,100)),((-6500,5100,1700),(-4300,4300,250)),((-2600,2900,1600),(2200,-1500,150)),((5600,-2900,1700),(5000,-5200,300)),((1800,4200,1400),(500,1400,180))]
for i,(pos,target) in enumerate(views):
    v=actor(u.TargetPoint,'Vista %d'%(i+1),pos)
    v.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*pos),u.Vector(*target)),False)
    v.tags=['View%d'%(i+1)];v.set_folder_path('05 / Viewpoints')
start=actor(u.PlayerStart,'Entry',views[0][0]);start.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*views[0][0]),u.Vector(0,0,0)),False)
u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(*views[0][0]),u.MathLibrary.find_look_at_rotation(u.Vector(*views[0][0]),u.Vector(0,0,0)))
LS.save_current_level();EL.save_directory('/Game',False,True)
(ROOT/'Saved/build-report.json').write_text(json.dumps(dict(meshes=meshes,textures=len(mats),map='/Game/Maps/EternalGrounds',original_instances=len(report['converted']),triangles=report['triangles']),indent=2))
log('BUILD_COMPLETE')
