# Architecture

## System Overview

The SFMC → Salesforce CRM integration is a **two-stage automation pipeline** that collects form submissions from ~35 BizBash content sources, deduplicates them against previously processed records, and creates Lead records in Salesforce via the MC Connect bridge.

There is **no custom REST webhook or Apex REST endpoint** involved. The entire integration runs inside SFMC using SQL Query Activities and an AMPscript Content Block that calls `CreateSalesforceObject()` and `UpdateSingleSalesforceObject()` — native SFMC functions that use the MC Connect bridge (system user `mc-connect-crm@bizbash.com`).

## Data Flow

### Stage 1: FormEntries_ToCRM (Daily, 5am ET)

This automation runs a massive UNION ALL SQL query across ~35 individual form Data Extensions. Each form DE captures submissions from a specific content source (newsletter signup, whitepaper download, webinar registration, etc.).

The SQL consolidates all form submissions into a single `Form_Entries` Data Extension with 11 standardized columns:

```
EmailAddress, FirstName, LastName, JobTitle, Company,
Phone, Address, City, State, Country, Source
```

The `Source` column carries the originating form identifier (e.g., `EventTechNewsletter_Form`, `Convene_Syndication_March2026`, `CORTEvents_FebWebinar`).

### Stage 2: CRM_Integration (Hourly)

This automation has three steps:

**Step 1 — SQL Query (Anti-Join)**

Queries `Form_Entries` and `Manual_Entries` DEs, anti-joining against the `CRMProcessed` DE to identify records that haven't been sent to Salesforce yet. Output goes to a staging DE for processing.

**Step 2 — Verification**

Validates the staging records (email format, required fields, etc.).

**Step 3 — AMPscript Content Block Execution**

Runs the Content Block `CRM_Integration_ProcessRecs_BizBash` (Asset ID: `67116`). For each record in the staging DE, the script:

1. Looks up the `Source` value in the `Source_OptInTo` mapping table (DE Key: `A6DA18FC-0754-464B-8DF5-31D2ACD0B811`) to determine which BizBash opt-in boolean field to set on the Lead.
2. Looks up the `Source` value in the `Source_Campaign` mapping table (DE Key: `3951ACCF-6B86-4FBA-9710-E4C28C0BE7A0`) to determine Salesforce Campaign membership.
3. Checks if a Lead/Contact already exists in Salesforce with that email.
4. If **new**: Calls `CreateSalesforceObject('Lead', ...)` with 10 fields including `Lead_Details__c` (granular source) and `LeadSource` (= "MC BizBash").
5. If **existing**: Calls `UpdateSingleSalesforceObject()` to update the opt-in field.
6. Writes the result to `CRMProcessed` DE with the CRMID, action taken, and source.

## Authentication

The MC Connect bridge uses an OAuth connection between SFMC and Salesforce. The system user `mc-connect-crm@bizbash.com` (Salesforce User ID: `0054X00000Dk173QAB`) is the CreatedBy user for all Leads created through this pipeline. No API keys or tokens are needed for the SFMC-to-Salesforce leg — it's handled by the MC Connect configuration.

## Key Constraints

- **Salesforce org blocks Apex class deployment** to production (`Can not create Apex Class on an active organization`). Use Anonymous Apex for one-off operations.
- **CRMProcessed DE** has ~220,000+ records and is append-only. It serves as the audit trail and deduplication key.
- **SFMC script timeout** is ~30 minutes per execution. For the hourly automation, this is sufficient for typical daily volumes.
- **MC Connect** uses a specific Salesforce Connected App. The connection must be maintained in SFMC Setup → Salesforce Integration.
