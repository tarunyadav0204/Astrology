import { apiService } from '../../../services/apiService';

class PanchangService {
  async calculatePanchang(date, latitude, longitude, timezone) {
    if (!date || !latitude || !longitude || !timezone) {
      throw new Error('Missing required parameters for Panchang calculation');
    }

    const response = await apiService.calculatePanchang({
      transit_date: date,
      birth_data: {
        name: 'Panchang',
        date: date,
        time: '12:00',
        latitude: latitude,
        longitude: longitude,
        timezone: timezone,
        place: `${latitude}, ${longitude}`
      }
    });

    return response;
  }

  async calculateSunriseSunset(date, latitude, longitude) {
    if (!date || !latitude || !longitude) {
      throw new Error('Missing required parameters for sunrise/sunset calculation');
    }

    const response = await apiService.calculateSunriseSunset(date, latitude, longitude);
    return response;
  }

  async calculatePlanetaryPositions(date, latitude, longitude, timezone) {
    if (!date || !latitude || !longitude || !timezone) {
      throw new Error('Missing required parameters for planetary positions');
    }

    const response = await apiService.calculateTransits({
      transit_date: date,
      birth_data: {
        name: 'Transit',
        date: date,
        time: '12:00',
        latitude: latitude,
        longitude: longitude,
        timezone: timezone,
        place: `${latitude}, ${longitude}`
      }
    });

    return response;
  }

  async calculateMoonPhase(date) {
    if (!date) {
      throw new Error('Date is required for moon phase calculation');
    }

    const response = await apiService.calculateMoonPhase(date);
    return response;
  }

  async getFestivals(date) {
    if (!date) {
      throw new Error('Date is required for festival information');
    }

    const response = await apiService.getFestivals(date);
    return response;
  }

  async getInauspiciousTimes(date, latitude, longitude) {
    if (!date || !latitude || !longitude) {
      throw new Error('Missing required parameters for inauspicious times');
    }

    const response = await apiService.calculateInauspiciousTimes(date, latitude, longitude);
    return response;
  }

  async getRahuKaal(date, latitude, longitude) {
    if (!date || !latitude || !longitude) {
      throw new Error('Missing required parameters for Rahu Kaal calculation');
    }

    const response = await apiService.calculateRahuKaal(date, latitude, longitude);
    return response;
  }

  async calculateChoghadiya(date, latitude, longitude) {
    if (!date || !latitude || !longitude) {
      throw new Error('Missing required parameters for Choghadiya calculation');
    }

    const response = await apiService.calculateChoghadiya(date, latitude, longitude);
    return response;
  }

  async calculateHora(date, latitude, longitude) {
    if (!date || !latitude || !longitude) {
      throw new Error('Missing required parameters for Hora calculation');
    }

    const response = await apiService.calculateHora(date, latitude, longitude);
    return response;
  }

  async calculateSpecialMuhurtas(date, latitude, longitude) {
    if (!date || !latitude || !longitude) {
      throw new Error('Missing required parameters for Special Muhurtas calculation');
    }

    const response = await apiService.calculateSpecialMuhurtas(date, latitude, longitude);
    return response;
  }
}

export const panchangService = new PanchangService();