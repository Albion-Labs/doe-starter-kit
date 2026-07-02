#!/usr/bin/env python3
"""DOE Methodology Testing Framework.

Verifies that DOE rules are being followed across this project.
Runs scenario-based checks that report PASS / WARN / FAIL.

Usage:
    python3 execution/test_methodology.py              # run all scenarios
    python3 execution/test_methodology.py --help       # show this help
    python3 execution/test_methodology.py --list       # list all scenarios
    python3 execution/test_methodology.py --scenario <name>            # run one scenario
    python3 execution/test_methodology.py --scenario <name> --verbose  # verbose output
    python3 execution/test_methodology.py --quick      # fast subset (CI, no execution tests)
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── Colour helpers (plain fallback for CI) ───────────────────

def _fmt(text: str, code: str) -> str:
    """Apply ANSI colour code if stdout is a tty."""
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text

def _green(t): return _fmt(t, "32")
def _yellow(t): return _fmt(t, "33")
def _red(t): return _fmt(t, "31")
def _bold(t): return _fmt(t, "1")
def _dim(t): return _fmt(t, "2")


# ── Result builder ────────────────────────────────────────────

def _result(status: str, detail: str = "", verbose_lines: list = None):
    return {"status": status, "detail": detail, "verbose": verbose_lines or []}


# ════════════════════════════════════════════════════════════
# Scenario 1: session_start_discipline
# ════════════════════════════════════════════════════════════

def scenario_session_start_discipline(verbose: bool = False):
    """Check .tmp/.session-start exists (PASS if recent, WARN if stale/missing)."""
    marker = PROJECT_ROOT / ".tmp" / ".session-start"
    vlines = []
    if not marker.exists():
        vlines.append(f"  File not found: {marker.relative_to(PROJECT_ROOT)}")
        return _result("WARN", "no .tmp/.session-start found", vlines)

    try:
        mtime = datetime.fromtimestamp(marker.stat().st_mtime, tz=timezone.utc)
        age = datetime.now(timezone.utc) - mtime
        age_h = age.total_seconds() / 3600
        vlines.append(f"  File: {marker.relative_to(PROJECT_ROOT)}")
        vlines.append(f"  Age: {age_h:.1f} hours")
        if age > timedelta(hours=24):
            return _result("WARN", f"session-start marker is {age_h:.0f}h old (stale)", vlines)
        return _result("PASS", f"session-start marker is {age_h:.1f}h old", vlines)
    except OSError as e:
        return _result("WARN", f"cannot read marker: {e}", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 2: contract_completeness
# ════════════════════════════════════════════════════════════

_VALID_VERIFY_RE = re.compile(
    r"Verify:\s+(?:file:\s+.+?\s+exists|file:\s+.+?\s+contains\s+.+|run:\s+.+|html:\s+.+?\s+has\s+.+)"
)
_AUTO_CRITERION_RE = re.compile(r"-\s+\[[ x]\]\s+\[auto\]")
_STEP_LINE_RE = re.compile(r"^\d+\.\s+\[[ x]\]")
_CONTRACT_RE = re.compile(r"^\s*Contract:", re.IGNORECASE)


def scenario_contract_completeness(verbose: bool = False):
    """Scan tasks/todo.md for steps missing contracts, missing [auto] criteria, or invalid Verify: patterns.

    Only checks ## Current and ## Awaiting Sign-off sections.
    Skips ## Done (historical) and ## Queue (not started).
    """
    todo = PROJECT_ROOT / "tasks" / "todo.md"
    vlines = []
    if not todo.exists():
        return _result("WARN", "tasks/todo.md not found", vlines)

    lines = todo.read_text(encoding="utf-8").splitlines()

    # Only scan active sections (Current, Awaiting Sign-off)
    _ACTIVE_SECTIONS = {"## current", "## awaiting sign-off"}
    _SKIP_SECTIONS = {"## done", "## queue", "## pending prs"}
    in_active_section = False

    total_steps = 0
    steps_with_contract = 0
    steps_with_auto = 0
    valid_verify_count = 0
    issues = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped_lower = line.strip().lower()
        if stripped_lower.startswith("## "):
            section_key = stripped_lower.split("(")[0].strip()
            if any(section_key.startswith(s) for s in _ACTIVE_SECTIONS):
                in_active_section = True
            elif any(section_key.startswith(s) for s in _SKIP_SECTIONS):
                in_active_section = False
        if in_active_section and _STEP_LINE_RE.match(line.strip()):
            total_steps += 1
            step_text = line.strip()[:60]
            # Scan ahead for Contract block
            has_contract = False
            has_auto = False
            has_valid_verify = False
            j = i + 1
            while j < len(lines):
                ahead = lines[j]
                stripped = ahead.strip()
                # Stop at next step
                if _STEP_LINE_RE.match(stripped):
                    break
                if _CONTRACT_RE.match(stripped):
                    has_contract = True
                if _AUTO_CRITERION_RE.search(stripped):
                    has_auto = True
                if _VALID_VERIFY_RE.search(stripped):
                    has_valid_verify = True
                    valid_verify_count += 1
                j += 1

            if has_contract:
                steps_with_contract += 1
            else:
                issues.append(f"  Missing Contract: on step: {step_text}")

            if has_auto:
                steps_with_auto += 1
            elif has_contract:
                issues.append(f"  Contract has no [auto] criteria: {step_text}")
        i += 1

    vlines.append(f"  Total steps: {total_steps}")
    vlines.append(f"  Steps with Contract block: {steps_with_contract}/{total_steps}")
    vlines.append(f"  Steps with [auto] criteria: {steps_with_auto}/{total_steps}")
    vlines.append(f"  Valid Verify: patterns found: {valid_verify_count}")
    for issue in issues[:10]:
        vlines.append(issue)
    if len(issues) > 10:
        vlines.append(f"  ...and {len(issues) - 10} more issues")

    if total_steps == 0:
        return _result("PASS", "no steps found in todo.md (nothing to check)", vlines)

    if steps_with_contract == total_steps and steps_with_auto == total_steps:
        return _result(
            "PASS",
            f"{total_steps}/{total_steps} steps have valid contracts",
            vlines,
        )

    missing = total_steps - steps_with_contract
    return _result(
        "WARN",
        f"{steps_with_contract}/{total_steps} steps have contracts ({missing} missing)",
        vlines,
    )


# ════════════════════════════════════════════════════════════
# Scenario 3: learnings_freshness
# ════════════════════════════════════════════════════════════

def scenario_learnings_freshness(verbose: bool = False):
    """Check learnings.md for recent entries; warn if last 5 retros were all [quick: nothing to log]."""
    learnings = PROJECT_ROOT / "learnings.md"
    vlines = []

    # Parse git log for retro commits
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--all", "--grep=retro", "-20"],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=10,
        )
        retro_commits = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        retro_commits = []

    vlines.append(f"  Retro commits found: {len(retro_commits)}")
    for c in retro_commits[:5]:
        vlines.append(f"    {c[:80]}")

    # Check for quick-retro drift: last 5 retros all "nothing to log"
    nothing_count = sum(
        1 for c in retro_commits[:5]
        if "nothing to log" in c.lower()
    )
    vlines.append(f"  'nothing to log' in last 5 retros: {nothing_count}/5")

    # Check learnings.md freshness
    if not learnings.exists():
        vlines.append("  learnings.md: not found")
        return _result("WARN", "learnings.md not found", vlines)

    try:
        content = learnings.read_text(encoding="utf-8")
        # Count entries — look for bullet points or sections after headings
        entry_count = len(re.findall(r"^[-*]\s+\S", content, re.MULTILINE))
        vlines.append(f"  learnings.md entries (approx): {entry_count}")
    except OSError as e:
        vlines.append(f"  learnings.md read error: {e}")

    if nothing_count >= 5 and len(retro_commits) >= 5:
        return _result(
            "WARN",
            f"last {nothing_count}/5 retros were 'nothing to log' — possible retro drift",
            vlines,
        )

    return _result("PASS", "learnings freshness looks healthy", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 4: rationalisation_coverage
# ════════════════════════════════════════════════════════════

def scenario_rationalisation_coverage(verbose: bool = False):
    """Check that every YOU MUST / YOU MUST NOT rule in CLAUDE.md has a matching entry in rationalisation-tables.md."""
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    rat_tables = PROJECT_ROOT / "directives" / "rationalisation-tables.md"
    vlines = []

    if not claude_md.exists():
        return _result("WARN", "CLAUDE.md not found", vlines)

    claude_text = claude_md.read_text(encoding="utf-8")
    must_rules = re.findall(r"YOU MUST(?:\s+NOT)?\s+[A-Za-z].*", claude_text)
    vlines.append(f"  YOU MUST / YOU MUST NOT rules in CLAUDE.md: {len(must_rules)}")

    if not rat_tables.exists():
        vlines.append("  rationalisation-tables.md: not found")
        return _result("WARN", "rationalisation-tables.md not found — cannot assess coverage", vlines)

    rat_text = rat_tables.read_text(encoding="utf-8").lower()
    matched = 0
    unmatched = []

    for rule in must_rules:
        # Extract 3-5 key words from the rule to check coverage
        words = re.findall(r"\b[a-zA-Z]{4,}\b", rule.lower())[:5]
        if len(words) < 2:
            matched += 1  # too short to check meaningfully
            continue
        # Check if at least 2 of the key words appear near each other in rat_tables
        found = sum(1 for w in words if w in rat_text)
        if found >= 2:
            matched += 1
        else:
            unmatched.append(rule[:80])

    total = len(must_rules)
    if total == 0:
        return _result("PASS", "no YOU MUST rules found (nothing to check)", vlines)

    pct = (matched / total) * 100
    vlines.append(f"  Matched: {matched}/{total} ({pct:.0f}%)")
    for u in unmatched[:5]:
        vlines.append(f"  Unmatched: {u}")
    if len(unmatched) > 5:
        vlines.append(f"  ...and {len(unmatched) - 5} more")

    if pct >= 70:
        return _result("PASS", f"{matched}/{total} rules covered ({pct:.0f}%)", vlines)
    return _result("WARN", f"only {pct:.0f}% coverage ({matched}/{total}) — below 70% threshold", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 5: trigger_completeness
# ════════════════════════════════════════════════════════════

def scenario_trigger_completeness(verbose: bool = False):
    """Check that every directive file has at least one trigger in CLAUDE.md."""
    directives_dir = PROJECT_ROOT / "directives"
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    vlines = []

    if not directives_dir.exists():
        return _result("WARN", "directives/ directory not found", vlines)
    if not claude_md.exists():
        return _result("WARN", "CLAUDE.md not found", vlines)

    claude_text = claude_md.read_text(encoding="utf-8").lower()

    # Collect directive files (exclude _TEMPLATE.md and subdirectories)
    directives = [
        f for f in directives_dir.iterdir()
        if f.is_file() and f.suffix == ".md" and not f.name.startswith("_")
    ]
    vlines.append(f"  Directive files: {len(directives)}")

    covered = []
    uncovered = []
    for d in sorted(directives):
        stem = d.stem.lower()
        # Check if the file's stem or name appears in CLAUDE.md
        if stem in claude_text or d.name.lower() in claude_text:
            covered.append(d.name)
        else:
            uncovered.append(d.name)

    total = len(directives)
    if total == 0:
        return _result("PASS", "no directive files found (nothing to check)", vlines)

    pct = (len(covered) / total) * 100
    vlines.append(f"  With triggers: {len(covered)}/{total} ({pct:.0f}%)")
    for u in uncovered:
        vlines.append(f"  No trigger: {u}")

    if pct >= 70:
        return _result("PASS", f"{len(covered)}/{total} directives have triggers ({pct:.0f}%)", vlines)
    return _result("WARN", f"only {pct:.0f}% of directives have triggers ({len(covered)}/{total})", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 6: review_discipline
# ════════════════════════════════════════════════════════════

def scenario_review_discipline(verbose: bool = False):
    """Check git log for features that shipped without review evidence."""
    vlines = []

    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-30"],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=10,
        )
        commits = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return _result("PASS", "git unavailable — skipping (informational)", vlines)

    # Look for review-related commits. "merge" is deliberately NOT a keyword:
    # on a PR-workflow repo every 'Merge pull request' commit would count as
    # review evidence, making the no-review WARN unfalsifiable (audit B8).
    review_keywords = ["review", "snagging", "audit", "adversarial", "diff-review", "pr:"]
    review_commits = [
        c for c in commits
        if any(kw in c.lower() for kw in review_keywords)
    ]
    feature_commits = [
        c for c in commits
        if any(kw in c.lower() for kw in ["feature", "add", "build", "implement", "complete"])
    ]

    vlines.append(f"  Last 30 commits checked")
    vlines.append(f"  Feature-related commits: {len(feature_commits)}")
    vlines.append(f"  Review-related commits: {len(review_commits)}")
    for c in review_commits[:3]:
        vlines.append(f"    {c[:80]}")

    # If there are many feature commits but no review commits, warn
    if len(feature_commits) > 5 and len(review_commits) == 0:
        return _result(
            "WARN",
            f"{len(feature_commits)} feature commits but no review evidence in last 30 commits",
            vlines,
        )

    return _result("PASS", "review discipline looks healthy (informational check)", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 8: claude_md_quality
# ════════════════════════════════════════════════════════════

def scenario_claude_md_quality(verbose: bool = False):
    """Score CLAUDE.md against a DOE methodology quality rubric.

    Two-tier scoring: DOE Methodology (60 pts) checks structural compliance
    with DOE principles; Content Quality (40 pts) checks that the content is
    useful regardless of language or framework.  All checks are structural --
    no hardcoded tool names -- so any tech stack scores fairly.
    """
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    vlines = []

    if not claude_md.exists():
        return _result("WARN", "CLAUDE.md not found", vlines)

    text = claude_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    total_lines = len(lines)

    # Extract code blocks once for reuse
    code_blocks = re.findall(r"```[^\n]*\n(.*?)```", text, re.DOTALL)

    scores = {}

    # ── Tier 1: DOE Methodology (60 pts) ──────────────────────

    # 1. DOE Architecture (15 pts): explains the DOE layer split
    arch = 0
    doe_terms = ["directive", "orchestration", "execution"]
    doe_hits = sum(1 for t in doe_terms if re.search(rf"\b{t}\b", text, re.IGNORECASE))
    if doe_hits >= 3:
        arch += 10
    elif doe_hits >= 2:
        arch += 7
    elif doe_hits >= 1:
        arch += 3
    # References to DOE directories (backtick-quoted or in code blocks)
    doe_dirs = ["directives/", "execution/", "tasks/"]
    dir_hits = sum(1 for d in doe_dirs if d in text)
    arch += min(5, dir_hits * 2)
    scores["DOE Architecture"] = min(15, arch)

    # 2. Directory Structure (10 pts): project layout documented
    dir_score = 0
    if re.search(r"##\s+Directory\s+Structure", text, re.IGNORECASE):
        dir_score += 5
    elif any(re.search(r"(?:src/|app/|lib/|directives/)", b) for b in code_blocks):
        dir_score += 3  # structure shown in code blocks but no dedicated section
    path_refs = len(re.findall(r"`[a-zA-Z0-9_./-]+/[a-zA-Z0-9_./-]*`", text))
    dir_score += min(5, path_refs // 2)
    scores["Directory Structure"] = min(10, dir_score)

    # 3. Trigger Routing (15 pts): topics route to directive files
    trigger_score = 0
    if re.search(r"##\s+Triggers?", text, re.IGNORECASE):
        trigger_score += 5
    # Lines with -> pointing to a path (any file, not just directives/)
    trigger_lines = [l for l in lines if re.search(r"->\s*.*[/.]", l)]
    trigger_score += min(5, len(trigger_lines) // 2)
    # Referenced directive files exist on disk
    directive_refs = re.findall(r"`(directives/[^`]+)`", text)
    if directive_refs:
        existing = sum(1 for f in directive_refs if (PROJECT_ROOT / f).exists())
        trigger_score += int((existing / len(directive_refs)) * 5)
    elif trigger_lines:
        trigger_score += 2  # triggers exist but don't use backtick refs
    scores["Trigger Routing"] = min(15, trigger_score)

    # 4. Commands Section (10 pts): has a commands area with code blocks
    cmd_score = 0
    if re.search(r"##\s+(?:Common\s+)?Commands|##\s+Usage|##\s+Getting\s+Started", text, re.IGNORECASE):
        cmd_score += 5
    if code_blocks:
        cmd_score += 3
    multi_line_blocks = sum(1 for b in code_blocks if len(b.strip().splitlines()) >= 2)
    if multi_line_blocks:
        cmd_score += 2
    scores["Commands Section"] = min(10, cmd_score)

    # 5. Operational Knowledge (10 pts): gotchas, warnings, edge cases
    ops_score = 0
    if re.search(r"##\s+(?:Gotchas|Edge\s+Cases|Warnings|Caveats|Troubleshooting)", text, re.IGNORECASE):
        ops_score += 5
    # Structured warning markers (bold labels)
    markers = re.findall(
        r"\*\*(?:Warning|Caveat|Workaround|Note|Important|Caution)\s*[:*]",
        text, re.IGNORECASE,
    )
    ops_score += min(5, len(markers))
    scores["Operational Knowledge"] = min(10, ops_score)

    # ── Tier 2: Content Quality (40 pts) ──────────────────────

    # 6. Executable Commands (10 pts): code blocks contain real commands
    #    Structural: any line with 2+ tokens that isn't a comment counts.
    #    Catches `cargo test`, `go build`, `python3 -m pytest`, etc.
    #    Skips directory-listing lines (first token ends with `/`).
    cmd_lines = []
    for block in code_blocks:
        for bline in block.strip().splitlines():
            stripped = bline.strip()
            if not stripped or stripped.startswith("#"):
                continue
            first_token = stripped.split()[0]
            if first_token.endswith("/"):
                continue  # directory listing, not a command
            if re.match(r"\S+\s+\S+", stripped):
                cmd_lines.append(stripped)
    if len(cmd_lines) >= 6:
        exec_pts = 10
    elif len(cmd_lines) >= 3:
        exec_pts = 7
    elif len(cmd_lines) >= 1:
        exec_pts = 4
    else:
        exec_pts = 0
    scores["Executable Commands"] = exec_pts

    # 7. Conciseness (10 pts): density vs bloat
    long_lines = sum(1 for l in lines if len(l) > 200)
    long_penalty = min(6, long_lines)
    if total_lines > 0:
        density = sum(1 for l in lines if l.strip()) / total_lines
        density_pts = int(density * 6)
    else:
        density_pts = 0
    scores["Conciseness"] = max(0, min(10, density_pts + 4 - long_penalty))

    # 8. Currency (10 pts): referenced file paths exist on disk
    referenced_files = re.findall(r"`([a-zA-Z0-9_./-]+\.[a-zA-Z]{2,5})`", text)
    if referenced_files:
        existing = sum(1 for f in referenced_files if (PROJECT_ROOT / f).exists())
        scores["Currency"] = int((existing / len(referenced_files)) * 10)
    else:
        scores["Currency"] = 5  # neutral if no file refs

    # 9. Actionability (10 pts): commands have specific paths, flags, arguments
    actionable = 0
    for block in code_blocks:
        for bline in block.strip().splitlines():
            stripped = bline.strip()
            if not stripped or stripped.startswith("#"):
                continue
            first_token = stripped.split()[0]
            if first_token.endswith("/"):
                continue  # directory listing, not a command
            if re.search(r"[/][\w.]|--\w|-\w|\.\w+\b", stripped):
                actionable += 1
    if actionable >= 5:
        action_pts = 10
    elif actionable >= 3:
        action_pts = 7
    elif actionable >= 1:
        action_pts = 4
    else:
        action_pts = 0
    scores["Actionability"] = action_pts

    # ── Grade ─────────────────────────────────────────────────

    total = sum(scores.values())
    if total >= 90:
        grade = "A"
    elif total >= 70:
        grade = "B"
    elif total >= 50:
        grade = "C"
    elif total >= 30:
        grade = "D"
    else:
        grade = "F"

    # ── Display ───────────────────────────────────────────────

    max_map = {
        "DOE Architecture": 15, "Directory Structure": 10, "Trigger Routing": 15,
        "Commands Section": 10, "Operational Knowledge": 10,
        "Executable Commands": 10, "Conciseness": 10, "Currency": 10, "Actionability": 10,
    }
    tier1 = ["DOE Architecture", "Directory Structure", "Trigger Routing",
             "Commands Section", "Operational Knowledge"]
    tier2 = ["Executable Commands", "Conciseness", "Currency", "Actionability"]

    vlines.append(f"  Grade {grade} ({total:.0f}/100)")
    vlines.append("")
    vlines.append("  DOE Methodology (60 pts)")
    for name in tier1:
        pts = scores[name]
        limit = max_map[name]
        bar_full = int((pts / limit) * 10)
        bar = "█" * bar_full + "░" * (10 - bar_full)
        vlines.append(f"  {bar} {name}: {pts:.0f}/{limit} pts")
    vlines.append("")
    vlines.append("  Content Quality (40 pts)")
    for name in tier2:
        pts = scores[name]
        limit = max_map[name]
        bar_full = int((pts / limit) * 10)
        bar = "█" * bar_full + "░" * (10 - bar_full)
        vlines.append(f"  {bar} {name}: {pts:.0f}/{limit} pts")

    # DOE-prescriptive suggestions
    _suggestions = {
        "DOE Architecture":     "explain the directive/orchestration/execution split and reference DOE directories",
        "Directory Structure":  "add a directory structure section so Claude can navigate your project",
        "Trigger Routing":      "add triggers routing topics to directive files -- enables context-first architecture",
        "Commands Section":     "add a commands section with build/test/deploy code blocks for your stack",
        "Operational Knowledge": "document gotchas and edge cases that would trip up Claude in your project",
        "Executable Commands":  "make code blocks copy-paste ready with real commands for your stack",
        "Conciseness":          "break lines >200 chars, move detail to directives",
        "Currency":             "fix references to renamed/deleted files",
        "Actionability":        "add specific paths and flags to commands so they work without modification",
    }
    suggestions = []
    for name, pts in scores.items():
        limit = max_map[name]
        if pts < limit - 0.5:
            gap = limit - pts
            suggestions.append(f"  +{gap:.0f} {name}: {_suggestions[name]}")

    if suggestions:
        vlines.append("")
        vlines.append("  Suggestions:")
        vlines.extend(suggestions)

    if grade in ("A", "B"):
        return _result("PASS", f"CLAUDE.md quality grade {grade} ({total:.0f}/100)", vlines)
    elif grade == "C":
        return _result("WARN", f"CLAUDE.md quality grade {grade} ({total:.0f}/100) -- below B threshold", vlines)
    return _result("FAIL", f"CLAUDE.md quality grade {grade} ({total:.0f}/100) -- needs attention", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 9: execution_script_tests
# ════════════════════════════════════════════════════════════

def scenario_execution_script_tests(verbose: bool = False):
    """Run pytest against tests/execution/ and report results."""
    tests_dir = PROJECT_ROOT / "tests" / "execution"
    vlines = []

    if not tests_dir.exists():
        return _result("WARN", "tests/execution/ not found — create it to enable this scenario", vlines)

    # Prefer project venv if present (PEP 668 blocks system-Python pip installs on
    # Homebrew). Falls back to sys.executable so CI and fresh checkouts still work.
    venv_python = PROJECT_ROOT / ".venv" / "bin" / "python3"
    python_bin = str(venv_python) if venv_python.exists() else sys.executable

    try:
        result = subprocess.run(
            [python_bin, "-m", "pytest", str(tests_dir), "--tb=short", "-q"],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=120,
        )
        output_lines = (result.stdout + result.stderr).splitlines()
        vlines.extend([f"  {l}" for l in output_lines[:40]])

        # Parse pytest summary line
        summary_match = re.search(
            r"(\d+) passed(?:, (\d+) warning)?(?:, (\d+) skipped)?(?:, (\d+) failed)?",
            result.stdout + result.stderr,
        )
        failed_match = re.search(r"(\d+) failed", result.stdout + result.stderr)
        skipped_match = re.search(r"(\d+) skipped", result.stdout + result.stderr)

        passed = int(summary_match.group(1)) if summary_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        skipped = int(skipped_match.group(1)) if skipped_match else 0

        if result.returncode == 0:
            if skipped > 0:
                return _result(
                    "WARN",
                    f"{passed} passed, {skipped} skipped — some tests were skipped",
                    vlines,
                )
            return _result("PASS", f"{passed} passed", vlines)
        elif failed > 0:
            return _result(
                "FAIL",
                f"{failed} failed, {passed} passed",
                vlines,
            )
        else:
            # Non-zero exit but no "failed" found — collection error or crash
            return _result("FAIL", f"pytest exited {result.returncode}", vlines)

    except subprocess.TimeoutExpired:
        return _result("FAIL", "pytest timed out after 120s", vlines)
    except FileNotFoundError:
        return _result("WARN", "pytest not installed — skipping", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 10: router_coverage
# ════════════════════════════════════════════════════════════

def scenario_router_coverage(verbose: bool = False):
    """Check that CLAUDE.md triggers cover all directive files in directives/."""
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    directives_dir = PROJECT_ROOT / "directives"
    vlines = []

    if not claude_md.exists():
        return _result("WARN", "CLAUDE.md not found", vlines)
    if not directives_dir.exists():
        return _result("WARN", "directives/ not found", vlines)

    triggers_text = claude_md.read_text(encoding="utf-8")

    all_directives = []
    for p in directives_dir.rglob("*.md"):
        if p.name.startswith("_"):
            continue
        all_directives.append(p)

    # Build set of referenced directories (e.g. "directives/adversarial-review/")
    dir_refs = set(re.findall(r"`(directives/[^`]+/)`", triggers_text))

    covered = []
    uncovered = []
    for d in sorted(all_directives):
        rel = str(d.relative_to(PROJECT_ROOT))
        # Direct reference check
        if rel in triggers_text or d.stem in triggers_text or d.name in triggers_text:
            covered.append(rel)
        # Parent directory reference check (e.g. file inside directives/adversarial-review/)
        elif any(rel.startswith(dr) for dr in dir_refs):
            covered.append(rel)
        else:
            uncovered.append(rel)

    total = len(all_directives)
    vlines.append(f"  Total directive files: {total}")
    vlines.append(f"  Referenced in CLAUDE.md: {len(covered)}")
    for u in uncovered:
        vlines.append(f"  Missing trigger: {u}")

    if total == 0:
        return _result("PASS", "no directive files found", vlines)

    pct = len(covered) / total * 100
    if pct >= 80:
        return _result("PASS", f"{len(covered)}/{total} directives routed ({pct:.0f}%)", vlines)
    return _result("WARN", f"only {pct:.0f}% of directives routed ({len(covered)}/{total})", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 11: rule_completeness
# ════════════════════════════════════════════════════════════

def scenario_rule_completeness(verbose: bool = False):
    """Check that Core Behaviour rules in CLAUDE.md have corresponding directive coverage."""
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    vlines = []

    if not claude_md.exists():
        return _result("WARN", "CLAUDE.md not found", vlines)

    text = claude_md.read_text(encoding="utf-8")
    rules = re.findall(r"^\d+\.\s+\*\*(.+?)\.\*\*", text, re.MULTILINE)
    vlines.append(f"  Core Behaviour rules found: {len(rules)}")

    if not rules:
        return _result("WARN", "no Core Behaviour rules found in CLAUDE.md", vlines)

    rules_with_pointers = 0
    for rule in rules:
        rule_section = text[text.find(rule):text.find(rule) + 200]
        if "directives/" in rule_section or "->" in rule_section:
            rules_with_pointers += 1
        else:
            vlines.append(f"  No directive pointer: {rule[:50]}")

    pct = rules_with_pointers / len(rules) * 100
    vlines.append(f"  Rules with directive pointers: {rules_with_pointers}/{len(rules)} ({pct:.0f}%)")

    if pct >= 80:
        return _result("PASS", f"{rules_with_pointers}/{len(rules)} rules have directive pointers", vlines)
    return _result("WARN", f"only {pct:.0f}% rules have directive pointers", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 12: scale_consistency
# ════════════════════════════════════════════════════════════

def scenario_scale_consistency(verbose: bool = False):
    """Check that directives mentioning scale modes use consistent section headings."""
    directives_dir = PROJECT_ROOT / "directives"
    vlines = []

    if not directives_dir.exists():
        return _result("WARN", "directives/ not found", vlines)

    scale_terms = ["solo", "informal parallel", "formal parallel"]
    expected_headings = {"solo", "informal parallel", "formal parallel"}

    files_with_scale = []
    checked = 0
    inconsistent = []

    for d in sorted(directives_dir.rglob("*.md")):
        text = d.read_text(encoding="utf-8").lower()
        mentions = [t for t in scale_terms if t in text]
        if len(mentions) >= 2:
            files_with_scale.append(d.name)
            headings = set()
            for h in expected_headings:
                if f"## {h}" in text or f"### {h}" in text:
                    headings.add(h)
            # Only files that USE scale headings are comparable; the rest
            # merely discuss scale in prose and have nothing to check.
            if headings:
                checked += 1
                if headings != expected_headings:
                    missing = expected_headings - headings
                    inconsistent.append(f"{d.name}: missing headings {missing}")

    vlines.append(f"  Files discussing scale: {len(files_with_scale)}")
    for f in files_with_scale:
        vlines.append(f"    {f}")
    for i in inconsistent:
        vlines.append(f"  Inconsistent: {i}")

    if inconsistent:
        return _result("WARN", f"{len(inconsistent)} files with inconsistent scale headings", vlines)
    # Honest coverage label (liveness audit B8): the heading comparison only
    # applies to files that have scale headings at all — claiming all
    # scale-DISCUSSING files "use consistent terminology" overstated the check.
    return _result(
        "PASS",
        f"{checked} of {len(files_with_scale)} scale-discussing files have "
        "headings to compare — all consistent",
        vlines,
    )


# ════════════════════════════════════════════════════════════
# Scenario 14: directive_schema
# ════════════════════════════════════════════════════════════

def scenario_directive_schema(verbose: bool = False):
    """Check that directive files follow the required schema: Goal section, When to Use trigger."""
    directives_dir = PROJECT_ROOT / "directives"
    vlines = []

    if not directives_dir.exists():
        return _result("WARN", "directives/ not found", vlines)

    required_sections = {
        "goal": re.compile(r"^##\s+Goal", re.MULTILINE | re.IGNORECASE),
        "trigger": re.compile(r"^##\s+When to Use", re.MULTILINE | re.IGNORECASE),
    }
    _SCHEMA_SKIP = {"spec-reviewer.md", "code-quality-reviewer.md", "implementer-prompt.md"}

    total = 0
    issues = []

    for d in sorted(directives_dir.rglob("*.md")):
        if d.name.startswith("_") or d.name in _SCHEMA_SKIP:
            continue
        total += 1
        text = d.read_text(encoding="utf-8")
        rel = str(d.relative_to(PROJECT_ROOT))

        for section_name, pattern in required_sections.items():
            if not pattern.search(text):
                issues.append(f"{rel}: missing '## {section_name.title()}' section")
                vlines.append(f"  {rel}: missing {section_name}")

    vlines.insert(0, f"  Directives checked: {total}")
    vlines.insert(1, f"  Required sections: Goal, When to Use (trigger)")
    vlines.insert(2, f"  Schema issues: {len(issues)}")

    if not issues:
        return _result("PASS", f"all {total} directives have Goal + When to Use sections", vlines)
    return _result("WARN", f"{len(issues)} schema issue(s) in {total} directives", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 15: cross_reference_consistency
# ════════════════════════════════════════════════════════════

import os as _os

def scenario_cross_reference_consistency(verbose: bool = False):
    """Validate that directive cross-references and CLAUDE.md triggers point to real files.

    Handles:
    - Forward references: files from uncompleted todo.md steps are exempt.
    - Glob patterns: paths containing * are skipped (not resolvable).
    - Global paths: .claude/ paths also checked at ~/.claude/ (global install).
    - Layer-conditional: directives/ refs checked in kit as fallback (may be
      from a different capability layer that isn't active in this project).
    """
    vlines = []

    # Collect forward-reference exempt files (from uncompleted steps in todo.md)
    exempt_files = set()
    step_re = re.compile(r"^\d+\.\s+\[[ x]\]")
    owns_re = re.compile(r"^\s+Owns:\s*(.+)$", re.IGNORECASE)
    todo = PROJECT_ROOT / "tasks" / "todo.md"
    if todo.exists():
        todo_text = todo.read_text(encoding="utf-8")
        in_uncompleted = False
        for line in todo_text.splitlines():
            step_match = step_re.match(line.strip())
            if step_match:
                in_uncompleted = "[ ]" in line
            if in_uncompleted:
                owns_match = owns_re.match(line)
                if owns_match:
                    for f in owns_match.group(1).split(","):
                        exempt_files.add(f.strip())

    # Kit directory (fallback for layer-conditional directive refs)
    kit_dir = Path(_os.path.expanduser("~/doe-starter-kit"))

    vlines.append(f"  Forward-reference exempt files: {len(exempt_files)}")

    def _ref_exists(ref):
        """Check if a reference resolves to a real path."""
        if "*" in ref:
            return True  # Glob patterns can't be resolved
        # Project-relative
        if (PROJECT_ROOT / ref).exists():
            return True
        # Home-relative (.claude/ -> ~/.claude/)
        if ref.startswith(".claude/"):
            home_path = Path.home() / ref
            if home_path.exists():
                return True
        # Tilde-expanded
        expanded = Path(_os.path.expanduser(ref))
        if expanded.exists():
            return True
        # Layer-conditional: directive exists in the kit but not this project
        if ref.startswith("directives/") and kit_dir.exists():
            kit_path = kit_dir / ref
            if kit_path.exists():
                return True
        return False

    # Check CLAUDE.md trigger references
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    issues = []

    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8")
        refs = re.findall(r"`((?:directives|execution|\.claude)/[^`]+)`", text)
        for ref in refs:
            if ref not in exempt_files and not _ref_exists(ref):
                issues.append(f"CLAUDE.md references missing file: {ref}")
                vlines.append(f"  Missing: {ref} (from CLAUDE.md)")

    # Check directive cross-references (skip templates)
    directives_dir = PROJECT_ROOT / "directives"
    if directives_dir.exists():
        for d in sorted(directives_dir.rglob("*.md")):
            if d.name.startswith("_"):
                continue
            text = d.read_text(encoding="utf-8")
            refs = re.findall(r"`((?:directives|execution|\.claude)/[^`]+)`", text)
            for ref in refs:
                if ref not in exempt_files and not _ref_exists(ref):
                    rel = str(d.relative_to(PROJECT_ROOT))
                    issues.append(f"{rel} references missing file: {ref}")
                    vlines.append(f"  Missing: {ref} (from {rel})")

    vlines.insert(1, f"  Cross-reference issues: {len(issues)}")

    if not issues:
        return _result("PASS", "all cross-references resolve", vlines)
    return _result("WARN", f"{len(issues)} broken cross-reference(s)", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 16: agent_definition_integrity
# ════════════════════════════════════════════════════════════

def scenario_agent_definition_integrity(verbose: bool = False):
    """Validate agent files match their README claims (tool lists, scoring)."""
    agents_dir = PROJECT_ROOT / ".claude" / "agents"
    readme = PROJECT_ROOT / "directives" / "adversarial-review" / "README.md"
    vlines = []

    if not agents_dir.exists():
        return _result("WARN", ".claude/agents/ not found", vlines)

    agent_files = sorted(agents_dir.glob("*.md"))
    vlines.append(f"  Agent files found: {len(agent_files)}")

    issues = []

    for af in agent_files:
        text = af.read_text(encoding="utf-8")
        name = af.stem

        tools_match = re.search(r"^tools:\s*(.+)$", text, re.MULTILINE)
        if not tools_match:
            issues.append(f"{name}: missing tools: line in frontmatter")
            continue

        tools = [t.strip() for t in tools_match.group(1).split(",")]
        vlines.append(f"  {name}: tools = {', '.join(tools)}")

        if name in ("Finder", "Adversarial", "Referee", "ReadOnly"):
            if "Edit" in tools or "Write" in tools:
                issues.append(f"{name}: has Edit/Write — should be read-only")

    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8")
        for role in ("Finder", "Adversarial", "Referee"):
            af = agents_dir / f"{role}.md"
            if not af.exists():
                issues.append(f"README references {role} but agent file missing")
                continue
            agent_text = af.read_text(encoding="utf-8")
            if role == "Adversarial":
                if "-1x" not in agent_text and "dismissing" not in agent_text.lower():
                    issues.append(f"{role}: missing -1x dismissal penalty (README claims it)")

    if not issues:
        return _result("PASS", f"all {len(agent_files)} agent definitions are consistent", vlines)
    return _result("WARN", f"{len(issues)} agent integrity issue(s)", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 17: plan_vs_actual
# ════════════════════════════════════════════════════════════

def scenario_plan_vs_actual(verbose: bool = False):
    """For completed features, verify plan deliverables exist on disk.

    Structural only — checks files exist, not semantic intent.
    Only checks features in ROADMAP.md ## Complete.
    """
    roadmap = PROJECT_ROOT / "ROADMAP.md"
    plans_dir = PROJECT_ROOT / ".claude" / "plans"
    vlines = []

    if not roadmap.exists():
        return _result("PASS", "no ROADMAP.md — nothing to check", vlines)
    if not plans_dir.exists():
        return _result("PASS", "no .claude/plans/ — nothing to check", vlines)

    roadmap_text = roadmap.read_text(encoding="utf-8")
    complete_match = re.search(r"^## Complete\b.*?\n(.*?)(?=^## |\Z)", roadmap_text, re.MULTILINE | re.DOTALL)
    if not complete_match:
        return _result("PASS", "no ## Complete section in ROADMAP.md", vlines)

    complete_text = complete_match.group(1)
    # Live format: "- **Name (vX.Y.Z)** [TAG] -- ..." bullets; legacy: "### Name (vX.Y.Z)"
    # headings. Liveness audit B2: only the legacy form was parsed, so the scenario
    # checked 0 features on every modern ROADMAP and passed vacuously.
    completed_features = re.findall(r"^###\s+(.+?)(?:\s+\(|$)", complete_text, re.MULTILINE)
    completed_features += re.findall(
        r"^-\s+\*\*(.+?)(?:\s+\(v\d+\.\d+\.\d+\))?\*\*", complete_text, re.MULTILINE
    )
    vlines.append(f"  Completed features in ROADMAP: {len(completed_features)}")

    body = re.sub(r"<!--.*?-->", "", complete_text, flags=re.DOTALL).strip()
    if body and not completed_features:
        return _result(
            "WARN",
            "## Complete has content but 0 entries parsed — ROADMAP format drift "
            "(this scenario is blind until parser and file agree)",
            vlines,
        )

    issues = []
    checked = 0

    for feature in completed_features:
        safe_name = re.sub(r"[^a-z0-9-]", "-", feature.lower().strip())
        candidates = list(plans_dir.glob(f"*{safe_name[:20]}*"))
        if not candidates:
            continue
        checked += 1
        plan_file = candidates[0]
        plan_text = plan_file.read_text(encoding="utf-8")
        file_refs = re.findall(r"`((?:execution|directives|\.claude|src)/[^`]+\.\w+)`", plan_text)
        missing = [f for f in file_refs if not (PROJECT_ROOT / f).exists()]
        if missing:
            issues.append(f"{feature}: {len(missing)} deliverable(s) missing")
            for m in missing[:3]:
                vlines.append(f"  Missing: {m} (plan: {plan_file.name})")

    vlines.append(f"  Plans checked: {checked}")

    if not issues:
        return _result(
            "PASS",
            f"parsed {len(completed_features)} Complete entries, checked {checked} "
            "with plan files — all referenced deliverables exist",
            vlines,
        )
    return _result("WARN", f"{len(issues)} feature(s) have missing deliverables", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 18: non_political_layers_domain_neutral
# ════════════════════════════════════════════════════════════

# Electoral/political domain terms that must NOT appear in any NON-political layer.
# This content (electoral register, PPERA, canvass, etc.) belongs ONLY in the opt-in
# `political` layer, so a project that isn't a political campaign never inherits it.
# Word-boundaried so "selector" (electoral) and "constituent" (constituency) do not
# false-positive. "political opinion" is deliberately NOT a term — it's a legitimate
# generic GDPR special-category example.
_DOMAIN_LEAK_RE = re.compile(
    r"\belectoral\b|\bppera\b|\bcanvass\w*|\bconstituenc\w*"
    r"|reform uk|good law project|voting intention|representation of the people",
    re.IGNORECASE,
)
# The opt-in layer that is ALLOWED to contain the above. Everything else must be clean.
_POLITICAL_LAYER = "political"
# Each category maps to the candidate directories an entry may live in. Git hooks
# (pre-commit, commit-msg, pre-push) live in .githooks/, not .claude/hooks/, so
# both are listed — an entry that resolves in none is surfaced, not silently dropped.
_LAYER_DIRS = {
    "files": ["."],
    "directives": ["directives"],
    "commands": ["global-commands"],
    "scripts": ["global-scripts", "execution"],
    "hooks": [".githooks", ".claude/hooks"],
}


def scenario_non_political_layers_domain_neutral(verbose: bool = False):
    """FAIL if any NON-political layer file carries electoral/political content.

    The whole point of the `political` layer is that a normal project (even one
    with a database and personal data) never inherits electoral-register/PPERA/
    campaign content. So every layer EXCEPT `political` must be domain-clean.

    Skips when manifest.json is absent (e.g. a consumer project) — nothing to check.
    """
    import json
    manifest = PROJECT_ROOT / "manifest.json"
    vlines = []
    if not manifest.exists():
        return _result("PASS", "no manifest.json — not the kit repo, nothing to check", vlines)
    try:
        layers = json.loads(manifest.read_text(encoding="utf-8")).get("layers", {})
    except (json.JSONDecodeError, OSError) as e:
        return _result("WARN", f"cannot read manifest.json: {e}", vlines)

    leaks = []
    unresolved = []
    scanned = 0
    for layer, content in layers.items():
        if layer == _POLITICAL_LAYER:
            continue  # the political layer is allowed to contain this content
        for category, subdirs in _LAYER_DIRS.items():
            for name in content.get(category, []):
                p = next((PROJECT_ROOT / sd / name for sd in subdirs
                          if (PROJECT_ROOT / sd / name).is_file()), None)
                if p is None:
                    unresolved.append(f"{layer}/{category}:{name}")
                    continue
                scanned += 1
                matches = sorted({m.group(0).lower()
                                  for m in _DOMAIN_LEAK_RE.finditer(p.read_text(encoding="utf-8", errors="ignore"))})
                if matches:
                    rel = p.relative_to(PROJECT_ROOT)
                    leaks.append(f"[{layer}] {rel}: {', '.join(matches)}")
                    vlines.append(f"  [{layer}] {rel}: {', '.join(matches)}")

    vlines.insert(0, f"  Non-political layer files scanned: {scanned}")
    if unresolved:
        vlines.append(f"  Unresolved entries (coverage gap): {', '.join(unresolved)}")
    if leaks:
        return _result("FAIL", f"{len(leaks)} non-political file(s) carry electoral/political content (move to the `political` layer): " + "; ".join(leaks), vlines)
    if unresolved:
        return _result("WARN", f"scanned {scanned}; {len(unresolved)} entr(y/ies) could not be located: {', '.join(unresolved)}", vlines)
    return _result("PASS", f"no electoral/political leakage across {scanned} non-political layer files", vlines)


# ════════════════════════════════════════════════════════════
# Scenario registry
# ════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════
# Scenario 18: readme_claims_match_disk
# ════════════════════════════════════════════════════════════

# Guardrail hooks the README advertises as accident-prevention blockers.
# Adding/removing one must update both this list and the README count.
_GUARDRAIL_HOOKS = [
    "block_dangerous_commands.py",
    "block_secrets_in_code.py",
    "block_unnecessary_admin_merge.py",
    "confirm_pr_merge.py",
    "enforce_review_gate.py",
    "guard_kit_writes.py",
    "protect_directives.py",
]


def _count_operating_rules() -> int:
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    if not claude_md.exists():
        return -1
    text = claude_md.read_text(encoding="utf-8")
    return len(re.findall(r"^\d+\.\s+\*\*(.+?)\.\*\*", text, re.MULTILINE))


def _count_slash_commands() -> int:
    d = PROJECT_ROOT / "global-commands"
    if not d.exists():
        return -1
    return len([p for p in d.glob("*.md") if p.name.lower() != "readme.md"])


def _count_guardrail_hooks() -> int:
    hooks = PROJECT_ROOT / ".claude" / "hooks"
    return sum(1 for h in _GUARDRAIL_HOOKS if (hooks / h).exists())


def scenario_readme_claims_match_disk(verbose: bool = False):
    """FAIL if a numeric claim in README.md disagrees with the files on disk.

    This is why the README counts rotted (178 files, 33 directives, ...): nothing
    held them to the tree. Each claim is parsed from README.md and compared to a
    live count. Update the README when you add/remove the things it counts.
    """
    readme = PROJECT_ROOT / "README.md"
    vlines = []
    if not readme.exists():
        return _result("WARN", "README.md not found", vlines)
    text = readme.read_text(encoding="utf-8")

    checks = [
        ("operating rules", r"(\d+)\s+operating rules", _count_operating_rules),
        ("directives", r"(\d+)\s+directives",
            lambda: len(list((PROJECT_ROOT / "directives").rglob("*.md")))),
        ("execution scripts", r"(\d+)\s+execution scripts",
            lambda: len(list((PROJECT_ROOT / "execution").glob("*.py")))),
        ("slash commands", r"(\d+)\s+slash commands", _count_slash_commands),
        ("guardrail hooks", r"(\d+)\s+guardrail hooks", _count_guardrail_hooks),
        ("HTML tutorial pages", r"(\d+)\s+HTML tutorial pages",
            lambda: len(list((PROJECT_ROOT / "docs" / "tutorial").glob("*.html")))),
        ("markdown reference docs", r"(\d+)\s+markdown reference docs",
            lambda: len(list((PROJECT_ROOT / "docs" / "reference").rglob("*.md")))),
        ("custom agents", r"(\d+)\s+custom agents",
            lambda: len(list((PROJECT_ROOT / ".claude" / "agents").glob("*.md")))),
    ]

    # A claim that is ABSENT means this isn't the kit's README (e.g. a consumer
    # project where test_methodology.py is installed). Skip absent claims; only
    # FAIL on a claim that is present AND wrong. Otherwise this scenario would
    # break --quick in every downstream project.
    mismatches = []
    checked = 0
    for label, pattern, actual_fn in checks:
        m = re.search(pattern, text)
        if m is None:
            vlines.append(f"  {label}: no claim in README — skipped (not the kit repo?)")
            continue
        checked += 1
        actual = actual_fn()
        claimed = int(m.group(1))
        ok = claimed == actual
        vlines.append(f"  {label}: claim {claimed} vs actual {actual} {'OK' if ok else 'MISMATCH'}")
        if not ok:
            mismatches.append(f"{label}: README says {claimed}, disk has {actual}")

    if checked == 0:
        return _result("PASS", "no kit count claims in README — nothing to enforce here", vlines)
    if mismatches:
        return _result("FAIL", f"{len(mismatches)} README claim(s) wrong: " + "; ".join(mismatches), vlines)
    return _result("PASS", f"all {checked} README counts match disk", vlines)


# ════════════════════════════════════════════════════════════
# Scenario 19: execution_determinism
# ════════════════════════════════════════════════════════════

# Patterns that introduce hidden nondeterminism into a "pure" execution script.
# Clock and git reads are intentionally NOT flagged — they are the explicit I/O
# layer (see CLAUDE.md). These must stay out of pure scripts.
_NONDET_PATTERNS = {
    "random": re.compile(r"\bimport random\b|\brandom\.(random|randint|choice|shuffle|uniform|sample)\b"),
    "interactive input()": re.compile(r"(?<![\w.])input\s*\("),
    "in-process network": re.compile(r"\b(urllib\.request|urlopen|requests\.(get|post|put|delete|patch|request)|http\.client|socket\.socket)\b"),
}
# Scripts that ARE the I/O layer: each maps to the categories it may legitimately use.
_DETERMINISM_ALLOWLIST = {
    "doe_init.py": {"interactive input()"},        # interactive setup wizard
    "slack_notify.py": {"in-process network"},     # posts to Slack webhook
}
# The scanner itself defines the forbidden tokens as regex string literals, so it
# trips its own patterns. It is the test harness, not a pure-work script — skip it.
_DETERMINISM_SKIP = {"test_methodology.py"}


def scenario_execution_determinism(verbose: bool = False):
    """FAIL if a pure execution/ script hides randomness, prompts, or network I/O.

    Backs the CLAUDE.md claim that execution/ avoids hidden nondeterminism. The
    genuine I/O scripts are allowlisted; a NEW script that adds random/input/network
    must drop it or be added to the allowlist consciously.
    """
    exec_dir = PROJECT_ROOT / "execution"
    vlines = []
    if not exec_dir.exists():
        return _result("WARN", "execution/ not found", vlines)

    scripts = [p for p in sorted(exec_dir.glob("*.py")) if p.name not in _DETERMINISM_SKIP]
    violations = []
    for py in scripts:
        allowed = _DETERMINISM_ALLOWLIST.get(py.name, set())
        src = py.read_text(encoding="utf-8")
        for category, pattern in _NONDET_PATTERNS.items():
            if pattern.search(src) and category not in allowed:
                violations.append(f"{py.name}: {category}")
                vlines.append(f"  {py.name}: {category} (not allowlisted)")

    vlines.insert(0, f"  Scripts scanned: {len(scripts)}")
    if violations:
        return _result("FAIL", f"{len(violations)} determinism violation(s): " + "; ".join(violations), vlines)
    return _result("PASS", f"no hidden nondeterminism in execution/ ({len(scripts)} scripts)", vlines)


def scenario_report_generator_styling(verbose: bool = False):
    """Guard: HTML report generators must consume the shared html_builder, not
    carry their own design tokens.

    Every report generator routes its document through html_builder.page_scaffold
    (single <style>, single :root, Chalk & Flint tokens). A generator-local
    ``<style>`` tag or ``:root {`` selector means it has drifted off the builder
    and will diverge from the locked design system. html_builder.py itself is the
    single source and is exempt. WARN (not FAIL) so a deliberate exception can
    ship while still surfacing the drift.
    """
    vlines = []
    # (relative path, label) — the builder is the source of truth, excluded.
    generators = [
        "global-scripts/wrap_html.py",
        "global-scripts/eod_html.py",
        "global-scripts/build_hq.py",
        "execution/generate_test_checklist.py",
        # generate_whats_new.py was deleted in v1.72.0 with the rest of the
        # docs site (the liveness audit's B3 exemption note died with it).
    ]
    offenders = []
    scanned = 0
    for rel in generators:
        path = PROJECT_ROOT / rel
        if not path.exists():
            vlines.append(f"  {rel}: not found — skipped")
            continue
        scanned += 1
        src = path.read_text(encoding="utf-8", errors="replace")
        hits = []
        if "<style>" in src or "<style " in src:
            hits.append("<style> tag")
        if re.search(r":root\s*\{", src):
            hits.append(":root selector")
        if hits:
            offenders.append(f"{rel} ({', '.join(hits)})")
            vlines.append(f"  DRIFT  {rel}: {', '.join(hits)}")
        else:
            vlines.append(f"  ok     {rel}: consumes html_builder")

    vlines.insert(0, f"  Generators scanned: {scanned}")
    if scanned == 0:
        return _result("WARN", "no report generators found to scan", vlines)
    if offenders:
        return _result(
            "WARN",
            f"{len(offenders)} generator(s) carry local styling off the builder: "
            + "; ".join(offenders),
            vlines,
        )
    return _result(
        "PASS",
        f"all {scanned} report generators consume html_builder (no local <style>/:root)",
        vlines,
    )


SCENARIOS = [
    ("session_start_discipline",    scenario_session_start_discipline),
    ("contract_completeness",       scenario_contract_completeness),
    ("learnings_freshness",         scenario_learnings_freshness),
    ("rationalisation_coverage",    scenario_rationalisation_coverage),
    ("trigger_completeness",        scenario_trigger_completeness),
    ("review_discipline",           scenario_review_discipline),
    ("claude_md_quality",           scenario_claude_md_quality),
    ("execution_script_tests",      scenario_execution_script_tests),
    ("router_coverage",             scenario_router_coverage),
    ("rule_completeness",           scenario_rule_completeness),
    ("scale_consistency",           scenario_scale_consistency),
    ("directive_schema",            scenario_directive_schema),
    ("cross_reference_consistency", scenario_cross_reference_consistency),
    ("agent_definition_integrity",  scenario_agent_definition_integrity),
    ("plan_vs_actual",              scenario_plan_vs_actual),
    ("readme_claims_match_disk",    scenario_readme_claims_match_disk),
    ("execution_determinism",       scenario_execution_determinism),
    ("non_political_layers_domain_neutral", scenario_non_political_layers_domain_neutral),
    ("report_generator_styling",    scenario_report_generator_styling),
]

# Scenarios excluded from --quick mode
_QUICK_EXCLUDE = {"execution_script_tests"}


# ════════════════════════════════════════════════════════════
# Output helpers
# ════════════════════════════════════════════════════════════

def _status_str(status: str) -> str:
    if status == "PASS":
        return _green("PASS")
    if status == "WARN":
        return _yellow("WARN")
    if status == "FAIL":
        return _red("FAIL")
    return status


def _print_result(idx: int, name: str, res: dict, verbose: bool):
    detail = f" ({res['detail']})" if res["detail"] else ""
    print(f"{idx}. {name}: {_status_str(res['status'])}{detail}")
    # Always show detail for claude_md_quality (it has grade + suggestions)
    # Show other scenarios' detail only in verbose mode
    if res.get("verbose"):
        if verbose or name == "claude_md_quality":
            for vline in res["verbose"]:
                print(_dim(vline))


# ════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="DOE methodology testing framework — verifies DOE rules are being followed.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Scenarios:
  session_start_discipline       Check .tmp/.session-start exists and is recent
  contract_completeness          Verify tasks/todo.md steps have valid contracts
  learnings_freshness            Check learnings.md and retro quality
  rationalisation_coverage       YOU MUST rules covered in rationalisation-tables.md
  trigger_completeness           Every directive has a trigger in CLAUDE.md
  review_discipline              Features shipped with review evidence (informational)
  claude_md_quality              Score CLAUDE.md against quality rubric (grades A-F)
  execution_script_tests         Run pytest against tests/execution/ (full mode only)
  router_coverage                CLAUDE.md triggers cover all directive files
  rule_completeness              Core Behaviour rules have directive pointers
  scale_consistency              Scale headings (Solo/Parallel) are consistent
  directive_schema               Directives have Goal + When to Use sections
  cross_reference_consistency    Cross-references point to real files
  agent_definition_integrity     Agent files match README claims
  plan_vs_actual                 Completed features' plan deliverables exist
  readme_claims_match_disk       README numeric claims (counts) match the tree (FAIL on drift)
  execution_determinism          No hidden randomness/input/network in pure execution/ scripts
  non_political_layers_domain_neutral  No electoral/political content outside the opt-in political layer (FAIL on leak)
        """,
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List all scenario names",
    )
    parser.add_argument(
        "--scenario", metavar="NAME", action="append",
        help="Run a specific scenario by name (can be repeated)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show detailed output for each scenario",
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Fast subset for CI (excludes execution_script_tests)",
    )
    args = parser.parse_args()

    if args.list:
        for i, (name, _) in enumerate(SCENARIOS, 1):
            print(f"{i}. {name}")
        return

    # Build list of scenarios to run
    if args.scenario:
        requested = args.scenario  # list from action="append"
        found = [(i, name, fn) for i, (name, fn) in enumerate(SCENARIOS, 1) if name in requested]
        unknown = set(requested) - {name for _, name, _ in found}
        if unknown:
            known = ", ".join(n for n, _ in SCENARIOS)
            print(f"Unknown scenario(s): {', '.join(unknown)}. Known: {known}", file=sys.stderr)
            sys.exit(2)
        to_run = found
    elif args.quick:
        to_run = [
            (i, name, fn)
            for i, (name, fn) in enumerate(SCENARIOS, 1)
            if name not in _QUICK_EXCLUDE
        ]
    else:
        to_run = [(i, name, fn) for i, (name, fn) in enumerate(SCENARIOS, 1)]

    results = []
    for idx, name, fn in to_run:
        res = fn(verbose=args.verbose)
        results.append((idx, name, res))
        _print_result(idx, name, res, verbose=args.verbose)

    # Summary
    statuses = [r["status"] for _, _, r in results]
    passes = statuses.count("PASS")
    warns = statuses.count("WARN")
    fails = statuses.count("FAIL")

    print()
    parts = []
    if passes:
        parts.append(_green(f"{passes} PASS"))
    if warns:
        parts.append(_yellow(f"{warns} WARN"))
    if fails:
        parts.append(_red(f"{fails} FAIL"))
    print(_bold("Summary: ") + ", ".join(parts))

    if warns or fails:
        attention = [(name, r) for _, name, r in results if r["status"] in ("WARN", "FAIL")]
        print()
        print(_bold("Needs attention:"))
        for name, r in attention:
            label = _status_str(r["status"])
            print(f"  {label}  {name}: {r['detail']}")

    sys.exit(1 if fails > 0 else 0)


if __name__ == "__main__":
    main()
