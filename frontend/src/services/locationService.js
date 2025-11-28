import { APP_CONFIG } from '../config/app.config';

const NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org';

export const locationService = {
  searchPlaces: async (query) => {
    if (query.length < APP_CONFIG.location.minSearchLength) {
      return [];
    }

    try {
      const response = await fetch(
        `${NOMINATIM_BASE_URL}/search?format=json&q=${encodeURIComponent(query)}&limit=5&addressdetails=1`,
        {
          headers: {
            'User-Agent': 'AstrologyApp/1.0'
          }
        }
      );
      
      if (!response.ok) {
        throw new Error('Location search failed');
      }
      
      const data = await response.json();
      
      return data.map(item => ({
        id: item.place_id,
        name: item.display_name,
        latitude: parseFloat(item.lat),
        longitude: parseFloat(item.lon),
        timezone: locationService.getTimezoneFromCoords(item.lat, item.lon)
      }));
    } catch (error) {
      console.error('Location search error:', error);
      throw new Error('Failed to search locations');
    }
  },

  getTimezoneFromCoords: (lat, lon) => {
    const latitude = parseFloat(lat);
    const longitude = parseFloat(lon);
    
    // India: Use IST (UTC+5:30) for Indian subcontinent
    if (latitude >= 6.0 && latitude <= 37.0 && longitude >= 68.0 && longitude <= 97.0) {
      return 'UTC+5:30';
    }
    
    // China: Use CST (UTC+8)
    if (latitude >= 18.0 && latitude <= 54.0 && longitude >= 73.0 && longitude <= 135.0) {
      return 'UTC+8';
    }
    
    // Nepal: Use NPT (UTC+5:45)
    if (latitude >= 26.0 && latitude <= 31.0 && longitude >= 80.0 && longitude <= 89.0) {
      return 'UTC+5:45';
    }
    
    // Myanmar: Use MMT (UTC+6:30)
    if (latitude >= 9.0 && latitude <= 29.0 && longitude >= 92.0 && longitude <= 102.0) {
      return 'UTC+6:30';
    }
    
    // Afghanistan: Use AFT (UTC+4:30)
    if (latitude >= 29.0 && latitude <= 39.0 && longitude >= 60.0 && longitude <= 75.0) {
      return 'UTC+4:30';
    }
    
    // Iran: Use IRST (UTC+3:30)
    if (latitude >= 25.0 && latitude <= 40.0 && longitude >= 44.0 && longitude <= 64.0) {
      return 'UTC+3:30';
    }
    
    // For other locations, use standard hour-based calculation
    const offset = Math.round(longitude / 15);
    return `UTC${offset >= 0 ? '+' : ''}${offset}`;
  }
};