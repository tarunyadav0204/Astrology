import axios from 'axios';
import { APP_CONFIG, isPublicAppPath } from '../config/app.config';

/**
 * In development, use same-origin `/api/...` (see package.json "proxy") so requests
 * are not cross-origin from localhost:3001 → localhost:8001. Otherwise the browser may
 * omit `Authorization` and FastAPI returns {"detail":"Not authenticated"}.
 * Set REACT_APP_API_BASE_URL to override (e.g. direct backend URL when not using proxy).
 */
const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL !== undefined && process.env.REACT_APP_API_BASE_URL !== ''
    ? process.env.REACT_APP_API_BASE_URL
    : '';

console.log('Environment:', process.env.NODE_ENV);
console.log('API Base URL:', API_BASE_URL || '(same-origin /api)');

// Helper function to handle API endpoints for both dev and production
const getEndpoint = (path) => {
  // For localhost development, add /api prefix
  if (API_BASE_URL.includes('localhost')) {
    const endpoint = `/api${path}`;
    console.log('DEV - API_BASE_URL:', API_BASE_URL, 'Path:', path, 'Final endpoint:', endpoint);
    return endpoint;
  }
  // For production, add /api prefix
  const endpoint = `/api${path}`;
  // console.log('PROD - API_BASE_URL:', API_BASE_URL, 'Path:', path, 'Final endpoint:', endpoint);
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



// Request interceptor to add JWT token (only when a saved session exists)
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    console.log('API Request:', config.url, 'Token:', token && savedUser ? 'Present' : 'Missing');
    if (token && savedUser) {
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
    const denialCode = error.response?.data?.detail?.code;
    if (error.response?.status === 403 && denialCode === 'ASTROLOGER_LICENSE_REQUIRED') {
      return Promise.reject(error);
    }
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');

      const pathname = window.location.pathname;
      // Public tools (e.g. Panchang) must work without login — never send guests to /login
      if (isPublicAppPath(pathname)) {
        return Promise.reject(error);
      }

      if (pathname !== '/' && pathname !== '/login') {
        window.location.href = '/';
      }
      return Promise.reject(new Error('Session expired. Please login again.'));
    }
    throw error;
  }
);

export const apiService = {
  calculateLongevity: async ({ birthData, chartData, horizonYears = 12, subject = 'self', ashtakavargaProfile = 'pvr_narasimha_rao' }) => {
    const response = await apiClient.post(getEndpoint('/longevity/calculate'), {
      birth_data: birthData,
      chart_data: chartData,
      horizon_years: horizonYears,
      subject,
      ashtakavarga_profile: ashtakavargaProfile,
    });
    return response.data;
  },

  startInstantChatSession: async ({ chatSessionId, clientInstanceId }) => {
    const response = await apiClient.post(getEndpoint('/credits/instant-session/start'), {
      chat_session_id: chatSessionId,
      client_instance_id: clientInstanceId,
    });
    return response.data;
  },

  heartbeatInstantChatSession: async (sessionId) => {
    const response = await apiClient.post(getEndpoint(`/credits/instant-session/${encodeURIComponent(sessionId)}/heartbeat`), {});
    return response.data;
  },

  endInstantChatSession: async (sessionId, reason = 'user_ended') => {
    const response = await apiClient.post(getEndpoint(`/credits/instant-session/${encodeURIComponent(sessionId)}/end`), { reason });
    return response.data;
  },

  // Health check API
  healthCheck: async () => {
    try {
      const response = await apiClient.get(getEndpoint('/health'));
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },
  
  // Test API connectivity
  testConnection: async () => {
    try {
      const response = await apiClient.get(getEndpoint('/test'));
      return response.data;
    } catch (error) {
      console.error('Connection test failed:', error);
      throw error;
    }
  },
  
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
    // Remove timezone field to let backend calculate it from coordinates
    const { timezone, ...birthDataWithoutTimezone } = birthData;
    const response = await apiClient.post(`${getEndpoint('/calculate-chart')}?node_type=${nodeType}`, birthDataWithoutTimezone);
    return response.data;
  },
  
  calculateChartOnly: async (birthData, nodeType = 'mean', calculationProfile = null) => {
    // Remove timezone field to let backend calculate it from coordinates
    const { timezone, ...birthDataWithoutTimezone } = birthData;
    const payload = calculationProfile
      ? { birth_data: birthDataWithoutTimezone, calculation_profile: calculationProfile }
      : birthDataWithoutTimezone;
    const response = await apiClient.post(`${getEndpoint('/calculate-chart-only')}?node_type=${nodeType}`, payload);
    return response.data;
  },

  /** Vimshottari hierarchy for a date (maha → prana); used by chat header chips. */
  calculateCascadingDashas: async (birthData, targetDateStr) => {
    const rawDate = birthData?.date != null ? String(birthData.date) : '';
    const dateStr = rawDate.includes('T') ? rawDate.split('T')[0] : rawDate;
    let timeStr = birthData?.time != null ? String(birthData.time) : '';
    if (timeStr.includes('T')) {
      try {
        timeStr = new Date(timeStr).toTimeString().slice(0, 5);
      } catch {
        timeStr = timeStr.slice(11, 16) || timeStr;
      }
    }
    const payload = {
      name: birthData?.name || 'Unknown',
      date: dateStr,
      time: timeStr,
      latitude: parseFloat(birthData.latitude),
      longitude: parseFloat(birthData.longitude),
      place: birthData.place || 'Unknown',
    };
    const target =
      targetDateStr && String(targetDateStr).trim()
        ? String(targetDateStr).trim()
        : new Date().toISOString().split('T')[0];
    // Keep clock when caller passes YYYY-MM-DDTHH:mm[:ss] (desk as-of time).
    // Date-only values stay date-only; backend anchors those at noon.
    const response = await apiClient.post(getEndpoint('/calculate-cascading-dashas'), {
      birth_data: payload,
      target_date: target,
    });
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
  
  getExistingCharts: async (search = '', limit = 50, offset = 0) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', String(limit));
    params.append('offset', String(offset));
    const response = await apiClient.get(`${getEndpoint('/birth-charts')}?${params}`);
    return response.data;
  },

  getActivationExplorer: async ({ birthChartId, birthData, asOf, horizonDays = 90, trace = true }) => {
    const response = await apiClient.post(getEndpoint('/prediction-engine/activation-explorer'), {
      birth_chart_id: birthChartId || null,
      birth_data: birthChartId ? null : birthData,
      as_of: asOf,
      horizon_days: horizonDays,
      maximum_candidates: 100,
      trace,
    });
    return response.data;
  },

  getEventWindows: async ({ birthChartId, birthData, eventKey, year, includeDeveloping = false, focusHouses = null }) => {
    const response = await apiClient.post(getEndpoint('/prediction-engine/event-windows'), {
      birth_chart_id: birthChartId || null,
      birth_data: birthChartId ? null : birthData,
      event_key: eventKey,
      year,
      include_developing: includeDeveloping,
      focus_houses: eventKey === 'custom' ? (focusHouses || []) : null,
    });
    return response.data;
  },

  getNadiDesk: async ({ birthData, chartData, asOf, transitPlanets }) => {
    const response = await apiClient.post(getEndpoint('/nadi-desk'), {
      birth_data: birthData,
      chart_data: chartData,
      as_of: asOf,
      transit_planets: transitPlanets || null,
    });
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
    const response = await apiClient.post(getEndpoint('/yogi-points'), {
      birth_data: birthData
    });
    // Backend returns { success, yogi_points }
    return response.data?.yogi_points || response.data;
  },
  
  calculatePanchang: async (birthData) => {
    const response = await apiClient.post(getEndpoint('/panchang/calculate-panchang'), birthData);
    return response.data;
  },

  /** Janma pañcāṅga at birth moment (tithi, vāra, nakṣatra, yoga, karaṇa). */
  calculateBirthPanchang: async (birthData) => {
    const response = await apiClient.post(getEndpoint('/panchang/calculate-birth-panchang'), {
      birth_data: birthData,
    });
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
  
  calculateDivisionalChart: async (birthData, division, calculationProfile = null) => {
    // Remove timezone field to let backend calculate it from coordinates
    const { timezone, ...birthDataWithoutTimezone } = birthData;
    const response = await apiClient.post(getEndpoint('/calculate-divisional-chart'), {
      birth_data: birthDataWithoutTimezone,
      division: division,
      ...(calculationProfile ? { calculation_profile: calculationProfile } : {}),
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

  getChatAnswerStyle: async () => {
    const response = await apiClient.get(getEndpoint('/user-settings/chat-answer-style'));
    return response.data;
  },

  updateChatAnswerStyle: async (answerStyle) => {
    const response = await apiClient.put(getEndpoint('/user-settings/chat-answer-style'), {
      answer_style: answerStyle === 'technical' ? 'technical' : 'simple',
    });
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
  },
  
  calculateBadhakaMaraka: async (chartData) => {
    const response = await apiClient.post(getEndpoint('/badhaka-maraka-analysis'), {
      natal_chart: chartData
    });
    return response.data;
  },
  
  calculatePlanetaryDignities: async (chartData, birthData) => {
    const response = await apiClient.post(getEndpoint('/planetary-dignities'), {
      chart_data: chartData,
      birth_data: birthData
    });
    return response.data;
  },
  
  calculateCharaKarakas: async (chartData, birthData) => {
    const response = await apiClient.post(getEndpoint('/chara-karakas'), {
      chart_data: chartData,
      birth_data: birthData
    });
    return response.data;
  },
  
  calculateShadbala: async (chartData, birthData) => {
    const response = await apiClient.post(getEndpoint('/calculate-classical-shadbala'), {
      chart_data: chartData,
      birth_data: birthData
    });
    return response.data;
  },
  
  // Panchang APIs
  calculateSunriseSunset: async (date, latitude, longitude) => {
    const response = await apiClient.post(getEndpoint('/panchang/calculate-sunrise-sunset'), {
      date: date,
      latitude: latitude,
      longitude: longitude
    });
    return response.data;
  },
  
  calculateMoonPhase: async (date) => {
    const response = await apiClient.post(getEndpoint('/panchang/calculate-moon-phase'), {
      date: date
    });
    return response.data;
  },
  
  calculateInauspiciousTimes: async (date, latitude, longitude) => {
    const response = await apiClient.post(getEndpoint('/panchang/calculate-inauspicious-times'), {
      date: date,
      latitude: latitude,
      longitude: longitude
    });
    return response.data;
  },
  
  getFestivals: async (date) => {
    const response = await apiClient.get(getEndpoint(`/panchang/festivals/${date}`));
    return response.data;
  },
  
  calculateRahuKaal: async (date, latitude, longitude) => {
    const response = await apiClient.post(getEndpoint('/panchang/calculate-rahu-kaal'), {
      date: date,
      latitude: latitude,
      longitude: longitude
    });
    return response.data;
  },
  
  calculateChoghadiya: async (date, latitude, longitude) => {
    const response = await apiClient.get(`${getEndpoint('/panchang/choghadiya')}?date=${date}&latitude=${latitude}&longitude=${longitude}`);
    return response.data;
  },
  
  calculateHora: async (date, latitude, longitude) => {
    const response = await apiClient.get(`${getEndpoint('/panchang/hora')}?date=${date}&latitude=${latitude}&longitude=${longitude}`);
    return response.data;
  },
  
  calculateSpecialMuhurtas: async (date, latitude, longitude) => {
    const response = await apiClient.get(`${getEndpoint('/panchang/special-muhurtas')}?date=${date}&latitude=${latitude}&longitude=${longitude}`);
    return response.data;
  },
  
  calculatePlanetaryPositions: async (transitRequest) => {
    const response = await apiClient.post(getEndpoint('/calculate-transits'), transitRequest);
    return response.data;
  },
  
  // Muhurat APIs
  getVivahMuhurat: async (date, latitude, longitude) => {
    const response = await apiClient.get(`${getEndpoint('/panchang/vivah-muhurat')}?date=${date}&latitude=${latitude}&longitude=${longitude}`);
    return response.data;
  },
  
  getPropertyMuhurat: async (date, latitude, longitude) => {
    const response = await apiClient.get(`${getEndpoint('/panchang/property-muhurat')}?date=${date}&latitude=${latitude}&longitude=${longitude}`);
    return response.data;
  },
  
  getVehicleMuhurat: async (date, latitude, longitude, birthData = null) => {
    const params = new URLSearchParams({ date, latitude, longitude });
    if (birthData?.date && birthData?.time) {
      params.set('birth_date', String(birthData.date).split('T')[0]);
      params.set('birth_time', birthData.time);
      if (birthData.latitude != null) params.set('birth_latitude', birthData.latitude);
      if (birthData.longitude != null) params.set('birth_longitude', birthData.longitude);
      if (birthData.timezone) params.set('birth_timezone', birthData.timezone);
    }
    const response = await apiClient.get(`${getEndpoint('/panchang/vehicle-muhurat')}?${params.toString()}`);
    return response.data;
  },
  
  getGrihaPraveshMuhurat: async (date, latitude, longitude) => {
    const response = await apiClient.get(`${getEndpoint('/panchang/griha-pravesh-muhurat')}?date=${date}&latitude=${latitude}&longitude=${longitude}`);
    return response.data;
  },

  /** Event timeline (yearly 12-month or single-month deep) — same API as mobile EventScreen */
  startEventTimeline: async (payload) => {
    const response = await apiClient.post(getEndpoint('/chat/monthly-events'), payload);
    return response.data;
  },

  getEventTimelineStatus: async (jobId) => {
    const response = await apiClient.get(getEndpoint(`/chat/monthly-events/status/${jobId}`));
    return response.data;
  },

  streamEventTimeline: async (jobId, onEvent, signal) => {
    const token = localStorage.getItem('token');
    const endpoint = `${API_BASE_URL}${getEndpoint(`/chat/monthly-events/stream/${jobId}`)}`;
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      signal,
    });
    if (!response.ok) {
      throw new Error(`Timeline stream failed (${response.status})`);
    }
    if (!response.body) {
      throw new Error('Timeline stream body is unavailable');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let sepIndex = buffer.indexOf('\n\n');
      while (sepIndex !== -1) {
        const chunk = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + 2);
        sepIndex = buffer.indexOf('\n\n');

        const lines = chunk.split('\n');
        let eventName = 'message';
        const dataLines = [];
        for (const line of lines) {
          if (line.startsWith('event:')) eventName = line.slice(6).trim();
          if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
        }
        if (dataLines.length > 0) {
          try {
            onEvent?.(eventName, JSON.parse(dataLines.join('\n')));
          } catch {
            // ignore malformed chunks and continue streaming
          }
        }
      }
    }
  },

  getCachedEventTimeline: async (payload) => {
    const response = await apiClient.post(getEndpoint('/chat/monthly-events/cached'), payload);
    return response.data;
  },

  getCachedEventTimelineYears: async (birthChartId) => {
    const response = await apiClient.get(
      `${getEndpoint('/chat/monthly-events/cached-years')}?birth_chart_id=${encodeURIComponent(String(birthChartId))}`
    );
    return response.data;
  },

  getKpFructification: async (payload) => {
    const response = await apiClient.post(getEndpoint('/kp/fructification'), payload);
    return response.data;
  },

  getKpChart: async (payload) => {
    const response = await apiClient.post(getEndpoint('/kp/chart'), payload);
    return response.data;
  },

  getKpRulingPlanets: async (payload) => {
    const response = await apiClient.post(getEndpoint('/kp/ruling-planets'), payload);
    return response.data;
  },

  getHouseInsight: async ({ birthData, houseNum, chartId = 'lagna', transitDate }) => {
    const dateStr = String(birthData?.date || '').includes('T')
      ? String(birthData.date).split('T')[0]
      : birthData?.date;
    let timeStr = String(birthData?.time || '');
    if (timeStr.includes('T')) timeStr = timeStr.split('T')[1]?.slice(0, 5) || timeStr;
    else timeStr = timeStr.slice(0, 5);
    const response = await apiClient.post(getEndpoint('/chart-house-insight'), {
      birth_data: {
        name: birthData?.name || 'Native',
        date: dateStr,
        time: timeStr,
        latitude: parseFloat(birthData?.latitude),
        longitude: parseFloat(birthData?.longitude),
        place: birthData?.place || 'Unknown',
      },
      house_num: houseNum,
      chart_id: chartId,
      transit_date: transitDate || new Date().toISOString().split('T')[0],
    });
    return response.data;
  },

  calculateMudakkuAnalysis: async (chartData) => {
    const response = await apiClient.post(getEndpoint('/mudakku-analysis'), { chart_data: chartData });
    return response.data;
  },

  getDoubleTransits: async ({ chartData, startDate, endDate, includeAspectOnly = true }) => {
    const response = await apiClient.post(getEndpoint('/double-transits'), {
      chart_data: chartData,
      start_date: startDate,
      end_date: endDate,
      include_aspect_only: includeAspectOnly,
    });
    return response.data;
  },

  calculateGandantaAnalysis: async (chartData) => {
    const response = await apiClient.post(getEndpoint('/gandanta-analysis'), { chart_data: chartData });
    return response.data;
  },

  getYogas: async (birthData) => {
    const dateStr = String(birthData?.date || '').includes('T')
      ? String(birthData.date).split('T')[0]
      : birthData?.date;
    let timeStr = String(birthData?.time || '');
    if (timeStr.includes('T')) timeStr = timeStr.split('T')[1]?.slice(0, 5) || timeStr;
    else timeStr = timeStr.slice(0, 5);
    const response = await apiClient.post(getEndpoint('/yogas/'), {
      name: birthData?.name || 'Native',
      date: dateStr,
      time: timeStr,
      place: birthData?.place || 'Unknown',
      latitude: birthData?.latitude != null ? parseFloat(birthData.latitude) : undefined,
      longitude: birthData?.longitude != null ? parseFloat(birthData.longitude) : undefined,
      timezone: birthData?.timezone,
      gender: birthData?.gender,
    });
    return response.data;
  },

  calculateKarkamsaChart: async (chartData, atmakaraka) => {
    const response = await apiClient.post(getEndpoint('/karkamsa-chart'), {
      chart_data: chartData,
      atmakaraka,
    });
    return response.data;
  },

  calculateSwamsaChart: async (chartData, atmakaraka) => {
    const response = await apiClient.post(getEndpoint('/swamsa-chart'), {
      chart_data: chartData,
      atmakaraka,
    });
    return response.data;
  },

  calculateJaiminiSpecialLagnas: async (chartData, atmakaraka, d9Chart = null) => {
    const response = await apiClient.post(getEndpoint('/jaimini-special-lagnas'), {
      chart_data: chartData,
      atmakaraka,
      d9_chart: d9Chart,
    });
    return response.data;
  },

  calculateSniperPoints: async (chartData, d3Chart = null, d9Chart = null) => {
    const response = await apiClient.post(getEndpoint('/sniper-points'), {
      chart_data: chartData,
      d3_chart: d3Chart,
      d9_chart: d9Chart,
    });
    return response.data;
  },

  calculatePushkaraAnalysis: async (chartData, d9Chart = null) => {
    const response = await apiClient.post(getEndpoint('/pushkara-analysis'), {
      chart_data: chartData,
      d9_chart: d9Chart,
    });
    return response.data;
  },
};
