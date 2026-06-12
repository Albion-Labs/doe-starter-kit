#!/usr/bin/env python3
"""DOE Proof Kit — fault-injection harness (PK-1).

Injects a corpus of known defects, runs the REAL DOE gates, scores catch-rate
(caught / injected). Two honest measurements accompany it:
  - falsePositives: each gate is also run against a BENIGN counterpart input;
    it must NOT fire. This is MEASURED and proves the gates discriminate rather
    than always-fire.
  - control: 0 by CONSTRUCTION (vanilla tooling has none of these gates) -- this
    is labelled as such, not dressed up as a measured experiment.

"enforcement" distinguishes a hard BLOCK (hook decision) from an advisory FLAG
(health_check WARN, non-blocking), so the card never presents a flag as a block.

Deterministic: pure Python 3, no network, no LLM, no randomness (bar generatedAt).
provenance records the sha256 of each real gate + the kit commit.

Usage:
  python3 run.py            # run, write out/scorecard.json, print summary
  python3 run.py --json     # also print the scorecard JSON
  python3 run.py --self-test
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

PROOF = Path(__file__).resolve().parent
KIT = PROOF.parent
HOOKS = KIT / ".claude" / "hooks"
HEALTH = KIT / "execution" / "health_check.py"
FIXTURE = PROOF / "fixture"
MANIFEST = PROOF / "corpus" / "manifest.json"
OUT = PROOF / "out" / "scorecard.json"
ENFORCEMENT = {"block": "blocked", "flag": "flagged", "miss": "none"}

# Escape-valve env vars are scrubbed before every hook invocation: an
# inherited shell override must never silently green a fault. GIT_* vars are
# scrubbed too -- an ambient GIT_DIR makes `git -C <non-git-dir>` succeed
# against the OUTER repo, silently inverting fail-closed faults (F15), and
# global git config (e.g. commit.gpgsign) must not leak into fixtures.
ESCAPE_VALVES = ("SKIP_KIT_GUARD", "SKIP_REVIEW_GATE", "BYPASS_BLOCK",
                 "ALLOW_MERGE", "SKIP_MAIN_PROTECTION")


def _scrubbed_env(env_extra=None):
    env = {k: v for k, v in os.environ.items()
           if k not in ESCAPE_VALVES and not k.startswith("GIT_")}
    if env_extra:
        env.update(env_extra)
    return env


def _run_hook(hook_file, event, env_extra=None, cwd=None):
    path = HOOKS / hook_file
    if not path.exists():
        return None, f"gate script missing: {path}"
    try:
        # cwd is anchored to the kit so relative-path checks inside hooks
        # (e.g. protect_directives' existence test) are deterministic
        # regardless of where run.py is invoked from.
        p = subprocess.run([sys.executable, str(path)], input=json.dumps(event),
                           capture_output=True, text=True, timeout=30,
                           cwd=cwd or str(KIT), env=_scrubbed_env(env_extra))
    except (OSError, subprocess.SubprocessError) as ex:
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
    if not HEALTH.exists():
        return None, f"gate script missing: {HEALTH}"
    tmp = Path(tempfile.mkdtemp(prefix="doe-proof-"))
    try:
        dst = tmp / "fixture"
        shutil.copytree(FIXTURE, dst)
        if inject:
            with open(dst / "src" / "app.py", "a") as f:
                f.write(inject)
        try:
            p = subprocess.run([sys.executable, str(HEALTH), "--json", "--quick"],
                               cwd=str(dst), capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError) as ex:
            return None, f"invoke error: {ex}"
        try:
            data = json.loads(p.stdout)
        except json.JSONDecodeError:
            return None, "health_check produced non-JSON output"
        if check_name is None:
            return any(r.get("status") == "WARN" for r in data.get("universal", [])), "any-gate scan"
        for r in data.get("universal", []):
            if r.get("name") == check_name:
                return (r.get("status") == "WARN"), r.get("detail", "") or r.get("status")
        return False, f"check '{check_name}' not present"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _git(tmp, *args):
    subprocess.run(["git", "-C", str(tmp), *args], capture_output=True,
                   text=True, timeout=15, check=True,
                   env=_scrubbed_env({"GIT_CONFIG_GLOBAL": "/dev/null",
                                      "GIT_CONFIG_SYSTEM": "/dev/null"}))


def _assign_field(ti, field, value):
    """Assign value at input_field. Flat names assign directly; the indexed
    form 'name[i].sub' reaches into a list-of-dicts field (MultiEdit edits)."""
    m = re.fullmatch(r"(\w+)\[(\d+)\]\.(\w+)", field)
    if m:
        ti[m.group(1)][int(m.group(2))][m.group(3)] = value
    else:
        ti[field] = value


def _fire_hook_value(fa, value, benign=False):
    # Deep copy: indexed assignment must not leak the assembled trigger value
    # back into the shared manifest dict between the fault and benign arms.
    ti = json.loads(json.dumps(fa.get("input_extra", {})))
    _assign_field(ti, fa["input_field"], value)
    event = {"tool_name": fa["tool_name"], "tool_input": ti}
    env_extra, cwd, tmps = {}, None, []
    try:
        # gh_shim: hooks that would call the gh CLI get a PATH-front shim
        # that always exits 1 -- the fail-closed arm is exercised with zero
        # network, identically with/without gh installed or authed.
        if fa.get("gh_shim"):
            shim = Path(tempfile.mkdtemp(prefix="doe-proof-shim-"))
            tmps.append(shim)
            gh = shim / "gh"
            gh.write_text("#!/bin/sh\necho 'proof shim: gh unavailable' >&2\nexit 1\n")
            gh.chmod(0o755)
            env_extra["PATH"] = f"{shim}:{os.environ.get('PATH', '')}"
        # neutral_cwd: run the hook from a disposable directory instead of
        # the kit, so cwd-sensitive arms (guard_kit_writes' cwd-inside-kit
        # branch) cannot mask the pattern arm under test.
        if fa.get("neutral_cwd"):
            ncwd = Path(tempfile.mkdtemp(prefix="doe-proof-cwd-"))
            tmps.append(ncwd)
            cwd = str(ncwd)
        # git_fixture: hooks that read git state via $CLAUDE_PROJECT_DIR get
        # a disposable fixture: a branch name means a one-commit repo checked
        # out on that branch; null means a plain non-git directory
        # (exercises the fail-closed arm).
        gf = fa.get("git_fixture")
        if gf:
            branch = gf["benign_branch"] if benign else gf["fault_branch"]
            tmp = Path(tempfile.mkdtemp(prefix="doe-proof-git-"))
            tmps.append(tmp)
            if branch is not None:
                try:
                    _git(tmp, "init", "-q")
                    _git(tmp, "-c", "user.email=proof@doe", "-c", "user.name=proof",
                         "commit", "--allow-empty", "-q", "-m", "fixture")
                    _git(tmp, "checkout", "-q", "-b", branch)
                except (OSError, subprocess.SubprocessError) as ex:
                    return None, f"git fixture setup failed: {ex}"
            if fa.get("git_fixture_as_event_cwd"):
                # Issue #107 class: the project dir is a NON-git decoy (a
                # background job's $HOME) and the repo arrives via the
                # event's cwd field, exactly as the live harness sends it.
                decoy = Path(tempfile.mkdtemp(prefix="doe-proof-decoy-"))
                tmps.append(decoy)
                env_extra["CLAUDE_PROJECT_DIR"] = str(decoy)
                event["cwd"] = str(tmp)
            else:
                env_extra["CLAUDE_PROJECT_DIR"] = str(tmp)
            # Ceiling stops git's upward discovery at the fixture's parent:
            # without it, a TMPDIR nested inside any git repo makes
            # `git -C <non-git-fixture>` resolve the ENCLOSING repo and
            # silently invert the fail-closed arm.
            env_extra["GIT_CEILING_DIRECTORIES"] = str(tmp.parent)
        return _run_hook(fa["hook"], event,
                         env_extra=env_extra or None, cwd=cwd)
    finally:
        for d in tmps:
            shutil.rmtree(d, ignore_errors=True)


def _fire(fa, benign=False):
    """Run the gate for fault `fa`. benign=True runs the safe counterpart and
    expects NO fire. Returns (fired, detail)."""
    m = fa["method"]
    if m == "hook":
        parts = fa["benign_value_parts"] if benign else fa["value_parts"]
        return _fire_hook_value(fa, "".join(parts), benign=benign)
    inject = "" if benign else fa["inject"]
    check = fa.get("check")
    return _run_filescan(inject, check if check else None)


def _stamp():
    try:
        return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                              capture_output=True, text=True, timeout=5).stdout.strip() or "1970-01-01T00:00:00Z"
    except (OSError, subprocess.SubprocessError):
        return "1970-01-01T00:00:00Z"


def _gate_scripts():
    """Every distinct hook the corpus exercises, plus health_check —
    derived from the manifest so provenance can never lag the corpus."""
    seen, scripts = set(), []
    for fa in json.loads(MANIFEST.read_text())["faults"]:
        h = fa.get("hook")
        if h and h not in seen:
            seen.add(h)
            scripts.append(HOOKS / h)
    scripts.append(HEALTH)
    return scripts


def _provenance():
    gates = []
    for p in _gate_scripts():
        if p.exists():
            gates.append({"script": str(p.relative_to(KIT)),
                          "sha256_16": hashlib.sha256(p.read_bytes()).hexdigest()[:16]})
        else:
            gates.append({"script": str(p.relative_to(KIT)), "sha256_16": "MISSING"})
    commit = ""
    try:
        commit = subprocess.run(["git", "-C", str(KIT), "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return {"kitCommit": commit or "UNKNOWN", "gates": gates}


def run():
    faults = json.loads(MANIFEST.read_text())["faults"]
    results, by_gate = [], []
    fp_fired = 0
    fp_detail = []
    for fa in faults:
        fired, detail = _fire(fa, benign=False)
        caught = bool(fired)
        results.append({**fa, "fired": fired, "caught": caught, "detail": detail})
        by_gate.append({
            "gate": fa["gate"] or "(none - no deterministic gate)",
            "defectClass": fa["class"],
            "enforcement": ENFORCEMENT.get(fa.get("expect"), "unknown"),
            "injected": 1, "caught": 1 if caught else 0,
        })
        # measured false-positive arm: run the benign counterpart, expect no fire.
        # None means the arm ERRORED (fixture setup, missing gate) -- recorded
        # loudly rather than passing as "no fire".
        bfired, bdetail = _fire(fa, benign=True)
        if bfired is None:
            results[-1]["benign_error"] = bdetail
        elif bfired:
            fp_fired += 1
            fp_detail.append(f"{fa['id']} false-fired on benign input ({bdetail})")
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
            "control": {
                "injected": injected, "caught": 0, "rate": 0.0,
                "basis": "by-construction: vanilla tooling (raw Claude / Lovable / Replit) has none of these gates, so it catches none of these defects",
            },
        },
        "falsePositives": {
            "injected": injected, "fired": fp_fired,
            "rate": round(fp_fired / injected, 4) if injected else 0.0,
            "basis": "measured: each gate run against a benign counterpart input; it must not fire",
            "detail": fp_detail,
        },
        "provenance": _provenance(),
    }
    return scorecard, results, cov_caught, len(covered)


def main(argv):
    scorecard, results, cov_caught, cov_total = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(scorecard, indent=2))
    cr = scorecard["catchRate"]
    fp = scorecard["falsePositives"]
    blocked = sum(1 for g in cr["byGate"] if g["enforcement"] == "blocked" and g["caught"])
    flagged = sum(1 for g in cr["byGate"] if g["enforcement"] == "flagged" and g["caught"])
    print("DOE Proof - fault injection")
    print(f"  injected {cr['injected']} | caught {cr['caught']} ({blocked} blocked, {flagged} flagged) | rate {cr['rate']:.0%}")
    print(f"  covered classes (DOE has a gate): {cov_caught}/{cov_total} caught")
    print(f"  false-positives on benign input (MEASURED): {fp['fired']}/{fp['injected']}")
    print(f"  control without DOE: 0/{cr['injected']} (by construction)")
    for r in results:
        enf = ENFORCEMENT.get(r.get("expect"), "?")
        mark = (enf.upper() if r["caught"] else ("MISS" if r.get("expect") == "miss" else "LEAK"))
        print(f"    [{mark:<8}] {r['id']} {r['class']:<20} via {r['gate'] or '(none)'}")
    print(f"  scorecard -> {OUT.relative_to(KIT)}")
    if "--self-test" in argv:
        problems = []
        # Liveness audit B7: an empty corpus must never self-test green --
        # "all covered faults caught" is vacuously true over zero faults.
        if cr["injected"] == 0:
            problems.append("EMPTY CORPUS: 0 faults injected -- nothing was tested")
        for r in results:
            if r.get("covered") and not r["caught"]:
                problems.append(f"covered fault {r['id']} NOT caught -- {r['detail']}")
            if r.get("expect") == "miss" and r["caught"]:
                problems.append(f"fault {r['id']} expected MISS but was caught")
            if r.get("benign_error"):
                problems.append(f"benign arm of {r['id']} errored -- {r['benign_error']}")
        if fp["fired"] != 0:
            problems.append("MEASURED false-positive(s): " + "; ".join(fp["detail"]))
        v = subprocess.run([sys.executable, str(PROOF / "schema" / "validate.py"), str(OUT)],
                           capture_output=True, text=True)
        if v.returncode != 0:
            problems.append(f"scorecard fails schema validation: {v.stdout.strip()}")
        if problems:
            print("SELF-TEST FAILED:")
            for pr in problems:
                print("  -", pr)
            return 1
        print("SELF-TEST PASSED (covered faults caught, zero measured false-positives, scorecard valid)")
    if "--json" in argv:
        print(json.dumps(scorecard, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
