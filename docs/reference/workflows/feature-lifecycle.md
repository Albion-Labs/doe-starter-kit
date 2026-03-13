# Building a Feature from Start to Finish

Every feature follows the same lifecycle, from a vague idea to a shipped, verified result. This page walks through each stage so you know what to expect and what your role is at each point.

```
Idea → Plan → Queue → Current → Build → Verify → Ship → Awaiting Sign-off → Done → Retro
```

---

## 1. The idea

Every feature starts as an idea. It might be yours, or someone might suggest it, or Claude might pitch it while working on something else.

At this stage, the idea might be vague — that's fine. You have two paths:

- **If it's vague:** Run `/scope` to clarify it through conversation. Claude will ask you questions to pin down what you actually want — who it's for, what the output looks like, what counts as "done." This produces a brief you can review before committing to building anything.

- **If it's clear:** Describe it to Claude and ask it to plan. For example: "I want a page that shows voter turnout by constituency on a map. Plan this feature."

## 2. Planning

Claude writes a plan to `.claude/plans/feature-name.md`. This plan includes:

- **What to build** — the end result, described concretely
- **How to build it** — technical approach, tools, data sources
- **What order** — steps sequenced so each one builds on the last
- **What model and effort for each step** — some steps need deep reasoning, others are mechanical. The plan assigns the right level of effort to each.

From this plan, Claude creates:

- **Steps in `tasks/todo.md`** under the Queue section. Each step has a contract — testable criteria that define exactly what "done" means for that step. Contracts use `[auto]` for things Claude can verify itself and `[manual]` for things that need your eyes.
- **A ROADMAP.md entry** under "Up Next" so the feature is visible in the big picture.

Review the plan. If the approach doesn't make sense to you, ask Claude to explain its reasoning or suggest alternatives. This is the cheapest time to change direction — before any code exists.

## 3. Starting the build

When it's time to build, the feature moves from Queue to Current in todo.md. This means Claude is actively working on it.

Each step becomes one commit — a single, focused save point in git. This keeps changes small and reversible. If step 4 breaks something, you can undo step 4 without losing steps 1 through 3.

The first step typically starts the feature's version number. For example, if your project is at v0.4.2 and you start a new feature, step 1 might be v0.5.0.

## 4. Building step by step

For each step, the cycle is:

1. **Claude builds** — writes code, creates files, makes changes
2. **Claude runs contract checks** — the `[auto]` criteria from the step's contract are tested automatically
3. **Claude fixes any failures** — if a check fails, Claude diagnoses the issue and attempts up to 3 fixes before asking you for help
4. **Claude commits** — the passing step is saved to git with a clear message describing what changed

Version numbers bump with each step (v0.5.0, v0.5.1, v0.5.2, and so on), so you can always tell which step produced which version.

`[manual]` criteria — things like "the chart looks right" or "the layout works on mobile" — are not checked at this stage. They're collected and presented to you later, so Claude can keep building without stopping after every step to wait for your approval.

## 5. Mid-feature checkpoint (for big features)

For larger features (five or more steps), Claude pauses after the core UI step — typically the step where the main visual elements first appear — and presents all accumulated manual checks up to that point.

This is your chance to catch visual issues early, before later steps build on top of them. You test what's there, report any problems, and Claude fixes them before continuing.

For smaller features, this checkpoint is skipped and all manual checks are presented at the end.

## 6. Housekeeping

Before the feature is complete, there's a housekeeping step that handles:

- **Changelog entry** — a human-readable record of what changed in this version
- **Version bump** — the final version number for the feature
- **Roadmap update** — moving the feature from "In Progress" to reflect its new status

This is always the second-to-last step. It's not glamorous, but it keeps your project's records clean and accurate.

## 7. Retro

After building is complete, Claude runs a quick retrospective:

- **What worked** — things that went smoothly and should be repeated
- **What was slow** — bottlenecks, confusing requirements, or technical friction
- **What to do differently** — concrete improvements for next time

Any learnings get recorded to `learnings.md`, where they become part of the project's institutional memory. Next time a similar situation comes up, Claude will already know the lesson.

The feature moves to "Awaiting Sign-off" in todo.md.

## 8. Awaiting Sign-off

The feature is now code-complete — all steps are built, all `[auto]` criteria pass. But `[manual]` items still need human verification. The feature sits in the `## Awaiting Sign-off` section of todo.md until you test everything.

Claude presents the full manual test checklist — every `[manual]` criterion from every step, organised so you can work through them systematically. The SIGN-OFF row in `/stand-up` and `/sitrep` cards reminds you how many manual items are pending.

For each item, Claude tells you:
- What to test
- How to test it
- Which step and contract it relates to

You test everything that needs human eyes. Report any failures, and Claude fixes them. Once everything passes, the feature moves to "Done" in todo.md and "Complete" in ROADMAP.md.

---

## The full picture

```
Idea               You describe what you want (or run /scope to clarify)
  ↓
Plan               Claude writes a plan with steps, contracts, and sequencing
  ↓
Queue              Steps added to todo.md, feature added to ROADMAP.md
  ↓
Current            Feature moves to active work
  ↓
Build              Each step: build → verify → fix → commit
  ↓
Verify             Mid-feature checkpoint for big features, final sign-off for all
  ↓
Ship               Changelog, version bump, roadmap update
  ↓
Awaiting Sign-off  All auto checks pass; manual items await your testing
  ↓
Done               All contracts verified — feature complete
  ↓
Retro              What worked, what didn't, learnings recorded
```

Every feature follows this path. Small features move through it in a single session. Large features span multiple sessions, with stand-up and wrap keeping state intact between them.
