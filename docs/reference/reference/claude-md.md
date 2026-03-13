# CLAUDE.md — The Project Rulebook

Every DOE project has a file called `CLAUDE.md` in its root directory. This is the project's instruction manual for Claude Code. Every time you start a new conversation (session), Claude reads this file automatically and follows whatever rules it contains.

Think of it as the constitution for your project. You write the rules once, and Claude follows them in every session without being asked.

## What It Contains

CLAUDE.md is organised into sections, each controlling a different aspect of how Claude behaves.

### Operating Rules

These are numbered rules that define how Claude works in your project. A DOE starter kit comes with rules covering:

1. **Plan before building** — Claude checks the task tracker and state file before starting work, and writes a plan for anything complex.
2. **Ask, don't assume** — When something is unclear, Claude asks you rather than guessing.
3. **Check before spending** — If a script uses paid APIs, Claude confirms with you first.
4. **Verify before delivering** — Claude tests its own work before saying it's done.
5. **Explain decisions simply** — No jargon without context.
6. **Commit after every task** — One task, one git commit. Never batching multiple changes together.

Here is what rules 2 and 4 look like in an actual CLAUDE.md:

```markdown
## Operating Rules

2. **Ask, don't assume.** If a requirement is ambiguous, ask. Wrong assumptions
   waste more time than questions.

4. **Verify before delivering.** Never hand off output without checking it works.
   Run the script, test the output, confirm it matches the directive's verification
   criteria. If there's no way to verify, say so explicitly.
```

### Guardrails

Guardrails are things Claude must never do. They use the phrase "YOU MUST NOT" to make the constraint absolute. Examples from a real project:

```markdown
## Guardrails

- **YOU MUST NOT overwrite or delete existing directives without explicit
  permission.** These are living SOPs — propose changes, don't make them.
- **YOU MUST NOT store secrets outside `.env`.** No API keys in code, comments,
  or logs.
- **YOU MUST NOT force-push, revert commits, or delete branches without explicit
  permission.**
```

Guardrails are enforced by [hooks](hooks.md) that run automatically, so even if Claude's reasoning drifts, the guardrail catches it.

### Code Hygiene

Rules for keeping the codebase clean:

- Check if a file already exists before creating a new one
- Make surgical edits (fix the bug, don't rewrite the file)
- Reuse existing code before writing new functions
- Delete old files when you replace them
- Put files in the right directories

### Self-Annealing

This is the failure recovery process. When something goes wrong, Claude follows a structured loop:

1. Read the full error
2. Diagnose why (not just what)
3. Fix it
4. Retest
5. Log the learning

Small failures get a one-line note. Significant failures (wasted more than 30 minutes, broke something, or happened before) get a structured write-up in `learnings.md`.

See [Self-Annealing](../concepts/self-annealing.md) for the full explanation.

### Directory Structure

A map of where everything lives in the project. Claude uses this to know where to put new files. Example:

```markdown
## Directory Structure

directives/         # SOPs — read these before starting any task
execution/          # Deterministic Python scripts
tasks/              # Plans and todo tracking
learnings.md        # Project-specific institutional memory
STATE.md            # Session memory
.env                # API keys and credentials (NEVER commit)
.claude/            # Hooks, settings, plans, and commands
```

### Progressive Disclosure

A list of triggers that tell Claude when to read a specific file before starting a task. Rather than loading every directive into every session (which wastes context), Claude only reads what's relevant.

```markdown
## Progressive Disclosure

### Triggers
- Importing external data → check `learnings.md` ## API & Integration Patterns
- Working with Census data → check `learnings.md` ## API & Integration Patterns
- Creating a new execution script → check `execution/` for existing patterns
- Editing src/ files → run `python3 execution/build.py` afterwards
```

This is what makes DOE efficient — Claude loads context on demand, not all at once.

## When You'd Edit It

**Do edit:**
- Adding triggers specific to your project (e.g., "When importing Stripe data, read the Stripe directive first")
- Updating the directory structure when you add new directories
- Adding guardrails specific to your project (e.g., "Never delete customer records without confirmation")
- Adjusting the directory structure section when your project grows

**Don't edit:**
- The core Operating Rules — these are battle-tested across hundreds of sessions. They work as a system; changing one can have knock-on effects.
- The Guardrails section's general rules (secrets, force-push, directives) — these prevent real damage.
- The Self-Annealing process — this is how the system learns from failure.

If you think a core rule needs changing, discuss it with Claude first. It can explain why the rule exists and what might break if you change it.

## Where It Lives

The file must be at the root of your project directory: `your-project/CLAUDE.md`. Claude Code looks for it automatically when a session starts. There is no configuration needed to enable it.

There is also a global CLAUDE.md at `~/.claude/CLAUDE.md` that applies to all projects. Project-specific rules go in the project file; universal patterns (like "macOS sed requires an empty backup argument") go in the global file.

## Related Files

- [STATE.md](state-md.md) — session memory that CLAUDE.md rules reference
- [tasks/todo.md](todo-md.md) — the task tracker that Operating Rules govern
- [learnings.md](learnings-md.md) — long-term memory that Self-Annealing writes to
- [Hooks](hooks.md) — the enforcement mechanism for Guardrails
