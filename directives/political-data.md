# Directive: Political & Electoral Data

Installed with the **political** capability layer. Load this ONLY for projects that handle UK electoral or political-campaign data — it adds criminal-liability and campaign-finance rules on top of the generic guidance in `data-safety.md` and `data-compliance.md`. A normal project that merely stores personal data does **not** need this.

## Goal
Keep political-campaign features (electoral register, canvass responses, voter contact, political donations) on the right side of criminal law and campaign-finance regulation, not just GDPR.

Tradeoff: this content carries hard legal stakes (imprisonment for electoral-register misuse, statutory donation retention). Apply it whenever a feature touches electoral-register data, canvass/voter opinions, or political donations. Skip when: the project handles ordinary personal data with no electoral or campaign-finance dimension — `data-compliance.md` covers that.

## When to Use
- Integrating or storing full electoral register data
- Recording canvass responses, voting intention, or other voter opinions
- Building fundraising or political-donation features subject to campaign-finance law
- Merging voter/electoral data with any other dataset
- Any feature where a political party or campaign is the data controller

## Inputs
- `data-compliance.md` -- the generic GDPR/DPA process this extends
- `data-safety.md` -- generic technical data-protection controls
- `THREAT_MODEL-political.md` -- electoral threat model and data classification
- `legal-framework.md` -- current legal position and review triggers

## Process

### Electoral Register Data — Criminal Liability

**Misuse of the full electoral register is a criminal offence carrying imprisonment.** Under the Representation of the People (England and Wales) Regulations 2001 (reg. 115), it is an offence to:
- Use full register data for any purpose other than those specified in law
- Disclose full register data to an unauthorised person
- Fail to comply with security requirements for register data

Political parties may use the full register for electoral purposes, but merging it with commercial data, sharing it with third parties, or using it for non-electoral purposes is criminal. If the system integrates electoral register data:
- It must be stored separately from other data, with its own access controls
- Access must be logged and auditable
- It must never be included in seed data, test data, backups shared outside the secure environment, or any non-production system
- A leak of electoral register data is both a GDPR breach (ICO notification) AND a criminal matter (police)

This is not a fine. This is a court appearance.

### Legal basis for political data

- **Political opinions** (canvass responses, voting intention — Article 9 special category): requires EITHER explicit consent (Article 9(2)(a)) OR substantial public interest under DPA 2018 Schedule 1 Part 2 paragraph 22 (political activities) — document which basis is used.
- **Electoral register data:** lawful under the Representation of the People Act 1983 for electoral/political purposes — but merging with other sources requires its own legal basis, documented in the DPIA.
- **Political donations:** legitimate interest for campaign-finance compliance (a legal obligation).
- **Canvass data** records voter opinions (special category). Each response needs a legal basis — best practice: inform the voter at the door that their response will be recorded and offer the right to refuse.

### GDPR Right to Erasure vs Campaign-Finance Retention

GDPR Article 17 gives individuals the right to erasure, but campaign-finance law (PPERA) requires parties to retain donation records (s.71) and expenditure records (s.81) for specific periods. These conflict.

**Resolution:** GDPR Article 17(3)(b) exempts erasure where processing is necessary "for compliance with a legal obligation." PPERA record-keeping IS a legal obligation. Therefore:
- **Donation records:** retain for the period required by PPERA (currently 6 years). The individual cannot demand deletion during this period. Document the basis: "Retention required under PPERA s.71 for Electoral Commission reporting."
- **Expenditure records:** same — PPERA requires retention for Electoral Commission reporting periods.
- **All other personal data:** the right to erasure applies normally — delete everything except what PPERA legally requires you to keep.
- **After the PPERA retention period expires:** the legal basis disappears. Delete the records.

## Outputs
- Electoral-register data stored in an isolated store with dedicated access controls
- Documented legal basis per political data category in the DPIA
- Campaign-finance retention periods documented and enforced

## Edge Cases
- **Cautionary case — Reform UK v Good Law Project (2026):** a party sued by 51 voters (High Court, Article 80(1) UK GDPR) for (a) missing 96% of DSAR deadlines, (b) false "no record" replies, (c) processing political-opinion data without a clear legal basis, (d) merging electoral register with third-party data without transparency. The lesson: automated SAR handling, a transparent privacy notice that matches actual processing, and a documented legal basis for every category.
- **Merging electoral data** with commercial/social/third-party sources needs a separate legal basis AND DPIA entry — this is the specific failure above.

## Verification
- [ ] Electoral register data (if any) isolated with its own access controls and audit log
- [ ] Legal basis documented for each political data category
- [ ] Campaign-finance (PPERA) retention periods documented and enforced
- [ ] Erasure requests honour the statutory-retention exemption correctly
- [ ] No electoral or canvass data in seed/test/non-production environments
