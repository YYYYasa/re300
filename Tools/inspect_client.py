"""Read-only JMP inventory/extraction. Never writes to the installed game.
Format reference: Anran-233/300ResourceBrowser (Unlicense), define/cpatch.cpp.
"""
from pathlib import Path
import struct, zlib, json, collections, argparse, re

ROOT = Path(__file__).resolve().parents[1]
CLIENT = Path(r'D:\JumpGame\300Hero')

def inventory():
    items = []
    for p in sorted(CLIENT.glob('Data*.jmp')):
        with p.open('rb') as f:
            if f.read(7) != b'DATA1.0' or p.stat().st_size < 54: continue
            f.seek(50)
            count, = struct.unpack('<I', f.read(4))
            assert count < 100000
            for i in range(count):
                raw = f.read(304)
                name = raw[:260].split(b'\0')[0].decode('gb18030', errors='replace')
                offset, packed, size = struct.unpack_from('<IIi', raw, 260)
                if not name or name == '..\\': continue
                if offset + packed > p.stat().st_size: continue
                items.append(dict(archive=p.name, name=name, offset=offset, packed=packed, size=size))
    return items

def data(item):
    with (CLIENT / item['archive']).open('rb') as f:
        f.seek(item['offset']); b = f.read(item['packed'])
    b = zlib.decompress(b) if item['size'] > 0 else b
    if item['size'] > 0: assert len(b) == item['size'], item['name']
    return b

def extract(item):
    parts = [p for p in item['name'].replace('\\','/').split('/') if p not in ('','..','.')]
    dest = ROOT / 'Research' / 'Extracted'
    target = dest.joinpath(*parts).resolve()
    if not target.is_relative_to(dest.resolve()): raise ValueError('unsafe path')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data(item))
    return target

if __name__ == '__main__':
    a=argparse.ArgumentParser(); a.add_argument('--extract'); args=a.parse_args()
    items=inventory()
    (ROOT/'Research'/'client_inventory.json').write_text(json.dumps(items,ensure_ascii=False,indent=1),encoding='utf-8')
    print('Entries:', len(items))
    print('Extensions:',collections.Counter(Path(i['name']).suffix.lower() for i in items).most_common(25))
    chosen=[i for i in items if re.search(args.extract or r'(?i)(map|scene|terrain|minimap)',i['name'])]
    print('Matches:',len(chosen))
    for i in chosen[:150]: print(i['name'],i['size'])
    if args.extract:
        for i in chosen: extract(i)
        print('Extracted:',len(chosen))
