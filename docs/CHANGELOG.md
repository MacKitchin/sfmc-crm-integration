# Changelog

## [1.1.0] — 2026-06-10

### Added — SFMC Lead Data view + report deployed to production
- **Lead list view** `SFMC Lead Data - Enrichment` (`Lead.SFMC_Lead_Data`, Id `00BUX000006ZTlF2AW`): 15 columns (list view max) covering pipeline attribution (Lead_Details__c, Lead_Source__c, SFMC_Form_Submission_Date__c, SFMC_Import_Source__c), Silverpop sync, ZoomInfo ID, Quality Score, deliverability. Filter: `silverpop__Silverpop_RecipientID__c` not blank.
- **Lead report** `SFMC Lead Data - Segmentation` (`unfiled$public/SFMC_Lead_Data_Report`, Id `00OUX00000AusKv2AJ`, Public Reports folder): 46 columns — full set incl. all 14 BizBash opt-in booleans, MC subscription flags, Silverpop scores, ZoomInfo enrichment status/dates, quality/decision-maker scores. Same filter; ~105k rows on first run.
- Deployed via Metadata API `createMetadata` from Anonymous Apex (org-domain callout); no Apex class deploy needed.
- **Bundle corrected:** `SFMC_Lead_View_Metadata_bundle` XMLs updated to deployed state. Original bundle had invalid tokens — list views need `LEAD.`-prefixed standard fields and max 15 columns / 40-char label; LeadList reports use `FIRST_NAME`/`LAST_NAME`/`CITY`/`STATE`/`COUNTRY` (not `FULL_NAME`/`ADDRESS1_*`) and `scope=org` (not `organization`).

## [1.0.0] — 2026-04-02

### Fixed — Lead Source Attribution
- **Problem:** All leads created by the SFMC CRM_Integration arrived in Salesforce with `LeadSource = null` and `Lead_Details__c = null`. The granular source identifier (newsletter, whitepaper, webinar, etc.) was being discarded.
- **Root cause:** The AMPscript Content Block `CRM_Integration_ProcessRecs_BizBash` (Asset ID: 67116) only passed 8 fields to `CreateSalesforceObject()`. The `Source` column was used for `Source_OptInTo` boolean lookups but never stored on the Lead record itself.
- **Fix:** Updated the Content Block to pass 10 fields, adding:
  - `'LeadSource', 'MC BizBash'` (standard field)
  - `'Lead_Details__c', @Source` (granular source identifier)
- **Backup:** Original code preserved at Asset ID `179321`, Key: `CRM_ProcessRecs_BKP_20260402`
- **Verification:** Test lead `00QUX00000QGaa12AD` confirmed with correct attribution

### Added — Historical Backfill
- Backfilled `Lead_Details__c` on 7,697 historical leads across 31 source types
- Method: Bulk Anonymous Apex execution using SFMC CRMProcessed data as the source-of-truth
- Strategy: Set all leads to `MeetingsNet2025` (72% of records), then corrected 2,122 non-MN leads to their actual sources

### Documented
- Created this repo with full integration documentation
- Architecture, automation configs, Content Block code, DE schemas, source mappings, troubleshooting guide
