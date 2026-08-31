# Classical Bhava Bala validation

## Implemented worksheet

`backend/calculators/classical_bhava_bala.py` implements BPHS 27.26–31 as five
visible columns, matching the detailed Parashara's Light presentation:

1. From Lord — the Bhava lord's complete Shadbala in virupas.
2. Dig Bala — the sign-form directional calculation in BPHS 27.26–28.
3. Drishti — the net degree-based benefic/malefic aspect contribution.
4. Planets in — +60 for Mercury/Jupiter and -60 for Sun/Mars/Saturn in the Bhava.
5. Day-Night — +15 for the applicable Seershodaya, dual or Prishtodaya sign.

The total is the arithmetic sum of those columns. Sixty virupas equal one rupa.
The app's older weighted house score remains separately labelled and is not used
as classical Bhava Bala.

## Parashara's Light 7.0.3 cross-check

Public Sample Report 2:

- 30 August 1991, 05:23:00
- Pune, India; 18N45, 73E45
- Lahiri ayanamsha

The automated test locks the four Bhava-specific rows printed by the sample:

| Row | Houses I–XII |
| --- | --- |
| Dig Bala | 0, 20, 40, 30, 40, 20, 30, 10, 10, 60, 50, 50 |
| Drishti | -20, -10, 5, 67, 65, 19, 110, 69, 59, 31, -7, -20 |
| Planets in | 60, 0, -60, 0, 0, 0, -60, 0, 0, 0, 0, 0 |
| Day-Night | 15, 0, 0, 0, 0, 15, 15, 0, 0, 15, 15, 0 |

Drishti is allowed less than 1.5 virupas rounding tolerance. Dig, occupation and
day/night rows are exact. The From Lord row intentionally comes from this app's
selected Shadbala convention, so its already-disclosed Chesta/Kala differences
remain visible in the final Bhava total.

## Disclosed convention

BPHS specifies a twilight adjustment but does not define its boundary in these
verses. The engine uses one ghati (24 minutes) on either side of sunrise/sunset
as Sandhya and reports that convention in the API validation note.

Sources:

- BPHS chapter 27, verses 26–31: https://enjoylearningsanskrit.com/scriptures/parashara/chapter-27/
- Public Parashara's Light sample: https://www.astrograha.com/Content/AstrologyReports/North-Indian-Astrology-Report.pdf
