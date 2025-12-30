import { apiService } from './apiService';

export const muhuratService = {
  async getVivahMuhurat(date, latitude, longitude, timezone) {
    try {
      const userTimezone = timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
      return await apiService.getVivahMuhurat(date, latitude, longitude, userTimezone);
    } catch (error) {
      throw new Error(`Failed to get marriage muhurat: ${error.message}`);
    }
  },

  async getPropertyMuhurat(date, latitude, longitude, timezone) {
    try {
      const userTimezone = timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
      return await apiService.getPropertyMuhurat(date, latitude, longitude, userTimezone);
    } catch (error) {
      throw new Error(`Failed to get property muhurat: ${error.message}`);
    }
  },

  async getVehicleMuhurat(date, latitude, longitude, timezone) {
    try {
      const userTimezone = timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
      return await apiService.getVehicleMuhurat(date, latitude, longitude, userTimezone);
    } catch (error) {
      throw new Error(`Failed to get vehicle muhurat: ${error.message}`);
    }
  },

  async getGrihaPraveshMuhurat(date, latitude, longitude, timezone) {
    try {
      const userTimezone = timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
      return await apiService.getGrihaPraveshMuhurat(date, latitude, longitude, userTimezone);
    } catch (error) {
      throw new Error(`Failed to get griha pravesh muhurat: ${error.message}`);
    }
  }
};