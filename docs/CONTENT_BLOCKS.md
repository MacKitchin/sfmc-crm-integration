# Content Blocks

## CRM_Integration_ProcessRecs_BizBash

- **Asset ID:** `67116`
- **Customer Key:** `CRM_Integration_ProcessRecs_BizBash`
- **Type:** Code Snippet Block (Asset Type 220)
- **Latest Backup:** Asset ID `188074`, Key: `CRM_BKP_202604280821_DF`
- **Prior Backups:** Asset ID `188072`, Key: `CRM_ProcessRecs_BKP_20260428T075606Z`; Asset ID `179321`, Key: `CRM_ProcessRecs_BKP_20260402`

### What It Does

For each record in the staging DE (output of the CRM_Integration SQL step), this AMPscript:

1. Reads the `Source` column value
2. Looks up `Source_OptInTo` mapping DE to find which boolean field to set (e.g., `BizBash_White_Paper__c = true`)
3. Looks up `Source_Campaign` mapping DE to find the Salesforce Campaign name
4. Checks if a Lead or Contact already exists in Salesforce with that email address
5. Formats `DateAdded` into a Salesforce-compatible DateTime string for `SFMC_Form_Submission_Date__c`
6. **If new lead:** Calls `CreateSalesforceObject('Lead', ...)` with 16 fields
7. **If existing:** Calls `UpdateSingleSalesforceObject()` to set address/source attribution and the opt-in flag
8. Writes the result to `CRMProcessed` DE

### Key AMPscript Functions Used

- `CreateSalesforceObject('Lead', 16, ...)` — Creates a new Lead with 16 field-value pairs
- `UpdateSingleSalesforceObject('Lead', @CRMID, ...)` — Updates an existing Lead
- `RetrieveSalesforceObjects('Lead', ...)` — Checks for existing records
- `LookupRows('Source_OptInTo', 'Source', @Source)` — Maps Source to opt-in field
- `LookupRows('Source_Campaign', 'Source', @Source)` — Maps Source to Campaign name
- `insertData('CRMProcessed', ...)` — Writes audit trail

### Fields Set on CreateSalesforceObject (16 fields)

```
CreateSalesforceObject('Lead', 16,
  'FirstName',       @FirstName,
  'LastName',        @LastName,
  'Company',         @Company,
  'Email',                         @EmailAddress,
  'Phone',                         @Phone,
  'Title',                         @JobTitle,
  'Street',                        @Address,
  'City',                          @City,
  'State',                         @State,
  'Country',                       @Country,
  'New_MC_Lead_To_Sort__c',        'true',
  'Lead_Source__c',                'MC BizBash',
  'LeadSource',                    'MC BizBash',
  'Lead_Details__c',               @Source,
  'SFMC_Form_Submission_Date__c',  @SubmissionDate,
  'SFMC_Import_Source__c',         'CRM_Integration'
)
```

`@SubmissionDate` is derived from `DateAdded` when present and falls back to `Now()`:

```
if empty(@DateAdded) then
  set @SubmissionDate = Replace(FormatDate(Now(),"yyyy-MM-ddT","hh:mm:ss"),' ','')
else
  set @SubmissionDate = Replace(FormatDate(@DateAdded,"yyyy-MM-ddT","hh:mm:ss"),' ','')
endif
```

### Modification History

**April 28, 2026 — Expanded Lead Field Capture**

- **Changed:** Field count from 10 → 16 in `CreateSalesforceObject` call
- **Added:** Standard address fields: `Street`, `City`, `State`, `Country`
- **Added:** `SFMC_Form_Submission_Date__c` populated from SFMC `DateAdded` / `@SubmissionDate`
- **Added:** `SFMC_Import_Source__c = "CRM_Integration"`
- **Updated:** Existing Lead update path now updates address, source attribution, submission date, and import source fields
- **Backup:** Original live code preserved at Asset ID `188072`, Key: `CRM_ProcessRecs_BKP_20260428T075606Z`
- **Date format fix:** `DateAdded` is formatted before being passed to Salesforce DateTime fields
- **Date format backup:** Pre-fix expanded code preserved at Asset ID `188074`, Key: `CRM_BKP_202604280821_DF`
- **Verified:** Production test lead `00QUX00000R61xx2AB` created from `EventTechNewsletter_Form` with address fields, source attribution, `SFMC_Form_Submission_Date__c`, `SFMC_Import_Source__c`, opt-ins, and `CRMProcessed` audit row populated
- **Tracked Source:** `sfmc-assets/CRM_Integration_ProcessRecs_BizBash.ampscript`


**April 2, 2026 — Lead Source Attribution Fix**

- **Changed:** Field count from 8 → 10 in `CreateSalesforceObject` call
- **Added:** `'LeadSource', 'MC BizBash'` (standard field — was previously null)
- **Added:** `'Lead_Details__c', @Source` (stores the granular source identifier)
- **Backup:** Original code preserved at Asset ID `179321`, Key: `CRM_ProcessRecs_BKP_20260402`
- **Verified:** Test lead `00QUX00000QGaa12AD` confirmed with `Lead_Details__c = "Convene_Syndication_March2026"`

### How to Modify

1. **Always create a backup first** — Use the SFMC REST API: `POST /asset/v1/content/assets` with the current code
2. **Update the live asset** — `PATCH /asset/v1/content/assets/67116` with `{"content": "new AMPscript code"}`
3. **Test** — Insert a test record into `Manual_Entries` DE, trigger `CRM_Integration`, verify the Lead in Salesforce
4. **Revert if needed** — Copy the backup content back to Asset ID `67116`
