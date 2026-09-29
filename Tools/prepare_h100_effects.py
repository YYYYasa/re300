"""Extract every base-skin H100 effect and its referenced textures, read-only."""
from collections import defaultdict
from io import BytesIO
from pathlib import Path
import json
import sys
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from inspect_client import data
from hero_jumpx import JumpXHero

root = Path(__file__).resolve().parents[1]
out = root / 'EternalRebirth/SourceArt/Effects/H100'
(out / 'Raw').mkdir(parents=True, exist_ok=True)
(out / 'Textures').mkdir(parents=True, exist_ok=True)
items = json.loads((root / 'Research/client_inventory.json').read_text(encoding='utf8'))
by_name = defaultdict(list)
for item in items:
    by_name[Path(item['name'].replace('\\', '/')).name.lower()].append(item)

def find_texture(name):
    stem = Path(name.replace('\\', '/')).stem.lower()
    candidates = []
    for extension in ('.dds', '.tga', '.png', '.bmp'):
        candidates.extend(by_name[stem + extension])
    candidates.sort(key=lambda entry: (
        '/magic/textures/' in entry['name'].replace('\\', '/').lower(),
        entry['name'].lower().endswith(name.lower())), reverse=True)
    return candidates[0] if candidates else None

effects, textures, missing = [], {}, []
for item in items:
    path = item['name'].replace('\\', '/')
    if '/magic/skill/100_bolilinmeng/' not in path.lower() or '_skin' in path.lower() or not path.lower().endswith('.x'):
        continue
    raw = data(item)
    model = JumpXHero(raw)
    name = Path(path).stem
    destination = out / 'Raw' / path.lower().split('/100_bolilinmeng/', 1)[1]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    effects.append(dict(name=name, source=path, file=destination.relative_to(out).as_posix(),
                        meshes=len(model.meshes), bones=len(model.bones), actions=model.actions,
                        textures=model.textures))
    for source_texture in model.textures:
        stem = Path(source_texture.replace('\\', '/')).stem.lower()
        if stem in textures:
            continue
        candidate = find_texture(source_texture)
        if not candidate:
            missing.append(source_texture)
            continue
        try:
            image = Image.open(BytesIO(data(candidate))).convert('RGBA')
            png = out / 'Textures' / (stem + '.png')
            image.save(png)
            textures[stem] = dict(file=png.relative_to(out).as_posix(), source=candidate['name'], size=list(image.size))
        except Exception as exc:
            missing.append(source_texture + ': ' + str(exc))
companions, portraits = {}, {}
for item in items:
    path = item['name'].replace('\\', '/')
    lower = path.lower()
    if ('/effect/skill/100_bolilinmeng/' in lower and '_skin' not in lower) or lower.endswith('/audio/hero/100.bank'):
        relative = lower.split('/data/', 1)[-1]
        destination = out / 'SourceConfig' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data(item))
        companions[lower] = destination.relative_to(out).as_posix()
    if lower in ('../ui/head/half/half_0100.bmp', '../ui/head/small/sm_0100.bmp',
                 '../ui/head/role/chara_0100.dds', '../ui/hero/100.bmp', '../ui/icon/supericon/100.png'):
        key = Path(lower).stem if '/hero/' not in lower else 'hero_100'
        if '/supericon/' in lower:
            key = 'super_100'
        destination = out / 'UI' / (key + '.png')
        destination.parent.mkdir(parents=True, exist_ok=True)
        image = Image.open(BytesIO(data(item))).convert('RGBA')
        image.save(destination)
        portraits[key] = dict(file=destination.relative_to(out).as_posix(), source=path, size=list(image.size))
manifest = dict(hero='H100', source_effects=effects, textures=textures,
                source_configs=companions, ui=portraits, missing_textures=sorted(set(missing)))
(out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf8')
print('REBIRTH_H100_EFFECTS_PREPARED', len(effects), 'sources', len(textures), 'textures', len(missing), 'missing')
print('REBIRTH_H100_COMPANIONS', len(companions), 'configs/audio', len(portraits), 'UI images')
