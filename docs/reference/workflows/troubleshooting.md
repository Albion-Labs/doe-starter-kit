# When Things Go Wrong

Things will go wrong. That's normal — and DOE is designed to make recovery straightforward. This page covers common problems and how to fix them.

---

## "Claude seems confused or is going in circles"

This usually means the conversation has accumulated too much context, or the task description is ambiguous.

**Fix:**
1. Run `/clear` to reset the conversation. This wipes the chat history but keeps all your files, git history, and project state intact. Nothing is lost.
2. Start a fresh session with `/stand-up`.
3. Describe what you want more specifically. Instead of "fix the layout," try "the header on the results page overlaps the chart on mobile — make the header stack above the chart on screens narrower than 768px."

If it keeps happening, the task might be too large. Break it into smaller, concrete steps.

---

## "Something broke and I don't know what changed"

Every commit (save point) in git is a snapshot of your entire project. You can always see what changed and go back.

**Fix:**
1. Run `git log --oneline` to see your recent commits. Each line is a save point with a short description.
2. Run `git diff` to see what's changed since the last commit — these are unsaved changes.
3. If you need to undo the last change, ask Claude: "Revert the last commit." This undoes the most recent save point cleanly.
4. If you need to go back further, tell Claude which commit you want to return to.

Don't panic. Every commit is a save point you can return to. Nothing in git is permanently lost unless you deliberately delete it.

---

## "Claude made a file in the wrong place"

Claude follows the directory structure defined in CLAUDE.md, but occasionally drifts.

**Fix:**
1. Tell Claude to move it: "Move src/utils.js to execution/utils.py"
2. Check the directory structure section in your CLAUDE.md — this is the reference for where files belong.
3. Run `/audit` to check for structural issues across the project. The audit catches misplaced files, missing documentation, and other drift.

---

## "A contract check is failing"

Contracts are the testable criteria that define "done" for each step. When one fails, something about the implementation doesn't match the specification.

**Fix:**
1. Run `/agent-verify` to see exactly which criteria are failing and why.
2. Read the `Verify:` pattern carefully — it tells you precisely what's being checked. For example, `file: src/chart.js contains renderChart` means the file `src/chart.js` must contain the text `renderChart`.
3. Common causes:
   - A typo in a function or file name
   - A file wasn't saved before the check ran
   - The build step wasn't run after editing source files
4. Claude will attempt up to 3 fixes automatically before asking for your help. If it can't fix it after 3 attempts, it will explain what's going wrong and ask for guidance.

---

## "I closed the terminal without wrapping"

This happens to everyone. Here's what it means:

- **Your code is safe.** Everything that was committed to git is still there.
- **STATE.md won't reflect the last session.** It still shows the state from your previous wrap, so the next stand-up will be slightly out of date.

**Fix:**
- Just start a new session normally with `/stand-up`. Claude will read the git history and figure out where things are. It won't be as clean as a proper wrap, but it works.
- If you want to be thorough, you can update STATE.md manually to note where you left off.

This isn't catastrophic, but building the `/wrap` habit avoids it entirely.

---

## "I don't understand what Claude is doing"

It's important to understand what's happening in your project. Never let Claude keep building if you're lost.

**Fix:**
1. Run `/sitrep` for a plain-language status update — what's being worked on, what's been done recently, and what's coming next.
2. Ask Claude directly: "Explain what you just did in simple terms." Claude will break down the last action without jargon.
3. Check `tasks/todo.md` to see the current step and its contract. The contract tells you exactly what this step is supposed to achieve.

---

## "The audit is showing warnings"

The `/audit` command checks your project's health — file structure, documentation freshness, claim accuracy, and more.

**Fix:**
1. Run `/audit` to see the full report.
2. Understand the severity levels:
   - **WARN** means something needs attention but isn't broken. For example, a document that hasn't been updated in a while, or a mild style inconsistency.
   - **FAIL** means something is actually wrong and needs fixing. For example, a claim in your documentation that isn't backed by data, or a missing required file.
3. Tell Claude to fix the issues: "Fix the audit warnings" or "Fix the audit failures." Claude can usually resolve them automatically.

---

## "I want to start over on a feature"

Sometimes a feature isn't working out and you want a fresh start.

**Fix:**
1. Don't delete files manually — tell Claude what you want to undo.
2. Git keeps every version of every file, so nothing is permanently lost. Claude can revert your project to the commit just before the feature started.
3. Tell Claude: "Revert to before we started the [feature name] feature." Claude will find the right commit and take you back to that point.

Your previous work on the feature is still in git history if you ever want to reference it.

---

## Emergency: "Something is really broken"

If something has gone seriously wrong — corrupted files, a bad commit that broke everything, data that looks wrong — don't improvise.

**Fix:**
1. **Read `directives/break-glass.md`** — this file contains step-by-step recovery procedures for serious problems. It's written for exactly this situation.
2. **Don't run destructive commands** like `rm -rf` (delete everything) or `git reset --hard` (discard all changes) unless you understand exactly what they do. These commands can make things worse if used incorrectly.
3. **Ask Claude for help.** Describe the error message or the symptoms. Claude can diagnose most issues and will walk you through the recovery.

The most important thing in an emergency is to stop and read before acting. Your git history is almost certainly intact, which means recovery is almost always possible.
