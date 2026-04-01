# Threat Model

This document defines the project's threat landscape, data classification, and trust boundaries. It is a living document -- update it when the architecture changes or new data categories are introduced.

---

## Data Classification

Every piece of data in the system belongs to one of four classification levels. The level determines storage, access, encryption, and retention requirements.

| Level | Description | Examples | Storage Requirements |
|-------|-------------|----------|---------------------|
| **PUBLIC** | Freely available data. No harm if disclosed. | Published election results, public candidate statements, constituency boundaries, publicly available policy documents | No special requirements. Can be cached, logged, displayed without restriction. |
| **INTERNAL** | Operational data not intended for public release. Disclosure causes embarrassment or minor competitive harm. | Campaign strategy documents, internal polling, canvass route plans, volunteer schedules, draft communications | Access restricted to project team. Not committed to a public repo. Not included in error logs or analytics. |
| **CONFIDENTIAL** | Personal data subject to UK GDPR. Disclosure causes harm to individuals. | Voter names, email addresses, phone numbers, postal addresses, donation amounts, membership records | Encrypted at rest and in transit. Access logged. Retention periods enforced. Subject to SAR and erasure procedures. See `directives/data-compliance.md`. |
| **RESTRICTED** | Special category data (Article 9 UK GDPR) or data with criminal liability for misuse. Highest sensitivity. | Political opinions (canvass responses, voting intention), trade union membership, health data, ethnicity data, full electoral register data | All CONFIDENTIAL requirements plus: explicit legal basis required (Article 9(2)), access limited to named individuals, stored separately from other personal data, breach triggers criminal as well as civil liability for electoral register data. |

### Classification Decision Tree

1. Is it special category data (political opinion, health, ethnicity, trade union, religion, sexual orientation, biometrics, genetics)? -> **RESTRICTED**
2. Is it from the full electoral register? -> **RESTRICTED** (criminal liability under Representation of the People Act)
3. Can it identify a living individual (directly or by combination)? -> **CONFIDENTIAL**
4. Is it internal operational data not intended for public release? -> **INTERNAL**
5. Otherwise -> **PUBLIC**

---

## Trust Boundaries

```
+--------------------------------------------------+
|  BROWSER / CLIENT                                 |
|  - Public data only                               |
|  - anon key (respects RLS)                        |
|  - No secrets, no service_role key                |
+------------------------+-------------------------+
                         | HTTPS
+------------------------v-------------------------+
|  SERVER / API ROUTES                              |
|  - Validates all input                            |
|  - Authenticates requests via JWT                 |
|  - Authorises via RLS policies                    |
|  - Logs access (IDs only, not data values)        |
+------------------------+-------------------------+
                         | Authenticated connection
+------------------------v-------------------------+
|  DATABASE (Supabase/Neon)                         |
|  - RLS enforced on all tables                     |
|  - service_role used only by execution scripts    |
|  - Encrypted at rest                              |
|  - Backup and recovery tested                     |
+--------------------------------------------------+

+--------------------------------------------------+
|  AI AGENTS (Claude Code, CI)                      |
|  - Read-only database credentials                 |
|  - No production access                           |
|  - No access to RESTRICTED data                   |
|  - Pre-commit hooks enforce guardrails            |
+--------------------------------------------------+

+--------------------------------------------------+
|  THIRD-PARTY PROCESSORS (Sentry, email, etc.)     |
|  - DPA required before sending personal data      |
|  - Minimise data sent                             |
|  - UK/EEA data residency preferred                |
+--------------------------------------------------+
```

---

## Threat Catalogue

### T1: Credential Exposure

**Risk:** Secrets committed to version control or exposed in logs/error messages.
**Likelihood:** High (AI agents consistently attempt this).
**Impact:** Full database access, data breach.
**Mitigations:**
- Pre-commit hooks scan for secret patterns
- GitHub secret scanning enabled
- `.env*.local` in `.gitignore`
- Rotate immediately on detection (see `SECURITY.md`)

### T2: Destructive Database Operations

**Risk:** Unguarded DELETE, DROP, TRUNCATE, or mass ORM operations destroy data.
**Likelihood:** Medium (AI agents generate unfiltered queries).
**Impact:** Irrecoverable data loss, breach notification obligations.
**Mitigations:**
- Bash hook blocks dangerous SQL patterns
- Soft-delete policy for all regulated data
- AI agents use read-only database credentials
- Migration safety protocol (backup before every schema change)

### T3: Environment Cross-Contamination

**Risk:** Production credentials used in development, or real data loaded into non-production.
**Likelihood:** Medium (especially under demo pressure).
**Impact:** Uncontrolled personal data processing, breach if dev environment is compromised.
**Mitigations:**
- Strict environment isolation (see `directives/data-safety.md` ## 1)
- Synthetic seed data only in non-production
- The "First Personal Data Gate" checklist blocks premature use of real data

### T4: Supply Chain (Dependencies)

**Risk:** Compromised or vulnerable npm packages.
**Likelihood:** Medium.
**Impact:** Ranges from data exfiltration to arbitrary code execution.
**Mitigations:**
- `npm audit` in CI
- Dependabot enabled
- Pin major versions
- Review changelogs before major bumps

### T5: AI Data Leakage

**Risk:** Personal data sent to AI providers in prompts during development-time processing.
**Likelihood:** Medium (developers paste data into AI tools for debugging).
**Impact:** Personal data processed by third party without legal basis or DPA.
**Mitigations:**
- Never send raw personal data in AI prompts
- Use IDs and synthetic examples instead
- Check AI provider data retention policies
- Document AI tools as sub-processors if they receive personal data

### T6: Insider / Team Member Departure

**Risk:** Departing team member retains access to systems, credentials, or data.
**Likelihood:** Low in small teams, increases with scale.
**Impact:** Unauthorised access, data breach.
**Mitigations:**
- Offboarding checklist in `directives/incident-response.md`
- Rotate secrets after any departure
- Review access quarterly
- Principle of least privilege from the start

### T7: Electoral Register Misuse

**Risk:** Full electoral register data used for non-electoral purposes, merged with commercial data, or disclosed to unauthorised persons.
**Likelihood:** Low if controls are followed.
**Impact:** Criminal liability (Representation of the People Act), not just civil/GDPR.
**Mitigations:**
- Register data stored separately with dedicated access controls
- Never in seed data, test data, or non-production environments
- Access logged and auditable
- See `directives/data-safety.md` for criminal liability details

---

## Repository Visibility

This project is intended to run as a **public repo** (or private repo with the assumption that code could become public). This means:

- **No secrets in code.** Ever. Not even "temporary" ones.
- **No real personal data in seed files, test fixtures, or documentation.** Use synthetic data.
- **No internal infrastructure details** that would help an attacker (server IPs, internal URLs, admin endpoints not protected by auth).
- **Security through architecture, not obscurity.** The system must be secure even if the attacker reads every line of code.

If the repository is private, maintain these standards anyway. Private repos become public (open-sourced, forked, leaked) more often than expected.

---

## Review Schedule

Review this threat model when:
- A new data category is introduced
- A new third-party service is integrated
- The architecture changes (new database, new deployment target, new auth provider)
- A security incident occurs
- At minimum, every 6 months

## Cross-References

- `SECURITY.md` -- Disclosure policy, secret rotation, dependency security
- `directives/data-safety.md` -- Technical enforcement of data protection
- `directives/data-compliance.md` -- Legal compliance (GDPR, DPA 2018, PPERA)
- `directives/incident-response.md` -- Incident response procedure
- `legal-framework.md` -- Legal obligations and review triggers
