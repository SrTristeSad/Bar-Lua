#!/usr/bin/env python3
"""F21: valida pontos de controle do ciclo de habilidades no ELF original.

Usa somente símbolos dinâmicos/endereços/instruções. Não exporta disassembly
nem reproduz códigos nativos. Em caso de divergência, rejeita o relatório.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'Hero::onButtonClicked': (0xe57918, 104, '_ZN4Hero15onButtonClicked'),
    'Entity::addSkill(configId)': (0xe46b7c, 456, '_ZN6Entity8addSkillEii'),
    'Entity::addSkill(skillPtr)': (0xe48744, 552, '_ZN6Entity8addSkillEP6CSkillb'),
    'CSkill::CreateSkillBySkillConfigId': (0xe650b4, 320, '_ZN6CSkill26CreateSkillBySkillConfigId'),
    'CSkill::SetTargetEntitys': (0xe65204, 412, '_ZN6CSkill16SetTargetEntitys'),
    'CSkill::Release': (0xe65034, 128, '_ZN6CSkill7Release'),
    'CSkill::Update(float)': (0xe65200, 4, '_ZN6CSkill6UpdateEf'),
}
PATTERNS = {
    'Hero::onButtonClicked': {
        'button_range_guard': r'cmp\s+w1,\s*#0x11',
        'config_id_read': r'ldr\s+w9,\s*\[x8,\s*#0x3bc\]',
        'creator_call': r'bl\s+[^\n]*CreateSkillBySkillConfigId',
        'add_skill_call': r'\bb\s+[^\n]*Entity8addSkill',
    },
    'Entity::addSkill(configId)': {
        'config_family_check': r'cmp\s+w9,\s*#0x14',
        'create_skill_call': r'bl\s+[^\n]*CreateSkillBySkillConfigId',
        'level_assignment': r'bl\s+[^\n]*CSkill8SetLevel',
        'handoff_to_entity': r'\bb\s+[^\n]*Entity8addSkill',
    },
    'Entity::addSkill(skillPtr)': {
        'null_pointer_guard': r'cbz\s+x19',
        'release_call': r'bl\s+[^\n]*CSkill7Release',
    },
    'CSkill::CreateSkillBySkillConfigId': {
        'type_10050': r'mov\s+w8,\s*#0x2742',
        'self_skill_constructor': r'bl\s+[^\n]*CSelfSkillC2',
        'multi_target_constructor': r'bl\s+[^\n]*CMultiTargetSkillC2',
        'virtual_init_call': r'blr\s+x8',
    },
    'CSkill::SetTargetEntitys': {},
    'CSkill::Release': {},
    'CSkill::Update(float)': {'empty_base_update': r'^\s*[a-f0-9]+:\s+[a-f0-9]{8}\s+ret\s*$',},
}
SYMBOL = re.compile(r'^\s*\d+:\s*([0-9a-f]+)\s+(\d+)\s+FUNC\s+\w+\s+DEFAULT\s+\d+\s+(\S+)', re.M)
INSN = re.compile(r'^\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+([a-z][a-z.0-9_]*)', re.M|re.I)


def audit(library: Path, manifest: Path) -> dict:
    metadata = json.loads(manifest.read_text(encoding='utf-8'))
    expected_hash = next(x['sha256'] for x in metadata['libraries'] if x['name'] == 'libcocos2dcpp.so')
    observed_hash = hashlib.sha256(library.read_bytes()).hexdigest()
    if observed_hash != expected_hash:
        raise ValueError('SHA-256 incorreto: biblioteca diferente da versão 1.0.1811')
    elf = subprocess.run(['readelf', '-Ws', str(library)], capture_output=True, text=True, check=True, timeout=30).stdout
    symbol_index = {name: (int(address, 16), int(size)) for address, size, name in SYMBOL.findall(elf)}
    results = {}
    total = 0
    for display_name, (addr, size, prefix) in EXPECTED.items():
        matching = [(symbol, a, s) for symbol, (a, s) in symbol_index.items() if symbol.startswith(prefix) and a == addr and s == size]
        if not matching:
            raise ValueError(f'Símbolo ELF incompatível: {display_name}')
        disasm = subprocess.run(['llvm-objdump', '-d', f'--start-address=0x{addr:x}',
                                 f'--stop-address=0x{addr+size:x}', str(library)],
                                capture_output=True, text=True, check=True, timeout=30).stdout
        instructions = [(int(a, 16), op) for a, op in INSN.findall(disasm)]
        if [a for a, _ in instructions] != list(range(addr, addr + size, 4)):
            raise ValueError(f'Instruções/endereços inválidos: {display_name}')
        checks = PATTERNS[display_name]
        missing = [k for k, pattern in checks.items() if not re.search(pattern, disasm, re.M)]
        if missing:
            raise ValueError(f'Padrões ARM64 ausentes em {display_name}: {missing}')
        total += len(instructions)
        results[display_name] = {'virtual_address': f'0x{addr:x}', 'size_bytes': size,
                                 'instruction_count': len(instructions),
                                 'checks': sorted(checks)}
    return {
        'phase': 21,
        'apk_version': '1.0.1811',
        'library_sha256': observed_hash,
        'functions': results,
        'total_instructions': total,
        'verified_facts': [
            'Hero::onButtonClicked cria a habilidade configurada e a entrega a Entity::addSkill.',
            'Entity::addSkill(int,...) confere a família de ID 20 antes de criar habilidade e ajustar nível.',
            'CreateSkillBySkillConfigId escolhe entre CSelfSkill e CMultiTargetSkill usando tipo 10050.',
            'A implementação base CSkill::Update(float) tem apenas a instrução ret.',
        ],
        'limits': ('Não recupera execução de efeitos, cálculo de dano, identificação de hitbox, '
                   'cooldown nem estados internos de subclasses. Métodos dinâmicos podem sobrescrever Update.'),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--library', type=Path, default=ROOT / 'lib/arm64-v8a/libcocos2dcpp.so')
    ap.add_argument('--manifest', type=Path, default=ROOT / 'reports/native_arm64.json')
    ap.add_argument('--out', type=Path, default=ROOT / 'reports/native_skill_flow.json')
    args = ap.parse_args()
    report = audit(args.library, args.manifest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('F21: funções=', len(report['functions']), 'instruções=', report['total_instructions'])

if __name__ == '__main__':
    main()
