import axios from 'axios';

// Configure base URL - update this to match your backend
const API_BASE_URL = 'http://localhost:8000'; // Change to your backend URL

class ApiService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async calculateChart(birthData) {
    try {
      const response = await this.api.post('/calculate-chart', {
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'UTC',
      });
      return response.data;
    } catch (error) {
      console.error('Error calculating chart:', error);
      throw new Error('Failed to calculate birth chart');
    }
  }

  async calculateNavamsa(birthData) {
    try {
      const response = await this.api.post('/calculate-navamsa', {
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'UTC',
      });
      return response.data;
    } catch (error) {
      console.error('Error calculating navamsa:', error);
      throw new Error('Failed to calculate navamsa chart');
    }
  }

  async calculateDivisional(birthData, division) {
    try {
      const response = await this.api.post('/calculate-divisional', {
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'UTC',
        division: division,
      });
      return response.data;
    } catch (error) {
      console.error('Error calculating divisional chart:', error);
      throw new Error(`Failed to calculate D${division} chart`);
    }
  }

  async calculateDashas(birthData) {
    try {
      const response = await this.api.post('/calculate-dashas', {
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'UTC',
      });
      return response.data;
    } catch (error) {
      console.error('Error calculating dashas:', error);
      throw new Error('Failed to calculate dasha periods');
    }
  }

  async calculateTransits(birthData, transitDate) {
    try {
      const response = await this.api.post('/calculate-transits', {
        birth_data: {
          name: birthData.name,
          date: birthData.date,
          time: birthData.time,
          latitude: parseFloat(birthData.latitude),
          longitude: parseFloat(birthData.longitude),
          timezone: birthData.timezone || 'UTC',
        },
        transit_date: transitDate,
      });
      return response.data;
    } catch (error) {
      console.error('Error calculating transits:', error);
      throw new Error('Failed to calculate transits');
    }
  }

  async searchPlaces(query) {
    try {
      const response = await this.api.get(`/search-places?q=${encodeURIComponent(query)}`);
      return response.data.results || [];
    } catch (error) {
      console.error('Error searching places:', error);
      throw new Error('Failed to search places');
    }
  }

  async saveChart(birthData) {
    try {
      const response = await this.api.post('/save-chart', birthData);
      return response.data;
    } catch (error) {
      console.error('Error saving chart:', error);
      throw new Error('Failed to save chart');
    }
  }

  async getExistingCharts(search = '') {
    try {
      const response = await this.api.get(`/existing-charts?search=${encodeURIComponent(search)}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching charts:', error);
      throw new Error('Failed to fetch existing charts');
    }
  }
}

export const apiService = new ApiService();