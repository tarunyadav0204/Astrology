import React, { useState, useEffect } from 'react';

const HouseAnalysisTab = ({ chartData, birthData }) => {
  const [houseData, setHouseData] = useState([]);
  const [selectedHouse, setSelectedHouse] = useState(null);
  const [loading, setLoading] = useState(true);

  const houseSignifications = {
    1: { name: 'Ascendant/Self', significations: 'Personality, appearance, health, vitality, general life path' },
    2: { name: 'Wealth/Family', significations: 'Money, family, speech, food, values, accumulated wealth' },
    3: { name: 'Courage/Siblings', significations: 'Siblings, courage, communication, short travels, skills' },
    4: { name: 'Home/Mother', significations: 'Mother, home, property, education, emotional security, vehicles' },
    5: { name: 'Children/Creativity', significations: 'Children, creativity, intelligence, romance, speculation, mantras' },
    6: { name: 'Health/Enemies', significations: 'Health, enemies, debts, service, daily routine, obstacles' },
    7: { name: 'Partnership/Marriage', significations: 'Marriage, business partnerships, public relations, spouse' },
    8: { name: 'Transformation/Longevity', significations: 'Longevity, transformation, occult, inheritance, sudden events' },
    9: { name: 'Fortune/Dharma', significations: 'Fortune, dharma, higher learning, guru, long travels, father' },
    10: { name: 'Career/Status', significations: 'Career, reputation, status, authority, government, public image' },
    11: { name: 'Gains/Friends', significations: 'Gains, friends, elder siblings, hopes, aspirations, income' },
    12: { name: 'Loss/Liberation', significations: 'Expenses, losses, foreign lands, spirituality, moksha, isolation' }
  };

  useEffect(() => {
    if (chartData && birthData) {
      analyzeHouses();
    }
  }, [chartData, birthData]);

  const analyzeHouses = () => {
    setLoading(true);
    
    if (!chartData?.planets || !chartData?.ascendant) {
      setHouseData([]);
      setLoading(false);
      return;
    }

    const houses = [];
    const planets = chartData.planets;
    const ascendantDegree = chartData.ascendant;
    const ascendant = Math.floor(ascendantDegree / 30); // Convert degree to sign (0-11)
    
    console.log('Ascendant degree:', ascendantDegree, 'Ascendant sign:', ascendant);

    for (let house = 1; house <= 12; house++) {
      const occupants = [];
      const houseSign = (ascendant + house - 1) % 12;
      
      // Find planets in this house
      Object.entries(planets).forEach(([planet, data]) => {
        // Calculate house position from planet's sign and ascendant
        let planetHouse = data.sign - ascendant + 1;
        if (planetHouse <= 0) planetHouse += 12;
        
        if (planetHouse === house) {
          occupants.push({
            name: planet,
            sign: data.sign,
            degree: data.degree,
            isExalted: isExalted(planet, data.sign),
            isDebilitated: isDebilitated(planet, data.sign),
            isOwnSign: isOwnSign(planet, data.sign)
          });
        }
      });

      const strengthData = calculateHouseStrength(house, occupants, planets);
      
      houses.push({
        number: house,
        ...houseSignifications[house],
        sign: houseSign,
        signName: getSignName(houseSign),
        occupants,
        strength: strengthData.strength,
        strengthReasons: strengthData.reasons,
        strengthScore: strengthData.score,
        isEmpty: occupants.length === 0
      });
    }

    setHouseData(houses);
    setLoading(false);
  };

  const isExalted = (planet, sign) => {
    const exaltationSigns = { 'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6 };
    return exaltationSigns[planet] === sign;
  };

  const isDebilitated = (planet, sign) => {
    const debilitationSigns = { 'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 'Jupiter': 9, 'Venus': 5, 'Saturn': 0 };
    return debilitationSigns[planet] === sign;
  };

  const isOwnSign = (planet, sign) => {
    const ownSigns = { 'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5], 'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10] };
    return ownSigns[planet]?.includes(sign);
  };

  const getSignName = (sign) => {
    const signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
    return signs[sign];
  };

  const getOrdinal = (num) => {
    const suffixes = ['th', 'st', 'nd', 'rd'];
    const v = num % 100;
    return num + (suffixes[(v - 20) % 10] || suffixes[v] || suffixes[0]);
  };

  const getFunctionalNature = (planetName, ascendantSign) => {
    const lordships = {
      'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5], 
      'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
    };
    
    const planetSigns = lordships[planetName] || [];
    const housesRuled = planetSigns.map(sign => {
      let house = sign - ascendantSign + 1;
      if (house <= 0) house += 12;
      return house;
    });
    
    const beneficHouses = [1, 4, 5, 7, 9, 10, 11];
    const maleficHouses = [3, 6, 8, 12];
    
    const isBeneficLord = housesRuled.some(h => beneficHouses.includes(h));
    const isMaleficLord = housesRuled.some(h => maleficHouses.includes(h));
    
    // For mixed lordships, prioritize the stronger house
    if (housesRuled.includes(1)) return 'benefic'; // Lagna lord always benefic
    if (housesRuled.includes(6) || housesRuled.includes(8) || housesRuled.includes(12)) return 'malefic'; // Dusthana lords
    if (isBeneficLord && !isMaleficLord) return 'benefic';
    if (isMaleficLord && !isBeneficLord) return 'malefic';
    return 'neutral';
  };

  const calculateHouseStrength = (house, occupants, planets) => {
    let score = 0;
    const reasons = [];
    const ascendantSign = Math.floor(chartData.ascendant / 30);
    
    // Points for occupant planets
    occupants.forEach(planet => {
      const functionalNature = getFunctionalNature(planet.name, ascendantSign);
      
      // Get houses ruled by this planet for debugging
      const lordships = {
        'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5], 
        'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
      };
      const planetSigns = lordships[planet.name] || [];
      const housesRuled = planetSigns.map(sign => {
        let house = sign - ascendantSign + 1;
        if (house <= 0) house += 12;
        return house;
      });
      
      if (functionalNature === 'benefic') {
        score += 2;
        reasons.push(`${planet.name} rules houses ${housesRuled.join(',')} (functional benefic) (+2)`);
      } else if (functionalNature === 'malefic') {
        score -= 1;
        reasons.push(`${planet.name} rules houses ${housesRuled.join(',')} (functional malefic) (-1)`);
      } else {
        // Rahu/Ketu always malefic
        if (['Rahu', 'Ketu'].includes(planet.name)) {
          score -= 1;
          reasons.push(`${planet.name} (shadow planet) occupies house (-1)`);
        }
      }
      if (planet.isExalted) {
        score += 3;
        reasons.push(`${planet.name} is exalted (+3)`);
      }
      if (planet.isOwnSign) {
        score += 2;
        reasons.push(`${planet.name} in own sign (+2)`);
      }
      if (planet.isDebilitated) {
        score -= 3;
        reasons.push(`${planet.name} is debilitated (-3)`);
      }
    });
    
    // Points for aspects received
    const aspects = getAspectsToHouse(house);
    aspects.forEach(aspect => {
      const functionalNature = getFunctionalNature(aspect.planet, ascendantSign);
      
      if (functionalNature === 'benefic') {
        score += 1;
        reasons.push(`${aspect.planet} (functional benefic) aspects house (+1)`);
      } else if (functionalNature === 'malefic') {
        score -= 0.5;
        reasons.push(`${aspect.planet} (functional malefic) aspects house (-0.5)`);
      } else if (['Rahu', 'Ketu'].includes(aspect.planet)) {
        score -= 0.5;
        reasons.push(`${aspect.planet} (shadow planet) aspects house (-0.5)`);
      }
    });

    // Kendra houses (1,4,7,10) get bonus
    if ([1, 4, 7, 10].includes(house)) {
      score += 1;
      reasons.push('Kendra house (angular) (+1)');
    }
    
    // Trikona houses (1,5,9) get bonus
    if ([1, 5, 9].includes(house)) {
      score += 1;
      reasons.push('Trikona house (trinal) (+1)');
    }
    
    // Dusthana houses (6,8,12) get penalty
    if ([6, 8, 12].includes(house)) {
      score -= 1;
      reasons.push('Dusthana house (malefic) (-1)');
    }

    const strength = score >= 3 ? 'Strong' : score >= 0 ? 'Medium' : 'Weak';
    return { strength, reasons, score };
  };

  const getStrengthColor = (strength) => {
    switch (strength) {
      case 'Strong': return '#22c55e';
      case 'Medium': return '#f59e0b';
      case 'Weak': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getPlanetStatus = (planet) => {
    if (planet.isExalted) return { text: '↑', color: '#22c55e', title: 'Exalted' };
    if (planet.isDebilitated) return { text: '↓', color: '#ef4444', title: 'Debilitated' };
    if (planet.isOwnSign) return { text: '●', color: '#3b82f6', title: 'Own Sign' };
    return null;
  };

  const getAspectsToHouse = (houseNumber) => {
    if (!chartData?.planets) return [];
    
    const aspects = [];
    const planets = chartData.planets;
    const ascendantDegree = chartData.ascendant;
    const ascendant = Math.floor(ascendantDegree / 30);
    
    Object.entries(planets).forEach(([planetName, data]) => {
      // Calculate planet's house
      let planetHouse = data.sign - ascendant + 1;
      if (planetHouse <= 0) planetHouse += 12;
      
      // 7th house aspect (all planets except Rahu/Ketu aspect 7th house from them)
      if (!['Rahu', 'Ketu'].includes(planetName)) {
        let aspectHouse = planetHouse + 6;
        if (aspectHouse > 12) aspectHouse -= 12;
        
        if (aspectHouse === houseNumber) {
          aspects.push({ planet: planetName, type: '7th' });
        }
      }
      
      // Rahu and Ketu special aspects (3rd and 11th houses)
      if (['Rahu', 'Ketu'].includes(planetName)) {
        let aspect3rd = planetHouse + 2;
        let aspect11th = planetHouse + 10;
        if (aspect3rd > 12) aspect3rd -= 12;
        if (aspect11th > 12) aspect11th -= 12;
        
        if (aspect3rd === houseNumber) aspects.push({ planet: planetName, type: '3rd' });
        if (aspect11th === houseNumber) aspects.push({ planet: planetName, type: '11th' });
      }
      
      // Special aspects for Mars, Jupiter, Saturn
      if (planetName === 'Mars') {
        // Mars aspects 4th and 8th houses
        let mars4th = planetHouse + 3;
        let mars8th = planetHouse + 7;
        if (mars4th > 12) mars4th -= 12;
        if (mars8th > 12) mars8th -= 12;
        
        if (mars4th === houseNumber) aspects.push({ planet: planetName, type: '4th' });
        if (mars8th === houseNumber) aspects.push({ planet: planetName, type: '8th' });
      }
      
      if (planetName === 'Jupiter') {
        // Jupiter aspects 5th and 9th houses
        let jupiter5th = planetHouse + 4;
        let jupiter9th = planetHouse + 8;
        if (jupiter5th > 12) jupiter5th -= 12;
        if (jupiter9th > 12) jupiter9th -= 12;
        
        if (jupiter5th === houseNumber) aspects.push({ planet: planetName, type: '5th' });
        if (jupiter9th === houseNumber) aspects.push({ planet: planetName, type: '9th' });
      }
      
      if (planetName === 'Saturn') {
        // Saturn aspects 3rd and 10th houses
        let saturn3rd = planetHouse + 2;
        let saturn10th = planetHouse + 9;
        if (saturn3rd > 12) saturn3rd -= 12;
        if (saturn10th > 12) saturn10th -= 12;
        
        if (saturn3rd === houseNumber) aspects.push({ planet: planetName, type: '3rd' });
        if (saturn10th === houseNumber) aspects.push({ planet: planetName, type: '10th' });
      }
    });
    
    return aspects;
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '2rem' }}>Analyzing Houses...</div>;
  }

  return (
    <div style={{ 
      display: 'grid', 
      gridTemplateColumns: window.innerWidth <= 768 
        ? '1fr' 
        : selectedHouse ? '1fr 400px' : '1fr', 
      gap: '1rem', 
      height: '100%' 
    }}>
      {/* Main Grid - Houses Overview */}
      {(!selectedHouse || window.innerWidth > 768) && (
      <div>
        <h3 style={{ color: '#e91e63', marginBottom: '1rem', fontSize: '1.1rem' }}>
          🏠 House Analysis Overview
        </h3>
        
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: window.innerWidth <= 768 
            ? '1fr' 
            : 'repeat(auto-fit, minmax(300px, 1fr))', 
          gap: '1rem',
          maxHeight: window.innerWidth <= 768 ? '75vh' : '70vh',
          overflowY: 'auto',
          WebkitOverflowScrolling: 'touch'
        }}>
          {houseData.map(house => (
            <div 
              key={house.number}
              onClick={() => setSelectedHouse(house)}
              style={{ 
                border: '1px solid #e91e63',
                borderRadius: '8px',
                padding: window.innerWidth <= 768 ? '0.75rem' : '1rem',
                cursor: 'pointer',
                background: selectedHouse?.number === house.number ? '#f0f9ff' : 'white',
                borderLeft: selectedHouse?.number === house.number ? '4px solid #e91e63' : '1px solid #e91e63'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h4 style={{ margin: 0, color: '#1f2937', fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem' }}>
                  {getOrdinal(house.number)} House - {house.name}
                </h4>
                <span style={{ 
                  fontSize: '0.7rem',
                  padding: '0.2rem 0.4rem',
                  borderRadius: '12px',
                  background: getStrengthColor(house.strength),
                  color: 'white',
                  fontWeight: '600'
                }}>
                  {house.strength}
                </span>
              </div>
              
              <div style={{ fontSize: window.innerWidth <= 768 ? '0.65rem' : '0.7rem', color: '#666', marginBottom: '0.5rem' }}>
                Sign: {house.signName}
              </div>
              
              <div style={{ marginBottom: '0.5rem' }}>
                {house.isEmpty ? (
                  <span style={{ fontSize: '0.8rem', color: '#999', fontStyle: 'italic' }}>Empty House</span>
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                    {house.occupants.map((planet, idx) => {
                      const status = getPlanetStatus(planet);
                      return (
                        <span key={idx} style={{ 
                          fontSize: window.innerWidth <= 768 ? '0.65rem' : '0.7rem',
                          padding: window.innerWidth <= 768 ? '0.1rem 0.25rem' : '0.1rem 0.3rem',
                          background: '#e91e63',
                          color: 'white',
                          borderRadius: '4px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.2rem'
                        }}>
                          {planet.name}
                          {status && (
                            <span style={{ color: status.color }} title={status.title}>
                              {status.text}
                            </span>
                          )}
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>
              
              <p style={{ 
                fontSize: window.innerWidth <= 768 ? '0.65rem' : '0.7rem', 
                color: '#666', 
                margin: 0,
                lineHeight: '1.3'
              }}>
                {house.significations.length > 60 ? 
                  `${house.significations.substring(0, 60)}...` : 
                  house.significations
                }
              </p>
            </div>
          ))}
        </div>
      </div>
      )}

      {/* Right Panel - Detailed House Analysis */}
      {selectedHouse && (
        <div style={{ 
          gridColumn: window.innerWidth <= 768 ? '1' : 'auto'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ color: '#e91e63', fontSize: '1.1rem', margin: 0 }}>
              🏠 {getOrdinal(selectedHouse.number)} House Details
            </h3>
            <button 
              onClick={() => setSelectedHouse(null)}
              style={{
                marginLeft: '1rem',
                padding: '0.3rem 0.6rem',
                background: '#e91e63',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.7rem'
              }}
            >
              ← Back
            </button>
          </div>
          
          <div style={{ 
            maxHeight: window.innerWidth <= 768 ? '70vh' : '65vh', 
            overflowY: 'auto',
            border: '1px solid #e91e63',
            borderRadius: '8px',
            padding: window.innerWidth <= 768 ? '0.75rem' : '1rem',
            background: 'white',
            WebkitOverflowScrolling: 'touch'
          }}>
            <div style={{ marginBottom: '1rem' }}>
              <h4 style={{ color: '#e91e63', fontSize: '1rem', marginBottom: '0.5rem' }}>
                {selectedHouse.name}
              </h4>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: window.innerWidth <= 768 ? '1fr' : '1fr 1fr', 
                gap: window.innerWidth <= 768 ? '0.3rem' : '0.5rem', 
                marginBottom: '1rem' 
              }}>
                <div><strong>House:</strong> {getOrdinal(selectedHouse.number)}</div>
                <div><strong>Sign:</strong> {selectedHouse.signName}</div>
                <div><strong>Strength:</strong> 
                  <span style={{ 
                    marginLeft: '0.5rem',
                    padding: '0.1rem 0.3rem',
                    borderRadius: '4px',
                    background: getStrengthColor(selectedHouse.strength),
                    color: 'white',
                    fontSize: '0.7rem'
                  }}>
                    {selectedHouse.strength}
                  </span>
                </div>
                <div><strong>Occupants:</strong> {selectedHouse.occupants.length || 'None'}</div>
              </div>
            </div>
            
            <div style={{ marginBottom: '1rem' }}>
              <h4 style={{ color: '#3b82f6', fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', marginBottom: '0.5rem' }}>📖 Significations</h4>
              <p style={{ fontSize: window.innerWidth <= 768 ? '0.75rem' : '0.8rem', lineHeight: '1.4', color: '#333' }}>
                {selectedHouse.significations}
              </p>
            </div>
            
            {selectedHouse.occupants.length > 0 && (
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#22c55e', fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', marginBottom: '0.5rem' }}>🪐 Planetary Occupants</h4>
                {selectedHouse.occupants.map((planet, idx) => {
                  const status = getPlanetStatus(planet);
                  return (
                    <div key={idx} style={{ 
                      padding: window.innerWidth <= 768 ? '0.4rem' : '0.5rem',
                      border: '1px solid #eee',
                      borderRadius: '4px',
                      marginBottom: '0.5rem'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong style={{ color: '#1f2937' }}>{planet.name}</strong>
                        {status && (
                          <span style={{ 
                            color: status.color,
                            fontSize: '0.8rem',
                            fontWeight: '600'
                          }} title={status.title}>
                            {status.title}
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: window.innerWidth <= 768 ? '0.65rem' : '0.7rem', color: '#666' }}>
                        Degree: {planet.degree?.toFixed(2)}° in {getSignName(planet.sign)}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            
            {selectedHouse.isEmpty && (
              <div style={{ 
                padding: '1rem',
                background: '#f8f9fa',
                borderRadius: '4px',
                textAlign: 'center'
              }}>
                <h4 style={{ color: '#666', fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', marginBottom: '0.5rem' }}>Empty House</h4>
                <p style={{ fontSize: window.innerWidth <= 768 ? '0.75rem' : '0.8rem', color: '#666', margin: 0 }}>
                  This house has no planetary occupants. Its results depend on the house lord's placement and aspects received.
                </p>
              </div>
            )}
            
            <div style={{ marginTop: '1rem' }}>
              <h4 style={{ color: '#f59e0b', fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', marginBottom: '0.5rem' }}>👁️ Aspects Received</h4>
              <div style={{ fontSize: window.innerWidth <= 768 ? '0.75rem' : '0.8rem', color: '#666' }}>
                {getAspectsToHouse(selectedHouse.number).length === 0 ? (
                  <p>No major aspects to this house.</p>
                ) : (
                  getAspectsToHouse(selectedHouse.number).map((aspect, idx) => (
                    <div key={idx} style={{ 
                      padding: '0.3rem',
                      marginBottom: '0.3rem',
                      background: '#fff',
                      border: '1px solid #eee',
                      borderRadius: '4px'
                    }}>
                      <strong>{aspect.planet}</strong> aspects this house ({aspect.type} aspect)
                    </div>
                  ))
                )}
              </div>
            </div>
            
            <div style={{ marginTop: '1rem' }}>
              <h4 style={{ color: '#8b5cf6', fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', marginBottom: '0.5rem' }}>⚖️ Strength Analysis</h4>
              <div style={{ 
                padding: '0.5rem',
                background: '#f8f9fa',
                borderRadius: '4px',
                marginBottom: '0.5rem'
              }}>
                <div style={{ fontSize: window.innerWidth <= 768 ? '0.75rem' : '0.8rem', fontWeight: '600', marginBottom: '0.3rem' }}>
                  Score: {selectedHouse.strengthScore?.toFixed(1)} → {selectedHouse.strength}
                </div>
                {selectedHouse.strengthReasons?.map((reason, idx) => (
                  <div key={idx} style={{ 
                    fontSize: window.innerWidth <= 768 ? '0.65rem' : '0.7rem',
                    color: '#666',
                    marginBottom: '0.2rem'
                  }}>
                    • {reason}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {!selectedHouse && window.innerWidth > 768 && (
        <div style={{ 
          padding: '2rem',
          textAlign: 'center',
          border: '2px dashed #e91e63',
          borderRadius: '8px',
          color: '#666'
        }}>
          <h3 style={{ color: '#e91e63', marginBottom: '1rem' }}>
            🏠 Select a house for detailed analysis
          </h3>
          <p>Click on any house from the grid to view detailed information about its significations, occupants, and strength.</p>
        </div>
      )}
    </div>
  );
};

export default HouseAnalysisTab;