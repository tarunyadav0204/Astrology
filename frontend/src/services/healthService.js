import { apiService } from './apiService';

export const healthService = {
  async getBodyZones(birthDetails) {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/health/body-zones', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify({
        name: birthDetails?.name,
        date: birthDetails.date || '1990-01-01',
        time: birthDetails.time || '12:00',
        place: birthDetails.place || 'New Delhi',
        latitude: birthDetails.latitude || 28.6139,
        longitude: birthDetails.longitude || 77.2090,
        timezone: birthDetails.timezone,
        gender: birthDetails.gender,
      }),
    });
    if (!response.ok) {
      throw new Error(`Health body-zone request failed (${response.status})`);
    }
    const result = await response.json();
    return result.data;
  },

  async getOverallHealthAssessment(birthDetails) {
    try {
      const response = await apiService.post('/health/overall-assessment', birthDetails);
      return response.data;
    } catch (error) {
      console.error('Health analysis error:', error);
      throw error;
    }
  },

  async getPlanetaryHealthAnalysis(birthDetails) {
    try {
      const response = await apiService.post('/health/planetary-analysis', {
        birth_details: birthDetails
      });
      return response.data;
    } catch (error) {
      console.error('Planetary health analysis error:', error);
      throw error;
    }
  },

  async getHouseHealthAnalysis(birthDetails) {
    try {
      const response = await apiService.post('/health/house-analysis', {
        birth_details: birthDetails
      });
      return response.data;
    } catch (error) {
      console.error('House health analysis error:', error);
      throw error;
    }
  },

  async getHealthYogasAnalysis(birthDetails) {
    try {
      const response = await apiService.post('/health/yogas-analysis', {
        birth_details: birthDetails
      });
      return response.data;
    } catch (error) {
      console.error('Health yogas analysis error:', error);
      throw error;
    }
  },

  async getGandantaHealthAnalysis(birthDetails) {
    try {
      const response = await apiService.post('/health/gandanta-analysis', {
        birth_details: birthDetails
      });
      return response.data;
    } catch (error) {
      console.error('Gandanta health analysis error:', error);
      throw error;
    }
  }
};