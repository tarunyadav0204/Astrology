import { apiService } from './apiService';

export const longevityService = {
  async calculate(birthData, chartData, horizonYears = 12, subject = 'self') {
    const response = await apiService.calculateLongevity({
      birthData,
      chartData,
      horizonYears,
      subject,
    });
    return response?.result;
  },
};
