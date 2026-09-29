"""Build a small playable top-down combat arena without changing the showcase."""
import unreal as u

EL = u.EditorAssetLibrary
AT = u.AssetToolsHelpers.get_asset_tools()
ML = u.MaterialEditingLibrary
ES = u.get_editor_subsystem(u.EditorActorSubsystem)
LS = u.get_editor_subsystem(u.LevelEditorSubsystem)
MAP = '/Game/Maps/HeroCombatPrototype'
ART = '/Game/Art/Combat'
EL.make_directory(ART)


def material(name, color, roughness=.7, metallic=0.):
    path = ART + '/' + name
    mat = u.load_asset(path) or AT.create_asset(name, ART, u.Material, u.MaterialFactoryNew())
    ML.delete_all_material_expressions(mat)
    rgb = ML.create_material_expression(mat, u.MaterialExpressionConstant3Vector, 0, 0)
    rgb.set_editor_property('constant', u.LinearColor(*color))
    ML.connect_material_property(rgb, '', u.MaterialProperty.MP_BASE_COLOR)
    rough = ML.create_material_expression(mat, u.MaterialExpressionConstant, 0, 210)
    rough.set_editor_property('r', roughness)
    ML.connect_material_property(rough, '', u.MaterialProperty.MP_ROUGHNESS)
    metal = ML.create_material_expression(mat, u.MaterialExpressionConstant, 0, 360)
    metal.set_editor_property('r', metallic)
    ML.connect_material_property(metal, '', u.MaterialProperty.MP_METALLIC)
    ML.recompile_material(mat)
    if not EL.save_loaded_asset(mat, False):
        raise RuntimeError('Could not save ' + path)
    return mat


floor_mat = material('M_ArenaFloor', (.13, .18, .24), .82)
rim_mat = material('M_ArenaRim', (.025, .12, .18), .32, .55)
accent_mat = material('M_ArenaAccent', (.11, .42, .48), .28, .25)
wall_mat = material('M_ArenaWall', (.055, .075, .12), .86)

if EL.does_asset_exist(MAP):
    if not LS.load_level(MAP):
        raise RuntimeError('Cannot load combat prototype')
    for old in ES.get_all_level_actors():
        if old.get_class().get_name() not in ('WorldSettings', 'DefaultPhysicsVolume', 'Brush'):
            ES.destroy_actor(old)
else:
    if not LS.new_level(MAP):
        raise RuntimeError('Cannot create combat prototype')


def actor(cls, name, location=(0, 0, 0), rotation=(0, 0, 0)):
    a = ES.spawn_actor_from_class(cls, u.Vector(*location), u.Rotator(*rotation))
    if not a:
        raise RuntimeError('Cannot spawn ' + name)
    a.set_actor_label(name)
    return a


cube = u.load_asset('/Engine/BasicShapes/Cube')


def block(name, mat, location, scale):
    a = actor(u.StaticMeshActor, name, location)
    a.static_mesh_component.set_static_mesh(cube)
    a.static_mesh_component.set_material(0, mat)
    a.set_actor_scale3d(u.Vector(*scale))
    return a


block('Arena ground', floor_mat, (0, 0, -20), (18, 18, .4))
for x in (-850, 850):
    block('Arena edge X', wall_mat, (x, 0, 38), (.35, 17, 1.15))
for y in (-850, 850):
    block('Arena edge Y', wall_mat, (0, y, 38), (17, .35, 1.15))
for x in (-600, 600):
    for y in (-600, 600):
        block('Arena pillar base', rim_mat, (x, y, 30), (1.3, 1.3, .6))
        block('Arena pillar', wall_mat, (x, y, 135), (.65, .65, 1.5))
        block('Arena pillar glow', accent_mat, (x, y, 210), (.75, .75, .09))
for x in (-500, 0, 500):
    block('Lane accent', accent_mat, (x, 0, .8), (3.8, .065, .016))
for y in (-520, 520):
    block('Lane rail', rim_mat, (0, y, 3), (14, .18, .055))

start = actor(u.PlayerStart, 'H100 player start', (-260, 0, 90), (0, 0, 0))
start.set_folder_path('Combat')
dummy_class = u.load_class(None, '/Script/EternalRebirth.CombatTrainingDummy')
mode_class = u.load_class(None, '/Script/EternalRebirth.CombatArenaGameMode')
if not dummy_class or not mode_class:
    raise RuntimeError('Compile CombatPrototype C++ before building map')
dummy = actor(dummy_class, 'Training dummy', (170, 0, 90))
dummy.set_folder_path('Combat')
world_settings = u.EditorLevelLibrary.get_editor_world().get_world_settings()
world_settings.set_editor_property('default_game_mode', mode_class)

actor(u.SkyAtmosphere, 'Arena atmosphere')
sun = actor(u.DirectionalLight, 'Arena sun', rotation=(-48, -25, 0))
sun_component = sun.get_component_by_class(u.DirectionalLightComponent)
sun_component.set_mobility(u.ComponentMobility.MOVABLE)
sun_component.set_intensity(2.8)
sun_component.set_light_color(u.LinearColor(1, .9, .79))
sun_component.set_editor_property('light_source_angle', 4.5)
sky = actor(u.SkyLight, 'Arena skylight')
sky_component = sky.get_component_by_class(u.SkyLightComponent)
sky_component.set_mobility(u.ComponentMobility.MOVABLE)
sky_component.set_editor_property('real_time_capture', True)
sky_component.set_intensity(.8)
for y, color in ((-590, (.3, .75, 1.)), (590, (1., .47, .28))):
    light = actor(u.PointLight, 'Arena fill', (80, y, 370))
    comp = light.get_component_by_class(u.PointLightComponent)
    comp.set_mobility(u.ComponentMobility.MOVABLE)
    comp.set_intensity(150)
    comp.set_light_color(u.LinearColor(*color))
    comp.set_attenuation_radius(1200)
post = actor(u.PostProcessVolume, 'Arena grade')
post.set_editor_property('unbound', True)
settings = post.get_editor_property('settings')
for name, value in (('auto_exposure_min_brightness', 1.),
                    ('auto_exposure_max_brightness', 1.),
                    ('bloom_intensity', .42),
                    ('motion_blur_amount', 0.)):
    settings.set_editor_property('override_' + name, True)
    settings.set_editor_property(name, value)
post.set_editor_property('settings', settings)
if not LS.save_current_level():
    raise RuntimeError('Could not save combat prototype')
u.log('REBIRTH: COMBAT_ARENA_COMPLETE map=' + MAP)
