#!/usr/bin/env python3
"""Pre-commit contract verification for solo mode.

Reads tasks/todo.md, finds the current step (first unchecked under ## Current),
and checks whether contract criteria indicate partially-verified work. Only
blocks when a step has a MIX of [x] and [ ] criteria (work started but
verification incomplete). All [ ] = next step (don't block). All [x] = done.

Exit codes:
  0 — allow commit (no contract, all criteria pass, next step, or no current step)
  1 — block commit (partially verified — some [x] and some [ ])
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

    checked_count = sum(1 for c, _ in criteria if c)
    unchecked = [(text) for checked, text in criteria if not checked]

    if not unchecked:
        return 0  # All criteria pass

    if checked_count == 0:
        return 0  # All criteria unchecked — this is the next step, not current work

    # Mix of [x] and [ ] — work started but verification incomplete
    step_desc = re.sub(r"^\d+\.\s+\[ \]\s*", "", current_step_line)
    print("")
    print("═══ Contract verification failed ═══")
    print("")
    print(f"  Step: {step_desc}")
    print(f"  BLOCKED: {len(unchecked)} contract criteria not yet verified")
    print(f"  ({checked_count} checked, {len(unchecked)} remaining)")
    print("")
    for item in unchecked:
        print(f"  [ ] {item}")
    print("")
    print("  Run verification first, or skip with:")
    print("  SKIP_CONTRACT_CHECK=1 git commit -m '...'")
    print("")
    return 1


if __name__ == "__main__":
    sys.exit(check_contract())
