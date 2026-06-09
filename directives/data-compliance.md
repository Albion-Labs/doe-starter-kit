# Directive: Data Compliance

## Goal
Ensure every feature that handles personal data meets UK/EU GDPR and DPA 2018 requirements before any data is collected, stored, or processed.

For political-campaign data, additional obligations apply (criminal liability, campaign-finance retention) — see the political layer's dedicated directive (`directives/political-data.md`), installed only when that layer is enabled.

Tradeoff: Compliance work costs upfront design time in exchange for legal cover and stakeholder trust when personal data flows. Apply on any feature touching names, emails, addresses, or special-category data (health, biometrics, etc.). Skip when: the feature operates only on aggregated, anonymised, or synthetic data with no identifiable individual.

## When to Use
- Building any feature that collects, stores, or processes personal data (names, emails, addresses, account details)
- Adding user accounts, authentication, or membership features
- Handling special-category data (health, biometrics, etc.)
- Building payment or billing features
- Collecting survey or feedback data
- Any feature that merges data from multiple sources about individuals

## Inputs
- `legal-framework.md` -- current legal position and review triggers
- `data-governance.md` -- dataset register, licensing, provenance
- Feature contract from `tasks/todo.md` -- what the feature does

## Process

### Before building (hard blockers)

1. **DPIA check.** Complete and approve a DPIA (Article 35) before any personal data enters the system. The DPIA documents: what data is collected, why, the legal basis, risks, and mitigations. This is the gate -- no DPIA, no data.

2. **Legal basis check.** For each category of personal data the feature handles, confirm the legal basis:
   - Standard personal data (name, email, address): Legitimate interest (Article 6(1)(f)) with documented balancing test, or explicit consent (Article 6(1)(a))
   - Special-category data (health, biometrics, etc. under Article 9): Requires EITHER explicit consent (Article 9(2)(a)) OR another Article 9(2) condition with a matching DPA 2018 Schedule 1 basis — document which basis is used, and maintain an "appropriate policy document" where Schedule 1 requires one
   - Financial data (payments, billing): Legitimate interest, contract performance (Article 6(1)(b)), or legal obligation (Article 6(1)(c)) where record-keeping is legally required

3. **Consent mechanism.** If using consent as a legal basis, the feature MUST include: (a) clear, specific consent language, (b) granular opt-in (not bundled with T&Cs), (c) record of when/how consent was given, (d) easy withdrawal mechanism.

### During building (architecture requirements)

4. **SAR-ready schema.** Every table that stores personal data must have a column or foreign key that links records to a user/person ID, so a Subject Access Request can query all data held about one person across all tables. Test: "Can I run one query to find everything we hold about person X?" If not, fix the schema.

5. **Erasure cascade.** Deletion of a person must cascade across all linked tables (notes, tags, activity logs, transactions). Use database foreign keys with ON DELETE CASCADE, or document the deletion sequence. Soft-delete first (set deleted_at), hard-delete after retention period. Test: "If I delete person X, is ANY trace of them left anywhere?" If yes, fix it.

6. **Retention policy.** Every personal data table must have a documented retention period. Soft-deleted records must be hard-deleted after the retention period via a scheduled function. No personal data should persist indefinitely without review.

7. **Audit trail.** Log all access to and modifications of personal data (who, what, when). The audit log references personal data by ID only -- the log row holds operation metadata, the data lives in its own table.

8. **Data minimisation.** Collect only what is needed for the stated purpose. When a feature can work without a field, omit it. When a field is needed only temporarily, delete it after use.

### After building (verification)

9. **DSAR response test.** Run a test Subject Access Request against the feature: query all tables for a test user, compile the export, verify it contains everything the system holds. This must complete in under 30 days (legal requirement) -- aim for seconds.

10. **Erasure test.** Delete a test user and verify: no records remain in any table, the audit log shows the deletion, and the user cannot be reconstructed from remaining data.

11. **Update legal-framework.md.** Update the relevant section to reflect the new legal position. If the feature changes the GDPR position, bump the version and update the "Applies to" field.

12. **Update privacy notice.** Update the privacy notice in the same PR that introduces the data processing it describes. The privacy notice must match the actual processing -- a notice that describes processing the system does not do, or omits processing it does, is a transparency failure. The cure is co-located edits, not parallel docs.

## Outputs
- Updated `legal-framework.md` with new legal position
- DPIA document (if first personal data feature)
- SAR export function (tested)
- Erasure cascade (tested)
- Updated privacy notice (if applicable)

## Edge Cases
- **Special-category data** (Article 9: health, biometrics, political opinion, etc.) requires explicit consent OR another Article 9(2) condition with a matching DPA 2018 Schedule 1 basis. If relying on a Schedule 1 condition, document why it applies and maintain an "appropriate policy document" where one is required (DPA 2018 Schedule 1 Part 4). Merging special-category data with other sources requires its own legal basis and must be documented in the DPIA.
- **Children's data** -- if any feature could involve under-18s, additional safeguards apply under Article 8 (parental consent for information society services offered to children).
- **Cross-border transfers** -- if data is processed outside the UK/EU (e.g. by a third-party API), ensure adequacy or appropriate safeguards. Choosing a database region inside the UK/EU (e.g. a Supabase EU/London region) avoids this for database storage.

## Verification
- [ ] DPIA completed before any personal data collected
- [ ] Legal basis documented for each data category
- [ ] SAR export function works (returns all data for a person)
- [ ] Erasure cascade works (no orphaned records)
- [ ] Retention periods documented for all personal data tables
- [ ] Audit trail captures all data access and modifications
- [ ] Privacy notice accurately describes data processing
- [ ] legal-framework.md updated with new position

## Placeholder Pattern for Shared Secrets

When sharing example secrets in code, docs, tickets, or commit messages, use placeholder tokens (`<API_KEY>`, `<DB_URL>`, `<SUPABASE_SERVICE_ROLE>`). The placeholder makes the shape of the value clear without leaking a live credential. The `block_secrets_in_code.py` PreToolUse hook scans for secret-shaped values; placeholders pass the scan because they do not match any real-credential pattern.
