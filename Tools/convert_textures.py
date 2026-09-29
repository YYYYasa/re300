from pathlib import Path
import json,re,sys
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1]
P=R/'EternalRebirth/SourceArt'
report=json.loads((P/'conversion_report.json').read_text(encoding='utf8'))
files={p.stem.lower():p for p in (R/'Research/Extracted/data/sceneobjs/textures').rglob('*') if p.is_file()}
textures={}
for i,item in enumerate(report['missing']):
    if 'texture' not in item:continue
    stem=Path(item['texture']).stem.lower();key=re.sub(r'[^a-zA-Z0-9_]','_',stem)
    src=files[stem];im=Image.open(src).convert('RGBA');pixels=np.asarray(im)
    dst=P/'Textures'/('T_'+key+'.png');im.save(dst)
    textures[key]=dict(file=dst.name,original=item['texture'],masked=bool((pixels[:,:,3]<128).mean()>.015),size=list(im.size))
    if i%25==0:print('TEXTURES',i,flush=True)
report['textures']=textures
report['missing']=[i for i in report['missing'] if 'texture' not in i]
(P/'conversion_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('DONE',len(textures),'textures')
