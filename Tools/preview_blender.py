import bpy,math
from mathutils import Vector
from pathlib import Path
R=Path('G:/Code/UE')
bpy.ops.wm.open_mainfile(filepath=str(R/'EternalRebirth/SourceArt/Arena_Reconstructed.blend'))
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.world.color=(.3,.3,.3)
bpy.ops.object.light_add(type='SUN',location=(0,0,15000));sun=bpy.context.object;sun.data.energy=2;sun.rotation_euler=(.35,-.45,-.5)
bpy.ops.object.camera_add(location=(0,0,40000));cam=bpy.context.object;cam.rotation_euler=(0,0,0);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=23000;cam.data.clip_end=100000
scene.camera=cam;scene.render.filepath=str(R/'Research/map_topdown.png')
bpy.ops.render.render(write_still=True)
