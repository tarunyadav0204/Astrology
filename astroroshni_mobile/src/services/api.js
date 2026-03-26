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

// ---- Transparent client-side caching (charts) ----
const CHART_ONLY_CACHE_VERSION = 3;
const CHART_ONLY_CACHE_TTL_MS = 30 * 60 * 1000; // 30 minutes
const chartOnlyInFlight = new Map(); // storageKey -> Promise
const chartOnlyMemory = new Map(); // storageKey -> { expiresAt, data }

const normalizeChartOnlyBirthDataKey = (birthData) => {
  // Prefer the unique birth chart id when available.
  const birthChartId =
    birthData?.birth_chart_id ??
    birthData?.birthChartId ??
    birthData?.birthChartID ??
    birthData?.id ??
    null;

  // Fallback: deterministic from the inputs that affect chart computation.
  const dateRaw = birthData?.date;
  const timeRaw = birthData?.time;

  const date =
    typeof dateRaw === 'string'
      ? dateRaw.includes('T')
        ? dateRaw.split('T')[0]
        : dateRaw
      : dateRaw;

  const time =
    typeof timeRaw === 'string'
      ? timeRaw.includes('T')
        ? new Date(timeRaw).toTimeString().slice(0, 5)
        : timeRaw.slice(0, 5)
      : timeRaw;

  const roundCoord = (v) => {
    const n = typeof v === 'string' || typeof v === 'number' ? Number(v) : null;
    if (n === null || Number.isNaN(n)) return null;
    return Math.round(n * 1e6) / 1e6; // stable against tiny float changes
  };

  const lat = roundCoord(birthData?.latitude);
  const lon = roundCoord(birthData?.longitude);

  // Ayanamsa isn't present in the mobile birth/profile payloads (at least in this app codebase),
  // so we keep the fingerprint to the deterministic inputs we actually have.
  const fp = `dt:${JSON.stringify({ date, time, lat, lon })}`;

  // Even if backend keeps the same birth_chart_id after user edits,
  // we include the fingerprint so the cache can't return a stale chart.
  if (birthChartId !== null && typeof birthChartId !== 'undefined' && birthChartId !== '') {
    return `id:${String(birthChartId)}|${fp}`;
  }

  return fp;
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

    // Only treat proxy / gateway / explicit overload as "servers down".
    // Plain 500 from our API usually means an app/DB bug or constraint — not "you have no internet".
    // Showing the global overlay there confuses users (e.g. duplicate key → 500 before we fixed it).
    const status = error.response?.status;
    if (status === 502 || status === 503 || status === 504) {
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
  getUserStats: () => api.get(getEndpoint('/user/stats')),

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
  tts: (text, lang = 'en', voiceName) =>
    api.post(getEndpoint('/tts/synthesize'), null, {
      params: { text, lang, voice_name: voiceName },
    }),
  getTtsVoices: () =>
    api.get(getEndpoint('/tts/voices')),
  getPodcastAudio: (messageContent, language = 'en', messageId = null, sessionId = null, preview = null, nativeName = null) =>
    api.post(getEndpoint('/tts/podcast'), {
      message_content: messageContent,
      language,
      ...(messageId ? { message_id: messageId } : {}),
      ...(sessionId ? { session_id: sessionId } : {}),
      ...(preview ? { preview } : {}),
      ...(nativeName ? { native_name: nativeName } : {}),
    }),
  checkPodcastCache: (messageId, lang = 'en') =>
    api.get(getEndpoint('/tts/podcast/check-cache'), {
      params: { message_id: messageId, lang: lang?.toLowerCase?.()?.startsWith?.('hi') ? 'hi' : 'en' },
    }),
  getPodcastHistory: () =>
    api.get(getEndpoint('/tts/podcast/history')),
  getPodcastStreamUrl: (messageId, lang = 'en') => {
    const langCode = lang?.toLowerCase?.()?.startsWith?.('hi') ? 'hi' : 'en';
    const base = API_BASE_URL?.replace(/\/$/, '') || '';
    const path = getEndpoint('/tts/podcast/stream').replace(/^\//, '');
    return `${base}/${path}?message_id=${encodeURIComponent(String(messageId))}&lang=${encodeURIComponent(langCode)}`;
  },
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
    const cacheKey = normalizeChartOnlyBirthDataKey(birthData);
    const storageKey = `chart_only_cache:v${CHART_ONLY_CACHE_VERSION}:${cacheKey}`;

    const mem = chartOnlyMemory.get(storageKey);
    if (mem && mem.expiresAt > Date.now() && mem.data) {
      return Promise.resolve({ data: mem.data, status: 200 });
    }

    const existingPromise = chartOnlyInFlight.get(storageKey);
    if (existingPromise) return existingPromise;

    const requestPromise = (async () => {
      // 1) AsyncStorage cache
      try {
        const cached = await AsyncStorage.getItem(storageKey);
        if (cached) {
          const parsed = JSON.parse(cached);
          if (parsed?.expiresAt > Date.now() && parsed?.data) {
            chartOnlyMemory.set(storageKey, { expiresAt: parsed.expiresAt, data: parsed.data });
            return { data: parsed.data, status: 200 };
          }
        }
      } catch (_) {
        // ignore cache errors
      }

      // 2) Network call
      const response = await api.post(getEndpoint('/calculate-chart-only'), birthData);

      // 3) Store in caches
      try {
        const expiresAt = Date.now() + CHART_ONLY_CACHE_TTL_MS;
        const chartData = response?.data;
        if (chartData) {
          chartOnlyMemory.set(storageKey, { expiresAt, data: chartData });
          await AsyncStorage.setItem(storageKey, JSON.stringify({ expiresAt, data: chartData }));
        }
      } catch (_) {
        // ignore storage errors
      }

      return response;
    })();

    chartOnlyInFlight.set(storageKey, requestPromise);
    return requestPromise.finally(() => {
      chartOnlyInFlight.delete(storageKey);
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
  getSadeSatiPeriods: (birthData) => {
    const transitDate = new Date().toISOString().split('T')[0];
    return api.post(getEndpoint('/transits/sade-sati-periods'), { birth_data: birthData, transit_date: transitDate })
      .then(response => response)
      .catch(error => {
        console.error('getSadeSatiPeriods error:', error?.response?.data || error);
        throw error;
      });
  },
  getNakshatraYearCalendar: async (year, latitude, longitude) => {
    const lat = latitude != null ? Number(latitude) : 28.6139;
    const lon = longitude != null ? Number(longitude) : 77.2090;
    const latR = Math.round(lat * 10000) / 10000;
    const lonR = Math.round(lon * 10000) / 10000;
    const CACHE_KEY_PREFIX = 'nakshatra_year_';
    const NAKSHATRA_CACHE_VERSION = 5; // bump when backend nakshatra logic/response changes
    const CACHE_HOURS = 24;
    const cacheKey = `${CACHE_KEY_PREFIX}v${NAKSHATRA_CACHE_VERSION}_${year}_${latR}_${lonR}`;
    try {
      const cached = await AsyncStorage.getItem(cacheKey);
      if (cached) {
        const { cachedAt, data } = JSON.parse(cached);
        const ageHours = (Date.now() - (cachedAt || 0)) / (1000 * 60 * 60);
        if (ageHours <= CACHE_HOURS && data) {
          return { data };
        }
      }
    } catch (_) { /* ignore parse/storage errors */ }
    return api.get(getEndpoint(`/nakshatra/year/${year}`), { params: { latitude: lat, longitude: lon } })
      .then(async (response) => {
        try {
          await AsyncStorage.setItem(cacheKey, JSON.stringify({
            cachedAt: Date.now(),
            data: response.data,
          }));
        } catch (_) { /* ignore */ }
        return response;
      })
      .catch(error => {
        console.error('getNakshatraYearCalendar error:', error?.response?.data || error);
        throw error;
      });
  },
  calculateYogi: (birthData) =>
    api.post(getEndpoint('/yogi-points'), { birth_data: birthData })
      .then(response => response.data?.yogi_points || response.data)
      .catch(error => {
        throw error;
      }),
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

  getExistingCharts: (search = '', limit = 10, offset = 0) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', String(limit));
    params.append('offset', String(offset));
    return api.get(`${getEndpoint('/birth-charts')}?${params}`);
  },
  updateChart: (id, data) => api.put(`${getEndpoint('/birth-charts')}/${id}`, data),
  deleteChart: (id) => api.delete(`${getEndpoint('/birth-charts')}/${id}`),
  setChartAsSelf: (id) => api.put(`${getEndpoint('/birth-charts')}/${id}/set-as-self`),
  searchUsers: (query) => api.get(`${getEndpoint('/users/search')}?query=${encodeURIComponent(query)}`),
  shareChart: (chartId, targetUserId) => api.post(getEndpoint('/charts/share'), { chart_id: chartId, target_user_id: targetUserId }),
};

export const nudgeAPI = {
  registerDeviceToken: (token, platform) =>
    api.post(getEndpoint('/nudge/device-token'), { token, platform }),
  getInbox: (params = {}) => {
    const sp = new URLSearchParams();
    if (params.limit != null) sp.set('limit', String(params.limit));
    if (params.offset != null) sp.set('offset', String(params.offset));
    const q = sp.toString();
    return api.get(getEndpoint(`/nudge/inbox${q ? `?${q}` : ''}`));
  },
  getUnreadCount: () => api.get(getEndpoint('/nudge/inbox/unread-count')),
  /** ids omitted or empty array = mark all read */
  markRead: (body = {}) => api.post(getEndpoint('/nudge/inbox/mark-read'), body),
};

export const creditAPI = {
  getBalance: () => api.get(getEndpoint('/credits/balance')),
  getSubscriptionDetails: () => api.get(getEndpoint('/credits/subscription')),
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
  verifyGooglePlayPurchase: (purchaseToken, productId, orderId) =>
    api.post(getEndpoint('/credits/google-play/verify'), {
      purchase_token: purchaseToken,
      product_id: productId,
      order_id: orderId,
    }),
  getGooglePlayProducts: () => api.get(getEndpoint('/credits/google-play/products')),
  getSubscriptionPlans: () => api.get(getEndpoint('/credits/google-play/subscription-plans')),
  syncSubscription: (purchaseToken, productId) =>
    api.post(getEndpoint('/credits/google-play/subscription/sync'), {
      purchase_token: purchaseToken,
      product_id: productId,
    }),
  clearSubscriptionNoPurchase: () =>
    api.post(getEndpoint('/credits/google-play/subscription/clear')),
  verifyGooglePlaySubscription: (purchaseToken, productId, orderId) =>
    api.post(getEndpoint('/credits/google-play/subscription/verify'), {
      purchase_token: purchaseToken,
      product_id: productId,
      order_id: orderId,
    }),
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
  /** Base pricing (unauthenticated). */
  getAnalysisPricing: () => api.get(getEndpoint('/credits/settings/analysis-pricing')),
  /** User's pricing with subscription discount (authenticated). Returns subscription_tier_name, subscription_discount_percent, pricing, pricing_original. */
  getMyPricing: () => api.get(getEndpoint('/credits/settings/my-pricing')),
  /**
   * Best available pricing: when logged in uses my-pricing (discounted); otherwise analysis-pricing.
   * Use this so VIP users see 30% off and correct costs.
   */
  async getPricing() {
    try {
      const r = await api.get(getEndpoint('/credits/settings/my-pricing'));
      return r;
    } catch (e) {
      if (e.response?.status === 401 || !e.response) {
        return api.get(getEndpoint('/credits/settings/analysis-pricing'));
      }
      throw e;
    }
  },
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

export const blogAPI = {
  getPosts: (status = 'published', category = null, limit = 10, offset = 0) => {
    let url = `/blog/posts?status=${status}&limit=${limit}&offset=${offset}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    return api.get(getEndpoint(url));
  },
  getPostById: (id) => api.get(getEndpoint(`/blog/posts/${id}`)),
  getPostBySlug: (slug) => api.get(getEndpoint(`/blog/posts/slug/${slug}`)),
  getBlogCategories: () => api.get(getEndpoint('/blog/categories')),
};

export default api;
