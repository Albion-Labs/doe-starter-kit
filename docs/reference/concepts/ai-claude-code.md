# AI and Claude Code Concepts

This page explains the core ideas you'll encounter when working with Claude Code. None of these require a technical background — they're just concepts that help you understand what's happening and why the system works the way it does.

---

## Context Window

The context window is Claude's working memory for a conversation. Everything you've typed, everything Claude has replied, and every file it has read during a session all live in the context window.

The catch: the context window has a size limit. Once it fills up, Claude starts "forgetting" the oldest parts of the conversation — the way you might forget the start of a long meeting by the time it ends. This can cause Claude to make decisions that contradict things you agreed on earlier.

**Why this matters in practice:** This is why `/wrap` and `/clear` exist. `/wrap` saves the important parts of your session to disk (STATE.md, learnings.md) before the context window gets noisy. `/clear` resets the conversation — wiping the window clean — without touching any of your files. If Claude starts making odd or contradictory decisions mid-session, a `/clear` often fixes it.

Keeping sessions focused (one task at a time) also helps. A session that bounces between five unrelated topics fills the context window faster and gives Claude less useful signal to work from.

---

## Models

Claude comes in three models. They are not tiers of quality — they are different tools optimised for different jobs.

### Opus — Deep Reasoning

Opus is the most capable model. It has the best judgment for complex, open-ended problems: architectural decisions, cross-file reasoning, evaluating trade-offs, reviewing a plan before you build it. It is also the slowest and most expensive.

Use Opus when the task requires genuine judgment — not just following instructions, but figuring out which instructions to follow.

### Sonnet — Balanced, Most Work

Sonnet is the default for most tasks. It is fast enough to feel responsive, capable enough to handle implementation work, and cheap enough to use freely. If you are building a feature from a clear spec, fixing a bug with a known cause, or doing anything that involves following explicit instructions, Sonnet is the right choice.

### Haiku — Fast Lookups

Haiku is the fastest and cheapest model. It is well suited to narrow, mechanical tasks: finding a file, searching for a pattern, doing a quick calculation, or running a lookup. It is not well suited to tasks that require judgment or extensive reasoning.

> **In Plain English:** Opus is the senior consultant you bring in for the hard decisions. Sonnet is the competent generalist who does most of the work. Haiku is the quick errand runner for lookups and simple tasks.

---

## Thinking Levels

Thinking level controls how carefully Claude reasons through a problem before responding. There are three levels: low, medium, and high.

- **Low:** Claude answers quickly, drawing on the most immediate response. Good for straightforward tasks where the answer is clear.
- **Medium:** Claude pauses to consider the problem more carefully before responding. The default for most implementation work.
- **High:** Claude thinks through the problem at length — examining edge cases, weighing alternatives, checking its own reasoning. Best for complex decisions and architectural choices.

Higher thinking takes longer and costs more tokens. It is not always better — for a simple task, high thinking is overkill and just adds delay.

> **In Plain English:** Low is "just do it." Medium is "take a moment before you start." High is "sit down and think this through carefully before touching anything."

Thinking level and model choice work together. Opus at high thinking is appropriate for hard problems that need real judgment. Sonnet at low thinking is fine for a quick file edit.

---

## Tokens

Tokens are the unit Claude uses to process text. Roughly every four characters — a letter, a space, a punctuation mark — makes up one token. "Hello world" is about three tokens. A typical paragraph is around 50–80 tokens.

**Why it matters:** Cost and speed are both measured in tokens. The more tokens in a request (your message plus all the context Claude has access to), the more it costs to run and the longer it takes to respond. Reading a large file, or working with a very long conversation, increases the token count.

This is one of the reasons the system is designed to pass Claude only the files it needs for a specific task, rather than loading the entire codebase every time. Smaller context = faster responses = lower cost.

You do not need to count tokens manually. The model and thinking level selections already account for cost. But if Claude ever seems slow on a task, "large context window" is often the reason.

---

## Subagents

Claude can spawn helper instances of itself — called subagents — to work on tasks in parallel. Each subagent is a separate Claude session with its own context window. They work independently and report back when done.

Think of it like delegating tasks to assistants. Instead of one Claude doing five things sequentially, it can hand four of them to subagents and coordinate the results. This is faster for multi-step work and also preserves the main conversation's context window — the subagents do the heavy lifting without filling up the primary session.

**In this project:** Subagents are used during `/agent-launch` waves, where multiple independent tasks are distributed across separate Claude sessions and run at the same time. A coordinator Claude monitors progress; worker Claudes do the actual building. The full approach is documented in `.claude/plans/multi-agent-coordination.md`.

Each subagent gets only the files and context it needs for its specific task — this is both a context-saving measure and a safety guardrail. Subagents on a wave cannot edit shared project files (STATE.md, todo.md) mid-task; those changes are merged by the coordinator at the end.
