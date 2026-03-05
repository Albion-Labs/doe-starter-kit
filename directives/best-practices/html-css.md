# Best Practices: HTML/CSS

## Goal
Prevent common agent failure modes in HTML and CSS before they reach commit.

## When to Use
Read before writing or modifying any HTML or CSS file.

## Process

### Security
- Never use `innerHTML` with untrusted or dynamic data — use `textContent` or DOM APIs (XSS risk)
- Never include inline event handlers (`onclick="..."`) with dynamic values

### Accessibility
- Always add `alt` attributes to `<img>` tags — use descriptive text or `alt=""` for decorative images
- Always associate `<label>` elements with form inputs — use `for` attribute or wrap the input
- Use semantic HTML elements (`<nav>`, `<main>`, `<article>`, `<section>`, `<header>`, `<footer>`) — not `<div>` for everything
- Always include `lang` attribute on `<html>` element

### Correctness
- Never reuse `id` values on a page — IDs must be unique (JS selectors and anchors break)
- Always include `<meta name="viewport" content="width=device-width, initial-scale=1">` for responsive pages
- Always include `<meta charset="utf-8">` as the first element in `<head>`
- Never use inline styles — use CSS classes (maintenance, caching, consistency)

### CSS Maintainability
- Never use `!important` unless overriding third-party CSS — fix specificity instead
- Use CSS custom properties (`--color-primary`) for repeated values — never hardcode colors/sizes in multiple places
- Never use fixed pixel widths for layout containers — use relative units, flexbox, or grid
- Prefer classes over element selectors for styling — element selectors are fragile to markup changes

## Verification
- [ ] All images have `alt` attributes
- [ ] All form inputs have associated labels
- [ ] No duplicate `id` values
- [ ] No inline styles (CSS classes used instead)
- [ ] Viewport meta tag present
- [ ] No `!important` without justification
