"""Create an original distant mountain ring around the reconstructed arena."""
import bpy,math
from pathlib import Path
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
n=193;extent=65000;verts=[];faces=[]
peaks=[(-32000,-24000,7700,9000),(24000,-29000,8900,10000),(33000,-11000,6800,8000),(-30000,13000,8200,11000),(18000,31000,6400,9000),(-11000,-34000,6800,10000),(-2000,36000,8300,11000)]
for y in range(n):
 for x in range(n):
  px=(x/(n-1)*2-1)*extent;py=(y/(n-1)*2-1)*extent
  radius=math.sqrt(px*px+py*py);fade=max(0,min(1,(radius-14500)/8000))
  hills=sum(h*math.exp(-((px-cx)**2+(py-cy)**2)/(width*width)) for cx,cy,h,width in peaks)
  ridges=abs(math.sin(px*.00029+math.cos(py*.00019)))*900+math.sin(py*.00057+px*.00031)*300
  z=-2200+fade*(hills+ridges)
  verts.append((px,py,z))
for y in range(n-1):
 for x in range(n-1):
  a=y*n+x;faces.extend([(a,a+1,a+n+1),(a,a+n+1,a+n)])
m=bpy.data.meshes.new('DistantHighlands');m.from_pydata(verts,[],faces);m.update()
obj=bpy.data.objects.new('SM_DistantHighlands',m);bpy.context.collection.objects.link(obj)
for poly in m.polygons:poly.use_smooth=True
obj.select_set(True);bpy.context.view_layer.objects.active=obj
folder=Path('G:/Code/UE/EternalRebirth/SourceArt/Environment');folder.mkdir(exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(folder/'SM_DistantHighlands.fbx'),use_selection=True,object_types={'MESH'},mesh_smooth_type='FACE',bake_anim=False,axis_forward='-Y',axis_up='Z')
print('ENVIRONMENT_COMPLETE',len(faces),flush=True)
