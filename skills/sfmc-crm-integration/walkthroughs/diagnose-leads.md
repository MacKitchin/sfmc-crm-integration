# Walkthrough: Diagnose Lead Problems

Symptom-driven debugging for the most common "the leads look wrong" reports. Work top-down:
confirm the record reached each stage of the pipeline before blaming the next one.

Underlying reference: `../../docs/TROUBLESHOOTING.md`, `../../docs/SALESFORCE_FIELDS.md`,
`../../docs/DATA_EXTENSIONS.md`.

## Pipeline checkpoints (where a record can fall out)

```
Source form DE → Form_Entries → (anti-join vs CRMProcessed) → staging → Content Block 67116 → Lead → CRMProcessed
```

For any "missing lead" report, find the last checkpoint where the record exists.

## Baseline: find leads created by the integration

```sql
SELECT Id, Email, Lead_Details__c, LeadSource, Lead_Source__c, CreatedDate
FROM Lead
WHERE CreatedById = '0054X00000Dk173QAB'    -- MC Connect user
ORDER BY CreatedDate DESC
```

## Symptom: leads arriving with `Lead_Details__c = null`

Most likely a **Content Block regression** — someone reverted or edited Asset `67116` and
dropped the field.

1. Read the live Content Block:
   ```bash
   curl "https://mc4y763vp8r2sk5c18sv5j2sphry.rest.marketingcloudapis.com/asset/v1/content/assets/67116" \
     -H "Authorization: Bearer $SFMC_TOKEN"
   ```
2. Confirm the `CreateSalesforceObject('Lead', 10, …)` call includes `'Lead_Details__c', @Source`
   and `'LeadSource', 'MC BizBash'` (10 fields, not 8).
3. If missing, re-apply the correct code via `modify-content-block.md` (back up first).

Find the affected leads:
```sql
SELECT Id, Email, CreatedDate FROM Lead
WHERE CreatedById = '0054X00000Dk173QAB' AND Lead_Details__c = null
```
If these are historical (pre-fix) rather than new, use `backfill-lead-attribution.md`.

## Symptom: a submission never became a Lead

1. Did it reach `Form_Entries`? If it came from a source form, it only lands after the daily
   5am `FormEntries_ToCRM` run — a same-day submission may simply not be consolidated yet. For
   urgent cases, add it to `Manual_Entries`.
2. Is it already in `CRMProcessed`? If yes, the anti-join treats it as done and won't
   reprocess. Query CRMProcessed by email:
   ```bash
   curl "https://mc4y763vp8r2sk5c18sv5j2sphry.rest.marketingcloudapis.com/data/v1/customobjectdata/key/CRMProcessed/rowset?\$filter=EmailAddress%20eq%20'test@example.com'" \
     -H "Authorization: Bearer $SFMC_TOKEN"
   ```
3. Did the verification step reject it (bad email format / missing required field)?
4. Did `CRM_Integration` actually run? See `trigger-and-monitor-automation.md`.

## Symptom: duplicate leads created

The `CRMProcessed` anti-join only suppresses an exact email+source combo it has already
logged.

1. Query `CRMProcessed` for the email — was the original create logged?
2. If the same person submitted under a **different `Source`**, the integration treats it as a
   new processable record (by design). Salesforce-side duplicate rules / matching govern
   whether a true duplicate Lead is created.
3. If the original was never logged to `CRMProcessed`, that's the real bug — investigate why
   the audit write failed.

## Symptom: lead created but no opt-in boolean set

The `Source` has no row in `Source_OptInTo`.

1. Query `Source_OptInTo` (key `A6DA18FC-0754-464B-8DF5-31D2ACD0B811`) for the `Source`.
2. If absent, add the mapping row (see `add-new-source.md`, step 2). Several known sources are
   intentionally/accidentally unmapped — see the list in `../../docs/SOURCE_MAPPING.md`.

## Symptom: errors during bulk Lead updates

- `CANNOT_UPDATE_CONVERTED_LEAD` → add `WHERE IsConverted = false`.
- `Too many query rows: 50001` → add date/`LIMIT` filters or drive by explicit Id batches.
- `Can not create Apex Class on an active organization` → use Anonymous Apex, not class deploy.

## Always report

The checkpoint where the record was last seen, the exact query/asset you inspected, and the
specific fix applied or recommended.
