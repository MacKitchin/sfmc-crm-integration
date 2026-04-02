# Content Blocks

## CRM_Integration_ProcessRecs_BizBash

- **Asset ID:** `67116`
- **Customer Key:** `CRM_Integration_ProcessRecs_BizBash`
- **Type:** Code Snippet Block (Asset Type 220)
- **Backup:** Asset ID `179321`, Key: `CRM_ProcessRecs_BKP_20260402`

### What It Does

For each record in the staging DE (output of the CRM_Integration SQL step), this AMPscript:

1. Reads the `Source` column value
2. Looks up `Source_OptInTo` mapping DE to find which boolean field to set (e.g., `BizBash_White_Paper__c = true`)
3. Looks up `Source_Campaign` mapping DE to find the Salesforce Campaign ID
4. Checks if a Lead or Contact already exists in Salesforce with that email address
5. **If new lead:** Calls `CreateSalesforceObject('Lead', ...)` with 10 fields
6. **If existing:** Calls `UpdateSingleSalesforceObject()` to set the opt-in flag
7. Writes the result to `CRMProcessed` DE

### Key AMPscript Functions Used

- `CreateSalesforceObject('Lead', 10, ...)` — Creates a new Lead with 10 field-value pairs
- `UpdateSingleSalesforceObject('Lead', @CRMID, ...)` — Updates an existing Lead
- `RetrieveSalesforceObjects('Lead', ...)` — Checks for existing records
- `LookupRows('Source_OptInTo', 'Source', @Source)` — Maps Source to opt-in field
- `LookupRows('Source_Campaign', 'Source', @Source)` — Maps Source to Campaign ID
- `InsertDE('CRMProcessed', ...)` — Writes audit trail

### Fields Set on CreateSalesforceObject (10 fields)

```
CreateSalesforceObject('Lead', 10,
  'FirstName',       @FirstName,
  'LastName',        @LastName,
  'Email',           @EmailAddress,
  'Company',         @Company,
  'Title',           @JobTitle,
  'Phone',           @Phone,
  'Lead_Source__c',  'MC BizBash',
  'LeadSource',      'MC BizBash',        ← Added April 2, 2026
  'Lead_Details__c', @Source,              ← Added April 2, 2026
  @OptInField,       'true'
)
```

### Modification History

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
