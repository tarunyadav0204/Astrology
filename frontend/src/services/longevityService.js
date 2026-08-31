import { apiService } from './apiService';

export const longevityService = {
  async calculate(birthData, chartData, horizonYears = 12, subject = 'self', ashtakavargaProfile = 'pvr_narasimha_rao') {
    const response = await apiService.calculateLongevity({
      birthData,
      chartData,
      horizonYears,
      subject,
      ashtakavargaProfile,
    });
    return response?.result;
  },
};
