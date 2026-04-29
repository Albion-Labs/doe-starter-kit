# Product Roadmap

A living notepad for what to build. Sections flow from most concrete to most speculative. When you're ready to build something, tell Claude to plan it.

<!--
Claude: section rules
- ## Up Next: Planned and scoped. Has todo.md steps or a plan file. Pull from here when Current is empty.
- ## Suggested Next: Claude's strategic recommendation based on project state. 2-3 items max. Update when project state changes significantly (feature ships, new data, user feedback). If empty, promote from Ideas or pitch new ones.
- ## Must Plan: Important items that need scoping before they can be built. Blockers, prerequisites, compliance. Not ideas — these WILL be built, just not yet planned.
- ## Ideas: Casual captures. No commitment, no order. Just don't lose them.
- ## Claude Suggested Ideas: AI-pitched additions based on the codebase and product direction. Refresh periodically. User can promote to Ideas, Must Plan, or Up Next.
- ## Parked: Considered but not pursuing right now.
- ## Complete: Shipped, newest first.
- Every entry gets a *(pitched/added DD/MM/YY)* or *(added HH:MM DD/MM/YY)* timestamp.
- Status tags: PLANNED, IN PROGRESS, COMPLETE. Used on Up Next and Must Plan entries.
- When pitching (Rule 9): add to Ideas with timestamp. If the user says "this is important" or "note for later", add to Must Plan instead.
-->

## Up Next
<!-- Planned and scoped. Has todo.md steps or a plan file. Pull from here when Current is empty. -->

## Suggested Next
<!-- Claude's strategic recommendation based on where the project is now. 2-3 items, updated when project state changes. -->

## Must Plan
<!-- Important items that WILL be built but need scoping first. Blockers, prerequisites, compliance. Not ideas — these are commitments waiting for a plan. -->

## Ideas
<!-- Anything you might want to build. No commitment, no order. Just capture it. -->

## Claude Suggested Ideas
<!-- AI-pitched additions based on the codebase and product direction. Refreshed periodically. Promote to Ideas or Must Plan if interesting. -->

## Parked
<!-- Things you considered but aren't pursuing right now. Keeps them out of the way without losing them. -->

## Complete
<!-- Shipped features, newest first. One-line summary each, tagged [APP] or [INFRA]. For step-by-step detail, see tasks/archive.md. -->

- **Pink Elephant rewrite (v1.59.0)** [INFRA] — Converted load-bearing negation rules across CLAUDE.md, the universal template, and 35 directives to positive "When X, do Y" form per the Pink Elephant article (arxiv 2503.22395) and IFEval/InFoBench evidence. Added `Tradeoff:` lines to 25 of 26 flat directives. Fixed PreToolUse and PostToolUse matcher casing in `.claude/settings.json` (kit hooks were silently non-functional since their introduction; case-sensitive Tool name strings now match real tool calls). Extended `protect_directives.py` and `block_secrets_in_code.py` to the `Bash` matcher so redirected writes (`cat >`, `tee`, `sed -i`) covering `directives/` files or carrying secret-shaped values are caught. Authored `migrations/v1.59.0.md` with 135 OLD/NEW/WHY phrase pairs across 31 files plus four behavioural-change records, consumed by a new `/pull-doe` pre-flight phase that warns projects about retired phrases before they pull. *(shipped 29/04/26)*
