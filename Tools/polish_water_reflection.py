"""Place one high-quality planar capture over the central river corridor."""
import unreal as u

levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
if not levels.load_level('/Game/Maps/EternalShowcase'):
    raise RuntimeError('Showcase map missing')

for old in actors.get_all_level_actors():
    if old.get_actor_label() == 'River | planar reflection':
        actors.destroy_actor(old)

reflection = actors.spawn_actor_from_class(u.PlanarReflection,
                                           u.Vector(0, 0, 20), u.Rotator(0, 0, 0))
reflection.set_actor_label('River | planar reflection')
reflection.set_folder_path('02 / Atmosphere')
reflection.set_actor_scale3d(u.Vector(120, 120, 1))
component = reflection.get_component_by_class(u.PlanarReflectionComponent)
component.set_editor_property('screen_percentage', 100)
component.set_editor_property('normal_distortion_strength', 30.0)
component.set_editor_property('prefilter_roughness', .008)
component.set_editor_property('show_preview_plane', False)
hidden = 0
for actor in actors.get_all_level_actors():
    if actor.get_actor_label().startswith('SM_Water'):
        component.hide_actor_components(actor)
        hidden += 1
if hidden != 4:
    raise RuntimeError('Expected four water mesh actors; found ' + str(hidden))
if not levels.save_current_level():
    raise RuntimeError('Unable to save planar reflection level')
u.log('REBIRTH: WATER_REFLECTION_COMPLETE hidden_water=%d' % hidden)
