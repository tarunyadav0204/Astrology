import axios from 'axios';
import { APP_CONFIG } from '../config/app.config';

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? APP_CONFIG.api.prod 
  : APP_CONFIG.api.dev;

// Helper function to add /api prefix only for localhost
const getEndpoint = (path) => {
  const endpoint = API_BASE_URL.includes('localhost') ? `/api${path}` : path;
  console.log('API_BASE_URL:', API_BASE_URL, 'Path:', path, 'Final endpoint:', endpoint);
  return endpoint;
};

// Simple request caching to prevent duplicate calls
const requestCache = new Map();
const CACHE_DURATION = 5000; // 5 seconds

const getCacheKey = (url, data) => {
  return `${url}-${JSON.stringify(data)}`;
};

const cachedRequest = async (config) => {
  const cacheKey = getCacheKey(config.url, config.data);
  const cached = requestCache.get(cacheKey);
  
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.data;
  }
  
  const response = await apiClient(config);
  requestCache.set(cacheKey, {
    data: response,
    timestamp: Date.now()
  });
  
  return response;
};

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
    // Add headers to help with load balancer debugging
    config.headers['X-Requested-With'] = 'XMLHttpRequest';
    config.headers['Cache-Control'] = 'no-cache';
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
  // Auth APIs
  register: async (userData) => {
    const response = await apiClient.post(getEndpoint('/register'), userData);
    return response.data;
  },
  
  login: async (credentials) => {
    const response = await apiClient.post(getEndpoint('/login'), credentials);
    return response.data;
  },
  
  forgotPassword: async (phone) => {
    const response = await apiClient.post(getEndpoint('/forgot-password'), { phone });
    return response.data;
  },
  
  sendResetCode: async (phone) => {
    const response = await apiClient.post(getEndpoint('/send-reset-code'), { phone });
    return response.data;
  },
  
  verifyResetCode: async (phone, code) => {
    const response = await apiClient.post(getEndpoint('/verify-reset-code'), { phone, code });
    return response.data;
  },
  
  resetPasswordWithToken: async (token, newPassword) => {
    const response = await apiClient.post(getEndpoint('/reset-password-with-token'), { token, new_password: newPassword });
    return response.data;
  },
  
  calculateChart: async (birthData, nodeType = 'mean') => {
    const response = await apiClient.post(`${getEndpoint('/calculate-chart')}?node_type=${nodeType}`, birthData);
    return response.data;
  },
  
  calculateTransits: async (transitRequest) => {
    const response = await apiClient.post(getEndpoint('/calculate-transits'), transitRequest);
    return response.data;
  },
  
  getDasha: async (birthDate) => {
    const response = await apiClient.get(`${getEndpoint('/dasha')}/${birthDate}`);
    return response.data;
  },
  
  getExistingCharts: async (search = '', limit = 50) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', limit.toString());
    const response = await apiClient.get(`${getEndpoint('/birth-charts')}?${params}`);
    return response.data;
  },
  
  updateChart: async (chartId, birthData) => {
    const response = await apiClient.put(`${getEndpoint('/birth-charts')}/${chartId}`, birthData);
    return response.data;
  },
  
  deleteChart: async (chartId) => {
    const response = await apiClient.delete(`${getEndpoint('/birth-charts')}/${chartId}`);
    return response.data;
  },
  
  calculateYogi: async (birthData) => {
    const response = await apiClient.post(getEndpoint('/calculate-yogi'), birthData);
    return response.data;
  },
  
  calculatePanchang: async (birthData) => {
    const response = await apiClient.post(getEndpoint('/calculate-panchang'), birthData);
    return response.data;
  },
  
  calculateFriendship: async (birthData) => {
    const response = await apiClient.post(getEndpoint('/calculate-friendship'), birthData);
    return response.data;
  },
  
  calculateHouse7Events: async (birthData) => {
    const response = await apiClient.post(getEndpoint('/predict-house7-events'), birthData);
    return response.data;
  },
  
  predictYearEvents: async (data) => {
    const response = await apiClient.post(getEndpoint('/predict-year-events'), data);
    return response.data;
  },
  
  calculateDivisionalChart: async (birthData, division) => {
    const response = await apiClient.post(getEndpoint('/calculate-divisional-chart'), {
      birth_data: birthData,
      division: division
    });
    return response.data;
  },
  
  // Rule Engine APIs
  getRules: async () => {
    const response = await apiClient.get(getEndpoint('/rule-engine/rules'));
    return response.data;
  },
  
  createRule: async (rule) => {
    const response = await apiClient.post(getEndpoint('/rule-engine/rules'), rule);
    return response.data;
  },
  
  updateRule: async (ruleId, rule) => {
    const response = await apiClient.put(`${getEndpoint('/rule-engine/rules')}/${ruleId}`, rule);
    return response.data;
  },
  
  deleteRule: async (ruleId) => {
    const response = await apiClient.delete(`${getEndpoint('/rule-engine/rules')}/${ruleId}`);
    return response.data;
  },
  
  analyzeEvent: async (birthChart, eventDate, eventType) => {
    const response = await apiClient.post(getEndpoint('/rule-engine/analyze-event'), {
      birth_chart: birthChart,
      event_date: eventDate,
      event_type: eventType
    });
    return response.data;
  },
  
  getEventTypes: async () => {
    const response = await apiClient.get(getEndpoint('/rule-engine/event-types'));
    return response.data;
  },
  
  searchRules: async (query) => {
    const response = await apiClient.get(`${getEndpoint('/rule-engine/search')}?q=${encodeURIComponent(query)}`);
    return response.data;
  },
  
  getUserSettings: async (phone) => {
    const response = await apiClient.get(`${getEndpoint('/user-settings/settings')}/${phone}`);
    return response.data;
  },
  
  updateUserSettings: async (phone, settings) => {
    const response = await apiClient.put(`${getEndpoint('/user-settings/settings')}/${phone}`, settings);
    return response.data;
  },
  
  analyzeHouses: async (birthData) => {
    const response = await apiClient.post(getEndpoint('/analyze-houses'), birthData);
    return response.data;
  },
  
  analyzeSingleHouse: async (birthData, houseNumber) => {
    const response = await apiClient.post(getEndpoint('/analyze-single-house'), {
      birth_data: birthData,
      house_number: houseNumber
    });
    return response.data;
  },
  
  calculateDasha: async (birthData) => {
    const response = await cachedRequest({
      method: 'post',
      url: getEndpoint('/calculate-dasha'),
      data: birthData
    });
    return response.data;
  },
  
  calculateSubDashas: async (requestData) => {
    const response = await cachedRequest({
      method: 'post',
      url: getEndpoint('/calculate-sub-dashas'),
      data: requestData
    });
    return response.data;
  },
  
  getDailyPredictions: async (requestData) => {
    const response = await apiClient.post(getEndpoint('/daily-predictions'), requestData);
    return response.data;
  },
  
  // Daily Prediction Rules APIs
  getDailyPredictionRules: async () => {
    const response = await apiClient.get(getEndpoint('/daily-prediction-rules'));
    return response.data;
  },
  
  createDailyPredictionRule: async (rule) => {
    const response = await apiClient.post(getEndpoint('/daily-prediction-rules'), rule);
    return response.data;
  },
  
  updateDailyPredictionRule: async (ruleId, rule) => {
    const response = await apiClient.put(`${getEndpoint('/daily-prediction-rules')}/${ruleId}`, rule);
    return response.data;
  },
  
  deleteDailyPredictionRule: async (ruleId) => {
    const response = await apiClient.delete(`${getEndpoint('/daily-prediction-rules')}/${ruleId}`);
    return response.data;
  },
  
  resetDailyPredictionRules: async () => {
    const response = await apiClient.post(getEndpoint('/reset-prediction-rules'));
    return response.data;
  },
  
  getPlanetNakshatraInterpretation: async (planet, nakshatra, house) => {
    const response = await apiClient.get(`${getEndpoint('/interpretations/planet-nakshatra')}?planet=${planet}&nakshatra=${nakshatra}&house=${house}`);
    return response.data.interpretation;
  },
  
  // Nakshatra Management APIs
  getNakshatras: async () => {
    const response = await apiClient.get(getEndpoint('/nakshatras'));
    return response.data;
  },
  
  createNakshatra: async (nakshatraData) => {
    const response = await apiClient.post(getEndpoint('/nakshatras'), nakshatraData);
    return response.data;
  },
  
  updateNakshatra: async (nakshatraId, nakshatraData) => {
    const response = await apiClient.put(`${getEndpoint('/nakshatras')}/${nakshatraId}`, nakshatraData);
    return response.data;
  },
  
  deleteNakshatra: async (nakshatraId) => {
    const response = await apiClient.delete(`${getEndpoint('/nakshatras')}/${nakshatraId}`);
    return response.data;
  },
  
  getNakshatrasPublic: async () => {
    const response = await apiClient.get(getEndpoint('/nakshatras-public'));
    return response.data;
  },
  
  getMarriageAnalysis: async (requestData) => {
    const response = await apiClient.post(getEndpoint('/marriage-analysis'), requestData);
    return response.data;
  }
};