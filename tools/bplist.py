"""Leitor estrito dos atlas FlatBuffers .bplist encontrados no BarbarQ 1.0.1811.

Não depende de schemas gerados nem de pacotes externos. Decodifica SOMENTE as
estruturas de atlas empiricamente confirmadas, e falha em formatos inesperados.
Os dois esquemas observados têm frames com geometria numérica (campos 1-8)
ou retângulos representados por strings (campos 9, 11-13).
"""
from __future__ import annotations

import re
import struct
from pathlib import Path

_VECTOR = re.compile(r"-?\d+(?:\.\d+)?")
_MAX_FRAMES = 20000


class BPlistError(ValueError):
    """Atlas FlatBuffers inválido ou formato não suportado."""


class Buffer:
    def __init__(self, data: bytes):
        self.data = data
        self.size = len(data)

    def get(self, fmt: str, offset: int):
        size = struct.calcsize(fmt)
        if offset < 0 or offset + size > self.size:
            raise BPlistError(f"Leitura fora do arquivo em {offset} ({size} bytes)")
        return struct.unpack_from(fmt, self.data, offset)[0]

    def uint(self, pos):
        return self.get("<I", pos)

    def int(self, pos):
        return self.get("<i", pos)

    def short(self, pos):
        return self.get("<H", pos)

    def float(self, pos):
        return self.get("<f", pos)

    def table(self, pos):
        if pos < 4 or pos >= self.size:
            raise BPlistError(f"Tabela fora do arquivo: {pos}")
        vt = pos - self.int(pos)
        vsize = self.short(vt)
        object_size = self.short(vt + 2)
        if vsize < 4 or vsize % 2 or vsize > 256 or object_size < 4:
            raise BPlistError(f"Vtable inválida na posição {vt}")
        if vt + vsize > self.size or pos + object_size > self.size:
            raise BPlistError("Tabela FlatBuffers truncada")
        return Table(self, pos, vt, vsize)

    def deref(self, pos):
        displacement = self.uint(pos)
        target = pos + displacement
        if displacement == 0 or target >= self.size:
            raise BPlistError(f"Ponteiro inválido: {pos} + {displacement}")
        return target

    def string(self, pos):
        target = self.deref(pos)
        length = self.uint(target)
        if length > 2048 or target + 4 + length >= self.size:
            raise BPlistError("String inválida / truncada")
        if self.data[target + 4 + length] != 0:
            raise BPlistError("String sem terminador NUL")
        try:
            return self.data[target + 4:target + 4 + length].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BPlistError("String não UTF-8") from exc


class Table:
    def __init__(self, reader: Buffer, pos: int, vt: int, vsize: int):
        self.r, self.pos, self.vt, self.vsize = reader, pos, vt, vsize

    def addr(self, index: int):
        offset = 4 + 2 * index
        if offset >= self.vsize:
            return None
        field = self.r.short(self.vt + offset)
        return self.pos + field if field else None

    def string(self, index: int, default=""):
        pos = self.addr(index)
        return self.r.string(pos) if pos is not None else default

    def float(self, index: int, default=0):
        pos = self.addr(index)
        return self.r.float(pos) if pos is not None else default

    def uint(self, index: int, default=0):
        pos = self.addr(index)
        return self.r.uint(pos) if pos is not None else default

    def nested(self, index: int):
        pos = self.addr(index)
        return self.r.table(self.r.deref(pos)) if pos is not None else None

    def vector_tables(self, index: int):
        field = self.addr(index)
        if field is None:
            raise BPlistError("Vetor de quadros ausente")
        start = self.r.deref(field)
        count = self.r.uint(start)
        if count > _MAX_FRAMES or start + 4 + count * 4 > self.r.size:
            raise BPlistError(f"Vetor de quadros inválido: {count}")
        for i in range(count):
            slot = start + 4 + 4 * i
            yield self.r.table(self.r.deref(slot))


def _coords(s: str, expected: int):
    nums = [float(x) for x in _VECTOR.findall(s)]
    if len(nums) != expected:
        raise BPlistError(f"Geometria inesperada: {s!r}")
    return nums


def _number(n: float) -> int:
    if not 0 <= n <= 65536 or n != round(n):
        raise BPlistError(f"Coordenada fora de faixa / fracionária: {n}")
    return int(n)


def decode_bytes(data: bytes) -> dict:
    r = Buffer(data)
    if r.size < 36:
        raise BPlistError("Atlas muito pequeno")
    root = r.table(r.uint(0))
    version = root.uint(0)
    if version != 2:
        raise BPlistError(f"Versão de atlas não suportada: {version}")
    meta = root.nested(2)
    if meta is None:
        raise BPlistError("Metadados do atlas ausentes")
    texture = meta.string(1) or meta.string(2)
    # Nas tabelas da versão original, metadata[3] é o tamanho da textura.
    image_size = _coords(meta.string(3), 2) if meta.string(3) else [0, 0]
    frames = []
    for frame in root.vector_tables(1):
        name = frame.string(0)
        if not name:
            raise BPlistError("Sprite sem nome")
        if frame.addr(9) is not None:
            x, y, w, h = _coords(frame.string(9), 4)
            sx, sy, sw, sh = _coords(frame.string(12), 4)
            source_w, source_h = _coords(frame.string(13), 2)
            ox, oy = _coords(frame.string(11), 2)
            rotated = frame.uint(10) != 0
        else:
            x, y, w, h = [frame.float(i) for i in (1, 2, 3, 4)]
            ox, oy = frame.float(5), frame.float(6)
            source_w, source_h = frame.uint(7), frame.uint(8)
            # Conteúdo recortado: tamanho do trim pode ser inferido da dimensão do frame.
            sx, sy, sw, sh = 0, 0, w, h
            rotated = False
        x, y, w, h = [_number(v) for v in (x, y, w, h)]
        source_w, source_h = [_number(v) for v in (source_w, source_h)]
        if w <= 0 or h <= 0:
            raise BPlistError(f"Sprite {name!r} de tamanho zero")
        if not (source_w and source_h):
            # Vários registros do arquivo compactado usam origem sem margens.
            source_w, source_h = w, h
        frames.append({
            "name": name, "x": x, "y": y, "w": w, "h": h,
            "rotated": rotated, "source_w": source_w, "source_h": source_h,
            "offset_x": ox, "offset_y": oy,
            "trim_x": sx, "trim_y": sy,
        })
    if not texture:
        raise BPlistError("Nome da textura ausente")
    return {"texture": texture, "size": [_number(n) for n in image_size], "frames": frames}


def decode_file(path: Path) -> dict:
    return decode_bytes(Path(path).read_bytes())