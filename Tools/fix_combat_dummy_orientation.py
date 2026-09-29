"""Make the existing training dummy upright without rebuilding the arena."""
import unreal as u

ls = u.get_editor_subsystem(u.LevelEditorSubsystem)
es = u.get_editor_subsystem(u.EditorActorSubsystem)
if not ls.load_level('/Game/Maps/HeroCombatPrototype'):
    raise RuntimeError('Combat map missing')
dummy = next(a for a in es.get_all_level_actors() if a.get_actor_label() == 'Training dummy')
dummy.set_actor_rotation(u.Rotator(0, 0, 0), False)
origin, extent = dummy.get_actor_bounds(False)
if origin.z - extent.z < -1:
    raise RuntimeError('Dummy remains below arena floor')
if not ls.save_current_level():
    raise RuntimeError('Could not save corrected combat map')
u.log('REBIRTH: COMBAT_DUMMY_ORIENTATION_FIXED bottom={:.2f}'.format(origin.z - extent.z))
