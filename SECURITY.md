# Security Policy

## Responsible Disclosure

If you discover a security vulnerability in this project, please report it responsibly. Do **not** open a public issue.

**How to report:**
1. Email the project maintainer directly (see `legal-framework.md` for contact details, or use the GitHub "Security" tab if configured).
2. Include: what you found, how to reproduce it, and what data (if any) could be affected.
3. We will acknowledge receipt within 48 hours and provide an initial assessment within 5 working days.

We will not pursue legal action against good-faith security researchers who follow this disclosure process.

---

## Secret Management

### Prevention

- All secrets live in `.env` files (local) or deployment platform environment variables. Nowhere else.
- `.env*.local` is in `.gitignore`. Verify after every `.gitignore` change.
- `.env.example` contains key names with empty values only.
- Pre-commit hooks scan for common secret patterns (JWTs, API keys, connection strings). See `directives/data-safety.md` ## 4 for the full pattern list.
- Enable GitHub secret scanning on the repository. This catches secrets that slip past local hooks.

### Rotation

If a secret is exposed in a commit, log, error message, or any public surface, rotate immediately:

1. **Revoke the compromised secret** and generate a new one. Do not wait to assess impact -- rotate first, investigate second.
2. Update the new secret in all environments (production, preview, local).
3. Verify the application works with the new secret.
4. Revoke the old secret if not already done.
5. Check git history -- the old secret exists in every clone. Force-pushing does not fix this. Treat the secret as permanently compromised.

**Scheduled rotation:** High-sensitivity keys (database passwords, service_role keys) should be rotated every 90 days. Document the rotation date in your environment management notes.

**Reactive rotation triggers:**
- Any suspected compromise
- Team member offboarding or departure
- Secret detected in logs, error output, or version control
- Third-party provider reports a breach

---

## Dependency Security

### npm Audit

Run `npm audit` as part of CI and before every release.

- **Critical and high vulnerabilities:** Fix before merging. No exceptions.
- **Moderate vulnerabilities:** Fix within one sprint/iteration. Document if deferring.
- **Low vulnerabilities or false positives:** Add to an allowlist with justification. The allowlist lives in `.nsprc` or equivalent audit config. Every allowlist entry must have a comment explaining why it is acceptable and a review date.

### Keeping Dependencies Current

- Run `npm outdated` monthly.
- Pin major versions in `package.json`. Use `^` for minor/patch only.
- Review changelogs before major version bumps -- especially for security-sensitive packages (auth libraries, crypto, database drivers).

---

## Repository Security

### Branch Protection

For any repository containing personal data processing code:
- Require pull request reviews before merging to `main`.
- Require status checks to pass (CI, audit, lint).
- Do not allow force pushes to `main`.
- Do not allow deletion of `main`.

### Access Control

- Use the principle of least privilege for repository access.
- For a public repo: no secrets in code, no real data in seed files, no internal infrastructure details in documentation.
- Review collaborator access quarterly. Remove anyone who no longer needs it.

### GitHub Features

- Enable **Dependabot** for automated dependency update PRs.
- Enable **secret scanning** to detect accidentally committed credentials.
- Enable **code scanning** (CodeQL or equivalent) if the repository contains server-side code handling personal data.

---

## Data Breach Response

If personal data is compromised, the **72 hours** ICO notification window starts from the moment of discovery, not the moment of occurrence.

See `directives/incident-response.md` for the full incident response procedure, including:
- Triage and containment steps
- ICO notification requirements (Article 33)
- Individual notification requirements (Article 34)
- Post-incident review

See `directives/data-safety.md` ## 7 for the detailed breach notification chain with hour-by-hour actions.

---

## AI Agent Security

AI coding agents (Claude Code, GitHub Copilot, Cursor) introduce specific security risks. These are documented in `directives/data-safety.md` ## 3, but the key rules are:

- AI agents connect to databases using **read-only credentials only**.
- AI agents **never** have access to production credentials.
- The `service_role` key is never used in client-side code, regardless of who wrote it.
- Pre-commit hooks enforce these rules deterministically. The AI cannot override them.

---

## Verification

- [ ] GitHub secret scanning enabled
- [ ] Pre-commit hooks scan for secret patterns
- [ ] `.env*.local` is in `.gitignore`
- [ ] No secrets in version control history (run `git log -p | grep -i secret` periodically)
- [ ] npm audit runs in CI with no unaddressed critical/high findings
- [ ] allowlist entries have justification and review dates
- [ ] Branch protection rules configured on `main`
- [ ] Team member access reviewed quarterly
- [ ] Secret rotation schedule documented
- [ ] Breach notification procedure documented and rehearsed

## Cross-References

- `directives/data-safety.md` -- Technical data protection (environment isolation, destructive operation prevention, secret management details)
- `directives/data-compliance.md` -- Legal compliance (GDPR, DPA 2018, PPERA)
- `directives/incident-response.md` -- Incident response procedure
- `THREAT_MODEL.md` -- Threat model and data classification
- `legal-framework.md` -- Legal obligations
