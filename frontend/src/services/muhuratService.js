import { apiService } from './apiService';

const formatMuhuratError = (label, error) => {
  const detail = error?.response?.data?.detail;
  const message = detail || error?.message || 'Unknown error';
  return new Error(`Failed to get ${label}: ${typeof detail === 'string' ? detail : message}`);
};

export const muhuratService = {
  async getVivahMuhurat(date, latitude, longitude) {
    try {
      return await apiService.getVivahMuhurat(date, latitude, longitude);
    } catch (error) {
      throw formatMuhuratError('marriage muhurat', error);
    }
  },

  async getPropertyMuhurat(date, latitude, longitude) {
    try {
      return await apiService.getPropertyMuhurat(date, latitude, longitude);
    } catch (error) {
      throw formatMuhuratError('property muhurat', error);
    }
  },

  async getVehicleMuhurat(date, latitude, longitude) {
    try {
      return await apiService.getVehicleMuhurat(date, latitude, longitude);
    } catch (error) {
      throw formatMuhuratError('vehicle muhurat', error);
    }
  },

  async getGrihaPraveshMuhurat(date, latitude, longitude) {
    try {
      return await apiService.getGrihaPraveshMuhurat(date, latitude, longitude);
    } catch (error) {
      throw formatMuhuratError('griha pravesh muhurat', error);
    }
  }
};