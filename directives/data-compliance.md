# Directive: Data Compliance

## Goal
Ensure every feature that handles personal data meets UK GDPR, DPA 2018, and PPERA requirements before any data is collected, stored, or processed.

Tradeoff: Compliance work costs upfront design time in exchange for legal cover and stakeholder trust when personal data flows. Apply on any feature touching names, emails, addresses, political opinions, or canvass responses. Skip when: the feature operates only on aggregated, anonymised, or synthetic data with no identifiable individual.

## When to Use
- Building any feature that collects, stores, or processes personal data (names, emails, addresses, political opinions, canvass responses)
- Adding user accounts, authentication, or membership features
- Integrating with electoral register data
- Building fundraising, donation, or payment features
- Adding canvassing, survey, or voter contact features
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
   - Political opinions (special category under Article 9): Requires EITHER explicit consent (Article 9(2)(a)) OR substantial public interest under DPA 2018 Schedule 1 Part 2 paragraph 22 (political activities) — document which basis is used
   - Electoral register data: Lawful under Representation of the People Act 1983 for electoral/political purposes — but merging with other sources requires its own legal basis
   - Financial data (donations): Legitimate interest for PPERA compliance (legal obligation)

3. **Consent mechanism.** If using consent as a legal basis, the feature MUST include: (a) clear, specific consent language, (b) granular opt-in (not bundled with T&Cs), (c) record of when/how consent was given, (d) easy withdrawal mechanism.

### During building (architecture requirements)

4. **SAR-ready schema.** Every table that stores personal data must have a column or foreign key that links records to a user/person ID, so a Subject Access Request can query all data held about one person across all tables. Test: "Can I run one query to find everything we hold about person X?" If not, fix the schema.

5. **Erasure cascade.** Deletion of a person must cascade across all linked tables (notes, tags, canvass records, activity logs, donations). Use database foreign keys with ON DELETE CASCADE, or document the deletion sequence. Soft-delete first (set deleted_at), hard-delete after retention period. Test: "If I delete person X, is ANY trace of them left anywhere?" If yes, fix it.

6. **Retention policy.** Every personal data table must have a documented retention period. Soft-deleted records must be hard-deleted after the retention period via a scheduled function. No personal data should persist indefinitely without review.

7. **Audit trail.** Log all access to and modifications of personal data (who, what, when). The audit log references personal data by ID only -- the log row holds operation metadata, the data lives in its own table.

8. **Data minimisation.** Collect only what is needed for the stated purpose. When a feature can work without a field, omit it. When a field is needed only temporarily, delete it after use.

### After building (verification)

9. **DSAR response test.** Run a test Subject Access Request against the feature: query all tables for a test user, compile the export, verify it contains everything the system holds. This must complete in under 30 days (legal requirement) -- aim for seconds.

10. **Erasure test.** Delete a test user and verify: no records remain in any table, the audit log shows the deletion, and the user cannot be reconstructed from remaining data.

11. **Update legal-framework.md.** Update the relevant section to reflect the new legal position. If the feature changes the GDPR or PPERA position, bump the version and update the "Applies to" field.

12. **Update privacy notice.** Update the privacy notice in the same PR that introduces the data processing it describes. Reform UK's problem was a privacy notice that described data merging while the company denied doing it -- the cure is co-located edits, not parallel docs.

## Outputs
- Updated `legal-framework.md` with new legal position
- DPIA document (if first personal data feature)
- SAR export function (tested)
- Erasure cascade (tested)
- Updated privacy notice (if applicable)

## Edge Cases
- **Electoral register data** is lawful to use for political purposes but merging it with commercial data sources, social media profiles, or third-party databases requires a separate legal basis and must be documented in the DPIA. Reform UK is being sued for exactly this.
- **Political opinion data** (Article 9 special category) requires explicit consent OR substantial public interest basis. If using the public interest exemption, document why it applies. The exemption is not a blank cheque -- it requires an "appropriate policy document" under DPA 2018 Schedule 1 Part 4.
- **Canvass data** records voter opinions, which is special category data. Each canvass response needs a legal basis. Best practice: inform the voter at the door that their response will be recorded and offer the right to refuse.
- **Children's data** -- if any feature could involve under-18s (unlikely in political campaigns but possible), additional safeguards apply under Article 8.
- **Cross-border transfers** -- if data is processed outside the UK (e.g. by a third-party API), ensure adequacy or appropriate safeguards. Supabase London region avoids this for database storage.

## Verification
- [ ] DPIA completed before any personal data collected
- [ ] Legal basis documented for each data category
- [ ] SAR export function works (returns all data for a person)
- [ ] Erasure cascade works (no orphaned records)
- [ ] Retention periods documented for all personal data tables
- [ ] Audit trail captures all data access and modifications
- [ ] Privacy notice accurately describes data processing
- [ ] legal-framework.md updated with new position

## Reference: Reform UK v Good Law Project (2026)
Reform UK is being sued by 51 voters (High Court, Article 80(1) UK GDPR) for: (a) failing to respond to 96% of DSARs within the legal 30-day deadline, (b) sending false "no record" replies, (c) processing political opinion data without clear legal basis, (d) merging electoral register with third-party data without transparency. This is the first Article 80(1) case in the UK. Every feature that touches personal data ships with automated SAR handling, a transparent privacy notice, and documented legal bases for each data category.

## Placeholder Pattern for Shared Secrets

When sharing example secrets in code, docs, tickets, or commit messages, use placeholder tokens (`<API_KEY>`, `<DB_URL>`, `<SUPABASE_SERVICE_ROLE>`). The placeholder makes the shape of the value clear without leaking a live credential. The `block_secrets_in_code.py` PreToolUse hook scans for secret-shaped values; placeholders pass the scan because they do not match any real-credential pattern.
