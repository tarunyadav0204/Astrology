import { apiService } from './apiService';

export const muhuratService = {
  async getVivahMuhurat(date, latitude, longitude) {
    try {
      return await apiService.getVivahMuhurat(date, latitude, longitude);
    } catch (error) {
      throw new Error(`Failed to get marriage muhurat: ${error.message}`);
    }
  },

  async getPropertyMuhurat(date, latitude, longitude) {
    try {
      return await apiService.getPropertyMuhurat(date, latitude, longitude);
    } catch (error) {
      throw new Error(`Failed to get property muhurat: ${error.message}`);
    }
  },

  async getVehicleMuhurat(date, latitude, longitude) {
    try {
      return await apiService.getVehicleMuhurat(date, latitude, longitude);
    } catch (error) {
      throw new Error(`Failed to get vehicle muhurat: ${error.message}`);
    }
  },

  async getGrihaPraveshMuhurat(date, latitude, longitude) {
    try {
      return await apiService.getGrihaPraveshMuhurat(date, latitude, longitude);
    } catch (error) {
      throw new Error(`Failed to get griha pravesh muhurat: ${error.message}`);
    }
  }
};