# Directive: Subagent Status Protocol

## Goal
Standardise how subagents report results back to the coordinator, replacing ad-hoc success/failure with structured status reporting that enables informed decisions.

## When to Use
- Dispatching any subagent (implementation, review, research, or utility)
- Receiving results from a subagent
- Running in serial dispatch mode (SDD) — see `directives/serial-dispatch-protocol.md`
- Evaluating whether to merge, re-dispatch, or escalate

## Status Definitions

Every subagent must report one of four statuses on completion:

### DONE
Task complete. All acceptance criteria pass. No concerns or caveats.
- **Coordinator action:** Run contract verification (`execution/verify.py`), merge if pass.

### DONE_WITH_CONCERNS
Task complete, but the agent noticed issues it chose not to block on. Concerns are listed with severity.
- **Coordinator action:** Evaluate each concern:
  - **Critical** (would break production, violates a guardrail, security issue) → re-dispatch with fix instructions
  - **Important** (code smell, suboptimal approach, missing edge case) → log to learnings.md, merge
  - **Minor** (style preference, naming suggestion, documentation gap) → merge, optionally note

### NEEDS_CONTEXT
Agent cannot proceed without information not provided in the task description. Specific questions are listed.
- **Coordinator action:** Provide the missing context and re-dispatch the same agent. Do NOT guess the answers — if the coordinator doesn't know either, escalate to the user.

### BLOCKED
Task cannot be completed. The agent explains why and suggests alternatives.
- **Coordinator action:** Evaluate the blocker. If it's a misunderstanding, clarify and re-dispatch. If it's a genuine impediment, escalate to the user or pivot approach.

## Required Report Format

Every subagent must include this report when returning results:

```
STATUS: [DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED]
WHAT: [1-2 line summary of what was implemented/attempted]
TEST RESULTS: [pass/fail counts from contract verification, or "no tests" with justification]
FILES CHANGED: [list of files created/modified/deleted]
SELF-REVIEW: [see checklist below]
CONCERNS: [if DONE_WITH_CONCERNS — severity + description for each]
QUESTIONS: [if NEEDS_CONTEXT — specific questions, not vague requests]
BLOCKER: [if BLOCKED — what prevents completion + suggested alternatives]
```

## Self-Review Checklist

Before reporting DONE or DONE_WITH_CONCERNS, the subagent must complete this self-review:

- [ ] **Completeness:** Does the implementation address every requirement in the task description?
- [ ] **Quality:** Would this code pass a code review? Any shortcuts taken?
- [ ] **YAGNI:** Did I add anything not explicitly requested? If so, why?
- [ ] **Testing:** Are contract criteria satisfied? Did I verify, not just assume?
- [ ] **Conventions:** Does the code follow patterns from `learnings.md` and existing codebase?
- [ ] **Files:** Are all changed files listed? Any unintended modifications?

If any checkbox is NO, the agent should either fix the issue or report DONE_WITH_CONCERNS with the gap listed.

## Dispatch Rules

When the coordinator dispatches a subagent:

1. **Include the status protocol in the prompt.** The subagent must know the expected report format.
2. **Specify the acceptance criteria.** Copy the relevant contract criteria from todo.md.
3. **Provide only necessary context.** Files the subagent needs to read/modify, relevant learnings, the plan excerpt. Not the entire project context.
4. **Set the expected status.** "Report back with STATUS: DONE when complete, or NEEDS_CONTEXT if you hit unknowns."
5. **Specify the model.** Opus for judgment, Sonnet for implementation, Haiku for lookups.

## Re-Dispatch Limits

- Maximum 2 re-dispatch cycles per step (implementer → reviewer → fix → reviewer → done OR escalate)
- If a subagent reports NEEDS_CONTEXT twice on the same question, escalate to the user
- If a subagent reports BLOCKED, do not blindly re-dispatch — the blocker must be resolved first

## Integration with Existing Rules

- **CLAUDE.md Rule 7** references this protocol for all subagent dispatch
- **CLAUDE.md Rule 10** references this protocol for parallel agent dispatch
- **Serial dispatch protocol** (`directives/serial-dispatch-protocol.md`) uses this as the communication layer between coordinator, implementer, and reviewer agents
- **Adversarial review templates** (`directives/adversarial-review/`) include status reporting requirements

## Edge Cases
- If a subagent crashes or times out, treat it as BLOCKED with reason "agent failed to complete"
- If a subagent returns results without a status report, treat it as DONE_WITH_CONCERNS with concern "missing status report — verify results manually"
- In solo mode (no subagents), the self-review checklist still applies — run it mentally before committing

## Implementation Patterns

Patterns for subagent orchestration that have emerged from retros. Not rules -- patterns to apply when they fit.

### Passing context to subagents
When delegating documentation, summary, or reference-page work, pass the actual data source (manifest.json, script output, file contents) rather than describing expected content. Subagents confronted with "the trigger table should have N rows" will fabricate rows; subagents handed the manifest will extract real ones. For tutorial or reference pages: generate the real output first, then tell the subagent to embed it verbatim.

### Parallel subagents on overlapping files
Two or more subagents editing the same files in parallel (without worktree isolation) merge into a single commit -- git stages all changes per-file, not per-agent. If separate commits are required, either use worktree isolation or serialise the agents. If one commit is acceptable, parallel dispatch is fine.

### Monitoring and coordination
PostToolUse hooks are the right integration point for background monitoring (heartbeats, context tracking, progress signals) -- cheap per-call, invisible to the user, no polling loop needed. Reserve explicit coordination scripts for cross-agent contract verification and merge decisions.

### Worktree root resolution
`Path.cwd()` breaks inside worktrees because agents cd into `.tmp/worktrees/<taskId>/`. Any script that uses cwd as the project root will fail silently. Resolve the main repo root by walking up from the script file and detecting the `.git` file (worktrees have a `.git` file, not a directory). Centralise this in a shared utility rather than open-coding in each script.

## Verification
- [ ] This directive exists at `directives/subagent-protocol.md`
- [ ] CLAUDE.md Rule 7 references the status protocol
- [ ] All four statuses are documented with coordinator actions
- [ ] Report format is specified with all required fields
- [ ] Self-review checklist is included
- [ ] Implementation Patterns section covers context passing, parallel file overlap, monitoring, worktree root resolution
