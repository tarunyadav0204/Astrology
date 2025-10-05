import React, { useState, useEffect } from 'react';

const YogasTab = ({ chartData, birthData }) => {
  const [yogas, setYogas] = useState([]);
  const [selectedYoga, setSelectedYoga] = useState(null);
  const [loading, setLoading] = useState(true);

  // Common data used across multiple yoga checks (0-indexed signs)
  const exaltationSigns = { 'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6 };
  const debilitationSigns = { 'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 'Jupiter': 9, 'Venus': 5, 'Saturn': 0 };
  const ownSigns = { 'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5], 'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10] };

  useEffect(() => {
    if (chartData && birthData) {
      calculateYogas();
    }
  }, [chartData, birthData]);

  const calculateYogas = () => {
    setLoading(true);
    
    if (!chartData?.planets) {
      setYogas([]);
      setLoading(false);
      return;
    }
    
    const detectedYogas = [];
    const planets = chartData.planets;
    const mainPlanets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

    // Gaja Kesari Yoga - Jupiter in Kendra from Moon
    if (planets.Moon && planets.Jupiter) {
      const moonSign = planets.Moon.sign;
      const jupiterSign = planets.Jupiter.sign;
      const kendraFromMoon = [moonSign, (moonSign + 3) % 12 || 12, (moonSign + 6) % 12 || 12, (moonSign + 9) % 12 || 12];
      
      if (kendraFromMoon.includes(jupiterSign)) {
        detectedYogas.push({
          name: 'Gaja Kesari Yoga',
          type: 'Raja Yoga',
          strength: 'Strong',
          description: 'Jupiter is in Kendra from Moon, creating the auspicious Gaja Kesari Yoga.',
          effects: 'Fame, respect, intelligence, good character, leadership qualities, prosperity, long life.',
          planets: ['Moon', 'Jupiter'],
          houses: [moonSign, jupiterSign]
        });
      }
    }

    // Chandra Mangal Yoga - Moon and Mars together
    if (planets.Moon && planets.Mars && planets.Moon.sign === planets.Mars.sign) {
      detectedYogas.push({
        name: 'Chandra Mangal Yoga',
        type: 'Wealth Yoga',
        strength: 'Medium',
        description: 'Moon and Mars are conjunct in the same sign.',
        effects: 'Business acumen, wealth through real estate, property gains, material prosperity.',
        planets: ['Moon', 'Mars'],
        houses: [planets.Moon.sign]
      });
    }

    // Budh Aditya Yoga - Sun and Mercury together
    if (planets.Sun && planets.Mercury && planets.Sun.sign === planets.Mercury.sign) {
      detectedYogas.push({
        name: 'Budh Aditya Yoga',
        type: 'Intelligence Yoga',
        strength: 'Medium',
        description: 'Sun and Mercury are conjunct in the same sign.',
        effects: 'Intelligence, communication skills, administrative abilities, success in education and career.',
        planets: ['Sun', 'Mercury'],
        houses: [planets.Sun.sign]
      });
    }

    // Guru Mangal Yoga - Jupiter and Mars together
    if (planets.Jupiter && planets.Mars && planets.Jupiter.sign === planets.Mars.sign) {
      detectedYogas.push({
        name: 'Guru Mangal Yoga',
        type: 'Leadership Yoga',
        strength: 'Strong',
        description: 'Jupiter and Mars are conjunct in the same sign.',
        effects: 'Leadership, courage, spiritual wisdom, success in ventures, good fortune.',
        planets: ['Jupiter', 'Mars'],
        houses: [planets.Jupiter.sign]
      });
    }

    // Shukra Guru Yoga - Venus and Jupiter together
    if (planets.Venus && planets.Jupiter && planets.Venus.sign === planets.Jupiter.sign) {
      detectedYogas.push({
        name: 'Shukra Guru Yoga',
        type: 'Prosperity Yoga',
        strength: 'Strong',
        description: 'Venus and Jupiter are conjunct in the same sign.',
        effects: 'Wealth, luxury, artistic talents, spiritual growth, harmonious relationships.',
        planets: ['Venus', 'Jupiter'],
        houses: [planets.Venus.sign]
      });
    }

    // Pancha Mahapurusha Yogas - need ascendant to calculate houses
    if (chartData.ascendant) {
      const mahapurushaYogas = [
        { planet: 'Mars', yoga: 'Ruchaka Yoga', effects: 'Courage, leadership, military success, physical strength, commanding personality.' },
        { planet: 'Mercury', yoga: 'Bhadra Yoga', effects: 'Intelligence, communication skills, business acumen, scholarly achievements, wit.' },
        { planet: 'Jupiter', yoga: 'Hamsa Yoga', effects: 'Wisdom, spirituality, teaching abilities, respect, moral character, prosperity.' },
        { planet: 'Venus', yoga: 'Malavya Yoga', effects: 'Beauty, artistic talents, luxury, comfort, harmonious relationships, creativity.' },
        { planet: 'Saturn', yoga: 'Sasha Yoga', effects: 'Discipline, hard work, organizational skills, authority, longevity, patience.' }
      ];



      mahapurushaYogas.forEach(({ planet, yoga, effects }) => {
        if (planets[planet]) {
          const planetSign = planets[planet].sign;
          
          // Calculate house position from ascendant
          const ascendantSign = chartData.ascendant;
          let housePosition = planetSign - ascendantSign + 1;
          if (housePosition <= 0) housePosition += 12;
          
          const isInKendra = [1, 4, 7, 10].includes(housePosition);
          const isExalted = exaltationSigns[planet] === planetSign;
          const isOwnSign = ownSigns[planet]?.includes(planetSign);
          
          if (isInKendra && (isExalted || isOwnSign)) {
            detectedYogas.push({
              name: yoga,
              type: 'Pancha Mahapurusha Yoga',
              strength: 'Very Strong',
              description: `${planet} is in its ${isExalted ? 'exaltation' : 'own sign'} in ${housePosition}th house (Kendra).`,
              effects: effects,
              planets: [planet],
              houses: [housePosition]
            });
          }
        }
      });
    }

    // Neecha Bhanga Raja Yoga - Debilitated planet with cancellation
    mainPlanets.forEach(planet => {
      if (planets[planet]) {
        const planetSign = planets[planet].sign;
        const isDebilitated = debilitationSigns[planet] === planetSign;
        
        const signNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
        console.log(`${planet} in sign ${planetSign} (${signNames[planetSign]}), debilitation sign: ${debilitationSigns[planet]} (${signNames[debilitationSigns[planet]]}), is debilitated: ${isDebilitated}`);
        
        if (isDebilitated) {
          // Check if debilitation is cancelled by exalted planet in same sign
          const sameSignPlanets = mainPlanets.filter(p => 
            p !== planet && planets[p] && planets[p].sign === planetSign
          );
          
          const hasExaltedPlanet = sameSignPlanets.some(p => 
            exaltationSigns[p] === planets[p].sign
          );
          
          console.log(`${planet} debilitated, same sign planets:`, sameSignPlanets, 'has exalted planet:', hasExaltedPlanet);
          
          if (hasExaltedPlanet) {
            detectedYogas.push({
              name: 'Neecha Bhanga Raja Yoga',
              type: 'Raja Yoga',
              strength: 'Strong',
              description: `${planet} is debilitated but cancellation creates Raja Yoga.`,
              effects: 'Rise from humble beginnings to great heights, unexpected success, overcoming obstacles.',
              planets: [planet],
              houses: [planetSign]
            });
          }
        }
      }
    });

    // Kala Sarpa Dosha - All planets between Rahu and Ketu
    if (planets.Rahu && planets.Ketu) {
      const rahuSign = planets.Rahu.sign;
      const ketuSign = planets.Ketu.sign;
      
      const allPlanetsBetween = mainPlanets.every(planet => {
        if (!planets[planet]) return true;
        const planetSign = planets[planet].sign;
        
        // Check if planet is between Rahu and Ketu
        if (rahuSign < ketuSign) {
          return planetSign > rahuSign && planetSign < ketuSign;
        } else {
          return planetSign > rahuSign || planetSign < ketuSign;
        }
      });
      
      if (allPlanetsBetween) {
        detectedYogas.push({
          name: 'Kala Sarpa Dosha',
          type: 'Dosha',
          strength: 'Negative',
          description: 'All planets are hemmed between Rahu and Ketu.',
          effects: 'Obstacles, delays, struggles in life, but can give spiritual growth and ultimate success.',
          planets: ['Rahu', 'Ketu'],
          houses: [rahuSign, ketuSign],
          remedies: 'Rahu-Ketu remedies, Sarpa Dosha puja, charity, and spiritual practices.'
        });
      }
    }

    // Kemadrum Yoga - Moon isolated
    if (planets.Moon) {
      const moonSign = planets.Moon.sign;
      const prevSign = moonSign === 1 ? 12 : moonSign - 1;
      const nextSign = moonSign === 12 ? 1 : moonSign + 1;
      
      const planetsInMoonSign = mainPlanets.filter(p => 
        p !== 'Moon' && planets[p] && planets[p].sign === moonSign
      );
      
      const planetsInPrevSign = mainPlanets.filter(p => 
        planets[p] && planets[p].sign === prevSign
      );
      
      const planetsInNextSign = mainPlanets.filter(p => 
        planets[p] && planets[p].sign === nextSign
      );
      
      if (planetsInMoonSign.length === 0 && planetsInPrevSign.length === 0 && planetsInNextSign.length === 0) {
        detectedYogas.push({
          name: 'Kemadrum Yoga',
          type: 'Dosha',
          strength: 'Negative',
          description: 'Moon has no planets on either side, creating isolation.',
          effects: 'Mental stress, emotional instability, financial difficulties, lack of support.',
          planets: ['Moon'],
          houses: [moonSign],
          remedies: 'Strengthen Moon through pearl gemstone, Moon mantras, and Monday fasting.'
        });
      }
    }

    setYogas(detectedYogas);
    setLoading(false);
  };

  const getStrengthColor = (strength) => {
    switch (strength) {
      case 'Very Strong': return '#22c55e';
      case 'Strong': return '#3b82f6';
      case 'Medium': return '#f59e0b';
      case 'Negative': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'Raja Yoga': return '#8b5cf6';
      case 'Wealth Yoga': return '#10b981';
      case 'Intelligence Yoga': return '#f59e0b';
      case 'Leadership Yoga': return '#22c55e';
      case 'Prosperity Yoga': return '#3b82f6';
      case 'Pancha Mahapurusha Yoga': return '#f59e0b';
      case 'Dosha': return '#ef4444';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '2rem' }}>Analyzing Yogas...</div>;
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedYoga ? '300px 1fr' : '1fr', gap: '1rem', height: '100%' }}>
      {/* Left side - Yogas List */}
      <div>
        <h3 style={{ color: '#e91e63', marginBottom: '1rem', fontSize: '1.1rem' }}>
          🔮 Detected Yogas ({yogas.length})
        </h3>
        
        <div style={{ 
          maxHeight: '70vh', 
          overflowY: 'auto',
          border: '1px solid #e91e63',
          borderRadius: '8px'
        }}>
          {yogas.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
              No significant yogas detected in this chart.
            </div>
          ) : (
            yogas.map((yoga, index) => (
              <div 
                key={index}
                onClick={() => setSelectedYoga(yoga)}
                style={{ 
                  padding: '0.8rem',
                  cursor: 'pointer',
                  borderBottom: '1px solid #eee',
                  background: selectedYoga === yoga ? '#f0f9ff' : 'white',
                  borderLeft: selectedYoga === yoga ? '4px solid #e91e63' : '4px solid transparent'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center', marginBottom: '0.3rem' }}>
                  <h4 style={{ 
                    margin: 0, 
                    fontSize: '0.9rem', 
                    color: '#1f2937',
                    fontWeight: '600'
                  }}>
                    {yoga.name}
                  </h4>
                  <span style={{ 
                    fontSize: '0.7rem',
                    padding: '0.2rem 0.4rem',
                    borderRadius: '12px',
                    background: getStrengthColor(yoga.strength),
                    color: 'white',
                    fontWeight: '600'
                  }}>
                    {yoga.strength}
                  </span>
                </div>
                
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.3rem' }}>
                  <span style={{ 
                    fontSize: '0.7rem',
                    padding: '0.1rem 0.3rem',
                    borderRadius: '8px',
                    background: getTypeColor(yoga.type),
                    color: 'white'
                  }}>
                    {yoga.type}
                  </span>
                  {yoga.planets && (
                    <span style={{ 
                      fontSize: '0.7rem',
                      color: '#666'
                    }}>
                      {yoga.planets.join(', ')}
                    </span>
                  )}
                </div>
                
                <p style={{ 
                  fontSize: '0.8rem', 
                  color: '#666', 
                  margin: 0,
                  lineHeight: '1.3'
                }}>
                  {yoga.description.length > 80 ? 
                    `${yoga.description.substring(0, 80)}...` : 
                    yoga.description
                  }
                </p>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right side - Detailed Yoga Information */}
      {selectedYoga && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ color: '#e91e63', fontSize: '1.2rem', margin: 0 }}>
              🔮 {selectedYoga.name}
            </h3>
            <button 
              onClick={() => setSelectedYoga(null)}
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
            maxHeight: '65vh', 
            overflowY: 'auto',
            border: '1px solid #e91e63',
            borderRadius: '8px',
            padding: '1rem',
            background: 'white'
          }}>
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <strong>Type:</strong> 
                  <span style={{ 
                    marginLeft: '0.5rem',
                    padding: '0.2rem 0.4rem',
                    borderRadius: '8px',
                    background: getTypeColor(selectedYoga.type),
                    color: 'white',
                    fontSize: '0.8rem'
                  }}>
                    {selectedYoga.type}
                  </span>
                </div>
                <div>
                  <strong>Strength:</strong> 
                  <span style={{ 
                    marginLeft: '0.5rem',
                    padding: '0.2rem 0.4rem',
                    borderRadius: '8px',
                    background: getStrengthColor(selectedYoga.strength),
                    color: 'white',
                    fontSize: '0.8rem'
                  }}>
                    {selectedYoga.strength}
                  </span>
                </div>
                {selectedYoga.planets && (
                  <div><strong>Planets:</strong> {selectedYoga.planets.join(', ')}</div>
                )}
                {selectedYoga.houses && (
                  <div><strong>Signs:</strong> {selectedYoga.houses.join(', ')}</div>
                )}
              </div>
            </div>
            
            <div style={{ marginBottom: '1rem' }}>
              <h4 style={{ color: '#ff6f00', fontSize: '1rem', marginBottom: '0.5rem' }}>📖 Description</h4>
              <p style={{ fontSize: '0.9rem', lineHeight: '1.5', color: '#333', textAlign: 'justify' }}>
                {selectedYoga.description}
              </p>
            </div>
            
            <div style={{ marginBottom: '1rem' }}>
              <h4 style={{ color: '#22c55e', fontSize: '1rem', marginBottom: '0.5rem' }}>✨ Effects</h4>
              <p style={{ fontSize: '0.9rem', lineHeight: '1.5', color: '#333', textAlign: 'justify' }}>
                {selectedYoga.effects}
              </p>
            </div>
            
            {selectedYoga.remedies && (
              <div>
                <h4 style={{ color: '#ef4444', fontSize: '1rem', marginBottom: '0.5rem' }}>💎 Remedies</h4>
                <p style={{ fontSize: '0.9rem', lineHeight: '1.5', color: '#333', textAlign: 'justify' }}>
                  {selectedYoga.remedies}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {!selectedYoga && (
        <div style={{ 
          padding: '2rem',
          textAlign: 'center',
          border: '2px dashed #e91e63',
          borderRadius: '8px',
          color: '#666'
        }}>
          <h3 style={{ color: '#e91e63', marginBottom: '1rem' }}>
            🔮 Select a Yoga for detailed analysis
          </h3>
          <p>Click on any yoga from the list to view its complete description, effects, and significance in your birth chart.</p>
        </div>
      )}
    </div>
  );
};

export default YogasTab;