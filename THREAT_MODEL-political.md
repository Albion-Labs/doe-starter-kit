# Threat Model — Political & Electoral Addendum

Installed with the **political** capability layer. Extends `THREAT_MODEL.md` with electoral/political-campaign data classes and threats that carry statutory or criminal liability. Load alongside `directives/political-data.md`.

Only install this layer for projects that handle UK electoral or political-campaign data. A normal personal-data project does not need it — `data-compliance.md` covers generic GDPR.

---

## Additional RESTRICTED data classes

| Data | Why RESTRICTED | Authority |
|------|----------------|-----------|
| Full electoral register data | Criminal liability for non-electoral use or unauthorised disclosure | Representation of the People Act; Representation of the People (England and Wales) Regulations 2001, reg. 115 |
| Canvass responses, voting intention | Special-category political opinion (Article 9 UK GDPR) | UK GDPR Art. 9 |
| Political donation records | Statutory retention and reporting | PPERA s.71 (6-year retention, Electoral Commission reporting) |

Classify any of the above as **RESTRICTED** in `THREAT_MODEL.md` terms: explicit legal basis, named-individual access, separate storage, criminal as well as civil exposure on breach.

---

## T7 (political): Electoral Register Misuse

**Risk:** Full electoral register data used for non-electoral purposes, merged with commercial data, or disclosed to unauthorised persons.
**Likelihood:** Low if controls are followed.
**Impact:** Criminal liability (Representation of the People Act), not just civil/GDPR.
**Mitigations:**
- Register data stored separately with dedicated access controls
- Never in seed data, test data, or non-production environments
- Access logged and auditable
- See `directives/data-compliance.md` and `legal-framework.md` for the full legal position

---

## GDPR erasure vs PPERA retention conflict

Donation records subject to PPERA's 6-year retention cannot be erased on request during that window. Document the lawful basis for refusing erasure (legal obligation / public task) rather than silently ignoring the request. See `directives/data-compliance.md`.

---

## Incident response: political-data specifics

These extend the generic flow in `directives/incident-response.md`:

- **Electoral register involvement** makes a breach a criminal matter as well as a GDPR matter — take legal advice immediately, before any external statement; the lawyer drafts the wording (ICO + police).
- **Bulk Subject Access Requests** are the most operationally dangerous compliance event. Verify the database for each data subject before responding — a "no records" reply requires evidence. Blanket "no record" replies sent without checking have been used as evidence against the controller.
- **Retention conflicts:** when deleting after a breach, keep records that have a competing legal basis for retention (e.g. PPERA donation record-keeping); delete the rest.

---

## Cross-references
- `THREAT_MODEL.md` -- the universal threat model this extends
- `directives/political-data.md` -- electoral criminal-liability + campaign-finance retention
- `directives/data-compliance.md` -- generic GDPR / DPA 2018 compliance
- `directives/data-safety.md` -- technical enforcement of data protection
- `legal-framework.md` -- legal obligations and review triggers
- `directives/incident-response.md` -- the generic incident-response procedure
