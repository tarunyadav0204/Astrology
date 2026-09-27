// Chart and Positions clients intentionally do not calculate astrological
// states. The backend chart contract is the single source of truth; this
// helper only extracts its canonical combustion flags for chart rendering.
export function combustSet(chartData) {
  const combust = new Set();
  Object.entries(chartData?.planets || {}).forEach(([planet, row]) => {
    const canonical = row?.combustion || chartData?.combustion?.planets?.[planet];
    if (canonical?.is_combust === true) combust.add(planet);
  });
  return combust;
}
