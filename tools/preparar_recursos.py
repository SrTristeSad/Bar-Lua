#!/usr/bin/env python3
"""Converte dados de mapas TMX e atlas XML plist do BarbarQ 1.0.1811
para tabelas Lua locais. Não redistribui arquivos originais.
Uso: python tools/preparar_recursos.py --assets assets_original --out cache
"""
from __future__ import annotations
import argparse
import base64
from collections import Counter
import json
from pathlib import Path
import plistlib
import re
import struct
import xml.etree.ElementTree as ET
import zlib

try:
    from bplist import BPlistError, decode_file
except ModuleNotFoundError:
    # Carregamento por importlib.spec_from_file_location em testes externos.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from bplist import BPlistError, decode_file

NUMBERS = re.compile(r"-?\d+")


def numvec(value: str, count: int) -> list[int]:
    nums = [int(v) for v in NUMBERS.findall(value)]
    if len(nums) != count:
        raise ValueError(f"Vetor com {len(nums)} números, esperados {count}: {value}")
    return nums


def lua(obj) -> str:
    if obj is None:
        return "nil"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, str):
        # Lua 5.1 entende string literal com escapes decimais para UTF-8.
        parts = ['"']
        for b in obj.encode("utf-8"):
            if b in (34, 92):
                parts.append("\\" + chr(b))
            elif b == 10:
                parts.append("\\n")
            elif b == 13:
                parts.append("\\r")
            elif b == 9:
                parts.append("\\t")
            elif b < 32 or b > 126:
                parts.append(f"\\{b:03d}")
            else:
                parts.append(chr(b))
        return "".join(parts) + '"'
    if isinstance(obj, (int, float)):
        return str(obj)
    if isinstance(obj, list):
        return "{" + ",".join(lua(x) for x in obj) + "}"
    if isinstance(obj, dict):
        return "{" + ",".join("[" + lua(str(k)) + "]=" + lua(v) for k, v in obj.items()) + "}"
    raise TypeError(type(obj))


def locate(root: Path, relative: str) -> Path:
    """Resolve nomes de assets ignorando diferença de capitalização Android/Windows."""
    cur = root
    for item in relative.replace("\\", "/").split("/"):
        if item in ("", "."):
            continue
        if item == "..":
            cur = cur.parent
            continue
        nxt = cur / item
        if not nxt.exists():
            matches = [p for p in cur.iterdir() if p.name.casefold() == item.casefold()] if cur.is_dir() else []
            if not matches:
                raise FileNotFoundError(f"Recurso referenciado não existe: {relative}")
            nxt = matches[0]
        cur = nxt
    return cur


def parse_tileset(node: ET.Element, base_dir: Path, root: Path) -> dict:
    firstgid = int(node.attrib["firstgid"])
    external = node.get("source")
    if external:
        tsx_file = locate(base_dir, external)
        source = ET.parse(tsx_file).getroot()
        image_base = tsx_file.parent
    else:
        source = node
        image_base = base_dir
    image = source.find("image")
    if image is None:
        raise ValueError(f"Tileset sem imagem: {source.attrib}")
    image_path = locate(image_base, image.attrib["source"])
    return {
        "firstgid": firstgid,
        "image": image_path.relative_to(root).as_posix(),
        "tilewidth": int(source.attrib["tilewidth"]),
        "tileheight": int(source.attrib["tileheight"]),
        "columns": int(source.get("columns", "0") or 0),
        "spacing": int(source.get("spacing", "0")),
        "margin": int(source.get("margin", "0")),
        "imagewidth": int(image.get("width", "0")),
        "imageheight": int(image.get("height", "0")),
        "tilecount": int(source.get("tilecount", "0")),
    }


def parse_map(path: Path, root: Path) -> dict:
    xml = ET.parse(path).getroot()
    if xml.attrib.get("orientation") != "orthogonal":
        raise ValueError(f"Mapa não ortogonal: {path}")
    width, height = int(xml.get("width", "0")), int(xml.get("height", "0"))
    result = {
        "name": path.stem,
        "path": path.relative_to(root).as_posix(),
        "width": width, "height": height,
        "tilewidth": int(xml.attrib["tilewidth"]),
        "tileheight": int(xml.attrib["tileheight"]),
        "tilesets": [parse_tileset(ts, path.parent, root) for ts in xml.findall("tileset")],
        "layers": [],
    }
    for layer in xml.findall("layer"):
        data = layer.find("data")
        if data is None or data.attrib.get("encoding") != "base64":
            raise ValueError(f"Camada não suportada em {path}")
        raw = base64.b64decode("".join(data.itertext()).strip())
        compression = data.get("compression")
        if compression == "zlib":
            raw = zlib.decompress(raw)
        elif compression == "gzip":
            import gzip
            raw = gzip.decompress(raw)
        elif compression:
            raise ValueError(f"Compressão não suportada: {compression}")
        count = int(layer.get("width", str(width))) * int(layer.get("height", str(height)))
        if len(raw) != count * 4:
            raise ValueError(f"Tamanho de camada inválido: {path}, {len(raw)} bytes, esperado {count*4}")
        gids = struct.unpack("<" + str(count) + "I", raw)
        runs = [[int(gid), sum(1 for _ in group)] for gid, group in __import__("itertools").groupby(gids)]
        result["layers"].append({"name": layer.get("name", ""), "runs": runs})
    return result


def parse_atlas(path: Path, root: Path) -> dict | None:
    data = plistlib.loads(path.read_bytes())
    if not isinstance(data, dict) or not isinstance(data.get("frames"), dict):
        return None  # Plist de partículas, não atlas de sprites.
    meta = data.get("metadata", {})
    source = meta.get("realTextureFileName") or meta.get("textureFileName") or path.with_suffix(".png").name
    image_path = locate(path.parent, str(source))
    frames = []
    for name, entry in sorted(data["frames"].items()):
        rect = entry.get("frame", entry.get("textureRect", ""))
        if isinstance(rect, str) and rect.strip():
            x, y, w, h = numvec(rect, 4)
        elif all(k in entry for k in ("x", "y", "width", "height")):
            x, y, w, h = [int(entry[k]) for k in ("x", "y", "width", "height")]
        else:
            continue
        src = numvec(str(entry.get("sourceSize", "{" + str(w) + "," + str(h) + "}")), 2)
        offset = numvec(str(entry.get("offset", "{0,0}")), 2)
        frames.append({"name": name, "x": x, "y": y, "w": w, "h": h,
                       "rotated": bool(entry.get("rotated", entry.get("textureRotated", False))),
                       "source_w": src[0], "source_h": src[1],
                       "offset_x": offset[0], "offset_y": offset[1]})
    return {"name": path.stem, "path": path.relative_to(root).as_posix(),
            "image": image_path.relative_to(root).as_posix(), "frames": frames}


def prepare(assets: Path, output: Path) -> dict:
    assets, output = assets.resolve(), output.resolve()
    if not assets.is_dir():
        raise FileNotFoundError(f"Pasta de recursos ausente: {assets}. Execute extrair_barbarq.py primeiro.")
    output.mkdir(parents=True, exist_ok=True)
    maps = [parse_map(p, assets) for p in sorted(assets.rglob("*.tmx"))]
    atlases = []
    for path in sorted(assets.rglob("*.plist")):
        atlas = parse_atlas(path, assets)
        if atlas is not None:
            atlas["kind"] = "plist XML"
            atlases.append(atlas)
    for path in sorted(assets.rglob("*.bplist")):
        decoded = decode_file(path)
        # O nome da textura nos metadados pode variar em maiúsculas/minúsculas.
        try:
            image_path = locate(path.parent, decoded["texture"])
            has_texture = image_path.is_file()
        except FileNotFoundError:
            # Alguns .bplist do próprio APK referenciam PNGs ausentes.
            # Preservamos os metadados e sinalizamos a ausência no visualizador.
            image_path = path.parent / decoded["texture"]
            has_texture = False
        atlas = {"name": path.stem, "path": path.relative_to(assets).as_posix(),
                 "image": image_path.relative_to(assets).as_posix(),
                 "missing_image": not has_texture,
                 "kind": "bplist FlatBuffers", "frames": decoded["frames"]}
        # Validação: cada frame precisa estar dentro das dimensões declaradas.
        image_w, image_h = decoded["size"]
        for frame in atlas["frames"]:
            if frame["x"] + frame["w"] > image_w or frame["y"] + frame["h"] > image_h:
                raise BPlistError(f"Sprite fora da textura: {atlas['path']} {frame['name']}")
        atlases.append(atlas)
    (output / "maps.lua").write_text("-- Gerado localmente a partir do APK; não versionar.\nreturn " + lua(maps) + "\n", encoding="utf-8")
    (output / "atlases.lua").write_text("-- Gerado localmente a partir do APK; não versionar.\nreturn " + lua(atlases) + "\n", encoding="utf-8")
    stats = {"maps": len(maps), "tile_layers": sum(len(m["layers"]) for m in maps),
             "atlases_xml": sum(a["kind"] == "plist XML" for a in atlases),
             "sprites_xml": sum(len(a["frames"]) for a in atlases if a["kind"] == "plist XML"),
             "atlases_bplist": sum(a["kind"] == "bplist FlatBuffers" for a in atlases),
             "sprites_bplist": sum(len(a["frames"]) for a in atlases if a["kind"] == "bplist FlatBuffers"),
             "atlas_sprites_total": sum(len(a["frames"]) for a in atlases),
             "atlases_missing_textures": sum(bool(a.get("missing_image")) for a in atlases)}
    (output / "summary.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, default=Path("assets_original"))
    parser.add_argument("--out", type=Path, default=Path("cache"))
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.assets, args.out), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, FileNotFoundError, OSError, ET.ParseError, plistlib.InvalidFileException, BPlistError) as exc:
        parser.exit(1, f"Erro de preparação: {exc}\n")

if __name__ == "__main__":
    raise SystemExit(main())