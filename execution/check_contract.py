#!/usr/bin/env python3
"""Pre-commit contract verification for solo mode.

Two checks:
1. Current step: finds the first unchecked step under ## Current and blocks if
   it has a MIX of [x] and [ ] criteria (work started but incomplete).
   All [ ] = next step (don't block). All [x] = done.
2. Completed step integrity: scans ALL completed [x] steps under ## Current for
   unchecked [auto] criteria. A step marked [x] with unchecked [auto] criteria
   means verification was skipped — always blocks.

Exit codes:
  0 — allow commit
  1 — block commit (partially verified or completed step with unchecked auto criteria)
"""

import re
import sys
from pathlib import Path


def find_project_root():
    """Walk up from cwd to find tasks/todo.md."""
    p = Path.cwd()
    while p != p.parent:
        if (p / "tasks" / "todo.md").exists():
            return p
        p = p.parent
    return Path.cwd()


def check_contract():
    root = find_project_root()
    todo_path = root / "tasks" / "todo.md"
    if not todo_path.exists():
        return 0  # No todo.md — nothing to check

    lines = todo_path.read_text().splitlines()

    # Find ## Current section
    in_current = False
    current_step_line = None
    current_step_idx = None

    for i, line in enumerate(lines):
        if line.strip().startswith("## Current"):
            in_current = True
            continue
        if in_current and line.strip().startswith("## "):
            break  # Hit next section
        if in_current and re.match(r"\d+\.\s+\[ \]", line.strip()):
            current_step_line = line.strip()
            current_step_idx = i
            break

    if current_step_idx is None:
        return 0  # No unchecked step — allow

    # Collect contract criteria for this step
    # Contract block starts after "Contract:" line, criteria are indented "- [ ]" or "- [x]"
    found_contract = False
    criteria = []  # (checked: bool, text: str)

    for j in range(current_step_idx + 1, len(lines)):
        line = lines[j]
        stripped = line.strip()

        # Stop if we hit the next step or a non-indented line that isn't part of the contract
        if re.match(r"\d+\.\s+\[", stripped):
            break  # Next step

        if stripped.lower().startswith("contract:"):
            found_contract = True
            continue

        if found_contract:
            m = re.match(r"-\s+\[([ x])\]\s+(.*)", stripped)
            if m:
                checked = m.group(1) == "x"
                text = m.group(2)
                criteria.append((checked, text))
            elif stripped and not stripped.startswith("-"):
                # Non-list line after contract — contract block ended
                break

    if not found_contract or not criteria:
        return 0  # No contract block — allow

    # Only [auto] criteria gate commits. [manual] items are batched for human
    # sign-off at feature end — they must not block mid-feature commits.
    auto_criteria = [(c, t) for c, t in criteria if "[auto]" in t]
    auto_checked = sum(1 for c, _ in auto_criteria if c)
    auto_unchecked = [t for c, t in auto_criteria if not c]

    if not auto_unchecked:
        return 0  # All [auto] criteria pass (or none exist)

    if auto_checked == 0:
        return 0  # All [auto] unchecked — this is the next step, not current work

    # Mix of [x] and [ ] in [auto] criteria — work started but verification incomplete
    step_desc = re.sub(r"^\d+\.\s+\[ \]\s*", "", current_step_line)
    print("")
    print("═══ Contract verification failed ═══")
    print("")
    print(f"  Step: {step_desc}")
    print(f"  BLOCKED: {len(auto_unchecked)} [auto] criteria not yet verified")
    print(f"  ({auto_checked} checked, {len(auto_unchecked)} remaining)")
    print("")
    for item in auto_unchecked:
        print(f"  [ ] {item}")
    print("")
    print("  Run verification first, or skip with:")
    print("  SKIP_CONTRACT_CHECK=1 git commit -m '...'")
    print("")
    return 1


def check_completed_step_integrity():
    """Block if any completed [x] step has unchecked [auto] criteria."""
    root = find_project_root()
    todo_path = root / "tasks" / "todo.md"
    if not todo_path.exists():
        return 0

    lines = todo_path.read_text().splitlines()

    # Find ## Current section
    in_current = False
    violations = []  # list of (step_desc, unchecked_auto_items)

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("## Current"):
            in_current = True
            i += 1
            continue
        if in_current and stripped.startswith("## "):
            break  # Hit next section

        # Look for completed steps: "N. [x] description"
        if in_current and re.match(r"\d+\.\s+\[x\]", stripped):
            step_desc = re.sub(r"^\d+\.\s+\[x\]\s*", "", stripped)
            # Strip timestamp suffix like "*(completed ...)*"
            step_desc = re.sub(r"\s*\*\(completed.*?\)\*\s*$", "", step_desc)

            # Collect [auto] criteria for this step
            found_contract = False
            unchecked_auto = []
            j = i + 1
            while j < len(lines):
                cline = lines[j].strip()
                if re.match(r"\d+\.\s+\[", cline):
                    break  # Next step
                if cline.lower().startswith("contract:"):
                    found_contract = True
                    j += 1
                    continue
                if found_contract:
                    m = re.match(r"-\s+\[([ x])\]\s+(.*)", cline)
                    if m:
                        checked = m.group(1) == "x"
                        text = m.group(2)
                        if not checked and "[auto]" in text:
                            unchecked_auto.append(text)
                    elif cline and not cline.startswith("-"):
                        break
                j += 1

            if unchecked_auto:
                violations.append((step_desc, unchecked_auto))

        i += 1

    if not violations:
        return 0

    print("")
    print("═══ Completed step integrity check failed ═══")
    print("")
    for step_desc, items in violations:
        print(f"  Step (marked done): {step_desc}")
        print(f"  BLOCKED: {len(items)} [auto] criteria unchecked")
        for item in items:
            print(f"    [ ] {item}")
        print("")
    print("  A step cannot be [x] while [auto] criteria are [ ].")
    print("  Run the verifications and mark criteria [x], or skip with:")
    print("  SKIP_CONTRACT_CHECK=1 git commit -m '...'")
    print("")
    return 1


if __name__ == "__main__":
    rc = check_contract()
    if rc != 0:
        sys.exit(rc)
    sys.exit(check_completed_step_integrity())
