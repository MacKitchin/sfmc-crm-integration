# Data Extensions

## Core DEs

### Form_Entries
- **Purpose:** Staging DE for consolidated form submissions
- **Populated by:** `FormEntries_ToCRM` automation (daily 5am ET)
- **Consumed by:** `CRM_Integration` automation (hourly)
- **Columns:** EmailAddress, FirstName, LastName, JobTitle, Company, Phone, Address, City, State, Country, Source

### Manual_Entries
- **Purpose:** Manual lead entry point (bypasses FormEntries_ToCRM)
- **Use case:** Ad-hoc leads, testing, one-off imports
- **Columns:** Same schema as Form_Entries
- **Note:** Records here are picked up by CRM_Integration's SQL step alongside Form_Entries

### CRMProcessed
- **DE Key:** `CRMProcessed`
- **Record Count:** ~220,000+ (append-only)
- **Purpose:** Audit trail and deduplication key. Every record processed by CRM_Integration gets logged here.
- **Columns:** EmailAddress, FirstName, LastName, JobTitle, Company, Phone, Address, City, State, Country, Source, DateAdded, Action (New/Update), CRMID (Salesforce Lead/Contact ID), CRMType (Lead/Contact), CampaignMemID, CampaignMemAction
- **Key behavior:** The CRM_Integration SQL step anti-joins against this DE to prevent reprocessing

## Mapping DEs

### Source_OptInTo
- **DE Key:** `A6DA18FC-0754-464B-8DF5-31D2ACD0B811`
- **Record Count:** 251
- **Purpose:** Maps each `Source` value to the corresponding BizBash opt-in boolean field on the Lead object
- **Columns:** Source, OptInField (Salesforce API field name), OptInDateField
- **Example rows:**
  - `EventTechNewsletter_Form` → `BizBash_Universe__c` + `BizBash_Universe_Change_Date__c`
  - `EventTechNewsletter_Form` → `BizBash_Event_Technology_Newsletter__c` + `BizBash_Event_Tech_News_Change_Date__c`
  - `Convene_Syndication_March2026` → `BizBash_White_Paper__c` + `BizBash_White_Paper_Date__c`
- **Missing mappings (~13 sources):** WP_Eventcombo_Oct2023, 2024_BBSports_EBook, BBSports_Newsletter, MediaKitDownloads_2025, Cvent_Whitepaper_May2025, and others. These sources will create Leads but won't set an opt-in boolean.

### Source_Campaign
- **DE Key:** `3951ACCF-6B86-4FBA-9710-E4C28C0BE7A0`
- **Purpose:** Maps each `Source` value to a Salesforce Campaign name for Campaign Member creation
- **Columns:** Source, CampaignName

## Querying DEs via API

**REST API (paginated):**
```
GET {base}/data/v1/customobjectdata/key/{DE_KEY}/rowset?$pageSize=2500&$page=1
Authorization: Bearer {token}
```

**SOAP API (filtered retrieve):**
Use `RetrieveRequest` with `DataExtensionObject` ObjectType and `Property` filters.
