import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL, getEndpoint } from '../utils/constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  console.log('API Request:', config.method?.toUpperCase(), config.url);
  console.log('Full URL:', config.baseURL + config.url);
  
  return config;
});

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.log('API Error:', error.response?.status, error.response?.data);
    
    if (error.response?.status === 401) {
      // Clear invalid token
      AsyncStorage.removeItem('authToken');
    }
    
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (credentials) => api.post(getEndpoint('/login'), credentials),
  register: (userData) => api.post(getEndpoint('/register'), userData),
  logout: () => api.post(getEndpoint('/logout')),
  sendRegistrationOtp: (data) => api.post(getEndpoint('/send-registration-otp'), data),
  sendResetCode: (data) => api.post(getEndpoint('/send-reset-code'), data),
  verifyResetCode: (data) => api.post(getEndpoint('/verify-reset-code'), data),
  resetPasswordWithToken: (data) => api.post(getEndpoint('/reset-password-with-token'), data),
};

export const chatAPI = {
  sendMessage: (message, language = 'english') => 
    api.post(getEndpoint('/chat/ask'), { question: message, language }),
  getChatHistory: (birthData) => api.post(getEndpoint('/chat/history'), birthData),
  clearHistory: () => api.delete(getEndpoint('/chat/history')),
  createSession: () => api.post(getEndpoint('/chat/session')),
  saveMessage: (sessionId, sender, content) => 
    api.post(getEndpoint('/chat/message'), { session_id: sessionId, sender, content }),
};

export const chartAPI = {
  calculateChart: (birthData) => api.post(getEndpoint('/calculate-chart'), birthData),
  calculateDivisionalChart: (birthData, division = 9) => 
    api.post(getEndpoint('/calculate-divisional-chart'), { birth_data: birthData, division }),
  calculateTransits: (birthData, transitDate = new Date().toISOString().split('T')[0]) => 
    api.post(getEndpoint('/calculate-transits'), { birth_data: birthData, transit_date: transitDate }),
  calculateYogi: (birthData) => api.post(getEndpoint('/calculate-yogi'), birthData),
  getExistingCharts: (search = '') => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', '50');
    return api.get(`${getEndpoint('/birth-charts')}?${params}`);
  },
  updateChart: (id, data) => api.put(`${getEndpoint('/birth-charts')}/${id}`, data),
  deleteChart: (id) => api.delete(`${getEndpoint('/birth-charts')}/${id}`),
};

export default api;