"""Inspect UE's imported hero slots and bounds without modifying assets."""
import unreal as u

for hero_id in ('013', '100', '101'):
    mesh = u.load_asset(f'/Game/Art/Heroes/H{hero_id}/SK_H{hero_id}')
    if not mesh:
        raise RuntimeError(f'Missing hero {hero_id}')
    bounds = mesh.get_bounds()
    for index, slot in enumerate(mesh.get_editor_property('materials')):
        u.log(f'REBIRTH_HERO_SLOT id={hero_id} index={index} name={slot.get_editor_property("material_slot_name")} '
              f'imported={slot.get_editor_property("imported_material_slot_name")} '
              f'material={slot.get_editor_property("material_interface")}')
    u.log(f'REBIRTH_HERO_BOUNDS id={hero_id} origin={bounds.origin} extent={bounds.box_extent} '
          f'slots={len(mesh.get_editor_property("materials"))}')
