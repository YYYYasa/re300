"""Read-only inventory of H100 actions, base-skin effects, and arena collision proxies."""
from collections import Counter
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))
from inspect_client import data
from hero_jumpx import JumpXHero

root = Path(__file__).resolve().parents[1]
items = json.loads((root / 'Research/client_inventory.json').read_text(encoding='utf8'))
effects = [x for x in items if '/magic/skill/100_bolilinmeng/' in x['name'].replace('\\', '/').lower()
           and '_skin' not in x['name'].lower()]
print('H100_BASE_EFFECT_FILES', len(effects))
print('H100_EFFECT_EXTENSIONS', Counter(Path(x['name']).suffix.lower() for x in effects))
for item in effects:
    print('H100_EFFECT', item['name'], 'size', item['size'])
    if item['name'].lower().endswith('.x'):
        try:
            model = JumpXHero(data(item))
            print('  PARSED', len(model.meshes), 'meshes', len(model.textures), 'textures',
                  len(model.bones), 'bones', len(model.actions), 'actions')
            print('  TEXTURES', model.textures[:12])
        except Exception as exc:
            print('  PARSE_ERROR', type(exc).__name__, str(exc)[:180])

hero = JumpXHero((root / 'EternalRebirth/SourceArt/Heroes/100/100.x').read_bytes())
print('H100_ACTIONS', hero.actions)
