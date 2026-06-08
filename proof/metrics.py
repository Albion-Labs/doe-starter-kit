#!/usr/bin/env python3
"""PK-3: derive DORA-style outcome metrics from a real git repo.

HONEST GIT-DERIVED PROXIES, not instrumented production telemetry:
  changeFailureRate ~ share of commits that revert/roll back/hotfix a change
  reworkRate        ~ share of commits that fix/redo/patch prior work (>= CFR;
                      catches rework CFR hides, per the DORA/DX literature)
  leadTimeHours     ~ median PR cycle time from merge commits (omitted if none)
  deployFrequency   ~ merges (or commits) per week over the window
Deterministic for a given repo state. Economics uses sourced, conservative
constants (economics/model.py) -- never the unsourced cost-curve folklore.

Usage:
  python3 metrics.py --repo <path> [--window-days 30] [--defects-caught N] [--json]
  python3 metrics.py --self-test
"""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

PROOF = Path(__file__).resolve().parent
sys.path.insert(0, str(PROOF))
from economics import model as econ  # noqa: E402

OUT = PROOF / "out" / "metrics.json"
FAIL_RE = re.compile(r'\b(revert|rollback|roll back|hotfix|regression)\b', re.I)
REWORK_RE = re.compile(r'\b(fix|fixup|redo|rework|patch|revert|rollback|hotfix|amend|bug)\b', re.I)


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout


def _stamp():
    try:
        return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                              capture_output=True, text=True, timeout=5).stdout.strip() or "1970-01-01T00:00:00Z"
    except Exception:
        return "1970-01-01T00:00:00Z"


def _commits(repo, days):
    out = _git(repo, "log", f"--since={days} days ago", "--no-merges", "--pretty=%ct%x09%s")
    rows = []
    for line in out.splitlines():
        if "\t" in line:
            ct, subj = line.split("\t", 1)
            rows.append((int(ct), subj))
    return rows


def _merges(repo, days):
    out = _git(repo, "log", f"--since={days} days ago", "--merges", "--pretty=%ct")
    return [int(x) for x in out.splitlines() if x.strip().isdigit()]


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return None
    mid = n // 2
    return xs[mid] if n % 2 else round((xs[mid - 1] + xs[mid]) / 2, 2)


def _lead_time_hours(repo, days):
    out = _git(repo, "log", f"--since={days} days ago", "--merges", "--pretty=%H %ct")
    leads = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        h, ct = parts[0], int(parts[1])
        parents = _git(repo, "rev-list", "--parents", "-n", "1", h).split()
        if len(parents) < 3:
            continue
        base = _git(repo, "merge-base", parents[1], parents[2]).strip()
        if not base:
            continue
        times = [int(x) for x in _git(repo, "log", f"{base}..{parents[2]}", "--pretty=%ct").splitlines() if x.strip().isdigit()]
        if times:
            leads.append((ct - min(times)) / 3600.0)
    return _median(leads)


def compute(repo, days, defects_caught=0):
    commits = _commits(repo, days)
    total = len(commits)
    failures = sum(1 for _, s in commits if FAIL_RE.search(s))
    rework = sum(1 for _, s in commits if REWORK_RE.search(s))
    cfr = round(failures / total, 4) if total else 0.0
    rwr = round(rework / total, 4) if total else 0.0
    merges = _merges(repo, days)
    weeks = max(days / 7.0, 1e-9)
    dora = {
        "changeFailureRate": min(cfr, 1.0),
        "reworkRate": min(rwr, 1.0),
        "deployFrequencyPerWeek": round((len(merges) or total) / weeks, 2),
        "deployFrequencyBasis": "merges" if merges else "commits (no merge commits found)",
        "basis": "git-commit-message heuristic PROXY -- not deployment/incident telemetry",
    }
    lead = _lead_time_hours(repo, days)
    if lead is not None:
        dora["leadTimeHours"] = lead
    econ_block = {"poundsSaved": econ.pounds_saved(defects_caught), "model": econ.MODEL, "sources": econ.SOURCES}
    if defects_caught <= 0:
        econ_block["note"] = "poundsSaved requires a defect-caught count (from the gate harness); not inferred from git."
    return {
        "schemaVersion": "1.0", "kind": "project-metrics",
        "project": {"id": Path(repo).name, "name": Path(repo).name, "repo": str(repo)},
        "generatedAt": _stamp(), "dora": dora, "economics": econ_block,
        "provenance": {"windowDays": days, "commitsAnalysed": total,
                       "failureCommits": failures, "reworkCommits": rework},
    }


def _self_test():
    tmp = Path(tempfile.mkdtemp(prefix="doe-metrics-"))
    repo = tmp / "r"
    repo.mkdir()

    def g(*a, **env):
        e = dict(os.environ)
        e.update(env)
        subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=e)
    try:
        g("init", "-q")
        g("config", "user.email", "t@t")
        g("config", "user.name", "t")
        msgs = ["feat: initial", "feat: add A", "fix: correct A", "feat: add B",
                "revert: revert B", "feat: add C", "hotfix: patch C", "docs: readme"]
        for i, m in enumerate(msgs):
            (repo / "f.txt").write_text(str(i))
            d = f"2026-01-0{i + 1}T12:00:00"
            g("add", "-A")
            g("commit", "-q", "-m", m, GIT_AUTHOR_DATE=d, GIT_COMMITTER_DATE=d)
        sc = compute(repo, 3650, defects_caught=6)
        problems = []
        if sc["dora"]["changeFailureRate"] != 0.25:
            problems.append(f"CFR {sc['dora']['changeFailureRate']} != 0.25")
        if sc["dora"]["reworkRate"] != 0.375:
            problems.append(f"reworkRate {sc['dora']['reworkRate']} != 0.375")
        if sc["economics"]["poundsSaved"] != 360.0:
            problems.append(f"poundsSaved {sc['economics']['poundsSaved']} != expected 360.0 (6 x 15 x 4)")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(sc, indent=2))
        v = subprocess.run([sys.executable, str(PROOF / "schema" / "validate.py"), str(OUT)],
                           capture_output=True, text=True)
        if v.returncode != 0:
            problems.append(f"schema: {v.stdout.strip()}")
        return problems, sc
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    if "--self-test" in argv:
        problems, sc = _self_test()
        print(f"self-test: CFR={sc['dora']['changeFailureRate']} rework={sc['dora']['reworkRate']} "
              f"poundsSaved={sc['economics']['poundsSaved']}")
        if problems:
            print("SELF-TEST FAILED:")
            for p in problems:
                print("  -", p)
            return 1
        print("SELF-TEST PASSED (CFR/rework correct, economics sourced, scorecard valid)")
        return 0
    if "--repo" not in argv:
        print("usage: metrics.py --repo <path> [--window-days N] [--defects-caught N] [--json]")
        return 2
    repo = argv[argv.index("--repo") + 1]
    days = int(argv[argv.index("--window-days") + 1]) if "--window-days" in argv else 30
    dc = int(argv[argv.index("--defects-caught") + 1]) if "--defects-caught" in argv else 0
    sc = compute(repo, days, dc)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(sc, indent=2))
    d = sc["dora"]
    print(f"project-metrics for {sc['project']['name']} (window {days}d, {sc['provenance']['commitsAnalysed']} commits)")
    print(f"  change-failure-rate: {d['changeFailureRate']:.0%}   rework-rate: {d['reworkRate']:.0%}"
          f"   deploy/wk: {d['deployFrequencyPerWeek']}" + (f"   lead: {d['leadTimeHours']}h" if 'leadTimeHours' in d else ""))
    print(f"  poundsSaved: GBP {sc['economics']['poundsSaved']}  -> out/metrics.json")
    if "--json" in argv:
        print(json.dumps(sc, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
