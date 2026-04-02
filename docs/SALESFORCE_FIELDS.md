# Salesforce Lead Fields

## Fields Set by CRM_Integration

| Field API Name | Type | Value | Notes |
|---|---|---|---|
| `FirstName` | Standard | From form submission | |
| `LastName` | Standard | From form submission | |
| `Email` | Standard | From form submission | Primary matching key |
| `Company` | Standard | From form submission | |
| `Title` | Standard | From form submission (JobTitle) | |
| `Phone` | Standard | From form submission | |
| `Lead_Source__c` | Custom (Text) | `"MC BizBash"` (hardcoded) | Legacy field — always the same value |
| `LeadSource` | Standard (Picklist) | `"MC BizBash"` (hardcoded) | Added April 2, 2026 — was previously null |
| `Lead_Details__c` | Custom (Text) | `@Source` variable (dynamic) | Added April 2, 2026 — granular source identifier |
| `[OptInField]` | Custom (Boolean) | `true` | Dynamic — field name comes from Source_OptInTo lookup |

## Key Fields for Querying Integration Leads

```sql
-- Find all leads created by the integration
SELECT Id, Email, Lead_Details__c, LeadSource, Lead_Source__c, CreatedDate
FROM Lead
WHERE CreatedById = '0054X00000Dk173QAB'  -- MC Connect user

-- Find leads missing source attribution (should be zero going forward)
SELECT Id, Email, CreatedDate
FROM Lead
WHERE CreatedById = '0054X00000Dk173QAB'
AND Lead_Details__c = null

-- Source distribution
SELECT Lead_Details__c, COUNT(Id)
FROM Lead
WHERE CreatedById = '0054X00000Dk173QAB' AND Lead_Details__c != null
GROUP BY Lead_Details__c ORDER BY COUNT(Id) DESC
```

## LeadSource vs Lead_Source__c vs Lead_Details__c

- **`LeadSource`** (standard picklist): High-level channel — always `"MC BizBash"` for this integration
- **`Lead_Source__c`** (custom text): Legacy field — also always `"MC BizBash"`, predates the standard field usage
- **`Lead_Details__c`** (custom text): **Granular source** — the specific form/campaign/content (e.g., `"EventTechNewsletter_Form"`, `"Convene_Syndication_March2026"`)
