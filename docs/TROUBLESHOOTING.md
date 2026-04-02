# Troubleshooting

## Common Issues

### Leads arriving without Lead_Details__c
- **Root cause:** Content Block regression — someone may have reverted or modified Asset ID 67116
- **Check:** Use SFMC REST API to read the current Content Block: `GET /asset/v1/content/assets/67116`
- **Verify:** The `CreateSalesforceObject` call should have 10 fields including `'Lead_Details__c', @Source`
- **Fix:** Re-apply the Content Block update using the code in [CONTENT_BLOCKS.md](CONTENT_BLOCKS.md)

### Automation not running
- **Check status:** Use SFMC REST API or Automation Studio UI to verify CRM_Integration is in `Scheduled` status
- **Re-trigger manually:** Use SOAP API Perform action to trigger CRM_Integration
- **Common cause:** SFMC session expiry, MC Connect OAuth token refresh failure

### Duplicate leads being created
- **Root cause:** CRMProcessed anti-join failure — the record's email wasn't in CRMProcessed
- **Check:** Query CRMProcessed DE for the email address to see if it was logged
- **Note:** The anti-join only prevents reprocessing of the exact same email+source combo

### CANNOT_UPDATE_CONVERTED_LEAD error (during backfill)
- **Cause:** Attempting to update a Lead that has been converted to a Contact
- **Fix:** Add `WHERE IsConverted = false` to any SOQL query used for bulk Lead updates

### Salesforce org blocks Apex deployment
- **Error:** `Can not create Apex Class on an active organization`
- **Cause:** The Salesforce org has deployment restrictions (no direct Apex class creation in prod)
- **Workaround:** Use `salesforce_execute_anonymous` for one-off Apex operations, or deploy through a sandbox + change set

### Too many query rows (50001) in Anonymous Apex
- **Cause:** Querying more than 50,000 records in a single SOQL query
- **Fix:** Add date filters (e.g., `CreatedDate = LAST_N_DAYS:90`) or `LIMIT` clauses
- **For bulk operations:** Process in batches of 400 IDs using IN clauses

### Source_OptInTo mapping not found for a source
- **Symptom:** Lead is created but no opt-in boolean field is set to true
- **Check:** Query the Source_OptInTo DE for the Source value
- **Fix:** Add a row to Source_OptInTo with Source, OptInField, and OptInDateField

## Useful API Commands

### Get SFMC auth token
```bash
curl -X POST "https://mc4y763vp8r2sk5c18sv5j2sphry.auth.marketingcloudapis.com/v2/token" \
  -H "Content-Type: application/json" \
  -d '{"grant_type":"client_credentials","client_id":"limi2qq52o8nlxrxh5ymapcn","client_secret":"YOUR_SECRET"}'
```

### Read Content Block
```bash
curl "https://mc4y763vp8r2sk5c18sv5j2sphry.rest.marketingcloudapis.com/asset/v1/content/assets/67116" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Query CRMProcessed for a specific email
```bash
curl "https://mc4y763vp8r2sk5c18sv5j2sphry.rest.marketingcloudapis.com/data/v1/customobjectdata/key/CRMProcessed/rowset?$filter=EmailAddress%20eq%20'test@example.com'" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
