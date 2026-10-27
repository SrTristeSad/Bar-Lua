"""Leitor conservador de animações .bexportjson (FlatBuffers) do BarbarQ 1.0.1811.

Decodifica a hierarquia observada: arquivos -> armatures/bones/displays,
animations -> movements -> tracks -> keyframes. Os dados preservam posições,
escalas e campos de duração SEM declarar que renderização de Cocos é 1:1.
Nenhum dado binário é executado.
"""
from __future__ import annotations
from pathlib import Path
import math
from bplist import Buffer, BPlistError

class BExportError(BPlistError):
    pass

MAX_COLLECTION = 25000
MAX_BONES = 1024
MAX_FRAMES = 10000


def vector(reader: Buffer, table, field: int, kind: str) -> list:
    addr = table.addr(field)
    if addr is None:
        return []
    base = reader.deref(addr)
    count = reader.uint(base)
    if count > MAX_COLLECTION or base + 4 + 4 * count > reader.size:
        raise BExportError(f"Vetor inválido no campo {field}: {count}")
    result = []
    for i in range(count):
        slot = base + 4 + 4 * i
        if kind == 'table':
            result.append(reader.table(reader.deref(slot)))
        elif kind == 'string':
            result.append(reader.string(slot))
        else:
            raise BExportError(f"Tipo de vetor desconhecido: {kind}")
    return result


def clean_name(name: str, what: str) -> str:
    if not name or len(name) > 500 or '\x00' in name:
        raise BExportError(f"Nome de {what} inválido")
    return name


def _parse_bytes(data: bytes, *, include_frames: bool = False) -> dict:
    r = Buffer(data)
    if r.size < 50 or r.size > 16 * 1024 * 1024:
        raise BExportError(f"Tamanho .bexportjson fora de faixa: {r.size}")
    root = r.table(r.uint(0))
    version = root.uint(0)
    if version != 2:
        raise BExportError(f"Versão não suportada: {version}")
    armatures = []
    for arm in vector(r, root, 2, 'table'):
        bones = []
        for bone in vector(r, arm, 3, 'table'):
            displays = []
            for display in vector(r, bone, 14, 'table'):
                name = display.string(0)
                # Preservar posições vazias impede deslocar os índices.
                displays.append(clean_name(name, 'imagem') if name else '')
            # bone[2]: display inicial; bone[5]: ordem de camada.
            # Campos 3-4 e 6-9: posição, escala e skew da pose base.
            bind = {'x': bone.float(3), 'y': bone.float(4),
                    'scale_x': bone.float(6, 1.0), 'scale_y': bone.float(7, 1.0),
                    'skew_x': bone.float(8), 'skew_y': bone.float(9)}
            if not all(math.isfinite(v) for v in bind.values()):
                raise BExportError('Transformação de osso não finita')
            initial = r.int(bone.addr(2)) if bone.addr(2) is not None else 0
            if initial < -1 or initial >= len(displays):
                raise BExportError('Display inicial fora da lista de imagens')
            order = r.int(bone.addr(5)) if bone.addr(5) is not None else 0
            bones.append({'name': clean_name(bone.string(0), 'osso'),
                          'parent': bone.string(1), 'displays': displays,
                          'initial_display': initial, 'layer_order': order,
                          'bind': bind})
        if len(bones) > MAX_BONES:
            raise BExportError("Armadura com ossos demais")
        armatures.append({'name': clean_name(arm.string(2), 'armadura'), 'bones': bones,
                          'format_version': arm.string(0)})
    animations = []
    for anim in vector(r, root, 3, 'table'):
        movements = []
        for move in vector(r, anim, 1, 'table'):
            duration = move.uint(1)
            if duration > 100000:
                raise BExportError(f"Duração excessiva: {duration}")
            tracks = []
            for track in vector(r, move, 7, 'table'):
                frames = vector(r, track, 2, 'table')
                if len(frames) > MAX_FRAMES:
                    raise BExportError("Trilha com quadros demais")
                keys = []
                for frame in frames:
                    at = frame.uint(8)
                    if at > 1000000:
                        raise BExportError("Índice de keyframe inválido")
                    # frame[0] é o display ZERO-BASED (-1 = oculto),
                    # validado nos 38.727 keyframes do APK. f1/f2: posição,
                    # f4/f5: escala, f6/f7: skew. O campo 11 é indeterminado.
                    if include_frames:
                        display_index = r.int(frame.addr(0)) if frame.addr(0) is not None else 0
                        key = {'at': at, 'display_index': display_index,
                               'x': frame.float(1), 'y': frame.float(2),
                               'scale_x': frame.float(4, 1.0), 'scale_y': frame.float(5, 1.0),
                               'skew_x': frame.float(6), 'skew_y': frame.float(7)}
                        if not all(math.isfinite(v) for k, v in key.items() if k != 'at'):
                            raise BExportError('Transformação de keyframe não finita')
                        keys.append(key)
                tracks.append({'bone': clean_name(track.string(0), 'trilha'),
                               'key_count': len(frames), 'keys': keys})
            movements.append({'name': clean_name(move.string(0), 'movimento'),
                              'duration': duration, 'tracks': tracks})
        animations.append({'name': clean_name(anim.string(0), 'animação'), 'movements': movements})
    # Proteção contra arquivos malformados que referenciem textura inexistente.
    for armature in armatures:
        by_name = {bone['name']: bone for bone in armature['bones']}
        for animation in animations:
            for movement in animation['movements']:
                for track in movement['tracks']:
                    bone = by_name.get(track['bone'])
                    if bone is None:
                        continue
                    for key in track['keys']:
                        i = key['display_index']
                        if i < -1 or i >= len(bone['displays']):
                            raise BExportError(f"Display {i} inválido em {track['bone']}")
    sprites = []
    for texture in vector(r, root, 4, 'table'):
        name = texture.string(0)
        if name:
            sprites.append(clean_name(name, 'sprite'))
    return {'version': version, 'armatures': armatures, 'animations': animations,
            'sprites': sprites, 'atlas_files': vector(r, root, 5, 'string'),
            'texture_files': vector(r, root, 6, 'string')}


def parse_bytes(data: bytes, *, include_frames: bool = False) -> dict:
    try:
        return _parse_bytes(data, include_frames=include_frames)
    except BExportError:
        raise
    except BPlistError as exc:
        raise BExportError(str(exc)) from exc


def parse_file(path: Path, *, include_frames: bool = False) -> dict:
    return parse_bytes(Path(path).read_bytes(), include_frames=include_frames)