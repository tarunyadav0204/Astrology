import { apiService } from './apiService';

export const healthService = {
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