# SFMC → Salesforce CRM Integration

**BizBash Lead Creation Pipeline**

This repo documents the Marketing Cloud (SFMC) to Salesforce CRM integration that creates Lead records from form submissions across ~35 BizBash content sources (newsletters, whitepapers, webinars, syndication partnerships, etc.).

## Quick Reference

| Component | Value |
|---|---|
| **Salesforce Org ID** | `00D30000001H2naEAC` |
| **SFMC Business Unit** | BizBash (`534000167`) |
| **SFMC Enterprise** | `526003676` |
| **SFMC Subdomain** | `mc4y763vp8r2sk5c18sv5j2sphry` |
| **MC Connect User** | `mc-connect-crm@bizbash.com` (ID: `0054X00000Dk173QAB`) |
| **Content Block (Live)** | Asset ID `67116`, Key: `CRM_Integration_ProcessRecs_BizBash` |
| **Content Block (Backup)** | Asset ID `179321`, Key: `CRM_ProcessRecs_BKP_20260402` |

## Pipeline Overview

```
Form Submissions (35+ sources)
        │
        ▼
[FormEntries_ToCRM Automation] ── Daily 5am ET
        │  UNION ALL SQL across ~35 form DEs
        ▼
   Form_Entries DE (11 columns)
        │
        ▼
[CRM_Integration Automation] ── Hourly
        │  Step 1: SQL anti-join against CRMProcessed
        │  Step 2: Verification
        │  Step 3: AMPscript Content Block
        ▼
   Salesforce Lead (via MC Connect bridge)
        │  CreateSalesforceObject() / UpdateSingleSalesforceObject()
        ▼
   CRMProcessed DE (audit trail)
```

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | Full pipeline architecture, data flow, and system diagram |
| [Automations](docs/AUTOMATIONS.md) | SFMC automation configuration and schedules |
| [Content Blocks](docs/CONTENT_BLOCKS.md) | AMPscript code — the core Lead creation logic |
| [Data Extensions](docs/DATA_EXTENSIONS.md) | DE schemas, keys, and relationships |
| [Source Mapping](docs/SOURCE_MAPPING.md) | Source → OptIn field mapping table |
| [Salesforce Fields](docs/SALESFORCE_FIELDS.md) | Lead fields set by the integration |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues, debugging, and recovery |
| [Changelog](docs/CHANGELOG.md) | Change history and modification log |

## Key Contacts

- **Mac Kitchin** — CRM/Data Operations, integration owner
- **MC Connect System User** — `mc-connect-crm@bizbash.com` (creates Leads in Salesforce)

## API Credentials (SFMC)

- **Client ID:** `limi2qq52o8nlxrxh5ymapcn`
- **Auth Endpoint:** `https://mc4y763vp8r2sk5c18sv5j2sphry.auth.marketingcloudapis.com/v2/token`
- **REST Base:** `https://mc4y763vp8r2sk5c18sv5j2sphry.rest.marketingcloudapis.com`
- **SOAP Endpoint:** `https://mc4y763vp8r2sk5c18sv5j2sphry.soap.marketingcloudapis.com/Service.asmx`

> **Note:** Client secret is stored separately and should not be committed to version control.
