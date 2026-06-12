"""Self-vacuity guards for the proof harness (liveness audit B7, v1.71.5).

The fault-injection harness is the kit's last line of evidence, so it
gets its own honesty checks: --self-test must not pass over an empty
corpus ("all covered faults caught" is vacuously true of zero faults),
and metrics.py must refuse a path that isn't a git repo instead of
reporting perfect 0%/0% over nothing.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
METRICS = KIT / "proof" / "metrics.py"


def test_metrics_refuses_non_repo_path(tmp_path):
    p = subprocess.run(
        [sys.executable, str(METRICS), "--repo", str(tmp_path / "nope")],
        capture_output=True, text=True, timeout=30,
    )
    assert p.returncode == 2, p.stdout + p.stderr
    assert "not a git repository" in p.stdout


def test_metrics_accepts_real_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "--allow-empty", "-q", "-m", "feat: x"], cwd=repo, check=True)
    p = subprocess.run(
        [sys.executable, str(METRICS), "--repo", str(repo)],
        capture_output=True, text=True, timeout=30,
    )
    assert p.returncode == 0, p.stdout + p.stderr


def test_self_test_fails_on_empty_corpus(tmp_path):
    """Copy the proof tree (plus the gates it invokes), empty the corpus,
    and assert --self-test goes red instead of vacuously green."""
    dst = tmp_path / "kit"
    dst.mkdir()
    for sub in ("proof", ".claude", "execution"):
        shutil.copytree(KIT / sub, dst / sub,
                        ignore=shutil.ignore_patterns("__pycache__", "out"))
    manifest = dst / "proof" / "corpus" / "manifest.json"
    manifest.write_text(json.dumps({"schemaVersion": "1.0", "note": "", "faults": []}))
    p = subprocess.run(
        [sys.executable, str(dst / "proof" / "run.py"), "--self-test"],
        capture_output=True, text=True, timeout=120,
    )
    assert p.returncode == 1, p.stdout + p.stderr
    assert "EMPTY CORPUS" in p.stdout
