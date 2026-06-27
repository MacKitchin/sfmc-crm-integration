# sfmc-crm-integration

> Org-wide context (org model, auth, API 66.0, `sf` not `sfdx`, knowledge base) is in
> the parent `~/Repos/CLAUDE.md`. This file covers only what's specific to this repo.

## Purpose

The Marketing Cloud (SFMC) → Salesforce CRM integration that creates **Lead** records
from form submissions across ~35 BizBash content sources (newsletters, whitepapers,
webinars, syndication). The live logic is an SFMC AMPscript Content Block, not Apex —
this repo is primarily docs + the AMPscript source + the Lead field metadata it sets.

## Key IDs

- Salesforce Org ID: `00D30000001H2naEAC`
- SFMC Business Unit: BizBash (`534000167`), Enterprise `526003676`
- Live Content Block: Asset ID `67116`, Key `CRM_Integration_ProcessRecs_BizBash`
- Runs daily ~5am ET via the `FormEntries_ToCRM` automation

## Owned metadata

- No custom objects. Adds Lead fields `SFMC_Form_Submission_Date__c`, `SFMC_Import_Source__c`
- `force-app/` — the two Lead field metas above
- `sfmc-assets/CRM_Integration_ProcessRecs_BizBash.ampscript` — source of the live block

## Working here

The deployed integration creates Leads with **16 fields** (address + source/date
attribution). Keep `docs/CONTENT_BLOCKS.md` and `docs/CHANGELOG.md` in sync with the
live AMPscript asset. Back up the live block (note the new Asset ID/Key) before editing.

```bash
sf project deploy start --source-dir force-app        # deploy Lead field metadata only
```
