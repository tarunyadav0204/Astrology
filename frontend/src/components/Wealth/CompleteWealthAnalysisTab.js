import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import './CompleteWealthAnalysisTab.css';

const CompleteWealthAnalysisTab = ({ chartData, birthDetails }) => {
  const [wealthData, setWealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedSections, setExpandedSections] = useState({});
  const [modalData, setModalData] = useState(null);

  useEffect(() => {
    const loadWealthAnalysis = async () => {
      if (!birthDetails) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/wealth/overall-assessment', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            birth_date: birthDetails.date,
            birth_time: birthDetails.time,
            birth_place: birthDetails.place,
            latitude: birthDetails.latitude,
            longitude: birthDetails.longitude,
            timezone: birthDetails.timezone
          })
        });
        
        if (!response.ok) {
          if (response.status === 401) {
            throw new Error('Authentication required. Please log in again.');
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        setWealthData(result.data);
      } catch (error) {
        console.error('Error loading wealth analysis:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    loadWealthAnalysis();
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
      <div className="complete-wealth-analysis">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Analyzing wealth prospects...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="complete-wealth-analysis">
        <div className="error-state">
          <h3>⚠️ Analysis Error</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry Analysis</button>
        </div>
      </div>
    );
  }

  if (!wealthData) {
    return (
      <div className="complete-wealth-analysis">
        <div className="no-data-state">
          <p>No wealth analysis available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="complete-wealth-analysis">
      <div className="analysis-header">
        <h3>💰 Complete Wealth Analysis</h3>
        <p>Comprehensive Vedic wealth analysis with detailed calculations</p>
      </div>

      <div className="analysis-sections">
        {/* Wealth Score & Constitution */}
        <div className="analysis-section">
          <div className="card-header" onClick={() => toggleSection('wealth-score')}>
            <div className="card-icon" style={{ backgroundColor: '#667eea' }}>
              💎
            </div>
            <div className="card-info">
              <h4>Wealth Constitution Analysis</h4>
              <p>Overall wealth potential and constitution type</p>
            </div>
            <div className="card-status">
              <span className={`expand-icon ${expandedSections['wealth-score'] ? 'expanded' : ''}`}>▼</span>
            </div>
          </div>
          
          {expandedSections['wealth-score'] && (
            <div className="card-content">
              <div className="wealth-score-summary">
                <div className="score-display">
                  <div className="score-circle">
                    <span className="score-number">{wealthData.wealth_score}</span>
                    <span className="score-label">Wealth Score</span>
                  </div>
                  <div className="score-breakdown">
                    <h5>Score Breakdown:</h5>
                    <ul>
                      {wealthData.wealth_score_breakdown.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                
                <div className="constitution-info">
                  <h4>💫 Wealth Constitution</h4>
                  <p className="constitution-type">{wealthData.wealth_constitution}</p>
                  
                  <div className="income-sources">
                    <h5>Primary Income Sources:</h5>
                    <ul>
                      {wealthData.income_sources.map((source, idx) => (
                        <li key={idx}>{source}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Planetary Wealth Analysis */}
        <div className="analysis-section">
          <div className="card-header" onClick={() => toggleSection('planetary-wealth')}>
            <div className="card-icon" style={{ backgroundColor: '#2196F3' }}>
              🪐
            </div>
            <div className="card-info">
              <h4>Planetary Wealth Analysis</h4>
              <p>All 9 planets wealth impact</p>
            </div>
            <div className="card-status">
              <span className={`expand-icon ${expandedSections['planetary-wealth'] ? 'expanded' : ''}`}>▼</span>
            </div>
          </div>
          
          {expandedSections['planetary-wealth'] && (
            <div className="card-content">
              <div className="planets-grid">
                {wealthData.planet_analysis && Object.entries(wealthData.planet_analysis).map(([planet, analysis]) => {
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
                  
                  const getDignityClass = (dignity) => {
                    const positive = ['own_sign', 'exalted', 'moolatrikona'];
                    const negative = ['debilitated', 'enemy_sign'];
                    
                    if (positive.includes(dignity)) return 'positive';
                    if (negative.includes(dignity)) return 'negative';
                    return '';
                  };
                  
                  return (
                    <div key={planet} className="planet-card">
                      <div className="planet-header">
                        <div className="planet-symbol">{planetSymbols[planet]}</div>
                        <div className="planet-info">
                          <h3 data-symbol={planetSymbols[planet]}>{planet}</h3>
                          <span className="wealth-systems">{analysis.wealth_systems?.slice(0, 2).join(', ') || 'Wealth influence'}</span>
                        </div>
                        <div 
                          className={`strength-badge clickable ${(() => {
                            const classicalGrade = analysis.basic_analysis?.overall_assessment?.classical_grade;
                            if (classicalGrade?.includes('Uttama')) return 'uttama';
                            if (classicalGrade?.includes('Madhyama')) return 'madhyama';
                            return 'adhama';
                          })()}`}
                          onClick={() => openModal(
                            `${planet} Classical Assessment`,
                            <div className="calculation-details">
                              <h4>Classical Vedic Planetary Assessment</h4>
                              
                              {analysis.basic_analysis?.overall_assessment?.assessment_factors && (
                                <div className="assessment-factors">
                                  <h5>Assessment Factors</h5>
                                  <div className="factors-visual">
                                    <div className="factor-bars">
                                      {Object.entries(analysis.basic_analysis.overall_assessment.assessment_factors).map(([factor, data]) => (
                                        <div key={factor} className="factor-bar">
                                          <div className="factor-name">{factor.replace(/_/g, ' ')}</div>
                                          <div className="progress-bar">
                                            <div 
                                              className="progress-fill" 
                                              style={{width: `${data.value}%`}}
                                            />
                                          </div>
                                          <div className="factor-score">{data.value?.toFixed(0)}/100</div>
                                          <div className="factor-reasoning">{data.reasoning}</div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              )}
                              
                              <div className="final-assessment">
                                <h5>Final Classical Assessment</h5>
                                <div className="assessment-result">
                                  <p><strong>Grade:</strong> {analysis.basic_analysis?.overall_assessment?.classical_grade}</p>
                                  <p><strong>Overall Score:</strong> {analysis.basic_analysis?.overall_assessment?.overall_strength_score}/100</p>
                                </div>
                              </div>
                            </div>
                          )}
                        >
                          {(() => {
                            const classicalGrade = analysis.basic_analysis?.overall_assessment?.classical_grade;
                            const score = analysis.basic_analysis?.overall_assessment?.overall_strength_score || 0;
                            
                            if (classicalGrade?.includes('Uttama')) {
                              return '💪 Uttama';
                            } else if (classicalGrade?.includes('Madhyama')) {
                              return '⚖️ Madhyama';
                            } else {
                              return '⚠️ Adhama';
                            }
                          })()} ({(analysis.basic_analysis?.overall_assessment?.overall_strength_score || 0).toFixed(0)}) 🔍
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
                                const signNames = {
                                  0: 'Aries', 1: 'Taurus', 2: 'Gemini', 3: 'Cancer',
                                  4: 'Leo', 5: 'Virgo', 6: 'Libra', 7: 'Scorpio',
                                  8: 'Sagittarius', 9: 'Capricorn', 10: 'Aquarius', 11: 'Pisces'
                                };
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
                              <p>{analysis.basic_analysis?.basic_info?.house}th house</p>
                            </div>
                          </div>
                          
                          <div className="info-item">
                            <span className="icon">🔥</span>
                            <div>
                              <strong>Classical Score</strong>
                              <p><span className={(() => {
                                const score = analysis.basic_analysis?.overall_assessment?.overall_strength_score || 0;
                                if (score >= 75) return 'positive';
                                if (score >= 50) return 'moderate';
                                return 'negative';
                              })()}>{(analysis.basic_analysis?.overall_assessment?.overall_strength_score || 0).toFixed(0)}</span>/100</p>
                            </div>
                          </div>
                          
                          <div className="info-item">
                            <span className="icon">{analysis.basic_analysis?.combustion_status?.is_combust ? '🌞' : '✨'}</span>
                            <div>
                              <strong>Status</strong>
                              <p><span className={analysis.basic_analysis?.combustion_status?.is_combust ? 'negative' : ''}>{analysis.basic_analysis?.combustion_status?.is_combust ? 'Combust' : 'Normal'}</span></p>
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
                                const signNames = {
                                  0: 'Aries', 1: 'Taurus', 2: 'Gemini', 3: 'Cancer',
                                  4: 'Leo', 5: 'Virgo', 6: 'Libra', 7: 'Scorpio',
                                  8: 'Sagittarius', 9: 'Capricorn', 10: 'Aquarius', 11: 'Pisces'
                                };
                                const signName = signNames[sign] || 'Unknown';
                                const signLords = {0:'Mars',1:'Venus',2:'Mercury',3:'Moon',4:'Sun',5:'Mercury',6:'Venus',7:'Mars',8:'Jupiter',9:'Saturn',10:'Saturn',11:'Jupiter'};
                                const signLord = signLords[sign];
                                const relationship = fa?.friendship_matrix?.[signLord];
                                const relMap = {great_friend:'Great Friend',friend:'Friend',neutral:'Neutral',enemy:'Enemy',great_enemy:'Great Enemy'};
                                const displayText = relMap[relationship] || relationship;
                                const getFriendshipClass = (rel) => {
                                  const positive = ['great_friend', 'friend'];
                                  const negative = ['great_enemy', 'enemy'];
                                  if (positive.includes(rel?.toLowerCase())) return 'positive';
                                  if (negative.includes(rel?.toLowerCase())) return 'negative';
                                  return '';
                                };
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
                            <span className={`gandanta-badge ${(() => {
                              const gandantaData = analysis.basic_analysis.gandanta_analysis;
                              if (gandantaData?.is_gandanta) {
                                return gandantaData.intensity === 'High' ? 'negative' : 'moderate';
                              }
                              return '';
                            })()}`}>
                              🌀 Gandanta ({analysis.basic_analysis.gandanta_analysis.gandanta_type || analysis.basic_analysis.gandanta_analysis.junction || 'Unknown'}, {analysis.basic_analysis.gandanta_analysis.intensity} intensity)
                            </span>
                          </div>
                        )}
                        
                        {analysis.basic_analysis?.aspects_received?.has_aspects && (
                          <div className="aspects-info">
                            <span className={`aspects-badge ${(() => {
                              const aspectAnalysis = analysis.basic_analysis.aspects_received;
                              if (!aspectAnalysis?.has_aspects) return '';
                              const maleficCount = aspectAnalysis.malefic_aspects?.length || 0;
                              const beneficCount = aspectAnalysis.benefic_aspects?.length || 0;
                              if (maleficCount > beneficCount) return 'moderate';
                              if (beneficCount > maleficCount) return 'positive';
                              return 'moderate';
                            })()}`}>
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
                        
                        <div className="wealth-summary">
                          <div className="classical-assessment-summary">
                            <p><strong>Classical Grade:</strong> {analysis.basic_analysis?.overall_assessment?.classical_grade}</p>
                            <p><strong>Wealth Impact:</strong> {analysis.wealth_impact?.reasoning}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* House Wealth Analysis */}
        <div className="analysis-section">
          <div className="card-header" onClick={() => toggleSection('house-wealth')}>
            <div className="card-icon" style={{ backgroundColor: '#FF9800' }}>
              🏠
            </div>
            <div className="card-info">
              <h4>House Wealth Analysis</h4>
              <p>Wealth houses analysis</p>
            </div>
            <div className="card-status">
              <span className={`expand-icon ${expandedSections['house-wealth'] ? 'expanded' : ''}`}>▼</span>
            </div>
          </div>
          
          {expandedSections['house-wealth'] && (
            <div className="card-content">
              <div className="house-wealth-grid">
                {wealthData.house_analysis && Object.entries(wealthData.house_analysis).map(([house, analysis]) => {
                  const houseSymbols = {
                    '1': '🏠', '2': '💰', '4': '🏡', '5': '📈', 
                    '7': '🤝', '9': '🍀', '10': '💼', '11': '💎'
                  };
                  
                  const houseNames = {
                    '1': 'Self-effort & Personal Wealth',
                    '2': 'Accumulated Wealth & Assets',
                    '4': 'Property & Real Estate',
                    '5': 'Speculation & Investments',
                    '7': 'Business Partnerships',
                    '9': 'Fortune & Luck',
                    '10': 'Career Income',
                    '11': 'Gains & Income Flow'
                  };
                  
                  return (
                    <div key={house} className="planet-card">
                      <div className="planet-header">
                        <div className="planet-symbol">{houseSymbols[house] || '🏠'}</div>
                        <div className="planet-info">
                          <h3>{house}th House</h3>
                          <span className="body-parts">{houseNames[house] || 'Wealth influence'}</span>
                        </div>
                        <div 
                          className={`strength-badge clickable ${(() => {
                            const score = analysis.house_analysis?.overall_house_assessment?.overall_strength_score || 0;
                            if (score >= 85) return 'strong';
                            if (score >= 55) return 'moderate';
                            return 'weak';
                          })()}`}
                          onClick={() => openModal(
                            `${house}th House Strength Calculation`,
                            <div className="calculation-details">
                              <h4>Classical Vedic Assessment Factors</h4>
                              {analysis.house_analysis?.overall_house_assessment?.assessment_factors && (
                                <div className="factors-breakdown">
                                  {Object.entries(analysis.house_analysis.overall_house_assessment.assessment_factors).map(([factor, data]) => (
                                    <div key={factor} className="factor-item">
                                      <div className="factor-header">
                                        <strong>{factor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</strong>
                                        <span className={`grade-badge ${data.grade?.toLowerCase()}`}>{data.grade}</span>
                                      </div>
                                      <div className="factor-details">
                                        <p><strong>Reasoning:</strong> {data.reasoning}</p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                              
                              <div className="final-assessment">
                                <h5>Final Classical Grade</h5>
                                <div className="grade-explanation">
                                  <p><strong>Grade:</strong> {analysis.house_analysis?.overall_house_assessment?.classical_grade}</p>
                                  <p><strong>Score:</strong> {(analysis.house_analysis?.overall_house_assessment?.overall_strength_score || 0).toFixed(0)}/100</p>
                                </div>
                              </div>
                            </div>
                          )}
                        >
                          {(() => {
                            const score = analysis.house_analysis?.overall_house_assessment?.overall_strength_score || 0;
                            if (score >= 85) return '💪 Strong';
                            if (score >= 55) return '⚖️ Average';
                            return '⚠️ Weak';
                          })()} ({(analysis.house_analysis?.overall_house_assessment?.overall_strength_score || 0).toFixed(0)}) 🔍
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
                              <p>{analysis.house_analysis?.basic_info?.house_lord || 'Unknown'}</p>
                            </div>
                          </div>
                          
                          <div className="info-item">
                            <span className="icon">🏛️</span>
                            <div>
                              <strong>Lord Dignity</strong>
                              <p>{analysis.house_analysis?.house_lord_analysis?.dignity_analysis?.dignity || 'Neutral'}</p>
                            </div>
                          </div>
                          
                          <div className="info-item">
                            <span className="icon">💰</span>
                            <div>
                              <strong>Wealth Significance</strong>
                              <p>{analysis.wealth_significance}</p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="wealth-summary">
                          <p>{analysis.wealth_interpretation}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Wealth Yogas Analysis */}
        <div className="analysis-section">
          <div className="card-header" onClick={() => toggleSection('wealth-yogas')}>
            <div className="card-icon" style={{ backgroundColor: '#4CAF50' }}>
              ✨
            </div>
            <div className="card-info">
              <h4>Wealth Yogas Analysis</h4>
              <p>Dhana, Lakshmi & Raja yogas</p>
            </div>
            <div className="card-status">
              <span className={`expand-icon ${expandedSections['wealth-yogas'] ? 'expanded' : ''}`}>▼</span>
            </div>
          </div>
          
          {expandedSections['wealth-yogas'] && (
            <div className="card-content">
              <div className="yogas-analysis">
                {/* Dhana Yogas */}
                {wealthData.yoga_analysis?.dhana_yogas && wealthData.yoga_analysis.dhana_yogas.length > 0 && (
                  <div className="yoga-category dhana-yogas">
                    <h5>💰 Dhana Yogas ({wealthData.yoga_analysis.dhana_yogas.length})</h5>
                    <div className="yoga-list">
                      {wealthData.yoga_analysis.dhana_yogas.map((yoga, index) => (
                        <div key={index} className="yoga-item benefic">
                          <div className="yoga-header">
                            <span className="yoga-name">{yoga.name}</span>
                            <span className="yoga-strength moderate">Wealth Yoga</span>
                          </div>
                          <div className="yoga-description">{yoga.description}</div>
                          {yoga.reasoning && <div className="yoga-effect">Reasoning: {yoga.reasoning}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Lakshmi Yogas */}
                {wealthData.yoga_analysis?.lakshmi_yogas && wealthData.yoga_analysis.lakshmi_yogas.length > 0 && (
                  <div className="yoga-category lakshmi-yogas">
                    <h5>🌟 Lakshmi Yogas ({wealthData.yoga_analysis.lakshmi_yogas.length})</h5>
                    <div className="yoga-list">
                      {wealthData.yoga_analysis.lakshmi_yogas.map((yoga, index) => (
                        <div key={index} className="yoga-item benefic">
                          <div className="yoga-header">
                            <span className="yoga-name">{yoga.name}</span>
                            <span className="yoga-strength moderate">Prosperity Yoga</span>
                          </div>
                          <div className="yoga-description">{yoga.description}</div>
                          {yoga.reasoning && <div className="yoga-effect">Reasoning: {yoga.reasoning}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Raja Yogas */}
                {wealthData.yoga_analysis?.raja_yogas && wealthData.yoga_analysis.raja_yogas.length > 0 && (
                  <div className="yoga-category raja-yogas">
                    <h5>👑 Raja Yogas ({wealthData.yoga_analysis.raja_yogas.length})</h5>
                    <div className="yoga-list">
                      {wealthData.yoga_analysis.raja_yogas.map((yoga, index) => (
                        <div key={index} className="yoga-item benefic">
                          <div className="yoga-header">
                            <span className="yoga-name">{yoga.name}</span>
                            <span className="yoga-strength moderate">Royal Yoga</span>
                          </div>
                          <div className="yoga-description">{yoga.description}</div>
                          {yoga.reasoning && <div className="yoga-effect">Reasoning: {yoga.reasoning}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Viparita Yogas */}
                {wealthData.yoga_analysis?.viparita_yogas && wealthData.yoga_analysis.viparita_yogas.length > 0 && (
                  <div className="yoga-category viparita-yogas">
                    <h5>🔄 Viparita Raja Yogas ({wealthData.yoga_analysis.viparita_yogas.length})</h5>
                    <div className="yoga-list">
                      {wealthData.yoga_analysis.viparita_yogas.map((yoga, index) => (
                        <div key={index} className="yoga-item benefic">
                          <div className="yoga-header">
                            <span className="yoga-name">{yoga.name}</span>
                            <span className="yoga-strength moderate">Transformation Yoga</span>
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

        {/* Wealth Timeline & Remedies */}
        <div className="analysis-section">
          <div className="card-header" onClick={() => toggleSection('wealth-timeline')}>
            <div className="card-icon" style={{ backgroundColor: '#607D8B' }}>
              📅
            </div>
            <div className="card-info">
              <h4>Wealth Timeline & Remedies</h4>
              <p>Timing and remedial measures</p>
            </div>
            <div className="card-status">
              <span className={`expand-icon ${expandedSections['wealth-timeline'] ? 'expanded' : ''}`}>▼</span>
            </div>
          </div>
          
          {expandedSections['wealth-timeline'] && (
            <div className="card-content">
              <div className="timeline-remedies">
                {wealthData.wealth_timeline && (
                  <div className="wealth-timeline">
                    <h5>📅 Wealth Timeline</h5>
                    <div className="timeline-info">
                      <p><strong>Current Period:</strong> {wealthData.wealth_timeline.current_period}</p>
                      <p><strong>Wealth Focus:</strong> {wealthData.wealth_timeline.wealth_focus}</p>
                      <p><strong>Upcoming Opportunities:</strong> {wealthData.wealth_timeline.upcoming_opportunities}</p>
                      {wealthData.wealth_timeline.favorable_periods && (
                        <div className="favorable-periods">
                          <strong>Favorable Periods:</strong>
                          <ul>
                            {wealthData.wealth_timeline.favorable_periods.map((period, index) => (
                              <li key={index}>{period}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {wealthData.wealth_remedies && (
                  <div className="wealth-remedies">
                    <h5>💎 Wealth Remedies</h5>
                    <div className="remedies-grid">
                      {wealthData.wealth_remedies.gemstones && (
                        <div className="remedy-category">
                          <strong>Gemstones:</strong>
                          <ul>
                            {wealthData.wealth_remedies.gemstones.map((gem, index) => (
                              <li key={index}>{gem}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {wealthData.wealth_remedies.mantras && (
                        <div className="remedy-category">
                          <strong>Mantras:</strong>
                          <ul>
                            {wealthData.wealth_remedies.mantras.map((mantra, index) => (
                              <li key={index}>{mantra}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {wealthData.wealth_remedies.donations && (
                        <div className="remedy-category">
                          <strong>Donations:</strong>
                          <ul>
                            {wealthData.wealth_remedies.donations.map((donation, index) => (
                              <li key={index}>{donation}</li>
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
      {modalData && createPortal(
        <div 
          className="analysis-modal-overlay" 
          onClick={closeModal}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 999999,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'center',
            paddingTop: '100px'
          }}
        >
          <div 
            className="analysis-modal" 
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'white',
              borderRadius: '12px',
              maxWidth: '600px',
              maxHeight: '80vh',
              overflowY: 'auto',
              boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
              zIndex: 999999,
              position: 'relative'
            }}
          >
            <div className="modal-header">
              <h3>{modalData.title}</h3>
              <button className="close-btn" onClick={closeModal}>×</button>
            </div>
            <div className="modal-content">
              {modalData.content}
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default CompleteWealthAnalysisTab;