import unreal as u
for name in ('BlendSpace1D', 'BlendSpace', 'BlendSpaceFactory1D', 'BlendSpaceLibrary', 'AnimationBlueprintLibrary'):
    cls = getattr(u, name, None)
    u.log('BLEND_API ' + name + ' ' + str(cls))
    if cls:
        u.log('BLEND_MEMBERS ' + name + ' ' + ','.join(x for x in dir(cls) if 'sample' in x.lower() or 'blend' in x.lower() or 'axis' in x.lower() or 'skeleton' in x.lower()))
for name in ('BlendSample', 'BlendParameter'):
    cls = getattr(u, name, None)
    u.log('BLEND_STRUCT ' + name + ' ' + str(cls))
    if cls:
        obj = cls()
        u.log('BLEND_STRUCT_MEMBERS ' + name + ' ' + ','.join(x for x in dir(obj) if not x.startswith('_')))
        u.log('BLEND_STRUCT_DICT ' + name + ' ' + str(obj.to_dict()))
factory = u.BlendSpaceFactory1D()
factory.set_editor_property('target_skeleton', u.load_asset('/Game/Art/Heroes/H100/SK_H100_Skeleton'))
asset = u.AssetToolsHelpers.get_asset_tools().create_asset('BS_H100_Probe', '/Game/Art/Heroes/H100', u.BlendSpace1D, factory)
u.log('BLEND_PROBE_ASSET ' + str(asset))
for name in ('sample_data', 'blend_parameters', 'target_weight_interpolation_speed_per_sec'):
    try:
        u.log('BLEND_PROBE_PROPERTY ' + name + ' ' + str(asset.get_editor_property(name)))
    except Exception as exc:
        u.log('BLEND_PROBE_PROPERTY_ERROR ' + name + ' ' + str(exc))
