"""Run with Blender --background --python to export skinned hero FBX files."""
from pathlib import Path, PureWindowsPath
import json
import re
import sys
import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from hero_jumpx import JumpXHero

ART = ROOT / 'EternalRebirth' / 'SourceArt' / 'Heroes'


def safe_name(value):
    clean = re.sub(r'[^A-Za-z0-9_]+', '_', value)
    return clean[:50] or 'Part'


def visible_meshes(hero_id, model):
    result = []
    for mesh in model.meshes:
        if mesh.flags:
            continue
        if mesh.material >= len(model.materials):
            continue
        texture_id = model.materials[mesh.material]['texture']
        if not 0 <= texture_id < len(model.textures):
            continue
        texture = PureWindowsPath(model.textures[texture_id]).stem.lower()
        if texture == hero_id or texture.startswith(hero_id + '_'):
            result.append((mesh, texture_id))
    return result


def convert(hero_id):
    folder = ART / hero_id
    model = JumpXHero((folder / (hero_id + '.x')).read_bytes())
    info = json.loads((folder / 'source.json').read_text(encoding='utf8'))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = .01

    arm_data = bpy.data.armatures.new('SK_H' + hero_id)
    arm = bpy.data.objects.new('SK_H' + hero_id, arm_data)
    scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    edit = []
    rest = []
    for index, bone in enumerate(model.bones):
        world = Matrix(bone.inverse_bind.tolist()).inverted().transposed()
        matrix = world.to_quaternion().to_matrix().to_4x4()
        matrix.translation = world.translation
        rest.append(matrix)
        edit_bone = arm_data.edit_bones.new(safe_name(bone.name) or f'Bone{index}')
        edit_bone.matrix = matrix
        edit_bone.length = 3.0
        edit.append(edit_bone)
    for index, bone in enumerate(model.bones):
        if 0 <= bone.parent < len(edit) and bone.parent != index:
            edit[index].parent = edit[bone.parent]
            edit[index].use_connect = False
    bone_names = [bone.name for bone in edit]
    bpy.ops.object.mode_set(mode='OBJECT')
    (folder / 'rig.json').write_text(json.dumps({'bone_names': bone_names}, ensure_ascii=False, indent=2),
                                     encoding='utf8')
    arm.select_set(False)

    materials = {}
    objects = []
    for part, (mesh, texture_id) in enumerate(visible_meshes(hero_id, model)):
        source_texture = model.textures[texture_id]
        texture_info = info['textures'].get(source_texture)
        if not texture_info:
            raise FileNotFoundError(f'{hero_id}: {source_texture}')
        if texture_id not in materials:
            material = bpy.data.materials.new('M_H' + hero_id + '_' + safe_name(PureWindowsPath(source_texture).stem))
            material.use_nodes = True
            image = bpy.data.images.load(str(folder / texture_info['file']), check_existing=True)
            texture_node = material.node_tree.nodes.new('ShaderNodeTexImage')
            texture_node.image = image
            shader = material.node_tree.nodes.get('Principled BSDF')
            material.node_tree.links.new(texture_node.outputs['Color'], shader.inputs['Base Color'])
            materials[texture_id] = material
        vertices = mesh.positions.tolist()
        faces = mesh.faces.tolist()
        mesh_data = bpy.data.meshes.new(f'H{hero_id}_Part{part:02d}')
        mesh_data.from_pydata(vertices, [], faces)
        mesh_data.update()
        uv_layer = mesh_data.uv_layers.new(name='UVMap')
        for loop in mesh_data.loops:
            u, v = mesh.uv[loop.vertex_index]
            uv_layer.data[loop.index].uv = (float(u), float(1 - v))
        mesh_data.materials.append(materials[texture_id])
        obj = bpy.data.objects.new(f'H{hero_id}_Part{part:02d}', mesh_data)
        scene.collection.objects.link(obj)
        groups = [obj.vertex_groups.new(name=name) for name in bone_names]
        assigned = 0
        for vertex_index in range(len(mesh.positions)):
            for slot in range(4):
                weight = float(mesh.bone_weights[vertex_index, slot])
                bone_id = int(mesh.bone_ids[vertex_index, slot])
                if weight > .0001 and bone_id < len(groups):
                    groups[bone_id].add([vertex_index], weight, 'REPLACE')
                    assigned += 1
        obj.parent = arm
        modifier = obj.modifiers.new('Skin', 'ARMATURE')
        modifier.object = arm
        objects.append(obj)
        print('HERO_PART', hero_id, obj.name, len(vertices), len(faces), 'weights', assigned, flush=True)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = arm
    destination = folder / ('SK_H' + hero_id + '.fbx')
    bpy.ops.export_scene.fbx(filepath=str(destination), use_selection=True,
                             object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=False, axis_forward='-Y', axis_up='Z',
                             use_space_transform=True, apply_unit_scale=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder / ('H' + hero_id + '.blend')))
    print('HERO_CONVERTED', hero_id, 'parts', len(objects), 'bones', len(model.bones),
          'fbx', destination.stat().st_size, flush=True)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['013', '100', '101']
    for selected in args:
        convert(selected)
