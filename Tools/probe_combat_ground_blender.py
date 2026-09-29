"""Ray cast a few world positions against source FBX geometry in Blender."""
from pathlib import Path
import bpy
from mathutils import Vector

root = Path('G:/Code/UE/EternalRebirth/SourceArt/Meshes')
points = [(0, 0), (0, -500), (0, -1000), (500, -1000), (1000, -1000),
          (1500, -1000), (2000, -1000), (2200, -1500), (2200, -2000),
          (500, 1400), (1000, 1400), (-500, 1400), (-1500, 1000),
          (1500, -1500), (1700, -1500), (1900, -1500), (2100, -1500)]
points += [(x, y) for x in (500, 750, 1000, 1250, 1500, 1750, 2000)
           for y in (-1500, -1250, -1000, -750, -500)]
files = ['SM_Arena_2_2.fbx', 'SM_Arena_3_2.fbx', 'SM_Arena_2_3.fbx',
         'SM_Arena_2_1.fbx', 'SM_Arena_1_2.fbx', 'SM_Arena_1_1.fbx']
results = {point: [] for point in points}
for filename in files:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(root / filename))
    all_bounds = []
    for item in bpy.context.scene.objects:
        if item.type == 'MESH':
            all_bounds.extend(item.matrix_world @ Vector(corner) for corner in item.bound_box)
    if all_bounds:
        print('COMBAT_FBX_BOUNDS', filename,
              tuple(round(min(point[i] for point in all_bounds), 1) for i in range(3)),
              tuple(round(max(point[i] for point in all_bounds), 1) for i in range(3)), flush=True)
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        if filename == files[0] and obj.name == next((item.name for item in bpy.context.scene.objects if item.type == 'MESH'), ''):
            print('COMBAT_FBX_DEBUG', obj.name, 'matrix', obj.matrix_world, 'local_bounds', obj.bound_box[:2], flush=True)
        inv = obj.matrix_world.inverted()
        for point in points:
            origin = inv @ Vector((point[0]/100, point[1]/100, 30))
            direction = (inv.to_3x3() @ Vector((0, 0, -1))).normalized()
            hit, local, normal, face = obj.ray_cast(origin, direction, distance=10000)
            if hit:
                world = obj.matrix_world @ local
                results[point].append((round(world.z*100, 1), filename, obj.name))
for point, hits in results.items():
    print('COMBAT_FBX_GROUND', point, sorted(hits, reverse=True)[:8], flush=True)
