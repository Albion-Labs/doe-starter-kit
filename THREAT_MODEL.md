# Threat Model

This document defines the project's threat landscape, data classification, and trust boundaries. It is a living document -- update it when the architecture changes or new data categories are introduced.

---

## Data Classification

Every piece of data in the system belongs to one of four classification levels. The level determines storage, access, encryption, and retention requirements.

| Level | Description | Examples | Storage Requirements |
|-------|-------------|----------|---------------------|
| **PUBLIC** | Freely available data. No harm if disclosed. | Published marketing pages, public documentation, open datasets, press releases | No special requirements. Can be cached, logged, displayed without restriction. |
| **INTERNAL** | Operational data not intended for public release. Disclosure causes embarrassment or minor competitive harm. | Internal strategy documents, roadmaps, employee schedules, draft communications | Access restricted to project team. Not committed to a public repo. Not included in error logs or analytics. |
| **CONFIDENTIAL** | Personal data subject to data-protection law (e.g. UK/EU GDPR). Disclosure causes harm to individuals. | User names, email addresses, phone numbers, postal addresses, payment details, account records | Encrypted at rest and in transit. Access logged. Retention periods enforced. Subject to access and erasure procedures. See `directives/data-compliance.md` (regulated layer). |
| **RESTRICTED** | Special-category data (Article 9 UK/EU GDPR) or data whose misuse carries criminal or sector-specific liability. Highest sensitivity. | Health, biometric, genetic, ethnicity, religious/political-belief or trade-union data; plus any sector-regulated dataset (see the regulated-layer threat addendum) | All CONFIDENTIAL requirements plus: explicit legal basis required (Article 9(2)), access limited to named individuals, stored separately from other personal data, breach may trigger criminal as well as civil liability. |

### Classification Decision Tree

1. Is it special-category data (political opinion, health, ethnicity, trade union, religion, sexual orientation, biometrics, genetics)? -> **RESTRICTED**
2. Is it a sector-regulated dataset whose misuse carries statutory or criminal penalties (e.g. financial or health records, or a regulated register)? -> **RESTRICTED** (see the regulated-layer threat addendum if installed)
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

### T7: Special-Category / Regulated-Data Misuse

**Risk:** Special-category or sector-regulated data used beyond its lawful purpose, merged with other datasets, or disclosed to unauthorised persons.
**Likelihood:** Low if controls are followed.
**Impact:** Potential criminal as well as civil liability, depending on the dataset and sector.
**Mitigations:**
- Regulated datasets stored separately with dedicated access controls
- Never in seed data, test data, or non-production environments
- Access logged and auditable
- For sector-specific obligations and criminal-liability detail, install the regulated layer — see the regulated-layer threat addendum

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
- `directives/data-safety.md` -- Technical enforcement of data protection (data-handling layer)
- `directives/data-compliance.md` -- Legal compliance, GDPR / DPA 2018 (regulated layer)
- `directives/incident-response.md` -- Incident response procedure
- `THREAT_MODEL-regulated.md` -- Sector-specific data classes, threats, and criminal-liability detail (regulated layer)
