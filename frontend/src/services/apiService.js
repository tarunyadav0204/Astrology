import axios from 'axios';
import { APP_CONFIG } from '../config/app.config';

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? APP_CONFIG.api.prod 
  : APP_CONFIG.api.dev;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: APP_CONFIG.api.timeout,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Request interceptor to add JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    console.log('API Request:', config.url, 'Token:', token ? 'Present' : 'Missing');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout. Please try again.');
    }
    if (error.response?.status >= 500) {
      throw new Error('Server error. Please try again later.');
    }
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.reload();
    }
    throw error;
  }
);

export const apiService = {
  calculateChart: async (birthData) => {
    const response = await apiClient.post('/calculate-chart', birthData);
    return response.data;
  },
  
  calculateTransits: async (transitRequest) => {
    const response = await apiClient.post('/calculate-transits', transitRequest);
    return response.data;
  },
  
  getDasha: async (birthDate) => {
    const response = await apiClient.get(`/dasha/${birthDate}`);
    return response.data;
  },
  
  getExistingCharts: async (search = '', limit = 50) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', limit.toString());
    const response = await apiClient.get(`/birth-charts?${params}`);
    return response.data;
  },
  
  updateChart: async (chartId, birthData) => {
    const response = await apiClient.put(`/birth-charts/${chartId}`, birthData);
    return response.data;
  },
  
  deleteChart: async (chartId) => {
    const response = await apiClient.delete(`/birth-charts/${chartId}`);
    return response.data;
  },
  
  calculateYogi: async (birthData) => {
    const response = await apiClient.post('/calculate-yogi', birthData);
    return response.data;
  },
  
  calculatePanchang: async (birthData) => {
    const response = await apiClient.post('/calculate-panchang', birthData);
    return response.data;
  },
  
  calculateFriendship: async (birthData) => {
    const response = await apiClient.post('/calculate-friendship', birthData);
    return response.data;
  },
  
  calculateHouse7Events: async (birthData) => {
    const response = await apiClient.post('/predict-house7-events', birthData);
    return response.data;
  },
  
  predictYearEvents: async (data) => {
    const response = await apiClient.post('/predict-year-events', data);
    return response.data;
  },
  
  calculateDivisionalChart: async (birthData, division) => {
    const response = await apiClient.post('/calculate-divisional-chart', {
      birth_data: birthData,
      division: division
    });
    return response.data;
  }
};