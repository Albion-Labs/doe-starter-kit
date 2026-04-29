# Directive: Security Rules

## Goal
Enforce defence in depth across all code — input handling, output rendering, data transport, and deployment configuration. Security is not a feature; it is a property of every line of code.

Tradeoff: Defence-in-depth costs review time on every input, output, and dependency change in exchange for resilience to single-layer compromises. Apply when writing code that handles user input, renders dynamic content, talks to APIs or databases, or configures deployment infrastructure. Skip when: the change is provably scope-limited (a rename inside a pure function, a comment-only edit) and the diff confirms no boundary surface changed.

## When to Use
Loaded when writing code that handles user input, renders dynamic content, communicates with APIs or databases, or configures deployment infrastructure. If in doubt, load it.

## Principles

1. **Defence in depth.** No single layer is trusted. Every boundary validates, sanitises, and constrains independently.
2. **client-side access control is zero security.** Hiding a button or checking a role in the browser provides no protection. All access control must be enforced server-side. Client-side checks are UX only.
3. **Fail closed.** Security checks deny access on error -- the default response is denial, not permission.

## Input Handling

- **No dynamic execution.** Dynamic code execution lives in pre-registered, statically-analysable code paths. JavaScript: avoid the three string-execution APIs (`eval()`, `Function()` constructor, string form of `setTimeout`/`setInterval`) -- pass functions instead.
- **Validate and constrain.** Validate type, length, range, and format at the boundary. Reject anything outside the expected shape.
- **Use parameterised queries.** All SQL, NoSQL, and ORM queries take user input via parameter bindings -- the query string is a static template, the values pass separately.

## Output & Rendering

- **Sanitise all dynamic content.** DOM insertion of untrusted values goes through `textContent` or framework escaping (Vue/React/Angular built-ins). `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, and `[innerHTML]` are reserved for known-safe HTML you generated yourself.
- **Subresource integrity.** Every externally-loaded script or stylesheet must include an `integrity` attribute (SRI hash). Pin the version. If the CDN is compromised, the browser will refuse the tampered resource.

## Transport & Headers

- **HTTPS only.** All endpoints, all environments. No mixed content.
- **Security headers.** Every response must include at minimum:
  - `Content-Security-Policy` — restrict script sources, disable inline scripts where possible.
  - `X-Content-Type-Options: nosniff` — prevent MIME-type sniffing.
  - `Strict-Transport-Security` — enforce HTTPS with a long max-age.
  - `X-Frame-Options: DENY` — prevent clickjacking.
  - `Referrer-Policy: strict-origin-when-cross-origin` — limit referrer leakage.

## Secrets & Data Classification

- **Redact secrets at the log boundary.** A logging redactor strips secret-shaped tokens (API keys, tokens, passwords, session identifiers) before any sink receives the log line.
- **Classify data in logging.** Mark sensitive fields as `CONFIDENTIAL` or `RESTRICTED` in log schemas. Routing matches sink clearance to field classification -- a CONFIDENTIAL field only flows to a CONFIDENTIAL-cleared sink.
- **Environment variables for secrets.** Credentials live in `.env` or a secrets manager. The pre-commit secret-detection hook gates accidental commits to other files.

## Authentication & Sessions

- **Use established libraries.** Authentication, password hashing, and token generation come from established libraries -- Argon2 / libsodium / the framework's auth module -- never a from-scratch implementation.
- **Short-lived tokens.** Prefer short expiry with refresh over long-lived tokens. Rotate secrets on schedule.
- **Secure cookie flags.** `HttpOnly`, `Secure`, `SameSite=Strict` (or `Lax` with justification).

## Dependency Management

- **Pin versions.** Use lockfiles. Review changelogs before upgrading.
- **Audit regularly.** Run `npm audit`, `pip audit`, or equivalent. Fix critical and high vulnerabilities before release.

## Production Deployment Security Checklist

Use this security checklist before every production deployment:

- [ ] All user input is validated server-side (type, length, format)
- [ ] No dynamic code execution anywhere in the codebase
- [ ] All database queries use parameterised statements
- [ ] All dynamic DOM content uses `escapeHTML` or framework escaping
- [ ] External scripts/stylesheets have `integrity` (SRI) attributes
- [ ] `Content-Security-Policy` header is configured and tested
- [ ] `X-Content-Type-Options: nosniff` header is present
- [ ] `Strict-Transport-Security` header is present
- [ ] No secrets in source code, logs, or client-side bundles
- [ ] Data classified as `CONFIDENTIAL` or `RESTRICTED` is not logged to uncleared sinks
- [ ] Dependencies audited — zero critical or high vulnerabilities
- [ ] Authentication uses established libraries, not custom implementations
- [ ] Session cookies have `HttpOnly`, `Secure`, and `SameSite` flags
- [ ] Client-side access control is backed by server-side enforcement
- [ ] HTTPS enforced on all endpoints
