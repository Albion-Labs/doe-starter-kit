# Introduction to DOE

## What is DOE?

DOE (Directive, Orchestration, Execution) is a framework that organises how you work with Claude Code so your projects stay structured, trackable, and recoverable. It gives Claude Code a set of rules, memory, and tools that turn freeform AI conversations into a disciplined build process — one where every decision is recorded, every change can be undone, and no context is lost between sessions.

## Why does DOE exist?

Without structure, AI-assisted coding sessions produce chaos. You ask Claude to build something, it creates files in random places, you close the session, and next time you come back Claude has no memory of what it did or why. Files pile up. Mistakes compound. You can't undo a bad change because you don't know when it happened. If something breaks, you're stuck reading through hundreds of lines trying to figure out what went wrong.

DOE solves this by giving every session a beginning (stand-up), a middle (structured building with save points), and an end (wrap-up). It keeps a memory of what was built, what was learned, and what's next. It enforces rules — like "commit after every task" and "verify before delivering" — that prevent the most common disasters. And it puts guardrails around Claude so it can't accidentally overwrite your work or make changes you didn't ask for.

## Who is DOE for?

DOE is for anyone building software with Claude Code. That includes:

- **First-time builders** who have never written code before but want to create something real. DOE provides the structure you don't yet know you need — it catches mistakes before they become problems.
- **People learning to code** who want to build projects while picking up programming concepts along the way. DOE's organised approach means you can always understand what Claude did and why.
- **Experienced developers** who want to move faster with AI assistance without sacrificing the engineering discipline they already value. DOE formalises the practices that make AI coding sessions productive instead of chaotic.

## What you'll learn from these docs

These reference docs cover everything you need to go from zero to shipping features with DOE:

- **Getting started** — installing the tools, running your first session, understanding the configuration files that make DOE work
- **How sessions work** — the rhythm of stand-up, build, and wrap-up that keeps every session productive and recoverable
- **What the commands do** — every slash command explained, with examples of when and why to use each one
- **Core concepts** — the ideas behind DOE (separation of concerns, deterministic execution, session memory) explained without jargon
- **Workflows** — how to go from a product idea to a shipped feature, step by step

By the end, you'll understand not just how to use DOE, but why it works the way it does — so you can adapt it to your own projects.

## How to use these docs

There are two tracks through the DOE documentation, designed for different needs:

### Visual tutorials (HTML pages)

The `docs/` folder contains interactive HTML pages that walk you through DOE concepts visually. These are the best way to **learn** DOE for the first time. They use diagrams, animations, and step-by-step walkthroughs to build understanding. Start here if you're new.

### Reference docs (these markdown files)

The `docs/reference/` folder (where you are now) contains structured reference documentation. These are the best way to **look things up** when you're already working. Need to remember what a command does? Check the commands section. Forgot how to configure something? Check getting-started. Hit an error? Check the troubleshooting examples.

**If you're brand new**, start with the visual tutorials to build understanding, then come back to these reference docs when you need specifics.

**If you're already building**, keep these reference docs open as a quick-lookup resource. They're organised so you can find what you need without reading everything.
