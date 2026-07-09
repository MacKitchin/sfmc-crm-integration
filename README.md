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
| **Content Block (Latest Backup)** | Asset ID `188074`, Key: `CRM_BKP_202604280821_DF` |

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

## Prerequisites

- [Salesforce CLI](https://developer.salesforce.com/tools/salesforcecli) (`sf`) — not legacy `sfdx`
- Access to the production org (`00D30000001H2naEAC`) for Lead field deploys
- SFMC Business Unit access (BizBash `534000167`) for automation and AMPscript changes
- Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before modifying the pipeline

## Local setup

```bash
git clone https://github.com/MacKitchin/sfmc-crm-integration.git
cd sfmc-crm-integration

sf org login web --alias connect-prod

# Validate Salesforce metadata (dry-run)
sf project deploy start --source-dir force-app --target-org connect-prod --dry-run

# Deploy Lead fields and related metadata
sf project deploy start --source-dir force-app --target-org connect-prod
```

### SFMC assets

AMPscript content blocks and automation documentation live in `sfmc-assets/` and `docs/`. SFMC-side changes are made in Marketing Cloud UI or via SFMC API — not via `sf project deploy`. See [docs/CONTENT_BLOCKS.md](docs/CONTENT_BLOCKS.md) and [docs/AUTOMATIONS.md](docs/AUTOMATIONS.md).

### Tests

See [tests/README.md](tests/README.md) for the security/validation test suite (active on `add-security-validation-suite` branch).

## Repository layout

```
sfmc-crm-integration/
├── force-app/           # Salesforce Lead fields (SFMC_Form_Submission_Date__c, etc.)
├── sfmc-assets/         # AMPscript content block references and backups
├── docs/                # Architecture, automations, troubleshooting
├── tests/               # Validation scripts
├── skills/              # Agent skills for SFMC work
├── sfdx-project.json    # sourceApiVersion 66.0
└── CLAUDE.md            # Repo-specific agent context
```

## Deployment notes

- **Salesforce metadata** — deploy via `sf project deploy start --source-dir force-app`
- **SFMC automations** — manual or API update; document every change in [docs/CHANGELOG.md](docs/CHANGELOG.md)
- **Always dry-run** before production Salesforce deploys — Lead is a shared object
- Check `git branch` before deploying — active work may be on `add-security-validation-suite`

## Key Contacts

- **Mac Kitchin** — CRM/Data Operations, integration owner
- **MC Connect System User** — `mc-connect-crm@bizbash.com` (creates Leads in Salesforce)

## API Credentials (SFMC)

- **Client ID:** `limi2qq52o8nlxrxh5ymapcn`
- **Auth Endpoint:** `https://mc4y763vp8r2sk5c18sv5j2sphry.auth.marketingcloudapis.com/v2/token`
- **REST Base:** `https://mc4y763vp8r2sk5c18sv5j2sphry.rest.marketingcloudapis.com`
- **SOAP Endpoint:** `https://mc4y763vp8r2sk5c18sv5j2sphry.soap.marketingcloudapis.com/Service.asmx`

> **Note:** Client secret is stored separately and should not be committed to version control. Use [../sfmc-mcp-server/.env.example](../sfmc-mcp-server/.env.example) as the env var naming reference for SFMC API tooling.

## Related

- **Canonical repo:** this directory — do not use `sfmc-crm-integration-main` (stale fork, API 61.0)
- Org knowledge: [../Salesforce/Knowledge/](../Salesforce/Knowledge/)
- SFMC MCP server: [../sfmc-mcp-server/](../sfmc-mcp-server/)
