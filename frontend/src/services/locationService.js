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
    // Simplified timezone detection - in production use a proper timezone API
    const longitude = parseFloat(lon);
    const offset = Math.round(longitude / 15);
    return `UTC${offset >= 0 ? '+' : ''}${offset}`;
  }
};