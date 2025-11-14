export const APP_CONFIG = {
  api: {
    dev: 'http://localhost:8001',
    prod: 'https://astroroshni.com',  // Production API base URL
    timeout: 30000,
    retries: 3
  },
  form: {
    dateFormat: 'YYYY-MM-DD',
    timeFormat: '12h',
    dateRange: {
      min: '1900-01-01',
      max: '2100-12-31'
    },
    validation: {
      nameMinLength: 2,
      nameMaxLength: 50,
      placeMinLength: 2
    }
  },
  ui: {
    breakpoints: {
      mobile: '768px',
      tablet: '1024px',
      desktop: '1200px'
    },
    toast: {
      duration: 4000,
      position: 'top-right'
    }
  },
  location: {
    geocodingService: 'nominatim',
    debounceMs: 300,
    minSearchLength: 3
  }
};