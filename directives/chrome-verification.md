# Directive: Chrome Verification

## Goal
Use Claude Code's Chrome integration (MCP tools via the Chrome extension) to automate visual verification, converting `[manual]` checks into machine-verified results wherever possible.

## When to Use
- Running `/snagging` on an [APP] feature with `[manual]` visual items
- Starting an [APP] feature session (prompt Chrome enablement at `/crack-on`)
- Reviewing sign-off items that could be machine-verified
- Any time a `[manual]` criterion describes something Chrome could check (DOM state, element existence, text content, layout, console errors)

## Prerequisites
- Chrome browser open
- "Claude in Chrome" extension installed (Chrome Web Store)
- Chrome enabled in Claude Code: run `/chrome` or start with `claude --chrome`
- App served locally (snagging orchestrator handles this on port 8080)

## How Chrome Verification Works

Claude Code gains MCP tools when Chrome is enabled. These tools let Claude:

| Action | What Claude can check |
|--------|----------------------|
| **Navigate** to a URL | Page loads without errors |
| **Screenshot** the viewport | Visual layout, rendering, element presence |
| **Read DOM** state | Element existence, text content, class names, attributes |
| **Click** elements | Interactive flows (dropdowns, tabs, navigation) |
| **Type** into fields | Search, form inputs, filters |
| **Read console** | JavaScript errors, warnings, failed network requests |

Chrome verification is **interactive** — Claude uses the MCP tools during the session, interprets visual results, and reports pass/fail. It is NOT a scripted pattern like `Verify: run:` or `Verify: file:`.

## Integration Points

### 1. Snagging (primary — pre-merge gate)

**When:** After automated tests (Playwright, Lighthouse) and before presenting the checklist to the user.

**Flow:**
1. Automated tests run (`execution/run_test_suite.py`) — server starts on port 8080
2. Code trace runs
3. Checklist generated
4. **Chrome verification step (NEW):**
   - If Chrome MCP is available, Claude navigates to the served app
   - Claude works through each `[manual]` item and checks what it can:
     - DOM presence checks (element exists, has correct text)
     - Navigation flows (click tab, verify page loads)
     - Console error checks (no JS errors on page load)
     - Layout checks (screenshot + visual assessment)
   - Items Claude can verify get marked `[auto-chrome]` in the results
   - Items requiring subjective judgment stay `[manual]` for the user
5. Checklist presented with Chrome-verified items pre-checked
6. User only needs to verify truly subjective items

**If Chrome is NOT available:** Fall back to current behaviour — all `[manual]` items go to the user. Show: "Chrome not enabled -- run `/chrome` to auto-verify visual items."

### 2. Crack-On (session start — prompt only)

**When:** Starting a session on an [APP] feature.

**Flow:**
- After the kick-off card, if the feature is tagged `[APP]`, show:
  ```
  This is an [APP] feature -- enable Chrome for visual verification?
  Run /chrome to enable, or skip to use manual checks only.
  ```
- Do NOT auto-enable Chrome (it increases context usage). Just prompt.
- If the feature is `[INFRA]`, skip the prompt.

### 3. Per-Step Verification (opportunistic)

**When:** After completing an [APP] step that has `[manual]` criteria involving visible UI changes.

**Flow:**
- If Chrome is already enabled AND the app is being served locally, Claude can navigate to the relevant page and screenshot the result
- This gives the user immediate visual feedback in the conversation
- Do NOT start a server just for this — only use if one is already running

### 4. Sign-Off Acceleration

**When:** Features in `## Awaiting Sign-off` have `[manual]` items that could be machine-verified.

**Flow:**
- When the user runs `/snagging` on a sign-off feature, Chrome verification runs on all `[manual]` items
- Items that Chrome can verify are pre-checked in the new checklist
- The user reviews only the remaining subjective items
- This reduces the 8 pending manual items to only the ones that genuinely need human eyes

## What Chrome CAN and CANNOT Verify

### Can verify (convert to [auto-chrome]):
- "Element X renders on the page" → Navigate + check DOM
- "Card shows correct data" → Read element text content
- "No console errors on page load" → Read console after navigation
- "Tab navigation works" → Click tabs, verify content changes
- "Search returns results" → Type query, check results appear
- "Page loads without errors" → Navigate, check status + console
- "Responsive layout" → Resize viewport, screenshot at breakpoints

### Cannot verify (keep as [manual]):
- "UI looks professional/polished" → Subjective aesthetic judgment
- "Interaction feels smooth" → Perceived performance, not measurable
- "Content is clear and understandable" → Requires domain knowledge
- "Accessibility is good" → Partially automatable (use axe-core), but full a11y needs human testing
- "Print layout renders correctly" → Chrome can't trigger print preview reliably
- "Data visualisation tells the right story" → Analytical judgment

### Grey area (use Chrome + describe findings, let user judge):
- "Layout looks correct" → Screenshot and describe what's visible, but don't judge aesthetic quality
- "Colours are consistent" → Can check CSS values, but can't judge if they "feel right"
- "Mobile layout works" → Can resize and screenshot, but "works" is subjective

## Result Tagging

When Chrome verifies a `[manual]` item, tag it `[auto-chrome]` in the exported results to distinguish from `[auto]` contract criteria and `[auto]` snagging results:

```
- [x] [auto-chrome] Tab navigation works -- clicked 3 tabs, all loaded correct content
- [x] [auto-chrome] No console errors on page load -- checked 5 pages, 0 errors
- [ ] [manual] UI looks polished and professional -- requires human judgment
```

## Edge Cases
- **Chrome extension disconnects mid-session:** The extension service worker can go idle during long sessions. If tools fail, tell the user to refresh Chrome and re-run `/chrome`.
- **Port conflict:** If port 8080 is occupied by something else, snagging orchestrator will detect this. Don't try to start a second server.
- **Login-gated pages:** Chrome shares the user's browser session, so authenticated pages work. But if a login page appears, pause and ask the user to log in manually.
- **JavaScript dialogs:** `alert()`/`confirm()` block Chrome automation. If encountered, ask the user to dismiss manually.

## Verification
- [ ] Directive exists at `directives/chrome-verification.md`
- [ ] CLAUDE.md triggers reference this directive
- [ ] Snagging command references Chrome verification step
- [ ] Crack-on prompts Chrome for [APP] features
