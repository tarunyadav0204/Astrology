import { apiService } from './apiService';

export const timezoneService = {
  /**
   * Detect timezone from coordinates using backend service
   * @param {number} latitude 
   * @param {number} longitude 
   * @returns {Promise<string>} UTC offset format (e.g., 'UTC+5:30')
   */
  async detectTimezone(latitude, longitude) {
    try {
      const response = await apiService.post('/detect-timezone', {
        latitude,
        longitude
      });
      return response.data.timezone;
    } catch (error) {
      console.error('Timezone detection failed:', error);
      return 'UTC+0'; // UTC fallback
    }
  },

  /**
   * Get timezone for location with coordinates
   * @param {Object} location - Location object with lat/lng
   * @returns {Promise<Object>} Location with detected timezone
   */
  async enrichLocationWithTimezone(location) {
    if (!location.latitude || !location.longitude) {
      return { ...location, timezone: 'UTC+0' };
    }

    const timezone = await this.detectTimezone(location.latitude, location.longitude);
    return { ...location, timezone };
  }
};