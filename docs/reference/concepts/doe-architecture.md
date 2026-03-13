# DOE Architecture

## The Problem

When you use AI to write code without any structure, things go wrong in predictable ways:

- **It forgets.** Each new conversation starts from scratch. Claude doesn't remember that you renamed a file yesterday, or that the database schema changed last week.
- **It improvises.** Without rules, Claude creates files wherever it feels like, names things inconsistently, and invents its own conventions that clash with what's already there.
- **It can't undo.** If Claude makes a mistake three steps deep, there's no clean way to roll back. The changes are tangled together.
- **It bluffs.** Claude will confidently tell you something works when it doesn't. Not maliciously — it genuinely believes it. But belief isn't the same as proof.

DOE prevents all four problems. It gives Claude a framework: written instructions it can read, scripts it can run, and checkpoints it must pass before declaring victory.

## The Three Layers

DOE stands for **Directive, Orchestration, Execution**. Each layer has a specific job.

### Directive — The Instructions

**Where:** `directives/` folder
**What:** Plain English instructions written in markdown files

Directives are like Standard Operating Procedures (SOPs) — step-by-step instructions for handling specific tasks. They tell Claude what to do, what to watch out for, and what "done" looks like.

For example, a data import directive might say:

> When importing external data, always cache the download locally first. Validate the format before processing. Log what you imported and how many records you got. If the source is an API with rate limits, add a delay between requests.

You write these once. Claude reads the right one automatically based on what it's doing — if you ask it to import data, it loads the data import directive. If you ask it to build a UI component, it loads the UI directive.

Directives contain no code. They're pure intent — what you want to happen and why.

### Orchestration — The Decision-Maker

**Where:** Claude itself (the AI)
**What:** The intelligent router between your instructions and the code that runs

Claude is the orchestrator. When you give it a task, it:

1. Reads the relevant directive to understand the rules
2. Checks what execution scripts already exist
3. Decides what order to do things in
4. Calls the right scripts with the right inputs
5. Handles errors when things go wrong
6. Asks you for clarification when something is ambiguous

This is where AI reasoning belongs — making judgment calls, understanding context, choosing between approaches. Claude is good at this. The key is making sure it reasons about *what* to do, not *how* the mechanics work. The mechanics are handled by the next layer.

### Execution — The Machinery

**Where:** `execution/` folder
**What:** Python scripts that do the actual work

Execution scripts are deterministic — they run the same way every time with the same inputs. They handle API calls, data transformations, file operations, calculations. There's no randomness, no AI interpretation, no hallucination risk.

When Claude needs to fetch data from an API, it doesn't write the HTTP request inline and hope it gets the headers right. It calls an execution script that's been written and tested for that exact API. The script handles authentication, pagination, error codes, and caching — reliably, every time.

The AI decides **what** to run. The scripts decide **how** it runs.

## Why This Separation Matters

> **In Plain English:** Think of it like a restaurant. The directive is the recipe card. The orchestrator (Claude) is the head chef reading the card and calling out orders. The execution scripts are the cooking equipment — the oven, the mixer, the timer. The chef decides what to cook and when. The equipment does the actual cooking, reliably, every time. You wouldn't want the chef to "imagine" what temperature the oven is at — you read the dial.

The separation matters because AI is good at reasoning but unreliable at mechanical tasks. When Claude writes a complex SQL query from scratch every time, it might get it slightly wrong in a way that's hard to spot. When it calls a tested script that always builds the query the same way, the result is predictable.

It also makes debugging straightforward. If the output is wrong:

- **Wrong decision?** That's an orchestration problem — update the directive or give Claude better context.
- **Wrong result?** That's an execution problem — fix the script, and the fix applies everywhere it's used.
- **Wrong instructions?** That's a directive problem — update the SOP, and every future session follows the new rules.

Each layer can be fixed independently without touching the others.

## Deterministic vs Probabilistic

The DOE framework is built around one core insight: AI and code are good at fundamentally different things, and mixing them up causes problems.

### Probabilistic (AI / Claude)

Claude is an AI. It reasons, makes judgments, and generates creative solutions. It can read a vague request and figure out what you actually mean. It can look at a bug and diagnose the root cause. It can write code, plan features, and explain trade-offs.

But it can also hallucinate — confidently stating something that isn't true. It can forget context mid-conversation, or claim a script works when it doesn't. This is the "probabilistic" part: powerful but unpredictable. Every response is a best guess, even when that guess is usually right.

### Deterministic (Scripts / Code)

Execution scripts run the same way every time. `2 + 2` always equals `4`. An API call either succeeds or fails. A file either exists or it doesn't. There's no creativity, no judgment, and no hallucination risk — just reliable, repeatable operations. If a script worked yesterday with the same inputs, it will work today.

### DOE's Key Insight

Let the AI handle what it's good at — reasoning, planning, writing code, making decisions — and let deterministic code handle what *it's* good at — running commands, making API calls, checking files, verifying results. The framework enforces this separation so you get the best of both without the worst of either.

**What this means for you:** You get an AI that can reason about complex problems AND a system that verifies its work with cold, hard checks. Without DOE, you're trusting the AI's word that things work. With DOE, you have proof.

> **In Plain English:** Think of it like a pilot and an autopilot. The pilot (Claude) makes the big decisions — where to fly, how to handle weather, when to change course. The autopilot (execution scripts) handles the precise, repeatable operations — maintain this altitude, follow this heading, adjust for wind. You wouldn't want the pilot manually trimming the flaps, and you wouldn't want the autopilot deciding to reroute the flight. Each does what it's best at.

**Probabilistic (Claude):** Reasoning, Planning, Code generation, Decisions, Error diagnosis

**Deterministic (Scripts):** API calls, File operations, Data transforms, Verification, Builds

DOE connects them — the AI decides *what* to do, the scripts handle *how* it's done.

## How It Works in Practice

Here's a concrete walkthrough. Say you ask Claude: "Import the latest election results data."

**Step 1 — Claude reads the directive.**
It checks `directives/` and finds the data import directive. This tells it: cache the download, validate the format, log what was imported, update the data governance register.

**Step 2 — Claude checks for existing scripts.**
It looks in `execution/` and finds `import_election_results.py` — a script that's been written and tested before. It knows the API endpoint, handles pagination, and outputs a clean CSV.

**Step 3 — Claude runs the script.**
It calls `python3 execution/import_election_results.py` and watches the output. The script downloads the data, caches it locally, validates the format, and reports back: "Downloaded 650 constituency results, all fields validated."

**Step 4 — Claude verifies the result.**
Following the directive, it checks that the output file exists, has the expected number of records, and the data looks reasonable (no empty columns, no obvious duplicates).

**Step 5 — Claude commits the result.**
It saves the work with a clear commit message: "Import March 2026 election results — 650 constituencies." If anything goes wrong later, this single commit can be reverted cleanly.

**What if no script exists?** Say you ask Claude to import data from a source it hasn't seen before. Claude doesn't improvise — it creates a new script in `execution/`, following the patterns it can see in the existing scripts. Same structure, same error handling, same logging. The new script becomes part of the toolkit for next time.

This is DOE working as designed: the directive set the rules, Claude made the decisions, and the script did the work.
