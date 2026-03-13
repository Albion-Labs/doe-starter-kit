# Product & Planning Commands

These commands help you think about what to build, not just how to build it. They cover idea generation, feature scoping, and honest assessment of where things stand.

---

## /pitch

**What it does:** Reads the current project state and generates strategic suggestions for what to build next.

**When to use it:** When you've finished a feature and are wondering what's next. Or when you want Claude to look at the project with fresh eyes and spot opportunities you might have missed.

**How it works:** Claude reads across the project — `ROADMAP.md`, `STATE.md`, `learnings.md`, the codebase itself — and identifies gaps, natural extensions, or improvements that would add genuine value. It doesn't generate ideas randomly; it bases suggestions on what actually exists and what would logically come next.

**What to expect:** One or more brief pitches, each with two parts: what the idea is and why it matters.

```
PITCH: Add constituency comparison view

The targeting data already includes per-constituency metrics, but
users can only view one at a time. A side-by-side comparison would
let campaigners quickly identify which constituencies to prioritise —
the data is already there, it just needs a new view.

Effort: ~2 steps. Reuses existing card components.
```

Pitches are suggestions, not commitments. You can:
- Say **"add it"** to put it on the roadmap's Ideas section
- Say **"this is important"** to flag it for near-term planning
- Ignore it entirely

Claude is told to only pitch when something genuinely clicks — not to fill space.

---

## /scope

**What it does:** Takes a fuzzy idea and turns it into a clear, buildable brief through a guided conversation.

**When to use it:** When you have an idea but haven't figured out the details. Maybe you know the problem but not the solution. Maybe you know roughly what you want but haven't thought through edge cases. This command structures the thinking.

**How it works:** The scoping session has three phases:

1. **Explore** — What problem are we solving? Who has this problem? How do they deal with it today? Claude asks questions to understand the motivation and context.

2. **Define** — What does the solution look like? What are the key interactions? What data does it need? This phase shapes the idea into something concrete.

3. **Bound** — What's in scope and what's not? What's the minimum viable version? What could be added later? This phase prevents scope creep by drawing clear lines.

**What to expect:** A back-and-forth conversation (not a monologue). Claude asks questions, you answer, and the scope narrows with each round. At the end, you get a scoping document:

```
SCOPE: Constituency Comparison View

Problem: Campaigners need to compare constituencies side-by-side
         to prioritise resource allocation.

Solution: Split-screen view showing 2-3 constituencies with
          key metrics aligned for easy comparison.

In scope:
  - Select constituencies from dropdown
  - Side-by-side metric cards
  - Highlight differences above threshold

Out of scope (future):
  - More than 3 constituencies
  - Custom metric selection
  - Export comparison as PDF

Dependencies: Requires constituency data (already available)
Estimated steps: 4
```

This document can become a `ROADMAP.md` entry or a set of `todo.md` tasks. The scoping session doesn't build anything — it just clarifies what to build.

---

## /roast

**What it does:** Reads the codebase and gives you an honest, humorous critique.

**When to use it:** When you want brutal honesty about code quality. Also useful as a sanity check before a demo or release — better to find the embarrassing bits yourself than have someone else find them. Or just when you want entertainment.

**How it works:** Claude scans the project looking for:

- Messy code that works but shouldn't
- Forgotten TODOs and FIXMEs
- Architectural smells (things that will cause pain later)
- Inconsistencies (doing the same thing three different ways)
- Dead code (functions that nothing calls)
- Overly clever solutions that should be simpler

**What to expect:** A candid assessment with a sense of humour:

```
ROAST:

Your filter logic works, but it's written like you were solving
a puzzle, not writing maintainable code. Line 87 of filters.py
has a list comprehension nested inside a dict comprehension
inside a generator expression. Future-you will not thank
present-you for this.

There are 4 TODO comments older than 30 days. They're not TODOs
at that point — they're prayers.

execution/build.py reads the same config file 3 times in the
same function. It's not wrong, but it is a choice.

On the bright side: your test coverage is solid, your commit
messages are clear, and the data pipeline is genuinely clean.
```

The roast is constructive underneath the humour — each observation points to something you could actually improve. Nothing is mean-spirited, but nothing is sugarcoated either.
