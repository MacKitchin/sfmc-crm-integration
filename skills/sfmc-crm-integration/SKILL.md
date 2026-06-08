---
name: sfmc-crm-integration
description: In-repo Standard Operating Procedure for AI agents working inside /Users/mackitchin/Repos/sfmc-crm-integration — the SFMC (Salesforce Marketing Cloud) to Salesforce CRM lead-creation pipeline that turns BizBash form submissions into Salesforce Leads via the MC Connect bridge. Use whenever working in this repo or on the leads integration — the FormEntries_ToCRM / CRM_Integration automations, the CRM_Integration_ProcessRecs_BizBash AMPscript Content Block (Asset 67116), the Form_Entries / Manual_Entries / CRMProcessed / Source_OptInTo / Source_Campaign Data Extensions, MC Connect (mc-connect-crm@bizbash.com), lead source attribution (Lead_Details__c / LeadSource), adding/fixing a Source mapping, opt-in assignment, dedup, backfills, or troubleshooting missing/duplicate leads.
---

# SFMC → Salesforce CRM Integration — In-Repo Agent SOP

You are working inside `/Users/mackitchin/Repos/sfmc-crm-integration`, the documentation and
operating home for the **BizBash Lead Creation Pipeline**. This repo holds **no deployable
application code** — the integration runs inside SFMC (SQL Query Activities + an AMPscript
Content Block) and in Salesforce. Your job here is to diagnose, document, and carefully
change that live system using the references and walkthroughs below.

## How This Folder Is Organized

- `SKILL.md` (this file) — the operating manual: facts, rules, and where to go.
- `walkthroughs/` — step-by-step guides for the recurring tasks:
  - `add-new-source.md` — onboard a new form/content source end to end.
  - `modify-content-block.md` — safely change the AMPscript that creates Leads.
  - `backfill-lead-attribution.md` — repair `Lead_Details__c` on historical leads.
  - `diagnose-leads.md` — symptom-driven debugging for missing/duplicate/no-opt-in leads.
  - `trigger-and-monitor-automation.md` — run and watch the automations safely.
- `../../docs/` — the detailed system reference (architecture, automations, content block,
  data extensions, source mapping, salesforce fields, troubleshooting, changelog).

The `docs/` files are the authoritative system reference; the walkthroughs are the
procedural layer that tells you *how to act* using those docs. Read the one walkthrough that
matches the task, then dip into the specific `docs/` file it points to.

## Critical Facts (verify live before any write)

| Component | Value |
|---|---|
| Salesforce Org ID | `00D30000001H2naEAC` |
| MC Connect user (Lead `CreatedById`) | `mc-connect-crm@bizbash.com` / `0054X00000Dk173QAB` |
| SFMC subdomain (tenant) | `mc4y763vp8r2sk5c18sv5j2sphry` |
| SFMC Business Unit (BizBash) | `534000167` (Enterprise `526003676`) |
| Live Content Block | Asset `67116`, Key `CRM_Integration_ProcessRecs_BizBash` |
| Backup Content Block | Asset `179321`, Key `CRM_ProcessRecs_BKP_20260402` |
| Stage 1 automation | `FormEntries_ToCRM` — daily 5:00 AM ET |
| Stage 2 automation | `CRM_Integration` — hourly |
| Manual automation | `CRM_IntegrationManual` — manual trigger (uses `Manual_Entries`) |
| Dedup / audit DE | `CRMProcessed` (~220k+ rows, append-only) |
| Opt-in mapping DE | `Source_OptInTo` (key `A6DA18FC-0754-464B-8DF5-31D2ACD0B811`, ~251 rows) |
| Campaign mapping DE | `Source_Campaign` (key `3951ACCF-6B86-4FBA-9710-E4C28C0BE7A0`) |

Values are from the repo docs and can drift. Confirm against live SFMC/Salesforce before
acting on them.

## Pipeline at a Glance

```
~35 source form DEs
   │  [FormEntries_ToCRM] daily 5am ET — UNION ALL SQL; each block hardcodes its Source
   ▼
Form_Entries DE (11 cols)  +  Manual_Entries DE (ad-hoc)
   │  [CRM_Integration] hourly
   │   1. SQL anti-join vs CRMProcessed (find unprocessed)
   │   2. Verification (email format / required fields)
   │   3. AMPscript Content Block 67116
   ▼
Salesforce Lead  ── MC Connect ──  CreateSalesforceObject / UpdateSingleSalesforceObject
   ▼
CRMProcessed DE  (audit + dedup key: EmailAddress, Source, Action, CRMID)
```

The 11 standardized columns carried through the pipeline:
`EmailAddress, FirstName, LastName, JobTitle, Company, Phone, Address, City, State, Country, Source`.

## First Moves

1. `git status --short` — protect unrelated user changes before editing anything.
2. Classify the task: **read/diagnose** (safe) vs **write/modify** (live: Content Block
   edits, automation triggers, Lead create/update, DE writes, backfills).
3. Open the matching `walkthroughs/*.md`; it lists the exact steps, commands, and the
   `docs/` file with the underlying detail.
4. Confirm live auth before assuming state — a valid SFMC OAuth token and a working
   Salesforce session/MCP connection. Never infer current behavior from docs alone for a
   write task.
5. Keep changes scoped to the one source/automation/asset in the request.

## Project Rules

- **Production is live.** `CRM_Integration` runs hourly and creates real CRM Leads. Do not
  trigger automations, edit the Content Block, or write to DEs/Leads unless asked, or unless
  required for the current fix and made explicit and confirmed first.
- **Confirm before any SFMC/Salesforce write or trigger.** State precisely what will change
  (asset, automation, DE, or record set) and get the user's go-ahead. Reads don't need it.
- **Back up the Content Block before editing.** Always snapshot Asset `67116` to a dated
  backup asset first. See `walkthroughs/modify-content-block.md`.
- **Test through `Manual_Entries` + `CRM_IntegrationManual`.** Validate Content Block or
  mapping changes with a single test record and verify the resulting Lead in Salesforce —
  never test by poking the live hourly path.
- **Never commit secrets — the `.gitignore` is the guardrail.** The only true secrets here
  are the SFMC **client secret** and any OAuth **bearer/refresh token**; never commit, paste,
  log, or write them into docs or commit messages. Keep secret material only in files the
  `.gitignore` already catches (`.env`, `client_secret*`, `*.secret`, `*.token`, `*.pem`,
  `*.key`, …), load it from an env var, and use it inline in a single auth call. See
  **Security & Secrets** below for the full workflow.
- **`CRMProcessed` is the dedup key + audit trail and is append-only.** Don't delete or
  rewrite rows; the hourly anti-join depends on it.
- **Respect Salesforce org limits.** Direct Apex class deploy to prod is blocked
  (`Can not create Apex Class on an active organization`) — use Anonymous Apex, batch ~400
  IDs per `IN`, add `WHERE IsConverted = false` to Lead updates, and add date/`LIMIT`
  filters to dodge the 50,001-row query error.
- **Source attribution is the whole point.** Every new Lead must carry
  `Lead_Details__c = @Source`, `LeadSource = 'MC BizBash'`, and `Lead_Source__c = 'MC BizBash'`.
  Dropping `Lead_Details__c` is a regression.
- **Adding a source is a coordinated change.** It requires editing the `FormEntries_ToCRM`
  SQL **and** the mapping DEs together — never one without the other.

## Security & Secrets

The `.gitignore` at the repo root is the safety net that keeps credentials out of version
control. Treat it as load-bearing, not boilerplate — these docs intentionally contain
internal identifiers, so the discipline below is what prevents a real leak. The
`tests/check_security_guidelines.py` validator enforces these standards mechanically (run it
or wire it as a pre-commit hook — see `../../tests/README.md`).

- **Know what is secret vs. not.** Secrets = the SFMC **client secret** and any OAuth
  **bearer/refresh token**. These must never be committed, echoed, logged, or written into
  docs or commit messages. Everything else referenced here — Org ID, client ID, SFMC
  subdomain, BU IDs, asset IDs, DE keys, the MC Connect user email — are non-credential
  config identifiers that cannot authenticate without the secret, so they may stay in the
  docs. Keep this repo **private** as a second layer of protection.
- **Store secrets only in ignored paths.** Put any credential file where the `.gitignore`
  already matches it — `.env`, `client_secret*`, `*.secret`, `*.token`, `*.pem`, `*.key`,
  `credentials*`. Pull the value from the environment (`CLIENT_SECRET=$(...)`) and reference
  `$CLIENT_SECRET` inline; never paste the literal value into a command, file, or message.
- **Extend the guardrail before adding a new secret type.** If a task introduces a new kind
  of credential file, add a matching pattern to `.gitignore` *first*, then create the file.
  Never bypass the ignore with `git add -f`, and never loosen or delete existing patterns.
- **Verify before every commit.** Run `git status` and `git --no-pager diff --cached` (or
  `python3 tests/check_security_guidelines.py --staged`) and confirm no secret value or
  credential file is staged. If a secret was already committed, stop and tell the user — the
  credential likely needs rotating and history rewriting.

## Tooling

Prefer MCP servers when available; fall back to the documented `curl`/SOQL in `docs/`:

- `sfmc-mcp-server` — Marketing Cloud auth, automations, Data Extensions, assets.
- `salesforce` / `salesforce-mcp-server` — SOQL, describes, record operations.

Raw REST/SOAP command examples live in `../../docs/TROUBLESHOOTING.md` and
`../../docs/AUTOMATIONS.md`. SFMC endpoints for tenant `mc4y763vp8r2sk5c18sv5j2sphry`:
auth `https://{tenant}.auth.marketingcloudapis.com/v2/token`,
REST `https://{tenant}.rest.marketingcloudapis.com`,
SOAP `https://{tenant}.soap.marketingcloudapis.com/Service.asmx`.

## Done Criteria

- **Diagnosis:** report what you checked (live vs repo), the finding, and the exact evidence
  (asset ID, DE key, SOQL, API response) so the user can verify.
- **Change:** report what changed, the backup/revert path (especially for Asset 67116), how
  you tested (Manual_Entries → Lead verification), and the result.
- **Handoff:** give the exact command, asset ID, DE key, or SOQL needed to reproduce/verify.
- **Keep docs current:** if you changed live behavior or found the docs wrong, update the
  relevant `../../docs/*.md` and add an entry to `../../docs/CHANGELOG.md`.
