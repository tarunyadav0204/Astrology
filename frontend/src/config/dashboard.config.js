export const DASHBOARD_CONFIG = {
  grid: {
    cols: { lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 },
    breakpoints: { lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 },
    rowHeight: 60,
    margin: [10, 10]
  },
  
  defaultLayout: [
    { i: 'lagna', x: 0, y: 0, w: 4, h: 8, minW: 3, minH: 6 },
    { i: 'navamsa', x: 4, y: 0, w: 4, h: 8, minW: 3, minH: 6 },
    { i: 'transit', x: 8, y: 0, w: 4, h: 8, minW: 3, minH: 6 },
    { i: 'dasha', x: 0, y: 8, w: 12, h: 6, minW: 6, minH: 4 }
  ],

  mobileLayout: [
    { i: 'lagna', x: 0, y: 0, w: 4, h: 8 },
    { i: 'navamsa', x: 0, y: 8, w: 4, h: 8 },
    { i: 'transit', x: 0, y: 16, w: 4, h: 8 },
    { i: 'dasha', x: 0, y: 24, w: 4, h: 6 }
  ],

  charts: {
    lagna: { title: 'Lagna Chart', type: 'birth' },
    navamsa: { title: 'Navamsa Chart', type: 'divisional', division: 9 },
    transit: { title: 'Transit Chart', type: 'transit' }
  }
};

export const CHART_CONFIG = {
  signs: ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'],
  planets: ['Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ra', 'Ke', 'Gu', 'Mn'],
  planetNames: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi'],
  
  styles: {
    north: 'North Indian',
    south: 'South Indian'
  },

  colors: {
    background: '#ffffff',
    border: '#333333',
    text: '#000000',
    planet: '#0066cc',
    house: '#f0f0f0'
  }
};

export const DASHA_CONFIG = {
  systems: ['maha', 'antar', 'pratyantar', 'sookshma', 'prana'],
  labels: ['Maha Dasha', 'Antar Dasha', 'Pratyantar Dasha', 'Sookshma Dasha', 'Prana Dasha'],
  
  periods: {
    'Sun': 6, 'Moon': 10, 'Mars': 7, 'Rahu': 18, 'Jupiter': 16,
    'Saturn': 19, 'Mercury': 17, 'Ketu': 7, 'Venus': 20
  }
};