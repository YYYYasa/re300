"""Read-only check of client walkable/collision meshes omitted from beauty geometry."""
from collections import defaultdict
from pathlib import Path
import json
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from inspect_client import data
from hero_jumpx import JumpXHero

root = Path(__file__).resolve().parents[1]
inventory = json.loads((root / 'Research/client_inventory.json').read_text(encoding='utf8'))
layout = json.loads((root / 'Research/scene_layout.json').read_text(encoding='utf8'))
by_name = defaultdict(list)
for item in inventory:
    by_name[Path(item['name'].replace('\\', '/')).name.lower()].append(item)
seen = set()
for scene in layout:
    if scene['group'] in ('sound', 'effect', 'wall'):
        continue
    path = scene['name']
    if path.lower() not in by_name:
        continue
    item = by_name[path.lower()][0]
    if item['name'] in seen:
        continue
    seen.add(item['name'])
    try:
        model = JumpXHero(data(item))
    except Exception as exc:
        print('PARSE_ERROR', path, exc)
        continue
    helpers = [mesh for mesh in model.meshes if mesh.flags in (4, 5, 9)]
    for mesh in helpers:
        bounds = (np.round(mesh.positions.min(axis=0), 1).tolist(),
                  np.round(mesh.positions.max(axis=0), 1).tolist())
        print('HELPER', path, 'flag', mesh.flags, 'name', mesh.name,
              'vertices', len(mesh.positions), 'triangles', len(mesh.faces), 'bounds', bounds)
