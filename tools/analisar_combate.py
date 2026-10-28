#!/usr/bin/env python3
"""F23: cadeia de dano e busca de alvos, comprovada por símbolos e chamadas ARM64.

Não executa o ELF, não calcula dano e não copia o código do executável.
A análise exige o SHA-256 de libcocos2dcpp.so da versão 1.0.1811.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Nome, endereço, tamanho e símbolo exato da biblioteca fornecida.
FUNCTIONS = (
    ('CDamageFunction::Run()', 0xe52ff8, 120, '_ZN15CDamageFunction3RunEv'),
    ('CDamageFunction::Run(target)', 0xe53070, 280, '_ZN15CDamageFunction3RunEP12CSkillEntity'),
    ('CDamageFunction::GetDamageValue', 0xe52950, 1328, '_ZN15CDamageFunction14GetDamageValueEPb'),
    ('CDamageFunction::GetParamValue', 0xe52e94, 356, '_ZN15CDamageFunction13GetParamValueEPKN6config5skill14FunctionDamage18DamageFormulaParamEf'),
    ('CSelectTargetSector::GetSelectTargets', 0xe63e14, 632, '_ZN19CSelectTargetSector16GetSelectTargetsEv'),
    ('CSelectTargetNearest::GetSelectTargets', 0xe63990, 612, '_ZN20CSelectTargetNearest16GetSelectTargetsEv'),
    ('CMultiTargetSkill::Update', 0xe65f2c, 524, '_ZN17CMultiTargetSkill6UpdateEf'),
    ('Entity::skill_update', 0xe4a28c, 488, '_ZN6Entity12skill_updateEf'),
)
# Dependências observáveis nas instruções, não garantia de fluxo tomado em todo caso.
CHECKS = {
    'CDamageFunction::Run()': {
        'damage_run_target': r'\bbl\s+[^\n]*_ZN15CDamageFunction3RunEP12CSkillEntity',
    },
    'CDamageFunction::Run(target)': {
        'resolve_target_entity': r'\bbl\s+[^\n]*_ZNK12CSkillEntity9GetEntityEb',
        'get_damage_value': r'\bbl\s+[^\n]*_ZN15CDamageFunction14GetDamageValueEPb',
        'hero_hurt': r'\bbl\s+[^\n]*_ZN4Hero16addHurtFromEnemy',
    },
    'CDamageFunction::GetDamageValue': {
        'read_parameter': r'\bbl\s+[^\n]*_ZN15CDamageFunction13GetParamValue',
        'random_number': r'\bbl\s+[^\n]*_ZN7RandNum9__NextInt',
    },
    'CSelectTargetSector::GetSelectTargets': {
        'stick_direction': r'\bbl\s+[^\n]*_ZNK4Hero17getButtonStickDir',
        'physical_query': r'\bbl\s+[^\n]*_ZNK7b2World9QueryAABB',
        'trig_cosine': r'\bbl\s+[^\n]*_ZN14WildsMathUtils6cosDeg',
        'trig_sine': r'\bbl\s+[^\n]*_ZN14WildsMathUtils6sinDeg',
    },
    'CSelectTargetNearest::GetSelectTargets': {},
    'CMultiTargetSkill::Update': {
        'bind_function_entity': r'\bbl\s+[^\n]*_ZN9CFunction9SetEntity',
    },
    'Entity::skill_update': {
        'release_skill': r'\bbl\s+[^\n]*_ZN6CSkill7ReleaseEv',
    },
    'CDamageFunction::GetParamValue': {},
}
SYMBOL_RE = re.compile(r'^\s*\d+:\s*([0-9a-f]+)\s+(\d+)\s+FUNC\s+\w+\s+DEFAULT\s+\d+\s+(\S+)', re.M)
INSTRUCTION_RE = re.compile(r'^\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+([a-z][a-z.0-9_]*)', re.M|re.I)
CALL_RE = re.compile(r'^\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+bl\s+[^\n]*?<([^>]+)>', re.M|re.I)


def capture(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, text=True, capture_output=True, timeout=35).stdout


def audit(library: Path, manifest: Path) -> dict:
    manifest_data = json.loads(manifest.read_text(encoding='utf-8'))
    correct_hash = next(v['sha256'] for v in manifest_data['libraries'] if v['name'] == 'libcocos2dcpp.so')
    with library.open('rb') as stream:
        actual_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual_hash != correct_hash:
        raise ValueError('Biblioteca incompatível: SHA-256 difere da versão 1.0.1811')
    symbols = {(int(addr, 16), int(size), name) for addr, size, name in SYMBOL_RE.findall(capture(['readelf', '-Ws', str(library)]))}
    findings: list[dict] = []
    total_insns = 0
    for name, addr, size, symbol in FUNCTIONS:
        if (addr, size, symbol) not in symbols:
            raise ValueError(f'Símbolo original ausente ou alterado: {name}')
        disasm = capture(['llvm-objdump', '-d', f'--start-address=0x{addr:x}',
                          f'--stop-address=0x{addr + size:x}', str(library)])
        addresses = [int(a, 16) for a, _ in INSTRUCTION_RE.findall(disasm)]
        if addresses != list(range(addr, addr + size, 4)):
            raise ValueError(f'Instruções incompletas ou desalinhadas: {name}')
        missing = [k for k, pattern in CHECKS[name].items() if not re.search(pattern, disasm)]
        if missing:
            raise ValueError(f'Cadeia nativa alterada em {name}: {missing}')
        calls = []
        for _, ref in CALL_RE.findall(disasm):
            mangled = ref.split('@')[0].split('+')[0]
            # Só expor uma lista compacta dos símbolos relacionados à investigação.
            if any(token in mangled for token in ('DamageFunction', 'addHurtFromEnemy', 'SelectTarget', 'QueryAABB', 'getButtonStickDir', 'SetEntity', 'CSkill7Release', 'RandNum')):
                if mangled not in calls:
                    calls.append(mangled)
        total_insns += len(addresses)
        findings.append({'name': name, 'virtual_address': f'0x{addr:x}',
                         'size_bytes': size, 'instruction_count': len(addresses),
                         'checks': sorted(CHECKS[name]), 'observed_calls': calls})
    return {
        'phase': 23, 'apk_version': '1.0.1811', 'library_sha256': actual_hash,
        'functions': findings, 'total_instructions': total_insns,
        'confirmed': [
            'Run() chama Run(CSkillEntity*) em um ramo.',
            'Run(CSkillEntity*) consulta GetDamageValue e pode chamar Hero::addHurtFromEnemy.',
            'GetDamageValue lê parâmetros de fórmula e chama um gerador de números aleatórios.',
            'SelectTargetSector consulta direção de controle, trigonometria e uma busca AABB no Box2D.',
            'Entity::skill_update contém chamada para liberar CSkill.',
        ],
        'limits': ('Chamada presente não implica execução incondicional. Não foram recuperados valores de dano, '
                   'probabilidades, seleção final de vítimas, momento do acerto, recarga ou vínculo entre '
                   'a habilidade 4010020 e uma função de dano. Não executar combate com este relatório.'),
    }


def export_lua(report: dict) -> str:
    lines = ['-- Fase 23: metadados auditados do ELF ARM64, não dados de execução.', 'return {']
    for row in report['functions']:
        safe = lambda s: json.dumps(s, ensure_ascii=True)
        lines.append(f'  {{name={safe(row["name"])}, address={safe(row["virtual_address"])}, instructions={row["instruction_count"]}, checks={{')
        for check in row['checks']:
            lines.append(f'    {safe(check)},')
        lines.append('  }},')
    lines.append('}')
    return '\n'.join(lines) + '\n'


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--library', type=Path, default=ROOT / 'lib/arm64-v8a/libcocos2dcpp.so')
    p.add_argument('--manifest', type=Path, default=ROOT / 'reports/native_arm64.json')
    p.add_argument('--report', type=Path, default=ROOT / 'reports/native_combat.json')
    p.add_argument('--lua', type=Path, default=ROOT / 'reports/native_combat.lua')
    args = p.parse_args()
    report = audit(args.library, args.manifest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.lua.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    args.lua.write_text(export_lua(report), encoding='utf-8')
    print('F23:', len(report['functions']), 'funções,', report['total_instructions'], 'instruções, SHA-256 confirmado')


if __name__ == '__main__':
    main()
