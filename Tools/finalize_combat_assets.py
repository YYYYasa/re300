import unreal as u

blend = u.load_asset('/Game/Art/Heroes/H100/BS_H100_Locomotion')
floor = u.load_asset('/Game/Art/Collision/SM_Arena_Walkable')
u.CombatAssetTools.finalize_movement_assets(blend, floor)
for asset in (blend, floor):
    u.EditorAssetLibrary.save_loaded_asset(asset, False)
u.log('REBIRTH: COMBAT_ASSETS_FINALIZED')
