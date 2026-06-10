# Walkthrough: Add a New Form/Content Source

Use this when a new BizBash form, newsletter, whitepaper, webinar, or syndication feed needs
its submissions turned into Salesforce Leads. Adding a source is a **coordinated change**:
the consolidation SQL and the mapping DEs must change together, or leads will arrive with no
opt-in flag (or not arrive at all).

Underlying reference: `../../docs/SOURCE_MAPPING.md`, `../../docs/AUTOMATIONS.md`,
`../../docs/DATA_EXTENSIONS.md`.

## Before you start — gather inputs

You need four things from the requester. Don't guess these:

1. **Source form DE** — the SFMC Data Extension that captures the new submissions (name/key),
   and which of its columns map to the 11 standard columns.
2. **`Source` identifier** — the exact string that will tag these rows (e.g.
   `Convene_Syndication_March2026`). This is what lands in `Lead_Details__c`, so make it
   stable and descriptive. Match the existing naming style.
3. **Opt-in field** — the Salesforce Lead boolean API field to set `true` for this source
   (e.g. `BizBash_White_Paper__c`) plus its companion date field (e.g.
   `BizBash_White_Paper_Date__c`). Confirm the field exists via a Salesforce describe.
4. **Campaign (optional)** — the Salesforce Campaign Id if these leads should become Campaign
   Members.

## Steps

### 1. Add a UNION ALL block to `FormEntries_ToCRM`

This daily 5am ET SQL Query Activity consolidates all source DEs into `Form_Entries`. Add a
new `SELECT … UNION ALL` block that reads the new form DE and maps its columns to the 11
standard columns, hardcoding the `Source` value:

```sql
-- existing blocks above ...
UNION ALL
SELECT
  EmailAddress, FirstName, LastName, JobTitle, Company,
  Phone, Address, City, State, Country,
  'Convene_Syndication_March2026' AS Source      -- hardcoded for this block
FROM   [Source_Form_DE_Name]
WHERE  EmailAddress IS NOT NULL
```

Keep column order and names identical to the rest of the query. Mismatched columns silently
drop data.

### 2. Add the opt-in mapping row to `Source_OptInTo`

DE key `A6DA18FC-0754-464B-8DF5-31D2ACD0B811`. Insert one row so the Content Block knows
which boolean to set:

- `Source` = the new identifier (exact match to step 1)
- `OptInField` = Salesforce API field name (e.g. `BizBash_White_Paper__c`)
- `OptInDateField` = the date field (e.g. `BizBash_White_Paper_Date__c`)

If you skip this, leads will still be created but **no opt-in boolean is set** (see the
"missing mappings" list in `../../docs/SOURCE_MAPPING.md`).

### 3. (Optional) Add the campaign mapping row to `Source_Campaign`

DE key `3951ACCF-6B86-4FBA-9710-E4C28C0BE7A0`. Insert `Source` + `CampaignId` if these leads
should join a Salesforce Campaign.

### 4. Test with a single record (do NOT wait for the 5am run)

1. Insert one test row into `Manual_Entries` with the new `Source` value and a test email you
   control. `Manual_Entries` is picked up by the same hourly logic, so it exercises the real
   path without touching `FormEntries_ToCRM`.
2. Trigger `CRM_IntegrationManual` (see `trigger-and-monitor-automation.md`).
3. Verify in Salesforce:

```sql
SELECT Id, Email, Lead_Details__c, LeadSource, Lead_Source__c, BizBash_White_Paper__c, CreatedDate
FROM Lead
WHERE Email = 'your-test@example.com'
ORDER BY CreatedDate DESC
```

Confirm: `Lead_Details__c` = new Source, `LeadSource`/`Lead_Source__c` = `MC BizBash`, the
opt-in boolean = true, and (if mapped) a CampaignMember exists.

4. Confirm the audit row landed in `CRMProcessed` for that email+source.

### 5. Update the repo docs

Add the new source to the table in `../../docs/SOURCE_MAPPING.md` (and remove it from the
"missing mappings" list if it was there). If this is a notable change, add a
`../../docs/CHANGELOG.md` entry.

## Common mistakes

- Editing the SQL but forgetting the `Source_OptInTo` row → leads with no opt-in flag.
- A typo making the SQL `Source` differ from the `Source_OptInTo` `Source` → lookup misses.
- Testing by editing `Form_Entries` directly instead of using `Manual_Entries`.
- Adding a `Source` string that doesn't match the existing naming convention, making reporting
  on `Lead_Details__c` harder.
