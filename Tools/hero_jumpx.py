"""Read the mesh, skeleton and clip table from 300Hero JumpX v6 files.

Record sizes follow JumpXToolchain's MIT-licensed XUtil.h. The installed
client is read separately; this module only interprets bytes already loaded.
"""
from dataclasses import dataclass
import struct
import zlib
import numpy as np


@dataclass
class HeroMesh:
    name: str
    material: int
    flags: int
    positions: np.ndarray
    faces: np.ndarray
    uv: np.ndarray
    bone_ids: np.ndarray
    bone_weights: np.ndarray


@dataclass
class HeroBone:
    name: str
    parent: int
    frame_count: int
    inverse_bind: np.ndarray
    pos_offset: int
    rot_offset: int
    scale_offset: int


class JumpXHero:
    def __init__(self, raw: bytes):
        if not raw.startswith(b'JUMPX'):
            raise ValueError('Not a JumpX file')
        version, header_size = struct.unpack_from('<II', raw, 80)
        if version not in (6, 8) or header_size % 12:
            raise ValueError(f'Unsupported JumpX version/header: {version}/{header_size}')
        self.header = {
            raw[p:p + 4].decode('ascii'): struct.unpack_from('<I', raw, p + 8)[0]
            for p in range(88, 88 + header_size, 12)
        }
        p = 88 + header_size
        index_size, model_size, index_packed, model_packed = struct.unpack_from('<4I', raw, p)
        self.index = zlib.decompress(raw[p + 16:p + 16 + index_packed])
        self.model = zlib.decompress(raw[p + 16 + index_packed:p + 16 + index_packed + model_packed])
        if len(self.index) != index_size or len(self.model) != model_size:
            raise ValueError('Damaged JumpX payload')
        self.textures = self._textures()
        self.materials = self._materials()
        self.meshes = self._meshes()
        self.bones = self._bones()
        self.actions = self._actions()

    def string(self, offset):
        if offset >= len(self.index):
            raise ValueError(f'Bad string offset: {offset}')
        return self.index[offset:self.index.index(0, offset)].decode('gb18030', 'replace')

    def array(self, offset, dtype, count):
        if not offset:
            return None
        start = offset - 1000000000
        result = np.frombuffer(self.model, dtype=dtype, count=count, offset=start)
        if len(result) != count:
            raise ValueError('Truncated JumpX array')
        return result.copy()

    def _textures(self):
        h = self.header
        return [self.string(struct.unpack_from('<I', self.index, h['atex'] + i * 8 + 4)[0])
                for i in range(h['ntex'])]

    def _materials(self):
        h = self.header
        return [dict(flags=struct.unpack_from('<I', self.index, h['amtl'] + i * 48 + 8)[0],
                     texture=struct.unpack_from('<i', self.index, h['amtl'] + i * 48 + 12)[0])
                for i in range(h['nmtl'])]

    def _meshes(self):
        h = self.header
        meshes = []
        for i in range(h['ngeo']):
            g = h['ageo'] + i * 124
            name_offset, _, material, flags, _, vertex_count, face_count = struct.unpack_from('<7I', self.index, g + 8)
            if not vertex_count or not face_count:
                continue
            offsets = struct.unpack_from('<6Q', self.index, g + 36)
            positions = self.array(offsets[0], '<f4', vertex_count * 3).reshape(-1, 3)
            uv = self.array(offsets[2], '<f4', vertex_count * 2)
            uv = uv.reshape(-1, 2) if uv is not None else np.zeros((vertex_count, 2), dtype=np.float32)
            faces = self.array(offsets[5], '<u2', face_count * 3).reshape(-1, 3)
            if faces.max() >= vertex_count or not np.isfinite(positions).all():
                raise ValueError(f'Invalid geometry {i}')
            bone_offset = struct.unpack_from('<I', self.index, g + 92)[0]
            ids = np.zeros((vertex_count, 4), dtype=np.uint8)
            weights = np.zeros((vertex_count, 4), dtype=np.float32)
            if bone_offset:
                block = self.array(bone_offset, 'u1', vertex_count * 24).reshape(-1, 24)
                ids[:] = block[:, 1:5]
                weights[:] = np.frombuffer(block.tobytes(), dtype='<f4').reshape(-1, 6)[:, 2:6]
                counts = block[:, 0]
                weights[np.arange(4)[None, :] >= counts[:, None]] = 0
                weights[~np.isfinite(weights)] = 0
                weights = np.maximum(weights, 0)
                totals = weights.sum(axis=1)
                weights[totals > 0] /= totals[totals > 0, None]
            meshes.append(HeroMesh(self.string(name_offset), material, flags,
                                   positions, faces, uv, ids, weights))
        return meshes

    def _bones(self):
        h = self.header
        bones = []
        for i in range(h['nbon']):
            p = h['abon'] + i * 172
            name_offset, parent, frame_count = struct.unpack_from('<3I', self.index, p + 8)
            inverse_bind = np.frombuffer(self.index, dtype='<f4', count=16, offset=p + 24).reshape(4, 4).copy()
            pos_offset = struct.unpack_from('<I', self.index, p + 144)[0]
            rot_offset = struct.unpack_from('<I', self.index, p + 156)[0]
            scale_offset = struct.unpack_from('<I', self.index, p + 168)[0]
            bones.append(HeroBone(self.string(name_offset), -1 if parent == 0xffffffff else parent,
                                  frame_count, inverse_bind, pos_offset, rot_offset, scale_offset))
        return bones

    def _actions(self):
        h = self.header
        actions = []
        for i in range(h['nact']):
            p = h['aact'] + i * 90
            name = self.index[p:p + 80].split(b'\0')[0].decode('gb18030', 'replace')
            start, end = struct.unpack_from('<HH', self.index, p + 80)
            if start <= end:
                actions.append(dict(name=name, start=start, end=end))
        return actions

    def frames(self, bone, kind, start, end):
        offset, width = {'pos': (bone.pos_offset, 3), 'rot': (bone.rot_offset, 4),
                         'scale': (bone.scale_offset, 3)}[kind]
        if not offset:
            return None
        if end >= bone.frame_count:
            end = bone.frame_count - 1
        begin = offset - 1000000000 + start * width * 4
        return np.frombuffer(self.model, dtype='<f4', count=(end - start + 1) * width,
                             offset=begin).reshape(-1, width).copy()
