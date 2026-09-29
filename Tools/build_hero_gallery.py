"""Create a separate lit gallery map for validating imported heroes."""
import unreal as u

EL = u.EditorAssetLibrary
AT = u.AssetToolsHelpers.get_asset_tools()
ML = u.MaterialEditingLibrary
ES = u.get_editor_subsystem(u.EditorActorSubsystem)
LS = u.get_editor_subsystem(u.LevelEditorSubsystem)
MAP = '/Game/Maps/HeroShowcase'
MATERIALS = '/Game/Art/Heroes/Materials'
EL.make_directory(MATERIALS)


def color_material(name, color, roughness):
    material = u.load_asset(MATERIALS + '/' + name) or AT.create_asset(
        name, MATERIALS, u.Material, u.MaterialFactoryNew())
    ML.delete_all_material_expressions(material)
    tint = ML.create_material_expression(material, u.MaterialExpressionConstant3Vector, 0, 0)
    tint.set_editor_property('constant', u.LinearColor(*color))
    ML.connect_material_property(tint, '', u.MaterialProperty.MP_BASE_COLOR)
    rough = ML.create_material_expression(material, u.MaterialExpressionConstant, 0, 200)
    rough.set_editor_property('r', roughness)
    ML.connect_material_property(rough, '', u.MaterialProperty.MP_ROUGHNESS)
    ML.recompile_material(material)
    EL.save_loaded_asset(material, False)
    return material


floor_material = color_material('M_GalleryFloor', (.075, .11, .15), .55)
back_material = color_material('M_GalleryBackdrop', (.035, .06, .10), .9)
if EL.does_asset_exist(MAP):
    if not LS.load_level(MAP):
        raise RuntimeError('Cannot load hero gallery')
    for old in ES.get_all_level_actors():
        if old.get_class().get_name() not in ('WorldSettings', 'DefaultPhysicsVolume', 'Brush'):
            ES.destroy_actor(old)
else:
    if not LS.new_level(MAP):
        raise RuntimeError('Cannot create hero gallery')


def actor(cls, name, position=(0, 0, 0), rotation=(0, 0, 0)):
    result = ES.spawn_actor_from_class(cls, u.Vector(*position), u.Rotator(*rotation))
    result.set_actor_label(name)
    return result


cube = u.load_asset('/Engine/BasicShapes/Cube')


def architecture(name, material, position, scale):
    result = actor(u.StaticMeshActor, name, position)
    result.static_mesh_component.set_static_mesh(cube)
    result.static_mesh_component.set_material(0, material)
    result.set_actor_scale3d(u.Vector(*scale))
    return result


architecture('Gallery floor', floor_material, (0, 0, -15), (13, 6, .3))
architecture('Gallery backdrop', back_material, (0, 340, 300), (13, .3, 6))
for index, hero_id in enumerate(('013', '100', '101')):
    x = (index - 1) * 310
    architecture('Plinth H' + hero_id, floor_material, (x, 0, 4), (2.35, 1.75, .08))
    mesh = u.load_asset(f'/Game/Art/Heroes/H{hero_id}/SK_H{hero_id}')
    if not isinstance(mesh, u.SkeletalMesh):
        raise RuntimeError('Missing skeletal mesh ' + hero_id)
    hero = actor(u.SkeletalMeshActor, 'Hero H' + hero_id, (x, 0, 8))
    hero.skeletal_mesh_component.set_skeletal_mesh(mesh)
    hero.set_actor_scale3d(u.Vector(2, 2, 2))
    hero.set_actor_rotation(u.Rotator(0, 180, 0), False)
    # Match the component transform corrected and saved in the editor.
    # The source FBX's local up axis is inverted relative to this level.
    hero.skeletal_mesh_component.set_editor_property(
        'relative_rotation', u.Rotator(180, 360, -180))
    hero.set_folder_path('02 / Imported Heroes')
    hero.tags = ['Hero' + hero_id]

actor(u.SkyAtmosphere, 'Gallery atmosphere')
sun = actor(u.DirectionalLight, 'Studio sun', rotation=(-40, -24, 0))
sun_component = sun.get_component_by_class(u.DirectionalLightComponent)
sun_component.set_mobility(u.ComponentMobility.MOVABLE)
sun_component.set_intensity(2.2)
sun_component.set_light_color(u.LinearColor(1, .92, .82))
sun_component.set_editor_property('light_source_angle', 5.)
sky = actor(u.SkyLight, 'Studio skylight')
sky_component = sky.get_component_by_class(u.SkyLightComponent)
sky_component.set_mobility(u.ComponentMobility.MOVABLE)
sky_component.set_editor_property('real_time_capture', True)
sky_component.set_intensity(.75)
for x, color in ((-450, (.35, .75, 1.)), (450, (1., .45, .36))):
    fill = actor(u.PointLight, 'Studio fill', (x, -150, 260))
    component = fill.get_component_by_class(u.PointLightComponent)
    component.set_mobility(u.ComponentMobility.MOVABLE)
    component.set_intensity(140)
    component.set_light_color(u.LinearColor(*color))
    component.set_attenuation_radius(900)
post = actor(u.PostProcessVolume, 'Hero color grade')
post.set_editor_property('unbound', True)
settings = post.get_editor_property('settings')
for name, value in (('auto_exposure_min_brightness', 1.),
                    ('auto_exposure_max_brightness', 1.),
                    ('bloom_intensity', .35),
                    ('motion_blur_amount', 0.)):
    settings.set_editor_property('override_' + name, True)
    settings.set_editor_property(name, value)
post.set_editor_property('settings', settings)
eye = u.Vector(0, -820, 220)
target = u.Vector(0, 0, 105)
view = actor(u.TargetPoint, 'View1 | hero lineup', (eye.x, eye.y, eye.z))
view.tags = ['View1']
view.set_actor_rotation(u.MathLibrary.find_look_at_rotation(eye, target), False)
start = actor(u.PlayerStart, 'Gallery start', (eye.x, eye.y, eye.z))
start.set_actor_rotation(view.get_actor_rotation(), False)
u.EditorLevelLibrary.set_level_viewport_camera_info(eye, view.get_actor_rotation())
if not LS.save_current_level():
    raise RuntimeError('Could not save hero gallery')
u.log('REBIRTH: HERO_GALLERY_COMPLETE heroes=3')
