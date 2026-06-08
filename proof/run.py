#!/usr/bin/env python3
"""DOE Proof Kit — fault-injection harness (PK-1).

Injects a corpus of known defects and measures how many the REAL DOE gates
catch. catch-rate = caught / injected. The control arm (no gate present) catches
0 by construction — that is the actual counterfactual for vanilla tooling
(Lovable/Replit/raw Claude have no such gate), stated plainly, not rigged.

Gates invoked are the actual kit scripts, unmodified:
  .claude/hooks/block_secrets_in_code.py     (stdin tool-event -> block JSON)
  .claude/hooks/block_dangerous_commands.py  (stdin tool-event -> block JSON)
  execution/health_check.py                  (file scan -> WARN on findings)

Usage:
  python3 run.py             # run, write out/scorecard.json, print summary
  python3 run.py --json      # also print the scorecard JSON
  python3 run.py --self-test # assert every COVERED fault is caught + control==0; exit 0/1
"""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path

PROOF = Path(__file__).resolve().parent
KIT = PROOF.parent
HOOKS = KIT / ".claude" / "hooks"
HEALTH = KIT / "execution" / "health_check.py"
FIXTURE = PROOF / "fixture"
MANIFEST = PROOF / "corpus" / "manifest.json"
OUT = PROOF / "out" / "scorecard.json"


def _run_hook(hook_file, event):
    """Invoke a PreToolUse hook with a tool-event on stdin.
    Returns (fired, detail): fired=True iff the hook emits a block decision."""
    path = HOOKS / hook_file
    if not path.exists():
        return None, f"gate script missing: {path}"
    try:
        p = subprocess.run([sys.executable, str(path)], input=json.dumps(event),
                           capture_output=True, text=True, timeout=30)
    except Exception as ex:
        return None, f"invoke error: {ex}"
    out = (p.stdout or "").strip()
    if not out:
        return False, "allowed (no block emitted)"
    try:
        dec = json.loads(out)
        if isinstance(dec, dict) and dec.get("decision") == "block":
            return True, dec.get("reason", "blocked")
    except json.JSONDecodeError:
        pass
    return False, f"no block decision (out: {out[:60]})"


def _run_filescan(inject, check_name):
    """Copy the fixture, inject a defect into src/app.py, run the REAL
    health_check, report whether the named universal check went WARN."""
    if not HEALTH.exists():
        return None, f"gate script missing: {HEALTH}"
    tmp = Path(tempfile.mkdtemp(prefix="doe-proof-"))
    try:
        dst = tmp / "fixture"
        shutil.copytree(FIXTURE, dst)
        with open(dst / "src" / "app.py", "a") as f:
            f.write(inject)
        try:
            p = subprocess.run([sys.executable, str(HEALTH), "--json", "--quick"],
                               cwd=str(dst), capture_output=True, text=True, timeout=60)
        except Exception as ex:
            return None, f"invoke error: {ex}"
        try:
            data = json.loads(p.stdout)
        except json.JSONDecodeError:
            return None, "health_check produced non-JSON output"
        if check_name is None:
            any_warn = any(r.get("status") == "WARN" for r in data.get("universal", []))
            return any_warn, "any-gate scan"
        for r in data.get("universal", []):
            if r.get("name") == check_name:
                return (r.get("status") == "WARN"), r.get("detail", "") or r.get("status")
        return False, f"check '{check_name}' not present"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _stamp():
    try:
        return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                              capture_output=True, text=True, timeout=5).stdout.strip() \
            or "1970-01-01T00:00:00Z"
    except Exception:
        return "1970-01-01T00:00:00Z"


def run():
    faults = json.loads(MANIFEST.read_text())["faults"]
    results, by_gate = [], []
    for fa in faults:
        m = fa["method"]
        if m == "hook":
            value = "".join(fa["value_parts"])
            ti = dict(fa.get("input_extra", {}))
            ti[fa["input_field"]] = value
            fired, detail = _run_hook(fa["hook"], {"tool_name": fa["tool_name"], "tool_input": ti})
        elif m == "filescan":
            fired, detail = _run_filescan(fa["inject"], fa["check"])
        elif m == "filescan-miss":
            fired, detail = _run_filescan(fa["inject"], None)
        else:
            fired, detail = None, f"unknown method {m}"
        caught = bool(fired)  # for expect=block/flag a block IS the catch; for miss, fired stays False
        results.append({**fa, "fired": fired, "caught": caught, "detail": detail})
        by_gate.append({
            "gate": fa["gate"] or "(none - no deterministic gate)",
            "defectClass": fa["class"], "injected": 1, "caught": 1 if caught else 0,
        })
    injected = len(faults)
    caught = sum(1 for r in results if r["caught"])
    covered = [r for r in results if r.get("covered")]
    cov_caught = sum(1 for r in covered if r["caught"])
    scorecard = {
        "schemaVersion": "1.0",
        "kind": "framework-benchmark",
        "project": {"id": "fixture-synthetic", "name": "Synthetic Fixture", "repo": None},
        "generatedAt": _stamp(),
        "catchRate": {
            "injected": injected, "caught": caught,
            "rate": round(caught / injected, 4) if injected else 0.0,
            "byGate": by_gate,
            "control": {"injected": injected, "caught": 0, "rate": 0.0},
        },
    }
    return scorecard, results, cov_caught, len(covered)


def main(argv):
    scorecard, results, cov_caught, cov_total = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(scorecard, indent=2))
    cr = scorecard["catchRate"]
    print("DOE Proof - fault injection")
    print(f"  injected {cr['injected']} | caught {cr['caught']} | rate {cr['rate']:.0%}")
    print(f"  covered defect classes (DOE has a gate): {cov_caught}/{cov_total} caught")
    print(f"  control (no gate / vanilla tooling): {cr['control']['caught']}/{cr['control']['injected']}")
    for r in results:
        mark = "CAUGHT" if r["caught"] else ("MISS  " if r.get("expect") == "miss" else "LEAK  ")
        print(f"    [{mark}] {r['id']} {r['class']:<20} via {r['gate'] or '(none)'}")
    print(f"  scorecard -> {OUT.relative_to(KIT)}")

    if "--self-test" in argv:
        problems = []
        for r in results:
            if r.get("covered") and not r["caught"]:
                problems.append(f"covered fault {r['id']} NOT caught -- {r['detail']}")
            if r.get("expect") == "miss" and r["caught"]:
                problems.append(f"fault {r['id']} expected MISS but was caught")
        if cr["control"]["caught"] != 0:
            problems.append("control caught > 0")
        v = subprocess.run([sys.executable, str(PROOF / "schema" / "validate.py"), str(OUT)],
                           capture_output=True, text=True)
        if v.returncode != 0:
            problems.append(f"scorecard fails schema validation: {v.stdout.strip()}")
        if problems:
            print("SELF-TEST FAILED:")
            for pr in problems:
                print("  -", pr)
            return 1
        print("SELF-TEST PASSED (every covered fault caught, control clean, scorecard valid)")

    if "--json" in argv:
        print(json.dumps(scorecard, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
