"""Read-only survey of likely combat locations on the reconstructed map."""
import unreal as u

ls = u.get_editor_subsystem(u.LevelEditorSubsystem)
es = u.get_editor_subsystem(u.EditorActorSubsystem)
if not ls.load_level('/Game/Maps/EternalShowcase'):
    raise RuntimeError('Showcase map missing')
points = [(0, 0), (500, 1400), (2200, -1500), (-1500, 1000), (1000, -1000),
          (2000, -1000), (1500, -2000), (-2000, 2000)]
actors = []
for actor in es.get_all_level_actors():
    if not isinstance(actor, u.StaticMeshActor):
        continue
    origin, extent = actor.get_actor_bounds(False)
    actors.append((actor.get_actor_label(), origin, extent))
for x, y in points:
    matches = []
    for name, origin, extent in actors:
        if abs(origin.x - x) <= extent.x and abs(origin.y - y) <= extent.y:
            matches.append((name, round(origin.z-extent.z), round(origin.z+extent.z),
                            round(extent.x), round(extent.y)))
    matches.sort(key=lambda row: row[2], reverse=True)
    u.log('COMBAT_SITE point=({}, {}) candidates={}'.format(x, y, matches[:16]))
u.log('COMBAT_SITE line_trace_doc=' + str(u.SystemLibrary.line_trace_single.__doc__)[:1400])
