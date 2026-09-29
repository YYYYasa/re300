"""Read-only FBX array probe for the water source meshes (FBX binary 7400)."""
from pathlib import Path
import struct
import zlib
import numpy as np


def array(data, name):
    key = bytes([len(name)]) + name.encode('ascii')
    at = data.find(key)
    if at < 0:
        return None
    at += len(key)
    typ = chr(data[at])
    length, encoding, byte_count = struct.unpack_from('<III', data, at + 1)
    raw = data[at+13:at+13+byte_count]
    if encoding:
        raw = zlib.decompress(raw)
    return np.frombuffer(raw, dtype={'d':'<f8','f':'<f4','i':'<i4'}[typ], count=length)


for path in sorted(Path('EternalRebirth/SourceArt/Meshes').glob('SM_Water*.fbx')):
    data = path.read_bytes()
    vertices = array(data, 'Vertices').reshape(-1, 3)
    indices = array(data, 'PolygonVertexIndex')
    faces = []
    face = []
    for raw in indices:
        face.append(int(raw if raw >= 0 else -raw - 1))
        if raw < 0:
            faces.append(face)
            face = []
    cross_z = []
    for face in faces:
        if len(face) < 3:
            continue
        a,b,c = vertices[face[:3]]
        cross_z.append(float(np.cross(b-a,c-a)[2]))
    uv = array(data, 'UV')
    normals = array(data, 'Normals')
    print(path.name, 'vertices', len(vertices), 'faces', len(faces),
          'z-range', np.unique(np.round(vertices[:,2],2))[:20],
          'face-normal-z', (min(cross_z), max(cross_z)),
          'uv-range', None if uv is None else (uv.min(), uv.max()),
          'normal-z', None if normals is None else np.unique(np.round(normals.reshape(-1,3)[:,2],2))[:10])
