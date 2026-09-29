"""Read-only complex ground traces around candidate combat lanes."""
import unreal as u

ls = u.get_editor_subsystem(u.LevelEditorSubsystem)
if not ls.load_level('/Game/Maps/EternalShowcase'):
    raise RuntimeError('Showcase map missing')
world = u.EditorLevelLibrary.get_editor_world()
points = [(0, 0), (0, -500), (0, -1000), (500, -1000), (1000, -1000),
          (1500, -1000), (2000, -1000), (2200, -1500), (2200, -2000),
          (500, 1400), (1000, 1400), (-500, 1400), (-1500, 1000)]
for x, y in points:
    try:
        hit = u.SystemLibrary.line_trace_single(
            world, u.Vector(x, y, 2000), u.Vector(x, y, -2000),
            u.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], u.DrawDebugTrace.NONE, True)
        u.log('COMBAT_GROUND point=({}, {}) hit={}'.format(x, y, hit))
    except Exception as error:
        u.log_error('COMBAT_GROUND_ERROR point=({}, {}) error={}'.format(x, y, error))
