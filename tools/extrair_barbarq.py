#!/usr/bin/env python3
"""Extrator específico do VISPACK do BarbarQ APK versão 1.0.1811.
Uso: python tools/extrair_barbarq.py caminho/para/barbarq.apk --out assets_original
Depende somente do Python 3 (stdlib). Não executa o APK.
"""
import argparse
import collections
import csv
import pathlib
import struct
import sys
import zipfile
import zlib

MAGIC = b"VISPACK\x00"
NAMES_BASE = 0x518
TABLE_OFFSET = 0x26F7C
TABLE_COUNT = 4839
ENTRY_SIZE = 24
MEMBER = "res/raw/asset.jet"


def get_records(data):
    if data[:8] != MAGIC:
        raise ValueError("Formato diferente: cabeçalho VISPACK ausente")
    start = TABLE_OFFSET + TABLE_COUNT * ENTRY_SIZE
    if data[start:start + 2] not in (b"\x78\xda", b"\x78\x9c", b"\x78\x01"):
        raise ValueError("Layout de pacote não compatível com a versão 1.0.1811")
    for idx in range(TABLE_COUNT):
        fname_offset, name_size, raw_size, stored_size, flags, offset = struct.unpack_from(
            "<6I", data, TABLE_OFFSET + idx * ENTRY_SIZE)
        if fname_offset == 0xffffffff:
            continue  # posição vazia da tabela hash
        pos = NAMES_BASE + fname_offset
        if not (0 < name_size < 512) or pos + name_size > TABLE_OFFSET:
            raise ValueError(f"Entrada #{idx}: nome fora do índice")
        if stored_size > len(data) or offset + stored_size > len(data) - start:
            raise ValueError(f"Entrada #{idx}: conteúdo fora do pacote")
        name = data[pos:pos + name_size].decode("utf-8")
        pp = pathlib.PurePosixPath(name)
        if pp.is_absolute() or ".." in pp.parts or ":" in name or "\\" in name:
            raise ValueError(f"Caminho não confiável: {name!r}")
        yield idx, name, raw_size, stored_size, flags, start + offset


def extract_record(data, record):
    idx, name, raw_size, stored_size, flags, absolute_offset = record
    if flags != 0:
        raise ValueError(f"Sinalizador desconhecido em {name}: {flags}")
    payload = data[absolute_offset:absolute_offset + stored_size]
    if stored_size < raw_size:
        try:
            contents = zlib.decompress(payload)
        except zlib.error as err:
            raise ValueError(f"Falha de descompressão em {name}: {err}") from err
    else:
        contents = payload
    if len(contents) != raw_size:
        raise ValueError(f"Tamanho incorreto em {name}: {len(contents)} != {raw_size}")
    return contents


def main():
    parser = argparse.ArgumentParser(description="Extrai recursos do BarbarQ 1.0.1811 (VISPACK)")
    parser.add_argument("apk", type=pathlib.Path, help="APK original, fornecido pelo usuário")
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("assets_original"))
    parser.add_argument("--ext", help="Apenas extensões especificadas; exemplo: png,jpg,tmx")
    args = parser.parse_args()
    extensions = set(x.lower().strip().lstrip(".") for x in args.ext.split(",")) if args.ext else None
    if not args.apk.is_file():
        parser.error(f"APK não encontrado: {args.apk}")
    with zipfile.ZipFile(args.apk) as zf:
        if MEMBER not in zf.namelist():
            parser.error("O APK não contém res/raw/asset.jet")
        print("Lendo VISPACK...")
        pack = zf.read(MEMBER)
    records = list(get_records(pack))
    print(f"Arquivos catalogados: {len(records)}")
    args.out.mkdir(parents=True, exist_ok=True)
    out_base = args.out.resolve()
    extracted = 0
    for i, record in enumerate(records):
        name = record[1]
        if extensions is not None and pathlib.PurePosixPath(name).suffix.lower().lstrip(".") not in extensions:
            continue
        out_file = (out_base / pathlib.PurePosixPath(name)).resolve()
        if out_file != out_base and out_base not in out_file.parents:
            raise ValueError(f"Caminho fora do destino: {name}")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_bytes(extract_record(pack, record))
        extracted += 1
        if extracted % 250 == 0:
            print(f"Extraídos {extracted} arquivos")
    print(f"Concluído: {extracted} arquivos em {out_base}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)