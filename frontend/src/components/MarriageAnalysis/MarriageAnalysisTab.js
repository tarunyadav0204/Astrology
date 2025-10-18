import React, { useState, useEffect } from 'react';
import './MarriageAnalysisTab.css';
import { apiService } from '../../services/apiService';
import { 
  getHouseLordship, getFriendship, ownSigns, exaltationSigns, debilitationSigns,
  houseLords, getPlanetStatus, getPlanetDignity, getStatusColor, getNakshatraLord,
  getAspectingPlanets, analyzeSpecialConditions, calculateD9HouseStrength
} from '../../utils/planetAnalyzer';

const MarriageAnalysisTab = ({ chartData, birthDetails }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisType, setAnalysisType] = useState('single');

  useEffect(() => {
    if (chartData && birthDetails) {
      fetchMarriageAnalysis();
    }
  }, [chartData, birthDetails, analysisType]);

  const fetchMarriageAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.getMarriageAnalysis({
        chart_data: chartData,
        birth_details: birthDetails,
        analysis_type: analysisType
      });
      setAnalysis(response);
    } catch (err) {
      setError('Failed to fetch marriage analysis');
      console.error('Marriage analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="marriage-analysis-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Analyzing marriage prospects...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="marriage-analysis-container">
        <div className="error-state">
          <p>{error}</p>
          <button onClick={fetchMarriageAnalysis} className="retry-btn">
            Retry Analysis
          </button>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="marriage-analysis-container">
        <div className="no-data-state">
          <p>No marriage analysis available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="marriage-analysis-container">
      <div className="analysis-header">
        <h2>💍 Marriage Analysis</h2>
        <div className="analysis-type-selector">
          <button 
            className={`type-btn ${analysisType === 'single' ? 'active' : ''}`}
            onClick={() => setAnalysisType('single')}
          >
            Single Chart
          </button>
          <button 
            className={`type-btn ${analysisType === 'compatibility' ? 'active' : ''}`}
            onClick={() => setAnalysisType('compatibility')}
          >
            Compatibility
          </button>
        </div>
      </div>

      {analysisType === 'single' && (
        <SingleChartAnalysis analysis={analysis} chartData={chartData} birthDetails={birthDetails} />
      )}

      {analysisType === 'compatibility' && (
        <CompatibilityAnalysis analysis={analysis} />
      )}
    </div>
  );
};

const SingleChartAnalysis = ({ analysis, chartData, birthDetails }) => {
  const overallScore = analysis.overall_score || {};
  const seventhHouse = analysis.seventh_house_analysis || {};
  const karakas = analysis.karaka_analysis || {};
  const manglik = analysis.manglik_analysis || {};
  const d9Analysis = analysis.d9_analysis || {};
  
  // Get detailed analysis using shared utilities
  const ascendantSign = chartData?.houses?.[0]?.sign || 0;
  const seventhHouseIndex = 6;
  const seventhHouseSign = chartData?.houses?.[seventhHouseIndex]?.sign || 0;
  const seventhHouseLord = houseLords[seventhHouseSign];
  
  const analyzeKaraka = (planetName) => {
    const planetData = chartData?.planets?.[planetName];
    if (!planetData) return null;
    
    const lordships = getHouseLordship(planetName, ascendantSign);
    const dignity = getPlanetDignity(planetName, planetData.sign);
    const status = getPlanetStatus(planetName, planetData.sign, lordships);
    const nakshatraLord = getNakshatraLord(planetData.longitude);
    const friendshipWithNakLord = getFriendship(planetName, nakshatraLord);
    
    return {
      ...planetData,
      lordships,
      dignity,
      status,
      nakshatraLord,
      friendshipWithNakLord
    };
  };
  
  const seventhLordAnalysis = analyzeKaraka(seventhHouseLord);
  
  // Get conjunctions (planets in same sign)
  const getConjunctions = (planetName) => {
    const planetData = chartData?.planets?.[planetName];
    if (!planetData) return [];
    
    return Object.entries(chartData?.planets || {})
      .filter(([name, data]) => name !== planetName && data.sign === planetData.sign)
      .map(([name]) => name);
  };
  
  // Calculate Yoga Score at component level
  const calculateYogaScore = (kalatraYogas, beneficYogas, maleficYogas) => {
    let yogaScore = 0;
    
    // Kalatra Yogas (Marriage-specific) - Higher weightage
    kalatraYogas.forEach(yoga => {
      if (yoga.strength === 'Very Strong') yogaScore += 0.4;
      else if (yoga.strength === 'Strong') yogaScore += 0.3;
      else if (yoga.strength === 'Moderate') yogaScore += 0.2;
    });
    
    // Benefic Yogas - Moderate weightage
    beneficYogas.forEach(yoga => {
      if (yoga.strength === 'Very Strong') yogaScore += 0.3;
      else if (yoga.strength === 'Strong') yogaScore += 0.2;
      else if (yoga.strength === 'Moderate') yogaScore += 0.1;
    });
    
    // Malefic Yogas - Negative impact
    maleficYogas.forEach(yoga => {
      if (yoga.strength === 'Very Strong') yogaScore -= 0.4;
      else if (yoga.strength === 'Strong') yogaScore -= 0.3;
      else if (yoga.strength === 'Moderate') yogaScore -= 0.2;
    });
    
    // Cap the yoga score between -1.5 and +1.5
    return Math.max(-1.5, Math.min(1.5, yogaScore));
  };
  
  // Calculate comprehensive yoga score upfront - copy from full yoga analysis
  const calculateComprehensiveYogaScore = () => {
    const beneficYogas = [];
    const maleficYogas = [];
    const kalatraYogas = [];
    
    // Get planet positions
    const venusData = chartData?.planets?.['Venus'];
    const jupiterData = chartData?.planets?.['Jupiter'];
    const moonData = chartData?.planets?.['Moon'];
    const marsData = chartData?.planets?.['Mars'];
    const sunData = chartData?.planets?.['Sun'];
    const saturnData = chartData?.planets?.['Saturn'];
    const mercuryData = chartData?.planets?.['Mercury'];
    const rahuData = chartData?.planets?.['Rahu'];
    const ketuData = chartData?.planets?.['Ketu'];
    
    // Helper function to get house number from sign
    const getHouseFromSign = (sign) => chartData?.houses?.findIndex(house => house.sign === sign) + 1;
    
    // KALATRA YOGAS (Specific Marriage Yogas)
    
    // 1. Kalatra Karaka Yoga - Venus exalted/own sign in 7th
    if (venusData) {
      const venusHouse = getHouseFromSign(venusData.sign);
      const venusDignity = getPlanetDignity('Venus', venusData.sign);
      if (venusHouse === 7 && (venusDignity === 'Exalted' || venusDignity === 'Own')) {
        kalatraYogas.push({ strength: 'Very Strong' });
      }
    }
    
    // 2. Shubha Kalatra Yoga - 7th lord with benefics
    if (seventhLordAnalysis) {
      const conjunctions = getConjunctions(seventhHouse.house_lord);
      const beneficConjunctions = conjunctions.filter(p => ['Jupiter', 'Venus', 'Moon'].includes(p));
      if (beneficConjunctions.length > 0) {
        kalatraYogas.push({ strength: 'Strong' });
      }
    }
    
    // 3. Dhana Kalatra Yoga - 7th lord in 2nd/11th house
    if (seventhLordAnalysis) {
      const seventhLordHouse = getHouseFromSign(seventhLordAnalysis.sign);
      if ([2, 11].includes(seventhLordHouse)) {
        kalatraYogas.push({ strength: 'Strong' });
      }
    }
    
    // BENEFIC YOGAS ENHANCING MARRIAGE
    
    // 1. Gajakesari Yoga - Jupiter-Moon conjunction/aspect
    if (jupiterData && moonData) {
      const jupiterHouse = getHouseFromSign(jupiterData.sign);
      const moonHouse = getHouseFromSign(moonData.sign);
      const isConjunct = jupiterData.sign === moonData.sign;
      const isAspect = Math.abs(jupiterHouse - moonHouse) === 6 || 
                      (jupiterHouse + 4) % 12 + 1 === moonHouse || 
                      (jupiterHouse + 8) % 12 + 1 === moonHouse;
      
      if (isConjunct || isAspect) {
        beneficYogas.push({ strength: 'Strong' });
      }
    }
    
    // 2. Malavya Yoga - Venus in Kendra in own/exaltation
    if (venusData) {
      const venusHouse = getHouseFromSign(venusData.sign);
      const venusDignity = getPlanetDignity('Venus', venusData.sign);
      if ([1, 4, 7, 10].includes(venusHouse) && (venusDignity === 'Exalted' || venusDignity === 'Own')) {
        beneficYogas.push({ strength: 'Very Strong' });
      }
    }
    
    // 3. Hamsa Yoga - Jupiter in Kendra in own/exaltation
    if (jupiterData) {
      const jupiterHouse = getHouseFromSign(jupiterData.sign);
      const jupiterDignity = getPlanetDignity('Jupiter', jupiterData.sign);
      if ([1, 4, 7, 10].includes(jupiterHouse) && (jupiterDignity === 'Exalted' || jupiterDignity === 'Own')) {
        beneficYogas.push({ strength: 'Very Strong' });
      }
    }
    
    // 4. Raj Yoga - Kendra-Trikona lords together
    const kendraLords = [1, 4, 7, 10].map(h => houseLords[chartData?.houses?.[h-1]?.sign || 0]);
    const trikonaLords = [1, 5, 9].map(h => houseLords[chartData?.houses?.[h-1]?.sign || 0]);
    
    Object.entries(chartData?.planets || {}).forEach(([planet1, data1]) => {
      if (!kendraLords.includes(planet1)) return;
      const conjunctions = getConjunctions(planet1);
      conjunctions.forEach(planet2 => {
        if (trikonaLords.includes(planet2)) {
          beneficYogas.push({ strength: 'Strong' });
        }
      });
    });
    
    // MALEFIC YOGAS CAUSING DELAYS/PROBLEMS
    
    // 1. Manglik Dosha
    if (manglik.is_manglik) {
      maleficYogas.push({ strength: manglik.severity === 'High' ? 'Very Strong' : 'Moderate' });
    }
    
    // 2. Kala Sarpa Yoga - All planets between Rahu-Ketu
    if (rahuData && ketuData) {
      const rahuSign = rahuData.sign;
      const ketuSign = ketuData.sign;
      const planetsBetween = Object.entries(chartData?.planets || {})
        .filter(([name, data]) => !['Rahu', 'Ketu'].includes(name))
        .every(([name, data]) => {
          const planetSign = data.sign;
          return (rahuSign < ketuSign) ? 
            (planetSign > rahuSign && planetSign < ketuSign) :
            (planetSign > rahuSign || planetSign < ketuSign);
        });
      
      if (planetsBetween) {
        maleficYogas.push({ strength: 'Strong' });
      }
    }
    
    // 3. Shani Dosha - Saturn in 7th house
    if (saturnData) {
      const saturnHouse = getHouseFromSign(saturnData.sign);
      if (saturnHouse === 7) {
        maleficYogas.push({ strength: 'Moderate' });
      }
    }
    
    // 4. Guru Chandal Yoga - Jupiter with Rahu
    if (jupiterData && rahuData && jupiterData.sign === rahuData.sign) {
      maleficYogas.push({ strength: 'Moderate' });
    }
    
    // 5. Papakartari Yoga - 7th house hemmed by malefics
    const seventhHouseSign = chartData?.houses?.[6]?.sign || 0;
    const sixthHouseSign = chartData?.houses?.[5]?.sign || 0;
    const eighthHouseSign = chartData?.houses?.[7]?.sign || 0;
    
    const maleficsIn6th = Object.entries(chartData?.planets || {})
      .filter(([name, data]) => ['Mars', 'Saturn', 'Rahu', 'Ketu'].includes(name) && data.sign === sixthHouseSign)
      .map(([name]) => name);
    
    const maleficsIn8th = Object.entries(chartData?.planets || {})
      .filter(([name, data]) => ['Mars', 'Saturn', 'Rahu', 'Ketu'].includes(name) && data.sign === eighthHouseSign)
      .map(([name]) => name);
    
    if (maleficsIn6th.length > 0 && maleficsIn8th.length > 0) {
      maleficYogas.push({ strength: 'Strong' });
    }
    
    return calculateYogaScore(kalatraYogas, beneficYogas, maleficYogas);
  };
  
  const yogaData = { yogaScore: calculateComprehensiveYogaScore() };
  
  // Calculate Darakarka (planet with lowest degree)
  const getDarakarka = () => {
    let lowestDegree = 360;
    let darakarka = null;
    
    Object.entries(chartData?.planets || {}).forEach(([name, data]) => {
      if (!['Rahu', 'Ketu'].includes(name)) {
        const degreeInSign = data.longitude % 30;
        if (degreeInSign < lowestDegree) {
          lowestDegree = degreeInSign;
          darakarka = name;
        }
      }
    });
    
    return darakarka;
  };
  
  const darakarka = getDarakarka();
  
  // Calculate frontend overall score using all components
  const calculateFrontendOverallScore = () => {
    const seventhScore = (seventhHouse.strength_score || 0) / 100 * 3.0; // Max 3.0
    const venusScore = (karakas.venus?.strength || 0) / 10 * 1.5; // Max 1.5
    const jupiterScore = (karakas.jupiter?.strength || 0) / 10 * 1.0; // Max 1.0
    // Get darakarka strength - try from karakas first, then calculate from chart data
    const darakarkaStrength = karakas[darakarka?.toLowerCase()]?.strength || 
                              (darakarka && chartData?.planets?.[darakarka] ? 
                               Math.min(10, Math.max(1, 5 + (getPlanetDignity(darakarka, chartData.planets[darakarka].sign) === 'Exalted' ? 3 : 
                                                                getPlanetDignity(darakarka, chartData.planets[darakarka].sign) === 'Own' ? 2 : 
                                                                getPlanetDignity(darakarka, chartData.planets[darakarka].sign) === 'Debilitated' ? -3 : 0))) : 0);
    const darakarkaScore = darakarkaStrength / 10 * 0.5; // Max 0.5
    const yogaScore = yogaData.yogaScore; // Max 1.5
    const d9Score = (d9Analysis?.overall_strength || 0) / 10 * 2.0; // Max 2.0
    
    const manglikPenalty = manglik.is_manglik ? 
      (manglik.severity === 'High' ? 1.5 : 0.8) : 0;
    
    const totalScore = seventhScore + venusScore + jupiterScore + darakarkaScore + yogaScore + d9Score - manglikPenalty;
    const finalScore = Math.max(0, Math.min(10, totalScore));
    
    return {
      score: Math.round(finalScore * 10) / 10,
      percentage: Math.round((finalScore / 10) * 100 * 10) / 10,
      components: {
        seventh_house_d1: Math.round(seventhScore * 10) / 10,
        venus_d1: Math.round(venusScore * 10) / 10,
        jupiter_d1: Math.round(jupiterScore * 10) / 10,
        darakarka: Math.round(darakarkaScore * 10) / 10,
        yoga_score: Math.round(yogaScore * 10) / 10,
        d9_strength: Math.round(d9Score * 10) / 10,
        manglik_penalty: manglikPenalty
      }
    };
  };
  
  const frontendOverallScore = calculateFrontendOverallScore();
  
  const signNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
  
  const getDignityExplanation = (planet, sign, longitude = null) => {
    const dignity = getPlanetDignity(planet, sign);
    const signName = signNames[sign];
    
    let signDignity = '';
    if (dignity === 'Exalted') {
      signDignity = `Exalted in ${signName}`;
    } else if (dignity === 'Debilitated') {
      signDignity = `Debilitated in ${signName}`;
    } else if (dignity === 'Own') {
      signDignity = `Own sign ${signName}`;
    } else {
      const signLord = houseLords[sign];
      const friendship = getFriendship(planet, signLord);
      signDignity = friendship === 'Friend' ? `Friend's sign ${signName}` : 
                   friendship === 'Enemy' ? `Enemy's sign ${signName}` : 
                   `Neutral in ${signName}`;
    }
    
    // Add nakshatra dignity if longitude is provided
    if (longitude !== null) {
      const nakshatraLord = getNakshatraLord(longitude);
      const nakFriendship = getFriendship(planet, nakshatraLord);
      const nakStatus = nakFriendship === 'Friend' ? 'Supportive Nak' : 
                       nakFriendship === 'Enemy' ? 'Challenging Nak' : 'Neutral Nak';
      return `${signDignity} • ${nakStatus}`;
    }
    
    return signDignity;
  };
  
  const planetsIn7th = Object.entries(chartData?.planets || {}).filter(
    ([name, data]) => data.sign === seventhHouseSign
  ).map(([name]) => name);
  
  const aspectingPlanets = getAspectingPlanets(seventhHouseIndex, chartData);
  
  const venusAnalysis = analyzeKaraka('Venus');
  const jupiterAnalysis = analyzeKaraka('Jupiter');
  const marsAnalysis = analyzeKaraka('Mars');
  

  
  // Get aspects to a planet
  const getAspectsTo = (planetName) => {
    const planetData = chartData?.planets?.[planetName];
    if (!planetData) return [];
    
    const aspects = [];
    const planetSign = planetData.sign;
    
    Object.entries(chartData?.planets || {}).forEach(([name, data]) => {
      if (name === planetName) return;
      
      // 7th aspect (opposition)
      const aspectSign = (data.sign + 6) % 12;
      if (aspectSign === planetSign) {
        aspects.push({ planet: name, aspect: '7th' });
      }
      
      // Special aspects
      if (name === 'Mars') {
        const fourthAspect = (data.sign + 3) % 12;
        const eighthAspect = (data.sign + 7) % 12;
        if (fourthAspect === planetSign) aspects.push({ planet: name, aspect: '4th' });
        if (eighthAspect === planetSign) aspects.push({ planet: name, aspect: '8th' });
      } else if (name === 'Jupiter') {
        const fifthAspect = (data.sign + 4) % 12;
        const ninthAspect = (data.sign + 8) % 12;
        if (fifthAspect === planetSign) aspects.push({ planet: name, aspect: '5th' });
        if (ninthAspect === planetSign) aspects.push({ planet: name, aspect: '9th' });
      } else if (name === 'Saturn') {
        const thirdAspect = (data.sign + 2) % 12;
        const tenthAspect = (data.sign + 9) % 12;
        if (thirdAspect === planetSign) aspects.push({ planet: name, aspect: '3rd' });
        if (tenthAspect === planetSign) aspects.push({ planet: name, aspect: '10th' });
      }
    });
    
    return aspects;
  };
  
  // Check special conditions (Yogi, Avayogi, Dagdha, Tithi Shunya)
  const checkSpecialConditions = (sign) => {
    // This would need yogiData from API - placeholder for now
    return {
      isYogi: false,
      isAvayogi: false,
      isDagdha: false,
      isTithiShunya: false
    };
  };

  return (
    <div className="single-chart-analysis">
      {/* Overall Score Card */}
      <div className="score-card">
        <div className="score-header">
          <h3>Marriage Prospects Score</h3>
          <div className="score-display">
            <span className="score-number">{frontendOverallScore.score}</span>
            <span className="score-max">/10</span>
          </div>
        </div>
        <div className="score-bar">
          <div 
            className="score-fill" 
            style={{ width: `${frontendOverallScore.percentage}%` }}
          ></div>
        </div>
        <div className="score-grade">{frontendOverallScore.score >= 8.5 ? 'Excellent' : frontendOverallScore.score >= 7.0 ? 'Very Good' : frontendOverallScore.score >= 5.5 ? 'Good' : frontendOverallScore.score >= 4.0 ? 'Average' : 'Below Average'}</div>
        
        {/* Score Breakdown */}
        <div className="score-breakdown">
          <h4 className="score-breakdown-title">📊 Score Breakdown</h4>
          <div className="score-breakdown-grid">
            <div className="score-breakdown-item">
              <span className="score-label">🏠 D1 7th House:</span>
              <span className="score-value">{frontendOverallScore.components.seventh_house_d1}/3.0</span>
              <div className="score-details">
                <small>({seventhHouse.strength_score || 0}/100 → {frontendOverallScore.components.seventh_house_d1})</small>
              </div>
            </div>
            <div className="score-breakdown-item">
              <span className="score-label">♀ D1 Venus:</span>
              <span className="score-value">{frontendOverallScore.components.venus_d1}/1.5</span>
              <div className="score-details">
                <small>({karakas.venus?.strength || 0}/10 → {frontendOverallScore.components.venus_d1})</small>
              </div>
            </div>
            <div className="score-breakdown-item">
              <span className="score-label">♃ D1 Jupiter:</span>
              <span className="score-value">{frontendOverallScore.components.jupiter_d1}/1.0</span>
              <div className="score-details">
                <small>({karakas.jupiter?.strength || 0}/10 → {frontendOverallScore.components.jupiter_d1})</small>
              </div>
            </div>
            <div className="score-breakdown-item">
              <span className="score-label">🎯 Darakarka ({darakarka}):</span>
              <span className="score-value">{frontendOverallScore.components.darakarka}/0.5</span>
              <div className="score-details">
                <small>({(() => {
                  const darakarkaStrength = karakas[darakarka?.toLowerCase()]?.strength || 
                                            (darakarka && chartData?.planets?.[darakarka] ? 
                                             Math.min(10, Math.max(1, 5 + (getPlanetDignity(darakarka, chartData.planets[darakarka].sign) === 'Exalted' ? 3 : 
                                                                            getPlanetDignity(darakarka, chartData.planets[darakarka].sign) === 'Own' ? 2 : 
                                                                            getPlanetDignity(darakarka, chartData.planets[darakarka].sign) === 'Debilitated' ? -3 : 0))) : 0);
                  return darakarkaStrength;
                })()}/10 → {frontendOverallScore.components.darakarka})</small>
              </div>
            </div>
            <div className="score-breakdown-item">
              <span className="score-label">🕉️ Marriage Yogas:</span>
              <span className="score-value" style={{ color: frontendOverallScore.components.yoga_score >= 0 ? '#4caf50' : '#f44336' }}>{frontendOverallScore.components.yoga_score >= 0 ? '+' : ''}{frontendOverallScore.components.yoga_score}/1.5</span>
            </div>
            <div className="score-breakdown-item">
              <span className="score-label">🌟 D9 Navamsa:</span>
              <span className="score-value">{frontendOverallScore.components.d9_strength}/2.0</span>
              <div className="score-details">
                <small>({d9Analysis?.overall_strength || 0}/10 → {frontendOverallScore.components.d9_strength})</small>
              </div>
            </div>
            <div className="score-breakdown-item manglik-status-item">
              <span className="score-label">🔥 Manglik Status:</span>
              <div className="manglik-compact">
                <span className={`manglik-indicator ${manglik.is_manglik ? 'manglik' : 'non-manglik'}`}>
                  {manglik.is_manglik ? `${manglik.severity} Manglik` : 'Non-Manglik'}
                </span>
                <span className="score-value" style={{ color: manglik.is_manglik ? '#f44336' : '#4caf50' }}>
                  {manglik.is_manglik ? `-${frontendOverallScore.components.manglik_penalty}` : '+0.0'}
                </span>
                {manglik.is_manglik && (
                  <div className="manglik-details-compact">
                    <span>Mars in {manglik.mars_house}th house</span>
                    {manglik.cancellation?.has_cancellation && <span className="cancellation-note">• Cancellation present</span>}
                  </div>
                )}
              </div>
            </div>
            <div className="score-breakdown-item">
              <span className="score-label">📊 D1 Total:</span>
              <span className="score-value">{(frontendOverallScore.components.seventh_house_d1 + frontendOverallScore.components.venus_d1 + frontendOverallScore.components.jupiter_d1 + frontendOverallScore.components.yoga_score).toFixed(1)}/7.0</span>
            </div>
            <div className="score-breakdown-item">
              <span className="score-label">🌟 D9 Total:</span>
              <span className="score-value">{frontendOverallScore.components.d9_strength}/2.5</span>
            </div>
          </div>
          <div className="score-formula">
            <div className="formula-title">📋 Enhanced Parasara Formula (D9 Weight: 30%):</div>
            <div className="formula-text">
              <strong>Formula:</strong> 7th House + Venus + Jupiter + Darakarka + Yogas + D9 Navamsa - Manglik Penalty<br/>
              <strong>Calculation:</strong> {frontendOverallScore.components.seventh_house_d1} + {frontendOverallScore.components.venus_d1} + {frontendOverallScore.components.jupiter_d1} + {frontendOverallScore.components.darakarka} + {frontendOverallScore.components.yoga_score >= 0 ? frontendOverallScore.components.yoga_score : `(${frontendOverallScore.components.yoga_score})`} + {frontendOverallScore.components.d9_strength}{frontendOverallScore.components.manglik_penalty > 0 ? ` - ${frontendOverallScore.components.manglik_penalty}` : ' - 0'} = <strong>{frontendOverallScore.score}/10</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Simple Explanation for Laymen */}
      <div className="analysis-section">
        <h3>📖 What This Analysis Means (Simple Explanation)</h3>
        <div className="layman-explanation">
          <div className="explanation-card">
            <h4>🎯 Your Marriage Score: {frontendOverallScore.score}/10</h4>
            <div className="score-meaning">
              {frontendOverallScore.score >= 8 ? (
                <div className="meaning excellent">
                  <span className="meaning-icon">🌟</span>
                  <div className="meaning-text">
                    <strong>Excellent Marriage Prospects!</strong>
                    <p>Your birth chart shows very strong indicators for a happy and harmonious marriage. The planets are well-positioned to bring you a loving, compatible partner.</p>
                  </div>
                </div>
              ) : frontendOverallScore.score >= 6.5 ? (
                <div className="meaning good">
                  <span className="meaning-icon">😊</span>
                  <div className="meaning-text">
                    <strong>Good Marriage Prospects</strong>
                    <p>Your chart shows positive signs for marriage. With some effort and the right timing, you can find a good life partner and build a happy relationship.</p>
                  </div>
                </div>
              ) : frontendOverallScore.score >= 5 ? (
                <div className="meaning average">
                  <span className="meaning-icon">🤔</span>
                  <div className="meaning-text">
                    <strong>Average Marriage Prospects</strong>
                    <p>Your chart shows mixed signals. Marriage is possible, but you may need to work harder on relationships or consider remedies to improve compatibility.</p>
                  </div>
                </div>
              ) : (
                <div className="meaning challenging">
                  <span className="meaning-icon">💪</span>
                  <div className="meaning-text">
                    <strong>Marriage Needs Extra Care</strong>
                    <p>Your chart suggests some challenges in marriage. Don't worry - with proper guidance, remedies, and patience, you can still find happiness in relationships.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <div className="explanation-grid">
            <div className="explanation-item">
              <span className="item-icon">🏠</span>
              <div className="item-content">
                <h5>Your 7th House: {seventhHouse.strength_score >= 70 ? 'Excellent' : seventhHouse.strength_score >= 50 ? 'Good' : seventhHouse.strength_score >= 30 ? 'Weak' : 'Very Weak'} ({seventhHouse.strength_score}/100)</h5>
                <p>{seventhHouse.strength_score >= 70 ? 
                  'Your marriage area is very strong! You have natural ability to attract and maintain good relationships. Marriage will likely be harmonious.' :
                  seventhHouse.strength_score >= 50 ?
                  'Your marriage area is reasonably good. With some effort, you can build a stable and happy marriage.' :
                  seventhHouse.strength_score >= 30 ?
                  'Your marriage area needs attention. You may face some challenges in relationships, but they can be overcome with proper remedies and patience.' :
                  'Your marriage area is quite challenging. You will need to work harder on relationships and may benefit from astrological remedies to strengthen this area.'}</p>
              </div>
            </div>
            
            <div className="explanation-item">
              <span className="item-icon">♀</span>
              <div className="item-content">
                <h5>Your Venus: {karakas.venus?.strength >= 7 ? 'Strong' : karakas.venus?.strength >= 6 ? 'Average' : karakas.venus?.strength >= 3 ? 'Weak' : 'Very Weak'} ({karakas.venus?.strength || 0}/10)</h5>
                <p>{karakas.venus?.strength >= 7 ? 
                  'You have excellent romantic energy! You naturally attract love and will have good chemistry with your partner. Your marriage will be filled with affection and beauty.' :
                  karakas.venus?.strength >= 6 ?
                  'Your romantic nature is decent. You can experience good love and attraction, though it may take some time to find the right person.' :
                  karakas.venus?.strength >= 3 ?
                  'Your romantic side needs strengthening. You may struggle with expressing love or attracting the right partner. Venus remedies will help significantly.' :
                  'Your love life faces serious challenges. You may have difficulty in romantic relationships or feel unloved. Strong Venus remedies are essential for marriage success.'}</p>
              </div>
            </div>
            
            <div className="explanation-item">
              <span className="item-icon">♃</span>
              <div className="item-content">
                <h5>Your Jupiter: {karakas.jupiter?.strength >= 7 ? 'Strong' : karakas.jupiter?.strength >= 6 ? 'Average' : karakas.jupiter?.strength >= 3 ? 'Weak' : 'Very Weak'} ({karakas.jupiter?.strength || 0}/10)</h5>
                <p>{karakas.jupiter?.strength >= 7 ? 
                  'You have excellent wisdom for marriage! You will make good decisions about your life partner and have a spiritually fulfilling relationship with divine blessings.' :
                  karakas.jupiter?.strength >= 6 ?
                  'Your marriage wisdom is reasonable. You generally make good relationship decisions, though you may need guidance in some areas.' :
                  karakas.jupiter?.strength >= 3 ?
                  'Your marriage judgment needs improvement. You may make poor relationship choices or lack wisdom in marriage matters. Jupiter remedies will help.' :
                  'You face serious challenges in marriage wisdom. You may repeatedly choose wrong partners or make bad marriage decisions. Strong Jupiter remedies are crucial.'}</p>
              </div>
            </div>
            
            <div className="explanation-item">
              <span className="item-icon">🌟</span>
              <div className="item-content">
                <h5>Your D9 Soul Chart: {d9Analysis?.overall_strength >= 7 ? 'Excellent' : d9Analysis?.overall_strength >= 5 ? 'Good' : d9Analysis?.overall_strength >= 3 ? 'Weak' : 'Very Weak'} ({d9Analysis?.overall_strength || 0}/10)</h5>
                <p>{d9Analysis?.overall_strength >= 7 ? 
                  'Your soul connection with your spouse will be amazing! You will understand each other deeply and have a truly fulfilling marriage that satisfies your inner desires.' :
                  d9Analysis?.overall_strength >= 5 ?
                  'Your soul connection with your spouse will be good. You will generally understand each other well and have a satisfying marriage.' :
                  d9Analysis?.overall_strength >= 3 ?
                  'Your soul connection may be challenging. You and your spouse might not understand each other deeply, leading to some dissatisfaction in marriage.' :
                  'Your soul connection faces serious issues. You may feel emotionally disconnected from your spouse or unfulfilled in marriage. Spiritual practices are essential.'}</p>
              </div>
            </div>
            
            {manglik.is_manglik && (
              <div className="explanation-item manglik-explanation">
                <span className="item-icon">🔥</span>
                <div className="item-content">
                  <h5>Your Manglik Status: {manglik.severity === 'High' ? 'High Risk' : 'Manageable'}</h5>
                  <p>{manglik.severity === 'High' ? 
                    'You have strong Mars energy that can create conflicts in marriage. This is serious and requires either marrying another Manglik person or performing specific rituals before marriage.' :
                    'You have mild Mars energy that may cause some initial friction in marriage. This is easily manageable with simple remedies like fasting on Tuesdays or prayers to Hanuman ji.'}</p>
                </div>
              </div>
            )}
          </div>
          
          <div className="simple-recommendations">
            <h4>💡 What You Can Do</h4>
            <div className="simple-rec-list">
              {(() => {
                const recommendations = [];
                
                // Specific recommendations based on actual chart problems
                if (seventhHouse.strength_score < 50) {
                  const houseLord = seventhHouse.house_lord;
                  const gemstones = {
                    'Sun': 'Ruby', 'Moon': 'Pearl', 'Mars': 'Red Coral', 'Mercury': 'Emerald',
                    'Jupiter': 'Yellow Sapphire', 'Venus': 'Diamond', 'Saturn': 'Blue Sapphire'
                  };
                  recommendations.push({
                    icon: '🏠',
                    text: `Your 7th house is weak (${seventhHouse.strength_score}/100). Strengthen ${houseLord} by wearing ${gemstones[houseLord] || 'appropriate gemstone'} or chanting ${houseLord} mantras.`,
                    type: 'challenging'
                  });
                }
                
                if (karakas.venus?.strength < 6) {
                  recommendations.push({
                    icon: '💎',
                    text: `Venus is weak (${karakas.venus.strength}/10). Wear diamond/white sapphire, donate white clothes on Fridays, and avoid relationships on Fridays.`,
                    type: 'challenging'
                  });
                }
                
                if (karakas.jupiter?.strength < 6) {
                  recommendations.push({
                    icon: '📿',
                    text: `Jupiter is weak (${karakas.jupiter.strength}/10). Wear yellow sapphire, visit temples on Thursdays, respect teachers, and donate yellow items.`,
                    type: 'challenging'
                  });
                }
                
                if (manglik.is_manglik) {
                  const severity = manglik.severity;
                  if (severity === 'High') {
                    recommendations.push({
                      icon: '🔥',
                      text: `Strong Manglik dosha detected. Essential: Marry another Manglik, perform Mangal Shanti puja, or do Kumbh Vivah ritual before marriage.`,
                      type: 'challenging'
                    });
                  } else {
                    recommendations.push({
                      icon: '🕯️',
                      text: `Mild Manglik dosha present. Remedy: Fast on Tuesdays, offer red flowers to Hanuman ji, and recite Hanuman Chalisa daily.`,
                      type: 'neutral'
                    });
                  }
                }
                
                if (d9Analysis && d9Analysis.overall_strength < 5) {
                  recommendations.push({
                    icon: '🌟',
                    text: `D9 chart is weak (${d9Analysis.overall_strength}/10). Focus on spiritual practices, meditation, and character development before marriage.`,
                    type: 'neutral'
                  });
                }
                
                // Check for specific planetary afflictions
                const venusAnalysisCheck = analyzeKaraka('Venus');
                if (venusAnalysisCheck && venusAnalysisCheck.dignity === 'Debilitated') {
                  recommendations.push({
                    icon: '💔',
                    text: 'Venus is debilitated in Virgo. Remedy: Worship Goddess Lakshmi, donate to unmarried girls, and avoid being overly critical in relationships.',
                    type: 'challenging'
                  });
                }
                
                const jupiterAnalysisCheck = analyzeKaraka('Jupiter');
                if (jupiterAnalysisCheck && jupiterAnalysisCheck.dignity === 'Debilitated') {
                  recommendations.push({
                    icon: '📚',
                    text: 'Jupiter is debilitated in Capricorn. Remedy: Respect elders and teachers, donate books/education materials, and study spiritual texts.',
                    type: 'challenging'
                  });
                }
                
                // Check for 7th house lord placement
                if (seventhLordAnalysis) {
                  const seventhLordHouse = chartData?.houses?.findIndex(house => house.sign === seventhLordAnalysis.sign) + 1;
                  if ([6, 8, 12].includes(seventhLordHouse)) {
                    recommendations.push({
                      icon: '👑',
                      text: `7th lord ${seventhHouse.house_lord} is in ${seventhLordHouse}th house (challenging). Strengthen it through specific mantras and gemstone therapy.`,
                      type: 'challenging'
                    });
                  }
                }
                
                // Positive recommendations for strong planets
                if (d9Analysis && d9Analysis.venus_d9?.strength >= 7 && karakas.venus?.strength < 5) {
                  recommendations.push({
                    icon: '💕',
                    text: `Excellent! Venus is strong in D9 (${d9Analysis.venus_d9.strength}/10). Your marriage will bring deep fulfillment despite initial challenges.`,
                    type: 'positive'
                  });
                }
                
                if (d9Analysis && d9Analysis.jupiter_d9?.strength >= 7) {
                  recommendations.push({
                    icon: '🙏',
                    text: `Jupiter is powerful in D9 (${d9Analysis.jupiter_d9.strength}/10). You'll find a wise, spiritual partner. Continue dharmic practices.`,
                    type: 'positive'
                  });
                }
                
                // Specific timing based on actual planetary weaknesses
                if (overallScore.score >= 7) {
                  const strongPlanets = [];
                  if (karakas.venus?.strength >= 7) strongPlanets.push('Venus');
                  if (karakas.jupiter?.strength >= 7) strongPlanets.push('Jupiter');
                  if (seventhHouse.strength_score >= 70) strongPlanets.push('7th house');
                  
                  recommendations.push({
                    icon: '⏰',
                    text: `Excellent prospects (${overallScore.score}/10) with strong ${strongPlanets.join(', ')}. Best timing: Venus periods, Thursday/Friday ceremonies, spring/autumn seasons.`,
                    type: 'positive'
                  });
                } else if (overallScore.score >= 5) {
                  const weakAreas = [];
                  if (karakas.venus?.strength < 6) weakAreas.push(`Venus (${karakas.venus.strength}/10)`);
                  if (karakas.jupiter?.strength < 6) weakAreas.push(`Jupiter (${karakas.jupiter.strength}/10)`);
                  if (seventhHouse.strength_score < 50) weakAreas.push(`7th house (${seventhHouse.strength_score}/100)`);
                  
                  recommendations.push({
                    icon: '🔍',
                    text: `Moderate prospects (${overallScore.score}/10). Weak: ${weakAreas.join(', ')}. Strategy: 6-month remedial period targeting these areas, then arranged meetings during favorable transits.`,
                    type: 'neutral'
                  });
                } else {
                  const criticalIssues = [];
                  
                  if ((karakas.venus?.strength || 0) < 6) criticalIssues.push(`Venus weak (${karakas.venus?.strength || 0}/10)`);
                  if ((karakas.jupiter?.strength || 0) < 6) criticalIssues.push(`Jupiter weak (${karakas.jupiter?.strength || 0}/10)`);
                  if ((seventhHouse.strength_score || 0) < 50) criticalIssues.push(`7th house weak (${seventhHouse.strength_score || 0}/100)`);
                  if (manglik.is_manglik) criticalIssues.push(`Manglik dosha present`);
                  
                  // Add 7th lord placement issues
                  if (seventhLordAnalysis) {
                    const seventhLordHouse = chartData?.houses?.findIndex(house => house.sign === seventhLordAnalysis.sign) + 1;
                    if ([6, 8, 12].includes(seventhLordHouse)) {
                      criticalIssues.push(`7th lord ${seventhHouse.house_lord} in ${seventhLordHouse}th house`);
                    }
                  }
                  
                  // Add debilitation issues
                  const venusAnalysisLocal = analyzeKaraka('Venus');
                  if (venusAnalysisLocal && venusAnalysisLocal.dignity === 'Debilitated') {
                    criticalIssues.push('Venus debilitated in Virgo');
                  }
                  
                  const jupiterAnalysisLocal = analyzeKaraka('Jupiter');
                  if (jupiterAnalysisLocal && jupiterAnalysisLocal.dignity === 'Debilitated') {
                    criticalIssues.push('Jupiter debilitated in Capricorn');
                  }
                  
                  const currentAge = birthDetails?.date_of_birth ? new Date().getFullYear() - new Date(birthDetails.date_of_birth).getFullYear() : 25;
                  
                  // Astrological timing based on planetary maturity and Saturn cycles
                  let suggestedAge;
                  if (manglik.is_manglik && manglik.severity === 'High') {
                    // High Manglik: After Mars maturity (28) + remedial period
                    suggestedAge = Math.max(currentAge + 2, 30);
                  } else if ((karakas.venus?.strength || 0) < 2 && (karakas.jupiter?.strength || 0) < 2) {
                    // Both Venus & Jupiter critically weak: After Saturn return (29.5 years)
                    suggestedAge = Math.max(currentAge + 2, 30);
                  } else if ((seventhHouse.strength_score || 0) < 20) {
                    // 7th house severely damaged: After planetary maturity
                    suggestedAge = Math.max(currentAge + 3, 32);
                  } else {
                    // General challenging chart: After Venus maturity (25) + remedial time
                    suggestedAge = Math.max(currentAge + 2, 27);
                  }
                  
                  const remedialPeriod = manglik.is_manglik && manglik.severity === 'High' ? '24-36 months' : 
                                        ((karakas.venus?.strength || 0) < 2 || (karakas.jupiter?.strength || 0) < 2) ? '18-24 months' : '12-18 months';
                  
                  const astrologicalReason = manglik.is_manglik && manglik.severity === 'High' ? 'after Mars maturity (28) and Manglik remedies' :
                                            ((karakas.venus?.strength || 0) < 2 && (karakas.jupiter?.strength || 0) < 2) ? 'after Saturn return (30) when planets mature' :
                                            (seventhHouse.strength_score || 0) < 20 ? 'after 7th house strengthening and planetary maturity' :
                                            'after Venus maturity (25) and remedial completion';
                  

                  
                  recommendations.push({
                    icon: '⏳',
                    text: `Critical chart (${overallScore.score}/10). Issues: ${criticalIssues.join(', ')}. Required: ${remedialPeriod} intensive remedial program, marriage ${astrologicalReason} during favorable planetary periods.`,
                    type: 'challenging'
                  });
                }
                
                // Specific favorable periods based on planetary strengths
                if (overallScore.score >= 6 && recommendations.filter(r => r.type === 'challenging').length <= 1) {
                  const favorablePeriods = [];
                  if (karakas.venus?.strength >= 6) favorablePeriods.push('Venus Mahadasha/Antardasha');
                  if (karakas.jupiter?.strength >= 6) favorablePeriods.push('Jupiter periods');
                  if (seventhHouse.strength_score >= 60) favorablePeriods.push(`${seventhHouse.house_lord} periods`);
                  
                  recommendations.push({
                    icon: '✨',
                    text: `Good chart (${overallScore.score}/10). Best marriage timing: ${favorablePeriods.length > 0 ? favorablePeriods.join(' or ') : 'Venus/Jupiter favorable transits'}. Continue spiritual practices for optimal results.`,
                    type: 'positive'
                  });
                }
                
                return recommendations.map((rec, index) => (
                  <div key={index} className={`simple-rec-item ${rec.type}`}>
                    <span className="rec-icon">{rec.icon}</span>
                    <span>{rec.text}</span>
                  </div>
                ));
              })()}
            </div>
          </div>
        </div>
      </div>

      {/* Number of Marriages Analysis */}
      <div className="analysis-section">
        <h3>💍 Number of Marriages</h3>
        {(() => {
          const marriageIndicators = [];
            let marriageCount = 1; // Default single marriage
            
            // Multiple marriage indicators
            const venusData = chartData?.planets?.['Venus'];
            const marsData = chartData?.planets?.['Mars'];
            const moonData = chartData?.planets?.['Moon'];
            
            // Venus in dual signs (Gemini, Virgo, Sagittarius, Pisces)
            if (venusData && [2, 5, 8, 11].includes(venusData.sign)) {
              marriageIndicators.push('Venus in dual sign indicates multiple relationships');
              marriageCount = Math.max(marriageCount, 2);
            }
            
            // 7th lord in dual sign
            if (seventhLordAnalysis && [2, 5, 8, 11].includes(seventhLordAnalysis.sign)) {
              marriageIndicators.push('7th lord in dual sign suggests multiple marriages');
              marriageCount = Math.max(marriageCount, 2);
            }
            
            // Multiple planets in 7th house
            if (planetsIn7th.length >= 2) {
              marriageIndicators.push(`${planetsIn7th.length} planets in 7th house indicate multiple partnerships`);
              marriageCount = Math.max(marriageCount, 2);
            }
            
            // Mars-Venus conjunction in certain houses
            const venusConjunctions = getConjunctions('Venus');
            if (venusConjunctions.includes('Mars')) {
              const venusHouse = chartData?.houses?.findIndex(house => house.sign === venusData.sign) + 1;
              if ([1, 5, 7, 9].includes(venusHouse)) {
                marriageIndicators.push('Mars-Venus conjunction suggests passionate but unstable relationships');
                marriageCount = Math.max(marriageCount, 2);
              }
            }
            
            // Rahu/Ketu influence on 7th house or Venus
            const rahuData = chartData?.planets?.['Rahu'];
            const ketuData = chartData?.planets?.['Ketu'];
            
            if (rahuData) {
              const rahuHouse = chartData?.houses?.findIndex(house => house.sign === rahuData.sign) + 1;
              if (rahuHouse === 7) {
                marriageIndicators.push('Rahu in 7th house creates unconventional marriage patterns');
                marriageCount = Math.max(marriageCount, 2);
              }
            }
            
            // Venus aspected by Saturn (delays/multiple attempts)
            const venusAspects = getAspectsTo('Venus');
            if (venusAspects.some(a => a.planet === 'Saturn')) {
              marriageIndicators.push('Saturn aspects Venus - multiple marriage attempts possible');
            }
            
            // Moon in 7th house (emotional instability in marriage)
            if (moonData) {
              const moonHouse = chartData?.houses?.findIndex(house => house.sign === moonData.sign) + 1;
              if (moonHouse === 7) {
                marriageIndicators.push('Moon in 7th house - emotional changes in marriage');
              }
            }
            
            // Strong indicators for single stable marriage
            const singleMarriageIndicators = [];
            
            // Jupiter aspects 7th house (stability)
            if (aspectingPlanets.includes('Jupiter')) {
              singleMarriageIndicators.push('Jupiter aspects 7th house - promotes stable marriage');
              if (marriageCount > 1) marriageCount = 1; // Jupiter's influence reduces multiple marriages
            }
            
            // Venus in fixed signs (Taurus, Leo, Scorpio, Aquarius) and strong
            if (venusData && [1, 4, 7, 10].includes(venusData.sign) && (karakas.venus?.strength || 0) >= 6) {
              singleMarriageIndicators.push('Strong Venus in fixed sign promotes single stable marriage');
              marriageCount = 1;
            }
            
            // 7th lord strong and well-placed
            if (seventhLordAnalysis && seventhLordAnalysis.status === 'Benefic' && (seventhHouse.strength_score || 0) >= 60) {
              singleMarriageIndicators.push('Strong 7th lord ensures marital stability');
            }
            
            let prediction, confidence, description;
            
            if (marriageCount === 1 && singleMarriageIndicators.length > 0) {
              prediction = 'Single Marriage';
              confidence = 'High';
              description = 'Your chart strongly indicates one stable, long-lasting marriage. You are likely to find your life partner and stay committed.';
            } else if (marriageCount === 1) {
              prediction = 'Single Marriage';
              confidence = 'Moderate';
              description = 'Your chart suggests one marriage, though you may face some relationship challenges that can be overcome with effort.';
            } else if (marriageIndicators.length >= 3) {
              prediction = 'Multiple Relationships';
              confidence = 'High';
              description = 'Your chart shows strong indicators for multiple relationships or marriages. You may experience more than one significant partnership in life.';
            } else {
              prediction = 'Likely Multiple Attempts';
              confidence = 'Moderate';
              description = 'Your chart suggests you may have multiple relationship attempts before finding lasting marriage, or face some instability in partnerships.';
            }
            
            return (
              <div className="marriage-count-result">
                <div className="marriage-count-header">
                  <div className="marriage-count-icon">
                    {prediction === 'Single Marriage' ? '💑' : '💕'}
                  </div>
                  <div className="marriage-count-info">
                    <h4>{prediction}</h4>
                    <span className="confidence-level">Confidence: {confidence}</span>
                  </div>
                </div>
                <p className="marriage-count-description">{description}</p>
                
                <div className="indicators-grid">
                  {marriageIndicators.length > 0 && (
                    <div className="indicators-column multiple-indicators">
                      <h5>💕 Multiple Marriage Indicators ({marriageIndicators.length})</h5>
                      <ul>
                        {marriageIndicators.map((indicator, index) => (
                          <li key={index}>{indicator}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {singleMarriageIndicators.length > 0 && (
                    <div className="indicators-column single-indicators">
                      <h5>💑 Single Marriage Indicators ({singleMarriageIndicators.length})</h5>
                      <ul>
                        {singleMarriageIndicators.map((indicator, index) => (
                          <li key={index}>{indicator}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                
                {marriageIndicators.length === 0 && singleMarriageIndicators.length === 0 && (
                  <div className="neutral-indicators">
                    <p>📊 Your chart shows neutral indicators. Marriage patterns depend more on personal choices and circumstances.</p>
                  </div>
                )}
              </div>
            );
        })()}
      </div>

      {/* Marriage Yoga Detection */}
      <div className="analysis-section">
        <h3>🕉️ Marriage Yogas</h3>
        <div className="section-score-header">
          <span className="section-score">Yoga Score: {frontendOverallScore.components.yoga_score >= 0 ? '+' : ''}{frontendOverallScore.components.yoga_score}/1.5</span>
        </div>
        {(() => {
          const beneficYogas = [];
            const maleficYogas = [];
            const kalatraYogas = [];
            
            // Get planet positions
            const venusData = chartData?.planets?.['Venus'];
            const jupiterData = chartData?.planets?.['Jupiter'];
            const moonData = chartData?.planets?.['Moon'];
            const marsData = chartData?.planets?.['Mars'];
            const sunData = chartData?.planets?.['Sun'];
            const saturnData = chartData?.planets?.['Saturn'];
            const mercuryData = chartData?.planets?.['Mercury'];
            const rahuData = chartData?.planets?.['Rahu'];
            const ketuData = chartData?.planets?.['Ketu'];
            
            // Helper function to get house number from sign
            const getHouseFromSign = (sign) => chartData?.houses?.findIndex(house => house.sign === sign) + 1;
            
            // KALATRA YOGAS (Specific Marriage Yogas)
            
            // 1. Kalatra Karaka Yoga - Venus exalted/own sign in 7th
            if (venusData) {
              const venusHouse = getHouseFromSign(venusData.sign);
              const venusDignity = getPlanetDignity('Venus', venusData.sign);
              if (venusHouse === 7 && (venusDignity === 'Exalted' || venusDignity === 'Own')) {
                kalatraYogas.push({
                  name: 'Kalatra Karaka Yoga',
                  description: `Venus ${venusDignity.toLowerCase()} in 7th house - Excellent marriage prospects with beautiful, loving spouse`,
                  strength: 'Very Strong',
                  effect: 'Harmonious marriage, attractive spouse, marital bliss'
                });
              }
            }
            
            // 2. Shubha Kalatra Yoga - 7th lord with benefics
            if (seventhLordAnalysis) {
              const conjunctions = getConjunctions(seventhHouse.house_lord);
              const beneficConjunctions = conjunctions.filter(p => ['Jupiter', 'Venus', 'Moon'].includes(p));
              if (beneficConjunctions.length > 0) {
                kalatraYogas.push({
                  name: 'Shubha Kalatra Yoga',
                  description: `7th lord ${seventhHouse.house_lord} with ${beneficConjunctions.join(', ')} - Auspicious marriage`,
                  strength: 'Strong',
                  effect: 'Good spouse, happy marriage, family harmony'
                });
              }
            }
            
            // 3. Dhana Kalatra Yoga - 7th lord in 2nd/11th house
            if (seventhLordAnalysis) {
              const seventhLordHouse = getHouseFromSign(seventhLordAnalysis.sign);
              if ([2, 11].includes(seventhLordHouse)) {
                kalatraYogas.push({
                  name: 'Dhana Kalatra Yoga',
                  description: `7th lord in ${seventhLordHouse}th house - Wealthy spouse bringing prosperity`,
                  strength: 'Strong',
                  effect: 'Financial gains through marriage, prosperous spouse'
                });
              }
            }
            
            // BENEFIC YOGAS ENHANCING MARRIAGE
            
            // 1. Gajakesari Yoga - Jupiter-Moon conjunction/aspect
            if (jupiterData && moonData) {
              const jupiterHouse = getHouseFromSign(jupiterData.sign);
              const moonHouse = getHouseFromSign(moonData.sign);
              const isConjunct = jupiterData.sign === moonData.sign;
              const isAspect = Math.abs(jupiterHouse - moonHouse) === 6 || 
                              (jupiterHouse + 4) % 12 + 1 === moonHouse || 
                              (jupiterHouse + 8) % 12 + 1 === moonHouse;
              
              if (isConjunct || isAspect) {
                beneficYogas.push({
                  name: 'Gajakesari Yoga',
                  description: 'Jupiter-Moon connection enhances wisdom and emotional stability in marriage',
                  strength: 'Strong',
                  effect: 'Wise decisions in marriage, emotional maturity, respected spouse'
                });
              }
            }
            
            // 2. Malavya Yoga - Venus in Kendra in own/exaltation
            if (venusData) {
              const venusHouse = getHouseFromSign(venusData.sign);
              const venusDignity = getPlanetDignity('Venus', venusData.sign);
              if ([1, 4, 7, 10].includes(venusHouse) && (venusDignity === 'Exalted' || venusDignity === 'Own')) {
                beneficYogas.push({
                  name: 'Malavya Yoga',
                  description: `Venus ${venusDignity.toLowerCase()} in ${venusHouse}th house (Kendra) - Royal marriage yoga`,
                  strength: 'Very Strong',
                  effect: 'Luxurious lifestyle, beautiful spouse, artistic talents, high status marriage'
                });
              }
            }
            
            // 3. Hamsa Yoga - Jupiter in Kendra in own/exaltation
            if (jupiterData) {
              const jupiterHouse = getHouseFromSign(jupiterData.sign);
              const jupiterDignity = getPlanetDignity('Jupiter', jupiterData.sign);
              if ([1, 4, 7, 10].includes(jupiterHouse) && (jupiterDignity === 'Exalted' || jupiterDignity === 'Own')) {
                beneficYogas.push({
                  name: 'Hamsa Yoga',
                  description: `Jupiter ${jupiterDignity.toLowerCase()} in ${jupiterHouse}th house - Divine blessings in marriage`,
                  strength: 'Very Strong',
                  effect: 'Spiritual spouse, dharmic marriage, divine protection, wisdom in relationships'
                });
              }
            }
            
            // 4. Raj Yoga - Kendra-Trikona lords together
            const kendraLords = [1, 4, 7, 10].map(h => houseLords[chartData?.houses?.[h-1]?.sign || 0]);
            const trikonaLords = [1, 5, 9].map(h => houseLords[chartData?.houses?.[h-1]?.sign || 0]);
            
            Object.entries(chartData?.planets || {}).forEach(([planet1, data1]) => {
              if (!kendraLords.includes(planet1)) return;
              const conjunctions = getConjunctions(planet1);
              conjunctions.forEach(planet2 => {
                if (trikonaLords.includes(planet2)) {
                  beneficYogas.push({
                    name: 'Raj Yoga',
                    description: `${planet1} (Kendra lord) with ${planet2} (Trikona lord) - Royal combination`,
                    strength: 'Strong',
                    effect: 'High status marriage, prosperity, recognition through spouse'
                  });
                }
              });
            });
            
            // MALEFIC YOGAS CAUSING DELAYS/PROBLEMS
            
            // 1. Manglik Dosha
            if (manglik.is_manglik) {
              maleficYogas.push({
                name: 'Mangal Dosha',
                description: `Mars in ${manglik.mars_house}th house - ${manglik.severity} severity`,
                strength: manglik.severity === 'High' ? 'Very Strong' : 'Moderate',
                effect: 'Conflicts in marriage, aggressive spouse, delays, need for remedies',
                remedy: manglik.severity === 'High' ? 'Marry another Manglik, Kumbh Vivah, Mangal Shanti puja' : 'Tuesday fasting, Hanuman worship'
              });
            }
            
            // 2. Kala Sarpa Yoga - All planets between Rahu-Ketu
            if (rahuData && ketuData) {
              const rahuSign = rahuData.sign;
              const ketuSign = ketuData.sign;
              const planetsBetween = Object.entries(chartData?.planets || {})
                .filter(([name, data]) => !['Rahu', 'Ketu'].includes(name))
                .every(([name, data]) => {
                  const planetSign = data.sign;
                  return (rahuSign < ketuSign) ? 
                    (planetSign > rahuSign && planetSign < ketuSign) :
                    (planetSign > rahuSign || planetSign < ketuSign);
                });
              
              if (planetsBetween) {
                maleficYogas.push({
                  name: 'Kala Sarpa Yoga',
                  description: 'All planets hemmed between Rahu-Ketu axis',
                  strength: 'Strong',
                  effect: 'Delays in marriage, karmic relationships, spiritual lessons through marriage',
                  remedy: 'Rahu-Ketu remedies, spiritual practices, patience'
                });
              }
            }
            
            // 3. Shani Dosha - Saturn in 7th house
            if (saturnData) {
              const saturnHouse = getHouseFromSign(saturnData.sign);
              if (saturnHouse === 7) {
                maleficYogas.push({
                  name: 'Shani Dosha',
                  description: 'Saturn in 7th house causing delays and restrictions',
                  strength: 'Moderate',
                  effect: 'Late marriage, older spouse, responsibilities in marriage, slow progress',
                  remedy: 'Saturn remedies, blue sapphire (if suitable), Saturday fasting'
                });
              }
            }
            
            // 4. Guru Chandal Yoga - Jupiter with Rahu
            if (jupiterData && rahuData && jupiterData.sign === rahuData.sign) {
              maleficYogas.push({
                name: 'Guru Chandal Yoga',
                description: 'Jupiter conjunct Rahu - Wisdom clouded by illusions',
                strength: 'Moderate',
                effect: 'Wrong judgment in marriage, unconventional spouse, spiritual confusion',
                remedy: 'Jupiter strengthening, avoid hasty marriage decisions, seek elder guidance'
              });
            }
            
            // 5. Papakartari Yoga - 7th house hemmed by malefics
            const seventhHouseSign = chartData?.houses?.[6]?.sign || 0;
            const sixthHouseSign = chartData?.houses?.[5]?.sign || 0;
            const eighthHouseSign = chartData?.houses?.[7]?.sign || 0;
            
            const maleficsIn6th = Object.entries(chartData?.planets || {})
              .filter(([name, data]) => ['Mars', 'Saturn', 'Rahu', 'Ketu'].includes(name) && data.sign === sixthHouseSign)
              .map(([name]) => name);
            
            const maleficsIn8th = Object.entries(chartData?.planets || {})
              .filter(([name, data]) => ['Mars', 'Saturn', 'Rahu', 'Ketu'].includes(name) && data.sign === eighthHouseSign)
              .map(([name]) => name);
            
            if (maleficsIn6th.length > 0 && maleficsIn8th.length > 0) {
              maleficYogas.push({
                name: 'Papakartari Yoga',
                description: `7th house hemmed by malefics: ${maleficsIn6th.join(',')} in 6th, ${maleficsIn8th.join(',')} in 8th`,
                strength: 'Strong',
                effect: 'Obstacles in marriage, conflicts, health issues to spouse',
                remedy: 'Strengthen 7th house, benefic planet remedies, protective mantras'
              });
            }
            
            return (
              <div className="yoga-results">
                {/* Kalatra Yogas */}
                {kalatraYogas.length > 0 && (
                  <div className="yoga-category kalatra-yogas">
                    <h4>🏆 Kalatra Yogas (Marriage-Specific)</h4>
                    <div className="yoga-list">
                      {kalatraYogas.map((yoga, index) => (
                        <div key={index} className="yoga-item benefic">
                          <div className="yoga-header">
                            <span className="yoga-name">{yoga.name}</span>
                            <span className={`yoga-strength ${yoga.strength.toLowerCase().replace(' ', '-')}`}>{yoga.strength}</span>
                          </div>
                          <div className="yoga-description">{yoga.description}</div>
                          <div className="yoga-effect">Effect: {yoga.effect}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Benefic Yogas */}
                {beneficYogas.length > 0 && (
                  <div className="yoga-category benefic-yogas">
                    <h4>✨ Benefic Yogas (Enhancing Marriage)</h4>
                    <div className="yoga-list">
                      {beneficYogas.map((yoga, index) => (
                        <div key={index} className="yoga-item benefic">
                          <div className="yoga-header">
                            <span className="yoga-name">{yoga.name}</span>
                            <span className={`yoga-strength ${yoga.strength.toLowerCase().replace(' ', '-')}`}>{yoga.strength}</span>
                          </div>
                          <div className="yoga-description">{yoga.description}</div>
                          <div className="yoga-effect">Effect: {yoga.effect}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Malefic Yogas */}
                {maleficYogas.length > 0 && (
                  <div className="yoga-category malefic-yogas">
                    <h4>⚠️ Malefic Yogas (Causing Challenges)</h4>
                    <div className="yoga-list">
                      {maleficYogas.map((yoga, index) => (
                        <div key={index} className="yoga-item malefic">
                          <div className="yoga-header">
                            <span className="yoga-name">{yoga.name}</span>
                            <span className={`yoga-strength ${yoga.strength.toLowerCase().replace(' ', '-')}`}>{yoga.strength}</span>
                          </div>
                          <div className="yoga-description">{yoga.description}</div>
                          <div className="yoga-effect">Effect: {yoga.effect}</div>
                          {yoga.remedy && (
                            <div className="yoga-remedy">Remedy: {yoga.remedy}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* No Yogas Found */}
                {kalatraYogas.length === 0 && beneficYogas.length === 0 && maleficYogas.length === 0 && (
                  <div className="no-yogas">
                    <div className="neutral-indicator">
                      <span className="neutral-icon">📊</span>
                      <span className="neutral-text">No specific marriage yogas detected</span>
                    </div>
                    <p>Your chart shows standard planetary combinations. Marriage prospects depend on individual planet strengths and overall chart harmony.</p>
                  </div>
                )}
                
                {/* Yoga Summary */}
                {(kalatraYogas.length > 0 || beneficYogas.length > 0 || maleficYogas.length > 0) && (
                  <div className="yoga-summary">
                    <h4>📋 Yoga Summary</h4>
                    <div className="summary-stats">
                      <div className="stat-item positive">
                        <span className="stat-number">{kalatraYogas.length + beneficYogas.length}</span>
                        <span className="stat-label">Benefic Yogas</span>
                      </div>
                      <div className="stat-item negative">
                        <span className="stat-number">{maleficYogas.length}</span>
                        <span className="stat-label">Malefic Yogas</span>
                      </div>
                      <div className="stat-item neutral">
                        <span className="stat-number">{calculateYogaScore(kalatraYogas, beneficYogas, maleficYogas).toFixed(1)}</span>
                        <span className="stat-label">Yoga Score</span>
                      </div>
                    </div>
                    <div className="overall-yoga-effect">
                      {calculateYogaScore(kalatraYogas, beneficYogas, maleficYogas) > 0.3 ? (
                        <div className="positive-effect">
                          <span className="effect-icon">🌟</span>
                          <span>Strong positive yoga influence boosting marriage prospects (+{calculateYogaScore(kalatraYogas, beneficYogas, maleficYogas).toFixed(1)} points)</span>
                        </div>
                      ) : calculateYogaScore(kalatraYogas, beneficYogas, maleficYogas) < -0.3 ? (
                        <div className="negative-effect">
                          <span className="effect-icon">⚠️</span>
                          <span>Challenging yogas reducing marriage prospects ({calculateYogaScore(kalatraYogas, beneficYogas, maleficYogas).toFixed(1)} points) - remedies essential</span>
                        </div>
                      ) : (
                        <div className="balanced-effect">
                          <span className="effect-icon">⚖️</span>
                          <span>Balanced yoga effects ({calculateYogaScore(kalatraYogas, beneficYogas, maleficYogas) >= 0 ? '+' : ''}{calculateYogaScore(kalatraYogas, beneficYogas, maleficYogas).toFixed(1)} points) - mixed influences on marriage</span>
                        </div>
                      )}
                    </div>
                    <div className="yoga-breakdown">
                      <h5>📊 Yoga Score Breakdown:</h5>
                      <div className="yoga-score-details">
                        <div className="yoga-score-item">
                          <span>Kalatra Yogas ({kalatraYogas.length}):</span>
                          <span>{kalatraYogas.reduce((sum, yoga) => sum + (yoga.strength === 'Very Strong' ? 0.4 : yoga.strength === 'Strong' ? 0.3 : 0.2), 0).toFixed(1)}</span>
                        </div>
                        <div className="yoga-score-item">
                          <span>Benefic Yogas ({beneficYogas.length}):</span>
                          <span>+{beneficYogas.reduce((sum, yoga) => sum + (yoga.strength === 'Very Strong' ? 0.3 : yoga.strength === 'Strong' ? 0.2 : 0.1), 0).toFixed(1)}</span>
                        </div>
                        <div className="yoga-score-item">
                          <span>Malefic Yogas ({maleficYogas.length}):</span>
                          <span>{maleficYogas.reduce((sum, yoga) => sum - (yoga.strength === 'Very Strong' ? 0.4 : yoga.strength === 'Strong' ? 0.3 : 0.2), 0).toFixed(1)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="yoga-score-explanation">
                      <h5>📊 How Yoga Score Affects Overall Rating:</h5>
                      <p>The yoga score ({calculateYogaScore(kalatraYogas, beneficYogas, maleficYogas) >= 0 ? '+' : ''}{calculateYogaScore(kalatraYogas, beneficYogas, maleficYogas).toFixed(1)}/1.5) contributes 15% to your overall marriage score. Powerful yogas like Malavya or Kalatra Karaka can significantly boost your prospects, while malefic yogas like Kala Sarpa or strong Manglik dosha can create challenges that require specific remedies.</p>
                    </div>
                  </div>
                )}
              </div>
            );
        })()}
      </div>

      {/* Where Will You Meet Your Spouse Analysis */}
      <div className="analysis-section">
        <h3>📍 Where Will You Meet Your Spouse</h3>
        {(() => {
          const meetingIndicators = [];
            
            // 1. 7th House Lord's Position Analysis
            const seventhLordHouse = seventhLordAnalysis ? chartData?.houses?.findIndex(house => house.sign === seventhLordAnalysis.sign) + 1 : null;
            
            const houseIndicators = {
              1: { place: 'Through self-effort, personal network', icon: '👤', description: 'You will meet through your own initiatives, personal connections, or while pursuing individual goals' },
              2: { place: 'Through family connections, financial institutions', icon: '👨‍👩‍👧‍👦', description: 'Family introductions, banks, financial meetings, or wealth-related gatherings' },
              3: { place: 'Through siblings, neighbors, short travels, media', icon: '🚗', description: 'Local travel, neighborhood events, through brothers/sisters, or media/communication work' },
              4: { place: 'Through mother\'s side, home, real estate, vehicles', icon: '🏠', description: 'Maternal connections, property dealings, home-based events, or vehicle-related places' },
              5: { place: 'Through education, entertainment, creative fields', icon: '🎓', description: 'Schools, colleges, entertainment venues, creative workshops, or children-related activities' },
              6: { place: 'Through work, service, health sector, competitions', icon: '💼', description: 'Workplace, hospitals, gyms, competitive events, or service-oriented activities' },
              7: { place: 'Through business partnerships, legal matters', icon: '⚖️', description: 'Business meetings, legal offices, courts, or formal partnership events' },
              8: { place: 'Through research, occult, inheritance matters', icon: '🔬', description: 'Research institutions, mystical places, insurance offices, or transformation-related events' },
              9: { place: 'Through religious places, higher education, foreign lands', icon: '🕌', description: 'Temples, universities, foreign countries, or spiritual/philosophical gatherings' },
              10: { place: 'Through career, workplace, authority figures', icon: '🏢', description: 'Professional settings, government offices, through bosses, or career-related events' },
              11: { place: 'Through friends, social networks, elder siblings', icon: '👥', description: 'Friend circles, social media, community events, or through elder siblings' },
              12: { place: 'Through foreign lands, hospitals, spiritual places', icon: '✈️', description: 'Foreign countries, hospitals, ashrams, isolated places, or charitable institutions' }
            };
            
            if (seventhLordHouse && houseIndicators[seventhLordHouse]) {
              meetingIndicators.push({
                type: '7th Lord Position',
                strength: 'Primary',
                ...houseIndicators[seventhLordHouse]
              });
            }
            
            // 2. Darakarka Analysis
            const darakarka = getDarakarka();
            const darakarkaIndicators = {
              'Sun': { place: 'Government offices, authoritative places', icon: '🏛️', description: 'Government buildings, administrative offices, places of authority, or through father figures' },
              'Moon': { place: 'Public places, water bodies, maternal connections', icon: '🌊', description: 'Public gatherings, near water, through mother or maternal relatives, or emotional settings' },
              'Mars': { place: 'Sports venues, military, engineering fields', icon: '⚽', description: 'Gyms, sports events, military areas, engineering sites, or competitive environments' },
              'Mercury': { place: 'Educational institutions, communication sector', icon: '📚', description: 'Schools, libraries, media houses, communication companies, or intellectual gatherings' },
              'Jupiter': { place: 'Religious places, universities, legal institutions', icon: '🏛️', description: 'Temples, universities, law courts, spiritual centers, or through teachers/gurus' },
              'Venus': { place: 'Entertainment venues, arts, luxury places', icon: '🎭', description: 'Theaters, art galleries, luxury hotels, beauty salons, or artistic/cultural events' },
              'Saturn': { place: 'Traditional places, older connections, hard work environments', icon: '🏭', description: 'Traditional settings, through elderly people, factories, or long-term work environments' }
            };
            
            if (darakarka && darakarkaIndicators[darakarka]) {
              meetingIndicators.push({
                type: 'Darakarka Influence',
                strength: 'Strong',
                ...darakarkaIndicators[darakarka]
              });
            }
            
            // 3. Venus Position Analysis
            const venusData = chartData?.planets?.['Venus'];
            if (venusData) {
              const venusHouse = chartData?.houses?.findIndex(house => house.sign === venusData.sign) + 1;
              if (houseIndicators[venusHouse]) {
                meetingIndicators.push({
                  type: 'Venus Position',
                  strength: 'Moderate',
                  place: `Romantic settings: ${houseIndicators[venusHouse].place.toLowerCase()}`,
                  icon: '💕',
                  description: `Venus indicates romantic circumstances in ${houseIndicators[venusHouse].description.toLowerCase()}`
                });
              }
            }
            
            // 4. 5th House vs 7th House Analysis
            const fifthHouseStrength = chartData?.houses?.[4] ? Object.entries(chartData?.planets || {}).filter(([name, data]) => data.sign === chartData.houses[4].sign).length : 0;
            const seventhHouseStrength = chartData?.houses?.[6] ? Object.entries(chartData?.planets || {}).filter(([name, data]) => data.sign === chartData.houses[6].sign).length : 0;
            
            if (fifthHouseStrength > seventhHouseStrength) {
              meetingIndicators.push({
                type: '5th House Dominance',
                strength: 'Moderate',
                place: 'Romantic, casual settings',
                icon: '💝',
                description: 'Strong 5th house suggests meeting in romantic, fun, or casual environments before formal commitment'
              });
            } else if (seventhHouseStrength > fifthHouseStrength) {
              meetingIndicators.push({
                type: '7th House Dominance',
                strength: 'Moderate',
                place: 'Formal, arranged settings',
                icon: '🤝',
                description: 'Strong 7th house suggests meeting through formal introductions or arranged circumstances'
              });
            }
            
            // 5. Rahu/Ketu Influence
            const rahuData = chartData?.planets?.['Rahu'];
            const ketuData = chartData?.planets?.['Ketu'];
            
            if (rahuData) {
              const rahuHouse = chartData?.houses?.findIndex(house => house.sign === rahuData.sign) + 1;
              if ([5, 7].includes(rahuHouse)) {
                meetingIndicators.push({
                  type: 'Rahu Influence',
                  strength: 'Moderate',
                  place: 'Foreign connections, unconventional places, online',
                  icon: '🌐',
                  description: 'Rahu suggests meeting through foreign connections, online platforms, or unconventional circumstances'
                });
              }
            }
            
            if (ketuData) {
              const ketuHouse = chartData?.houses?.findIndex(house => house.sign === ketuData.sign) + 1;
              if ([5, 7].includes(ketuHouse)) {
                meetingIndicators.push({
                  type: 'Ketu Influence',
                  strength: 'Moderate',
                  place: 'Spiritual places, past-life connections',
                  icon: '🕯️',
                  description: 'Ketu suggests meeting in spiritual settings or through karmic/past-life connections'
                });
              }
            }
            
            // 6. Nakshatra Analysis
            const venusNakshatra = venusData ? getNakshatraLord(venusData.longitude) : null;
            const nakshatraPlaces = {
              'Sun': 'Government offices, temples, authoritative places',
              'Moon': 'Water bodies, public places, maternal homes',
              'Mars': 'Sports venues, military areas, competitive places',
              'Mercury': 'Educational institutions, media houses, markets',
              'Jupiter': 'Religious places, universities, legal institutions',
              'Venus': 'Entertainment venues, luxury places, artistic centers',
              'Saturn': 'Traditional places, factories, elderly gatherings'
            };
            
            if (venusNakshatra && nakshatraPlaces[venusNakshatra]) {
              meetingIndicators.push({
                type: 'Venus Nakshatra',
                strength: 'Subtle',
                place: nakshatraPlaces[venusNakshatra],
                icon: '⭐',
                description: `Venus nakshatra lord ${venusNakshatra} suggests meeting in ${nakshatraPlaces[venusNakshatra].toLowerCase()}`
              });
            }
            
            return (
              <div className="meeting-analysis-result">
                <div className="meeting-summary">
                  <h4>🎯 Most Likely Meeting Places</h4>
                  <div className="primary-indicators">
                    {meetingIndicators.filter(indicator => indicator.strength === 'Primary').map((indicator, index) => (
                      <div key={index} className="primary-meeting-card">
                        <div className="meeting-icon">{indicator.icon}</div>
                        <div className="meeting-content">
                          <h5>{indicator.place}</h5>
                          <p>{indicator.description}</p>
                          <span className="indicator-type">{indicator.type}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="detailed-indicators">
                  <h4>📋 Detailed Analysis</h4>
                  <div className="indicators-grid">
                    {meetingIndicators.map((indicator, index) => (
                      <div key={index} className={`meeting-indicator ${indicator.strength.toLowerCase()}`}>
                        <div className="indicator-header">
                          <span className="indicator-icon">{indicator.icon}</span>
                          <div className="indicator-info">
                            <span className="indicator-title">{indicator.type}</span>
                            <span className={`indicator-strength ${indicator.strength.toLowerCase()}`}>{indicator.strength}</span>
                          </div>
                        </div>
                        <div className="indicator-place">{indicator.place}</div>
                        <div className="indicator-description">{indicator.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
                
                {meetingIndicators.length === 0 && (
                  <div className="no-indicators">
                    <div className="neutral-meeting">
                      <span className="neutral-icon">📊</span>
                      <span className="neutral-text">Standard meeting circumstances indicated</span>
                    </div>
                    <p>Your chart shows balanced indicators. You may meet your spouse through common social circumstances or family arrangements.</p>
                  </div>
                )}
                
                <div className="meeting-tips">
                  <h4>💡 Practical Guidance</h4>
                  <div className="tips-grid">
                    {meetingIndicators.length > 0 && (
                      <div className="tip-item">
                        <span className="tip-icon">🎯</span>
                        <span className="tip-text">Focus your social activities around the indicated places and circumstances for better chances of meeting your spouse.</span>
                      </div>
                    )}
                    <div className="tip-item">
                      <span className="tip-icon">⏰</span>
                      <span className="tip-text">The meeting will likely happen during favorable Venus or Jupiter periods in your life.</span>
                    </div>
                    <div className="tip-item">
                      <span className="tip-icon">🌟</span>
                      <span className="tip-text">Stay open to the indicated circumstances - destiny often works through seemingly ordinary situations.</span>
                    </div>
                  </div>
                </div>
              </div>
            );
        })()}
      </div>

      {/* Love vs Arranged Marriage Analysis */}
      <div className="analysis-section">
        <h3>💕 Love vs Arranged Marriage</h3>
        {(() => {
          const loveIndicators = [];
            const arrangedIndicators = [];
            
            // 5th house analysis (romance/love affairs)
            const fifthHouseSign = chartData?.houses?.[4]?.sign || 0;
            const fifthHouseLord = houseLords[fifthHouseSign];
            const planetsIn5th = Object.entries(chartData?.planets || {}).filter(([name, data]) => data.sign === fifthHouseSign);
            
            // Venus analysis for love
            if (karakas.venus?.strength >= 6) {
              loveIndicators.push('Strong Venus favors love marriage');
            }
            
            // Check Venus house position
            if (venusAnalysis) {
              const venusHouse = chartData?.houses?.findIndex(house => house.sign === venusAnalysis.sign) + 1;
              if ([5, 7, 11].includes(venusHouse)) {
                loveIndicators.push(`Venus in ${venusHouse}th house supports love`);
              }
            }
            
            // 7th lord in 5th house check
            if (seventhLordAnalysis) {
              const seventhLordHouse = chartData?.houses?.findIndex(house => house.sign === seventhLordAnalysis.sign) + 1;
              if (seventhLordHouse === 5) {
                loveIndicators.push('7th lord in 5th house - strong love indication');
              }
            }
            
            // Mars-Venus conjunction or aspect
            const venusConjunctions = getConjunctions('Venus');
            const venusAspects = getAspectsTo('Venus');
            if (venusConjunctions.includes('Mars') || venusAspects.some(a => a.planet === 'Mars')) {
              loveIndicators.push('Mars-Venus connection creates passionate love');
            }
            
            // Rahu influence on 5th/7th houses
            const rahuData = chartData?.planets?.['Rahu'];
            if (rahuData) {
              const rahuHouse = chartData?.houses?.findIndex(house => house.sign === rahuData.sign) + 1;
              if ([5, 7].includes(rahuHouse)) {
                loveIndicators.push(`Rahu in ${rahuHouse}th house indicates unconventional love`);
              }
            }
            
            // Moon-Venus connection
            if (venusConjunctions.includes('Moon') || venusAspects.some(a => a.planet === 'Moon')) {
              loveIndicators.push('Moon-Venus connection enhances romantic feelings');
            }
            
            // Jupiter analysis for arranged marriage
            if (karakas.jupiter?.strength >= 6) {
              arrangedIndicators.push('Strong Jupiter favors traditional arranged marriage');
            }
            
            // Saturn influence on 7th house
            const saturnData = chartData?.planets?.['Saturn'];
            if (saturnData) {
              const saturnHouse = chartData?.houses?.findIndex(house => house.sign === saturnData.sign) + 1;
              if (saturnHouse === 7) {
                arrangedIndicators.push('Saturn in 7th house - traditional structured approach');
              }
              // Saturn aspects 7th house (3rd, 7th, 10th aspects)
              const saturnSign = saturnData.sign;
              const seventhHouseSign = chartData?.houses?.[6]?.sign || 0;
              if ([(saturnSign + 2) % 12, (saturnSign + 6) % 12, (saturnSign + 9) % 12].includes(seventhHouseSign)) {
                arrangedIndicators.push('Saturn aspects 7th house - traditional approach');
              }
            }
            
            // 7th lord in 9th/10th house check
            if (seventhLordAnalysis) {
              const seventhLordHouse = chartData?.houses?.findIndex(house => house.sign === seventhLordAnalysis.sign) + 1;
              if (seventhLordHouse === 9) {
                arrangedIndicators.push('7th lord in 9th house - family arranged marriage');
              }
              if (seventhLordHouse === 10) {
                arrangedIndicators.push('7th lord in 10th house - status-based arranged marriage');
              }
            }
            
            // Sun influence (father/authority)
            const sunData = chartData?.planets?.['Sun'];
            if (sunData && seventhLordAnalysis && sunData.sign === seventhLordAnalysis.sign) {
              arrangedIndicators.push('Sun with 7th lord - father\'s choice in marriage');
            }
            
            // Calculate tendency
            const loveScore = loveIndicators.length;
            const arrangedScore = arrangedIndicators.length;
            
            let marriageType, confidence, description;
            if (loveScore > arrangedScore + 1) {
              marriageType = 'Love Marriage';
              confidence = 'High';
              description = 'Your chart strongly indicates love marriage. You are likely to fall in love first and then marry that person.';
            } else if (arrangedScore > loveScore + 1) {
              marriageType = 'Arranged Marriage';
              confidence = 'High';
              description = 'Your chart strongly favors arranged marriage. You will likely find happiness through family arrangements or traditional matchmaking.';
            } else if (loveScore > arrangedScore) {
              marriageType = 'Love Marriage';
              confidence = 'Moderate';
              description = 'Your chart leans toward love marriage, though family approval will be important.';
            } else if (arrangedScore > loveScore) {
              marriageType = 'Arranged Marriage';
              confidence = 'Moderate';
              description = 'Your chart leans toward arranged marriage, though you may develop feelings before marriage.';
            } else {
              marriageType = 'Mixed Approach';
              confidence = 'Balanced';
              description = 'Your chart shows equal potential for both. You might have an arranged marriage with someone you grow to love, or a love marriage with family approval.';
            }
            
            return (
              <div className="marriage-type-result">
                <div className="marriage-type-header">
                  <div className="marriage-type-icon">
                    {marriageType === 'Love Marriage' ? '💕' : marriageType === 'Arranged Marriage' ? '👨‍👩‍👧‍👦' : '💝'}
                  </div>
                  <div className="marriage-type-info">
                    <h4>{marriageType}</h4>
                    <span className="confidence-level">Confidence: {confidence}</span>
                  </div>
                </div>
                <p className="marriage-type-description">{description}</p>
                
                <div className="indicators-grid">
                  {loveIndicators.length > 0 && (
                    <div className="indicators-column love-indicators">
                      <h5>💕 Love Marriage Indicators ({loveScore})</h5>
                      <ul>
                        {loveIndicators.map((indicator, index) => (
                          <li key={index}>{indicator}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {arrangedIndicators.length > 0 && (
                    <div className="indicators-column arranged-indicators">
                      <h5>👨‍👩‍👧‍👦 Arranged Marriage Indicators ({arrangedScore})</h5>
                      <ul>
                        {arrangedIndicators.map((indicator, index) => (
                          <li key={index}>{indicator}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                
                {loveScore === 0 && arrangedScore === 0 && (
                  <div className="neutral-indicators">
                    <p>📊 Your chart shows neutral indicators. Both love and arranged marriage are equally possible based on circumstances and personal choices.</p>
                  </div>
                )}
              </div>
            );
        })()}
      </div>

      {/* 7th House Analysis */}
      <div className="analysis-section">
        <h3>🏠 7th House Analysis</h3>
        <div className="analysis-grid">
          <div className="analysis-item">
            <span className="label">House Sign:</span>
            <span className="value">{seventhHouse.house_sign || 'N/A'}</span>
          </div>
          <div className="analysis-item">
            <span className="label">House Lord:</span>
            <span className="value">{seventhHouse.house_lord || 'N/A'}</span>
          </div>
          <div className="analysis-item">
            <span className="label">Strength:</span>
            <span className="value">{seventhHouse.strength_score || 0}/100</span>
          </div>
          <div className="analysis-item">
            <span className="label">Planets in 7th:</span>
            <span className="value">
              {planetsIn7th.length > 0 ? planetsIn7th.join(', ') : 'None'}
            </span>
          </div>
        </div>
        
        {/* 7th House Lord Analysis */}
        <div className="house-lord-analysis">
          <h4 style={{ 
            margin: '0 0 16px 0', 
            color: '#9c27b0', 
            fontSize: '16px', 
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            👑 7th House Lord ({seventhHouseLord}) Analysis
          </h4>
          {seventhLordAnalysis && (
            <div style={{ 
              padding: window.innerWidth < 768 ? '8px' : '12px', 
              background: 'rgba(255,255,255,0.9)', 
              borderRadius: '6px'
            }}>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: window.innerWidth < 768 ? '1fr' : 'repeat(auto-fit, minmax(200px, 1fr))', 
                gap: window.innerWidth < 768 ? '6px' : '8px', 
                marginBottom: '8px'
              }}>
                <div style={{ 
                  padding: '8px 12px', 
                  background: 'rgba(156, 39, 176, 0.05)', 
                  borderRadius: '6px',
                  fontSize: '13px'
                }}>
                  <strong style={{ color: '#9c27b0' }}>Sign:</strong> {['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'][seventhLordAnalysis.sign]}
                </div>
                <div style={{ 
                  padding: '8px 12px', 
                  background: 'rgba(156, 39, 176, 0.05)', 
                  borderRadius: '6px',
                  fontSize: '13px'
                }}>
                  <strong style={{ color: '#9c27b0' }}>Dignity:</strong> <span style={{ color: seventhLordAnalysis.dignity === 'Exalted' ? '#4caf50' : seventhLordAnalysis.dignity === 'Debilitated' ? '#f44336' : seventhLordAnalysis.dignity === 'Own' ? '#2196f3' : '#666', fontWeight: '500' }}>{getDignityExplanation(seventhHouseLord, seventhLordAnalysis.sign, seventhLordAnalysis.longitude)}</span>
                </div>
                <div style={{ 
                  padding: '8px 12px', 
                  background: 'rgba(156, 39, 176, 0.05)', 
                  borderRadius: '6px',
                  fontSize: '13px'
                }}>
                  <strong style={{ color: '#9c27b0' }}>Status:</strong> <span style={{ color: getStatusColor(seventhLordAnalysis.status), fontWeight: '500' }}>{seventhLordAnalysis.status}</span>
                </div>
              </div>
              
              {getConjunctions(seventhHouseLord).length > 0 && (
                <div style={{ 
                  marginTop: '12px', 
                  padding: '10px', 
                  background: 'rgba(255, 193, 7, 0.08)', 
                  borderRadius: '6px',
                  borderLeft: '3px solid #ffc107'
                }}>
                  <strong style={{ color: '#f57c00', fontSize: '13px' }}>🤝 Conjunctions:</strong>
                  <div style={{ marginTop: '6px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {getConjunctions(seventhHouseLord).map(planet => {
                      const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                      return (
                        <span key={planet} style={{ 
                          color: isNaturalBenefic ? '#4caf50' : '#f44336',
                          background: isNaturalBenefic ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: '500'
                        }}>{planet}</span>
                      );
                    })}
                  </div>
                </div>
              )}
              
              {getAspectsTo(seventhHouseLord).length > 0 && (
                <div style={{ 
                  marginTop: '12px', 
                  padding: '10px', 
                  background: 'rgba(63, 81, 181, 0.08)', 
                  borderRadius: '6px',
                  borderLeft: '3px solid #3f51b5'
                }}>
                  <strong style={{ color: '#3f51b5', fontSize: '13px' }}>🎯 Aspected by:</strong>
                  <div style={{ marginTop: '6px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {getAspectsTo(seventhHouseLord).map(({ planet, aspect }) => {
                      const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                      return (
                        <span key={`${planet}-${aspect}`} style={{ 
                          color: isNaturalBenefic ? '#4caf50' : '#f44336',
                          background: isNaturalBenefic ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: '500'
                        }}>{planet} ({aspect})</span>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Detailed 7th House Occupants */}
        {planetsIn7th.length > 0 && (
          <div style={{ 
            marginTop: '16px', 
            padding: window.innerWidth < 768 ? '12px' : '16px', 
            background: 'linear-gradient(135deg, rgba(233, 30, 99, 0.08) 0%, rgba(233, 30, 99, 0.12) 100%)', 
            borderRadius: '8px',
            border: '1px solid rgba(233, 30, 99, 0.2)'
          }}>
            <h4 style={{ 
              margin: '0 0 16px 0', 
              color: '#e91e63', 
              fontSize: '16px', 
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              🏠 Planets in 7th House
            </h4>
            <div className="section-score-header" style={{ marginBottom: '12px' }}>
              <span className="section-score">Combined Effect: {(() => {
                let planetScore = 0;
                planetsIn7th.forEach(planetName => {
                  const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planetName);
                  const dignity = getPlanetDignity(planetName, seventhHouseSign);
                  if (dignity === 'Exalted') planetScore += isNaturalBenefic ? 2 : 1.5;
                  else if (dignity === 'Own') planetScore += isNaturalBenefic ? 1.5 : 1;
                  else if (dignity === 'Debilitated') planetScore -= isNaturalBenefic ? 1 : 1.5;
                  else planetScore += isNaturalBenefic ? 0.5 : -0.3;
                });
                return planetScore >= 0 ? `+${planetScore.toFixed(1)}` : planetScore.toFixed(1);
              })()}/10</span>
            </div>
            {planetsIn7th.map(planetName => {
              const planetData = chartData?.planets?.[planetName];
              const lordships = getHouseLordship(planetName, ascendantSign);
              const status = getPlanetStatus(planetName, seventhHouseSign, lordships);
              const dignity = getPlanetDignity(planetName, planetData?.sign);
              const conjunctions = getConjunctions(planetName);
              const aspects = getAspectsTo(planetName);
              const nakshatraLord = getNakshatraLord(planetData?.longitude || 0);
              const friendshipWithNakLord = getFriendship(planetName, nakshatraLord);
              
              return (
                <div key={planetName} style={{ 
                  padding: window.innerWidth < 768 ? '8px' : '12px', 
                  margin: window.innerWidth < 768 ? '4px 0' : '6px 0', 
                  background: 'rgba(255,255,255,0.9)', 
                  borderRadius: '6px',
                  border: '1px solid rgba(233, 30, 99, 0.1)',
                  fontSize: window.innerWidth < 768 ? '12px' : '13px'
                }}>
                  <div><strong>{planetName}</strong> - <span style={{ color: dignity === 'Exalted' ? '#4caf50' : dignity === 'Debilitated' ? '#f44336' : dignity === 'Own' ? '#2196f3' : '#666' }}>{getDignityExplanation(planetName, planetData?.sign, planetData?.longitude)}</span> - <span style={{ color: getStatusColor(status) }}>{status}</span>
                    <div style={{ fontSize: '11px', color: '#666', marginTop: '2px' }}>
                      Score: {(() => {
                        const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planetName);
                        if (dignity === 'Exalted') return isNaturalBenefic ? '+2.0' : '+1.5';
                        else if (dignity === 'Own') return isNaturalBenefic ? '+1.5' : '+1.0';
                        else if (dignity === 'Debilitated') return isNaturalBenefic ? '-1.0' : '-1.5';
                        else return isNaturalBenefic ? '+0.5' : '-0.3';
                      })()} (Dignity: {dignity === 'Exalted' ? '+3' : dignity === 'Own' ? '+2' : dignity === 'Debilitated' ? '-3' : '0'}, Nature: {['Jupiter', 'Venus', 'Moon'].includes(planetName) ? 'Benefic +0.5' : 'Malefic -0.3'})
                    </div>
                  </div>
                  {lordships.length > 0 && <div><strong>Lord of:</strong> {lordships.join(', ')}</div>}
                  <div><strong>Nakshatra Lord:</strong> {nakshatraLord} (<span style={{ color: friendshipWithNakLord === 'Friend' ? '#4caf50' : friendshipWithNakLord === 'Enemy' ? '#f44336' : '#666' }}>{friendshipWithNakLord}</span>)</div>
                  {conjunctions.length > 0 && (
                    <div style={{ margin: '4px 0' }}>
                      <strong>Conjunct:</strong> {conjunctions.map(planet => {
                        const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                        const effect = planetName === 'Venus' ? 
                          (isNaturalBenefic ? 'Enhances romance' : planet === 'Mars' ? 'Passionate marriage' : planet === 'Saturn' ? 'Delayed marriage' : planet === 'Rahu' ? 'Foreign spouse' : 'Mixed influence') :
                          planetName === 'Jupiter' ? 
                          (isNaturalBenefic ? 'Wise spouse' : planet === 'Mars' ? 'Religious spouse' : planet === 'Saturn' ? 'Mature spouse' : 'Mixed influence') :
                          (isNaturalBenefic ? 'Beneficial' : 'Challenging');
                        return (
                          <div key={planet} style={{ marginLeft: '10px', fontSize: '11px' }}>
                            <span style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336' }}>{planet}</span> - {effect}
                          </div>
                        );
                      })}
                    </div>
                  )}
                  {aspects.length > 0 && (
                    <div style={{ margin: '4px 0' }}>
                      <strong>Aspected by:</strong> {aspects.map(({ planet, aspect }) => {
                        const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                        return (
                          <span key={`${planet}-${aspect}`} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '8px' }}>
                            {planet} ({aspect})
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
        
        {/* Aspecting Planets */}
        {aspectingPlanets.length > 0 && (
          <div style={{ 
            marginTop: '16px', 
            padding: window.innerWidth < 768 ? '12px' : '16px', 
            background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.08) 0%, rgba(76, 175, 80, 0.12) 100%)', 
            borderRadius: '8px',
            border: '1px solid rgba(76, 175, 80, 0.2)'
          }}>
            <h4 style={{ 
              margin: '0 0 16px 0', 
              color: '#4caf50', 
              fontSize: '16px', 
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              🎯 Planets Aspecting 7th House
            </h4>
            <div className="section-score-header" style={{ marginBottom: '12px' }}>
              <span className="section-score">Combined Aspect Effect: {(() => {
                let aspectScore = 0;
                aspectingPlanets.forEach(planetName => {
                  const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planetName);
                  const lordships = getHouseLordship(planetName, ascendantSign);
                  const isMaleficLord = lordships.some(h => [6, 8, 12].includes(h));
                  if (isNaturalBenefic && !isMaleficLord) aspectScore += 0.5;
                  else if (['Rahu', 'Ketu'].includes(planetName)) aspectScore -= 0.3;
                  else aspectScore -= 0.2;
                });
                return aspectScore >= 0 ? `+${aspectScore.toFixed(1)}` : aspectScore.toFixed(1);
              })()}/10</span>
            </div>
            <div style={{ display: 'grid', gap: window.innerWidth < 768 ? '8px' : '10px' }}>
              {aspectingPlanets.map(planetName => {
                const planetData = chartData?.planets?.[planetName];
                const lordships = getHouseLordship(planetName, ascendantSign);
                const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planetName);
                const isMaleficLord = lordships.some(h => [6, 8, 12].includes(h));
                const aspectNature = isNaturalBenefic && !isMaleficLord ? 'Beneficial' : 'Challenging';
                const aspectEffect = planetName === 'Jupiter' ? 'Blesses with wisdom & good spouse' :
                                   planetName === 'Venus' ? 'Enhances love & attraction' :
                                   planetName === 'Mars' ? 'Adds passion but may cause conflicts' :
                                   planetName === 'Saturn' ? 'Delays marriage but ensures stability' :
                                   planetName === 'Rahu' ? 'Unconventional/foreign connections' :
                                   planetName === 'Ketu' ? 'Spiritual approach to marriage' :
                                   aspectNature + ' influence';
                
                return (
                  <div key={planetName} style={{ 
                    padding: window.innerWidth < 768 ? '8px' : '12px', 
                    background: 'rgba(255,255,255,0.9)', 
                    borderRadius: '6px',
                    border: '1px solid rgba(76, 175, 80, 0.1)',
                    borderLeft: `3px solid ${aspectNature === 'Beneficial' ? '#4caf50' : '#f44336'}`,
                    fontSize: window.innerWidth < 768 ? '12px' : '13px'
                  }}>
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      marginBottom: '6px'
                    }}>
                      <strong style={{ fontSize: '14px', color: '#333' }}>{planetName}</strong>
                      <span style={{ 
                        color: aspectNature === 'Beneficial' ? '#4caf50' : '#f44336',
                        background: aspectNature === 'Beneficial' ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '500'
                      }}>{aspectNature}</span>
                    </div>
                    {lordships.length > 0 && (
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                        Lord of: {lordships.join(', ')}
                      </div>
                    )}
                    <div style={{ 
                      fontSize: '12px', 
                      fontStyle: 'italic', 
                      color: '#555',
                      background: 'rgba(76, 175, 80, 0.05)',
                      padding: '4px 8px',
                      borderRadius: '4px'
                    }}>{aspectEffect}</div>
                    <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
                      Aspect Score: {(() => {
                        const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planetName);
                        const lordships = getHouseLordship(planetName, ascendantSign);
                        const isMaleficLord = lordships.some(h => [6, 8, 12].includes(h));
                        if (isNaturalBenefic && !isMaleficLord) return '+0.5';
                        else if (['Rahu', 'Ketu'].includes(planetName)) return '-0.3';
                        else return '-0.2';
                      })()} (Nature: {['Jupiter', 'Venus', 'Moon'].includes(planetName) ? 'Benefic' : ['Rahu', 'Ketu'].includes(planetName) ? 'Shadow' : 'Malefic'}, Lordship: {(() => {
                        const lordships = getHouseLordship(planetName, ascendantSign);
                        const isMaleficLord = lordships.some(h => [6, 8, 12].includes(h));
                        return isMaleficLord ? 'Malefic houses' : 'Neutral/Benefic houses';
                      })()})
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Karaka Analysis */}
      <div className="analysis-section">
        <h3>🌟 Marriage Significators</h3>
        <div className="karaka-grid">
          <div className="karaka-card">
            <h4>♀ Venus (Romance)</h4>
            <div className="karaka-details">
              <p><strong>Sign:</strong> {karakas.venus?.sign || 'N/A'}</p>
              <p><strong>House:</strong> {karakas.venus?.house || 'N/A'}</p>
              <p><strong>Dignity:</strong> <span style={{ color: karakas.venus?.dignity === 'Exalted' ? '#4caf50' : karakas.venus?.dignity === 'Debilitated' ? '#f44336' : karakas.venus?.dignity === 'Own' ? '#2196f3' : '#666' }}>{karakas.venus?.dignity || 'N/A'}</span></p>
              <p><strong>Strength:</strong> {karakas.venus?.strength || 0}/10</p>
              {venusAnalysis && (() => {
                const specialConditions = analyzeSpecialConditions(birthDetails, chartData);
                const venusConditions = [
                  ...specialConditions.combustionConditions.filter(c => c.planet === 'Venus'),
                  ...specialConditions.dagdhaConditions.filter(c => c.planet === 'Venus'),
                  ...specialConditions.tithiShunyaConditions.filter(c => c.planet === 'Venus')
                ];
                return (
                  <div style={{ marginTop: '10px', padding: '8px', background: 'rgba(233, 30, 99, 0.1)', borderRadius: '4px' }}>
                    {venusAnalysis.lordships.length > 0 && (
                      <p style={{ margin: '2px 0', fontSize: '12px' }}>
                        <strong>Lord of:</strong> {venusAnalysis.lordships.join(', ')}
                      </p>
                    )}
                    <p style={{ margin: '2px 0', fontSize: '12px' }}>
                      <strong>Status:</strong> <span style={{ color: getStatusColor(venusAnalysis.status) }}>{venusAnalysis.status}</span>
                    </p>
                    <p style={{ margin: '2px 0', fontSize: '12px' }}>
                      <strong>Nakshatra Lord:</strong> {venusAnalysis.nakshatraLord} (<span style={{ color: venusAnalysis.friendshipWithNakLord === 'Friend' ? '#4caf50' : venusAnalysis.friendshipWithNakLord === 'Enemy' ? '#f44336' : '#666' }}>{venusAnalysis.friendshipWithNakLord}</span>)
                    </p>
                    {venusConditions.length > 0 && (
                      <div style={{ margin: '4px 0', padding: '4px', background: 'rgba(244, 67, 54, 0.1)', borderRadius: '3px' }}>
                        <strong style={{ color: '#f44336', fontSize: '11px' }}>⚠️ Special Conditions:</strong>
                        {venusConditions.map((condition, idx) => (
                          <div key={idx} style={{ fontSize: '10px', color: '#f44336', marginLeft: '8px' }}>
                            {condition.condition}{condition.distance ? ` (${condition.distance}°)` : ''} - {condition.effect}
                          </div>
                        ))}
                      </div>
                    )}
                  {getConjunctions('Venus').length > 0 && (
                    <div style={{ margin: '4px 0', fontSize: '12px' }}>
                      <strong>Conjunct:</strong> {getConjunctions('Venus').map(planet => {
                        const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                        const effect = isNaturalBenefic ? 'Enhances romance' : planet === 'Mars' ? 'Adds passion/conflict' : planet === 'Saturn' ? 'Delays/restricts' : planet === 'Rahu' ? 'Unconventional desires' : planet === 'Ketu' ? 'Spiritual detachment' : 'Mixed influence';
                        return (
                          <div key={planet} style={{ marginLeft: '10px', fontSize: '11px' }}>
                            <span style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336' }}>{planet}</span> - {effect}
                          </div>
                        );
                      })}
                    </div>
                  )}
                  {getAspectsTo('Venus').length > 0 && (
                    <p style={{ margin: '2px 0', fontSize: '12px' }}>
                      <strong>Aspected by:</strong> {getAspectsTo('Venus').map(({ planet, aspect }) => {
                        const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                        return <span key={`${planet}-${aspect}`} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '5px' }}>{planet} ({aspect})</span>;
                      })}
                    </p>
                  )}
                  <div style={{ margin: '6px 0', padding: '6px', background: 'rgba(233, 30, 99, 0.05)', borderRadius: '4px' }}>
                    <strong style={{ fontSize: '11px', color: '#e91e63' }}>💯 Score Breakdown:</strong>
                    <div style={{ fontSize: '10px', color: '#666', marginTop: '2px' }}>
                      Base: {karakas.venus?.strength || 0}/10 → Weighted: {frontendOverallScore.components.venus_d1}/1.5<br/>
                      Factors: Dignity ({venusAnalysis.dignity}), Status ({venusAnalysis.status}), Lordships ({venusAnalysis.lordships.join(', ')})
                    </div>
                  </div>
                </div>
                );
              })()}
            </div>
          </div>
          <div className="karaka-card">
            <h4>🎯 {darakarka} (Darakarka - Spouse)</h4>
            <div className="karaka-details">
              <p><strong>Sign:</strong> {karakas[darakarka?.toLowerCase()]?.sign || (darakarka ? signNames[chartData?.planets?.[darakarka]?.sign || 0] : 'N/A')}</p>
              <p><strong>House:</strong> {karakas[darakarka?.toLowerCase()]?.house || 'N/A'}</p>
              <p><strong>Dignity:</strong> <span style={{ color: karakas[darakarka?.toLowerCase()]?.dignity === 'Exalted' ? '#4caf50' : karakas[darakarka?.toLowerCase()]?.dignity === 'Debilitated' ? '#f44336' : karakas[darakarka?.toLowerCase()]?.dignity === 'Own' ? '#2196f3' : '#666' }}>{karakas[darakarka?.toLowerCase()]?.dignity || (darakarka ? getPlanetDignity(darakarka, chartData?.planets?.[darakarka]?.sign || 0) : 'N/A')}</span></p>
              <p><strong>Strength:</strong> {karakas[darakarka?.toLowerCase()]?.strength || 0}/10 → <strong>{frontendOverallScore.components.darakarka}/0.5</strong></p>
              {(() => {
                const darakarkaAnalysis = analyzeKaraka(darakarka);
                return darakarkaAnalysis && (
                  <div style={{ marginTop: '10px', padding: '8px', background: 'rgba(63, 81, 181, 0.1)', borderRadius: '4px' }}>
                    {darakarkaAnalysis.lordships.length > 0 && (
                      <p style={{ margin: '2px 0', fontSize: '12px' }}>
                        <strong>Lord of:</strong> {darakarkaAnalysis.lordships.join(', ')}
                      </p>
                    )}
                    <p style={{ margin: '2px 0', fontSize: '12px' }}>
                      <strong>Status:</strong> <span style={{ color: getStatusColor(darakarkaAnalysis.status) }}>{darakarkaAnalysis.status}</span>
                    </p>
                    <p style={{ margin: '2px 0', fontSize: '12px' }}>
                      <strong>Nakshatra Lord:</strong> {darakarkaAnalysis.nakshatraLord} (<span style={{ color: darakarkaAnalysis.friendshipWithNakLord === 'Friend' ? '#4caf50' : darakarkaAnalysis.friendshipWithNakLord === 'Enemy' ? '#f44336' : '#666' }}>{darakarkaAnalysis.friendshipWithNakLord}</span>)
                    </p>
                    {getConjunctions(darakarka).length > 0 && (
                      <div style={{ margin: '4px 0', fontSize: '12px' }}>
                        <strong>Conjunct:</strong> {getConjunctions(darakarka).map(planet => {
                          const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                          const effect = darakarka === 'Venus' ? 
                            (isNaturalBenefic ? 'Enhances spouse beauty' : planet === 'Mars' ? 'Passionate spouse' : planet === 'Saturn' ? 'Mature spouse' : 'Mixed influence') :
                            darakarka === 'Jupiter' ? 
                            (isNaturalBenefic ? 'Wise spouse' : planet === 'Mars' ? 'Religious spouse' : 'Mixed influence') :
                            (isNaturalBenefic ? 'Beneficial for spouse' : 'Challenging for spouse');
                          return (
                            <div key={planet} style={{ marginLeft: '10px', fontSize: '11px' }}>
                              <span style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336' }}>{planet}</span> - {effect}
                            </div>
                          );
                        })}
                      </div>
                    )}
                    {getAspectsTo(darakarka).length > 0 && (
                      <div style={{ margin: '4px 0', fontSize: '12px' }}>
                        <strong>Aspected by:</strong> {getAspectsTo(darakarka).map(({ planet, aspect }) => {
                          const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                          return <span key={`${planet}-${aspect}`} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '5px' }}>{planet} ({aspect})</span>;
                        })}
                      </div>
                    )}
                  </div>
                );
              })()}
              <div style={{ margin: '6px 0', padding: '6px', background: 'rgba(63, 81, 181, 0.05)', borderRadius: '4px' }}>
                <strong style={{ fontSize: '11px', color: '#3f51b5' }}>💯 Score Breakdown:</strong>
                <div style={{ fontSize: '10px', color: '#666', marginTop: '2px' }}>
                  Base: {(() => {
                    const darakarkaStrength = karakas[darakarka?.toLowerCase()]?.strength || 
                                              (darakarka && chartData?.planets?.[darakarka] ? 
                                               Math.min(10, Math.max(1, 5 + (getPlanetDignity(darakarka, chartData.planets[darakarka].sign) === 'Exalted' ? 3 : 
                                                                              getPlanetDignity(darakarka, chartData.planets[darakarka].sign) === 'Own' ? 2 : 
                                                                              getPlanetDignity(darakarka, chartData.planets[darakarka].sign) === 'Debilitated' ? -3 : 0))) : 0);
                    return darakarkaStrength;
                  })()}/10 → Weighted: {frontendOverallScore.components.darakarka}/0.5<br/>
                  Factors: Dignity ({darakarka ? getPlanetDignity(darakarka, chartData?.planets?.[darakarka]?.sign || 0) : 'N/A'}), Lordships ({darakarka ? getHouseLordship(darakarka, ascendantSign).join(', ') : 'N/A'})
                </div>
              </div>
            </div>
          </div>
          <div className="karaka-card">
            <h4>♃ Jupiter (Wisdom)</h4>
            <div className="karaka-details">
              <p><strong>Sign:</strong> {karakas.jupiter?.sign || 'N/A'}</p>
              <p><strong>House:</strong> {karakas.jupiter?.house || 'N/A'}</p>
              <p><strong>Dignity:</strong> <span style={{ color: karakas.jupiter?.dignity === 'Exalted' ? '#4caf50' : karakas.jupiter?.dignity === 'Debilitated' ? '#f44336' : karakas.jupiter?.dignity === 'Own' ? '#2196f3' : '#666' }}>{karakas.jupiter?.dignity || 'N/A'}</span></p>
              <p><strong>Strength:</strong> {karakas.jupiter?.strength || 0}/10</p>
              {jupiterAnalysis && (
                <div style={{ marginTop: '10px', padding: '8px', background: 'rgba(255, 193, 7, 0.1)', borderRadius: '4px' }}>
                  {jupiterAnalysis.lordships.length > 0 && (
                    <p style={{ margin: '2px 0', fontSize: '12px' }}>
                      <strong>Lord of:</strong> {jupiterAnalysis.lordships.join(', ')}
                    </p>
                  )}
                  <p style={{ margin: '2px 0', fontSize: '12px' }}>
                    <strong>Status:</strong> <span style={{ color: getStatusColor(jupiterAnalysis.status) }}>{jupiterAnalysis.status}</span>
                  </p>
                  <p style={{ margin: '2px 0', fontSize: '12px' }}>
                    <strong>Nakshatra Lord:</strong> {jupiterAnalysis.nakshatraLord} (<span style={{ color: jupiterAnalysis.friendshipWithNakLord === 'Friend' ? '#4caf50' : jupiterAnalysis.friendshipWithNakLord === 'Enemy' ? '#f44336' : '#666' }}>{jupiterAnalysis.friendshipWithNakLord}</span>)
                  </p>
                  {getConjunctions('Jupiter').length > 0 && (
                    <div style={{ margin: '4px 0', fontSize: '12px' }}>
                      <strong>Conjunct:</strong> {getConjunctions('Jupiter').map(planet => {
                        const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                        const effect = isNaturalBenefic ? 'Enhances wisdom in marriage' : planet === 'Mars' ? 'Righteous but aggressive' : planet === 'Saturn' ? 'Mature/delayed marriage' : planet === 'Rahu' ? 'Foreign/unconventional spouse' : planet === 'Ketu' ? 'Spiritual marriage' : 'Mixed influence';
                        return (
                          <div key={planet} style={{ marginLeft: '10px', fontSize: '11px' }}>
                            <span style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336' }}>{planet}</span> - {effect}
                          </div>
                        );
                      })}
                    </div>
                  )}
                  {getAspectsTo('Jupiter').length > 0 && (
                    <p style={{ margin: '2px 0', fontSize: '12px' }}>
                      <strong>Aspected by:</strong> {getAspectsTo('Jupiter').map(({ planet, aspect }) => {
                        const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                        return <span key={`${planet}-${aspect}`} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '5px' }}>{planet} ({aspect})</span>;
                      })}
                    </p>
                  )}
                  <div style={{ margin: '6px 0', padding: '6px', background: 'rgba(255, 193, 7, 0.05)', borderRadius: '4px' }}>
                    <strong style={{ fontSize: '11px', color: '#f57c00' }}>💯 Score Breakdown:</strong>
                    <div style={{ fontSize: '10px', color: '#666', marginTop: '2px' }}>
                      Base: {karakas.jupiter?.strength || 0}/10 → Weighted: {frontendOverallScore.components.jupiter_d1}/1.0<br/>
                      Factors: Dignity ({jupiterAnalysis.dignity}), Status ({jupiterAnalysis.status}), Lordships ({jupiterAnalysis.lordships.join(', ')})
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Additional Houses Analysis */}
      <div className="analysis-section">
        <h3>🏘️ Supporting Houses Analysis</h3>
        <div className="supporting-houses-grid">
          {/* 2nd House - Family */}
          <div style={{ padding: '12px', background: 'rgba(103, 58, 183, 0.1)', borderRadius: '8px', border: '1px solid rgba(103, 58, 183, 0.2)' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#673ab7', fontSize: '14px' }}>👨‍👩‍👧‍👦 2nd House (Family)</h4>
            <div style={{ fontSize: '12px' }}>
              <div><strong>Sign:</strong> {signNames[chartData?.houses?.[1]?.sign || 0]}</div>
              <div><strong>Lord:</strong> {houseLords[chartData?.houses?.[1]?.sign || 0]}</div>
              {(() => {
                const houseSign = chartData?.houses?.[1]?.sign || 0;
                const houseLord = houseLords[houseSign];
                const lordData = chartData?.planets?.[houseLord];
                const occupants = Object.entries(chartData?.planets || {}).filter(([name, data]) => data.sign === houseSign);
                const aspectingPlanets = getAspectingPlanets(1, chartData);
                
                return (
                  <>
                    {lordData && (
                      <div style={{ marginTop: '6px', padding: '6px', background: 'rgba(255,255,255,0.3)', borderRadius: '4px' }}>
                        <div><strong>Lord Status:</strong> <span style={{ color: getStatusColor(getPlanetStatus(houseLord, lordData.sign, getHouseLordship(houseLord, ascendantSign))) }}>{getPlanetStatus(houseLord, lordData.sign, getHouseLordship(houseLord, ascendantSign))}</span></div>
                      </div>
                    )}
                    {occupants.length > 0 && (
                      <div style={{ marginTop: '4px' }}>
                        <strong>Occupants:</strong> {occupants.map(([name]) => {
                          const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(name);
                          return <span key={name} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '4px' }}>{name}</span>;
                        })}
                      </div>
                    )}
                    {aspectingPlanets.length > 0 && (
                      <div style={{ marginTop: '4px' }}>
                        <strong>Aspected by:</strong> {aspectingPlanets.map(planet => {
                          const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                          return <span key={planet} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '4px' }}>{planet}</span>;
                        })}
                      </div>
                    )}
                    <div style={{ marginTop: '4px', fontSize: '11px', fontStyle: 'italic', color: '#555' }}>
                      Family wealth, speech, values in marriage
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
          
          {/* 5th House - Romance */}
          <div style={{ padding: '12px', background: 'rgba(255, 87, 34, 0.1)', borderRadius: '8px', border: '1px solid rgba(255, 87, 34, 0.2)' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#ff5722', fontSize: '14px' }}>💕 5th House (Romance)</h4>
            <div style={{ fontSize: '12px' }}>
              <div><strong>Sign:</strong> {signNames[chartData?.houses?.[4]?.sign || 0]}</div>
              <div><strong>Lord:</strong> {houseLords[chartData?.houses?.[4]?.sign || 0]}</div>
              {(() => {
                const houseSign = chartData?.houses?.[4]?.sign || 0;
                const houseLord = houseLords[houseSign];
                const lordData = chartData?.planets?.[houseLord];
                const occupants = Object.entries(chartData?.planets || {}).filter(([name, data]) => data.sign === houseSign);
                const aspectingPlanets = getAspectingPlanets(4, chartData);
                
                return (
                  <>
                    {lordData && (
                      <div style={{ marginTop: '6px', padding: '6px', background: 'rgba(255,255,255,0.3)', borderRadius: '4px' }}>
                        <div><strong>Lord Status:</strong> <span style={{ color: getStatusColor(getPlanetStatus(houseLord, lordData.sign, getHouseLordship(houseLord, ascendantSign))) }}>{getPlanetStatus(houseLord, lordData.sign, getHouseLordship(houseLord, ascendantSign))}</span></div>
                      </div>
                    )}
                    {occupants.length > 0 && (
                      <div style={{ marginTop: '4px' }}>
                        <strong>Occupants:</strong> {occupants.map(([name]) => {
                          const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(name);
                          return <span key={name} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '4px' }}>{name}</span>;
                        })}
                      </div>
                    )}
                    {aspectingPlanets.length > 0 && (
                      <div style={{ marginTop: '4px' }}>
                        <strong>Aspected by:</strong> {aspectingPlanets.map(planet => {
                          const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                          return <span key={planet} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '4px' }}>{planet}</span>;
                        })}
                      </div>
                    )}
                    <div style={{ marginTop: '4px', fontSize: '11px', fontStyle: 'italic', color: '#555' }}>
                      Love affairs, romance, progeny, creativity
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
          
          {/* 8th House - Longevity */}
          <div style={{ padding: '12px', background: 'rgba(121, 85, 72, 0.1)', borderRadius: '8px', border: '1px solid rgba(121, 85, 72, 0.2)' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#795548', fontSize: '14px' }}>⏳ 8th House (Longevity)</h4>
            <div style={{ fontSize: '12px' }}>
              <div><strong>Sign:</strong> {signNames[chartData?.houses?.[7]?.sign || 0]}</div>
              <div><strong>Lord:</strong> {houseLords[chartData?.houses?.[7]?.sign || 0]}</div>
              {(() => {
                const houseSign = chartData?.houses?.[7]?.sign || 0;
                const houseLord = houseLords[houseSign];
                const lordData = chartData?.planets?.[houseLord];
                const occupants = Object.entries(chartData?.planets || {}).filter(([name, data]) => data.sign === houseSign);
                const aspectingPlanets = getAspectingPlanets(7, chartData);
                
                return (
                  <>
                    {lordData && (
                      <div style={{ marginTop: '6px', padding: '6px', background: 'rgba(255,255,255,0.3)', borderRadius: '4px' }}>
                        <div><strong>Lord Status:</strong> <span style={{ color: getStatusColor(getPlanetStatus(houseLord, lordData.sign, getHouseLordship(houseLord, ascendantSign))) }}>{getPlanetStatus(houseLord, lordData.sign, getHouseLordship(houseLord, ascendantSign))}</span></div>
                      </div>
                    )}
                    {occupants.length > 0 && (
                      <div style={{ marginTop: '4px' }}>
                        <strong>Occupants:</strong> {occupants.map(([name]) => {
                          const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(name);
                          return <span key={name} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '4px' }}>{name}</span>;
                        })}
                      </div>
                    )}
                    {aspectingPlanets.length > 0 && (
                      <div style={{ marginTop: '4px' }}>
                        <strong>Aspected by:</strong> {aspectingPlanets.map(planet => {
                          const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                          return <span key={planet} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '4px' }}>{planet}</span>;
                        })}
                      </div>
                    )}
                    <div style={{ marginTop: '4px', fontSize: '11px', fontStyle: 'italic', color: '#555' }}>
                      Marital longevity, transformations, obstacles
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
          
          {/* 11th House - Gains */}
          <div style={{ padding: '12px', background: 'rgba(0, 150, 136, 0.1)', borderRadius: '8px', border: '1px solid rgba(0, 150, 136, 0.2)' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#009688', fontSize: '14px' }}>💰 11th House (Gains)</h4>
            <div style={{ fontSize: '12px' }}>
              <div><strong>Sign:</strong> {signNames[chartData?.houses?.[10]?.sign || 0]}</div>
              <div><strong>Lord:</strong> {houseLords[chartData?.houses?.[10]?.sign || 0]}</div>
              {(() => {
                const houseSign = chartData?.houses?.[10]?.sign || 0;
                const houseLord = houseLords[houseSign];
                const lordData = chartData?.planets?.[houseLord];
                const occupants = Object.entries(chartData?.planets || {}).filter(([name, data]) => data.sign === houseSign);
                const aspectingPlanets = getAspectingPlanets(10, chartData);
                
                return (
                  <>
                    {lordData && (
                      <div style={{ marginTop: '6px', padding: '6px', background: 'rgba(255,255,255,0.3)', borderRadius: '4px' }}>
                        <div><strong>Lord Status:</strong> <span style={{ color: getStatusColor(getPlanetStatus(houseLord, lordData.sign, getHouseLordship(houseLord, ascendantSign))) }}>{getPlanetStatus(houseLord, lordData.sign, getHouseLordship(houseLord, ascendantSign))}</span></div>
                      </div>
                    )}
                    {occupants.length > 0 && (
                      <div style={{ marginTop: '4px' }}>
                        <strong>Occupants:</strong> {occupants.map(([name]) => {
                          const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(name);
                          return <span key={name} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '4px' }}>{name}</span>;
                        })}
                      </div>
                    )}
                    {aspectingPlanets.length > 0 && (
                      <div style={{ marginTop: '4px' }}>
                        <strong>Aspected by:</strong> {aspectingPlanets.map(planet => {
                          const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
                          return <span key={planet} style={{ color: isNaturalBenefic ? '#4caf50' : '#f44336', marginRight: '4px' }}>{planet}</span>;
                        })}
                      </div>
                    )}
                    <div style={{ marginTop: '4px', fontSize: '11px', fontStyle: 'italic', color: '#555' }}>
                      Gains from marriage, fulfillment of desires
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        </div>
      </div>


      {/* D9 Navamsa Analysis */}
      {d9Analysis && !d9Analysis.error && (
        <div className="analysis-section">
          <h3>🌟 D9 Navamsa Analysis</h3>
          <div className="d9-overview">
            <div className="d9-strength-indicator">
              <span className="d9-strength-label">Overall D9 Strength:</span>
              <div className="d9-strength-bar">
                <div 
                  className="d9-strength-fill" 
                  style={{ 
                    width: `${(d9Analysis.overall_strength || 0) * 10}%`,
                    background: d9Analysis.overall_strength >= 7 ? '#4caf50' : d9Analysis.overall_strength >= 5 ? '#ff9800' : '#f44336'
                  }}
                ></div>
              </div>
              <span className="d9-strength-value">{d9Analysis.overall_strength || 0}/10</span>
            </div>
            <div className="d9-interpretation">
              <p>{d9Analysis.interpretation || 'D9 analysis provides deeper insights into marital harmony and spouse characteristics.'}</p>
            </div>
          </div>
          
          <div className="d9-details-grid">
            {/* D9 7th House */}
            <div className="d9-detail-card">
              <h4>🏠 7th House in D9</h4>
              <div className="d9-card-content">
                <div className="d9-info-row">
                  <span className="d9-label">Sign:</span>
                  <span className="d9-value">{d9Analysis.seventh_house_d9?.sign_name || 'N/A'}</span>
                </div>
                <div className="d9-info-row">
                  <span className="d9-label">Lord:</span>
                  <span className="d9-value">{d9Analysis.seventh_house_d9?.lord || 'N/A'}</span>
                </div>
                <div className="d9-info-row">
                  <span className="d9-label">Strength:</span>
                  <span className="d9-value" style={{ 
                    color: (d9Analysis.seventh_house_d9?.strength || 0) >= 7 ? '#4caf50' : 
                           (d9Analysis.seventh_house_d9?.strength || 0) >= 5 ? '#ff9800' : '#f44336'
                  }}>
                    {(() => {
                      // Calculate corrected strength if planets are present
                      if (d9Analysis.seventh_house_d9?.planets?.length > 0 && d9Analysis.seventh_house_d9?.sign_name) {
                        const signIndex = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'].indexOf(d9Analysis.seventh_house_d9.sign_name);
                        const correctedStrength = calculateD9HouseStrength(signIndex, d9Analysis.seventh_house_d9.planets, { planets: chartData?.planets });
                        return correctedStrength;
                      }
                      return d9Analysis.seventh_house_d9?.strength || 0;
                    })()}/10
                  </span>
                </div>
                {d9Analysis.seventh_house_d9?.planets?.length > 0 && (
                  <div className="d9-info-row">
                    <span className="d9-label">Planets:</span>
                    <div className="d9-planets-list">
                      {d9Analysis.seventh_house_d9.planets.map(planet => {
                        // Get D9 planet dignity from backend data or calculate it
                        const planetD9Data = d9Analysis[`${planet.toLowerCase()}_d9`];
                        let dignity = planetD9Data?.dignity;
                        
                        // If backend doesn't provide dignity, calculate it based on D9 sign
                        if (!dignity && d9Analysis.seventh_house_d9?.sign_name) {
                          const signIndex = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'].indexOf(d9Analysis.seventh_house_d9.sign_name);
                          dignity = getPlanetDignity(planet, signIndex);
                        }
                        
                        dignity = dignity || 'Neutral';
                        return (
                          <span key={planet} className="d9-planet-item">
                            {planet}
                            <span className="d9-planet-dignity" style={{
                              color: dignity === 'Exalted' ? '#4caf50' : 
                                     dignity === 'Debilitated' ? '#f44336' : 
                                     dignity === 'Own' ? '#2196f3' : '#666'
                            }}>
                              ({dignity})
                            </span>
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            {/* Venus in D9 */}
            <div className="d9-detail-card">
              <h4>♀ Venus in D9</h4>
              <div className="d9-card-content">
                <div className="d9-info-row">
                  <span className="d9-label">Sign:</span>
                  <span className="d9-value">{d9Analysis.venus_d9?.sign_name || 'N/A'}</span>
                </div>
                <div className="d9-info-row">
                  <span className="d9-label">Dignity:</span>
                  <span className="d9-value" style={{ 
                    color: d9Analysis.venus_d9?.dignity === 'Exalted' ? '#4caf50' : 
                           d9Analysis.venus_d9?.dignity === 'Debilitated' ? '#f44336' : 
                           d9Analysis.venus_d9?.dignity === 'Own' ? '#2196f3' : '#666'
                  }}>
                    {d9Analysis.venus_d9?.dignity || 'N/A'}
                  </span>
                </div>
                <div className="d9-info-row">
                  <span className="d9-label">Strength:</span>
                  <span className="d9-value" style={{ 
                    color: (d9Analysis.venus_d9?.strength || 0) >= 7 ? '#4caf50' : 
                           (d9Analysis.venus_d9?.strength || 0) >= 5 ? '#ff9800' : '#f44336'
                  }}>
                    {d9Analysis.venus_d9?.strength || 0}/10
                  </span>
                </div>
                <div className="d9-effect">
                  {d9Analysis.venus_d9?.dignity === 'Exalted' ? '💖 Exceptional romantic fulfillment' :
                   d9Analysis.venus_d9?.dignity === 'Own' ? '💕 Natural charm and attraction' :
                   d9Analysis.venus_d9?.dignity === 'Debilitated' ? '💔 Relationship challenges possible' :
                   '💝 Moderate romantic prospects'}
                </div>
              </div>
            </div>
            
            {/* Jupiter in D9 */}
            <div className="d9-detail-card">
              <h4>♃ Jupiter in D9</h4>
              <div className="d9-card-content">
                <div className="d9-info-row">
                  <span className="d9-label">Sign:</span>
                  <span className="d9-value">{d9Analysis.jupiter_d9?.sign_name || 'N/A'}</span>
                </div>
                <div className="d9-info-row">
                  <span className="d9-label">Dignity:</span>
                  <span className="d9-value" style={{ 
                    color: d9Analysis.jupiter_d9?.dignity === 'Exalted' ? '#4caf50' : 
                           d9Analysis.jupiter_d9?.dignity === 'Debilitated' ? '#f44336' : 
                           d9Analysis.jupiter_d9?.dignity === 'Own' ? '#2196f3' : '#666'
                  }}>
                    {d9Analysis.jupiter_d9?.dignity || 'N/A'}
                  </span>
                </div>
                <div className="d9-info-row">
                  <span className="d9-label">Strength:</span>
                  <span className="d9-value" style={{ 
                    color: (d9Analysis.jupiter_d9?.strength || 0) >= 7 ? '#4caf50' : 
                           (d9Analysis.jupiter_d9?.strength || 0) >= 5 ? '#ff9800' : '#f44336'
                  }}>
                    {d9Analysis.jupiter_d9?.strength || 0}/10
                  </span>
                </div>
                <div className="d9-effect">
                  {d9Analysis.jupiter_d9?.dignity === 'Exalted' ? '🙏 Highly spiritual and wise spouse' :
                   d9Analysis.jupiter_d9?.dignity === 'Own' ? '📚 Knowledgeable and dharmic partner' :
                   d9Analysis.jupiter_d9?.dignity === 'Debilitated' ? '⚠️ Lack of wisdom in marriage decisions' :
                   '🤝 Balanced approach to marriage'}
                </div>
              </div>
            </div>
          </div>
          
          <div className="d9-significance">
            <h4>🔍 What is D9 Chart? (Simple Explanation)</h4>
            <div className="significance-points">
              <div className="significance-point">
                <span className="point-icon">🌟</span>
                <span className="point-text">Think of D9 as your "marriage soul chart" - it shows how you'll truly connect with your spouse beyond surface attraction</span>
              </div>
              <div className="significance-point">
                <span className="point-icon">💫</span>
                <span className="point-text">If planets are strong in D9, it means your marriage will fulfill your deepest desires and bring lasting happiness</span>
              </div>
              <div className="significance-point">
                <span className="point-icon">⚖️</span>
                <span className="point-text">Ancient astrology texts say D9 is 30% of your marriage analysis - it's that important!</span>
              </div>
              <div className="significance-point">
                <span className="point-icon">🎯</span>
                <span className="point-text">D9 reveals what kind of person your spouse will be and how well you'll understand each other</span>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {d9Analysis?.error && (
        <div className="analysis-section">
          <h3>🌟 D9 Navamsa Analysis</h3>
          <div className="d9-error">
            <p>⚠️ D9 analysis temporarily unavailable: {d9Analysis.error}</p>
            <p>Marriage analysis continues with D1 chart only.</p>
          </div>
        </div>
      )}


    </div>
  );
};

const CompatibilityAnalysis = ({ analysis }) => {
  // Placeholder for compatibility analysis
  return (
    <div className="compatibility-analysis">
      <div className="coming-soon">
        <h3>🔄 Compatibility Analysis</h3>
        <p>Two-chart compatibility analysis coming soon...</p>
        <p>This will include Guna Milan (Ashtakoot) scoring and detailed compatibility assessment.</p>
      </div>
    </div>
  );
};

const SpecialConditionsSection = ({ chartData, birthDetails }) => {
  const specialConditions = analyzeSpecialConditions(birthDetails, chartData);
  const signNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
  
  return (
    <div className="analysis-section">
      <h3>✨ Special Conditions Analysis</h3>
      
      {/* Yogi/Avayogi */}
      <div className="special-condition-card">
        <h4>🧘 Yogi & Avayogi Planets</h4>
        <div className="yogi-avayogi-grid">
          <div className="yogi-card">
            <div className="condition-header">
              <span className="condition-icon">✨</span>
              <span className="condition-title">Yogi Planet</span>
            </div>
            <div className="condition-value positive">{specialConditions.yogiAvayogi.yogi || 'N/A'}</div>
            <div className="condition-effect">Brings auspiciousness and positive results</div>
          </div>
          <div className="avayogi-card">
            <div className="condition-header">
              <span className="condition-icon">⚠️</span>
              <span className="condition-title">Avayogi Planet</span>
            </div>
            <div className="condition-value negative">{specialConditions.yogiAvayogi.avayogi || 'N/A'}</div>
            <div className="condition-effect">May cause obstacles and delays</div>
          </div>
        </div>
      </div>
      
      {/* Combustion Conditions */}
      {specialConditions.combustionConditions.length > 0 && (
        <div className="special-condition-card">
          <h4>🔥 Combust Planets</h4>
          <div className="conditions-list">
            {specialConditions.combustionConditions.map((condition, index) => (
              <div key={index} className="condition-item combust">
                <div className="condition-planet">{condition.planet}</div>
                <div className="condition-details">
                  <div className="condition-status">Combust ({condition.distance}° from Sun)</div>
                  <div className="condition-effect">{condition.effect}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Dagdha Conditions */}
      {specialConditions.dagdhaConditions.length > 0 && (
        <div className="special-condition-card">
          <h4>🔥 Dagdha Conditions</h4>
          <div className="conditions-list">
            {specialConditions.dagdhaConditions.map((condition, index) => {
              const planetData = chartData.planets?.[condition.planet];
              return (
                <div key={index} className="condition-item dagdha">
                  <div className="condition-planet">{condition.planet}</div>
                  <div className="condition-details">
                    <div className="condition-status">Dagdha in {signNames[planetData?.sign]}</div>
                    <div className="condition-effect">{condition.effect}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      {/* Tithi Shunya Conditions */}
      {specialConditions.tithiShunyaConditions.length > 0 && (
        <div className="special-condition-card">
          <h4>🌑 Tithi Shunya Conditions</h4>
          <div className="conditions-list">
            {specialConditions.tithiShunyaConditions.map((condition, index) => (
              <div key={index} className="condition-item tithi-shunya">
                <div className="condition-planet">{condition.planet}</div>
                <div className="condition-details">
                  <div className="condition-status">Tithi Shunya (Born on Tithi {birthDetails?.tithi || 'N/A'})</div>
                  <div className="condition-effect">{condition.effect}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* No Special Conditions */}
      {!specialConditions.hasSpecialConditions && (
        <div className="no-special-conditions">
          <div className="positive-indicator">
            <span className="positive-icon">✅</span>
            <span className="positive-text">No adverse special conditions found</span>
          </div>
          <p>Chart is free from Dagdha, Tithi Shunya, and Combustion afflictions affecting marriage significators.</p>
        </div>
      )}
    </div>
  );
};

export default MarriageAnalysisTab;