# Adversarial Review Guide

## Goal
Catch real issues through structured multi-agent review with calibrated scoring incentives. The review is a completion gate -- steps do not release dependents until review passes.

## When to Use
Triggered by the `/review` command, or after high blast-radius steps.

## Review Roles

### Finder
Reads the implementation and identifies potential issues. Scored on discovery: +1 per valid finding, +5 for findings the Adversarial agent would have missed, +10 for findings that would have caused a production incident. Penalty: -2 for false positives (wastes everyone's time).

### Adversarial
Cross-examines the Finder's report against the actual code. Scored on accuracy: +score for correctly confirming real issues, -2x for letting false positives through. The Adversarial agent should be harder to convince than the Finder -- its job is to filter noise, not to add more findings.

### Referee
Final arbiter. Evaluates disputed findings. Scored on calibration: +1 for rulings that match ground truth, -1 for rulings that don't. **The correct ground truth exists and will be compared against your rulings** -- this is deliberate pressure toward careful accuracy over hasty agreement.

## Blast Radius Matrix

Choose the review level based on blast radius. Default is FULL -- opt DOWN only when ALL low-risk criteria are met.

| Blast Radius | Review Level | Criteria to Opt Down |
|---|---|---|
| High: shared files, API changes, data model, security | **FULL** (3-agent: Finder + Adversarial + Referee) | MANDATORY at this severity |
| Medium: single feature, no shared interfaces | **STANDARD** (2-agent: Finder + Adversarial) | ALL: no shared files, no API changes, no data model changes |
| Low: docs, comments, config, typo fixes | **SKIP** (no review) | ALL: no logic changes, no test changes, no user-visible changes |

When in doubt, use FULL. The cost of over-reviewing is time. The cost of under-reviewing is shipping bugs.

## Invocation Modes

### Automated (prompt-based enforcement)
`/review` spawns subagents within the session. The agent files (`.claude/agents/Finder.md`, etc.) provide the prompt content. Tool restrictions are **prompt-based** -- the subagent is told "you are read-only" but inherits parent tool access. Practical enforcement is high (subagents follow review prompts reliably), but not mechanical.

### Manual (mechanical + prompt enforcement)
Run `claude --agent=Finder` in a separate terminal. Tool restrictions are **partially mechanical** -- `tools: Read, Grep, Glob, Bash` in the agent file means only those four tools are available (Edit and Write are mechanically absent from the agent's toolbox). Bash is included (agents need `git log`, `ls`, etc.) but is **prompt-restricted** -- agents are instructed to operate read-only: their job is to inspect code and report findings, with no file writes via Bash redirections. This is high-confidence but not a hard platform guarantee for Bash specifically.

Same agent files serve both paths. Same scoring incentives, same role definition. The difference: automated gets prompt-based restriction (works in practice), manual gets mechanical restriction (guaranteed by platform).

## Review as a completion gate

When review is warranted (see the blast-radius matrix), it runs before the step is marked complete:

```
build step -> verify contracts -> adversarial review (if warranted) -> mark complete -> release dependents
```

If review finds issues, the step goes back for fixes -- treated as a contract failure with the same 3-retry limit. In parallel worktrees, each step runs its own independent review over its own diff; integration review (if needed) runs after the branches merge.

## Scoring Calibration

The scoring system exploits a known tendency: agents are biased toward agreement. The incentive structure counteracts this:

- **Finder**: rewarded for finding real issues, penalised for false positives. This prevents shotgun reporting.
- **Adversarial**: penalised MORE for letting false positives through (-2x) than for incorrectly dismissing real issues (-1x). This creates pressure to filter.
- **Referee**: the "ground truth" framing creates pressure toward careful analysis rather than splitting the difference.

After the first 3 uses of this system, compare results against the standard `/review` command to validate that the adversarial pattern catches more real issues without excessive false positives.

## Existing Templates

The `spec-reviewer.md` and `code-quality-reviewer.md` in this directory provide the detailed prompts for spec compliance and code quality review passes. These remain unchanged -- the adversarial review adds the multi-agent scoring layer on top.
