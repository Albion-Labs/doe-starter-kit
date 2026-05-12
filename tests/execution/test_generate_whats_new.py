"""Tests for execution/generate_whats_new.py."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "execution"))

import generate_whats_new as gwn


# ── Parser: hero + background blocks ─────────────────────────

def test_parses_hero_only():
    """Entry with only a hero block parses cleanly; background is None."""
    text = (
        "## v1.0.0 (2026-01-01)\n"
        "<!-- hero -->\n"
        "First release.\n"
        "<!-- /hero -->\n"
        "\n"
        "### Added\n"
        "- **path** — thing.\n"
    )
    entries = gwn.parse_changelog(text)
    assert len(entries) == 1
    assert entries[0]["version"] == "v1.0.0"
    assert entries[0]["hero"] == "First release."
    assert entries[0]["background"] is None


def test_parses_hero_and_background():
    """Hero followed by background block (with blank line between) parses both."""
    text = (
        "## v1.0.0 (2026-01-01)\n"
        "<!-- hero -->\n"
        "Headline change in three sentences.\n"
        "<!-- /hero -->\n"
        "\n"
        "<!-- background -->\n"
        "Why we made this decision and how the bug was caught.\n"
        "<!-- /background -->\n"
        "\n"
        "### Fixed\n"
        "- **path** — thing.\n"
    )
    entries = gwn.parse_changelog(text)
    assert len(entries) == 1
    assert entries[0]["hero"] == "Headline change in three sentences."
    assert entries[0]["background"] == "Why we made this decision and how the bug was caught."


def test_parses_background_without_hero():
    """Background block without a preceding hero is allowed (renders Background only)."""
    text = (
        "## v1.0.0 (2026-01-01)\n"
        "<!-- background -->\n"
        "Standalone background.\n"
        "<!-- /background -->\n"
        "\n"
        "### Added\n"
        "- **path** — thing.\n"
    )
    entries = gwn.parse_changelog(text)
    assert entries[0]["hero"] is None
    assert entries[0]["background"] == "Standalone background."


def test_no_hero_no_background():
    """Entry with neither block parses with both fields None."""
    text = (
        "## v1.0.0 (2026-01-01)\n"
        "### Added\n"
        "- **path** — thing.\n"
    )
    entries = gwn.parse_changelog(text)
    assert entries[0]["hero"] is None
    assert entries[0]["background"] is None


# ── Renderer: Summary / Background labels ────────────────────

def test_renderer_emits_summary_label_when_hero_present():
    """Every release with a hero gets a <h4 class=\"summary\">Summary</h4> heading."""
    entry = {
        "version": "v1.0.0",
        "date": "2026-01-01",
        "hero": "Headline.",
        "background": None,
        "subsections": [("Added", ["**path** — thing."])],
    }
    html = gwn.render_entry(entry)
    assert '<h4 class="summary">Summary</h4>' in html
    assert '<p class="release-hero">Headline.</p>' in html
    # No Background heading when background is absent
    assert '<h4 class="background">' not in html
    assert 'release-background' not in html


def test_renderer_emits_background_label_when_present():
    """Background block produces <h4 class=\"background\">Background</h4> + <p class=\"release-background\">."""
    entry = {
        "version": "v1.0.0",
        "date": "2026-01-01",
        "hero": "Headline.",
        "background": "Postmortem prose.",
        "subsections": [("Fixed", ["**path** — thing."])],
    }
    html = gwn.render_entry(entry)
    assert '<h4 class="summary">Summary</h4>' in html
    assert '<h4 class="background">Background</h4>' in html
    assert '<p class="release-background">Postmortem prose.</p>' in html
    # Order: summary -> hero -> background heading -> background paragraph
    summary_at = html.index('<h4 class="summary">')
    hero_at = html.index('release-hero')
    bg_heading_at = html.index('<h4 class="background">')
    bg_para_at = html.index('release-background')
    assert summary_at < hero_at < bg_heading_at < bg_para_at


def test_renderer_skips_summary_when_no_hero():
    """Compact releases (no hero) get no Summary label and no Background label."""
    entry = {
        "version": "v1.0.0",
        "date": "2026-01-01",
        "hero": None,
        "background": None,
        "subsections": [("Fixed", ["**path** — thing."])],
    }
    html = gwn.render_entry(entry)
    assert '<h4 class="summary">' not in html
    assert 'release-hero' not in html
    assert 'release-background' not in html


# ── Backwards compatibility ──────────────────────────────────

def test_existing_changelog_parses_without_error():
    """The real CHANGELOG.md must parse cleanly under the new parser."""
    changelog_path = PROJECT_ROOT / "CHANGELOG.md"
    text = changelog_path.read_text(encoding="utf-8")
    entries = gwn.parse_changelog(text)
    assert len(entries) > 100, f"Expected >100 releases, got {len(entries)}"
    # The current v1.63.0 entry should have a hero, no background.
    v_1_63_0 = next((e for e in entries if e["version"] == "v1.63.0"), None)
    assert v_1_63_0 is not None
    assert v_1_63_0["hero"] is not None
    assert v_1_63_0["background"] is None
