from pathlib import Path
import json,struct,sys
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[1]/'Research'
def vi(b,p):
    v=0;s=0
    while True:
        x=b[p];p+=1;v|=(x&127)<<s
        if not x&128:return v,p
        s+=7
def proto(b):
    p=0;ret=[]
    while p<len(b):
        t,p=vi(b,p);w=t&7;k=t>>3
        if w==0:v,p=vi(b,p)
        elif w==2:n,p=vi(b,p);v=b[p:p+n];p+=n
        elif w==5:v=struct.unpack_from('<f',b,p)[0];p+=4
        elif w==1:v=b[p:p+8];p+=8
        else:raise ValueError(w)
        ret.append((k,v))
    return ret
b=(R/'Extracted/excel/worldmapcfg_c.dat').read_bytes()
records=[]
for k,v in proto(b):
    f=dict(proto(v)); row={str(k):(v.decode('gb18030','replace') if isinstance(v,bytes) else v) for k,v in f.items()};records.append(row)
    print({k:row[k] for k in ['1','2','3','20','21','28'] if k in row})
(R/'map_records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
