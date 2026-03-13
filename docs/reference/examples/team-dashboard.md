# Example: Team Dashboard

**Starting point:** "Full spec with roadmap"

This walkthrough follows a team building a multi-user dashboard with authentication and role-based views. They have a complete spec, a phased roadmap, and a timeline. It shows how DOE scales to larger projects — parallel work, governed documentation, and a system that gets faster the longer you use it.

---

## The idea

> "Team dashboard with three roles: admins see everything, managers see their team's data, members see their own. Authentication via email invite. Real-time updates when data changes."

This is a serious project. It has users, roles, authentication, real-time data — each one a significant feature on its own. Building this in a single session isn't realistic. Building it without structure would be chaos.

## How you'd start

The roadmap is already written. It breaks the project into three phases:

**Phase 1 — Foundation:** Authentication, user management, basic role assignment
**Phase 2 — Views:** Admin dashboard, manager team view, member personal view
**Phase 3 — Polish:** Real-time updates, notifications, onboarding flow

Claude translates this into a plan file with 12+ steps across the three phases. Each step has a full contract. The first few steps in `todo.md` look like:

```
## Queue — Phase 1

1. [ ] Email invite + authentication flow
   Contract:
   - [ ] [auto] Auth module exists. Verify: file: src/auth/auth.js exists
   - [ ] [auto] Can create invite and verify token. Verify: run: node tests/auth.test.js
   - [ ] [auto] Invalid tokens rejected. Verify: run: node tests/auth-invalid.test.js
   - [ ] [manual] Invite email is clear — user knows what to do with it

2. [ ] User management — create, deactivate, assign roles
   Contract:
   - [ ] [auto] User CRUD operations work. Verify: run: node tests/user-crud.test.js
   - [ ] [auto] Role assignment persists. Verify: run: node tests/roles.test.js
   - [ ] [manual] Admin can manage users without confusion

3. [ ] Role-based data access
   Contract:
   - [ ] [auto] Admins see all data. Verify: run: node tests/access-admin.test.js
   - [ ] [auto] Managers see only team data. Verify: run: node tests/access-manager.test.js
   - [ ] [auto] Members see only own data. Verify: run: node tests/access-member.test.js
```

There's also a governed document — a security policy directive in `directives/security-policy.md` — that defines rules for the auth system: how tokens work, session expiry, what gets logged. Claude reads this directive whenever it's working on authentication or access control, ensuring the auth system is built to spec rather than to whatever Claude thinks is reasonable.

## What a session looks like

### Sessions 1-4: Phase 1 (Foundation)

These sessions build auth and user management one step at a time. Each session starts with `/stand-up`, builds one or two steps, verifies contracts, commits, and ends with `/wrap`.

By session 4, the auth system works: invites go out, tokens verify correctly, roles restrict data access. The automated contract checks caught two bugs along the way — a token that didn't expire when it should, and a manager role that could see data from a different team.

### Sessions 5-6: Phase 2 with parallel work

Phase 2 has three independent views (admin, manager, member) that don't share code. This is where multi-agent waves come in.

You run `/agent-launch` to start a wave — two terminals working simultaneously:

- **Terminal 1** builds the admin dashboard view
- **Terminal 2** builds the manager team view

Each terminal works on its own files. Neither touches the other's code, shared state files, or the auth system built in Phase 1. You check progress with `/agent-status`:

```
Wave 2 — Phase 2 views
  Terminal 1: Admin dashboard — step 4/6 (building data tables)
  Terminal 2: Manager team view — step 3/5 (building team selector)
  No conflicts detected.
```

When both terminals finish, the results merge cleanly because they worked on separate files. The member personal view is built in the next session.

### Sessions 7-10: Phase 3 (Polish)

Real-time updates, notifications, onboarding. By now, the project has a rich `learnings.md` — patterns discovered during Phase 1 and 2 that Claude uses automatically:

- Token refresh timing (learned from the expiry bug in Phase 1)
- Role-checking patterns (learned from the data access bug)
- UI layout conventions (established during the dashboard views)

Claude doesn't rediscover these patterns. It reads them at the start of every session and applies them. Session 10 goes noticeably faster than Session 1 — not because the work is easier, but because the project has accumulated knowledge that prevents repeated mistakes.

### Phase retros

At the end of each phase, you run a retro: what worked, what didn't, what should change for the next phase. These findings get logged — some to `learnings.md` (project-specific patterns), some to the global `~/.claude/CLAUDE.md` (universal patterns any project could use).

Phase 1's retro might note: "Auth testing took longer than expected because we didn't have test utilities for creating fake users. Built a test helper — reuse it in Phase 2." Phase 2's retro might note: "Parallel sessions saved a full day on the dashboard views. Use waves for any phase with 2+ independent features."

## What DOE gives you

This walkthrough shows DOE at full scale:

**ROADMAP.md tracked the multi-phase plan from day one.** At any point, anyone could look at the roadmap and see what was done, what was in progress, and what was coming. This matters when there's a timeline — you can see early if a phase is running behind.

**Multi-agent waves let two features build simultaneously.** The admin and manager views were independent, so they built in parallel. The coordination system kept them from stepping on each other's files. What would have been four sequential sessions became two parallel ones.

**Governed docs ensured auth was built to spec.** The security policy directive wasn't a suggestion — it was a constraint. Claude read it every time it touched auth code. When it needed to decide how long a session token should last, it didn't guess — it checked the directive.

**Retros at each phase captured what worked and what didn't.** Phase 1's lessons made Phase 2 smoother. Phase 2's lessons made Phase 3 faster. This isn't just "we learned things" — it's systematic: the learnings are in files that Claude reads automatically, so the improvements happen without you reminding it.

**50+ sessions of learnings made later phases dramatically faster than the first.** By Phase 3, `learnings.md` contained dozens of project-specific patterns: API quirks, UI conventions, testing shortcuts, edge cases. Claude read these at every stand-up and applied them without being told. The compounding effect is real — the project gets easier to work on the longer you work on it.

---

This is DOE at scale: a multi-phase project with parallel work, governed documentation, and a system that genuinely improves over time. The same framework that organised a simple recipe book handles a team dashboard with authentication and role-based access — the principles are identical, the scale is different.
