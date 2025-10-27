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

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

class CareerService {
  // 10th House Lord Analysis
  async getTenthLordAnalysis(birthData) {
    const response = await apiClient.post('/api/career/tenth-lord-analysis', { birth_data: birthData });
    return response.data;
  }

  // Comprehensive Career Analysis
  async getComprehensiveAnalysis(birthData) {
    const response = await apiClient.post('/api/career/comprehensive-analysis', { birth_data: birthData });
    return response.data;
  }

  // 10th House Analysis
  async getTenthHouseAnalysis(birthData) {
    const response = await apiClient.post('/api/career/tenth-house-analysis', { birth_data: birthData });
    return response.data;
  }

  // Comprehensive 10th House Analysis
  async getTenthHouseComprehensive(birthData) {
    const response = await apiClient.post('/api/career/tenth-house-comprehensive', { birth_data: birthData });
    return response.data;
  }

  // D10 (Dasamsa) Analysis
  async getD10Analysis(birthData) {
    const response = await apiClient.post('/api/career/d10-analysis', { birth_data: birthData });
    return response.data;
  }

  // Saturn Karma Karaka Analysis
  async getSaturnKarakaAnalysis(birthData) {
    const response = await apiClient.post('/api/career/saturn-karaka-analysis', { birth_data: birthData });
    return response.data;
  }

  // Saturn's 10th House Analysis
  async getSaturnTenthAnalysis(birthData) {
    const response = await apiClient.post('/api/career/saturn-tenth-analysis', { birth_data: birthData });
    return response.data;
  }

  // Jaimini Amatyakaraka Analysis
  async getAmatyakarakaAnalysis(birthData) {
    const response = await apiClient.post('/api/career/amatyakaraka-analysis', { birth_data: birthData });
    return response.data;
  }

  // Career Success Yogas Analysis
  async getCareerYogasAnalysis(birthData) {
    const response = await apiClient.post('/api/career/success-yogas-analysis', { birth_data: birthData });
    return response.data;
  }

  // Nakshatra Career Analysis
  async getNakshatraAnalysis(birthData) {
    const response = await apiClient.post('/api/career/nakshatra-analysis', { birth_data: birthData });
    return response.data;
  }

  // Leadership Analysis
  async getLeadershipAnalysis(birthData) {
    const response = await apiClient.post('/api/career/leadership-analysis', { birth_data: birthData });
    return response.data;
  }

  // Work Style Analysis
  async getWorkStyleAnalysis(birthData) {
    const response = await apiClient.post('/api/career/work-style-analysis', { birth_data: birthData });
    return response.data;
  }

  // Solo vs Team Analysis
  async getSoloTeamAnalysis(birthData) {
    const response = await apiClient.post('/api/career/solo-team-analysis', { birth_data: birthData });
    return response.data;
  }

  // Career Fields Analysis
  async getCareerFieldsAnalysis(birthData) {
    const response = await apiClient.post('/api/career/career-fields-analysis', { birth_data: birthData });
    return response.data;
  }

  // Job Roles Analysis
  async getJobRolesAnalysis(birthData) {
    const response = await apiClient.post('/api/career/job-roles-analysis', { birth_data: birthData });
    return response.data;
  }

  // Work Mode Analysis (Employee vs Entrepreneur)
  async getWorkModeAnalysis(birthData) {
    const response = await apiClient.post('/api/career/work-mode-analysis', { birth_data: birthData });
    return response.data;
  }

  // Industries Analysis
  async getIndustriesAnalysis(birthData) {
    const response = await apiClient.post('/api/career/industries-analysis', { birth_data: birthData });
    return response.data;
  }

  // Work Type Analysis (Creative vs Technical vs Service)
  async getWorkTypeAnalysis(birthData) {
    const response = await apiClient.post('/api/career/work-type-analysis', { birth_data: birthData });
    return response.data;
  }

  // Avoid Careers Analysis
  async getAvoidCareersAnalysis(birthData) {
    const response = await apiClient.post('/api/career/avoid-careers-analysis', { birth_data: birthData });
    return response.data;
  }

  // Conjunction Analysis
  async getConjunctionAnalysis(birthData) {
    const response = await apiClient.post('/api/career/conjunction-analysis', { birth_data: birthData });
    return response.data;
  }

  // Use existing APIs for supporting data
  async getChartData(birthData) {
    return await apiClient.post('/api/calculate-chart', birthData);
  }

  async getDashaData(birthData) {
    return await apiClient.post('/api/calculate-dasha', birthData);
  }

  async getDivisionalChart(birthData, division = 10) {
    return await apiClient.post('/api/calculate-divisional-chart', {
      birth_data: birthData,
      division: division
    });
  }

  async getHouseAnalysis(birthData) {
    return await apiClient.post('/api/analyze-houses', birthData);
  }
}

export const careerService = new CareerService();