# Directive: Incident Response

## Goal
Provide a structured procedure for handling security incidents, data breaches, team member departures, and bulk data subject requests so that nothing is missed under pressure.

## When to Use
- A data breach or suspected data breach is discovered
- A security vulnerability is reported or detected
- A team member leaves or is removed from the project (offboarding)
- A bulk Subject Access Request (DSAR) or bulk erasure request is received
- Any event that could require ICO notification or legal escalation

## Inputs
- `SECURITY.md` -- disclosure policy and secret rotation procedures
- `THREAT_MODEL.md` -- data classification and threat catalogue
- `directives/data-safety.md` -- technical controls and breach notification chain
- `directives/data-compliance.md` -- legal requirements for personal data
- `legal-framework.md` -- current legal position and data controller identity
- `data-governance.md` -- dataset register and retention periods

## Process

### 1. Data Breach Response

When personal data may have been compromised, accessed without authorisation, lost, or exposed:

**Immediate (Hour 0):**
1. Confirm the breach is real. Check logs, access records, error reports.
2. If the breach is ongoing, stop it. Revoke credentials, restrict access, take the affected service offline if necessary.
3. Do NOT destroy evidence. Preserve logs and database state.

**Triage (Hour 0-1):**
4. Classify the data involved using `THREAT_MODEL.md` data classification.
5. Estimate the number of individuals affected.
6. Determine if electoral register data is involved (criminal matter -- take legal advice immediately).
7. Determine if RESTRICTED (special category) data is involved.

**Containment (Hour 1-4):**
8. Rotate all potentially compromised credentials. See `SECURITY.md` for rotation procedure.
9. Patch the vulnerability that caused the breach, if known.
10. Isolate affected systems from production if contamination is possible.

**Assessment (Hour 4-24):**
11. Determine exact scope: which records, which individuals, what time window.
12. Assess risk to individuals. Political opinion data breaches carry reputational and safety risks beyond typical PII.
13. Decide if individuals need direct notification (required if "high risk to rights and freedoms" -- Article 34).

**ICO Notification (Hour 24-72):**
14. If personal data was affected, file ICO notification at https://ico.org.uk/make-a-complaint/
15. Include: nature of breach, categories and approximate numbers of individuals/records, contact details of data controller, likely consequences, measures taken.
16. If information is incomplete, file what you have. Missing the 72-hour window is worse than filing incomplete details.

**Post-Incident:**
17. Notify affected individuals if required (high risk breaches).
18. Record the breach in a breach register (Article 33(5) requires records of ALL breaches, even unreported ones).
19. Conduct root cause analysis.
20. Update security controls, directives, and threat model based on findings.
21. If the breach revealed a gap in this directive, update it.

### 2. Team Member Offboarding

When a team member leaves or is removed, complete this checklist within 24 hours:

- [ ] Remove from GitHub repository (collaborator access)
- [ ] Remove from deployment platform (Vercel, Supabase dashboard, etc.)
- [ ] Remove from any shared credential stores or password managers
- [ ] Rotate all secrets the person had access to (database passwords, API keys, service_role keys, auth provider secrets). This is mandatory, not optional -- you cannot verify what was copied.
- [ ] Remove from communication channels (Slack, Discord, email groups)
- [ ] Remove from any third-party service dashboards (Sentry, PostHog, email provider)
- [ ] Review recent commits and deployments by the departing member for anomalies
- [ ] Update access documentation
- [ ] If the person was the data controller or had sole access to ICO registration, transfer these responsibilities before or during departure

### 3. Bulk DSAR Response

A bulk Subject Access Request occurs when multiple individuals (or an organisation on behalf of individuals) submit DSARs simultaneously. This happened to Reform UK (96% failure rate) and is the most operationally dangerous compliance event.

**On receipt:**
1. Log each DSAR individually with receipt date. The 30-day clock starts per-request from the date of receipt.
2. Verify identity for each requestor (proportionate to the data held).
3. Run the SAR export procedure (see `directives/data-compliance.md`) for each individual.
4. Review each export for: completeness (all tables checked), third-party data that requires the third party's consent to disclose, and any data that is legally exempt from disclosure.
5. Send each response within 30 days. If an extension is needed (complex or numerous requests -- Article 12(3)), notify the requestor within 30 days explaining why, and complete within 90 days total.

**For bulk requests specifically:**
- Prioritise by receipt date (FIFO).
- Track progress in a spreadsheet or task list -- each request must have: requestor name, receipt date, deadline, status, response date.
- Do NOT send a blanket "no records found" response without actually checking. This is what Reform UK did and it is now evidence against them.
- If the system genuinely holds no data about a requestor, confirm this after checking ALL data stores (database, backups, logs, email, paper files, third-party processors).

### 4. Bulk Erasure Response

Similar to bulk DSAR but for Right to Erasure (Article 17) requests:

1. Log each request with receipt date.
2. For each individual, identify all data held and the legal basis for retention.
3. Delete everything that does not have a competing legal basis for retention (e.g. PPERA record-keeping for donation records).
4. For data retained under legal obligation, inform the requestor which data is retained and why.
5. Run the erasure verification test (see `directives/data-compliance.md`).
6. Confirm deletion to each requestor.

### 5. Secret Compromise

When a secret (API key, database password, auth token) is found in version control, logs, or any public surface:

1. Rotate the compromised secret immediately. Generate new, update all environments, verify app works, revoke old. See `SECURITY.md`.
2. Determine the exposure window: when was the secret committed/exposed, when was it discovered?
3. Check access logs for the affected service during the exposure window. Look for unauthorised access.
4. If the compromised secret provided access to personal data, treat as a potential data breach and follow section 1 above.
5. Add the secret pattern to pre-commit hook scanning if not already covered.
6. Log the incident in `learnings.md`.

## Outputs
- Breach register entry (for any data breach, reported or not)
- ICO notification filing (if personal data breach)
- Individual notification letters (if high risk breach)
- Updated offboarding checklist confirmation
- DSAR response letters with data exports
- Erasure confirmation letters
- Updated security controls and directives

## Edge Cases
- **Electoral register breach** is both a GDPR matter (ICO) and a criminal matter (police). Take legal advice before responding. Do not self-incriminate.
- **AI-caused breach** (e.g. AI agent sent personal data to a third-party API) -- the data controller is still liable. Document the AI tool as a sub-processor and restrict its data access.
- **Breach discovered outside business hours** -- the 72-hour clock does not pause for weekends. Have ICO notification details accessible at all times.
- **Former team member refuses to confirm credential deletion** -- assume all credentials they had access to are compromised. Rotate everything.
- **DSAR from a hostile party** (e.g. political opponent fishing for internal data) -- you must still comply. DSARs cannot be refused based on the requestor's motives, but you can refuse if the request is "manifestly unfounded or excessive" (Article 12(5)). Document the reasoning carefully.

## Verification
- [ ] Breach response procedure documented and accessible to all team members
- [ ] ICO notification URL bookmarked and accessible
- [ ] Offboarding checklist completed within 24 hours of any departure
- [ ] All secrets rotated after team member departure
- [ ] DSAR response procedure tested with synthetic data
- [ ] Bulk DSAR tracking mechanism in place
- [ ] Breach register exists (even if empty)
- [ ] This directive reviewed after every incident
