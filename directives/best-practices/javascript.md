# Best Practices: JavaScript

## Goal
Prevent common agent failure modes in JavaScript before they reach commit.

## When to Use
Read before writing or modifying any JavaScript file.

## Process

### Security
- For untrusted data, use `textContent` or DOM creation APIs (`document.createElement`); reserve `innerHTML` for known-safe HTML you generated yourself (XSS risk)
- Build HTML via DOM creation APIs or template literals with explicit escaping -- string concatenation hides escape boundaries and invites XSS
- For dynamic execution, use pre-registered, statically-analysable code paths (`eval()` and `new Function()` are off-limits, including via `setTimeout`/`setInterval` with string arguments)

### Correctness
- Always use `===` and `!==` — never `==` or `!=` (type coercion bugs)
- Always handle null/undefined returns from `.find()`, `.find()` on arrays, `Map.get()` — check before using
- Always wrap `await` calls in try/catch — unhandled rejections crash Node and silently fail in browsers
- Always add `.catch()` to standalone promises not awaited
- Treat function parameters as read-only; return new values to convey changes
- Always clean up event listeners, timers, and subscriptions when done (memory leaks)
- Use `const` by default, `let` when reassignment is needed; `var` is reserved for legacy code you cannot edit

### Maintainability
- Extract magic numbers and strings to named constants or config -- a name documents intent that the literal value can't
- Remove all `console.log` debugging statements before committing
- Mark a function `async` only when it awaits something -- otherwise the wrapped Promise is overhead with no caller benefit
- Always handle all Promise states — don't ignore rejections or assume success

## Verification
- [ ] No `console.log` left in production code
- [ ] No `==` comparisons (use `===`)
- [ ] All async calls have error handling
- [ ] No `innerHTML` with dynamic content
- [ ] No event listeners without cleanup paths
