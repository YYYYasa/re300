from pathlib import Path
import struct,zlib,collections,json
R=Path('G:/Code/UE/Research/Extracted/data/sceneobjs/lm4jjcmap')
counts=collections.Counter()
for file in R.glob('*.x'):
 b=file.read_bytes()
 if not b.startswith(b'JUMPX'):continue
 ver,hs=struct.unpack_from('<II',b,80)
 h={b[p:p+4].decode():struct.unpack_from('<I',b,p+8)[0] for p in range(88,88+hs,12)}
 p=88+hs;isz,msz,ic,mc=struct.unpack_from('<4I',b,p)
 idx=zlib.decompress(b[p+16:p+16+ic])
 def string(p):return idx[p:idx.index(0,p)].decode('gb18030','replace')
 for i in range(h['ngeo']):
  g=h['ageo']+i*124
  nameoff,obj,mat,kind,flag,nv,nf=struct.unpack_from('<7I',idx,g+8)
  counts[kind]+=1
  if kind==4 or file.name=='2005_sterrain4_5.x':print(file.name,string(nameoff),'type',kind,'material',mat,'vertices',nv,'faces',nf)
print('TYPE COUNTS',counts)
