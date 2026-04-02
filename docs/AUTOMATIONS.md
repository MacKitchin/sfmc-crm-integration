# Automations

## FormEntries_ToCRM

- **Schedule:** Daily at 5:00 AM ET
- **Purpose:** Consolidates ~35 individual form Data Extensions into one `Form_Entries` DE
- **Type:** SQL Query Activity (UNION ALL)
- **Output DE:** `Form_Entries`
- **Output Schema:** EmailAddress, FirstName, LastName, JobTitle, Company, Phone, Address, City, State, Country, Source

Each source form DE contributes rows with a hardcoded `Source` value identifying the originating form/campaign. New form sources require adding a new `SELECT ... UNION ALL` block to this SQL.

## CRM_Integration

- **Schedule:** Hourly
- **Status:** Active (Scheduled)
- **Purpose:** Creates/updates Salesforce Leads from new form submissions
- **Steps:**
  1. **SQL Query** — Anti-joins `Form_Entries` + `Manual_Entries` against `CRMProcessed` to find unprocessed records
  2. **Verification** — Validates email format and required fields
  3. **AMPscript Content Block** — `CRM_Integration_ProcessRecs_BizBash` (Asset ID: `67116`) — creates/updates Leads in Salesforce

## CRM_IntegrationManual

- **Schedule:** Ready (manual trigger only)
- **Purpose:** Same logic as CRM_Integration but for ad-hoc/manual runs
- **Use case:** Processing `Manual_Entries` DE records outside the hourly schedule

## Triggering an Automation via API

Use the SFMC SOAP API `Perform` action:

```
POST https://mc4y763vp8r2sk5c18sv5j2sphry.soap.marketingcloudapis.com/Service.asmx
SOAPAction: "Perform"
```

See the SOAP XML template in `scripts/trigger_automation.xml` for the full request body.
