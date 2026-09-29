"""Add distant scenery and an animated portal to the showcase map."""
import unreal as u
import random,math
from pathlib import Path
at=u.AssetToolsHelpers.get_asset_tools();el=u.EditorAssetLibrary;ml=u.MaterialEditingLibrary
es=u.get_editor_subsystem(u.EditorActorSubsystem);ls=u.get_editor_subsystem(u.LevelEditorSubsystem)
base='/Game/Art/Atmosphere'
def material(name,unlit=False,masked=False):
 m=u.load_asset(base+'/'+name) or at.create_asset(name,base,u.Material,u.MaterialFactoryNew())
 ml.delete_all_material_expressions(m)
 if unlit:m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
 if masked:m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED)
 m.set_editor_property('two_sided',True)
 return m
def node(m,cls,**props):
 n=ml.create_material_expression(m,cls,-200,0)
 for k,v in props.items():n.set_editor_property(k,v)
 return n
def custom(m,code,inputs,kind=u.CustomMaterialOutputType.CMOT_FLOAT3):
 pins=[]
 for key in inputs:
  p=u.CustomInput();p.set_editor_property('input_name',key);pins.append(p)
 n=node(m,u.MaterialExpressionCustom,code=code,output_type=kind,inputs=pins)
 for key,v in inputs.items():ml.connect_material_expressions(v,'',n,key)
 return n
def output(n,m,slot):ml.connect_material_property(n,'',slot)
def finish(m):ml.layout_material_expressions(m);ml.recompile_material(m);el.save_loaded_asset(m,False)
mountain=material('M_DistantHighlands')
p=node(mountain,u.MaterialExpressionWorldPosition);normal=node(mountain,u.MaterialExpressionVertexNormalWS)
c=custom(mountain,'float f=sin(P.x*.002)*sin(P.y*.0023)+sin(P.x*.008+P.y*.011)*.22;float rock=smoothstep(.92,.6,N.z);float3 grass=lerp(float3(.018,.040,.036),float3(.070,.105,.077),f*.25+.5);float3 stone=lerp(float3(.10,.125,.14),float3(.19,.23,.25),f*.25+.5);return lerp(grass,stone,rock);',{'P':p,'N':normal})
output(c,mountain,u.MaterialProperty.MP_BASE_COLOR)
rough=node(mountain,u.MaterialExpressionConstant,r=.92);output(rough,mountain,u.MaterialProperty.MP_ROUGHNESS)
ml.set_material_usage(mountain,u.MaterialUsage.MATUSAGE_NANITE);finish(mountain)
portal=material('M_AstralGate',True,True)
uv=node(portal,u.MaterialExpressionTextureCoordinate);time=node(portal,u.MaterialExpressionTime)
color=custom(portal,'float2 p=UV.xy-.5;float r=length(p);float a=atan2(p.y,p.x);float swirl=pow(saturate(sin(a*3-r*30+Time*.55)*.5+.5),7);float rim=exp(-pow((r-.43)*95,2));float inner=pow(saturate(1-r*2),3);float stars=pow(saturate(sin(p.x*157+sin(p.y*73))*sin(p.y*183+Time*.3)),24);return float3(.012,.027,.07)+float3(.07,.60,1.2)*(swirl*.7+rim*4+stars*5)+float3(.65,.3,1)*inner*.55;',{'UV':uv,'Time':time})
output(color,portal,u.MaterialProperty.MP_EMISSIVE_COLOR)
mask=custom(portal,'return length(UV.xy-.5)<.46?1:0;',{'UV':uv},u.CustomMaterialOutputType.CMOT_FLOAT1);output(mask,portal,u.MaterialProperty.MP_OPACITY_MASK);finish(portal)
task=u.AssetImportTask();task.filename='G:/Code/UE/EternalRebirth/SourceArt/Environment/SM_DistantHighlands.fbx';task.destination_path=base;task.automated=True;task.replace_existing=True;task.save=True
opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_animations=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False;opt.static_mesh_import_data.auto_generate_collision=False
task.options=opt;at.import_asset_tasks([task]);mesh=u.load_asset(base+'/SM_DistantHighlands');mesh.set_material(0,mountain)
cfg=mesh.get_editor_property('nanite_settings');cfg.set_editor_property('enabled',True);mesh.set_editor_property('nanite_settings',cfg);el.save_loaded_asset(mesh,False)
if not ls.load_level('/Game/Maps/EternalShowcase'):raise RuntimeError('Cannot load showcase')
for a in es.get_all_level_actors():
 if a.actor_has_tag('ShowcasePolish'):es.destroy_actor(a)
def actor(cls,name,pos,rot=(0,0,0)):
 a=es.spawn_actor_from_class(cls,u.Vector(*pos),u.Rotator(*rot));a.set_actor_label(name);a.tags=['ShowcasePolish'];a.set_folder_path('03 / Atmosphere');return a
a=actor(u.StaticMeshActor,'Distant highlands',(0,0,0));a.static_mesh_component.set_static_mesh(mesh)
a=actor(u.StaticMeshActor,'Astral gate',(6960,-7080,845),(90,135,0));a.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Plane'));a.static_mesh_component.set_material(0,portal);a.set_actor_scale3d(u.Vector(13,18,1));a.static_mesh_component.set_editor_property('cast_shadow',False)
light=actor(u.PointLight,'Gate radiance',(6450,-6610,850));lc=light.get_component_by_class(u.PointLightComponent);lc.set_mobility(u.ComponentMobility.MOVABLE);lc.set_intensity(18000);lc.set_light_color(u.LinearColor(.04,.58,1));lc.set_attenuation_radius(2200)
if not ls.save_current_level():raise RuntimeError('Showcase map save failed')
u.log('REBIRTH: POLISH_COMPLETE')
