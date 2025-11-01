import React, { useState, useEffect } from 'react';
import './CompleteHealthAnalysisTab.css';

const CompleteHealthAnalysisTab = ({ chartData, birthDetails }) => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedSections, setExpandedSections] = useState({});
  const [modalData, setModalData] = useState(null);

  useEffect(() => {
    const loadHealthAnalysis = async () => {
      if (!birthDetails) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch('/api/health/overall-assessment', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            birth_date: birthDetails.date || '1990-01-01',
            birth_time: birthDetails.time || '12:00',
            birth_place: birthDetails.place || 'New Delhi',
            latitude: birthDetails.latitude || 28.6139,
            longitude: birthDetails.longitude || 77.2090,
            timezone: birthDetails.timezone || 'UTC+5:30'
          })
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        setHealthData(result.data);
      } catch (error) {
        console.error('Error loading health analysis:', error);
        setError(error.message || 'Failed to load health analysis');
      } finally {
        setLoading(false);
      }
    };

    loadHealthAnalysis();
  }, [birthDetails]);

  const toggleSection = (sectionId) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  const openModal = (title, content) => {
    setModalData({ title, content });
  };

  const closeModal = () => {
    setModalData(null);
  };

  if (loading) {
    return (
      <div className="complete-health-analysis">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Analyzing health prospects...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="complete-health-analysis">
        <div className="error-state">
          <h3>⚠️ Analysis Error</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry Analysis</button>
        </div>
      </div>
    );
  }

  if (!healthData) {
    return (
      <div className="complete-health-analysis">
        <div className="no-data-state">
          <p>No health analysis available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="complete-health-analysis">
      <div className="analysis-header">
        <h3>🏥 Complete Health Analysis</h3>
        <p>Comprehensive Vedic health analysis with detailed calculations</p>
      </div>

      <div className="analysis-sections">
        {/* Health Score & Constitution */}
        <div className="analysis-section">
          <div className="card-header" onClick={() => toggleSection('health-score')}>
            <div className="card-icon" style={{ backgroundColor: '#4CAF50' }}>
              🎯
            </div>
            <div className="card-info">
              <h4>Ayurvedic Constitution Analysis</h4>
              <p>Detailed constitutional analysis</p>
            </div>
            <div className="card-status">
              <span className={`expand-icon ${expandedSections['health-score'] ? 'expanded' : ''}`}>▼</span>
            </div>
          </div>
          
          {expandedSections['health-score'] && (
            <div className="card-content">
              <div className="health-score-summary">

                
                <div className="constitution-info">
                  {healthData.element_balance && (() => {
                    const elements = healthData.element_balance;
                    const dominantElement = Object.entries(elements).reduce((a, b) => elements[a[0]] > elements[b[0]] ? a : b)[0];
                    const secondaryElement = Object.entries(elements).filter(([el]) => el !== dominantElement).reduce((a, b) => elements[a[0]] > elements[b[0]] ? a : b)[0];
                    
                    const getConstitutionAnalysis = () => {
                      const fireContributors = Object.entries(healthData.planet_analysis || {})
                        .filter(([planet, analysis]) => analysis.element === 'Fire' && analysis.basic_analysis?.strength_analysis?.shadbala_rupas > 3)
                        .map(([planet, analysis]) => ({ planet, dignity: analysis.basic_analysis?.dignity_analysis?.dignity, house: analysis.basic_analysis?.basic_info?.house }));
                      
                      const waterContributors = Object.entries(healthData.planet_analysis || {})
                        .filter(([planet, analysis]) => analysis.element === 'Water' && analysis.basic_analysis?.strength_analysis?.shadbala_rupas > 3)
                        .map(([planet, analysis]) => ({ planet, dignity: analysis.basic_analysis?.dignity_analysis?.dignity, house: analysis.basic_analysis?.basic_info?.house }));
                      
                      const airContributors = Object.entries(healthData.planet_analysis || {})
                        .filter(([planet, analysis]) => analysis.element === 'Air' && analysis.basic_analysis?.strength_analysis?.shadbala_rupas > 3)
                        .map(([planet, analysis]) => ({ planet, dignity: analysis.basic_analysis?.dignity_analysis?.dignity, house: analysis.basic_analysis?.basic_info?.house }));
                      
                      if (elements.Fire > 40) {
                        return {
                          primary: 'Pitta (Fire Dominant)',
                          description: `Strong fire element (${elements.Fire}%) creates a Pitta constitution with excellent digestive power and sharp intellect`,
                          astrologyReason: fireContributors.length > 0 ? 
                            `${fireContributors.map(c => `${c.planet} (${c.dignity} in ${c.house}th house)`).join(', ')} strengthen your fire element, giving you natural leadership and strong metabolism` :
                            `Sun and Mars create natural Pitta tendencies through their fire element influence`,
                          characteristics: ['Excellent digestion and metabolism', 'Sharp, analytical mind', 'Natural leadership qualities', 'Strong willpower and determination'],
                          healthImplications: ['Prone to acidity, heartburn, and inflammatory conditions', 'May experience anger-related health issues', 'Excellent healing capacity when balanced', 'Watch for liver and blood-related problems'],
                          recommendations: ['Favor cooling foods: cucumber, coconut water, sweet fruits', 'Avoid spicy, oily, and fermented foods', 'Practice cooling pranayama and meditation', 'Exercise during cooler parts of the day']
                        };
                      } else if (elements.Water > 40) {
                        return {
                          primary: 'Kapha (Water Dominant)',
                          description: `Strong water element (${elements.Water}%) creates a Kapha constitution with excellent immunity and emotional stability`,
                          astrologyReason: waterContributors.length > 0 ? 
                            `${waterContributors.map(c => `${c.planet} (${c.dignity} in ${c.house}th house)`).join(', ')} enhance your water element, providing emotional depth and strong immunity` :
                            `Moon and Venus create natural Kapha qualities through their water element influence`,
                          characteristics: ['Excellent immunity and endurance', 'Calm, stable, and nurturing nature', 'Good long-term memory', 'Natural healing and recovery ability'],
                          healthImplications: ['Tendency toward weight gain and sluggish metabolism', 'Prone to respiratory congestion and allergies', 'May experience depression in cold, damp weather', 'Excellent recovery from illness when motivated'],
                          recommendations: ['Favor warm, light, spicy foods: ginger, black pepper, turmeric', 'Avoid cold, heavy, oily foods and dairy', 'Regular vigorous exercise is essential', 'Wake up early and stay active throughout the day']
                        };
                      } else if (elements.Air > 40) {
                        return {
                          primary: 'Vata (Air Dominant)',
                          description: `Strong air element (${elements.Air}%) creates a Vata constitution with high mental activity and creative energy`,
                          astrologyReason: airContributors.length > 0 ? 
                            `${airContributors.map(c => `${c.planet} (${c.dignity} in ${c.house}th house)`).join(', ')} amplify your air element, giving you mental agility and creative thinking` :
                            `Mercury, Jupiter, and Rahu create natural Vata characteristics through their air element influence`,
                          characteristics: ['Quick thinking and high creativity', 'Enthusiastic and energetic when balanced', 'Excellent communication skills', 'Adaptable and flexible nature'],
                          healthImplications: ['Prone to anxiety, insomnia, and nervous disorders', 'Digestive irregularity and gas formation', 'Joint pain and muscle tension', 'Variable energy levels and immunity'],
                          recommendations: ['Favor warm, nourishing, grounding foods: ghee, nuts, cooked grains', 'Maintain regular meal and sleep schedules', 'Practice grounding activities: yoga, meditation, massage', 'Avoid cold, dry, and processed foods']
                        };
                      } else {
                        const primaryDosha = dominantElement === 'Fire' ? 'Pitta' : dominantElement === 'Water' ? 'Kapha' : dominantElement === 'Air' ? 'Vata' : 'Earth';
                        const secondaryDosha = secondaryElement === 'Fire' ? 'Pitta' : secondaryElement === 'Water' ? 'Kapha' : secondaryElement === 'Air' ? 'Vata' : 'Earth';
                        
                        return {
                          primary: `${primaryDosha}-${secondaryDosha} Constitution`,
                          description: `Balanced constitution with ${dominantElement.toLowerCase()} (${elements[dominantElement]}%) and ${secondaryElement.toLowerCase()} (${elements[secondaryElement]}%) creating a mixed constitutional type`,
                          astrologyReason: (() => {
                            const strongPlanets = Object.entries(healthData.planet_analysis || {})
                              .filter(([planet, analysis]) => analysis.basic_analysis?.strength_analysis?.shadbala_rupas > 4)
                              .map(([planet, analysis]) => ({
                                planet,
                                element: analysis.element,
                                dignity: analysis.basic_analysis?.dignity_analysis?.dignity,
                                house: analysis.basic_analysis?.basic_info?.house,
                                strength: analysis.basic_analysis?.strength_analysis?.shadbala_rupas
                              }));
                            
                            const weakPlanets = Object.entries(healthData.planet_analysis || {})
                              .filter(([planet, analysis]) => analysis.basic_analysis?.strength_analysis?.shadbala_rupas < 3)
                              .map(([planet, analysis]) => ({
                                planet,
                                element: analysis.element,
                                dignity: analysis.basic_analysis?.dignity_analysis?.dignity,
                                house: analysis.basic_analysis?.basic_info?.house
                              }));
                            
                            let reasoning = [];
                            
                            if (strongPlanets.length > 0) {
                              const strongByElement = strongPlanets.reduce((acc, p) => {
                                if (!acc[p.element]) acc[p.element] = [];
                                acc[p.element].push(`${p.planet} (${p.dignity} in ${p.house}th, ${p.strength?.toFixed(1)} rupas)`);
                                return acc;
                              }, {});
                              
                              Object.entries(strongByElement).forEach(([element, planets]) => {
                                reasoning.push(`Strong ${element.toLowerCase()} element from ${planets.join(', ')}`);
                              });
                            }
                            
                            if (weakPlanets.length > 0) {
                              const weakByElement = weakPlanets.reduce((acc, p) => {
                                if (!acc[p.element]) acc[p.element] = [];
                                acc[p.element].push(`${p.planet} (${p.dignity} in ${p.house}th)`);
                                return acc;
                              }, {});
                              
                              Object.entries(weakByElement).forEach(([element, planets]) => {
                                reasoning.push(`Weak ${element.toLowerCase()} element from ${planets.join(', ')}`);
                              });
                            }
                            
                            return reasoning.length > 0 ? reasoning.join('. ') + '.' : 'Balanced planetary distribution creates mixed constitutional type.';
                          })(),
                          characteristics: [
                            `Primary ${dominantElement.toLowerCase()} qualities with secondary ${secondaryElement.toLowerCase()} influence`,
                            'Adaptable constitution that changes with seasons',
                            'Balanced energy patterns when lifestyle is regulated',
                            'May show characteristics of both constitutional types'
                          ],
                          healthImplications: [
                            'Health varies with seasonal changes and lifestyle',
                            `May experience ${dominantElement.toLowerCase()}-related issues during stress`,
                            'Generally good adaptability and recovery',
                            'Requires personalized approach to diet and lifestyle'
                          ],
                          recommendations: [
                            'Adjust diet and lifestyle according to seasons',
                            `Follow ${dominantElement.toLowerCase()}-pacifying diet during ${dominantElement.toLowerCase()} season`,
                            'Maintain consistent daily routine',
                            'Monitor your body\'s response to different foods and activities'
                          ]
                        };
                      }
                    };
                    
                    const constitution = getConstitutionAnalysis();
                    
                    return (
                      <div className="detailed-constitution">
                        
                        <div className="ayurvedic-constitution">
                          <div className="constitution-header">
                            <h4>🧬 Your Constitution</h4>
                            <div className="constitution-type">
                              <h3>{constitution.primary}</h3>
                              <p className="constitution-blend">{constitution.description}</p>
                            </div>
                          </div>
                          
                          <div className="element-display">
                            {Object.entries(elements).map(([element, percentage]) => {
                              const symbols = { Fire: '🜂', Water: '🜄', Air: '🜁', Earth: '🜃' };
                              const doshas = { Fire: 'Pitta', Water: 'Kapha', Air: 'Vata', Earth: '' };
                              return (
                                <span key={element} className="element-badge">
                                  {symbols[element]} {element} ({doshas[element]}): {percentage}%
                                </span>
                              );
                            })}
                          </div>
                          
                          <div className="astrological-details">
                            <details className="collapsible-section">
                              <summary>🔭 Show Astrological Details</summary>
                              <div className="details-content">
                                <p>Each planet in your birth chart represents one of the classical elements (Pancha Mahabhutas).</p>
                                <p>The elemental strength is calculated using:</p>
                                <ul>
                                  <li>Planetary nature (e.g. Sun = Fire, Moon = Water)</li>
                                  <li>Shadbala (planetary strength in rupas)</li>
                                  <li>House placement (favorable / neutral / unfavorable)</li>
                                </ul>
                                
                                <table className="element-table">
                                  <thead>
                                    <tr>
                                      <th>Element</th>
                                      <th>Major Planets in Your Chart</th>
                                      <th>Influence</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    <tr>
                                      <td>🔥 Fire (Pitta)</td>
                                      <td>Sun, Mars, Ketu</td>
                                      <td>Purpose, digestion, determination</td>
                                    </tr>
                                    <tr>
                                      <td>💧 Water (Kapha)</td>
                                      <td>Moon, Venus</td>
                                      <td>Calmness, nurturing, steadiness</td>
                                    </tr>
                                    <tr>
                                      <td>🌬️ Air (Vata)</td>
                                      <td>Mercury, Jupiter, Rahu</td>
                                      <td>Thinking, adaptability</td>
                                    </tr>
                                    <tr>
                                      <td>🌍 Earth (Kapha)</td>
                                      <td>Saturn</td>
                                      <td>Grounding, patience</td>
                                    </tr>
                                  </tbody>
                                </table>
                                
                                <div className="astrological-summary">
                                  <h5>🪔 Astrological Summary</h5>
                                  {Object.entries(healthData.planet_analysis || {}).map(([planet, analysis]) => {
                                    const house = analysis.basic_analysis?.basic_info?.house;
                                    const element = analysis.element;
                                    const dignity = analysis.basic_analysis?.dignity_analysis?.dignity;
                                    return (
                                      <p key={planet}>
                                        <strong>{planet}</strong> ({element}) in {house}th → {dignity === 'exalted' ? 'strong' : dignity === 'debilitated' ? 'weak' : 'moderate'} {element.toLowerCase()} influence
                                      </p>
                                    );
                                  })}
                                  <p><strong>➡️ Result:</strong> {constitution.primary}</p>
                                </div>
                              </div>
                            </details>
                          </div>
                          
                          <div className="constitution-meaning">
                            <h4>💫 What This Means for You</h4>
                            <table className="meaning-table">
                              <thead>
                                <tr>
                                  <th>Aspect</th>
                                  <th>Fire (Pitta)</th>
                                  <th>Water (Kapha)</th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr>
                                  <td><strong>Body</strong></td>
                                  <td>Warm, active, strong digestion</td>
                                  <td>Steady, smooth, cool temperament</td>
                                </tr>
                                <tr>
                                  <td><strong>Mind</strong></td>
                                  <td>Focused, ambitious</td>
                                  <td>Compassionate, calm</td>
                                </tr>
                                <tr>
                                  <td><strong>Strengths</strong></td>
                                  <td>Discipline, clarity, leadership</td>
                                  <td>Endurance, emotional balance</td>
                                </tr>
                                <tr>
                                  <td><strong>When imbalanced</strong></td>
                                  <td>Irritability, heat, acidity</td>
                                  <td>Lethargy, water retention</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                          
                          <div className="lifestyle-alignment">
                            <h4>🧘♀️ Lifestyle Alignment</h4>
                            <div className="lifestyle-grid">
                              <div className="favorable">
                                <h5>Favorable:</h5>
                                <ul>
                                  <li>Regular daily routine</li>
                                  <li>Light, warm foods with mild spices</li>
                                  <li>Morning meditation or pranayama</li>
                                  <li>Moderate physical activity (yoga, walking)</li>
                                </ul>
                              </div>
                              <div className="avoid">
                                <h5>Avoid:</h5>
                                <ul>
                                  <li>Skipping meals or sleep</li>
                                  <li>Over-eating heavy dairy/oily foods</li>
                                  <li>Over-heating (too much sun exposure)</li>
                                </ul>
                              </div>
                            </div>
                          </div>
                          
                          <div className="harmony-insight">
                            <h4>🕉️ Harmony Insight</h4>
                            <blockquote>
                              "Your inner fire drives your purpose; your calm waters sustain your peace. Balance these two and your energy stays steady in all seasons."
                            </blockquote>
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>
                

              </div>
            </div>
          )}
        </div>

        {/* Planetary Health Analysis */}
        <div className="analysis-section">
          <div className="card-header" onClick={() => toggleSection('planetary-health')}>
            <div className="card-icon" style={{ backgroundColor: '#2196F3' }}>
              🪐
            </div>
            <div className="card-info">
              <h4>Planetary Health Analysis</h4>
              <p>All 9 planets health impact</p>
            </div>
            <div className="card-status">
              <span className={`expand-icon ${expandedSections['planetary-health'] ? 'expanded' : ''}`}>▼</span>
            </div>
          </div>
          
          {expandedSections['planetary-health'] && (
            <div className="card-content">
              <div className="planets-grid">
                {healthData.planet_analysis && Object.entries(healthData.planet_analysis).map(([planet, analysis]) => {
                  const planetSymbols = {
                    'Sun': '☉',
                    'Moon': '☽',
                    'Mars': '♂',
                    'Mercury': '☿',
                    'Jupiter': '♃',
                    'Venus': '♀',
                    'Saturn': '♄',
                    'Rahu': '☊',
                    'Ketu': '☋'
                  };
                  
                  const bodyParts = {
                    'Sun': 'Vitality, Heart, Bones',
                    'Moon': 'Mind, Fluids, Digestive',
                    'Mars': 'Blood, Muscles, Energy',
                    'Mercury': 'Nervous, Respiratory, Communication',
                    'Jupiter': 'Liver, Immunity, Growth',
                    'Venus': 'Reproductive, Hormones, Beauty',
                    'Saturn': 'Bones, Teeth, Chronic',
                    'Rahu': 'Toxins, Stress, Nervous',
                    'Ketu': 'Hidden ailments, Detachment, Spiritual'
                  };
                  
                  const getDignityClass = (dignity) => {
                    const positive = ['own_sign', 'exalted', 'moolatrikona'];
                    const negative = ['debilitated', 'enemy_sign'];
                    
                    if (positive.includes(dignity)) return 'positive';
                    if (negative.includes(dignity)) return 'negative';
                    return '';
                  };

                  const getStrengthClass = (strength) => {
                    if (strength >= 5) return 'positive';
                    if (strength <= 2) return 'negative';
                    return '';
                  };

                  const getFriendshipClass = (relationship) => {
                    const positive = ['great_friend', 'friend'];
                    const negative = ['great_enemy', 'enemy'];
                    
                    if (positive.includes(relationship?.toLowerCase())) return 'positive';
                    if (negative.includes(relationship?.toLowerCase())) return 'negative';
                    return '';
                  };

                  const getCombustionClass = (isCombust) => {
                    return isCombust ? 'negative' : '';
                  };

                  const getHousePlacementClass = (house, planet) => {
                    const favorable = [1, 4, 5, 7, 9, 10, 11]; // Kendra, Trikona, Upachaya
                    const unfavorable = [6, 8, 12]; // Dusthana
                    
                    // Check for Viparita Raja Yoga (dusthana lord in dusthana)
                    const planetLordships = analysis.basic_analysis?.house_position_analysis?.house_types || [];
                    const isDusthanaLord = planetLordships.some(type => type.includes('6th') || type.includes('8th') || type.includes('12th'));
                    
                    // Check if any health yogas are cancelling negative effects for this planet
                    const hasYogaCancellation = healthData.yoga_analysis?.beneficial_yogas?.some(yoga => {
                      return yoga.planet === planet || (yoga.planets && yoga.planets.includes(planet));
                    }) || false;
                    
                    if (unfavorable.includes(house) && isDusthanaLord) {
                      return 'positive'; // Viparita Raja Yoga - dusthana lord in dusthana is good
                    } else if (unfavorable.includes(house) && hasYogaCancellation) {
                      return 'moderate'; // Negative placement but cancelled by beneficial yoga
                    } else if (favorable.includes(house)) {
                      return 'moderate';
                    } else if (unfavorable.includes(house)) {
                      return 'negative';
                    }
                    return '';
                  };

                  const getGandantaClass = (gandantaData) => {
                    if (gandantaData?.is_gandanta) {
                      return gandantaData.intensity === 'High' ? 'negative' : 'moderate';
                    }
                    return '';
                  };

                  const getAspectClass = (aspectAnalysis) => {
                    if (!aspectAnalysis?.has_aspects) return '';
                    const maleficCount = aspectAnalysis.malefic_aspects?.length || 0;
                    const beneficCount = aspectAnalysis.benefic_aspects?.length || 0;
                    
                    if (maleficCount > beneficCount) return 'moderate';
                    if (beneficCount > maleficCount) return 'positive';
                    return 'moderate';
                  };
                  
                  const signNames = {
                    0: 'Aries', 1: 'Taurus', 2: 'Gemini', 3: 'Cancer',
                    4: 'Leo', 5: 'Virgo', 6: 'Libra', 7: 'Scorpio',
                    8: 'Sagittarius', 9: 'Capricorn', 10: 'Aquarius', 11: 'Pisces'
                  };
                  
                  return (
                    <div key={planet} className="planet-card">
                      <div className="planet-header">
                        <div className="planet-symbol">{planetSymbols[planet]}</div>
                        <div className="planet-info">
                          <h3 data-symbol={planetSymbols[planet]}>{planet}</h3>
                          <span className="body-parts">{bodyParts[planet]}</span>
                        </div>
                        <div className={`strength-badge ${(() => {
                          const shadbala = analysis.basic_analysis?.strength_analysis?.shadbala_rupas || 0;
                          const conjunctions = analysis.basic_analysis?.conjunctions?.conjunctions || [];
                          const maleficConjunctions = conjunctions.filter(c => ['Saturn', 'Mars', 'Rahu', 'Ketu'].includes(c.planet));
                          
                          // Reduce effective strength if conjunct with multiple malefics
                          if (maleficConjunctions.length >= 2 && shadbala >= 5) {
                            return 'moderate'; // Downgrade from strong to moderate
                          } else if (maleficConjunctions.length >= 3 && shadbala >= 3) {
                            return 'weak'; // Downgrade from moderate to weak
                          } else if (shadbala >= 5) {
                            return 'strong';
                          } else if (shadbala >= 3) {
                            return 'moderate';
                          } else {
                            return 'weak';
                          }
                        })()}`}>
                          {(() => {
                            const shadbala = analysis.basic_analysis?.strength_analysis?.shadbala_rupas || 0;
                            const conjunctions = analysis.basic_analysis?.conjunctions?.conjunctions || [];
                            const maleficConjunctions = conjunctions.filter(c => ['Saturn', 'Mars', 'Rahu', 'Ketu'].includes(c.planet));
                            
                            if (maleficConjunctions.length >= 2 && shadbala >= 5) {
                              return '⚖️ Afflicted'; // Strong Shadbala but afflicted by conjunctions
                            } else if (maleficConjunctions.length >= 3 && shadbala >= 3) {
                              return '⚠️ Heavily Afflicted';
                            } else if (shadbala >= 5) {
                              return '💪 Strong';
                            } else if (shadbala >= 3) {
                              return '⚖️ Moderate';
                            } else {
                              return '⚠️ Weak';
                            }
                          })()
                        }
                        </div>
                      </div>
                      
                      <div className="planet-content">
                        <div className="info-grid">
                          <div className="info-item">
                            <span className="icon">🏛️</span>
                            <div>
                              <strong>Dignity</strong>
                              <p><span className={getDignityClass(analysis.basic_analysis?.dignity_analysis?.dignity)}>{(() => {
                                const dignity = analysis.basic_analysis?.dignity_analysis?.dignity;
                                const sign = signNames[analysis.basic_analysis?.basic_info?.sign] || 'Unknown';
                                
                                if (dignity === 'own_sign') {
                                  return `in own sign ${sign}`;
                                } else if (dignity === 'exalted') {
                                  return `exalted in ${sign}`;
                                } else if (dignity === 'debilitated') {
                                  return `debilitated in ${sign}`;
                                } else if (dignity === 'moolatrikona') {
                                  return `moolatrikona in ${sign}`;
                                } else {
                                  return `${dignity || 'neutral'} in ${sign}`;
                                }
                              })()}</span></p>
                            </div>
                          </div>
                          
                          <div className="info-item">
                            <span className="icon">🏠</span>
                            <div>
                              <strong>House</strong>
                              <p><span className={getHousePlacementClass(analysis.basic_analysis?.basic_info?.house, planet)}>{analysis.basic_analysis?.basic_info?.house}th house</span>{(() => {
                                const house = analysis.basic_analysis?.basic_info?.house;
                                const planetLordships = analysis.basic_analysis?.house_position_analysis?.house_types || [];
                                const isDusthanaLord = planetLordships.some(type => type.includes('6th') || type.includes('8th') || type.includes('12th'));
                                const unfavorable = [6, 8, 12];
                                
                                // Check for yoga cancellation
                                const hasYogaCancellation = healthData.yoga_analysis?.beneficial_yogas?.some(yoga => {
                                  return yoga.planet === planet || (yoga.planets && yoga.planets.includes(planet));
                                }) || false;
                                
                                if (unfavorable.includes(house) && isDusthanaLord) {
                                  return ' (Viparita Raja Yoga)';
                                } else if (unfavorable.includes(house) && hasYogaCancellation) {
                                  const yogaName = healthData.yoga_analysis.beneficial_yogas.find(yoga => 
                                    yoga.planet === planet || (yoga.planets && yoga.planets.includes(planet))
                                  )?.name || 'Beneficial Yoga';
                                  return ` (${yogaName} cancels negative effects)`;
                                }
                                return '';
                              })()}</p>
                            </div>
                          </div>
                          
                          <div className="info-item">
                            <span className="icon">🔥</span>
                            <div>
                              <strong>Shadbala</strong>
                              <p><span className={getStrengthClass(analysis.basic_analysis?.strength_analysis?.shadbala_rupas)}>{analysis.basic_analysis?.strength_analysis?.shadbala_rupas?.toFixed(1) || 0}</span>/7 Rupas</p>
                            </div>
                          </div>
                          
                          <div className="info-item">
                            <span className="icon">{analysis.basic_analysis?.combustion_status?.is_combust ? '🌞' : '✨'}</span>
                            <div>
                              <strong>Status</strong>
                              <p><span className={getCombustionClass(analysis.basic_analysis?.combustion_status?.is_combust)}>{analysis.basic_analysis?.combustion_status?.is_combust ? 'Combust' : 'Normal'}</span></p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="relationships">
                          <div className="relationship-item">
                            <span className="icon">🤝</span>
                            <p dangerouslySetInnerHTML={{
                              __html: (() => {
                                const fa = analysis.basic_analysis?.friendship_analysis;
                                const sign = analysis.basic_analysis?.basic_info?.sign;
                                const signName = signNames[sign] || 'Unknown';
                                const signLords = {0:'Mars',1:'Venus',2:'Mercury',3:'Moon',4:'Sun',5:'Mercury',6:'Venus',7:'Mars',8:'Jupiter',9:'Saturn',10:'Saturn',11:'Jupiter'};
                                const signLord = signLords[sign];
                                const relationship = fa?.friendship_matrix?.[signLord];
                                const relMap = {great_friend:'Great Friend',friend:'Friend',neutral:'Neutral',enemy:'Enemy',great_enemy:'Great Enemy'};
                                console.log(`${planet} relationship with ${signLord}:`, relationship);
                                const displayText = relMap[relationship] || relationship;
                                return relationship ? `<span class="${getFriendshipClass(relationship)}">${displayText}</span> of ${signName} lord ${signLord}` : 'Unknown relationship';
                              })()
                            }}></p>
                          </div>
                        </div>
                        
                        {(() => {
                          const sl = analysis.basic_analysis?.special_lordships;
                          const roles = [];
                          if (sl?.is_yogi_lord) roles.push({text: '🧘 Yogi Lord', type: 'good'});
                          if (sl?.is_avayogi_lord) roles.push({text: '⚡ Avayogi Lord', type: 'bad'});
                          if (sl?.is_dagdha_lord) roles.push({text: '🔥 Dagdha Lord', type: 'bad'});
                          if (sl?.is_tithi_shunya_lord) roles.push({text: '🌑 Tithi Shunya Lord', type: 'bad'});
                          if (sl?.is_badhaka_lord) roles.push({text: '⚠️ Badhaka Lord', type: 'bad'});
                          return roles.length > 0 ? (
                            <div className="special-roles">
                              {roles.map((role, index) => (
                                <span key={index} className={`role-badge role-${role.type}`}>{role.text}</span>
                              ))}
                            </div>
                          ) : null;
                        })()}
                        
                        {analysis.basic_analysis?.gandanta_analysis?.is_gandanta && (
                          <div className="gandanta-info">
                            <span className={`gandanta-badge ${getGandantaClass(analysis.basic_analysis.gandanta_analysis)}`}>
                              🌀 Gandanta ({analysis.basic_analysis.gandanta_analysis.gandanta_type || analysis.basic_analysis.gandanta_analysis.junction || 'Unknown'}, {analysis.basic_analysis.gandanta_analysis.intensity} intensity)
                            </span>
                          </div>
                        )}
                        
                        {analysis.basic_analysis?.aspects_received?.has_aspects && (
                          <div className="aspects-info">
                            <span className={`aspects-badge ${getAspectClass(analysis.basic_analysis.aspects_received)}`}>
                              👁️ Aspected by {analysis.basic_analysis.aspects_received.aspects.map(a => a.aspecting_planet).join(', ')}
                            </span>
                          </div>
                        )}
                        
                        {analysis.basic_analysis?.conjunctions?.has_conjunctions && (
                          <div className="conjunctions-info">
                            <span className={`conjunctions-badge ${(() => {
                              const conjunctions = analysis.basic_analysis.conjunctions.conjunctions;
                              const maleficConjunctions = conjunctions.filter(c => ['Saturn', 'Mars', 'Rahu', 'Ketu'].includes(c.planet));
                              const beneficConjunctions = conjunctions.filter(c => ['Jupiter', 'Venus', 'Mercury', 'Moon'].includes(c.planet));
                              
                              if (maleficConjunctions.length > beneficConjunctions.length) return 'negative';
                              if (beneficConjunctions.length > maleficConjunctions.length) return 'positive';
                              return 'moderate';
                            })()}`}>
                              🤝 Conjunct with {analysis.basic_analysis.conjunctions.conjunctions.map(c => c.planet).join(', ')}
                            </span>
                          </div>
                        )}
                        
                        <div className="health-summary">
                          <p>{(() => {
                            const originalReasoning = analysis.health_impact?.reasoning || `${planet} shows standard influence on health.`;
                            
                            // Check if there's a yoga cancellation for this planet
                            const hasYogaCancellation = healthData.yoga_analysis?.beneficial_yogas?.some(yoga => {
                              return yoga.planet === planet || (yoga.planets && yoga.planets.includes(planet));
                            }) || false;
                            
                            if (hasYogaCancellation) {
                              const yoga = healthData.yoga_analysis.beneficial_yogas.find(yoga => 
                                yoga.planet === planet || (yoga.planets && yoga.planets.includes(planet))
                              );
                              const yogaName = yoga?.name || 'Beneficial Yoga';
                              
                              // Get lordship information for detailed explanation
                              const planetLordships = analysis.basic_analysis?.house_position_analysis?.house_types || [];
                              const dusthanaLordships = planetLordships.filter(type => type.includes('6th') || type.includes('8th') || type.includes('12th'));
                              const currentHouse = analysis.basic_analysis?.basic_info?.house;
                              
                              console.log(`${planet} lordships:`, planetLordships, 'dusthana lordships:', dusthanaLordships, 'current house:', currentHouse);
                              
                              if (dusthanaLordships.length > 0 && [6, 8, 12].includes(currentHouse)) {
                                const lordshipText = dusthanaLordships.join(', ');
                                return `${originalReasoning}, but this is cancelled by ${yogaName} as ${planet} is Lord of ${lordshipText.replace('house lord', '')} Dusthana and is in another (${currentHouse}th) Dusthana.`;
                              } else {
                                return `${originalReasoning}, but this is cancelled by ${yogaName}.`;
                              }
                            }
                            
                            return originalReasoning;
                          })()}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* House Health Analysis */}
        <div className="analysis-section">
          <div className="card-header" onClick={() => toggleSection('house-health')}>
            <div className="card-icon" style={{ backgroundColor: '#FF9800' }}>
              🏠
            </div>
            <div className="card-info">
              <h4>House Health Analysis</h4>
              <p>Health houses analysis</p>
            </div>
            <div className="card-status">
              <span className={`expand-icon ${expandedSections['house-health'] ? 'expanded' : ''}`}>▼</span>
            </div>
          </div>
          
          {expandedSections['house-health'] && (
            <div className="card-content">
              <div className="planets-grid">
                {healthData.house_analysis && (() => {
                  const houseSymbols = {
                    '1': '🏠', '2': '💰', '6': '⚔️', '7': '💑', '8': '🔮', '12': '🧘'
                  };
                  
                  const houseNames = {
                    '1': 'Physical Body & Vitality',
                    '2': 'Face, Speech & Family Health',
                    '6': 'Diseases & Immunity',
                    '7': 'Partnerships & Health',
                    '8': 'Chronic Illness & Longevity',
                    '12': 'Hospitalization & Mental Health'
                  };
                  
                  const getDignityClass = (dignity) => {
                    const positive = ['own_sign', 'exalted', 'moolatrikona'];
                    const negative = ['debilitated', 'enemy_sign'];
                    
                    if (positive.includes(dignity)) return 'positive';
                    if (negative.includes(dignity)) return 'negative';
                    return '';
                  };
                  
                  return Object.entries(healthData.house_analysis).map(([house, analysis]) => (
                    <div key={house} className="planet-card">
                      <div className="planet-header">
                        <div className="planet-symbol">{houseSymbols[house] || '🏠'}</div>
                        <div className="planet-info">
                          <h3>{(() => {
                            const houseNum = parseInt(house);
                            if (houseNum === 1) return '1st House';
                            if (houseNum === 2) return '2nd House';
                            if (houseNum === 3) return '3rd House';
                            if (houseNum === 21) return '21st House';
                            if (houseNum === 22) return '22nd House';
                            if (houseNum === 23) return '23rd House';
                            return `${houseNum}th House`;
                          })()}</h3>
                          <span className="body-parts">{houseNames[house] || 'Health influence'}</span>
                        </div>
                        <div className={`strength-badge ${(() => {
                          const score = analysis.house_analysis?.overall_house_assessment?.overall_strength_score || 0;
                          if (score >= 70) return 'strong';
                          if (score >= 40) return 'moderate';
                          return 'weak';
                        })()}`}>
                          {(() => {
                            const score = analysis.house_analysis?.overall_house_assessment?.overall_strength_score || 0;
                            if (score >= 70) return '💪 Strong';
                            if (score >= 40) return '⚖️ Average';
                            return '⚠️ Weak';
                          })()} ({(analysis.house_analysis?.overall_house_assessment?.overall_strength_score || 0).toFixed(0)})
                        </div>
                      </div>
                      
                      <div className="planet-content">
                        <div className="info-grid">
                          <div className="info-item">
                            <span className="icon">♈</span>
                            <div>
                              <strong>Sign</strong>
                              <p>{analysis.house_analysis?.basic_info?.house_sign_name || 'Unknown'}</p>
                            </div>
                          </div>
                          
                          <div className="info-item">
                            <span className="icon">👑</span>
                            <div>
                              <strong>Lord</strong>
                              <p><span className={getDignityClass(analysis.house_analysis?.house_lord_analysis?.dignity_analysis?.dignity)}>{analysis.house_analysis?.basic_info?.house_lord || 'Unknown'}</span></p>
                            </div>
                          </div>
                          
                          <div className="info-item">
                            <span className="icon">🏛️</span>
                            <div>
                              <strong>Lord Dignity</strong>
                              <p><span className={getDignityClass(analysis.house_analysis?.house_lord_analysis?.dignity_analysis?.dignity)}>{analysis.house_analysis?.house_lord_analysis?.dignity_analysis?.dignity || 'Neutral'}</span></p>
                            </div>
                          </div>
                          
                          <div className="info-item">
                            <span className="icon">🎯</span>
                            <div>
                              <strong>House Types</strong>
                              <p>{analysis.house_analysis?.basic_info?.house_types?.join(', ') || 'Standard'}</p>
                            </div>
                          </div>
                        </div>
                        
                        {analysis.house_analysis?.resident_planets?.length > 0 && (
                          <div className="residents-info">
                            <span className="residents-badge">
                              🪐 Residents: {analysis.house_analysis.resident_planets.map(p => p.planet).join(', ')}
                            </span>
                          </div>
                        )}
                        
                        {analysis.house_analysis?.aspects_received?.length > 0 && (
                          <div className="aspects-info">
                            <span className="aspects-badge moderate">
                              👁️ Aspected by {analysis.house_analysis.aspects_received.map(a => a.aspecting_planet).join(', ')}
                            </span>
                          </div>
                        )}
                        
                        {analysis.house_analysis?.special_house_analysis?.dusthana_cancellation && (
                          <div className="special-yoga">
                            <span className="yoga-badge positive">
                              ✨ {analysis.house_analysis.special_house_analysis.dusthana_cancellation}
                            </span>
                          </div>
                        )}
                        
                        <div className="health-summary">
                          <p>{analysis.health_interpretation || 'Standard house influence on health'}</p>
                        </div>
                      </div>
                    </div>
                  ));
                })()}
              </div>
            </div>
          )}
        </div>

        {/* Health Yogas Analysis */}
        <div className="analysis-section">
          <div className="card-header" onClick={() => toggleSection('health-yogas')}>
            <div className="card-icon" style={{ backgroundColor: '#9C27B0' }}>
              ✨
            </div>
            <div className="card-info">
              <h4>Health Yogas Analysis</h4>
              <p>Beneficial & affliction yogas</p>
            </div>
            <div className="card-status">
              <span className={`expand-icon ${expandedSections['health-yogas'] ? 'expanded' : ''}`}>▼</span>
            </div>
          </div>
          
          {expandedSections['health-yogas'] && (
            <div className="card-content">
              <div className="yogas-analysis">
                {/* Beneficial Yogas */}
                {healthData.yoga_analysis?.beneficial_yogas && healthData.yoga_analysis.beneficial_yogas.length > 0 && (
                  <div className="yoga-category beneficial-yogas">
                    <h5>✅ Beneficial Health Yogas ({healthData.yoga_analysis.total_beneficial})</h5>
                    <div className="yoga-list">
                      {healthData.yoga_analysis.beneficial_yogas.map((yoga, index) => (
                        <div key={index} className="yoga-item benefic">
                          <div className="yoga-header">
                            <span className="yoga-name">{yoga.name}</span>
                            <span className="yoga-strength moderate">
                              Beneficial
                            </span>
                          </div>
                          <div className="yoga-description">{yoga.description}</div>
                          {yoga.reasoning && <div className="yoga-effect">Reasoning: {yoga.reasoning}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Affliction Yogas */}
                {healthData.yoga_analysis?.affliction_yogas && healthData.yoga_analysis.affliction_yogas.length > 0 && (
                  <div className="yoga-category affliction-yogas">
                    <h5>⚠️ Health Affliction Yogas ({healthData.yoga_analysis.total_afflictions})</h5>
                    <div className="yoga-list">
                      {healthData.yoga_analysis.affliction_yogas.map((yoga, index) => (
                        <div key={index} className="yoga-item malefic">
                          <div className="yoga-header">
                            <span className="yoga-name">{yoga.name}</span>
                            <span className="yoga-strength moderate">
                              Affliction
                            </span>
                          </div>
                          <div className="yoga-description">{yoga.description}</div>
                          {yoga.reasoning && <div className="yoga-effect">Reasoning: {yoga.reasoning}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Gandanta Health Impact */}
        <div className="analysis-section">
          <div className="card-header" onClick={() => toggleSection('gandanta-health')}>
            <div className="card-icon" style={{ backgroundColor: '#607D8B' }}>
              🌀
            </div>
            <div className="card-info">
              <h4>Gandanta Health Impact</h4>
              <p>Karmic knots health analysis</p>
            </div>
            <div className="card-status">
              <span className={`expand-icon ${expandedSections['gandanta-health'] ? 'expanded' : ''}`}>▼</span>
            </div>
          </div>
          
          {expandedSections['gandanta-health'] && (
            <div className="card-content">
              <div className="timeline-remedies">
                {healthData.health_timeline && (
                  <div className="health-timeline">
                    <h5>📅 Health Timeline</h5>
                    <div className="timeline-info">
                      <p><strong>Current Period:</strong> {healthData.health_timeline.current_period}</p>
                      <p><strong>Health Focus:</strong> {healthData.health_timeline.health_focus}</p>
                      <p><strong>Upcoming Challenges:</strong> {healthData.health_timeline.upcoming_challenges}</p>
                      {healthData.health_timeline.favorable_periods && (
                        <div className="favorable-periods">
                          <strong>Favorable Periods:</strong>
                          <ul>
                            {healthData.health_timeline.favorable_periods.map((period, index) => (
                              <li key={index}>{period}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {healthData.health_remedies && (
                  <div className="health-remedies">
                    <h5>💊 Health Remedies</h5>
                    <div className="remedies-grid">
                      {healthData.health_remedies.gemstones && (
                        <div className="remedy-category">
                          <strong>Gemstones:</strong>
                          <ul>
                            {healthData.health_remedies.gemstones.map((gem, index) => (
                              <li key={index}>{gem}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {healthData.health_remedies.lifestyle && (
                        <div className="remedy-category">
                          <strong>Lifestyle:</strong>
                          <ul>
                            {healthData.health_remedies.lifestyle.map((advice, index) => (
                              <li key={index}>{advice}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {healthData.health_remedies.mantras && (
                        <div className="remedy-category">
                          <strong>Mantras:</strong>
                          <ul>
                            {healthData.health_remedies.mantras.map((mantra, index) => (
                              <li key={index}>{mantra}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      {modalData && (
        <div className="analysis-modal-overlay" onClick={closeModal}>
          <div className="analysis-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{modalData.title}</h3>
              <button className="close-btn" onClick={closeModal}>×</button>
            </div>
            <div className="modal-content">
              {modalData.content}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CompleteHealthAnalysisTab;