# Directive: Break Glass

## Goal
Emergency recovery procedure when something goes seriously wrong — a bad commit, corrupted file, or a script that damaged data.

Tradeoff: Recovery procedures cost session time; they preserve recoverability and prevent compounded damage. Apply when something has gone seriously wrong (corrupted file, bad commit, damaged data). Skip when: the issue is a routine failed test or an expected error you can fix in the next edit.

## When to Use
When something has gone seriously wrong and needs immediate recovery. Triggered from CLAUDE.md: "When something goes seriously wrong, read `directives/break-glass.md` and follow it."

## Process

**Step 1: HALT.** Run only `git status` and other read-only inspection commands. Assess before any write. Stay calm -- nothing is unfixable.

**Step 2: Assess the damage.** Run these read-only commands to understand what happened:
```
git status                    # What files changed?
git log --oneline -5          # What were the last few commits?
git diff HEAD~1               # What did the last commit change?
```
Tell the user what you see. Explain in plain English: what changed, what broke, and what you think caused it.

**Step 3: Present options, get permission.** Show the user the relevant options and wait for explicit approval before any remediation:
- **Option A — Undo last commit, keep the changes visible:** `git reset --soft HEAD~1` (nothing is lost — changes become uncommitted edits you can review)
- **Option B — Undo last commit AND discard those changes:** `git reset --hard HEAD~1` (permanent — the work from that commit is gone)
- **Option C — Restore a single file** to how it was before the last commit: `git checkout HEAD~1 -- path/to/file`
- **Option D — Do nothing yet** — investigate further before taking action

Explain each option in plain language. Wait for explicit user approval ("go ahead" or equivalent) before any write.

**Step 4: After recovery.**
1. Verify the fix worked (`git status`, `git diff`, test affected files)
2. Log what happened and why in `learnings.md` under `## Common Mistakes`
3. If a script caused the problem, fix the script in the same session -- close the loop before moving on

## Key Principle
**STOP. Assess. Show. Ask. Then fix.**

## Verification
- [ ] Damage assessed with read-only commands before any action
- [ ] User shown options and gave explicit permission
- [ ] Recovery verified with git status/diff
- [ ] Incident logged to learnings.md
