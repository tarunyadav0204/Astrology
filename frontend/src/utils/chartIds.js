const DIVISION_TO_CHART_ID = {
  2: 'hora',
  3: 'drekkana',
  4: 'chaturthamsa',
  7: 'saptamsa',
  9: 'navamsa',
  10: 'dashamsa',
  12: 'dwadashamsa',
  16: 'shodasamsa',
  20: 'vimsamsa',
  24: 'chaturvimsamsa',
  27: 'saptavimshamsa',
  30: 'trimsamsa',
  40: 'khavedamsa',
  45: 'akshavedamsa',
  60: 'shashtyamsa',
};

export function resolveChartId(chartType, division) {
  if (!chartType || chartType === 'lagna') return 'lagna';
  if (chartType === 'navamsa') return 'navamsa';
  if (chartType === 'transit') return 'transit';
  if (chartType === 'divisional' && division) {
    return DIVISION_TO_CHART_ID[division] || 'lagna';
  }
  return chartType;
}
