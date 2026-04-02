# Changelog

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
