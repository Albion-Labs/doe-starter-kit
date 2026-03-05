# Best Practices: JavaScript

## Goal
Prevent common agent failure modes in JavaScript before they reach commit.

## When to Use
Read before writing or modifying any JavaScript file.

## Process

### Security
- Never use `innerHTML` with untrusted data — use `textContent` or DOM APIs (XSS risk)
- Never build HTML with string concatenation — use template literals with proper escaping or DOM creation
- Never use `eval()` or `new Function()` with dynamic input

### Correctness
- Always use `===` and `!==` — never `==` or `!=` (type coercion bugs)
- Always handle null/undefined returns from `.find()`, `.find()` on arrays, `Map.get()` — check before using
- Always wrap `await` calls in try/catch — unhandled rejections crash Node and silently fail in browsers
- Always add `.catch()` to standalone promises not awaited
- Never mutate function parameters — return new values instead
- Always clean up event listeners, timers, and subscriptions when done (memory leaks)
- Always use `const` by default, `let` when reassignment is needed — never `var`

### Maintainability
- Never hardcode magic numbers or strings — extract to named constants or config
- Remove all `console.log` debugging statements before committing
- Never use `async` on a function that doesn't `await` anything
- Always handle all Promise states — don't ignore rejections or assume success

## Verification
- [ ] No `console.log` left in production code
- [ ] No `==` comparisons (use `===`)
- [ ] All async calls have error handling
- [ ] No `innerHTML` with dynamic content
- [ ] No event listeners without cleanup paths
