import json
from pathlib import Path
import numpy as np
from inspect_client import data
from hero_jumpx import JumpXHero

root=Path(__file__).resolve().parents[1]
inventory=json.loads((root/'Research/client_inventory.json').read_text(encoding='utf8'))
layout=json.loads((root/'Research/scene_layout.json').read_text(encoding='utf8'))
tris=[]
for scene in layout:
    if not scene['name'].lower().startswith('floor'): continue
    candidates=[i for i in inventory if Path(i['name'].replace('\\','/')).name.lower()==scene['name'].lower()]
    item=next((i for i in candidates if '/lm4jjcmap/' in i['name'].lower()),candidates[0])
    for mesh in JumpXHero(data(item)).meshes:
        if mesh.flags!=4: continue
        p=mesh.positions*np.array(scene['scale'])*100+(np.array(scene['loc'])-[164,164,0])*100
        tris.extend(p[mesh.faces].tolist())
tris=np.array(tris)
for x,y in [(980,-1100),(1190,-1100),(2400,-1800),(980,1100),(2400,1800),(0,0)]:
    a,b,c=tris[:,0,:2],tris[:,1,:2],tris[:,2,:2]
    def cross(v,w): return v[:,0]*w[:,1]-v[:,1]*w[:,0]
    den=cross(b-a,c-a)
    with np.errstate(divide='ignore',invalid='ignore'):
        v=cross(np.array([x,y])-a,c-a)/den
        w=cross(b-a,np.array([x,y])-a)/den
    mask=(v>=0)&(w>=0)&(v+w<=1)&(abs(den)>.001)
    print(x,y,'hits',int(mask.sum()),'height',tris[mask,:,2].mean(axis=1).tolist())
