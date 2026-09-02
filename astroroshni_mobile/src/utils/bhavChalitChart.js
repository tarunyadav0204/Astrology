/** Build a renderable Bhava Chalit view from the calculator's D1 payload. */
export function buildBhavChalitChart(d1Chart) {
  const bhav = d1Chart?.bhav_chalit;
  const chalitPlanets = bhav?.planets;
  if (!d1Chart || !chalitPlanets || typeof chalitPlanets !== 'object') return null;

  const d1Planets = d1Chart.planets || {};
  const names = new Set([...Object.keys(d1Planets), ...Object.keys(chalitPlanets)]);
  const planets = {};

  names.forEach((name) => {
    const natal = d1Planets[name] && typeof d1Planets[name] === 'object' ? d1Planets[name] : {};
    const chalit = chalitPlanets[name] && typeof chalitPlanets[name] === 'object' ? chalitPlanets[name] : {};
    const house = Number(chalit.house ?? chalit.bhava ?? chalit.bhava_number ?? natal.house);
    planets[name] = {
      ...natal,
      ...chalit,
      ...(Number.isInteger(house) && house >= 1 && house <= 12 ? { house } : {}),
      _place_by_house: true,
    };
  });

  return {
    ...d1Chart,
    planets,
    ascendant: d1Chart.ascendant ?? bhav.ascendant,
    cusps: Array.isArray(bhav.cusps) ? bhav.cusps : [],
    _chart_label: 'Bhava Chalit',
    _reference: 'chalit',
    _place_by_house: true,
  };
}

export default buildBhavChalitChart;
