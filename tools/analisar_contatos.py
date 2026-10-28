#!/usr/bin/env python3
"""F15: análise estática dos contatos do Box2D em um APK local do BarbarQ 1.0.1811.

Confere SHA-256, símbolos ELF, desmontagem e padrões ARM64 antes de criar
relatórios. Não executa código Android e NÃO implementa colisões.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile

LIB = "lib/arm64-v8a/libcocos2dcpp.so"
TARGETS = {
 "b2World::Step(float, int, int)": (0x1b70eac, 508),
 "b2ContactManager::Collide()": (0x1b6dcc8, 408),
 "b2Contact::Update(b2ContactListener*)": (0x1b726d8, 592),
 "wildsContactListener::BeginContact(b2Contact*)": (0xe438c0, 100),
 "wildsContactListener::EndContact(b2Contact*)": (0xe43924, 4),
 "wildsContactListener::PreSolve(b2Contact*, b2Manifold const*)": (0xe43928, 4),
 "wildsContactListener::PostSolve(b2Contact*, b2ContactImpulse const*)": (0xe4392c, 4),
 "Entity::ProcessContact(b2Vec2)": (0xe4b574, 208),
}
PATTERNS = {
 "b2World::Step(float, int, int)": {
   "find_new_contacts": r"bl\s+[^\n]*b2ContactManager15FindNewContacts",
   "collide": r"bl\s+[^\n]*b2ContactManager7Collide",
   "solve": r"bl\s+[^\n]*b2World5Solve",
   "solve_toi": r"bl\s+[^\n]*b2World8SolveTOI",
   "nonpositive_step_guard": r"fcmp\s+s8,\s*#0\.0",
 },
 "b2ContactManager::Collide()": {"update_contact":r"bl\s+[^\n]*b2Contact6Update"},
 "b2Contact::Update(b2ContactListener*)": {
   "callback_indirect":r"blr\s+x8","touching_transition":r"cbnz\s+w24",
 },
 "wildsContactListener::BeginContact(b2Contact*)": {
   "first_contact_gate":r"ldrb\s+w8,\s*\[x0,\s*#0x1c1\]",
   "second_contact_gate":r"ldrb\s+w8,\s*\[x20,\s*#0x1c1\]",
   "call_process_contact":r"bl\s+[^\n]*Entity14ProcessContact",
   "tail_process_contact":r"b\s+[^\n]*Entity14ProcessContact",
   "contact_vector":r"ldp\s+s0,\s*s1,\s*\[x19,\s*#0xa0\]",
 },
 "Entity::ProcessContact(b2Vec2)": {
   "cos_degrees":r"bl\s+[^\n]*WildsMathUtils6cosDeg",
   "sin_degrees":r"bl\s+[^\n]*WildsMathUtils6sinDeg",
   "atan2_degrees":r"bl\s+[^\n]*WildsMathUtils8atan2Deg",
   "writes_angle":r"str\s+w8,\s*\[x19,\s*#0xdc\]",
   "secondary_gate":r"ldrb\s+w9,\s*\[x19,\s*#0x1c2\]",
 },
}
INS = re.compile(r"^\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+([a-z][\w.]*)\s*(.*)$",re.I)
CALL = re.compile(r"\b0x([0-9a-f]+)\s+<([^>]+)>",re.I)

def run(args, **kw):
    return subprocess.run(args,capture_output=True,text=True,check=True,timeout=40,**kw).stdout

def analyze(apk, manifest):
    source=json.loads(Path(manifest).read_text(encoding="utf-8"))
    expected=next(x["sha256"] for x in source["libraries"] if x["name"]=="libcocos2dcpp.so")
    with ZipFile(apk) as z:
        info=z.getinfo(LIB)
        if not 1_000_000 <= info.file_size <= 100_000_000:
            raise ValueError("ELF fora do limite permitido")
        binary=z.read(info)
    digest=hashlib.sha256(binary).hexdigest()
    if digest!=expected:
        raise ValueError("SHA-256 diferente: não reutilizar offsets de outro APK")
    if binary[:4]!=b"\x7fELF" or binary[4]!=2 or binary[5]!=1 or int.from_bytes(binary[18:20],"little")!=183:
        raise ValueError("Arquivo não é ELF64 AArch64 little-endian")
    result=[]
    with tempfile.TemporaryDirectory(prefix="barlua-f15-") as tmp:
        so=Path(tmp)/"cocos.so"
        so.write_bytes(binary)
        raw=run(["readelf","-Ws",str(so)])
        candidates=[]
        for row in raw.splitlines():
            f=row.split()
            if len(f)<8 or f[3]!="FUNC" or f[6]=="UND":
                continue
            mangled=f[7].split("@")[0]
            if mangled.startswith(("_ZN7b2World4Step","_ZN16b2ContactManager7Collide",
                                   "_ZN9b2Contact6Update","_ZN20wildsContactListener",
                                   "_ZN6Entity14ProcessContact")):
                candidates.append((mangled,int(f[1],16),int(f[2])))
        demangled=run(["c++filt"],input="\n".join(x[0] for x in candidates)+"\n").splitlines()
        if len(demangled)!=len(candidates):
            raise ValueError("Falha ao conferir os símbolos C++")
        found={}
        for name,(_,addr,size) in zip(demangled,candidates):
            if name in TARGETS:
                if name in found and found[name]!=(addr,size):
                    raise ValueError("Símbolo duplicado conflitante")
                found[name]=(addr,size)
        if found!=TARGETS:
            raise ValueError("Assinaturas, offsets ou tamanhos inesperados")
        for signature,(addr,size) in TARGETS.items():
            asm=run(["llvm-objdump","-d","--demangle",f"--start-address=0x{addr:x}",
                     f"--stop-address=0x{addr+size:x}",str(so)])
            ins=[]
            for line in asm.splitlines():
                m=INS.match(line)
                if m: ins.append((int(m[1],16),m[2].lower(),m[3]))
            if [i[0] for i in ins]!=list(range(addr,addr+size,4)):
                raise ValueError("Desmontagem incompleta de "+signature)
            checks=PATTERNS.get(signature,{})
            missing=[key for key,regex in checks.items() if not re.search(regex,asm)]
            if missing:
                raise ValueError(signature+": padrões faltantes: "+", ".join(missing))
            if signature.startswith("wildsContactListener::") and "BeginContact" not in signature:
                if len(ins)!=1 or ins[0][1]!="ret":
                    raise ValueError("Callback deixou de ser vazio")
            direct=indirect=branches=0
            targets={}
            for _,opcode,operands in ins:
                if opcode=="bl":
                    m=CALL.search(operands)
                    if not m: raise ValueError("Chamada sem destino")
                    direct+=1
                    targets[m[2]]=targets.get(m[2],0)+1
                elif opcode=="blr": indirect+=1
                if opcode in ("b","br","cbz","cbnz","tbz","tbnz") or opcode.startswith("b."):
                    branches+=1
            result.append({"signature":signature,"address":hex(addr),"size_bytes":size,
                           "instructions":len(ins),"direct_calls":direct,
                           "indirect_calls":indirect,"branches":branches,
                           "verified_patterns":sorted(checks),
                           "targets":[{"name":k,"count":v} for k,v in sorted(targets.items())]})
    return {"version":"1.0.1811","library_sha256":digest,
            "source":"análise estática ELF64 AArch64; nenhuma física executada",
            "functions":result,
            "limitations":["Não reconstrói geometria de colisores, resolução física, dano ou rede.",
                           "Resultados específicos da versão validada por SHA-256."]}

def to_lua(report):
    lines=["-- Metadados ARM64; nao e fisica jogavel.","return {"]
    for f in report["functions"]:
        q=lambda s: json.dumps(s,ensure_ascii=False)
        lines.append("  {name=%s,address=%s,instructions=%d,direct=%d,indirect=%d,checks=%d}," %
                     (q(f["signature"]),q(f["address"]),f["instructions"],
                      f["direct_calls"],f["indirect_calls"],len(f["verified_patterns"])))
    return "\n".join(lines+["}",""])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apk",type=Path,required=True)
    p.add_argument("--manifest",type=Path,default=Path("reports/native_arm64.json"))
    p.add_argument("--out",type=Path,default=Path("reports"))
    a=p.parse_args()
    for dep in ("readelf","c++filt","llvm-objdump"):
        if not shutil.which(dep):p.error(dep+" não encontrado")
    report=analyze(a.apk,a.manifest)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"native_contacts.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (a.out/"native_contacts.lua").write_text(to_lua(report),encoding="utf-8")
    print("F15:",len(report["functions"]),"funções",sum(x["instructions"] for x in report["functions"]),"instruções")

if __name__=="__main__": main()
