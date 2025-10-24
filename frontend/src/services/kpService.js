import { KP_CONFIG, NAKSHATRA_DATA, DAY_LORDS } from '../config/kpConfig';

class KPService {
  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
  }

  // Calculate KP Chart with Placidus Houses
  async calculateKPChart(birthData) {
    const response = await fetch(`${this.baseUrl}/api/kp/chart`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        birth_date: birthData.date,
        birth_time: birthData.time,
        latitude: birthData.latitude,
        longitude: birthData.longitude,
        timezone_offset: 0
      })
    });

    if (!response.ok) {
      throw new Error(`KP Chart API error: ${response.status}`);
    }

    const result = await response.json();
    return this.transformChartData(result.data);
  }

  // Calculate Sub-Lords for all planets
  async calculateSubLords(birthData) {
    // Use the chart endpoint which includes sub-sub lords
    const response = await fetch(`${this.baseUrl}/api/kp/chart`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        birth_date: birthData.date,
        birth_time: birthData.time,
        latitude: birthData.latitude,
        longitude: birthData.longitude,
        timezone_offset: 0
      })
    });

    if (!response.ok) {
      throw new Error(`Sub-Lords API error: ${response.status}`);
    }

    const result = await response.json();
    return this.transformSubLordsData(result.data, result.data);
  }

  // Calculate Ruling Planets
  async calculateRulingPlanets(birthData, questionTime = null) {
    const response = await fetch(`${this.baseUrl}/api/kp/ruling-planets`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        birth_date: birthData.date,
        birth_time: birthData.time,
        latitude: birthData.latitude,
        longitude: birthData.longitude,
        timezone_offset: 0
      })
    });

    if (!response.ok) {
      throw new Error(`Ruling Planets API error: ${response.status}`);
    }

    const result = await response.json();
    return this.transformRulingPlanetsData(result.data);
  }

  // Calculate Significators for all houses
  async calculateSignificators(birthData) {
    const response = await fetch(`${this.baseUrl}/api/kp/significators`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        birth_date: birthData.date,
        birth_time: birthData.time,
        latitude: birthData.latitude,
        longitude: birthData.longitude,
        timezone_offset: 0
      })
    });

    if (!response.ok) {
      throw new Error(`Significators API error: ${response.status}`);
    }

    const result = await response.json();
    return this.transformSignificatorsData(result.data);
  }

  // KP Horary Analysis
  async analyzeHorary(birthData, question, horary_number, questionTime) {
    const response = await fetch(`${this.baseUrl}/api/kp/horary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        question_number: horary_number,
        question_text: question
      })
    });

    if (!response.ok) {
      throw new Error(`Horary API error: ${response.status}`);
    }

    const result = await response.json();
    return result.data || result;
  }

  // Event Timing Predictions
  async predictEventTiming(birthData, eventType) {
    const response = await fetch(`${this.baseUrl}/api/kp/event-timing`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        birth_date: birthData.date,
        birth_time: birthData.time,
        latitude: birthData.latitude,
        longitude: birthData.longitude,
        event_type: eventType
      })
    });

    if (!response.ok) {
      throw new Error(`Event Timing API error: ${response.status}`);
    }

    const result = await response.json();
    return result.data || result;
  }

  // Get Nakshatra and Sub-Lord from degree
  getNakshatraFromDegree(degree) {
    const adjustedDegree = degree % 360;
    const nakshatraIndex = Math.floor(adjustedDegree / KP_CONFIG.NAKSHATRAS.DEGREES_PER_NAKSHATRA);
    const nakshatra = NAKSHATRA_DATA[nakshatraIndex];
    
    const degreesInNakshatra = adjustedDegree - nakshatra.startDegree;
    const padaIndex = Math.floor(degreesInNakshatra / (KP_CONFIG.NAKSHATRAS.DEGREES_PER_NAKSHATRA / 4));
    
    return {
      nakshatra: nakshatra.name,
      lord: nakshatra.lord,
      pada: padaIndex + 1,
      degreesInNakshatra: degreesInNakshatra
    };
  }

  // Get Day Lord from date
  getDayLord(date) {
    const dayOfWeek = new Date(date).getDay();
    return DAY_LORDS[dayOfWeek];
  }

  // Format degree to KP format (degrees, minutes, seconds)
  formatDegree(degree) {
    const deg = Math.floor(degree);
    const min = Math.floor((degree - deg) * 60);
    const sec = Math.floor(((degree - deg) * 60 - min) * 60);
    return `${deg}°${min}'${sec}"`;
  }

  // Validate Horary Number
  isValidHoraryNumber(number) {
    return number >= KP_CONFIG.HORARY.MIN_NUMBER && number <= KP_CONFIG.HORARY.MAX_NUMBER;
  }

  // Transform backend chart data to frontend format
  transformChartData(data) {
    const houses = [];
    const planets = [];

    // Transform houses
    for (let i = 1; i <= 12; i++) {
      houses.push({
        number: i,
        cusp_longitude: data.house_cusps[i],
        sign: this.getSignFromDegree(data.house_cusps[i])
      });
    }

    // Transform planets
    Object.entries(data.planet_positions).forEach(([name, longitude]) => {
      planets.push({
        name,
        symbol: this.getPlanetSymbol(name),
        longitude,
        sign: this.getSignFromDegree(longitude),
        sub_lord: data.planet_sub_lords ? data.planet_sub_lords[name] : ''
      });
    });

    return { houses, planets };
  }

  // Transform sub-lords data to frontend format
  transformSubLordsData(data, chartData = null) {
    const planets = [];
    const cusps = [];

    // Transform planet sub-lords
    Object.entries(data.planet_sub_lords || {}).forEach(([name, subLord]) => {
      const longitude = chartData?.planet_positions?.[name] || 0;
      
      // Calculate house position based on house cusps
      let houseNumber = 1;
      if (chartData?.house_cusps) {
        for (let i = 1; i <= 12; i++) {
          const currentCusp = chartData.house_cusps[i] || 0;
          const nextHouse = i === 12 ? 1 : i + 1;
          const nextCusp = chartData.house_cusps[nextHouse] || 0;
          
          if (currentCusp < nextCusp) {
            if (longitude >= currentCusp && longitude < nextCusp) {
              houseNumber = i;
              break;
            }
          } else {
            if (longitude >= currentCusp || longitude < nextCusp) {
              houseNumber = i;
              break;
            }
          }
        }
      }
      
      planets.push({
        name,
        symbol: this.getPlanetSymbol(name),
        longitude,
        sign: this.getSignFromDegree(longitude),
        house: houseNumber,
        sub_lord: subLord,
        sub_sub_lord: data.planet_sub_sub_lords?.[name] || ''
      });
    });

    // Transform cusp sub-lords
    Object.entries(data.cusp_sub_lords || {}).forEach(([house, subLord]) => {
      const longitude = chartData?.house_cusps?.[house] || 0;
      cusps.push({
        house: parseInt(house),
        longitude,
        sub_lord: subLord
      });
    });

    return { planets, cusps };
  }

  // Transform significators data to frontend format
  transformSignificatorsData(data) {
    const houses = [];

    // Transform significators by house
    for (let i = 1; i <= 12; i++) {
      const houseSignificators = data.significators[i] || [];
      const transformedSignificators = houseSignificators.map(sig => {
        // Parse significator string like "Mars (Star lord of Sun)"
        const match = sig.match(/^(\w+)\s*\((.+)\)$/);
        if (match) {
          const planet = match[1];
          const type = match[2].includes('Star lord') ? 'occupant' : 
                      match[2].includes('Sub lord') ? 'sub_lord' : 'owner';
          return { planet, type };
        }
        return { planet: sig, type: 'owner' };
      });
      
      houses.push({
        number: i,
        significators: transformedSignificators
      });
    }

    return { houses };
  }

  // Get zodiac sign from degree
  getSignFromDegree(degree) {
    const signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                   'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
    return signs[Math.floor(degree / 30)];
  }

  // Get planet symbol
  getPlanetSymbol(name) {
    const symbols = {
      'Sun': '☉', 'Moon': '☽', 'Mars': '♂', 'Mercury': '☿',
      'Jupiter': '♃', 'Venus': '♀', 'Saturn': '♄',
      'Rahu': '☊', 'Ketu': '☋'
    };
    return symbols[name] || name;
  }

  // Get sign lord from longitude
  getSignLord(longitude) {
    const signLords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury',
                      'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
    const signNum = Math.floor(longitude / 30);
    return signLords[signNum];
  }

  // Calculate sub-sub lord using KP method
  getSubSubLord(longitude, subLord) {
    // KP Vimshottari periods in years
    const periods = {
      'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7,
      'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17
    };
    
    const planetOrder = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'];
    
    // Get nakshatra info
    const nakshatra = this.getNakshatraFromDegree(longitude);
    const nakshatraLord = nakshatra.lord;
    
    // Position within nakshatra (0 to 13.333333 degrees)
    const nakshatraStart = Math.floor(longitude / 13.333333) * 13.333333;
    const positionInNakshatra = longitude - nakshatraStart;
    
    // Convert to minutes (800 minutes per nakshatra)
    const minutesInNakshatra = (positionInNakshatra / 13.333333) * 800;
    
    // Find sub-lord boundaries
    const nakshatraStartIndex = planetOrder.indexOf(nakshatraLord);
    let currentMinutes = 0;
    let subLordStartMinutes = 0;
    let subLordEndMinutes = 0;
    
    for (let i = 0; i < 9; i++) {
      const planet = planetOrder[(nakshatraStartIndex + i) % 9];
      const planetMinutes = (periods[planet] / 120) * 800; // Scale to 800 minutes
      
      if (planet === subLord) {
        subLordStartMinutes = currentMinutes;
        subLordEndMinutes = currentMinutes + planetMinutes;
        break;
      }
      currentMinutes += planetMinutes;
    }
    
    // Position within sub-lord period
    const minutesInSubLord = minutesInNakshatra - subLordStartMinutes;
    const subLordSpan = subLordEndMinutes - subLordStartMinutes;
    
    // Find sub-sub lord
    const subLordStartIndex = planetOrder.indexOf(subLord);
    let currentSubSubMinutes = 0;
    
    for (let i = 0; i < 9; i++) {
      const planet = planetOrder[(subLordStartIndex + i) % 9];
      const subSubMinutes = (periods[planet] / 120) * subLordSpan;
      
      if (minutesInSubLord >= currentSubSubMinutes && minutesInSubLord < currentSubSubMinutes + subSubMinutes) {
        return planet;
      }
      currentSubSubMinutes += subSubMinutes;
    }
    
    return subLord;
  }

  // Transform ruling planets data to frontend format
  transformRulingPlanetsData(data) {
    return {
      ascendant_sub_lord: data.ascendant?.sub_lord || '',
      moon_sign_sub_lord: data.moon?.sign_lord || '',
      moon_star_sub_lord: data.moon?.sub_lord || '',
      day_lord: data.day_lord || ''
    };
  }

  // Use backend sub-sub lord
  getSimpleSubSubLord(subLord) {
    // This will be replaced by backend calculation
    return 'Mercury'; // Temporary fallback
  }
}

export default new KPService();