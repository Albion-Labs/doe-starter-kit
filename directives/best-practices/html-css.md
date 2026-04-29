# Best Practices: HTML/CSS

## Goal
Prevent common agent failure modes in HTML and CSS before they reach commit.

## When to Use
Read before writing or modifying any HTML or CSS file.

## Process

### Security
- For untrusted or dynamic data, use `textContent` or DOM creation APIs (`document.createElement`); reserve `innerHTML` for known-safe HTML you generated yourself (XSS risk)
- Wire event handlers via `addEventListener` in JS rather than inline `onclick="..."` attributes -- inline handlers with dynamic values are a code-injection vector

### Accessibility
- Always add `alt` attributes to `<img>` tags — use descriptive text or `alt=""` for decorative images
- Always associate `<label>` elements with form inputs — use `for` attribute or wrap the input
- Use semantic HTML elements (`<nav>`, `<main>`, `<article>`, `<section>`, `<header>`, `<footer>`) — not `<div>` for everything
- Always include `lang` attribute on `<html>` element

### Correctness
- Each `id` is unique per page; reach for classes when you need a repeated marker (JS selectors and anchor links rely on uniqueness)
- Always include `<meta name="viewport" content="width=device-width, initial-scale=1">` for responsive pages
- Always include `<meta charset="utf-8">` as the first element in `<head>`
- Style via CSS classes -- the cascade lives in stylesheets where it can be maintained, cached, and kept consistent

### CSS Maintainability
- Resolve specificity issues by tightening selectors or restructuring the cascade; reserve `!important` for overriding third-party CSS
- Use CSS custom properties (`--color-primary`) for repeated values -- a single source of truth for colours and sizes
- Layout containers use relative units (`%`, `rem`, `vw`), flexbox, or grid -- fixed pixel widths break responsive layouts
- Prefer classes over element selectors for styling — element selectors are fragile to markup changes

## Verification
- [ ] All images have `alt` attributes
- [ ] All form inputs have associated labels
- [ ] No duplicate `id` values
- [ ] No inline styles (CSS classes used instead)
- [ ] Viewport meta tag present
- [ ] No `!important` without justification
