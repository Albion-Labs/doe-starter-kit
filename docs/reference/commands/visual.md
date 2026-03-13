# Visual Output Commands

These commands generate standalone HTML pages that open in your browser. They produce rich, visual documents — diagrams, comparisons, dashboards — that are easier to understand than terminal text for certain kinds of information.

All visual output is saved to the `docs/` directory in your project, so it's version-controlled and you can revisit it later.

---

## /project-recap

**What it does:** Generates a visual HTML page that rebuilds your mental model of the project — where things stand, what happened recently, what's in progress.

**When to use it:** When returning to a project after time away (a weekend, a holiday, a context switch to another project). Instead of reading through `STATE.md` and `todo.md` and `learnings.md` yourself, this command assembles the key information into a single visual page.

**What to expect:** An HTML page that opens in your browser, showing:

- Current project state and active feature
- Recent decisions and why they were made
- What's in progress and what's blocked
- Key learnings from recent sessions
- A visual timeline of recent activity

Think of it as a briefing document. Five minutes reading this page and you're caught up.

---

## /diff-review

**What it does:** Generates a visual HTML page showing a before/after comparison of your recent changes, with code review analysis.

**When to use it:** Before committing, especially for larger changes. Terminal diffs (`git diff`) are functional but hard to read for big changes. This gives you a visual, side-by-side view with annotations.

**What to expect:** An HTML page showing:

- Architecture-level view of what changed (which files, which modules)
- Side-by-side code comparison with syntax highlighting
- Review annotations pointing out potential issues
- Summary of the change's impact

This is particularly useful when you've made changes across multiple files and want to see the full picture before committing. It's easier to spot mistakes in a visual format than in raw diff output.

---

## /plan-review

**What it does:** Generates a visual HTML page comparing where the codebase is now versus where the implementation plan says it should be.

**When to use it:** Mid-feature, when you want to check that the implementation is tracking the plan. Useful for catching drift — where what you're building has diverged from what you planned.

**What to expect:** An HTML page showing:

- The plan's steps, colour-coded by status (done, in progress, not started)
- For completed steps: what was planned vs what was actually built
- For upcoming steps: dependencies and readiness
- Any gaps where the implementation has diverged from the plan

This is the visual equivalent of asking "are we building what we said we'd build?"

---

## /generate-visual-plan

**What it does:** Generates a detailed visual HTML implementation plan for a complex feature, complete with state machines, code snippets, and edge case analysis.

**When to use it:** When you're about to build something complex (3+ steps, multiple interacting components) and you want to think it through visually before writing code. The output is much richer than a text plan — it includes diagrams showing how components interact.

**What to expect:** An HTML page containing:

- State machine diagrams showing component lifecycle
- Code snippets showing proposed interfaces and data structures
- Edge case analysis with handling strategies
- Dependency graph showing build order
- Estimated complexity and risk areas

This is a planning tool, not a building tool. It helps you and Claude agree on what to build before building it. The output can be shared with others for review.

---

## /generate-web-diagram

**What it does:** Generates a standalone HTML diagram — architecture, data flow, relationship map, or whatever visual explanation you need — and opens it in your browser.

**When to use it:** When you need to understand or explain a system visually. Good for architecture overviews, data flow through the application, module relationships, or any concept that's clearer as a picture than as text.

**Example usage:**

```
You: /generate-web-diagram Show me how data flows from the API through
     to the rendered HTML cards
```

**What to expect:** A self-contained HTML file with an interactive diagram. No external dependencies — it works offline. The diagram uses clean, readable layouts with labels and annotations.

Common diagram types:
- **Architecture diagrams** — boxes and arrows showing system components
- **Data flow diagrams** — how data moves through the system, step by step
- **Relationship maps** — how modules, files, or concepts relate to each other
- **Sequence diagrams** — the order of operations in a process

---

## /generate-slides

**What it does:** Generates a magazine-quality slide deck as a self-contained HTML page.

**When to use it:** When you need to present work to others — stakeholders, collaborators, or yourself. The output is polished enough for external audiences.

**Example usage:**

```
You: /generate-slides Create a 5-slide deck explaining the Targeting
     feature: what problem it solves, how it works, key metrics
```

**What to expect:** An HTML file that functions as a slide deck:

- Clean, professional design with consistent styling
- Slides advance with arrow keys or click
- Self-contained (no internet connection needed)
- Includes data visualisations, code snippets, or diagrams as appropriate

The slides are generated from actual project data, not generic templates. If you ask for a feature overview, the slides will reference real metrics, real code, and real screenshots from your project.

---

## A Note on Visual Output

All these commands produce HTML files saved to your `docs/` directory. They're version-controlled, so you can:

- Revisit them later to see what you were thinking at a point in time
- Share them with collaborators (they're self-contained — just send the file)
- Compare plans vs outcomes by looking at planning docs alongside implementation docs

The files are designed to be opened directly in a browser — no server needed, no dependencies.
