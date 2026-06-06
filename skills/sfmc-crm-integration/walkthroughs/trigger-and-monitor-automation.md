# Walkthrough: Trigger & Monitor the Automations

How to run and watch the pipeline safely. Triggering `CRM_Integration` is a **write
operation** — it creates real Leads — so confirm with the user first unless they explicitly
asked you to run it.

Underlying reference: `../../docs/AUTOMATIONS.md`, `../../docs/ARCHITECTURE.md`.

## The three automations

- **`FormEntries_ToCRM`** — daily 5:00 AM ET. Consolidates ~35 source DEs into `Form_Entries`
  via UNION ALL SQL. Run this if you need fresh consolidation before the scheduled time.
- **`CRM_Integration`** — hourly, Active/Scheduled. The production path: SQL anti-join →
  verification → Content Block 67116 → Salesforce Leads. Normally leave it on its schedule.
- **`CRM_IntegrationManual`** — manual trigger only. Same logic, intended for ad-hoc runs and
  for processing `Manual_Entries`. **Use this for testing**, not the live hourly automation.

## Check status before doing anything

Use `sfmc-mcp-server` (preferred) or the SFMC UI / REST to confirm `CRM_Integration` is in
`Scheduled` status and not errored. A stalled automation is often an expired SFMC session or
an MC Connect OAuth token refresh failure (see `diagnose-leads.md` / docs/TROUBLESHOOTING.md).

## Trigger via the SOAP `Perform` action

```
POST https://mc4y763vp8r2sk5c18sv5j2sphry.soap.marketingcloudapis.com/Service.asmx
SOAPAction: "Perform"
```

The request body performs the `Automation` object by its key/ObjectID. (The repo's
`docs/AUTOMATIONS.md` references a SOAP XML template; build the `PerformRequestMsg` with the
target automation's ObjectID and a valid OAuth bearer token.) Prefer an MCP tool if one
exposes "run automation" directly.

## Recommended test loop (safe)

1. Insert a single test record into the `Manual_Entries` DE (email you control + a known
   `Source`).
2. Trigger **`CRM_IntegrationManual`** (not the live hourly one).
3. Watch for completion, then verify outputs (below).

## Monitor results

Confirm the run actually produced leads:

1. **Salesforce** — new Lead(s) by the MC Connect user:
   ```sql
   SELECT Id, Email, Lead_Details__c, LeadSource, CreatedDate
   FROM Lead
   WHERE CreatedById = '0054X00000Dk173QAB' AND CreatedDate = TODAY
   ORDER BY CreatedDate DESC
   ```
2. **CRMProcessed audit** — new rows for the processed email(s):
   ```bash
   curl "https://mc4y763vp8r2sk5c18sv5j2sphry.rest.marketingcloudapis.com/data/v1/customobjectdata/key/CRMProcessed/rowset?\$filter=EmailAddress%20eq%20'your-test@example.com'" \
     -H "Authorization: Bearer $SFMC_TOKEN"
   ```
   A matching row with the correct `Action` (New/Update), `CRMID`, and `Source` confirms the
   end-to-end path worked.

## Safety reminders

- Don't trigger the **live hourly** `CRM_Integration` for tests — use `CRM_IntegrationManual`.
- Each run is bounded by the ~30-minute SFMC script timeout; very large `Manual_Entries`
  batches may need to be split.
- Never paste the OAuth token or client secret into notes, docs, or commit messages.
