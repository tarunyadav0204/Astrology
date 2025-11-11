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
  
  // Use the endpoint helper for proper URL construction
  config.url = getEndpoint(config.url);
  
  console.log('API Request:', config.method?.toUpperCase(), config.url);
  
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
  login: (credentials) => api.post('/login', credentials),
  register: (userData) => api.post('/register', userData),
  logout: () => api.post('/logout'),
  sendResetCode: (data) => api.post('/send-reset-code', data),
  verifyResetCode: (data) => api.post('/verify-reset-code', data),
  resetPasswordWithToken: (data) => api.post('/reset-password-with-token', data),
};

export const chatAPI = {
  sendMessage: (message, language = 'english') => 
    api.post('/chat/ask', { question: message, language }),
  getChatHistory: (birthData) => api.post('/chat/history', birthData),
  clearHistory: () => api.delete('/chat/history'),
  createSession: () => api.post('/chat/session'),
  saveMessage: (sessionId, sender, content) => 
    api.post('/chat/message', { session_id: sessionId, sender, content }),
};

export const chartAPI = {
  calculateChart: (birthData) => api.post('/calculate-chart', birthData),
  calculateNavamsa: (birthData) => api.post('/calculate-navamsa', birthData),
  calculateTransit: (birthData) => api.post('/calculate-transit', birthData),
  calculateYogi: (birthData) => api.post('/calculate-yogi', birthData),
  getExistingCharts: (search = '') => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', '50');
    return api.get(`/birth-charts?${params}`);
  },
  updateChart: (id, data) => api.put(`/birth-charts/${id}`, data),
  deleteChart: (id) => api.delete(`/birth-charts/${id}`),
};

export default api;