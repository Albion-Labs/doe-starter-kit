# Directive: Security Rules

## Goal
Enforce defence in depth across all code — input handling, output rendering, data transport, and deployment configuration. Security is not a feature; it is a property of every line of code.

## When to Use
Loaded when writing code that handles user input, renders dynamic content, communicates with APIs or databases, or configures deployment infrastructure. If in doubt, load it.

## Principles

1. **Defence in depth.** No single layer is trusted. Every boundary validates, sanitises, and constrains independently.
2. **client-side access control is zero security.** Hiding a button or checking a role in the browser provides no protection. All access control must be enforced server-side. Client-side checks are UX only.
3. **Fail closed.** If a security check errors, deny access. Never default to permissive.

## Input Handling

- **no eval.** Never use `eval()`, `Function()`, `setTimeout(string)`, or any dynamic code execution. There are no exceptions.
- **Validate and constrain.** Validate type, length, range, and format at the boundary. Reject anything outside the expected shape.
- **Use parameterised queries.** Never concatenate user input into SQL, NoSQL, or ORM queries. Use parameterised / prepared statements exclusively.

## Output & Rendering

- **Sanitise all dynamic content.** Use `escapeHTML` or the framework's built-in escaping for every value inserted into the DOM. Never insert untrusted content via `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, or `[innerHTML]` without sanitisation.
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

- **Never log secrets.** API keys, tokens, passwords, and session identifiers must never appear in logs, error messages, or client-side output.
- **Classify data in logging.** Mark sensitive fields as `CONFIDENTIAL` or `RESTRICTED` in log schemas. Never log fields at a classification level higher than the log sink's clearance.
- **Environment variables for secrets.** Store credentials in `.env` or a secrets manager. Never commit secrets to version control.

## Authentication & Sessions

- **Use established libraries.** Do not implement authentication, hashing, or token generation from scratch.
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
