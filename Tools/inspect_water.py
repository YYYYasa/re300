"""Read-only measurements for the reconstructed river geometry and rendering."""
import unreal as u

level = u.get_editor_subsystem(u.LevelEditorSubsystem)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
if not level.load_level('/Game/Maps/EternalShowcase'):
    raise RuntimeError('Showcase map missing')
for actor in actors.get_all_level_actors():
    if not actor.get_actor_label().startswith('SM_Water'):
        continue
    component = actor.static_mesh_component
    origin, extent, radius = u.SystemLibrary.get_component_bounds(component)
    mesh = component.get_editor_property('static_mesh')
    triangles = mesh.get_num_triangles(0) if hasattr(mesh, 'get_num_triangles') else -1
    materials = [str(slot.material_interface.get_path_name())
                 for slot in mesh.get_editor_property('static_materials')]
    u.log('REBIRTH: WATER_GEOMETRY %s origin=%s extent=%s radius=%.1f vertices=%d scale=%s materials=%s' %
          (actor.get_actor_label(), origin, extent, radius,
           triangles, actor.get_actor_scale3d(), materials))
