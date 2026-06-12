"""Tests for execution/audit_claims.py."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "execution"))

import audit_claims
from audit_claims import (
    AuditReport,
    Finding,
    Severity,
    parse_semver,
    minor_gap,
    parse_frontmatter,
    parse_completed_tasks,
    register,
)


# ── Severity / Finding ────────────────────────────────────────

def test_finding_severity_enum():
    """Severity enum must have PASS, WARN, FAIL values."""
    assert Severity.PASS.value == "PASS"
    assert Severity.WARN.value == "WARN"
    assert Severity.FAIL.value == "FAIL"


def test_audit_report_counts():
    """AuditReport pass/warn/fail_count must reflect added findings."""
    report = AuditReport()
    report.add(Finding(Severity.PASS, "test", "all good"))
    report.add(Finding(Severity.WARN, "test", "slight concern"))
    report.add(Finding(Severity.FAIL, "test", "broken"))

    assert report.pass_count == 1
    assert report.warn_count == 1
    assert report.fail_count == 1
    assert report.exit_code == 1


def test_audit_report_exit_code_zero_when_no_failures():
    """exit_code must be 0 when no FAIL findings exist."""
    report = AuditReport()
    report.add(Finding(Severity.PASS, "test", "ok"))
    assert report.exit_code == 0


# ── Severity classification (parse_semver / minor_gap) ───────

def test_parse_semver_basic():
    """parse_semver must parse standard vX.Y.Z strings."""
    assert parse_semver("v1.2.3") == (1, 2, 3)
    assert parse_semver("v0.11.4") == (0, 11, 4)


def test_parse_semver_invalid_returns_zeros():
    """parse_semver must return (0,0,0) for unrecognised strings."""
    assert parse_semver("not-a-version") == (0, 0, 0)


def test_minor_gap_calculation():
    """minor_gap must return the absolute minor version difference."""
    assert minor_gap("v0.5.0", "v0.8.0") == 3
    assert minor_gap("v1.0.0", "v1.0.0") == 0
    assert minor_gap("v0.10.0", "v0.8.0") == 2


# ── False positive handling (parse_frontmatter) ──────────────

def test_parse_frontmatter_returns_none_when_no_block(tmp_path):
    """parse_frontmatter must return None for files without front-matter."""
    md = tmp_path / "no_fm.md"
    md.write_text("# Just a heading\n\nSome content.", encoding="utf-8")
    assert parse_frontmatter(md) is None


def test_parse_frontmatter_parses_valid_block(tmp_path):
    """parse_frontmatter must parse a valid YAML-style front-matter block."""
    md = tmp_path / "with_fm.md"
    md.write_text(
        "---\nVersion: 1\nLast updated: 01/01/25\nApplies to: v0.5.0\nUpdated by: William\n---\n\n# Content",
        encoding="utf-8",
    )
    fm = parse_frontmatter(md)
    assert fm is not None
    assert fm.get("Version") == "1"
    assert fm.get("Last updated") == "01/01/25"


# ── Finding detection (parse_completed_tasks) ────────────────

def test_parse_completed_tasks_empty_file(tmp_path):
    """parse_completed_tasks must return empty list for file with no [x] items."""
    md = tmp_path / "todo.md"
    md.write_text("## Current\n\n1. [ ] pending task\n", encoding="utf-8")
    tasks = parse_completed_tasks(md)
    assert tasks == []


def test_parse_completed_tasks_finds_done_items(tmp_path):
    """parse_completed_tasks must find all [x] completed items."""
    md = tmp_path / "todo.md"
    md.write_text(
        "## Done\n\n"
        "1. [x] First feature → v0.1.0 *(completed 10:00 01/01/25)*\n"
        "2. [x] Second feature → v0.2.0 *(completed 11:00 02/01/25)*\n"
        "3. [ ] Not done\n",
        encoding="utf-8",
    )
    tasks = parse_completed_tasks(md)
    assert len(tasks) == 2
    assert tasks[0]["version"] == "v0.1.0"
    assert tasks[1]["version"] == "v0.2.0"


def test_parse_completed_tasks_detects_missing_timestamp(tmp_path):
    """parse_completed_tasks must include items even without timestamps."""
    md = tmp_path / "todo.md"
    md.write_text(
        "## Done\n\n1. [x] Some feature → v0.3.0\n",
        encoding="utf-8",
    )
    tasks = parse_completed_tasks(md)
    assert len(tasks) == 1
    assert tasks[0]["timestamp"] is None  # no timestamp


# ── register decorator ────────────────────────────────────────

def test_register_decorator_adds_to_checks():
    """@register should add the decorated function to the _CHECKS registry."""
    initial_count = len(audit_claims._CHECKS.get("test_scope_xyz", []))

    @register("test_scope_xyz", fast=True)
    def _dummy_check(report):
        pass

    after_count = len(audit_claims._CHECKS.get("test_scope_xyz", []))
    assert after_count == initial_count + 1
    assert _dummy_check._audit_scope == "test_scope_xyz"
    assert _dummy_check._audit_fast is True


# ── run_audit ─────────────────────────────────────────────────

def test_run_audit_returns_report():
    """run_audit must return an AuditReport instance."""
    report = audit_claims.run_audit(scope="universal", fast_only=True)
    assert isinstance(report, AuditReport)


def test_run_audit_json_serialisable():
    """to_json() must produce valid JSON."""
    import json
    report = audit_claims.run_audit(scope="universal", fast_only=True)
    data = json.loads(report.to_json())
    assert "summary" in data
    assert "findings" in data


# ── parse_roadmap_complete: live + legacy formats (liveness audit B2) ──
# The parser matched only "### Name (vX.Y.Z) — desc" headings while the
# kit's ROADMAP moved to "- **Name (vX.Y.Z)** [TAG] -- desc" bullets, so
# 0 entries parsed everywhere and roadmap_consistency passed vacuously.

def _roadmap(tmp_path, monkeypatch, body):
    monkeypatch.setattr(audit_claims, "PROJECT_ROOT", tmp_path)
    (tmp_path / "ROADMAP.md").write_text("# Roadmap\n\n## Complete\n" + body)


def test_parse_live_bullet_format(tmp_path, monkeypatch):
    _roadmap(tmp_path, monkeypatch,
             "- **Proof fault net (v1.71.0)** [INFRA] -- corpus extended. *(shipped 11/06/26)*\n")
    entries, unparsed = audit_claims.parse_roadmap_complete()
    assert unparsed == 0
    assert len(entries) == 1
    assert entries[0]["name"] == "Proof fault net"
    assert entries[0]["version"] == "v1.71.0"
    assert entries[0]["date"] == "11/06/26"


def test_parse_legacy_heading_format(tmp_path, monkeypatch):
    _roadmap(tmp_path, monkeypatch,
             "### Old feature (v1.2.3) — did a thing\n")
    entries, unparsed = audit_claims.parse_roadmap_complete()
    assert unparsed == 0
    assert [e["version"] for e in entries] == ["v1.2.3"]


def test_parse_version_inside_larger_paren(tmp_path, monkeypatch):
    _roadmap(tmp_path, monkeypatch,
             "- **Hook commands cwd-safe ($CLAUDE_PROJECT_DIR, v1.62.2)** [INFRA] -- fix. *(shipped 12/05/26)*\n")
    entries, _ = audit_claims.parse_roadmap_complete()
    assert entries[0]["version"] == "v1.62.2"


def test_parse_reports_unparsed_content_as_drift(tmp_path, monkeypatch):
    """Content that matches neither format must be COUNTED, not skipped —
    the checker reports drift instead of passing over a blind spot."""
    _roadmap(tmp_path, monkeypatch,
             "* Some bullet in a third format (v9.9.9)\n<!-- a comment -->\n\n")
    entries, unparsed = audit_claims.parse_roadmap_complete()
    assert entries == []
    assert unparsed == 1


def test_consistency_warns_on_format_drift(tmp_path, monkeypatch):
    _roadmap(tmp_path, monkeypatch, "* third format entry\n")
    report = audit_claims.AuditReport()
    audit_claims.check_roadmap_consistency(report)
    assert any(f.severity == audit_claims.Severity.WARN and "format drift" in f.message
               for f in report.findings)


def test_consistency_accepts_git_tag_as_evidence(tmp_path, monkeypatch):
    """A release tag matching the entry's version is shipped-evidence even
    when todo/archive carry nothing (PR + tag workflow clears todo.md)."""
    _roadmap(tmp_path, monkeypatch,
             "- **Tagged thing (v0.0.1)** [INFRA] -- shipped via PR. *(shipped 01/01/26)*\n")
    import subprocess as sp
    env = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}
    sp.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    sp.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "--allow-empty", "-q", "-m", "x"], cwd=tmp_path, check=True, env={**env})
    sp.run(["git", "tag", "v0.0.1"], cwd=tmp_path, check=True)
    report = audit_claims.AuditReport()
    audit_claims.check_roadmap_consistency(report)
    fails = [f for f in report.findings if f.severity == audit_claims.Severity.FAIL]
    assert not fails, [f.message for f in fails]


# ── discover_version: live formats + tag fallback (liveness audit B4) ──
# All three original strategies used dead formats, so the version was
# "unknown" on every run and the staleness check never exercised.

def test_discover_version_from_state_md(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_claims, "PROJECT_ROOT", tmp_path)
    (tmp_path / "STATE.md").write_text("# State\nDOE Starter Kit — current version: v2.3.4\n")
    assert audit_claims.discover_version() == "v2.3.4"


def test_discover_version_from_todo_ascii_arrow(tmp_path, monkeypatch):
    """The kit writes '->' in todo.md; the old regex matched only the
    unicode arrow."""
    monkeypatch.setattr(audit_claims, "PROJECT_ROOT", tmp_path)
    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks" / "todo.md").write_text(
        "## Current\n1. [x] Ship the thing -> v1.5.0\n")
    assert audit_claims.discover_version() == "v1.5.0"


def test_discover_version_from_roadmap_bullets(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_claims, "PROJECT_ROOT", tmp_path)
    (tmp_path / "ROADMAP.md").write_text(
        "## Complete\n- **Newest (v3.0.0)** [APP] -- x *(shipped 01/06/26)*\n"
        "- **Older (v2.9.0)** [APP] -- y *(shipped 01/05/26)*\n")
    assert audit_claims.discover_version() == "v3.0.0"


def test_discover_version_falls_back_to_git_tag(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_claims, "PROJECT_ROOT", tmp_path)
    import subprocess as sp
    sp.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    sp.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "--allow-empty", "-q", "-m", "x"], cwd=tmp_path, check=True)
    sp.run(["git", "tag", "v0.4.2"], cwd=tmp_path, check=True)
    assert audit_claims.discover_version() == "v0.4.2"


def test_discover_version_none_when_no_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_claims, "PROJECT_ROOT", tmp_path)
    assert audit_claims.discover_version() is None
