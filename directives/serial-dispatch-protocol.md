# Directive: Serial Dispatch Protocol (SDD for DOE)

## Goal
Define when and how to use serial dispatch (coordinator → implementer → reviewer) for complex features, as an alternative to parallel dispatch for tasks with shared state or integration concerns.

## When to Use
- Building a complex feature (3+ steps with shared files or output dependencies)
- Using the decision tree below to choose between serial and parallel dispatch
- Running a multi-step feature where quality matters more than speed

## Decision Tree

```
Is this a complex feature (3+ steps)?
  └─ YES: Are steps interdependent (shared files, output dependencies)?
       └─ YES → Serial dispatch with review gates (this protocol)
       └─ NO → Parallel dispatch (CLAUDE.md Rule 10, multi-agent-coordination.md)
  └─ NO: Solo mode (no dispatch needed, use /review directly)
```

**When to use serial dispatch:**
- Feature has 3+ steps that build on each other
- Multiple steps modify the same files
- Later steps depend on the output of earlier steps
- Integration concerns span step boundaries
- The feature touches critical infrastructure (execution scripts, CLAUDE.md, hooks)

**When to use parallel dispatch:**
- 2+ truly independent tasks (different features, no shared files)
- Tasks have no output dependencies
- Each task owns distinct files (per the `owns` list in todo.md)

**When to use solo mode:**
- Single-step tasks or quick fixes
- Tasks where you (the coordinator) are also the implementer
- The common case for a solo developer

## Serial Dispatch Workflow

### Phase 1: Planning
1. Coordinator reads the plan file + todo.md contracts for all steps
2. Identifies dependencies between steps (which steps must complete before others)
3. Groups steps into a serial chain

### Phase 2: Step Execution (repeat for each step)

For each step in the chain:

**a) Dispatch implementer subagent:**
- Include: step description, contract criteria, relevant file list, `directives/adversarial-review/implementer-prompt.md` template, relevant `learnings.md` patterns
- Specify model: Sonnet for straightforward implementation, Opus for architecture/judgment
- Set expectation: "Report STATUS: DONE when complete, or NEEDS_CONTEXT if you hit unknowns"

**b) Receive implementer report:**
- Check status (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED)
- If NEEDS_CONTEXT → provide context, re-dispatch
- If BLOCKED → evaluate, escalate if genuine

**c) Run contract verification:**
- Execute all `Verify:` patterns from the step's contract
- If any fail → re-dispatch implementer with specific failures

**d) Mark step complete:**
- Update todo.md: mark step [x] with timestamp
- Commit and push

### Phase 3: Feature Review

After ALL steps complete (not after each step):

1. Dispatch **spec reviewer** subagent with:
   - Full feature contract (all steps)
   - Plan excerpt
   - Combined diff (`git diff main...HEAD`)
   - `directives/adversarial-review/spec-reviewer.md` template
   - Model: Haiku (mechanical comparison task)

2. If spec review passes, dispatch **code quality reviewer** with:
   - Changed files
   - `learnings.md` patterns
   - Base/head SHAs for diff
   - `directives/adversarial-review/code-quality-reviewer.md` template
   - Model: Sonnet (needs code understanding but follows template)

3. If both reviews pass → feature is ready for snagging/PR

4. If either review fails → re-dispatch implementer with review findings
   - Maximum 2 re-dispatch cycles per step
   - After 2 failures → escalate to user

### Phase 4: Final Review (optional)

For large features (5+ steps), dispatch a final **integration reviewer** (Opus):
- Reviews the full feature diff for cross-step coherence
- Checks for over-engineering, scope creep, architectural drift
- This is the "step back and look at the whole picture" pass

## Model Selection Guide

| Role | Default Model | When to use Opus |
|------|--------------|-----------------|
| Implementer | Sonnet | Architecture decisions, judgment calls, cross-file reasoning |
| Spec reviewer | Haiku | Never -- it's a mechanical comparison task |
| Code quality reviewer | Sonnet | Security-sensitive code, complex algorithms |
| Final integration reviewer | Opus | Always -- needs cross-step judgment |
| Coordinator | You (the main session) | N/A -- you are the coordinator |

## Re-Dispatch Limits

- Maximum 2 re-dispatch cycles per step (implementer → reviewer → fix → reviewer → done OR escalate)
- If spec review fails twice on the same issue, the contract may be wrong -- review the contract before re-dispatching
- If code quality review keeps finding the same pattern, add it to `learnings.md` as a convention

## Integration with Existing Systems

- **CLAUDE.md Rule 7:** References this protocol for subagent dispatch decisions
- **CLAUDE.md Rule 10:** References this protocol; parallel dispatch is preserved for truly independent tasks
- **Multi-agent coordination plan:** `.claude/plans/multi-agent-coordination.md` includes serial dispatch as an option alongside the wave model
- **Subagent protocol:** `directives/subagent-protocol.md` defines the STATUS report format used throughout
- **Adversarial review templates:** `directives/adversarial-review/` provides the review prompts

## When NOT to Use Serial Dispatch

- **Quick features (1-2 steps):** Solo mode is faster. Just build, verify, commit.
- **Truly independent tasks:** Use parallel dispatch (Rule 10). Serial dispatch adds overhead for no benefit when tasks don't interact.
- **Research/exploration:** Serial dispatch is for building, not exploring. Use research subagents without the review gates.
- **Hotfixes:** If something is broken in production, fix it directly. Don't ceremony a one-line fix.

## Edge Cases
- If the coordinator session is running low on context, dispatch a fresh coordinator subagent with the plan + progress summary
- If a step's contract criteria are invalid (flagged by `/agent-verify`), fix the contract before dispatching the implementer
- If mid-feature you discover the plan is wrong, stop dispatch and update the plan first -- don't let implementers build on a broken foundation

## Verification
- [ ] This directive exists at `directives/serial-dispatch-protocol.md`
- [ ] CLAUDE.md Rule 7 references serial dispatch
- [ ] Multi-agent coordination plan references serial dispatch
- [ ] Decision tree clearly distinguishes serial vs parallel dispatch
