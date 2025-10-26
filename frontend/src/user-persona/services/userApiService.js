// User-focused API service for consumer features
import { API_BASE_URL } from '../config/app.config';

class UserApiService {
  // Daily Horoscope
  async getDailyHoroscope(sunSign, date = null) {
    const response = await fetch(`${API_BASE_URL}/api/horoscope/daily/${sunSign.toLowerCase()}`);
    return response.json();
  }

  // Weekly Horoscope
  async getWeeklyHoroscope(sunSign) {
    const response = await fetch(`${API_BASE_URL}/api/horoscope/weekly/${sunSign.toLowerCase()}`);
    return response.json();
  }

  // Monthly Horoscope
  async getMonthlyHoroscope(sunSign) {
    const response = await fetch(`${API_BASE_URL}/api/horoscope/monthly/${sunSign.toLowerCase()}`);
    return response.json();
  }

  // Yearly Horoscope
  async getYearlyHoroscope(sunSign) {
    const response = await fetch(`${API_BASE_URL}/api/horoscope/yearly/${sunSign.toLowerCase()}`);
    return response.json();
  }

  // All Signs Daily Horoscope
  async getAllDailyHoroscopes() {
    const response = await fetch(`${API_BASE_URL}/api/horoscope/all-signs`);
    return response.json();
  }

  // Free Birth Chart
  async getFreeBirthChart(birthData) {
    const response = await fetch(`${API_BASE_URL}/user/birth-chart/free`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(birthData)
    });
    return response.json();
  }

  // Compatibility Analysis
  async getCompatibilityAnalysis(person1Data, person2Data) {
    const response = await fetch(`${API_BASE_URL}/user/compatibility`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        person1: person1Data,
        person2: person2Data
      })
    });
    return response.json();
  }

  // Life Predictions
  async getLifePredictions(birthData, category = 'all') {
    const response = await fetch(`${API_BASE_URL}/user/predictions/life`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ birth_data: birthData, category })
    });
    return response.json();
  }

  // Gemstone Recommendations
  async getGemstoneRecommendations(birthData) {
    const response = await fetch(`${API_BASE_URL}/user/remedies/gemstones`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(birthData)
    });
    return response.json();
  }

  // Muhurat (Auspicious Timing)
  async getAuspiciousTiming(birthData, eventType, dateRange) {
    const response = await fetch(`${API_BASE_URL}/user/muhurat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        birth_data: birthData,
        event_type: eventType,
        date_range: dateRange
      })
    });
    return response.json();
  }

  // Ask Astrologer - Get available astrologers
  async getAvailableAstrologers(specialization = null) {
    const params = specialization ? `?specialization=${specialization}` : '';
    const response = await fetch(`${API_BASE_URL}/user/astrologers${params}`);
    return response.json();
  }

  // Submit question to astrologer
  async submitQuestion(astrologerId, question, birthData) {
    const response = await fetch(`${API_BASE_URL}/user/astrologers/${astrologerId}/question`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        birth_data: birthData
      })
    });
    return response.json();
  }

  // Get user's consultation history
  async getConsultationHistory(userId) {
    const response = await fetch(`${API_BASE_URL}/user/consultations/${userId}`);
    return response.json();
  }

  // Marriage Timing
  async getMarriageTiming(birthData) {
    const response = await fetch(`${API_BASE_URL}/user/predictions/marriage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(birthData)
    });
    return response.json();
  }

  // Career Guidance
  async getCareerGuidance(birthData) {
    const response = await fetch(`${API_BASE_URL}/user/predictions/career`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(birthData)
    });
    return response.json();
  }

  // Health Predictions
  async getHealthPredictions(birthData) {
    const response = await fetch(`${API_BASE_URL}/user/predictions/health`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(birthData)
    });
    return response.json();
  }

  // Financial Forecast
  async getFinancialForecast(birthData, period = '1year') {
    const response = await fetch(`${API_BASE_URL}/user/predictions/finance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ birth_data: birthData, period })
    });
    return response.json();
  }

  // Remedial Solutions
  async getRemedialSolutions(birthData, problemArea) {
    const response = await fetch(`${API_BASE_URL}/user/remedies/solutions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        birth_data: birthData,
        problem_area: problemArea
      })
    });
    return response.json();
  }

  // Lucky Numbers & Colors
  async getLuckyElements(birthData, date = null) {
    const dateParam = date || new Date().toISOString().split('T')[0];
    const response = await fetch(`${API_BASE_URL}/user/lucky-elements`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ birth_data: birthData, date: dateParam })
    });
    return response.json();
  }

  // Panchang (Daily Calendar)
  async getPanchang(date, location) {
    const response = await fetch(`${API_BASE_URL}/user/panchang`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date, location })
    });
    return response.json();
  }
}

export const userApiService = new UserApiService();