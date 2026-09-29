"""Read-only inspection of the gallery's placed skeletal mesh actors."""
import unreal as u

ls = u.get_editor_subsystem(u.LevelEditorSubsystem)
es = u.get_editor_subsystem(u.EditorActorSubsystem)
if not ls.load_level('/Game/Maps/HeroShowcase'):
    raise RuntimeError('Could not load hero gallery')
for actor in es.get_all_level_actors():
    if not isinstance(actor, u.SkeletalMeshActor):
        continue
    component = actor.skeletal_mesh_component
    mesh = component.get_editor_property('skeletal_mesh_asset')
    origin, extent = actor.get_actor_bounds(False)
    u.log('HERO_GALLERY_PROBE label={} tags={} location={} rotation={} component_rotation={} scale={} bounds_origin={} bounds_extent={} mesh={} mode={} anim={}'.format(
        actor.get_actor_label(), list(actor.tags), actor.get_actor_location(),
        actor.get_actor_rotation(), component.get_editor_property('relative_rotation'),
        actor.get_actor_scale3d(), origin, extent,
        mesh.get_path_name() if mesh else None,
        component.get_editor_property('animation_mode'),
        component.get_editor_property('animation_data')))
