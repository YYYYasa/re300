"""Convert mesh-bearing H100 effects; retain particle-only sources in the manifest."""
from pathlib import Path
import json
import sys
import bpy
sys.path.insert(0, str(Path(__file__).parent))
from hero_jumpx import JumpXHero

root = Path(__file__).resolve().parents[1] / 'EternalRebirth/SourceArt/Effects/H100'
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf8'))
(root / 'Meshes').mkdir(exist_ok=True)
for entry in manifest['source_effects']:
    model = JumpXHero((root / entry['file']).read_bytes())
    if not model.meshes:
        continue
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = .01
    objects = []
    slots = []
    for index, source in enumerate(model.meshes):
        mesh = bpy.data.meshes.new('EffectPart')
        mesh.from_pydata(source.positions.tolist(), [], source.faces.tolist())
        mesh.update()
        uv = mesh.uv_layers.new(name='UVMap')
        for loop in mesh.loops:
            x, y = source.uv[loop.vertex_index]
            uv.data[loop.index].uv = (float(x), 1-float(y))
        tid = model.materials[source.material]['texture'] if source.material < len(model.materials) else -1
        texture = Path(model.textures[tid].replace('\\', '/')).stem.lower() if 0 <= tid < len(model.textures) else 'neutral'
        mat = bpy.data.materials.get('FX_' + texture) or bpy.data.materials.new('FX_' + texture)
        mesh.materials.append(mat)
        obj = bpy.data.objects.new('Part_' + str(index), mesh)
        bpy.context.collection.objects.link(obj)
        obj.select_set(True)
        objects.append(obj)
        slots.append(texture)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = 'SM_' + entry['name']
    destination = root / 'Meshes' / (obj.name + '.fbx')
    bpy.ops.export_scene.fbx(filepath=str(destination), use_selection=True, object_types={'MESH'},
                            add_leaf_bones=False, bake_anim=False, axis_forward='-Y', axis_up='Z',
                            use_space_transform=True, mesh_smooth_type='FACE')
    entry['fbx'] = destination.relative_to(root).as_posix()
    entry['material_slots'] = slots
    print('H100_EFFECT_MESH', obj.name, len(obj.data.polygons), flush=True)
(root / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf8')
print('REBIRTH_H100_EFFECT_MESHES_COMPLETE', sum('fbx' in e for e in manifest['source_effects']), flush=True)
