"""Extract selected base heroes and their referenced textures from the local client.

Reads D:/JumpGame/300Hero only. All outputs stay in this UE workspace.
"""
from pathlib import Path, PureWindowsPath
from io import BytesIO
import argparse
import collections
import json
import sys
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from inspect_client import data
from hero_jumpx import JumpXHero

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'EternalRebirth' / 'SourceArt' / 'Heroes'
ITEMS = json.loads((ROOT / 'Research' / 'client_inventory.json').read_text(encoding='utf8'))
BY_NAME = collections.defaultdict(list)
for item in ITEMS:
    BY_NAME[PureWindowsPath(item['name']).name.lower()].append(item)


def find_texture(name):
    stem = PureWindowsPath(name).stem.lower()
    candidates = []
    for ext in ('.dds', '.tga', '.png', '.bmp'):
        candidates.extend(BY_NAME[stem + ext])
    candidates.sort(key=lambda item: (
        '/character/roleaction/' in item['name'].lower().replace('\\', '/'),
        '/magic/textures/' in item['name'].lower().replace('\\', '/'),
        item['name'].lower().endswith(name.lower())), reverse=True)
    return candidates[0] if candidates else None


def prepare(hero_id):
    name = f'{hero_id}.x'
    candidates = [item for item in BY_NAME[name.lower()]
                  if '/character/roleaction/' in item['name'].lower().replace('\\', '/')]
    if not candidates:
        raise FileNotFoundError(f'Hero model {name} is absent')
    raw = data(candidates[0])
    hero = JumpXHero(raw)
    folder = OUT / hero_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(raw)
    textures = {}
    missing = []
    for source_name in hero.textures:
        item = find_texture(source_name)
        if not item:
            missing.append(source_name)
            continue
        destination = folder / (PureWindowsPath(source_name).stem.lower() + '.png')
        if not destination.exists():
            with Image.open(BytesIO(data(item))) as image:
                image.convert('RGBA').save(destination)
        with Image.open(destination) as image:
            alpha = image.getchannel('A')
            transparent = alpha.histogram()[:128]
            masked = sum(transparent) > image.width * image.height * .01
        textures[source_name] = dict(file=destination.name, source=item['name'], masked=masked)
    report = dict(id=hero_id, source=candidates[0]['name'], version=int.from_bytes(raw[80:84], 'little'),
                  meshes=len(hero.meshes), triangles=sum(len(mesh.faces) for mesh in hero.meshes),
                  bones=len(hero.bones), actions=hero.actions, textures=textures, missing_textures=missing)
    (folder / 'source.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(f"HERO_PREPARED {hero_id} meshes={report['meshes']} bones={report['bones']} "
          f"actions={len(hero.actions)} textures={len(textures)} missing={len(missing)}", flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ids', nargs='+', help='Three-digit base hero IDs')
    args = parser.parse_args()
    for selected in args.ids:
        if len(selected) != 3 or not selected.isdigit():
            raise ValueError(f'Expected a three-digit hero ID: {selected}')
        prepare(selected)
