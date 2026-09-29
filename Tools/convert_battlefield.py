"""Run with Blender --background --python. Reconstructs the actual local map.
JumpX record layouts adapted from Gamepiaynmo/JumpXToolchain (MIT, 2023).
The upstream license is retained in Tools/JumpXToolchain/LICENSE.
"""
from pathlib import Path
import sys,struct,zlib,json,re,collections,math
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from inspect_client import extract
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'EternalRebirth/SourceArt'
OUT.mkdir(exist_ok=True)
(OUT/'Meshes').mkdir(exist_ok=True); (OUT/'Textures').mkdir(exist_ok=True)
inventory=json.loads((ROOT/'Research/client_inventory.json').read_text(encoding='utf8'))
byname=collections.defaultdict(list)
for entry in inventory:byname[entry['name'].replace('\\','/').split('/')[-1].lower()].append(entry)
layout=json.loads((ROOT/'Research/scene_layout.json').read_text())

def locate(name):
    candidates=byname.get(name.lower(),[])
    if not candidates:
        for ext in ('.dds','.tga','.png','.bmp'):
            candidates=byname.get(Path(name).stem.lower()+ext,[])
            if candidates:break
    if not candidates:raise FileNotFoundError(name)
    candidates.sort(key=lambda i:('lm4jjcmap' in i['name'].lower(),'sceneobjs' in i['name'].lower(),'textures' in i['name'].lower()),reverse=True)
    return extract(candidates[0])

def read_x(path):
    b=path.read_bytes();assert b.startswith(b'JUMPX')
    version,hs=struct.unpack_from('<II',b,80)
    h={b[p:p+4].decode():struct.unpack_from('<I',b,p+8)[0] for p in range(88,88+hs,12)}
    p=88+hs;isz,msz,ic,mc=struct.unpack_from('<4I',b,p)
    idx=zlib.decompress(b[p+16:p+16+ic]);mod=zlib.decompress(b[p+16+ic:p+16+ic+mc])
    assert len(idx)==isz and len(mod)==msz
    def string(p):return idx[p:idx.index(0,p)].decode('gb18030','replace')
    tex=[string(struct.unpack_from('<I',idx,h['atex']+i*8+4)[0]) for i in range(h['ntex'])]
    mats=[dict(tex=struct.unpack_from('<i',idx,h['amtl']+i*48+12)[0],flags=struct.unpack_from('<I',idx,h['amtl']+i*48+8)[0]) for i in range(h['nmtl'])]
    meshes=[]
    for i in range(h['ngeo']):
        g=h['ageo']+i*124
        nameoff,obj,mat,f0,f1,nv,nf=struct.unpack_from('<7I',idx,g+8)
        # JumpX types 4/5/9 are gameplay floor, collision and bounding proxies.
        # They overlap the visible terrain and must never enter the beauty pass.
        if f0 in (4,5,9):continue
        offsets=struct.unpack_from('<6Q',idx,g+36)
        if nv==0 or nf==0:continue
        def arr(off,dtype,count):
            off=(off-1000000000)&0xffffffff
            return np.frombuffer(mod,dtype=dtype,count=count,offset=off).copy()
        pos=arr(offsets[0],'<f4',nv*3).reshape(-1,3)
        uv=arr(offsets[2],'<f4',nv*2).reshape(-1,2) if offsets[2] else np.zeros((nv,2))
        faces=arr(offsets[5],'<u2',nf*3).reshape(-1,3)
        assert faces.max()<nv and np.all(np.isfinite(pos))
        m=mats[mat] if mat<len(mats) else {'tex':-1,'flags':0}
        texture=tex[m['tex']] if 0<=m['tex']<len(tex) else ''
        meshes.append(dict(name=string(nameoff),pos=pos,uv=uv,faces=faces,texture=texture,flags=m['flags']))
    return meshes

prior_path=OUT/'conversion_report.json'
textures=json.loads(prior_path.read_text()).get('textures',{}) if prior_path.exists() else {}
materials={}; report=dict(converted=[],excluded_helpers=[],missing=[],textures=[],origin=[164,164,0],scale=100)
def material(texture):
    key=re.sub(r'[^a-zA-Z0-9_]','_',Path(texture).stem.lower()) or 'neutral'
    if key in materials:return materials[key]
    mat=bpy.data.materials.new('M_'+key);mat.use_nodes=True
    if texture:
        try:
            if key in textures and (OUT/'Textures'/textures[key]['file']).exists():
                node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(OUT/'Textures'/textures[key]['file']),check_existing=True)
                mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
                if textures[key]['masked']:mat.node_tree.links.new(node.outputs['Alpha'],mat.node_tree.nodes.get('Principled BSDF').inputs['Alpha'])
                materials[key]=mat
                return mat
            source=locate(texture);image=bpy.data.images.load(str(source),check_existing=True)
            image.filepath_raw=str(OUT/'Textures'/('T_'+key+'.png'));image.file_format='PNG';image.save()
            node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
            mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
            pixels=np.array(image.pixels[:],dtype=np.float32).reshape(-1,4)
            masked=bool((pixels[:,3]<.5).mean()>.015)
            textures[key]=dict(file='T_'+key+'.png',original=texture,masked=masked,size=list(image.size))
        except Exception as e:report['missing'].append(dict(texture=texture,error=str(e)))
    materials[key]=mat;return mat

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=.01
cells=collections.defaultdict(list); bounds=[]; tri_count=0
for number,item in enumerate(layout):
    if item['group'] in ('sound','effect','wall'):continue
    try:
        name=item['name'];path=locate(name);meshes=read_x(path)
        if not meshes:
            report['excluded_helpers'].append(name)
            continue
        for m in meshes:
            vertices=m['pos']*np.array(item['scale'])*100+(np.array(item['loc'])-np.array([164,164,0]))*100
            # FBX exporter converts Blender Z-up into UE, keep geometry coordinates in centimeters.
            mesh=bpy.data.meshes.new('Mesh');mesh.from_pydata(vertices.tolist(),[],m['faces'].tolist());mesh.update()
            uv=mesh.uv_layers.new(name='UVMap')
            coords=m['uv'][m['faces'].ravel()].copy();coords[:,1]=1-coords[:,1]
            uv.data.foreach_set('uv',coords.ravel())
            ob=bpy.data.objects.new(Path(name).stem,mesh);bpy.context.collection.objects.link(ob)
            mesh.materials.append(material(m['texture']) if item['group']!='water' else material(''))
            for poly in mesh.polygons:poly.use_smooth=True
            cx=int((item['loc'][0]-70)//40);cy=int((item['loc'][1]-70)//40)
            cells[(cx,cy,item['group']=='water')].append(ob)
            bounds.append([vertices.min(axis=0).tolist(),vertices.max(axis=0).tolist()]);tri_count+=len(m['faces'])
        report['converted'].append(name)
    except Exception as e:report['missing'].append(dict(model=item['name'],error=str(e)))
    if number%50==0: print('CONVERT',number,len(layout),flush=True)

for cell,objects in cells.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join()
    joined=bpy.context.view_layer.objects.active
    # Collapse repeated slots after join. Keep one material section per texture.
    unique=[];mapping={}
    for i,mat in enumerate(joined.data.materials):
        if mat not in unique:unique.append(mat)
        mapping[i]=unique.index(mat)
    inds=[mapping[p.material_index] for p in joined.data.polygons]
    joined.data.materials.clear()
    for mat in unique:joined.data.materials.append(mat)
    for p,mi in zip(joined.data.polygons,inds):p.material_index=mi
    joined.name=('SM_Water' if cell[2] else 'SM_Arena')+'_%d_%d'%cell[:2]
    bpy.ops.export_scene.fbx(filepath=str(OUT/'Meshes'/(joined.name+'.fbx')),use_selection=True,object_types={'MESH'},mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_space_transform=True)
    print('EXPORTED',joined.name,len(joined.data.polygons),len(unique),flush=True)

report['textures']=textures;report['triangles']=tri_count;report['cells']=len(cells)
report['bounds']=[np.array(bounds)[:,0,:].min(axis=0).tolist(),np.array(bounds)[:,1,:].max(axis=0).tolist()]
(OUT/'conversion_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Arena_Reconstructed.blend'))
print('DONE',len(report['converted']),'models',tri_count,'triangles',len(report['missing']),'missing',report['bounds'],flush=True)
