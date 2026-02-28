# Directive: Documentation Governance

## Goal
Ensure governed project documents stay current, versioned, and traceable as the product evolves.

## When to Use
Before any commit that:
- Adds or removes a dataset or external dependency
- Changes legal/regulatory position or adds personal data handling
- Completes a feature (check all governed docs for staleness)
- Creates a new governed document

## Inputs
- The commit diff (what changed)
- The governed document registry below
- Current app version from STATE.md or todo.md

## Governed Document Registry

| Document | Path | Domain | Created |
|----------|------|--------|---------|
| Learnings | `learnings.md` | Project patterns, decisions, API quirks, UI patterns | v0.1.0 |

<!-- Add governed documents to this registry as they're created. -->

## Front-matter Format

Every governed document must have this block at the top:

```
---
Version: 1.0
Last updated: DD/MM/YY
Applies to: v0.X.Y
Updated by: [session summary of what changed]
---
```

- **Version:** Minor bump (1.0 → 1.1) for content additions. Major bump (1.0 → 2.0) for structural rewrites.
- **Last updated:** Date of the most recent edit.
- **Applies to:** The app version this doc was last verified against.
- **Updated by:** One-line summary of what changed and why.

## Process

1. **Before committing**, check: does this change touch a governed doc's domain?
   - Refer to the registry table above to identify which doc(s) may be affected.
   - New pattern, decision, or API quirk → update `learnings.md` (already covered by Rule 8)
2. **If yes**, open the relevant doc and:
   - Make the content update
   - Bump the Version (minor or major as appropriate)
   - Set Last updated to today
   - Set Applies to to the current app version
   - Write a one-line Updated by summary
3. **If no**, check for staleness: is any governed doc's "Applies to" more than 1 minor version behind the current app? If yes, flag it to the user — it may need a review even if this commit didn't directly affect it.
4. **Include the doc update in the same commit** as the code change.

## Outputs
- Updated governed document(s) with current front-matter
- Staleness flag if any doc is >1 minor version behind

## Edge Cases
- **Creating a new governed doc:** Use the front-matter template above. Add it to the registry table in this directive. Add its path to the Directory Structure in CLAUDE.md.
- **Deleting a governed doc:** Requires explicit user permission. Remove from registry. Update CLAUDE.md Directory Structure.
- **Staleness discovered mid-session:** Flag to user. They decide whether to update now or defer. If deferred, note it in STATE.md as a known gap.
- **learnings.md:** Already has its own update rules via Rule 8. The front-matter addition is new — add it on next edit, don't force a separate commit just for front-matter.

## Verification
- [ ] Every governed doc has a valid front-matter block
- [ ] "Applies to" is within 1 minor version of the current app version
- [ ] Registry table in this directive matches the actual docs on disk
