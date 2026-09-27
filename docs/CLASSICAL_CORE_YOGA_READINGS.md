# Classical core-yoga rule ledger

This ledger records the exact textual reading used by
'backend/calculators/classical_core_yogas.py'. It is part of the calculation
contract. A later translation or recension must be added as a named variant;
it must not silently change or merge the selected rule.

## Planet nature policy

- **Source:** BPHS 3.11.
- **Rule:** Sun, Mars, Saturn, waning Moon, Rahu and Ketu are natural
  malefics. Jupiter, Venus and waxing Moon are benefics. Mercury becomes
  malefic when joined to a malefic.
- **Domain:** The nodes are included when a rule generally says
  'papa/asubha'. They remain excluded when the yoga expressly works with the
  seven visible planets, as in the Nabhasa scheme.

## Kendra–Trikona Raja Yoga

- **Source:** BPHS 34.11–15.
- **Implemented:** exchange, conjunction, or mutual full aspect between
  Kendra and Trikona lords; and the separate single-planet Yogakaraka
  condition when one planet owns a distinct Kendra and Trikona and occupies a
  Kendra or Trikona.
- **Exclusion:** a paired relationship is rejected when both participating
  lords also own difficult houses, following 34.15.
- **Evidence:** every result returns the relationship type, complete
  lordships, and the exclusion evaluation.

## Dhana combinations

- **Source:** BPHS 41.2–17.
- **Implemented:** the fourteen enumerated configurations in 41.2–15. All
  planets named in a plural conjunction/aspect clause are required.
- **Timing note:** 41.16 is returned separately as a delivery rule; it is not
  used to manufacture an additional natal yoga.
- **Qualification:** 41.17 directs judgment by planet nature and strength.
  The calculator therefore does not invent a High/Medium/Low grade.

## Dharma–Karma

- **Source:** Phaladeepika 6.37, read with its house definition in 1.17.
- **Implemented:** the distinct lords of Houses 9 and 10 must be conjoined in
  a 'mahita-bhava'.
- **Recorded reading:** 'mahita-bhava' is rendered as an auspicious/good
  house. Phaladeepika 1.17 calls Houses 6, 8 and 12 difficult and the others
  good, so those three houses are excluded.
- **Boundary:** when one planet owns both Houses 9 and 10, it is evaluated
  under BPHS 34.13's single-planet Yogakaraka rule. It is not relabelled as the
  two-lord conjunction in Phaladeepika 6.37.
- **Compatibility:** the public name remains 'Dharma-Karma Yoga'; the
  structured result also gives the closer textual name, “Raja Yoga of the
  conjoined 9th and 10th lords.”

## Harsha, Sarala and Vimala

- **Source:** Phaladeepika 6.57 with results in 6.63, 6.65 and 6.69.
- **Implemented branches:** the relevant lord is in a difficult house **or**
  it is joined/aspected by a classical malefic.
- **Evidence:** every result identifies which branch or branches formed it,
  the relevant lordship, and the joining/aspecting malefics.
- **Naming:** the calculator returns the three names used by the result
  verses. It does not add an unsourced strength score.

## Kemadruma

- **Selected source:** BPHS 37.11–12.
- **Implemented:** no qualifying planet other than the Sun in the 2nd or 12th
  from the Moon, followed by the BPHS Lagna-Kendra cancellation check. The
  cancellation check reads “planet other than Moon” literally and therefore
  includes the Sun and nodes.
- **Variant:** Phaladeepika 6.5's Kendra-from-Moon reading is calculated and
  returned under 'variant_readings'; it is not silently merged into the BPHS
  result.

## Gaja Kesari

- **Selected source:** BPHS 36.3–4.
- **Implemented:** Jupiter must be in a Kendra from Lagna or Moon, receive
  conjunction/aspect from another contextual natural benefic, and be free
  from debilitation, combustion and enemy-sign placement.
- **Boundary:** the common Moon–Jupiter Kendra shortcut alone is not accepted.

## Amala, Adhi, Dala and solar yogas

- **Sources:** BPHS 35.1–17, 36.5–6, 37.5–13 and 38.1–4.
- **Nature:** waxing/waning Moon and Mercury's company are evaluated through
  BPHS 3.11. Amala's exclusive occupancy check includes nodes as malefic
  occupants. Nabhasa Dala remains inside the seven-visible-planet scheme.
- **Solar yogas:** the Moon is excluded from Vesi, Vasi and Ubhayachari, and
  the benefic/malefic/mixed composition is returned without a strength score.

## Other implemented families

- Pancha Mahapurusha: Phaladeepika 6.1.
- Saraswati: Phaladeepika 6.26–27.
- Parivartana's Dainya, Khala and Maha partition: Phaladeepika 6.32.
- All 32 Nabhasa names and their precedence: BPHS 35.1–17.

## Change rule

A yoga is considered text-certified only when it has:

1. a named work and verse,
2. an executable condition with structured evidence,
3. an explicit policy for textual variants and ambiguous terms,
4. a false-positive regression test, and
5. no product-created probability or strength label presented as classical.
