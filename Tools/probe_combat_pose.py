"""Read-only world-space bounds for the current combat pawn and dummy."""
import unreal as u

ls = u.get_editor_subsystem(u.LevelEditorSubsystem)
es = u.get_editor_subsystem(u.EditorActorSubsystem)
if not ls.load_level('/Game/Maps/HeroCombatPrototype'):
    raise RuntimeError('Combat map missing')
for actor in es.get_all_level_actors():
    if 'Training dummy' not in actor.get_actor_label():
        continue
    mesh = actor.get_editor_property('mesh')
    origin, extent = actor.get_actor_bounds(False)
    u.log('COMBAT_POSE actor={} location={} yaw={} component_rotation={} component_location={} actor_bounds={} actor_extent={}'.format(
        actor.get_actor_label(), actor.get_actor_location(), actor.get_actor_rotation(),
        mesh.get_editor_property('relative_rotation'), mesh.get_editor_property('relative_location'),
        origin, extent))
