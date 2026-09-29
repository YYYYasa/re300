"""Create the refined map without touching assets held open in the first editor."""
import unreal as u
import json
from pathlib import Path
root=Path('G:/Code/UE/EternalRebirth')
exec(Path('G:/Code/UE/Tools/finalize_materials.py').read_text())
mesh_path='/Game/Art/Meshes_Showcase'
if '-SkipImport' not in u.SystemLibrary.get_command_line():
    exec(Path('G:/Code/UE/Tools/reimport_meshes.py').read_text())
else:
    el=u.EditorAssetLibrary
    exec(Path('G:/Code/UE/Tools/optimize_meshes.py').read_text())
es=u.get_editor_subsystem(u.EditorActorSubsystem)
ls=u.get_editor_subsystem(u.LevelEditorSubsystem)
map_path='/Game/Maps/EternalShowcase'
if el.does_asset_exist(map_path):
    if not ls.load_level(map_path):raise RuntimeError('Cannot load showcase map')
    for a in es.get_all_level_actors():
        if a.get_class().get_name() not in ('WorldSettings','DefaultPhysicsVolume','Brush'):es.destroy_actor(a)
else:
    if not ls.new_level(map_path):raise RuntimeError('Cannot create showcase map')
def actor(cls,name,pos=(0,0,0),rot=(0,0,0)):
    a=es.spawn_actor_from_class(cls,u.Vector(*pos),u.Rotator(*rot));a.set_actor_label(name);return a
for path in el.list_assets(mesh_path,True,False):
    mesh=u.load_asset(path)
    if not isinstance(mesh,u.StaticMesh):continue
    a=actor(u.StaticMeshActor,mesh.get_name());a.static_mesh_component.set_static_mesh(mesh)
    a.set_folder_path('01 / Reconstructed Arena')
    a.static_mesh_component.set_editor_property('cast_shadow',not mesh.get_name().startswith('SM_Water'))
actor(u.SkyAtmosphere,'Atmosphere')
sun=actor(u.DirectionalLight,'Sun | soft daylight',rot=(-49,-32,0));lc=sun.get_component_by_class(u.DirectionalLightComponent)
lc.set_mobility(u.ComponentMobility.MOVABLE);lc.set_intensity(4.7);lc.set_light_color(u.LinearColor(1,.92,.80))
lc.set_editor_property('atmosphere_sun_light',True);lc.set_editor_property('light_source_angle',8.);lc.set_editor_property('shadow_amount',.58)
sky=actor(u.SkyLight,'Sky | soft fill');sc=sky.get_component_by_class(u.SkyLightComponent)
sc.set_mobility(u.ComponentMobility.MOVABLE);sc.set_editor_property('real_time_capture',True);sc.set_intensity(2.0)
fog=actor(u.ExponentialHeightFog,'Valley haze',(0,0,-350));fc=fog.get_component_by_class(u.ExponentialHeightFogComponent)
fc.set_fog_density(.006);fc.set_fog_height_falloff(.18);fc.set_volumetric_fog(True);fc.set_volumetric_fog_distance(22000)
fc.set_fog_inscattering_color(u.LinearColor(.45,.54,.60))
pp=actor(u.PostProcessVolume,'Look development');pp.set_editor_property('unbound',True);s=pp.get_editor_property('settings')
for name,value in [('bloom_intensity',.4),('vignette_intensity',.21),('auto_exposure_bias',.3),('auto_exposure_min_brightness',1.),('auto_exposure_max_brightness',1.),('motion_blur_amount',0.),('ambient_occlusion_intensity',.65)]:
    s.set_editor_property('override_'+name,True);s.set_editor_property(name,value)
pp.set_editor_property('settings',s)
views=[((-11600,12800,11500),(0,0,200)),((3900,-3800,1100),(6300,-6900,600)),((-2600,2900,1500),(2200,-1500,150)),((-3800,4500,1100),(-6200,6500,650)),((1800,4200,1400),(500,1400,180))]
for i,(pos,target) in enumerate(views):
    a=actor(u.TargetPoint,'Vista %d'%(i+1),pos);a.tags=['View%d'%(i+1)];a.set_folder_path('05 / Viewpoints')
    a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*pos),u.Vector(*target)),False)
start=actor(u.PlayerStart,'Entry',views[0][0]);start.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*views[0][0]),u.Vector(*views[0][1])),False)
u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(*views[0][0]),start.get_actor_rotation())
if not ls.save_current_level():raise RuntimeError('Showcase map save failed')
r=json.loads((root/'SourceArt/conversion_report.json').read_text())
(root/'Saved/build-report.json').write_text(json.dumps(dict(map=map_path,instances=len(r['converted']),excluded_helpers=len(r['excluded_helpers']),textures=len(r['textures']),triangles=r['triangles'],missing=r['missing']),indent=2))
u.log('REBIRTH: SHOWCASE_COMPLETE')
