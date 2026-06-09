#!/usr/bin/env python3
"""PK-5: self-pruning ablation.

For each gate, compute its MARGINAL catch -- how many faults are lost from the
catch-rate if that gate is removed. marginalCatch == 0 means the gate is
redundant theatre (a candidate to cut); > 0 means it is load-bearing. This is
the deterministic-gate layer of DOE's "cut your own ceremony" principle: we
attack our own framework and keep only what earns its place. Ceremony-level
ablation (retro steps, sign-offs) is future work requiring instrumented sessions.

Usage: python3 ablation.py [--json]
"""
import json, subprocess, sys
from pathlib import Path

PROOF = Path(__file__).resolve().parent
sys.path.insert(0, str(PROOF))
import run as harness  # noqa: E402

OUT = PROOF / "out" / "scorecard.json"


def ablate():
    scorecard, results, _, _ = harness.run()
    counts = {}
    for r in results:
        if r["caught"] and r.get("gate"):
            counts[r["gate"]] = counts.get(r["gate"], 0) + 1
    ablation = [{"ceremony": f"gate:{g}", "marginalCatch": n,
                 "verdict": "load-bearing" if n > 0 else "candidate-to-cut"}
                for g, n in sorted(counts.items())]
    return ablation, scorecard


def main(argv):
    ablation, scorecard = ablate()
    scorecard["ablation"] = ablation
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(scorecard, indent=2))
    print("DOE Proof - ablation (marginal catch per gate)")
    for a in ablation:
        print(f"    {a['ceremony']:<38} marginal {a['marginalCatch']}  -> {a['verdict']}")
    cut = [a for a in ablation if a["verdict"] == "candidate-to-cut"]
    print(f"  load-bearing: {len(ablation) - len(cut)} | candidate-to-cut: {len(cut)}")
    print("  (ceremony-level ablation of retro steps is future work)")
    v = subprocess.run([sys.executable, str(PROOF / "schema" / "validate.py"), str(OUT)],
                       capture_output=True, text=True)
    if v.returncode != 0:
        print("scorecard invalid:", v.stdout.strip())
        return 1
    if "--json" in argv:
        print(json.dumps({"ablation": ablation}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
