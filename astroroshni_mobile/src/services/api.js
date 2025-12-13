import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL, getEndpoint, API_TIMEOUT } from '../utils/constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT, // 5 minutes timeout
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'User-Agent': 'AstroRoshni-Mobile/1.0',
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
      AsyncStorage.removeItem('authToken');
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (credentials) => api.post(getEndpoint('/login'), credentials),
  register: (userData) => api.post(getEndpoint('/register'), userData),
  registerWithBirth: (userData) => api.post(getEndpoint('/register-with-birth'), userData),
  logout: () => api.post(getEndpoint('/logout')),
  sendRegistrationOtp: (data) => api.post(getEndpoint('/send-registration-otp'), data),
  sendResetCode: (data) => api.post(getEndpoint('/send-reset-code'), data),
  verifyResetCode: (data) => api.post(getEndpoint('/verify-reset-code'), data),
  resetPasswordWithToken: (data) => api.post(getEndpoint('/reset-password-with-token'), data),
  updateSelfBirthChart: (birthData, clearExisting = true) => {
    const params = clearExisting ? '?clear_existing=true' : '?clear_existing=false';
    return api.put(getEndpoint('/user/self-birth-chart') + params, birthData);
  },
  getSelfBirthChart: () => api.get(getEndpoint('/user/self-birth-chart')),

};

export const chatAPI = {
  sendMessage: (birthData, message, language = 'english') => 
    api.post(getEndpoint('/chat/ask'), { ...birthData, question: message, language, response_style: 'detailed' }),
  getChatHistory: (birthData) => api.post(getEndpoint('/chat/history'), birthData),
  clearHistory: () => api.delete(getEndpoint('/chat/history')),
  createSession: () => api.post(getEndpoint('/chat/session')),
  saveMessage: (sessionId, sender, content) => 
    api.post(getEndpoint('/chat/message'), { session_id: sessionId, sender, content }),
  getEventPeriods: (birthData) => api.post(getEndpoint('/chat/event-periods'), birthData),
  getMonthlyEvents: (birthData) => api.post(getEndpoint('/chat/monthly-events'), birthData),
  getMonthlyEventsStatus: (jobId) => api.get(getEndpoint(`/chat/monthly-events/status/${jobId}`)),
  getCachedMonthlyEvents: (birthData) => api.post(getEndpoint('/chat/monthly-events/cached'), birthData),
  deductCredits: (amount) => api.post(getEndpoint('/credits/spend'), { 
    amount, 
    feature: 'event_timeline', 
    description: 'Cosmic Timeline Analysis' 
  }),
};

export const wealthAPI = {
  getWealthInsights: (birthData, language = 'english') => {
    const requestData = {
      ...birthData,
      language,
      response_style: 'detailed'
    };
    return api.post(getEndpoint('/wealth/ai-insights'), requestData);
  },
};

export const healthAPI = {
  getHealthInsights: (birthData, language = 'english') => {
    const requestData = {
      ...birthData,
      language,
      response_style: 'detailed'
    };
    return api.post(getEndpoint('/health/ai-insights'), requestData);
  },
};

export const chartAPI = {
  calculateChart: (birthData) => api.post(getEndpoint('/calculate-chart'), birthData),
  calculateChartOnly: (birthData) => api.post(getEndpoint('/calculate-chart-only'), birthData),
  calculateAllCharts: (birthData) => api.post(getEndpoint('/calculate-all-charts'), birthData),
  calculateDivisionalChart: (birthData, division = 9) => 
    api.post(getEndpoint('/calculate-divisional-chart'), { birth_data: birthData, division }),
  calculateTransits: (birthData, transitDate = new Date().toISOString().split('T')[0]) => 
    api.post(getEndpoint('/calculate-transits'), { birth_data: birthData, transit_date: transitDate }),
  calculateYogi: (birthData) => api.post(getEndpoint('/calculate-yogi'), birthData),
  calculateCascadingDashas: (birthData, targetDate) => 
    api.post(getEndpoint('/calculate-cascading-dashas'), { birth_data: birthData, target_date: targetDate }),
  calculateDasha: (birthData) => api.post(getEndpoint('/calculate-dasha'), birthData),
  calculateYoginiDasha: (birthData, years = 5) => 
    api.post(getEndpoint('/yogini-dasha'), { ...birthData, years }),


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
  redeemPromoCode: (code) => 
    api.post(getEndpoint('/credits/redeem'), { code: code.toString() }, {
      headers: { 'Content-Type': 'application/json' }
    }),
  spendCredits: (amount, feature, description) => 
    api.post(getEndpoint('/credits/spend'), { amount, feature, description }),
  getEventTimelineCost: () => api.get(getEndpoint('/credits/settings/event-timeline-cost')),
};

export const panchangAPI = {
  calculateSunriseSunset: (date, latitude, longitude) => 
    api.post(getEndpoint('/panchang/calculate-sunrise-sunset'), { date, latitude, longitude }),
  calculateMoonPhase: (date) => 
    api.post(getEndpoint('/panchang/calculate-moon-phase'), { date }),
  calculateRahuKaal: (date, latitude, longitude) => 
    api.post(getEndpoint('/panchang/calculate-rahu-kaal'), { date, latitude, longitude }),
  calculateInauspiciousTimes: (date, latitude, longitude) => 
    api.post(getEndpoint('/panchang/calculate-inauspicious-times'), { date, latitude, longitude }),
  calculateDailyPanchang: (date, latitude, longitude) => 
    api.get(getEndpoint(`/panchang/daily-detailed?date=${date}&latitude=${latitude}&longitude=${longitude}`)),
};

export const progenyAPI = {
  getProgenyInsights: (birthData, language = 'english') => {
    const requestData = {
      ...birthData,
      language,
      response_style: 'detailed'
    };
    return api.post(getEndpoint('/progeny/ai-insights'), requestData);
  },
};

export const careerAPI = {
  getCareerInsights: (birthData, language = 'english') => {
    const requestData = {
      ...birthData,
      language,
      response_style: 'detailed'
    };
    return api.post(getEndpoint('/career/ai-insights'), requestData);
  },
};

export const educationAPI = {
  getEducationInsights: (birthData, language = 'english') => {
    const requestData = {
      ...birthData,
      language,
      response_style: 'detailed'
    };
    return api.post(getEndpoint('/education/ai-insights'), requestData);
  },
};

export const marriageAPI = {
  getMarriageInsights: (birthData, language = 'english') => {
    const requestData = {
      ...birthData,
      language,
      response_style: 'detailed'
    };
    return api.post(getEndpoint('/marriage/ai-insights'), requestData);
  },
};

export const pricingAPI = {
  getAnalysisPricing: () => api.get(getEndpoint('/analysis-pricing')),
};

export default api;