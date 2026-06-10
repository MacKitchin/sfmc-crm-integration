# Walkthrough: Backfill Lead Source Attribution

Before the April 2026 fix, the Content Block discarded the granular `Source`, so historical
leads have `Lead_Details__c = null` (and previously `LeadSource = null`). This walkthrough
repairs those records using `CRMProcessed` as the source of truth. The original backfill
corrected **7,697 leads across 31 source types**.

Underlying reference: `../../docs/CHANGELOG.md`, `../../docs/SALESFORCE_FIELDS.md`,
`../../docs/TROUBLESHOOTING.md`.

## Why CRMProcessed is the source of truth

Every lead the integration ever created was logged to the `CRMProcessed` DE with its
`EmailAddress`, `Source`, and `CRMID` (the Salesforce Lead/Contact Id). That mapping of
`CRMID → Source` is what lets you set `Lead_Details__c` correctly after the fact.

## Steps

### 1. Scope the gap in Salesforce

```sql
SELECT COUNT(Id)
FROM Lead
WHERE CreatedById = '0054X00000Dk173QAB'   -- MC Connect user
  AND Lead_Details__c = null
  AND IsConverted = false
```

This count is your target; re-run it at the end to confirm it dropped to ~0.

### 2. Export the CRMID → Source map from CRMProcessed

Page through the DE via REST (it has ~220k+ rows, so paginate):

```bash
curl "https://mc4y763vp8r2sk5c18sv5j2sphry.rest.marketingcloudapis.com/data/v1/customobjectdata/key/CRMProcessed/rowset?\$pageSize=2500&\$page=1" \
  -H "Authorization: Bearer $SFMC_TOKEN"
```

Build a lookup of Salesforce `CRMID → Source` (dedupe to the most recent/most specific source
per CRMID if a record appears more than once).

### 3. Update Leads via Anonymous Apex (in batches)

This org blocks Apex class deployment to production, so use **Anonymous Apex** for the
update. Mind the limits:

- Batch IDs ~400 per `IN` clause / per DML chunk.
- Always filter `WHERE IsConverted = false` — updating a converted lead throws
  `CANNOT_UPDATE_CONVERTED_LEAD`.
- Avoid querying >50,000 rows in one SOQL (the `50001` error). Drive updates from explicit Id
  lists or add date filters (`CreatedDate = LAST_N_DAYS:90`).

```apex
// Example shape — feed in CRMID->Source from CRMProcessed in batches
Map<Id, String> idToSource = new Map<Id, String>{
  '00Q...AAA' => 'EventTechNewsletter_Form',
  '00Q...BBB' => 'Convene_Syndication_March2026'
  // ... up to ~400 per run
};
List<Lead> toUpdate = new List<Lead>();
for (Lead l : [SELECT Id FROM Lead
               WHERE Id IN :idToSource.keySet() AND IsConverted = false]) {
  l.Lead_Details__c = idToSource.get(l.Id);
  toUpdate.add(l);
}
update toUpdate;
System.debug('Updated ' + toUpdate.size());
```

### 4. Strategy for very large sets (optional)

The original backfill used a two-pass approach to stay efficient: bulk-set the dominant
source first (one source accounted for ~72% of records), then correct the minority
(~2,122 non-dominant leads) to their actual sources from CRMProcessed. Use this only when one
source clearly dominates and you can verify the corrections.

### 5. Verify

Re-run the count from step 1 (expect ~0 remaining nulls), and spot-check the distribution:

```sql
SELECT Lead_Details__c, COUNT(Id)
FROM Lead
WHERE CreatedById = '0054X00000Dk173QAB' AND Lead_Details__c != null
GROUP BY Lead_Details__c ORDER BY COUNT(Id) DESC
```

### 6. Document

Record the count updated and method in `../../docs/CHANGELOG.md`.

## Pitfalls

- Forgetting `IsConverted = false` → `CANNOT_UPDATE_CONVERTED_LEAD`.
- Querying the whole Lead table at once → `Too many query rows: 50001`.
- Trusting a stale CRMProcessed export — page through all rows before mapping.
