"""Try candidate dummy rotations in memory; never save the map."""
import unreal as u

ls = u.get_editor_subsystem(u.LevelEditorSubsystem)
es = u.get_editor_subsystem(u.EditorActorSubsystem)
if not ls.load_level('/Game/Maps/HeroCombatPrototype'):
    raise RuntimeError('Combat map missing')
dummy = next(a for a in es.get_all_level_actors() if a.get_actor_label() == 'Training dummy')
for pitch, yaw, roll in ((0, 180, 0), (0, 90, 0), (0, 0, 0), (0, 180, 180)):
    dummy.set_actor_rotation(u.Rotator(pitch, yaw, roll), False)
    origin, extent = dummy.get_actor_bounds(False)
    u.log('COMBAT_ORIENTATION requested={} actual={} bottom={:.2f} top={:.2f} component={}'.format(
        (pitch, yaw, roll), dummy.get_actor_rotation(), origin.z - extent.z,
        origin.z + extent.z, dummy.get_editor_property('mesh').get_editor_property('relative_rotation')))
