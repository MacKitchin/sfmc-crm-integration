# Glossary

Companion reference to `SKILL.md` and `../../docs/`. This file only defines terms — it does not
restate the pipeline, rules, or procedures (see `SKILL.md` and the walkthroughs for those).

## SFMC (Salesforce Marketing Cloud)

- **SFMC:** Salesforce Marketing Cloud — where the integration's logic runs (SQL Query
  Activities + an AMPscript Content Block).
- **Business Unit (BU):** A Marketing Cloud account partition. Here: **BizBash** (`534000167`)
  under Enterprise `526003676`.
- **Tenant / subdomain:** The org-specific MC host prefix (`mc4y763vp8r2sk5c18sv5j2sphry`) used
  in auth/REST/SOAP URLs.
- **Data Extension (DE):** A Marketing Cloud table. Key ones: `Form_Entries`, `Manual_Entries`,
  `CRMProcessed`, `Source_OptInTo`, `Source_Campaign`.
- **Automation:** A scheduled/triggered sequence of activities in Automation Studio. Here:
  `FormEntries_ToCRM` (daily 5am ET), `CRM_Integration` (hourly), `CRM_IntegrationManual` (manual).
- **SQL Query Activity:** An automation step running SQL over DEs (e.g. the `UNION ALL` that
  consolidates ~35 source DEs; the anti-join that finds unprocessed rows).
- **Anti-join:** The SQL pattern (`LEFT JOIN … WHERE … IS NULL`) used against `CRMProcessed` to
  select only rows not yet sent to CRM (the dedup mechanism).
- **AMPscript:** SFMC's scripting language; the Content Block uses it to create/update Leads.
- **Content Block:** A reusable Content Builder asset. The **live** one is Asset `67116`
  (`CRM_Integration_ProcessRecs_BizBash`); the **backup** is Asset `179321`
  (`CRM_ProcessRecs_BKP_20260402`).
- **Asset ID / Key:** The numeric ID and customer key identifying a Content Builder asset.
- **MC Connect:** The Marketing Cloud ↔ Salesforce bridge used to write Leads. Runs as
  **`mc-connect-crm@bizbash.com`** (`0054X00000Dk173QAB`) — the Lead `CreatedById`.
- **`CreateSalesforceObject()` / `UpdateSingleSalesforceObject()`:** AMPscript MC Connect
  functions that create/update Salesforce records from SFMC.

## Salesforce

- **Lead:** The Salesforce record this pipeline creates from form submissions.
- **`LeadSource` / `Lead_Source__c`:** Standard + custom source fields; both set to `MC BizBash`.
- **`Lead_Details__c`:** Custom field carrying the specific `@Source` (the attribution that is
  "the whole point" of the integration).
- **`IsConverted`:** Lead flag; updates should filter `WHERE IsConverted = false`.
- **Org ID:** `00D30000001H2naEAC` (BizBash/Connect production).
- **Anonymous Apex:** Ad-hoc Apex execution (direct Apex **class** deploy to prod is blocked).

## Pipeline / project

- **Source:** One of ~35 BizBash content origins (newsletter, whitepaper, webinar, syndication
  partner, etc.); hardcoded per `UNION ALL` block in `FormEntries_ToCRM`.
- **Opt-in mapping (`Source_OptInTo`):** DE mapping a Source → the opt-in field(s) to set.
- **Campaign mapping (`Source_Campaign`):** DE mapping a Source → campaign.
- **The 11 standardized columns:** `EmailAddress, FirstName, LastName, JobTitle, Company, Phone,
  Address, City, State, Country, Source` — carried through the pipeline.
- **Dedup/audit key:** `CRMProcessed` row identity (`EmailAddress, Source, Action, CRMID`);
  append-only.
- **Backfill:** Repairing attribution (`Lead_Details__c`) on historical Leads — see
  `walkthroughs/backfill-lead-attribution.md`.
- **Marketable lead:** A Lead eligible for marketing (opt-in present) — see the
  `Marketable_*` report exports in the repo root.
