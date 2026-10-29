#!/usr/bin/env python3
"""F50: cross-reference F49 vptr-load patterns with F47 relocation entries.

Itanium ABI address point is typically vtable symbol + 16 on 64-bit targets;
this is a candidate assumption, NOT proof of receiver type or runtime call.
Never marks a target verified from slot coincidence alone.
"""
import argparse
import json
from pathlib import Path

SHA="8199604d199b57ebe329725c9a624b85517f495f78c1dad745449684750e4677"

def correlate(f47, f49):
    if f47.get("phase") != 47 or f49.get("phase") != 49:
        raise ValueError("Expected F47 and F49 reports")
    if f47.get("library_sha256") != SHA or f49.get("elf_sha256") != SHA:
        raise ValueError("ELF fingerprint mismatch")
    tables=f47.get("vtable_candidates")
    calls=f49.get("candidate_local_patterns")
    if not isinstance(tables,list) or not isinstance(calls,dict):
        raise ValueError("Incomplete report")
    results=[]
    for routine, sites in sorted(calls.items()):
        for site in sites:
            if site.get("classification")!="local_load_pattern_only" or site.get("resolved_target") is not None:
                raise ValueError("Unexpected F49 provenance status")
            offset=site.get("slot_offset")
            if type(offset) is not int or offset<0 or offset%8:
                raise ValueError("Invalid slot offset")
            matches=[]
            for table in tables:
                # +16 is an ABI hypothesis for the address point of a primary
                # Itanium-style vtable, not a confirmed property of this object.
                assumed_table_offset=offset+16
                for entry in table.get("entries",[]):
                    if entry.get("slot_offset")==assumed_table_offset:
                        matches.append({
                            "vtable_symbol":table["vtable_symbol"],
                            "relocation_slot_offset":assumed_table_offset,
                            "referenced_symbol":entry["referenced_symbol"],
                            "hypothesis":"primary_itanium_address_point_plus_16",
                            "verified_destination":False
                        })
            results.append({
                "routine":routine,"callsite_va":site["callsite_va"],
                "vptr_receiver_register":site.get("receiver_register"),
                "method_offset_from_address_point":offset,
                "candidates":matches,
                "classification":"candidate_slot_match_without_receiver_type",
                "confirmed_destination":None
            })
    return {
        "phase":50,"apk_version":"1.0.1811","elf_sha256":SHA,
        "callsite_count":len(results),
        "candidate_match_count":sum(len(r["candidates"]) for r in results),
        "confirmed_destinations":0,
        "callsite_candidates":results,
        "assumptions":["Primary 64-bit Itanium-style vtable address point at symbol + 16; secondary construction tables may differ.",
                       "Receiver dynamic type, vptr initialization, and relocation semantics are not established."],
        "gameplay_enabled":False,"basic_attack_4010020_effect_verified":False
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--vtables",type=Path,default=Path("reports/vtables47.json"))
    parser.add_argument("--registers",type=Path,default=Path("reports/register_provenance49.json"))
    parser.add_argument("--out",type=Path,default=Path("reports/dispatch_candidates50.json"))
    args=parser.parse_args()
    output=correlate(json.loads(args.vtables.read_text(encoding="utf8")),
                     json.loads(args.registers.read_text(encoding="utf8")))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(output,indent=2)+"\n",encoding="utf8")
    print("F50 sites:",output["callsite_count"],"candidates:",output["candidate_match_count"],
          "verified:",output["confirmed_destinations"])

if __name__=="__main__":
    main()
