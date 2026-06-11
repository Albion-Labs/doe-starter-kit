#!/usr/bin/env python3
"""PK-4: deterministic integrity gate for the fault corpus.

Asserts every fault is well-formed and ids are unique, so the corpus can grow
(append-only) over time without silently breaking the harness. Exit 0/1.
"""
import json, sys
from pathlib import Path

PROOF = Path(__file__).resolve().parent
MANIFEST = PROOF / "corpus" / "manifest.json"
METHODS = {"hook", "filescan", "filescan-miss"}


def main():
    faults = json.loads(MANIFEST.read_text()).get("faults", [])
    errs, seen = [], set()
    if not faults:
        errs.append("no faults in corpus")
    for i, f in enumerate(faults):
        fid = f.get("id")
        if not fid:
            errs.append(f"fault #{i} missing id")
        elif fid in seen:
            errs.append(f"duplicate id {fid}")
        else:
            seen.add(fid)
        for k in ("class", "method", "expect"):
            if k not in f:
                errs.append(f"{fid}: missing '{k}'")
        m = f.get("method")
        if m not in METHODS:
            errs.append(f"{fid}: bad method {m!r}")
        if m == "hook":
            for k in ("hook", "tool_name", "input_field", "value_parts", "benign_value_parts"):
                if k not in f:
                    errs.append(f"{fid}: hook fault missing '{k}'")
            gf = f.get("git_fixture")
            if gf is not None and (
                not isinstance(gf, dict)
                or "fault_branch" not in gf
                or "benign_branch" not in gf
            ):
                errs.append(f"{fid}: git_fixture must carry fault_branch and benign_branch")
        if m in ("filescan", "filescan-miss") and "inject" not in f:
            errs.append(f"{fid}: filescan fault missing 'inject'")
    if errs:
        print("CORPUS INVALID:")
        for e in errs:
            print("  -", e)
        return 1
    print(f"corpus OK: {len(faults)} faults, ids unique, all well-formed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
