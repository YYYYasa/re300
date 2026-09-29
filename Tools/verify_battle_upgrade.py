"""Validate the runtime traversal, zoom endpoints, stop blending and combat results."""
from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[1]
log = (root / 'Research/battle_upgrade_runtime.log').read_text(encoding='utf8', errors='replace')
checks = {
    'walk_surface': 'REBIRTH_BATTLE_GROUND_START found=1' in log,
    'blend_two_samples': 'REBIRTH_UPGRADE_BLEND valid=1 samples=2' in log,
    'beyond_old_movement_bounds': bool(re.search(r'REBIRTH_UPGRADE_TRAVERSE.*beyond_old_bounds=1', log)),
    'zoom_near': 'REBIRTH_COMBAT_ZOOM target=280' in log,
    'zoom_far': 'REBIRTH_COMBAT_ZOOM target=4500' in log,
    'attack_hit': 'REBIRTH_COMBAT_HIT damage=75' in log,
    'skill_hit': 'REBIRTH_COMBAT_HIT damage=165' in log,
    'filter_toggle': 'REBIRTH_COMBAT_STYLE anime' in log,
}
alphas = {}
for name in ('initial', 'middle', 'settled'):
    match = re.search(r'REBIRTH_UPGRADE_STOP ' + name + r'=([0-9.]+)', log)
    alphas[name] = float(match.group(1)) if match else None
checks['smooth_stop'] = (all(x is not None for x in alphas.values()) and
                         alphas['initial'] > alphas['middle'] > alphas['settled'] and
                         alphas['initial'] > .8 and alphas['middle'] > .1 and alphas['settled'] < .05)
checks['screenshots'] = all((root / 'EternalRebirth/Saved/Screenshots' / name).exists()
                            for name in ('Upgrade_Attack.png', 'Upgrade_Skill.png', 'Upgrade_Anime.png'))
report = dict(passed=all(checks.values()), checks=checks, stop_alpha=alphas)
(root / 'Research/battle_upgrade_verification.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['passed'] else 1)
