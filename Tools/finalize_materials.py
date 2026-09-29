"""Persist Nanite material usage to avoid runtime shader fallback/recompiles."""
import unreal as u
el=u.EditorAssetLibrary;ml=u.MaterialEditingLibrary
for name in ('M_Surface','M_Foliage','M_neutral'):
    m=u.load_asset('/Game/Art/Materials/'+name)
    ml.set_material_usage(m,u.MaterialUsage.MATUSAGE_NANITE)
    ml.recompile_material(m)
    if not el.save_loaded_asset(m,False):raise RuntimeError('Material save failed: '+name)
for path in el.list_assets('/Game/Art/Materials',True,False):
    mi=u.load_asset(path)
    if isinstance(mi,u.MaterialInstanceConstant):
        ml.set_material_usage_override(mi,u.MaterialUsage.MATUSAGE_NANITE,True,True)
        ml.update_material_instance(mi)
        if not el.save_loaded_asset(mi,False):raise RuntimeError('Instance save failed: '+path)
u.log('REBIRTH: MATERIALS_FINALIZED')
