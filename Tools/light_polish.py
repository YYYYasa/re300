"""Small local light accents for the two bases and central river."""
import unreal as u
es=u.get_editor_subsystem(u.EditorActorSubsystem)
ls=u.get_editor_subsystem(u.LevelEditorSubsystem)
if not ls.load_level('/Game/Maps/EternalShowcase'):raise RuntimeError('Showcase level missing')
for old in es.get_all_level_actors():
    if old.actor_has_tag('RebirthFill'):es.destroy_actor(old)
lights=[
    ('River | reflected sky',(-1200,1500,900),(.22,.64,1.),3200,2600),
    ('Crimson | warm bounce',(-4400,4900,1050),(1.,.58,.32),4200,2600),
    ('Sapphire | forest bounce',(4200,-3500,1050),(.48,.79,1.),3600,2600),
]
for name,pos,color,power,radius in lights:
    a=es.spawn_actor_from_class(u.PointLight,u.Vector(*pos));a.set_actor_label(name)
    a.set_folder_path('03 / Atmosphere');a.tags=['RebirthFill']
    c=a.get_component_by_class(u.PointLightComponent)
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_intensity(power);c.set_light_color(u.LinearColor(*color))
    c.set_attenuation_radius(radius)
    c.set_editor_property('cast_shadows',False)
    c.set_editor_property('source_radius',120.)
    c.set_editor_property('volumetric_scattering_intensity',1.35)
if not ls.save_current_level():raise RuntimeError('Failed to save local lights')
u.log('REBIRTH: LIGHT_POLISH_COMPLETE')
