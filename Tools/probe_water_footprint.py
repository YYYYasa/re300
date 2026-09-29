"""Find camera positions above source water triangles (source FBX Y is mirrored)."""
from pathlib import Path
import numpy as np
import struct
import zlib


def fbx_array(data, name):
    at=data.find(bytes([len(name)])+name.encode())+len(name)+1
    typ=chr(data[at]); count,encoded,size=struct.unpack_from('<III',data,at+1)
    raw=data[at+13:at+13+size]
    if encoded: raw=zlib.decompress(raw)
    return np.frombuffer(raw, dtype={'d':'<f8','i':'<i4'}[typ], count=count)


triangles=[]
for path in Path('EternalRebirth/SourceArt/Meshes').glob('SM_Water*.fbx'):
    data=path.read_bytes()
    vertices=fbx_array(data,'Vertices').reshape(-1,3).copy()
    vertices[:,1]*=-1
    polygon=[]
    for raw in fbx_array(data,'PolygonVertexIndex'):
        polygon.append(int(raw if raw>=0 else -raw-1))
        if raw<0:
            for index in range(1,len(polygon)-1):
                triangles.append((path.stem,vertices[[polygon[0],polygon[index],polygon[index+1]]]))
            polygon=[]


def hit(point, triangle):
    p=np.asarray(point,dtype=float)
    a,b,c=triangle[:,:2]
    cross=lambda u,v:u[0]*v[1]-u[1]*v[0]
    total=cross(b-a,c-a)
    if abs(total)<1e-5:return False
    u=cross(b-p,c-p)/total
    v=cross(c-p,a-p)/total
    w=cross(a-p,b-p)/total
    return min(u,v,w)>=-1e-7


for y in [4500,4000,3500,3000,2500,2000,1500,1000,500,0]:
    row=[]
    for x in [500,1000,1500,2000,2500,3000,3500,4000,4500]:
        name=next((name for name,triangle in triangles if hit((x,y),triangle)),None)
        row.append('W' if name else '.')
    print(y,''.join(row))
