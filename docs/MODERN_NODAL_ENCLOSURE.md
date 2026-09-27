# Rahu–Ketu nodal enclosure (modern Kaal Sarp convention)

## Classification

AstroRoshni does not label Kaal Sarp as a classical rishi-authored dosha. A
named verse for it was not verified in the reviewed copies or catalogues of
*Brihat Parashara Hora Shastra*, *Brihat Jataka*, *Saravali*, *Phaladeepika*,
or *Jataka Parijata*. The calculator therefore identifies only the modern
astronomical convention and says so on screen.

This implementation does not attach predicted effects, severity grades,
remedies, cancellation rules, or the twelve serpent names. Those additions
need a separately selected and verified source before they may be used.

## Calculation

The canonical calculator is
`backend/calculators/nodal_enclosure_calculator.py`.

1. Read exact sidereal longitudes for Rahu, Ketu, Sun, Moon, Mars, Mercury,
   Jupiter, Venus, and Saturn.
2. Check the directed arc from Rahu to Ketu and the complementary directed arc
   from Ketu to Rahu.
3. A complete enclosure exists only when all seven visible planets lie on one
   closed nodal arc.
4. A strict enclosure requires every visible planet to lie inside the arc. A
   planet at the exact longitude of a node is returned as a boundary case and
   is never silently merged into the strict result.
5. If planets occur outside both possible halves, the result is not formed.
   The more populated half and its outside planets are returned as geometry,
   but AstroRoshni does not call this a partial Kaal Sarp configuration.
6. If any required longitude is missing, the result is unavailable. Missing
   planets are never skipped.

House and sign numbers are not used to decide enclosure because two planets in
the same sign can still lie on opposite sides of a nodal longitude.

## Compatibility

The legacy `major_doshas.kaal_sarp_dosha.present`, `type`, `cancellation`, and
`cancellation_reason` keys remain. Structured fields add status, direction,
the selected arc, contained/boundary/outside planets, both arcs checked, and
source classification. Existing clients can continue parsing the response,
while migrated clients can show the exact and qualified result.
