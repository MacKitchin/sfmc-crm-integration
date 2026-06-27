# Source Mapping Reference

## Known Source Values (31 active as of April 2026)

| Source | Volume | OptIn Field | Category |
|---|---|---|---|
| MeetingsNet2025 | 5,575 | Check Source_OptInTo | Newsletter syndication |
| EventTechNewsletter_Form | 1,278 | BizBash_Universe__c + BizBash_Event_Technology_Newsletter__c | Newsletter signup |
| CventApril_Registrants | 119 | Check Source_OptInTo | Webinar registrants |
| Czarnowski_WP_July2025 | 110 | Check Source_OptInTo | Whitepaper download |
| MagazineSubForm_BizbashBuzz | 102 | Check Source_OptInTo | Magazine subscription |
| Cvent_November20 | 86 | Check Source_OptInTo | Webinar registrants |
| eShow_OctoberWebinar_Registrants | 78 | Check Source_OptInTo | Webinar registrants |
| LS26_Formstack | 73 | Check Source_OptInTo | Event registration |
| CORTEvents_FebWebinar | 53 | Check Source_OptInTo | Webinar registrants |
| SanJose_WP_Dec2025 | 42 | Check Source_OptInTo | Whitepaper download |
| BizBash_Dolby_RSVPs | 26 | Check Source_OptInTo | Event RSVPs |
| MyrtleBeach_NovemberSurvey | 25 | Check Source_OptInTo | Survey respondents |
| Stova_WP_Aug2025 | 24 | Check Source_OptInTo | Whitepaper download |
| BBSports_Newsletter | 18 | **MISSING** | Newsletter signup |
| VisitDallasWebinar_Registrants | 17 | Check Source_OptInTo | Webinar registrants |
| 13EEA_Finalists | 11 | Check Source_OptInTo | Awards |
| SportsInnovationForum25_Registered | 9 | Check Source_OptInTo | Event registration |
| PalmSprings_JanuarySurvey | 8 | Check Source_OptInTo | Survey respondents |
| BizBash_Universe | 8 | Check Source_OptInTo | Platform |
| WP_BIzBashLeadershipSummit_May2025 | 7 | Check Source_OptInTo | Event registration |
| BizBash_Buzz_Newsletter | 6 | Check Source_OptInTo | Newsletter signup |
| Convene_Syndication_March2026 | 3 | BizBash_White_Paper__c | Content syndication |
| + 9 more small sources | <5 each | Various | Various |

## Adding a New Source

When a new form/content source is added:

1. **FormEntries_ToCRM SQL** — Add a new `SELECT ... UNION ALL` block for the new form DE, with the `Source` value hardcoded
2. **Source_OptInTo DE** — Add a row mapping the new `Source` value to the appropriate BizBash opt-in boolean field and date field
3. **Source_Campaign DE** — (Optional) Add a row mapping the new `Source` to a Salesforce Campaign name
4. **Test** — Insert a test record into `Manual_Entries` with the new Source value, trigger CRM_Integration, verify the Lead is created correctly

## Sources Missing OptIn Mappings (as of April 2026)

These sources exist in FormEntries_ToCRM but have no corresponding row in Source_OptInTo. Leads will be created but no opt-in boolean will be set:

- WP_Eventcombo_Oct2023
- 2024_BBSports_EBook
- BBSports_Newsletter
- MediaKitDownloads_2025
- Cvent_Whitepaper_May2025
- VisitDallasWebinar_Registrants
- 13EEA_Finalists
- 13EEA_AbandonedCart_Oct16
- 13EEA_AbandonedCart_Oct17
- SportsInnovationForum25_Registered
- SIF25_FinalAttendee
- SportsInnovation_SponsorInterest
- BBELS26_Registrants
