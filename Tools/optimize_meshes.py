"""Enable Nanite on eligible reconstructed scene cells and record the result."""
import unreal as u
import json
from pathlib import Path
el=u.EditorAssetLibrary
records=[]
for path in el.list_assets(globals().get('mesh_path','/Game/Art/Meshes_Showcase'),True,False):
    mesh=u.load_asset(path)
    if not isinstance(mesh,u.StaticMesh):continue
    slots=len(mesh.get_editor_property('static_materials'))
    eligible=not mesh.get_name().startswith('SM_Water') and slots<=64
    cfg=mesh.get_editor_property('nanite_settings')
    if eligible and not cfg.get_editor_property('enabled'):
        cfg.set_editor_property('enabled',True)
        cfg.set_editor_property('explicit_tangents',True)
        mesh.set_editor_property('nanite_settings',cfg)
        el.save_loaded_asset(mesh,False)
    records.append(dict(mesh=mesh.get_name(),material_slots=slots,nanite=bool(cfg.get_editor_property('enabled'))))
Path('G:/Code/UE/EternalRebirth/Saved/nanite-report.json').write_text(json.dumps(records,indent=2))
u.log('REBIRTH: NANITE_COMPLETE')
