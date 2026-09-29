"""Final light and material tuning for the saved showcase map."""
import unreal as u
from pathlib import Path
exec(Path('G:/Code/UE/Tools/finalize_materials.py').read_text())
ls=u.get_editor_subsystem(u.LevelEditorSubsystem)
es=u.get_editor_subsystem(u.EditorActorSubsystem)
if not ls.load_level('/Game/Maps/EternalShowcase'):raise RuntimeError('Showcase map missing')
found=False
for a in es.get_all_level_actors():
    if a.get_actor_label()=='Gate radiance':
        gate_light=a.get_component_by_class(u.PointLightComponent)
        gate_light.set_intensity(3000)
        gate_light.set_attenuation_radius(1800)
        found=True
if not found:raise RuntimeError('Gate light missing')
if not ls.save_current_level():raise RuntimeError('Failed to save tuned map')
u.log('REBIRTH: TUNING_COMPLETE')
