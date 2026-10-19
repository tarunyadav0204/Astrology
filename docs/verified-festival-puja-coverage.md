# Verified festival puja coverage — v1

Festival timing is a separate workflow from general purchase elections. All 54 existing catalog entries are selectable; this is not a claim that all 54 rituals have verified muhurats.

## Calculated ritual profiles

| Festival | Ritual | Period and additional rules | Source |
|---|---|---|---|
| Diwali | Household Lakshmi puja | pradosh taurus intersected with required tithi | [Rule description](https://www.drikpanchang.com/festivals/lakshmipuja/festivals-lakshmipuja-timings.html) |
| Dussehra/Vijayadashami | Shami / Aparajita puja | aparahna intersected with required tithi | [Rule description](https://www.drikpanchang.com/festivals/vijayadashami/vijayadashami-date-time.html) |
| Govardhan Puja | Govardhan puja | pratah intersected with required tithi | [Rule description](https://www.drikpanchang.com/festivals/govardhan-puja/govardhan-puja-date-time.html) |
| Ganesh Chaturthi | Ganesh sthapana and puja | madhyahna intersected with required tithi | [Rule description](https://www.drikpanchang.com/festivals/ganesh-chaturthi/ganesh-chaturthi-date-time.html) |
| Maha Shivratri | Nishita Shiva puja | nishita intersected with required tithi | [Rule description](https://www.drikpanchang.com/festivals/maha-shivaratri/maha-shivaratri-date-time.html) |
| Ram Navami | Rama Navami puja | madhyahna intersected with required tithi | [Rule description](https://www.drikpanchang.com/dashavatara/rama-navami/rama-navami-date-time.html) |
| Dhanteras | Dhanteras puja (not shopping) | pradosh taurus intersected with required tithi | [Rule description](https://www.drikpanchang.com/festivals/dhanteras/festivals-dhanteras-puja-timings.html) |
| Bhai Dooj | Bhai Dooj tika | aparahna intersected with required tithi | [Rule description](https://www.drikpanchang.com/festivals/bhai-dooj/bhai-dooj-date-time.html) |
| Vasant Panchami | Saraswati puja | purvahna intersected with required tithi | [Rule description](https://www.drikpanchang.com/festivals/vasant-panchami/vasant-panchami-puja-date-time.html) |

Madhyahna is the middle fifth of daylight; Aparahna is the fourth fifth. Pratah is the first fifth, Purvahna runs from sunrise to the middle of daylight. Pradosh uses the first fifth of the night. Nishita uses the eighth fifteenth of the night. Diwali/Dhanteras profiles require sidereal Taurus Lagna; other fixed-sign alternatives are not inferred.

[Solar convention](https://www.drikpanchang.com/panchang/sunrise/panchang-sunrise.html): apparent upper limb with standard refraction, sea-level horizon. Swiss Ephemeris under the shared chart lock, Lahiri sidereal signs, local IANA timezone/DST; no synthetic sunrise fallback. Tithi boundaries are bracketed at six-hour intervals and bisected to less than one second. Lagna intervals are bracketed by one-minute samples and bisected. Geographic horizon/weather/elevation effects are not modeled.

If the tithi overlaps the ritual period on two dates, the engine does not choose by largest overlap or sunrise alone. The implemented Dussehra special case requires a unique day with Dashami throughout Aparahna and Shravana present during it, supported by [Drik’s explanation](https://news.drikpanchang.com/2013/10/vijayadashami-on-october-13th-or-14th.html). Other two-date combinations return partial coverage, including Bhai Dooj in Delhi in 2026. Narrowing the search to one date cannot hide this ambiguity.

Dussehra Aparahna Shami/Aparajita puja is not the narrower Vijaya Muhurat and is not Bengali Durga Visarjan. Fasting, parana, shopping, immersion, Ghatasthapana and other distinct rituals are not silently substituted. An unrecognized explicit ritual/tradition receives only available lunar information.

Personalization adds a separate midpoint Tara/Chandra comparison using the selected natal chart. It does not move the festival, rank an entire interval as continuously favorable, or claim a complete kundli election. No dasha, strength, divisional or other natal suitability checks are implied.

## Remaining catalog audit

| Festival | Available result / missing rules |
|---|---|
| Holika Dahan | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Holi | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Sharad Navratri | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Krishna Janmashtami | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Hanuman Jayanti | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Karva Chauth | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Hariyali Teej | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Shukla Ekadashi | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Krishna Ekadashi | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Devutthana Ekadashi | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Utpanna Ekadashi | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Kansa Vadh | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Tulasi Vivah | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Dev Diwali | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Kalabhairav Jayanti | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Makar Sankranti | No verified date/window; solar, regional, nakshatra, multi-day or site-specific rules pending. |
| Baisakhi | No verified date/window; solar, regional, nakshatra, multi-day or site-specific rules pending. |
| Pitra Paksha | No verified date/window; solar, regional, nakshatra, multi-day or site-specific rules pending. |
| Gudi Padwa | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Ugadi | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Vishu | No verified date/window; solar, regional, nakshatra, multi-day or site-specific rules pending. |
| Pohela Boishakh | No verified date/window; solar, regional, nakshatra, multi-day or site-specific rules pending. |
| Rongali Bihu | No verified date/window; solar, regional, nakshatra, multi-day or site-specific rules pending. |
| Onam | No verified date/window; solar, regional, nakshatra, multi-day or site-specific rules pending. |
| Durga Puja | No verified date/window; solar, regional, nakshatra, multi-day or site-specific rules pending. |
| Guru Purnima | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Pradosh Vrat | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Sankashti Chaturthi | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Akshaya Tritiya | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Raksha Bandhan | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Nag Panchami | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Karthik Purnima | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Vat Savitri Vrat | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Ahoi Ashtami | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Sharad Purnima | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Naraka Chaturdashi | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Chaitra Navratri | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Ratha Saptami | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Buddha Purnima | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Radha Ashtami | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Anant Chaturdashi | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Hartalika Teej | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Sarva Pitru Amavasya | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Ganga Dussehra | Matching lunar tithi intervals only; observance-date priority and ritual rules pending. |
| Kumbh Mela | No verified date/window; solar, regional, nakshatra, multi-day or site-specific rules pending. |

## Integration and billing

Verified semantic intake recognizes festivals and Roman Hindi, requests explicit event city, and defaults an unspecified year from the trusted server clock for confirmation. Web/mobile use the same generated coverage catalog. Client catalog copies are checked against the backend registry in tests. Regenerate them with `backend/scripts/export_festival_puja_catalog.py` after changing coverage.

Clarification uses the existing uncharged path. A festival result containing only an incomplete-rule explanation and no ritual candidates is flagged internally as no charge: persistence neither spends credits nor consumes the free question. A completed search with no matches still follows the existing election billing policy. No production data or billing ledger was changed.

Published 2026 Delhi regression examples: Dussehra October 20 13:14–15:30; Diwali November 8 17:54–19:50; Ganesh Chaturthi September 14 11:02–13:31; Vasant Panchami January 23 07:13–12:33. Two-minute tolerances account for published minute rounding and geography. Further tests cover midnight, polar sunrise failure, scope, language, catalog parity and unsupported rites.

This change does not alter the legacy festival-calendar API or generic activity election policies. It is not deployed by this implementation task.

## Instant and Standard/Premium integration

All main chat tiers share election intake and deterministic evidence. Instant retains its configured model/provider and streams the final answer. Standard/Premium enter the parallel orchestrator's election-only branch before any school payload construction or branch planning. A ritual reviewer and, only when personalization is requested, a personal-check reviewer inspect the same calculation; the final merge receives the authoritative result. Full natal/transit context, Jaimini, Nadi, KP and the ordinary specialist branches are not constructed for this route. Each LLM call is included in the existing usage metadata; the selected tier is retained when submitting setup/refinement cards.

Web and mobile use a ritual dropdown generated from the backend registry. Aparajita Puja and Shami Puja are selectable separately. Unimplemented exact Vijaya Muhurat and Durga Visarjan are disabled and labelled unavailable. Known spelling/script aliases match the implemented rule without requiring the combined display label. Unknown saved rituals are retained explicitly rather than silently replaced. The Gurgaon 2026 Aparajita regression calculates October 20, 13:14:47–15:31:18 IST using coordinates 28.4595, 77.0266.

## Daytime Rahu Kaal overlay — festival-puja-v2

Every calculated festival candidate now includes the local daytime Rahu Kaal interval, its overlap with the ritual window, and the remaining portions outside Rahu Kaal. These are computed with the existing weekday-eighth table and the same sunrise/sunset convention as the ritual window. The broad ritual window remains unchanged: the overlay offers a conservative avoidance choice, not a universal replacement of festival-specific tradition. A fixed-time check states explicitly whether that instant lies in Rahu Kaal. No nighttime Rahu Kaal, ritual duration, or complete personal election is implied. An arbitrary midpoint must not be promoted to an optimal start time.

For Gurgaon on October 20, 2026, the main Shami/Aparajita window is approximately 13:14:47–15:31:18 IST; daytime Rahu Kaal is 14:57:10–16:22:29. The remaining portion is approximately 13:14:47–14:57:10, practically 13:15–14:57 when rounded inward to whole minutes. All chat tiers receive this same overlay.
