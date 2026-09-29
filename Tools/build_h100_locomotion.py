"""Create a cooked 1D blend space for smooth H100 idle/run transitions."""
import unreal as u

path = '/Game/Art/Heroes/H100'
assets = u.EditorAssetLibrary
asset = u.load_asset(path + '/BS_H100_Locomotion')
if not asset:
    factory = u.BlendSpaceFactory1D()
    factory.set_editor_property('target_skeleton', u.load_asset(path + '/SK_H100_Skeleton'))
    asset = u.AssetToolsHelpers.get_asset_tools().create_asset('BS_H100_Locomotion', path, u.BlendSpace1D, factory)
if not isinstance(asset, u.BlendSpace1D):
    raise RuntimeError('Could not create blend space')
idle = u.load_asset(path + '/AN_H100_Idle')
run = u.load_asset(path + '/AN_H100_Run')
if not idle or not run:
    raise RuntimeError('H100 movement clips missing')
axis = u.BlendParameter()
axis.set_editor_properties({'display_name': 'Movement', 'min': 0., 'max': 1., 'grid_num': 4})
asset.set_editor_property('blend_parameters', [axis, u.BlendParameter(), u.BlendParameter()])
idle_sample = u.BlendSample()
idle_sample.set_editor_properties({'animation': idle, 'sample_value': u.Vector(0, 0, 0)})
run_sample = u.BlendSample()
run_sample.set_editor_properties({'animation': run, 'sample_value': u.Vector(1, 0, 0)})
asset.set_editor_property('sample_data', [idle_sample, run_sample])
asset.set_editor_property('target_weight_interpolation_speed_per_sec', 6.)
if not assets.save_loaded_asset(asset, False):
    raise RuntimeError('Could not save H100 blend space')
u.log('REBIRTH_H100_BLEND_COMPLETE samples=' + str(len(asset.get_editor_property('sample_data'))))
