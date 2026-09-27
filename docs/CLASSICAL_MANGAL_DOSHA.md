# Classical Mangal Dosha contract

## Selected natal rule

AstroRoshni uses **Brihat Parashara Hora Shastra, Chapter 80,
verse 47** as the primary single-chart rule:

> *lagne vyaye sukhe vapi saptame castame kuje /  
> subha-drg-yoga-hine ca ...*

The calculation therefore requires both parts of the verse:

1. Mars is in House 1, 4, 7, 8, or 12 from the natal Lagna.
2. Mars has no benefic conjunction or Parashari graha aspect.

The verse occurs in the female-horoscope chapter. The API identifies the
formation for a supplied natal chart but does not reproduce the verse's
literal fatal prediction as a modern personal forecast.

For `subha`, planetary nature follows BPHS Chapter 3: Jupiter and Venus are
benefic; the waxing Moon is benefic; Mercury is benefic unless joined to a
malefic. Conjunction is same-sign conjunction. All benefics use the seventh
aspect and Jupiter additionally uses its fifth and ninth aspects.

Source text and morphology can be checked at
[BPHS 80.47](https://enjoylearningsanskrit.com/scriptures/parashara/chapter-80/verse-47/).
The Sanskrit Documents catalogue also links scans of BPHS chapters 71–80:
[BPHS source catalogue](https://sanskritdocuments.org/sanskrit/brihatparashara/).

## Separate second-house reading

The Agastya Samhita verse beginning *dhane vyaye ca patale...* names Houses
2, 12, 4, 7, and 8. AstroRoshni reports this as a separate `dhane` reading.
It does not merge it with BPHS 80.47 to manufacture a six-house rule.

The verse and its tradition are reproduced in the INFLIBNET course chapter
[Sixteen Samskaras, Part 2](https://ebooks.inflibnet.ac.in/icp05/chapter/sixteen-sa%E1%B9%83skaras-%E1%B9%A3o%E1%B8%8Dasasa%E1%B9%83skara%E1%B8%A5-part-2-vivaha%E1%B8%A5-and-antye%E1%B9%A3%E1%B9%ADi/).

## Moon and Venus references

Counting from the Moon and Venus is returned as supplementary traditional
evidence. It does not silently change the selected Lagna verdict. Each
reference point includes its own house and match result in the API.

## Partner comparison

The pair rule beginning *kuja doshavati deya kuja dosavate kila* is kept in a
separate two-chart function. It is cited to the Vivaha appendix of *Muhurta
Chintamani*, verse 50 in the referenced Hindi appendix edition. When both
charts contain the selected formation, the pair rule calls it balanced. It
does not erase either person's natal formation and supplies no numeric score.
The scanned edition is available at
[Muhurta Chintamani](https://archive.org/download/in.ernet.dli.2015.319680/2015.319680.Muhurt-Chintamani.pdf).

## Deliberate exclusions

The canonical result does not add:

- High, medium, low, or percentage severity;
- Navamsha-house counting;
- an age-28 expiry;
- own-sign, exaltation, or sign-specific cancellation lists;
- ritual prescriptions or gemstone advice;
- a numeric deduction from a marriage score.

Such claims require their own named, verified textual rule before they can be
added. Legacy API keys remain present during client migration, but are marked
as compatibility fields and do not control the classical verdict.

## API statuses

- `formed`: both BPHS 80.47 conditions are met.
- `protected`: Mars occupies a named house, but a benefic relationship means
  the complete verse condition is not met.
- `not_formed`: Mars is outside the five named Lagna houses.
- `unavailable`: Mars or Lagna data is missing.
