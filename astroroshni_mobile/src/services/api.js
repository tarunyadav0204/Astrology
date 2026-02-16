import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL, getEndpoint, API_TIMEOUT } from '../utils/constants';
import { Alert } from 'react-native';

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

// Global error handler
let errorHandlerCallback = null;

export const setGlobalErrorHandler = (callback) => {
  errorHandlerCallback = callback;
};

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Network error (no internet or backend down)
    if (!error.response && error.message === 'Network Error') {
      if (errorHandlerCallback) {
        errorHandlerCallback({
          type: 'network',
          message: 'No internet connection. Please check your network and try again.'
        });
      }
      return Promise.reject(error);
    }

    // Backend timeout
    if (error.code === 'ECONNABORTED') {
      if (errorHandlerCallback) {
        errorHandlerCallback({
          type: 'timeout',
          message: 'Request timed out. Please try again.'
        });
      }
      return Promise.reject(error);
    }

    // Backend down (5xx errors)
    if (error.response?.status >= 500) {
      if (errorHandlerCallback) {
        errorHandlerCallback({
          type: 'server',
          message: 'Server is temporarily unavailable. Please try again later.'
        });
      }
      return Promise.reject(error);
    }

    // Unauthorized - clear token
    if (error.response?.status === 401) {
      await AsyncStorage.removeItem('authToken');
      if (errorHandlerCallback) {
        errorHandlerCallback({
          type: 'auth',
          message: 'Session expired. Please login again.'
        });
      }
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
  updateSelfBirthChart: (birthData, clearExisting = true, chartId = null) => {
    let params = clearExisting ? '?clear_existing=true' : '?clear_existing=false';
    if (chartId) params += `&chart_id=${chartId}`;
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
  getYogas: (birthData) => api.post(getEndpoint('/chat/ask'), { ...birthData, question: 'yogas', include_context: true }),
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
  calculateChart: (birthData) => {
    // console.log('[API] Calling calculateChart');
    const startTime = Date.now();
    return api.post(getEndpoint('/calculate-chart'), birthData)
      .then(response => {
        // console.log(`[API] calculateChart completed in ${Date.now() - startTime}ms`);
        return response;
      })
      .catch(error => {
        // console.error(`[API] calculateChart failed after ${Date.now() - startTime}ms:`, error);
        throw error;
      });
  },
  calculateChartOnly: (birthData) => {
    // console.log('[API] Calling calculateChartOnly');
    const startTime = Date.now();
    return api.post(getEndpoint('/calculate-chart-only'), birthData)
      .then(response => {
        // console.log(`[API] calculateChartOnly completed in ${Date.now() - startTime}ms`);
        return response;
      })
      .catch(error => {
        // console.error(`[API] calculateChartOnly failed after ${Date.now() - startTime}ms:`, error);
        throw error;
      });
  },
  calculateAllCharts: (birthData) => {
    // console.log('[API] Calling calculateAllCharts');
    const startTime = Date.now();
    return api.post(getEndpoint('/calculate-all-charts'), birthData)
      .then(response => {
        // console.log(`[API] calculateAllCharts completed in ${Date.now() - startTime}ms`);
        return response;
      })
      .catch(error => {
        // console.error(`[API] calculateAllCharts failed after ${Date.now() - startTime}ms:`, error);
        throw error;
      });
  },
  calculateDivisionalChart: (birthData, division = 9) => {
    // console.log(`[API] Calling calculateDivisionalChart for D${division}`);
    const startTime = Date.now();
    return api.post(getEndpoint('/calculate-divisional-chart'), { birth_data: birthData, division })
      .then(response => {
        // console.log(`[API] calculateDivisionalChart D${division} completed in ${Date.now() - startTime}ms`);
        return response;
      })
      .catch(error => {
        // console.error(`[API] calculateDivisionalChart D${division} failed after ${Date.now() - startTime}ms:`, error);
        throw error;
      });
  },
  calculateTransits: (birthData, transitDate = new Date().toISOString().split('T')[0]) => {
    // console.log(`[API] Calling calculateTransits for date ${transitDate}`);
    const startTime = Date.now();
    return api.post(getEndpoint('/calculate-transits'), { birth_data: birthData, transit_date: transitDate })
      .then(response => {
        // console.log(`[API] calculateTransits completed in ${Date.now() - startTime}ms`);
        return response;
      })
      .catch(error => {
        // console.error(`[API] calculateTransits failed after ${Date.now() - startTime}ms:`, error);
        throw error;
      });
  },
  calculateYogi: (birthData) => api.post(getEndpoint('/calculate-yogi'), birthData),
  calculateCascadingDashas: (birthData, targetDate) => {
    // console.log('\n' + '='.repeat(60));
    // console.log('🔍 MOBILE: Calling calculateCascadingDashas');
    // console.log('='.repeat(60));
    // console.log('Birth Data:', JSON.stringify(birthData, null, 2));
    // console.log('Target Date:', targetDate);
    // console.log('Endpoint:', getEndpoint('/calculate-cascading-dashas'));
    
    return api.post(getEndpoint('/calculate-cascading-dashas'), { birth_data: birthData, target_date: targetDate })
      .then(response => {
        // console.log('\n✅ MOBILE: Dasha Response Received');
        // console.log('Response keys:', Object.keys(response.data));
        // console.log('Maha dashas count:', response.data.maha_dashas?.length || 0);
        // console.log('Antar dashas count:', response.data.antar_dashas?.length || 0);
        if (response.data.maha_dashas?.length > 0) {
          // console.log('First maha:', response.data.maha_dashas[0]);
        }
        return response;
      })
      .catch(error => {
        console.error('❌ MOBILE: Dasha API Error:', error.message);
        console.error('Error details:', error.response?.data || error);
        throw error;
      });
  },
  calculateDasha: (birthData) => api.post(getEndpoint('/calculate-dasha'), birthData),
  calculateYoginiDasha: (birthData, years = 5) => 
    api.post(getEndpoint('/yogini-dasha'), { ...birthData, years }),
  calculateCharaDasha: (birthData) => 
    api.post(getEndpoint('/chara-dasha/calculate'), birthData),
  calculateCharaAntardasha: (birthData, mahaSignId) => 
    api.post(getEndpoint('/chara-dasha/antardasha'), { ...birthData, maha_sign_id: mahaSignId }),
  calculateCharaKarakas: (chartData, birthData) => 
    api.post(getEndpoint('/chara-karakas'), { chart_data: chartData, birth_data: birthData }),
  
  calculateJaiminiLagnas: (chartData, d9Chart, atmakaraka) =>
    api.post(getEndpoint('/jaimini-special-lagnas'), { chart_data: chartData, d9_chart: d9Chart, atmakaraka }),
  
  calculateYogiPoints: (birthData) =>
    api.post(getEndpoint('/yogi-points'), { birth_data: birthData }),
  
  calculateSniperPoints: (chartData, d3Chart = {}, d9Chart = {}) =>
    api.post(getEndpoint('/sniper-points'), { chart_data: chartData, d3_chart: d3Chart, d9_chart: d9Chart }),
  
  calculatePushkaraNavamsha: (chartData, d9Chart = {}) =>
    api.post(getEndpoint('/pushkara-analysis'), { chart_data: chartData, d9_chart: d9Chart }),
  
  calculateKarkamsaChart: (chartData, atmakaraka) =>
    api.post(getEndpoint('/karkamsa-chart'), { chart_data: chartData, atmakaraka }),
  
  calculateSwamsaChart: (chartData, atmakaraka) =>
    api.post(getEndpoint('/swamsa-chart'), { chart_data: chartData, atmakaraka }),
  
  scanPhysicalTraits: (birthData, birthChartId = null) => 
    api.post(getEndpoint('/scan-physical'), { birth_data: birthData, birth_chart_id: birthChartId }),
  
  submitPhysicalFeedback: (feedbackData) => 
    api.post(getEndpoint('/physical-feedback'), feedbackData),

  getExistingCharts: (search = '') => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', '50');
    return api.get(`${getEndpoint('/birth-charts')}?${params}`);
  },
  updateChart: (id, data) => api.put(`${getEndpoint('/birth-charts')}/${id}`, data),
  deleteChart: (id) => api.delete(`${getEndpoint('/birth-charts')}/${id}`),
  setChartAsSelf: (id) => api.put(`${getEndpoint('/birth-charts')}/${id}/set-as-self`),
  searchUsers: (query) => api.get(`${getEndpoint('/users/search')}?query=${encodeURIComponent(query)}`),
  shareChart: (chartId, targetUserId) => api.post(getEndpoint('/charts/share'), { chart_id: chartId, target_user_id: targetUserId }),
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
  requestCredits: (amount, reason) => 
    api.post(getEndpoint('/credits/request'), { amount, reason }),
  getMyRequests: () => api.get(getEndpoint('/credits/requests/my')),
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
  calculateChoghadiya: (date, latitude, longitude) => 
    api.post(getEndpoint('/panchang/choghadiya'), { date, latitude, longitude }),
  calculateHora: (date, latitude, longitude) => 
    api.post(getEndpoint('/panchang/hora'), { date, latitude, longitude }),
  calculateSpecialMuhurtas: (date, latitude, longitude) => 
    api.post(getEndpoint('/panchang/special-muhurtas'), { date, latitude, longitude }),
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

export const lifeEventsAPI = {
  scanLifeEvents: (birthData, startAge = 18, endAge = 50) => 
    api.post(getEndpoint('/scan-life-events'), {
      birth_data: birthData,
      start_age: startAge,
      end_age: endAge
    }),
};

export const yogaAPI = {
  getYogas: (birthData) => {
    console.log('[yogaAPI] Endpoint:', getEndpoint('/yogas/'));
    console.log('[yogaAPI] Data:', birthData);
    return api.post(getEndpoint('/yogas/'), birthData);
  },
};

export const chatErrorAPI = {
  logError: (errorType, errorMessage, userQuestion = null, stackTrace = null) => 
    api.post(getEndpoint('/chat/log-error'), {
      error_type: errorType,
      error_message: errorMessage,
      user_question: userQuestion,
      stack_trace: stackTrace,
      platform: 'mobile'
    }),
};

export const kpAPI = {
  getKPChart: (birthData) => api.post(getEndpoint('/kp/chart'), birthData),
  getRulingPlanets: (birthData) => api.post(getEndpoint('/kp/ruling-planets'), birthData),
};

export default api;