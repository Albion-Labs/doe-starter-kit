"""Tests for execution/health_check.py."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "execution"))

import health_check


# ── SCAN_PROFILES ─────────────────────────────────────────────

def test_scan_profiles_not_empty():
    """SCAN_PROFILES must contain at least html-app and python profiles."""
    assert "html-app" in health_check.SCAN_PROFILES
    assert "python" in health_check.SCAN_PROFILES


def test_scan_profile_has_required_keys():
    """Every scan profile must have the required keys."""
    required = {"paths", "extensions", "stub_patterns", "todo_patterns", "empty_fn_patterns"}
    for name, profile in health_check.SCAN_PROFILES.items():
        for key in required:
            assert key in profile, f"Profile '{name}' missing key '{key}'"


# ── run_universal_checks ──────────────────────────────────────

def test_run_universal_checks_returns_list():
    """run_universal_checks must return a list of dicts."""
    results = health_check.run_universal_checks()
    assert isinstance(results, list)
    assert len(results) > 0


def test_run_universal_checks_result_shape():
    """Each universal check result must have 'name' and 'status' keys."""
    results = health_check.run_universal_checks()
    for r in results:
        assert "name" in r, f"Result missing 'name': {r}"
        assert "status" in r, f"Result missing 'status': {r}"
        assert r["status"] in ("OK", "WARN", "PASS", "FAIL", "SKIP"), (
            f"Unexpected status '{r['status']}' in result: {r}"
        )


# ── load_health_config ────────────────────────────────────────

def test_load_health_config_returns_none_when_missing(tmp_path, monkeypatch):
    """load_health_config returns None when tests/health.json doesn't exist."""
    monkeypatch.setattr(health_check, "ROOT", tmp_path)
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)
    result = health_check.load_health_config()
    assert result is None


def test_load_health_config_parses_valid_json(tmp_path, monkeypatch):
    """load_health_config parses a valid health.json correctly."""
    monkeypatch.setattr(health_check, "ROOT", tmp_path)
    health_dir = tmp_path / "tests"
    health_dir.mkdir(parents=True, exist_ok=True)
    config = {"checks": [{"name": "Test check", "verify": "run: echo ok"}]}
    (health_dir / "health.json").write_text(json.dumps(config), encoding="utf-8")

    result = health_check.load_health_config()
    assert result is not None
    assert "checks" in result
    assert len(result["checks"]) == 1


def test_load_health_config_handles_corrupt_json(tmp_path, monkeypatch):
    """load_health_config returns error dict for malformed JSON."""
    monkeypatch.setattr(health_check, "ROOT", tmp_path)
    health_dir = tmp_path / "tests"
    health_dir.mkdir(parents=True, exist_ok=True)
    (health_dir / "health.json").write_text("{corrupt json", encoding="utf-8")

    result = health_check.load_health_config()
    assert result is not None
    assert "error" in result


# ── print_json_output ─────────────────────────────────────────

def test_print_json_output_is_valid_json(capsys):
    """print_json_output must emit parseable JSON."""
    universal = [{"name": "No stubs", "status": "OK", "detail": ""}]
    health_check.print_json_output(universal, None)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "summary" in data
    assert "universal" in data


def test_print_json_output_summary_counts(capsys):
    """JSON summary must reflect the correct pass/warn/fail counts."""
    universal = [
        {"name": "check1", "status": "OK", "detail": ""},
        {"name": "check2", "status": "WARN", "detail": "something"},
    ]
    project = [
        {"name": "proj1", "status": "FAIL", "detail": "broken"},
    ]
    health_check.print_json_output(universal, project)
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["summary"]["pass"] == 1
    assert data["summary"]["warn"] == 1
    assert data["summary"]["fail"] == 1
    assert data["summary"]["total"] == 3


# ── quick mode (universal only) ───────────────────────────────

def test_quick_mode_skips_project_checks(tmp_path, monkeypatch):
    """In quick mode, project checks must be skipped (project_checks is None in JSON)."""
    monkeypatch.setattr(health_check, "ROOT", tmp_path)
    # Provide a tasks/todo.md so find_project_root-like logic works
    (tmp_path / "tasks").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "todo.md").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "js").mkdir(parents=True, exist_ok=True)

    # quick=True means project = None
    universal = health_check.run_universal_checks()
    project = None  # mirrors what main() does with --quick

    from io import StringIO
    import sys as _sys
    old = _sys.stdout
    _sys.stdout = StringIO()
    health_check.print_json_output(universal, project)
    out = _sys.stdout.getvalue()
    _sys.stdout = old

    data = json.loads(out)
    assert data["project_checks"] is None


# ── Scan coverage disclosure (liveness audit B1, v1.71.5) ─────
# The file-scan checks report OK on an empty file list, so a mismatched
# projectType used to mean permanent vacuous green over zero files.

def _coverage_row(results):
    return next(r for r in results if r["name"] == "Scan coverage")


def test_zero_files_scanned_warns(tmp_path, monkeypatch):
    """Profile paths missing entirely -> coverage WARN, never silent pass."""
    monkeypatch.setattr(health_check, "ROOT", tmp_path)
    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks" / "todo.md").write_text("## Current\n")
    results = health_check.run_universal_checks()
    row = _coverage_row(results)
    assert row["status"] == "WARN"
    assert "0 files scanned" in row["detail"]
    assert "projectType" in row["detail"]


def test_nonzero_files_scanned_reports_count(tmp_path, monkeypatch):
    """Real files under a profile path -> coverage OK with a count."""
    monkeypatch.setattr(health_check, "ROOT", tmp_path)
    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks" / "todo.md").write_text("## Current\n")
    src = tmp_path / "src" / "js"
    src.mkdir(parents=True)
    (src / "app.js").write_text("function go() { return 1; }\n")
    results = health_check.run_universal_checks()
    row = _coverage_row(results)
    assert row["status"] == "OK"
    assert "1 file(s) scanned" in row["detail"]


# ── Missing health.json is a disclosed SKIP (liveness audit B10) ──

def test_missing_health_json_is_skip_not_fail(tmp_path, monkeypatch):
    """Full mode on a project without tests/health.json must SKIP with a
    pointer, not permanently FAIL (which normalises ignoring a red check)."""
    monkeypatch.setattr(health_check, "ROOT", tmp_path)
    (tmp_path / "tests").mkdir()
    results = health_check.run_project_checks()
    assert len(results) == 1
    assert results[0]["status"] == "SKIP"
    assert "not present" in results[0]["detail"]


def test_corrupt_health_json_still_fails(tmp_path, monkeypatch):
    """A present-but-broken health.json is a real error and stays FAIL."""
    monkeypatch.setattr(health_check, "ROOT", tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "health.json").write_text("{not json")
    results = health_check.run_project_checks()
    assert results[0]["status"] == "FAIL"
