"""Duplicate the showcase and add a playable combat area without editing its source map."""
import unreal as u

source = '/Game/Maps/EternalShowcase'
target = '/Game/Maps/EternalCombat'
assets = u.EditorAssetLibrary
levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)

if not assets.does_asset_exist(source):
    raise RuntimeError('Source showcase map is missing')
if not assets.does_asset_exist(target):
    if not assets.duplicate_asset(source, target):
        raise RuntimeError('Could not duplicate showcase map')
if not levels.load_level(target):
    raise RuntimeError('Could not load duplicated combat map')

for old in actors.get_all_level_actors():
    name = old.get_class().get_name()
    if name in ('PlayerStart', 'RebirthPawn', 'CombatTrainingDummy') or old.get_actor_label() == 'Combat walkable floor':
        actors.destroy_actor(old)

def spawn(cls, label, xyz):
    result = actors.spawn_actor_from_class(cls, u.Vector(*xyz), u.Rotator(0, 0, 0))
    if not result:
        raise RuntimeError('Could not spawn ' + label)
    result.set_actor_label(label)
    result.set_folder_path('Combat')
    return result

floor = spawn(u.StaticMeshActor, 'Combat walkable floor', (0, 0, 0))
walkable = u.load_asset('/Game/Art/Collision/SM_Arena_Walkable')
if not isinstance(walkable, u.StaticMesh):
    raise RuntimeError('Import the client walk surface before building battle map')
floor.static_mesh_component.set_static_mesh(walkable)
floor.static_mesh_component.set_collision_profile_name('BlockAll')
floor.static_mesh_component.set_visibility(False)
floor.set_editor_property('tags', ['BattleWalkSurface'])
u.log('REBIRTH_WALKABLE_BOUNDS mesh={} actor={} collision={} profile={} trace_flag={}'.format(
    walkable.get_bounds(), floor.get_actor_bounds(False),
    floor.static_mesh_component.get_collision_enabled(),
    floor.static_mesh_component.get_collision_profile_name(),
    walkable.get_editor_property('body_setup').get_editor_property('collision_trace_flag')))

spawn(u.PlayerStart, 'H100 battle spawn', (980, -1100, 90))
dummy_class = u.load_class(None, '/Script/EternalRebirth.CombatTrainingDummy')
mode_class = u.load_class(None, '/Script/EternalRebirth.CombatArenaGameMode')
if not dummy_class or not mode_class:
    raise RuntimeError('Combat C++ classes are unavailable; build editor module first')
spawn(dummy_class, 'Training dummy', (1190, -1100, 90))
world = u.EditorLevelLibrary.get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode', mode_class)
for x, y in ((980, -1100), (1190, -1100), (3000, 1500), (-3500, 3500)):
    hit = u.SystemLibrary.line_trace_single(world, u.Vector(x, y, 3000),
                                            u.Vector(x, y, -3000),
                                            u.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                                            [], u.DrawDebugTrace.NONE, True)
    u.log('REBIRTH_WALKABLE_TRACE {} {} {}'.format(x, y, hit))
if not levels.save_current_level():
    raise RuntimeError('Could not save copied combat map')
u.log('REBIRTH: ETERNAL_COMBAT_COMPLETE map={} actors={} game_mode={}'.format(
    target, len(actors.get_all_level_actors()), mode_class.get_name()))
