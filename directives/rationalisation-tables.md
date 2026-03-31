# Directive: Rationalisation Tables

## Goal
Map every common excuse for skipping a DOE guardrail to the reality of why it matters. When you catch yourself rationalising, find your excuse here and do what the table says.

## When to Use
- When about to skip a guardrail, override a rule, or rationalise not following a process
- When a thought starts with "this probably doesn't need...", "just this once...", or "I already know..."
- When the 1% rule fires for any trigger (see CLAUDE.md Progressive Disclosure)
- When `/test-methodology` flags rationalisation drift

## How This Works

Every guardrail in DOE exists because something went wrong without it. These tables map the internal excuse an agent constructs to bypass a rule to the reality of what happens when you do. The format is consistent: recognise the excuse, understand why it fails, do the right thing instead.

**If your current thought matches any excuse in any table below: stop. Do what the "What to do instead" column says. No exceptions.**

---

## 1. TDD Rationalisations

Extends the table in `directives/best-practices/tdd-and-debugging.md`. That table covers the 7 most common excuses for skipping tests. These additional rows cover subtler rationalisations:

| Excuse | Why it's wrong | What to do instead |
|--------|---------------|-------------------|
| "Too simple to test -- it's a one-liner" | One-liners have edge cases. `x.trim()` fails on null. The test takes less time than this thought. | Write the test. If it's truly trivial, it takes 10 seconds. |
| "I manually tested it in the terminal" | Manual tests evaporate. The next person (including future-you) has no proof it works. | Convert your terminal check into a `Verify: run:` pattern or pytest case. |
| "I'm exploring -- I'll test once the design settles" | Exploration without tests produces code you don't understand a week later. Tests ARE the exploration. | Write a characterisation test for what you've built so far. Refactor the test when the design changes. |
| "Sunk cost -- I've already written the code, adding tests now is wasteful" | Tests written after the code catch fewer bugs (confirmation bias). But they still document intent and prevent regressions. | Write the tests anyway. Retroactive tests are better than no tests. |
| "TDD is dogmatic for this kind of work" | TDD is a tool, not a religion. But the alternative is "no tests", not "tests later". The rationalisation table exists because "later" doesn't come. | Choose your testing strategy (TDD, test-after, property-based) but choose one. "None" is not an option. |
| "The test would just be testing the framework" | If you're wrapping a framework call, test your wrapper's behaviour, not the framework. If there's no wrapper logic, you don't need a test -- but be honest about whether there really is no logic. | Ask: "Does my code make any decision?" If yes, test the decision. |
| "Tests will slow me down -- I'm on a deadline" | Untested code produces bugs that cost 10x more time than the test. Every "deadline" shortcut becomes technical debt that slows the next deadline. | Time-box the test to 5 minutes. If it takes longer, the design needs rethinking -- that's valuable information. |
| "The existing code has no tests so adding them here is inconsistent" | Inconsistency in the right direction is called progress. Every tested function is one fewer regression risk. | Add the test. Don't use existing gaps as permission to create more. |

---

## 2. Verification Rationalisations

| Excuse | Why it's wrong | What to do instead |
|--------|---------------|-------------------|
| "Should work now -- I'm confident in the change" | Confidence is not evidence. The confident change is the one most likely to harbour an unchecked assumption. | Run the verification. Confidence makes it fast, not unnecessary. |
| "I'm confident this works -- I've done this before" | Past success proves nothing about this context. Different files, different state, different edge cases. | Verify in THIS context. Muscle memory is not a substitute for evidence. |
| "Just this once I'll skip verification -- it's a trivial change" | "Trivial" changes are the ones that break production because nobody checks them. A typo fix that changes a variable name can break downstream code. | Verify trivially. `grep` takes 2 seconds. `ls` takes 1. Match the effort to the risk. |
| "The linter/formatter passed -- that's verification enough" | Linters check syntax and style. They don't check logic, correctness, or whether the output matches the spec. | Linting is layer 1. Run the actual verification criteria from the contract. |
| "The subagent said it succeeded" | Subagents are agents. Agents rationalise. Their success report is a claim, not proof. | Run contract verification yourself. Check file existence, content, command output. |
| "I'll check it all at the end" | Errors compound. A bug in step 2 that's caught in step 5 requires re-doing steps 3 and 4. Verify per-step. | Verify immediately after each step. The cost is seconds. The savings are hours. |
| "A partial check is enough -- I verified the main path" | Edge cases live in the paths you didn't check. The main path usually works. The bug is in the branch. | Check every contract criterion. If the contract is too broad, tighten it -- don't skip parts. |
| "Different words so the rule doesn't apply" | If the spirit of a verification rule applies, it applies. Reframing the task to avoid a rule is itself a rationalisation. | Read the rule's intent, not just its keywords. If in doubt, verify. |

---

## 3. Code Review Rationalisations

| Excuse | Why it's wrong | What to do instead |
|--------|---------------|-------------------|
| "Changes are small -- review is overkill" | Small changes have outsized impact. A one-character typo in a config can bring down a service. Small diffs are the fastest to review. | Review it. Small = fast review. No excuse. |
| "I wrote it so I know it works" | You know what you intended, not what you built. Author blindness is real -- you read what you meant to write, not what's on screen. | Review as if someone else wrote it. Or dispatch a review subagent. |
| "Review slows me down -- I'll review at the end" | End-of-feature review catches issues when fixing them is most expensive. Per-PR review catches them when the context is fresh. | Review is part of the work, not overhead. Budget time for it. |
| "It passed CI -- that's the review" | CI checks syntax, tests, and style. It doesn't check architecture, over-engineering, spec compliance, or silent failures. | CI is necessary but not sufficient. Human/AI review catches what automation misses. |
| "No one else is reviewing anyway" | You are someone. Self-review with an adversarial mindset catches real bugs. The `/review` command exists precisely for solo developers. | Run `/review`. The adversarial framing compensates for author bias. |
| "I'll review when the feature is complete" | By then you've forgotten why you made early decisions. And if an early decision was wrong, everything built on it is wrong. | Review at the PR level (per-feature), not at the end of a multi-feature sprint. |

---

## 4. Contract Writing Rationalisations

| Excuse | Why it's wrong | What to do instead |
|--------|---------------|-------------------|
| "this step is obvious -- contracts are overhead" | Obvious steps have implicit assumptions. The contract makes them explicit. "Add a button" is obvious until you specify where, what it does, what it's labelled, and what happens on error. | Write the contract. Obvious steps get simple contracts -- still needed. |
| "Manual is fine here -- I can't automate this check" | Most "can't automate" claims are wrong. DOM checks, file content, command output -- all automatable. Only keep [manual] for visual quality, interaction feel, and subjective judgment. | Try writing it as [auto] with a `Verify: run:` or `Verify: html:` pattern first. Only fall back to [manual] if it genuinely requires human eyes. |
| "One auto criterion is enough" | One criterion checks one thing. Steps do multiple things. Under-specified contracts let bugs through and make review harder. | Match criteria count to the step's scope. One criterion per distinct claim. |
| "I'll add contracts later -- let me build first" | Building without contracts is building without acceptance criteria. You don't know when you're done. Rework is guaranteed. | Write contracts before code. They take 2 minutes and save 20. |
| "The verify pattern is close enough" | "Close enough" fails silently. `file: foo contains bar` either matches or doesn't. Approximate patterns give false passes. | Write exact patterns that match actual implementation names. Check against code if editing existing contracts. |
| "This is an INFRA step so contracts can be loose" | INFRA code is the foundation everything else builds on. A bug in build.py breaks every feature. INFRA contracts should be tighter, not looser. | INFRA steps get full contracts. The only difference: no [manual] criteria required. |

---

## 5. Scope Creep Rationalisations

| Excuse | Why it's wrong | What to do instead |
|--------|---------------|-------------------|
| "While I'm here I should also fix this" | You're not here to fix that. The "while I'm here" impulse creates commits that mix concerns, break atomic steps, and make review harder. | Note it. Add it to todo.md or learnings.md. Do it in a separate step or session. |
| "This is a quick fix -- barely adds any scope" | Quick fixes have side effects. Quick fixes need testing. Quick fixes need review. "Quick" scope creep is still scope creep. | If it takes less than 60 seconds AND doesn't change behaviour, do it. Otherwise, separate step. |
| "It's related to what I'm building" | Related is not the same as required. The current step has a contract. If the "related" work isn't in the contract, it's out of scope. | Check the contract. If it's not there, it's not this step. |
| "The user will want this" | Maybe. But they didn't ask for it. Building unrequested features is the #1 cause of wasted effort. | Pitch it (Rule 9). Don't build it. Let the user decide. |
| "It'll be harder to do later" | Maybe. But doing it now violates the atomic step principle, mixes concerns, and makes this PR harder to review. The cost of "later" is usually lower than the cost of "while I'm here". | Accept the future cost. Ship what's scoped. Revisit when it's the priority. |
| "I'm just refactoring, not adding features" | Refactoring that isn't requested is scope creep. Refactoring changes structure, which changes risk. Unrequested refactoring is the most common form of "helpful" scope creep. | Only refactor what the current step requires. Flag structural improvements for a dedicated refactoring step. |

---

## 6. Trigger Loading Rationalisations

| Excuse | Why it's wrong | What to do instead |
|--------|---------------|-------------------|
| "I already know this area -- loading the directive would waste context" | You know what you knew last time. The directive may have been updated. Your memory of it may be incomplete or wrong. Context is cheaper than bugs. | Load it. Skim if you must. 30 seconds of reading vs 30 minutes of re-learning. |
| "The trigger doesn't quite match -- this is slightly different" | The 1% rule exists for this exact rationalisation. If there's even a 1% chance the trigger applies, load the directive. "Slightly different" is usually "exactly the same with one detail changed." | Load it. If it truly doesn't apply after reading, you've lost 30 seconds. If it does apply and you skipped it, you've lost much more. |
| "I'll check after I've started -- I want to get going first" | Starting without context means building on assumptions. If the directive contradicts your assumptions, you rework. Reading first is always cheaper than reworking after. | Read the directive before writing any code. Every time. |
| "Loading the directive will slow me down" | Not loading it will slow you down more when you hit the edge case it documents. Directives exist because someone already hit the wall you're about to hit. | Slow is smooth, smooth is fast. Load, read, build correctly once. |
| "This is too simple to need a directive" | The simpler the task, the faster the directive read. If it's truly simple, the directive confirms your approach in 10 seconds. If it's not as simple as you think, the directive just saved your session. | Load it. Simple tasks deserve simple verification. |
| "I'm experienced enough to know the patterns" | Experience creates the most dangerous blind spots -- overconfidence in familiar patterns applied to new contexts. The directive captures patterns from multiple sessions, not just your memory of one. | Load it. Treat directives as external memory, not training wheels. |

---

## Meta-Rationalisation

If you find yourself thinking "the rationalisation tables don't apply here" or "this situation is genuinely different" -- that IS a rationalisation. The tables apply. The situation is not different enough to matter.

**The Iron Law:** No guardrail may be skipped without explicit, reasoned justification stated before the skip (not after). "I decided to skip X because Y" stated in advance is legitimate professional judgment. Silently not doing X is a rationalisation.
