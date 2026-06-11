"""Reader/writer path symmetry for the review gate artifacts (kit v1.71.3).

Liveness-audit finding A9: the gate READER (enforce_review_gate.py)
anchors branch + artifact paths to $CLAUDE_PROJECT_DIR, but the WRITER
(record_review_result.py) used bare `git branch --show-current` and a
relative .tmp/ -- under cwd drift the pass artifact landed in the wrong
.tmp/ and a passed review still blocked PR creation (bit a live session;
artifacts had to be bridged by hand). persist_review_findings.py had the
mirror-image mismatch (worktree-safe root, cwd-relative git state).

These tests drive both scripts as subprocesses from a DRIFTED cwd (a
subdirectory of the project) with $CLAUDE_PROJECT_DIR set, and assert
every artifact lands in the project root's .tmp/ — the exact location
the reader checks.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
RECORD = KIT / "global-scripts" / "record_review_result.py"
PERSIST = KIT / "global-scripts" / "persist_review_findings.py"

BRANCH = "feature/proof-fixture"


def _make_repo(tmp_path):
    repo = tmp_path / "proj"
    repo.mkdir()
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}

    def git(*args):
        subprocess.run(["git", "-C", str(repo), *args], check=True,
                       capture_output=True, text=True, env=env)

    git("init", "-q")
    git("-c", "user.email=t@t", "-c", "user.name=t",
        "commit", "--allow-empty", "-q", "-m", "fixture")
    git("checkout", "-q", "-b", BRANCH)
    drifted = repo / "sub" / "dir"
    drifted.mkdir(parents=True)
    return repo, drifted


def _run(script, args, cwd, project_dir):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd), env=env, capture_output=True, text=True, timeout=30,
    )


def test_persist_anchors_to_project_dir_under_cwd_drift(tmp_path):
    repo, drifted = _make_repo(tmp_path)
    p = _run(PERSIST, ["finder", "no findings"], cwd=drifted, project_dir=repo)
    assert p.returncode == 0, p.stdout + p.stderr
    artifact = repo / ".tmp" / f"review-finder-{BRANCH}.json"
    assert artifact.exists(), "finder artifact must land in $CLAUDE_PROJECT_DIR/.tmp"
    data = json.loads(artifact.read_text())
    assert data["branch"] == BRANCH


def test_record_pass_anchors_to_project_dir_under_cwd_drift(tmp_path):
    repo, drifted = _make_repo(tmp_path)
    p = _run(PERSIST, ["finder", "no findings"], cwd=drifted, project_dir=repo)
    assert p.returncode == 0, p.stdout + p.stderr

    p = _run(RECORD, ["PASS"], cwd=drifted, project_dir=repo)
    assert p.returncode == 0, p.stdout + p.stderr
    artifact = repo / ".tmp" / f"review-passed-{BRANCH}.json"
    assert artifact.exists(), (
        "pass artifact must land where the gate reader looks: "
        "$CLAUDE_PROJECT_DIR/.tmp"
    )
    data = json.loads(artifact.read_text())
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    assert data["reviewed_sha"] == head
    # Nothing may leak into the drifted cwd.
    assert not (drifted / ".tmp").exists()


def test_record_pass_without_finder_artifact_refuses(tmp_path):
    repo, drifted = _make_repo(tmp_path)
    p = _run(RECORD, ["PASS"], cwd=drifted, project_dir=repo)
    assert p.returncode == 1
    assert "Finder" in p.stdout


def test_record_fail_removes_artifact(tmp_path):
    repo, drifted = _make_repo(tmp_path)
    _run(PERSIST, ["finder", "no findings"], cwd=drifted, project_dir=repo)
    _run(RECORD, ["PASS"], cwd=drifted, project_dir=repo)
    p = _run(RECORD, ["FAIL"], cwd=drifted, project_dir=repo)
    assert p.returncode == 0, p.stdout + p.stderr
    assert not (repo / ".tmp" / f"review-passed-{BRANCH}.json").exists()
