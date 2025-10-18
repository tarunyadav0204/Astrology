import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { reset } from './navigationService';

// Configure base URL - update this to match your backend
const API_BASE_URL = 'https://astroclick.net/api'; // GCP backend URL with HTTPS and /api prefix

class ApiService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Add auth token to requests
    this.api.interceptors.request.use(async (config) => {
      const token = await AsyncStorage.getItem('authToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
    
    // Handle 401 responses
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          await AsyncStorage.removeItem('authToken');
          await AsyncStorage.removeItem('userData');
          reset('Landing');
        }
        return Promise.reject(error);
      }
    );
  }

  async login(credentials) {
    try {
      console.log('Attempting login with:', { phone: credentials.phone });
      const response = await this.api.post('/login', credentials);
      console.log('Login successful:', response.data);
      return response.data;
    } catch (error) {
      console.error('Login error details:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
      });
      
      if (error.response?.status === 401) {
        throw new Error('Invalid phone number or password');
      }
      
      throw new Error(error.response?.data?.detail || error.response?.data?.message || 'Login failed');
    }
  }

  async register(userData) {
    try {
      const response = await this.api.post('/register', userData);
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      throw new Error(error.response?.data?.message || 'Registration failed');
    }
  }

  async calculateChart(birthData, userPhone = null) {
    try {
      let nodeType = 'mean';
      if (userPhone) {
        const settings = await this.getUserSettings(userPhone);
        nodeType = settings.node_type || 'mean';
      }
      
      const response = await this.api.post(`/calculate-chart?node_type=${nodeType}`, {
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'UTC+5:30',
      });
      return response.data;
    } catch (error) {
      console.error('Error calculating chart:', error);
      throw new Error('Failed to calculate chart');
    }
  }

  async calculateYogi(birthData) {
    try {
      const response = await this.api.post('/calculate-yogi', {
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'UTC',
      });
      return response.data;
    } catch (error) {
      console.error('Error calculating yogi:', error);
      throw new Error('Failed to calculate yogi');
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
      const response = await this.api.post('/calculate-dasha', {
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

  async calculateSubDashas(requestData) {
    try {
      const response = await this.api.post('/calculate-sub-dashas', requestData);
      return response.data;
    } catch (error) {
      console.error('Error calculating sub-dashas:', error);
      throw new Error('Failed to calculate sub-dashas');
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

  async getExistingCharts(search = '', limit = 50) {
    try {
      const response = await this.api.get(`/birth-charts?search=${encodeURIComponent(search)}&limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching charts:', error);
      throw new Error('Failed to fetch existing charts');
    }
  }

  async getUserSettings(phone) {
    try {
      const response = await this.api.get(`/user-settings/settings/${phone}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching user settings:', error);
      return {
        node_type: 'mean',
        default_chart_style: 'north'
      };
    }
  }

  async updateUserSettings(phone, settings) {
    try {
      const response = await this.api.put(`/user-settings/settings/${phone}`, settings);
      return response.data;
    } catch (error) {
      console.error('Error updating user settings:', error);
      throw new Error('Failed to update user settings');
    }
  }



  async getPlanetNakshatraInterpretation(planet, nakshatra, house) {
    try {
      const response = await this.api.get(`/interpretations/planet-nakshatra?planet=${planet}&nakshatra=${nakshatra}&house=${house}`);
      return response.data.interpretation;
    } catch (error) {
      console.error('Error fetching interpretation:', error);
      return null;
    }
  }
  
  async analyzeHouses(birthData) {
    try {
      const response = await this.api.post('/analyze-houses', {
        name: birthData.name,
        date: birthData.date,
        time: birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'UTC+5:30',
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing houses:', error);
      throw new Error('Failed to analyze houses');
    }
  }
  
  async analyzeSingleHouse(birthData, houseNumber) {
    try {
      const response = await this.api.post('/analyze-single-house', {
        birth_data: {
          name: birthData.name,
          date: birthData.date,
          time: birthData.time,
          latitude: parseFloat(birthData.latitude),
          longitude: parseFloat(birthData.longitude),
          timezone: birthData.timezone || 'UTC+5:30',
        },
        house_number: houseNumber
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing single house:', error);
      throw new Error(`Failed to analyze house ${houseNumber}`);
    }
  }

  async calculateAshtakavarga(data) {
    try {
      const response = await this.api.post('/calculate-ashtakavarga', data);
      return response.data;
    } catch (error) {
      console.error('Error calculating Ashtakavarga:', error);
      throw new Error('Failed to calculate Ashtakavarga');
    }
  }
  
  async getNakshatrasPublic() {
    try {
      const response = await this.api.get('/nakshatras-public');
      return response.data;
    } catch (error) {
      console.error('Error fetching nakshatras:', error);
      throw new Error('Failed to fetch nakshatra details');
    }
  }

  async sendResetCode(data) {
    try {
      const response = await this.api.post('/send-reset-code', data);
      return response.data;
    } catch (error) {
      console.error('Error sending reset code:', error);
      throw new Error(error.response?.data?.detail || 'Failed to send reset code');
    }
  }

  async verifyResetCode(data) {
    try {
      const response = await this.api.post('/verify-reset-code', data);
      return response.data;
    } catch (error) {
      console.error('Error verifying reset code:', error);
      throw new Error(error.response?.data?.detail || 'Invalid or expired code');
    }
  }

  async resetPasswordWithToken(data) {
    try {
      const response = await this.api.post('/reset-password-with-token', data);
      return response.data;
    } catch (error) {
      console.error('Error resetting password:', error);
      throw new Error(error.response?.data?.detail || 'Password reset failed');
    }
  }
}

export const apiService = new ApiService();