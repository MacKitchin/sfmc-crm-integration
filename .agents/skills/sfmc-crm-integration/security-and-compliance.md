# Security & Compliance

Companion to `SKILL.md` (which states the operating rules) and `../../docs/`. This consolidates
the **security, secrets, identity, and data-privacy** considerations in one place. Where this
overlaps `SKILL.md`, `SKILL.md` is authoritative for procedure.

## Secrets & credentials

- The SFMC integration authenticates with an **OAuth2 client_credentials** app (client
  ID/secret) against `https://{tenant}.auth.marketingcloudapis.com/v2/token`.
- **Never commit or paste secrets.** `.gitignore` blocks `.env`, `client_secret*`, and
  `*.secret`. Load the client secret from an env var, use it inline in a single auth call, and
  **never echo it** or write it into docs/commits/logs.
- Do not put real tokens, client secrets, or session IDs into `docs/` or `walkthroughs/` — use
  placeholders.

## Service identity

- Leads are created by the **MC Connect system user** `mc-connect-crm@bizbash.com`
  (`0054X00000Dk173QAB`); it is the Lead `CreatedById`. Treat this as a privileged integration
  identity:
  - Don't repurpose it for interactive use.
  - Changes to its permissions or status can silently break Lead creation.

## Production safety (security-adjacent)

- `CRM_Integration` runs **hourly against production** and creates real CRM Leads. Per
  `SKILL.md`: confirm before any SFMC/Salesforce **write or trigger**; reads are safe.
- **Back up Asset `67116`** before editing the Content Block (dated backup asset). The current
  backup is Asset `179321`.
- Test changes only through `Manual_Entries` + `CRM_IntegrationManual` with a single record —
  never by poking the live hourly path.
- `CRMProcessed` is append-only (dedup + audit). Don't delete/rewrite rows.

## Org limits & safe writes (Salesforce)

- Direct Apex **class** deploy to prod is blocked (`Can not create Apex Class on an active
  organization`) — use **Anonymous Apex**.
- Batch ID lists ~400 per `IN`; add `WHERE IsConverted = false` to Lead updates; add date/`LIMIT`
  filters to avoid the 50,001-row query error.

## Data privacy (PII & marketing consent)

- This pipeline handles **personal data**: name, email, job title, company, phone, postal
  address. The repo also contains spreadsheet exports of lead/attribution data
  (`*.xlsx`) — treat these as sensitive PII.
  - `TODO`: Confirm whether the committed `*.xlsx` / report bundles contain real PII that should
    be removed from version control or never committed.
- **Opt-in / marketability is consent data.** `Source_OptInTo` drives which opt-in fields are
  set per source. Mis-mapping opt-in can cause people to be marketed to without the right
  consent basis — treat opt-in mapping changes as compliance-sensitive (GDPR / CAN-SPAM /
  CASL), not just data plumbing.
- **Attribution is required, not optional:** every Lead must carry `Lead_Details__c = @Source`,
  `LeadSource = 'MC BizBash'`, `Lead_Source__c = 'MC BizBash'`. Beyond being the project's
  purpose, accurate source attribution supports lawful-basis/consent traceability.

## Verify-before-trust

- The "Critical Facts" in `SKILL.md` (org ID, MC Connect user, tenant, asset IDs, DE keys) can
  drift. **Confirm against live SFMC/Salesforce before acting on a write.**

## TODO / to verify

- `TODO`: Confirm committed `.xlsx`/report bundles don't contain real PII (or move them out of
  the repo / gitignore).
- `TODO`: Confirm the opt-in mappings in `Source_OptInTo` reflect current consent requirements
  per region.
- `TODO`: Confirm who can rotate the SFMC client secret and the MC Connect user's credentials.
