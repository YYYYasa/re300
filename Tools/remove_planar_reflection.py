"""Drop the experimental expensive river reflection capture."""
import unreal as u

levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
if not levels.load_level('/Game/Maps/EternalShowcase'):
    raise RuntimeError('Showcase level missing')
removed=0
for actor in actors.get_all_level_actors():
    if actor.get_actor_label()=='River | planar reflection':
        actors.destroy_actor(actor)
        removed+=1
if removed and not levels.save_current_level():
    raise RuntimeError('Could not save map without planar reflection')
u.log('REBIRTH: PLANAR_REFLECTION_REMOVED count=%d' % removed)
