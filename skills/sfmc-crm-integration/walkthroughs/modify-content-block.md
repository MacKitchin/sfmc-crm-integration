# Walkthrough: Modify the Lead-Creation Content Block

The AMPscript Content Block `CRM_Integration_ProcessRecs_BizBash` (**Asset ID `67116`**) is
the heart of the integration — it's the code that actually creates and updates Salesforce
Leads. Treat every edit as a production change with a guaranteed revert path.

Underlying reference: `../../docs/CONTENT_BLOCKS.md`, `../../docs/SALESFORCE_FIELDS.md`.

## What the Content Block does (per staging record)

1. Reads the `Source` column.
2. `LookupRows('Source_OptInTo', 'Source', @Source)` → the opt-in boolean field to set.
3. `LookupRows('Source_Campaign', 'Source', @Source)` → the Salesforce Campaign Id.
4. Checks Salesforce for an existing Lead/Contact by email.
5. **New:** `CreateSalesforceObject('Lead', 10, …)` with the 10 fields below.
6. **Existing:** `UpdateSingleSalesforceObject('Lead', @CRMID, …)` to set the opt-in flag.
7. `InsertDE('CRMProcessed', …)` to log CRMID, action, and source.

## The 10-field create (do not drop fields)

```ampscript
CreateSalesforceObject('Lead', 10,
  'FirstName',       @FirstName,
  'LastName',        @LastName,
  'Email',           @EmailAddress,
  'Company',         @Company,
  'Title',           @JobTitle,
  'Phone',           @Phone,
  'Lead_Source__c',  'MC BizBash',
  'LeadSource',      'MC BizBash',     /* standard field — added 2026-04-02 */
  'Lead_Details__c', @Source,          /* granular source — added 2026-04-02 */
  @OptInField,       'true'
)
```

`Lead_Details__c = @Source` is the source-attribution fix from April 2026. If an edit would
reduce the field count or remove `Lead_Details__c`/`LeadSource`, that is a regression — stop
and reconsider.

## Safe modification procedure

### 1. Read the current live code

```bash
curl "https://mc4y763vp8r2sk5c18sv5j2sphry.rest.marketingcloudapis.com/asset/v1/content/assets/67116" \
  -H "Authorization: Bearer $SFMC_TOKEN"
```

Capture the current `content` so you know exactly what you're changing.

### 2. Back it up to a NEW asset first

Create a dated backup so you always have a revert target (this is how Asset `179321` /
`CRM_ProcessRecs_BKP_<date>` was made):

```bash
curl -X POST "https://mc4y763vp8r2sk5c18sv5j2sphry.rest.marketingcloudapis.com/asset/v1/content/assets" \
  -H "Authorization: Bearer $SFMC_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"CRM_ProcessRecs_BKP_YYYYMMDD","assetType":{"id":220},"content":"<CURRENT CODE>"}'
```

Record the new backup asset ID and key in `../../docs/CONTENT_BLOCKS.md`.

### 3. Patch the live asset

```bash
curl -X PATCH "https://mc4y763vp8r2sk5c18sv5j2sphry.rest.marketingcloudapis.com/asset/v1/content/assets/67116" \
  -H "Authorization: Bearer $SFMC_TOKEN" -H "Content-Type: application/json" \
  -d '{"content":"<NEW AMPSCRIPT>"}'
```

### 4. Test before trusting it

1. Insert a test record into `Manual_Entries`.
2. Trigger `CRM_IntegrationManual`.
3. Verify the resulting Lead has every expected field (see `diagnose-leads.md` for the SOQL).
   Confirm `Lead_Details__c` is populated.

### 5. Revert if anything looks wrong

PATCH Asset `67116` with the backup `content` from step 2. Reverting is always preferred over
debugging live.

### 6. Document

Update `../../docs/CONTENT_BLOCKS.md` (modification history) and `../../docs/CHANGELOG.md`
with what changed, the backup asset ID, and the verifying test Lead Id.

## Notes / constraints

- Asset type for these code snippet blocks is `220`.
- SFMC script execution times out around ~30 minutes per run; keep added logic lean so the
  hourly job finishes within typical daily volume.
- Never edit `67116` in place without completing step 2 first.
