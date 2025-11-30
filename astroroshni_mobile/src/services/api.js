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
  
  return config;
});

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
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
  sendMessage: (birthData, message, language = 'english') => 
    api.post(getEndpoint('/chat/ask'), { ...birthData, question: message, language, response_style: 'detailed' }),
  getChatHistory: (birthData) => api.post(getEndpoint('/chat/history'), birthData),
  clearHistory: () => api.delete(getEndpoint('/chat/history')),
  createSession: () => api.post(getEndpoint('/chat/session')),
  saveMessage: (sessionId, sender, content) => 
    api.post(getEndpoint('/chat/message'), { session_id: sessionId, sender, content }),
};

export const chartAPI = {
  calculateChart: (birthData) => api.post(getEndpoint('/calculate-chart'), birthData),
  calculateChartOnly: (birthData) => api.post(getEndpoint('/calculate-chart-only'), birthData),
  calculateDivisionalChart: (birthData, division = 9) => 
    api.post(getEndpoint('/calculate-divisional-chart'), { birth_data: birthData, division }),
  calculateTransits: (birthData, transitDate = new Date().toISOString().split('T')[0]) => 
    api.post(getEndpoint('/calculate-transits'), { birth_data: birthData, transit_date: transitDate }),
  calculateYogi: (birthData) => api.post(getEndpoint('/calculate-yogi'), birthData),
  calculateCascadingDashas: (birthData, targetDate) => 
    api.post(getEndpoint('/calculate-cascading-dashas'), { birth_data: birthData, target_date: targetDate }),
  calculateDasha: (birthData) => api.post(getEndpoint('/calculate-dasha'), birthData),


  getExistingCharts: (search = '') => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', '50');
    return api.get(`${getEndpoint('/birth-charts')}?${params}`);
  },
  updateChart: (id, data) => api.put(`${getEndpoint('/birth-charts')}/${id}`, data),
  deleteChart: (id) => api.delete(`${getEndpoint('/birth-charts')}/${id}`),
};

export const creditAPI = {
  getBalance: () => api.get(getEndpoint('/credits/balance')),
  getHistory: () => api.get(getEndpoint('/credits/history')),
  redeemPromoCode: (code) => api.post(getEndpoint('/credits/redeem'), { code }),
  spendCredits: (amount, feature, description) => 
    api.post(getEndpoint('/credits/spend'), { amount, feature, description }),
};

export default api;