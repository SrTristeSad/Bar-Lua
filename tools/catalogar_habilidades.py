#!/usr/bin/env python3
"""Lê tabelas de configuração originais de BarbarQ 1.0.1811 sem inferir dano.

O arquivo .txt usa linhas com `ID tamanho_em_bytes_UTF8 descrição restante`.
Os recursos originais ficam fora do repositório público. O relatório público
contém somente contagens e IDs de ligações; o cache Lua fica em cache/.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

TABLES = (
    "heroskillconfig", "functionbindskill", "functiondamage", "functionanimation",
    "functionrandomskill", "functiondelayskill", "selectsector", "skilleventregister",
)
LINE_PREFIX = re.compile(rb"^(\d+) (\d+) ")


def parse_table(data: bytes, table: str) -> dict[int, dict]:
    if len(data) > 12 * 1024 * 1024:
        raise ValueError(f"Tabela excessivamente grande: {table}")
    result = {}
    for lineno, row in enumerate(data.splitlines(), 1):
        if not row.strip():
            continue
        match = LINE_PREFIX.match(row)
        if not match:
            raise ValueError(f"{table}:{lineno}: prefixo de ID/comprimento inválido")
        key, byte_length = int(match[1]), int(match[2])
        if key in result:
            raise ValueError(f"{table}:{lineno}: ID duplicado: {key}")
        start = match.end()
        end = start + byte_length
        if end >= len(row) or row[end:end + 1] != b" ":
            raise ValueError(f"{table}:{lineno}: comprimento UTF-8 inválido")
        try:
            label = row[start:end].decode("utf-8", errors="strict")
            payload = row[end + 1:].decode("utf-8", errors="strict")
        except UnicodeError as error:
            raise ValueError(f"{table}:{lineno}: texto UTF-8 inválido") from error
        result[key] = {"id": key, "description": label, "payload": payload}
    return result


def collect(assets_dir: Path) -> tuple[dict, dict]:
    data = {}
    sha = {}
    for table in TABLES:
        path = assets_dir / "configdata" / f"config.skill.{table}.txt"
        raw = path.read_bytes()
        sha[table] = hashlib.sha256(raw).hexdigest()
        data[table] = parse_table(raw, table)
    skills = data["heroskillconfig"]
    links = []
    for key, record in sorted(data["functionbindskill"].items()):
        tokens = record["payload"].split()
        # Observação: os registros deste APK possuem o formato (tipo, botão, ID).
        # Não é uma regra geral para outras versões.
        if len(tokens) != 3 or not all(re.fullmatch(r"\d+", t) for t in tokens):
            raise ValueError(f"Vínculo de botão com formato inesperado: {key}")
        kind, button, target = map(int, tokens)
        if target not in skills:
            raise ValueError(f"Vínculo {key} aponta para habilidade ausente {target}")
        links.append({"id": key, "name": record["description"], "kind": kind,
                      "button": button, "skill_id": target,
                      "skill_name": skills[target]["description"]})
    summary = {
        "phase": 21, "apk_version": "1.0.1811",
        "tables": {key: len(value) for key, value in data.items()},
        "table_sha256": sha, "button_links": len(links),
        "distinct_skills_in_links": len({row["skill_id"] for row in links}),
        "known_example": {"binding_id": 10039, "skill_config_id": 4010020},
        "limits": "Os IDs e nomes do vínculo são dados de configuração. Eles não provam dano, hitbox, duração de recarga ou correspondência entre cada tecla e animação."
    }
    example = next((row for row in links if row["id"] == 10039), None)
    if not example or example["skill_id"] != 4010020:
        raise ValueError("Vínculo esperado do ataque básico não foi encontrado")
    return summary, {"links": links, "summary": summary}


def lua_string(value: str) -> str:
    # Serialização literal segura, sem injeção de expressões Lua.
    result = ['"']
    for c in value:
        n = ord(c)
        if c in ('"', "\\"):
            result.append('\\' + c)
        elif n < 32 or n == 127:
            result.append("\\%03d" % n)
        else:
            result.append(c)
    result.append('"')
    return ''.join(result)


def lua_export(catalog: dict) -> str:
    lines = ['-- Cache local: gerado de recursos do APK pelo usuário; NÃO publicar no GitHub.', 'return {']
    lines.append('  links = {')
    for r in catalog['links']:
        lines.append(f'    {{id={r["id"]}, name={lua_string(r["name"])}, kind={r["kind"]}, '
                     f'button={r["button"]}, skill_id={r["skill_id"]}, skill_name={lua_string(r["skill_name"])}}},')
    lines.extend(['  },', '  tables = {'])
    for k, v in catalog['summary']['tables'].items():
        lines.append(f'    {k} = {v},')
    lines.extend(['  }', '}', ''])
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--assets', type=Path, default=Path(__file__).resolve().parents[1] / 'assets_original')
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parents[1] / 'cache' / 'skill_catalog.lua')
    parser.add_argument('--report', type=Path, default=Path(__file__).resolve().parents[1] / 'reports' / 'skill_catalog_summary.json')
    args = parser.parse_args()
    summary, catalog = collect(args.assets)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(lua_export(catalog), encoding='utf-8')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('F21: tabelas:', summary['tables'], 'vínculos:', summary['button_links'])

if __name__ == '__main__':
    main()
