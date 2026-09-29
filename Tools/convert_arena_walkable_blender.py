"""Restore the client's hidden floor proxies as a collision-only UE mesh."""
from collections import defaultdict
from pathlib import Path
import json
import sys
import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from inspect_client import data
from hero_jumpx import JumpXHero

root = Path(__file__).resolve().parents[1]
out = root / 'EternalRebirth/SourceArt/Collision/SM_Arena_Walkable.fbx'
out.parent.mkdir(parents=True, exist_ok=True)
inventory = json.loads((root / 'Research/client_inventory.json').read_text(encoding='utf8'))
layout = json.loads((root / 'Research/scene_layout.json').read_text(encoding='utf8'))
by_name = defaultdict(list)
for item in inventory:
    by_name[Path(item['name'].replace('\\', '/')).name.lower()].append(item)

verts, faces = [], []
used = []
for scene in layout:
    if not scene['name'].lower().startswith('floor'):
        continue
    item = next((x for x in by_name[scene['name'].lower()]
                 if '/lm4jjcmap/' in x['name'].replace('\\', '/').lower()), None)
    if not item:
        item = by_name[scene['name'].lower()][0]
    model = JumpXHero(data(item))
    for mesh in model.meshes:
        if mesh.flags != 4:
            continue
        position = mesh.positions * np.array(scene['scale']) * 100
        position += (np.array(scene['loc']) - np.array([164, 164, 0])) * 100
        position[:, 2] -= 20  # The proxy's source surface sits 20 cm above the beauty mesh.
        base = len(verts)
        verts.extend(position.tolist())
        for tri in mesh.faces:
            a, b, c = (int(i) for i in tri)
            normal_z = np.cross(position[b] - position[a], position[c] - position[a])[2]
            faces.append((base+a, base+b, base+c) if normal_z >= 0 else
                         (base+a, base+c, base+b))
        used.append(scene['name'])

if not faces:
    raise RuntimeError('No client floor proxies were found')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = .01
mesh = bpy.data.meshes.new('SM_Arena_Walkable')
mesh.from_pydata(verts, [], faces)
mesh.update()
obj = bpy.data.objects.new('SM_Arena_Walkable', mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(out), use_selection=True, object_types={'MESH'},
                         mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
                         axis_forward='-Y', axis_up='Z', use_space_transform=True)
print('REBIRTH_WALKABLE_EXPORTED', len(used), 'tiles', len(verts), 'vertices',
      len(faces), 'triangles', out.stat().st_size, flush=True)
