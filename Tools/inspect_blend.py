import bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='G:/Code/UE/EternalRebirth/SourceArt/Arena_Reconstructed.blend')
for name in ['M_stex_sterrain4_4','M_stex_cl_01','M_neutral']:
    m=bpy.data.materials.get(name)
    print('MATERIAL',name,[(n.type,n.image.filepath if n.type=='TEX_IMAGE' and n.image else '') for n in m.node_tree.nodes],[(l.from_node.name,l.to_socket.name) for l in m.node_tree.links])
for xy in [(0,0),(1000,1000),(-3000,-3000),(4000,4000),(0,4000)]:
    hit,loc,norm,face,obj,mat=bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector((*xy,40000)),Vector((0,0,-1)))
    if hit: print('HIT',xy,loc[:],obj.name,obj.data.polygons[face].material_index,obj.data.materials[obj.data.polygons[face].material_index].name)
