import React, { useState, useEffect } from 'react';
import { careerService } from '../../services/careerService';
import { NAKSHATRA_CONFIG, CAREER_NAKSHATRA_ROLES } from '../../config/nakshatra.config';
import CareerPersonality from './CareerPersonality';
import CareerPaths from './CareerPaths';
import CareerProfessions from './CareerProfessions';
import CareerTiming from './CareerTiming';
import CareerStrategy from './CareerStrategy';
import { renderYogiBadhakaDetails } from './YogiBadhakaDetails';
import './CareerAnalysisTab.css';

const CareerAnalysisTab = ({ chartData, birthDetails }) => {
  const [activeTab, setActiveTab] = useState('personality');
  const [careerData, setCareerData] = useState(null);
  const [nakshatraData, setNakshatraData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const tabs = [
    { id: 'personality', label: '👤 Your Career Personality' },
    { id: 'professions', label: '💼 Suitable Professions' },
    { id: 'nakshatras', label: '⭐ Nakshatra Analysis' },
    { id: 'timing', label: '⏰ Career Timing' },
    { id: 'strategy', label: '🎯 Growth Strategy' },
    { id: 'complete', label: '🔍 Complete Analysis' }
  ];

  useEffect(() => {
    const loadCareerAnalysis = async () => {
      if (!birthDetails) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const data = await careerService.getComprehensiveAnalysis(birthDetails);
        setCareerData(data);
      } catch (error) {
        console.error('Error loading career analysis:', error);
        setError(error.message || 'Failed to load career analysis');
      } finally {
        setLoading(false);
      }
    };

    loadCareerAnalysis();
    loadNakshatraAnalysis();
  }, [birthDetails]);
  
  const loadNakshatraAnalysis = async () => {
    if (!birthDetails) return;
    
    try {
      const data = await careerService.getNakshatraAnalysis(birthDetails);
      setNakshatraData(data);
    } catch (error) {
      console.error('Error loading nakshatra analysis:', error);
    }
  };

  const renderCareerPersonality = () => {
    return <CareerPersonality birthDetails={birthDetails} />;
  };




  
  const renderProfessions = () => {
    return <CareerProfessions careerData={careerData} />;
  };
  
  const renderTiming = () => {
    return <CareerTiming careerData={careerData} />;
  };
  
  const renderStrategy = () => {
    return <CareerStrategy careerData={careerData} />;
  };
  
  const renderNakshatraAnalysis = () => {
    if (!nakshatraData || !nakshatraData.nakshatra_analysis) {
      return (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading nakshatra analysis...</p>
        </div>
      );
    }
    
    const analysisData = nakshatraData.nakshatra_analysis;
    
    return (
      <div className="nakshatra-analysis">
        <h3>⭐ Key Career Nakshatras</h3>
        <p>Stellar guidance for professional success based on key planetary positions</p>
        
        <div className="core-nakshatras">
          {Object.entries(analysisData.key_nakshatras || {}).map(([role, data]) => {
            const config = NAKSHATRA_CONFIG[data.nakshatra];
            if (!config) return null;
            
            return (
              <div key={role} className="nakshatra-card">
                <div className="nakshatra-header">
                  <h4>{getRoleIcon(role)} {data.planet} - {data.nakshatra}</h4>
                  <span className="nakshatra-lord">Lord: {config.lord}</span>
                  <p className="role-explanation">{getRoleExplanation(role)}</p>
                </div>
                
                <div className="nakshatra-content">
                  <div className="role-description">
                    <strong>{data.description || CAREER_NAKSHATRA_ROLES[role]}</strong>
                  </div>
                  
                  <div className="career-traits">
                    <div className="trait-item">
                      <span className="trait-label">Your natural career approach:</span>
                      <span className="trait-value">{config.career_nature}</span>
                    </div>
                    <div className="trait-item">
                      <span className="trait-label">How you work best:</span>
                      <span className="trait-value">{config.work_style}</span>
                    </div>
                    <div className="trait-item">
                      <span className="trait-label">Your leadership style:</span>
                      <span className="trait-value">{config.leadership_style}</span>
                    </div>
                    <div className="trait-item">
                      <span className="trait-label">Ideal work environment:</span>
                      <span className="trait-value">{config.work_environment}</span>
                    </div>
                  </div>
                  
                  <div className="suitable-fields">
                    <strong>Career fields that suit you:</strong>
                    <div className="field-tags">
                      {config.suitable_fields.map((field, index) => (
                        <span key={index} className="field-tag">{field}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        {analysisData.current_dasha && (
          <div className="nakshatra-timing">
            <h4>⏰ Current Nakshatra Dasha Period</h4>
            <div className="dasha-info">
              <div className="dasha-current">
                <strong>Current Mahadasha:</strong> {analysisData.current_dasha.planet} 
                ({analysisData.current_dasha.start} - {analysisData.current_dasha.end})
              </div>
              <div className="dasha-career-impact">
                <strong>Career Impact:</strong> {analysisData.current_dasha.career_impact}
              </div>
              {analysisData.current_dasha.recommendations && (
                <div className="dasha-recommendations">
                  <strong>Recommendations:</strong>
                  <ul>
                    {analysisData.current_dasha.recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
        
        {analysisData.upcoming_periods && analysisData.upcoming_periods.length > 0 && (
          <div className="upcoming-periods">
            <h4>🔮 Upcoming Favorable Periods</h4>
            <div className="periods-list">
              {analysisData.upcoming_periods.slice(0, 3).map((period, index) => (
                <div key={index} className="period-item">
                  <div className="period-header">
                    <strong>{period.planet} Period</strong>
                    <span className="period-duration">({period.start} - {period.end})</span>
                  </div>
                  <p>{period.career_opportunities}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };
  
  const getRoleIcon = (role) => {
    const icons = {
      'JANMA': '🌙',
      'TENTH_LORD': '🏢',
      'ATMAKARAKA': '👑',
      'AMATYAKARAKA': '🎯',
      'SATURN': '🪐',
      'D10_TENTH_LORD': '📊',
      'LAGNA': '🌅'
    };
    return icons[role] || '⭐';
  };
  
  const getRoleExplanation = (role) => {
    const explanations = {
      'JANMA': 'Your birth nakshatra - reveals your natural career inclinations and core professional identity',
      'TENTH_LORD': 'The planet ruling your 10th house of career - shows how you achieve professional success',
      'ATMAKARAKA': 'Your Atmakaraka (soul planet with highest degrees) - reveals your dharmic path and ultimate career fulfillment',
      'AMATYAKARAKA': 'Your Amatyakaraka (professional minister planet) - reveals your natural work style and career approach',
      'SATURN': 'Saturn as Karma Karaka (natural career significator) - shows your discipline, hard work, and long-term career patterns',
      'D10_TENTH_LORD': 'The 10th lord in your career chart (D10) - indicates specialized professional skills',
      'LAGNA': 'Your ascendant nakshatra - shows how you present yourself professionally to the world'
    };
    return explanations[role] || 'This planetary position influences your career path';
  };
  
  const [completeAnalysisData, setCompleteAnalysisData] = useState({});
  const [completeAnalysisLoading, setCompleteAnalysisLoading] = useState({});

  const loadCompleteAnalysisSection = async (sectionId) => {
    if (completeAnalysisData[sectionId] || completeAnalysisLoading[sectionId]) return;
    
    setCompleteAnalysisLoading(prev => ({ ...prev, [sectionId]: true }));
    
    try {
      let data;
      if (sectionId === 'tenth-lord') {
        data = await careerService.getTenthLordAnalysis(birthDetails);
      } else if (sectionId === 'tenth-house') {
        data = await careerService.getTenthHouseAnalysis(birthDetails);
      } else if (sectionId === 'd10-analysis') {
        data = await careerService.getD10Analysis(birthDetails);
      } else if (sectionId === 'saturn-karaka') {
        data = await careerService.getSaturnKarakaAnalysis(birthDetails);
      } else if (sectionId === 'saturn-tenth') {
        data = await careerService.getSaturnTenthAnalysis(birthDetails);
      } else if (sectionId === 'amatyakaraka') {
        data = await careerService.getAmatyakarakaAnalysis(birthDetails);
      } else if (sectionId === 'career-yogas') {
        data = await careerService.getCareerYogasAnalysis(birthDetails);
      }
      setCompleteAnalysisData(prev => ({ ...prev, [sectionId]: data }));
    } catch (error) {
      console.error(`Error loading ${sectionId}:`, error);
      setCompleteAnalysisData(prev => ({ ...prev, [sectionId]: null }));
    } finally {
      setCompleteAnalysisLoading(prev => ({ ...prev, [sectionId]: false }));
    }
  };

  const renderTenthLordAnalysis = () => {
    const data = completeAnalysisData['tenth-lord'];
    const loading = completeAnalysisLoading['tenth-lord'];
    
    if (loading) {
      return <div className="loading-subsection">Loading 10th lord analysis...</div>;
    }
    
    if (!data) {
      return <div className="error-subsection">Failed to load analysis</div>;
    }
    
    const lordAnalysis = data.lord_analysis;
    const tenthHouseInfo = data.tenth_house_info;
    
    return (
      <div className="tenth-lord-analysis">
        <div className="lord-basic-info">
          <h5>10th House: {tenthHouseInfo.house_sign_name} - Lord: {tenthHouseInfo.house_lord}</h5>
        </div>
        
        <div className="subsection">
          <h5>Dignity Analysis</h5>
          <div className="analysis-data">
            <p><strong>Dignity:</strong> {lordAnalysis.dignity_analysis.dignity}</p>
            <p><strong>Functional Nature:</strong> {lordAnalysis.dignity_analysis.functional_nature}</p>
            <p><strong>Strength Multiplier:</strong> {lordAnalysis.dignity_analysis.strength_multiplier}</p>
            <p><strong>Description:</strong> {lordAnalysis.dignity_analysis.dignity_description}</p>
            {lordAnalysis.dignity_analysis.states.length > 0 && (
              <p><strong>States:</strong> {lordAnalysis.dignity_analysis.states.join(', ')}</p>
            )}
          </div>
        </div>
        
        <div className="subsection">
          <h5>Shadbala Strength</h5>
          <div className="analysis-data">
            <p><strong>Rupas:</strong> {lordAnalysis.strength_analysis.shadbala_rupas.toFixed(2)}</p>
            <p><strong>Grade:</strong> {lordAnalysis.strength_analysis.shadbala_grade}</p>
            <p><strong>Interpretation:</strong> {lordAnalysis.strength_analysis.strength_interpretation}</p>
          </div>
        </div>
        
        <div className="subsection">
          <h5>House Position</h5>
          <div className="analysis-data">
            <p><strong>House:</strong> {lordAnalysis.house_position_analysis.house_number}</p>
            <p><strong>Types:</strong> {lordAnalysis.house_position_analysis.house_types.join(', ') || 'Regular'}</p>
            <p><strong>Strength:</strong> {lordAnalysis.house_position_analysis.house_strength}</p>
            <p><strong>Significance:</strong> {lordAnalysis.house_position_analysis.house_significance}</p>
          </div>
        </div>
        
        <div className="subsection">
          <h5>5-Fold Friendship</h5>
          <div className="analysis-data">
            <p><strong>Sign Lord:</strong> {lordAnalysis.friendship_analysis.sign_lord} ({lordAnalysis.friendship_analysis.sign_friendship})</p>
            <p><strong>Nakshatra:</strong> {lordAnalysis.basic_info.nakshatra}</p>
            <p><strong>Nakshatra Lord:</strong> {lordAnalysis.friendship_analysis.nakshatra_lord} ({lordAnalysis.friendship_analysis.nakshatra_friendship})</p>
            <p><strong>Overall Status:</strong> {lordAnalysis.friendship_analysis.overall_friendship_status}</p>
          </div>
        </div>
        
        <div className="subsection">
          <h5>Conjunctions</h5>
          <div className="analysis-data">
            {lordAnalysis.conjunctions.has_conjunctions ? (
              <div>
                <p><strong>Count:</strong> {lordAnalysis.conjunctions.conjunction_count}</p>
                <p><strong>Overall Effect:</strong> {lordAnalysis.conjunctions.overall_conjunction_effect}</p>
                {lordAnalysis.conjunctions.conjunctions.map((conj, index) => (
                  <div key={index} className="conjunction-item">
                    <strong>{conj.planet}</strong> - {conj.type} ({conj.effect})
                  </div>
                ))}
              </div>
            ) : (
              <p>No conjunctions</p>
            )}
          </div>
        </div>
        
        <div className="subsection">
          <h5>Aspects Received</h5>
          <div className="analysis-data">
            {lordAnalysis.aspects_received.has_aspects ? (
              <div>
                <p><strong>Total Aspects:</strong> {lordAnalysis.aspects_received.aspect_count}</p>
                <p><strong>Benefic Aspects:</strong> {lordAnalysis.aspects_received.benefic_aspects.length}</p>
                <p><strong>Malefic Aspects:</strong> {lordAnalysis.aspects_received.malefic_aspects.length}</p>
                {lordAnalysis.aspects_received.aspects.map((aspect, index) => (
                  <div key={index} className="aspect-item">
                    <div className="aspect-header">
                      <strong>{aspect.aspecting_planet}</strong> - {aspect.aspect_type}
                      <span className={`effect-badge ${aspect.effect.toLowerCase().replace(' ', '-')}`}>
                        {aspect.effect} (Score: {aspect.effect_score})
                      </span>
                    </div>
                    {aspect.calculation_details && (
                      <div className="calculation-breakdown">
                        <h6>How this aspect effect is calculated:</h6>
                        <ul className="calculation-steps">
                          {aspect.calculation_details.map((detail, detailIndex) => (
                            <li key={detailIndex} className="calculation-step">{detail}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p>No aspects received</p>
            )}
          </div>
        </div>
        
        <div className="subsection">
          <h5>Combustion & Retrograde</h5>
          <div className="analysis-data">
            <p><strong>Combustion Status:</strong> {lordAnalysis.combustion_status.status}</p>
            <p><strong>Effect:</strong> {lordAnalysis.combustion_status.effect}</p>
            <p><strong>Retrograde:</strong> {lordAnalysis.retrograde_analysis.is_retrograde ? 'Yes' : 'No'}</p>
            <p><strong>Retrograde Effect:</strong> {lordAnalysis.retrograde_analysis.effect}</p>
          </div>
        </div>
        
        <div className="subsection overall-assessment">
          <h5>Overall Assessment</h5>
          <div className="analysis-data">
            <p><strong>Strength Score:</strong> {lordAnalysis.overall_assessment.overall_strength_score}/100</p>
            <p><strong>Grade:</strong> {lordAnalysis.overall_assessment.overall_grade}</p>
            
            {lordAnalysis.overall_assessment.key_strengths.length > 0 && (
              <div>
                <strong>Key Strengths:</strong>
                <ul>
                  {lordAnalysis.overall_assessment.key_strengths.map((strength, index) => (
                    <li key={index}>{strength}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {lordAnalysis.overall_assessment.key_weaknesses.length > 0 && (
              <div>
                <strong>Key Weaknesses:</strong>
                <ul>
                  {lordAnalysis.overall_assessment.key_weaknesses.map((weakness, index) => (
                    <li key={index}>{weakness}</li>
                  ))}
                </ul>
              </div>
            )}
            
            <div>
              <strong>Recommendations:</strong>
              <ul>
                {lordAnalysis.overall_assessment.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const [expandedSections, setExpandedSections] = useState({});
  const [modalData, setModalData] = useState(null);

  const toggleSection = (sectionId) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
    if (!expandedSections[sectionId]) {
      loadCompleteAnalysisSection(sectionId);
    }
  };

  const openModal = (title, content) => {
    setModalData({ title, content });
  };

  const renderTenthHouseDetails = (sectionKey) => {
    const data = completeAnalysisData['tenth-house'];
    if (!data) return <div>No data available</div>;

    switch (sectionKey) {
      case 'house-sign':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Sign:</span> <span>{data.sign_analysis.sign}</span></div>
            <div className="detail-row"><span>Sign Lord:</span> <span>{data.sign_analysis.sign_lord}</span></div>
            <div className="detail-row"><span>Element:</span> <span>{data.sign_analysis.sign_element}</span></div>
            <div className="detail-row"><span>Quality:</span> <span>{data.sign_analysis.sign_quality}</span></div>
            <div className="detail-row"><span>Career Nature:</span> <span>{data.sign_analysis.career_nature}</span></div>
            <div className="detail-row"><span>Career Approach:</span> <span>{data.sign_analysis.career_approach}</span></div>
          </div>
        );
      case 'planets-in-house':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Planet Count:</span> <span>{data.planets_in_house.planet_count}</span></div>
            <div className="detail-row"><span>Overall Influence:</span> <span>{data.planets_in_house.overall_planetary_influence}</span></div>
            {data.planets_in_house.strongest_planet && (
              <div className="detail-row"><span>Strongest Planet:</span> <span>{data.planets_in_house.strongest_planet.planet} ({data.planets_in_house.strongest_planet.strength.toFixed(1)} rupas)</span></div>
            )}
            {data.planets_in_house.planets.map((planet, index) => (
              <div key={index} className="planet-detail">
                <h4>{planet.planet}</h4>
                <div className="detail-row"><span>Dignity:</span> <span className={planet.dignity === 'exalted' || planet.dignity === 'own_sign' ? 'positive' : planet.dignity === 'debilitated' ? 'negative' : 'neutral'}>{planet.dignity}</span></div>
                <div className="detail-row"><span>Shadbala:</span> <span>{planet.shadbala_rupas.toFixed(1)} rupas</span></div>
                <div className="detail-row"><span>Career Significance:</span> <span>{planet.career_significance}</span></div>
                <div className="detail-row"><span>Overall Effect:</span> <span className={planet.overall_effect === 'Highly beneficial' || planet.overall_effect === 'Beneficial' ? 'positive' : planet.overall_effect === 'Challenging' ? 'negative' : 'neutral'}>{planet.overall_effect}</span></div>
              </div>
            ))}
          </div>
        );
      case 'aspects-on-house':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Total Aspects:</span> <span>{data.aspects_on_house.aspect_count}</span></div>
            <div className="detail-row"><span>Benefic Aspects:</span> <span className="positive">{data.aspects_on_house.benefic_aspects.length}</span></div>
            <div className="detail-row"><span>Malefic Aspects:</span> <span className="negative">{data.aspects_on_house.malefic_aspects.length}</span></div>
            <div className="detail-row"><span>Net Score:</span> <span className={data.aspects_on_house.net_aspect_score > 0 ? 'positive' : data.aspects_on_house.net_aspect_score < 0 ? 'negative' : 'neutral'}>{data.aspects_on_house.net_aspect_score > 0 ? '+' : ''}{data.aspects_on_house.net_aspect_score.toFixed(1)}</span></div>
            <div className="detail-row"><span>Overall Effect:</span> <span>{data.aspects_on_house.overall_aspect_effect}</span></div>
            {data.aspects_on_house.aspects.map((aspect, index) => (
              <div key={index} className="aspect-item">
                <div className="aspect-header">
                  <strong>{aspect.aspecting_planet} - {aspect.aspect_type}</strong>
                  <span className={`effect-badge ${aspect.effect.toLowerCase().replace(' ', '-')}`}>
                    {aspect.effect} (Score: {aspect.effect_score})
                  </span>
                </div>
                {aspect.calculation_details && (
                  <div className="calculation-breakdown">
                    <h6>How this aspect effect is calculated:</h6>
                    <ul className="calculation-steps">
                      {aspect.calculation_details.map((detail, detailIndex) => (
                        <li key={detailIndex} className="calculation-step">{detail}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        );
      case 'house-strength':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Total Score:</span> <span className={data.house_strength.total_score >= 70 ? 'positive' : data.house_strength.total_score <= 40 ? 'negative' : 'neutral'}>{data.house_strength.total_score}/100</span></div>
            <div className="detail-row"><span>Grade:</span> <span className={data.house_strength.grade === 'Excellent' || data.house_strength.grade === 'Very Good' ? 'positive' : data.house_strength.grade === 'Weak' ? 'negative' : 'neutral'}>{data.house_strength.grade}</span></div>
            <div className="detail-row"><span>Sign Lord Strength:</span> <span>{data.house_strength.components.sign_lord_strength}/100</span></div>
            <div className="detail-row"><span>Planets Strength:</span> <span>{data.house_strength.components.planets_strength}/100</span></div>
            <div className="detail-row"><span>Aspects Strength:</span> <span>{data.house_strength.components.aspects_strength}/100</span></div>
            <div className="detail-row"><span>Ashtakavarga Strength:</span> <span>{data.house_strength.components.ashtakavarga_strength}/100</span></div>
            <div className="detail-row"><span>Interpretation:</span> <span>{data.house_strength.interpretation}</span></div>
          </div>
        );
      case 'ashtakavarga':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Total Points:</span> <span className={data.ashtakavarga_points.total_points >= 30 ? 'positive' : data.ashtakavarga_points.total_points <= 25 ? 'negative' : 'neutral'}>{data.ashtakavarga_points.total_points}</span></div>
            <div className="detail-row"><span>Strength Level:</span> <span className={data.ashtakavarga_points.strength_level === 'Strong' ? 'positive' : data.ashtakavarga_points.strength_level === 'Weak' ? 'negative' : 'neutral'}>{data.ashtakavarga_points.strength_level}</span></div>
            <div className="detail-row"><span>Interpretation:</span> <span>{data.ashtakavarga_points.interpretation}</span></div>
          </div>
        );
      case 'house-overall':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Strength Score:</span> <span className={data.overall_assessment.overall_strength_score >= 70 ? 'positive' : data.overall_assessment.overall_strength_score <= 40 ? 'negative' : 'neutral'}>{data.overall_assessment.overall_strength_score}/100</span></div>
            <div className="detail-row"><span>Grade:</span> <span className={data.overall_assessment.overall_grade === 'Excellent' || data.overall_assessment.overall_grade === 'Very Good' ? 'positive' : data.overall_assessment.overall_grade === 'Weak' ? 'negative' : 'neutral'}>{data.overall_assessment.overall_grade}</span></div>
            <div className="detail-row"><span>Career Potential:</span> <span className={data.overall_assessment.career_potential === 'High' ? 'positive' : data.overall_assessment.career_potential === 'Needs attention' ? 'negative' : 'neutral'}>{data.overall_assessment.career_potential}</span></div>
            {data.overall_assessment.key_strengths.length > 0 && (
              <div className="strengths-weaknesses">
                <h4>Key Strengths:</h4>
                {data.overall_assessment.key_strengths.map((strength, index) => <div key={index} className="positive">• {strength}</div>)}
              </div>
            )}
            {data.overall_assessment.key_challenges.length > 0 && (
              <div className="strengths-weaknesses">
                <h4>Key Challenges:</h4>
                {data.overall_assessment.key_challenges.map((challenge, index) => <div key={index} className="negative">• {challenge}</div>)}
              </div>
            )}
            <div className="strengths-weaknesses">
              <h4>Recommendations:</h4>
              {data.overall_assessment.recommendations.map((rec, index) => <div key={index}>• {rec}</div>)}
            </div>
          </div>
        );
      default:
        return <div>Section details not available</div>;
    }
  };

  const renderSaturnSectionDetails = (sectionKey) => {
    const data = completeAnalysisData['saturn-karaka']?.saturn_analysis;
    if (!data) return <div>No data available</div>;

    // Use same logic as renderSectionDetails but for Saturn
    return renderSectionDetailsForPlanet(data, sectionKey);
  };

  const renderSaturnKarmaDetails = () => {
    const data = completeAnalysisData['saturn-karaka'];
    if (!data) return <div>No data available</div>;

    return (
      <div className="section-details">
        <div className="detail-row"><span>Karma Pattern:</span> <span>{data.karma_interpretation.primary_karma_pattern}</span></div>
        <div className="detail-row"><span>Work Dharma:</span> <span>{data.karma_interpretation.work_dharma}</span></div>
        <div className="detail-row"><span>Karmic Strength:</span> <span>{data.karma_interpretation.karmic_strength_level}</span></div>
        
        <h4>Career Timing</h4>
        <div className="detail-row"><span>Maturation:</span> <span>{data.career_karma_insights.career_timing.maturation_age}</span></div>
        <div className="detail-row"><span>Peak Periods:</span> <span>{data.career_karma_insights.career_timing.peak_periods}</span></div>
        <div className="detail-row"><span>Advice:</span> <span>{data.career_karma_insights.career_timing.advice}</span></div>
        
        <h4>Karmic Lessons</h4>
        {data.career_karma_insights.karmic_lessons.map((lesson, index) => (
          <div key={index} className="detail-row"><span>Lesson {index + 1}:</span> <span>{lesson}</span></div>
        ))}
        
        <h4>Remedial Guidance</h4>
        {data.career_karma_insights.remedial_guidance.map((remedy, index) => (
          <div key={index} className="detail-row"><span>Remedy {index + 1}:</span> <span>{remedy}</span></div>
        ))}
      </div>
    );
  };

  const renderSaturnTenthSectionDetails = (sectionKey) => {
    const data = completeAnalysisData['saturn-tenth'];
    if (!data) return <div>No data available</div>;

    switch (sectionKey) {
      case 'saturn-sign':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Saturn Position:</span> <span>H{data.saturn_info.saturn_house} ({data.saturn_info.saturn_sign})</span></div>
            <div className="detail-row"><span>10th from Saturn:</span> <span>H{data.saturn_tenth_house_info.house_number} ({data.saturn_tenth_house_info.house_sign})</span></div>
            <div className="detail-row"><span>House Lord:</span> <span>{data.saturn_tenth_house_info.house_lord}</span></div>
            <div className="detail-row"><span>Element:</span> <span>{data.sign_analysis.sign_element}</span></div>
            <div className="detail-row"><span>Quality:</span> <span>{data.sign_analysis.sign_quality}</span></div>
            <div className="detail-row"><span>Career Nature:</span> <span>{data.sign_analysis.career_nature}</span></div>
            <div className="detail-row"><span>Career Approach:</span> <span>{data.sign_analysis.career_approach}</span></div>
          </div>
        );
      case 'saturn-planets':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Planet Count:</span> <span>{data.planets_in_house.planet_count}</span></div>
            <div className="detail-row"><span>Overall Influence:</span> <span>{data.planets_in_house.overall_planetary_influence}</span></div>
            {data.planets_in_house.strongest_planet && (
              <div className="detail-row"><span>Strongest Planet:</span> <span>{data.planets_in_house.strongest_planet.planet} ({data.planets_in_house.strongest_planet.shadbala_rupas.toFixed(1)} rupas)</span></div>
            )}
            {data.planets_in_house.planets.map((planet, index) => (
              <div key={index} className="planet-detail">
                <h4>{planet.planet}</h4>
                <div className="detail-row"><span>Dignity:</span> <span className={planet.dignity === 'exalted' || planet.dignity === 'own_sign' ? 'positive' : planet.dignity === 'debilitated' ? 'negative' : 'neutral'}>{planet.dignity}</span></div>
                <div className="detail-row"><span>Shadbala:</span> <span>{planet.shadbala_rupas.toFixed(1)} rupas</span></div>
                <div className="detail-row"><span>Career Significance:</span> <span>{planet.career_significance}</span></div>
                <div className="detail-row"><span>Overall Effect:</span> <span className={planet.overall_effect === 'Highly beneficial' || planet.overall_effect === 'Beneficial' ? 'positive' : planet.overall_effect === 'Challenging' ? 'negative' : 'neutral'}>{planet.overall_effect}</span></div>
              </div>
            ))}
          </div>
        );
      case 'saturn-aspects':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Total Aspects:</span> <span>{data.aspects_on_house.aspect_count}</span></div>
            <div className="detail-row"><span>Benefic Aspects:</span> <span className="positive">{data.aspects_on_house.benefic_aspects.length}</span></div>
            <div className="detail-row"><span>Malefic Aspects:</span> <span className="negative">{data.aspects_on_house.malefic_aspects.length}</span></div>
            <div className="detail-row"><span>Net Score:</span> <span className={data.aspects_on_house.net_aspect_score > 0 ? 'positive' : data.aspects_on_house.net_aspect_score < 0 ? 'negative' : 'neutral'}>{data.aspects_on_house.net_aspect_score > 0 ? '+' : ''}{data.aspects_on_house.net_aspect_score.toFixed(1)}</span></div>
            <div className="detail-row"><span>Overall Effect:</span> <span>{data.aspects_on_house.overall_aspect_effect}</span></div>
            {data.aspects_on_house.aspects.map((aspect, index) => (
              <div key={index} className="aspect-item">
                <div className="aspect-header">
                  <strong>{aspect.aspecting_planet} - {aspect.aspect_type}</strong>
                  <span className={`effect-badge ${aspect.effect.toLowerCase().replace(' ', '-')}`}>
                    {aspect.effect} (Score: {aspect.effect_score})
                  </span>
                </div>
                {aspect.calculation_details && (
                  <div className="calculation-breakdown">
                    <h6>Calculation details:</h6>
                    <ul className="calculation-steps">
                      {aspect.calculation_details.map((detail, detailIndex) => (
                        <li key={detailIndex} className="calculation-step">{detail}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        );
      case 'saturn-strength':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Total Score:</span> <span className={data.house_strength.total_score >= 70 ? 'positive' : data.house_strength.total_score <= 40 ? 'negative' : 'neutral'}>{data.house_strength.total_score}/100</span></div>
            <div className="detail-row"><span>Grade:</span> <span className={data.house_strength.grade === 'Excellent' || data.house_strength.grade === 'Very Good' ? 'positive' : data.house_strength.grade === 'Weak' ? 'negative' : 'neutral'}>{data.house_strength.grade}</span></div>
            <div className="detail-row"><span>Sign Lord Strength:</span> <span>{data.house_strength.components.sign_lord_strength}/100</span></div>
            <div className="detail-row"><span>Planets Strength:</span> <span>{data.house_strength.components.planets_strength}/100</span></div>
            <div className="detail-row"><span>Aspects Strength:</span> <span>{data.house_strength.components.aspects_strength}/100</span></div>
            <div className="detail-row"><span>Ashtakavarga Strength:</span> <span>{data.house_strength.components.ashtakavarga_strength}/100</span></div>
            <div className="detail-row"><span>Interpretation:</span> <span>{data.house_strength.interpretation}</span></div>
          </div>
        );
      case 'saturn-ashtakavarga':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Total Points:</span> <span className={data.ashtakavarga_points.total_points >= 30 ? 'positive' : data.ashtakavarga_points.total_points <= 25 ? 'negative' : 'neutral'}>{data.ashtakavarga_points.total_points}</span></div>
            <div className="detail-row"><span>Strength Level:</span> <span className={data.ashtakavarga_points.strength_level === 'Strong' ? 'positive' : data.ashtakavarga_points.strength_level === 'Weak' ? 'negative' : 'neutral'}>{data.ashtakavarga_points.strength_level}</span></div>
            <div className="detail-row"><span>Interpretation:</span> <span>{data.ashtakavarga_points.interpretation}</span></div>
          </div>
        );
      case 'saturn-overall':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Strength Score:</span> <span className={data.overall_assessment.overall_strength_score >= 70 ? 'positive' : data.overall_assessment.overall_strength_score <= 40 ? 'negative' : 'neutral'}>{data.overall_assessment.overall_strength_score}/100</span></div>
            <div className="detail-row"><span>Grade:</span> <span className={data.overall_assessment.overall_grade === 'Excellent' || data.overall_assessment.overall_grade === 'Very Good' ? 'positive' : data.overall_assessment.overall_grade === 'Weak' ? 'negative' : 'neutral'}>{data.overall_assessment.overall_grade}</span></div>
            <div className="detail-row"><span>Career Potential:</span> <span className={data.overall_assessment.career_potential.includes('High') ? 'positive' : data.overall_assessment.career_potential.includes('attention') ? 'negative' : 'neutral'}>{data.overall_assessment.career_potential}</span></div>
            {data.overall_assessment.key_strengths.length > 0 && (
              <div className="strengths-weaknesses">
                <h4>Key Strengths:</h4>
                {data.overall_assessment.key_strengths.map((strength, index) => <div key={index} className="positive">• {strength}</div>)}
              </div>
            )}
            {data.overall_assessment.key_challenges.length > 0 && (
              <div className="strengths-weaknesses">
                <h4>Key Challenges:</h4>
                {data.overall_assessment.key_challenges.map((challenge, index) => <div key={index} className="negative">• {challenge}</div>)}
              </div>
            )}
            <div className="strengths-weaknesses">
              <h4>Recommendations:</h4>
              {data.overall_assessment.recommendations.map((rec, index) => <div key={index}>• {rec}</div>)}
            </div>
          </div>
        );
      default:
        return <div>Section details not available</div>;
    }
  };

  const renderSectionDetailsForPlanet = (data, sectionKey) => {
    // Common section details rendering for any planet analysis
    switch (sectionKey) {
      case 'dignity':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Dignity:</span> <span className={data.dignity_analysis.dignity === 'exalted' || data.dignity_analysis.dignity === 'own_sign' ? 'positive' : data.dignity_analysis.dignity === 'debilitated' ? 'negative' : 'neutral'}>{data.dignity_analysis.dignity}</span></div>
            <div className="detail-row"><span>Functional Nature:</span> <span>{data.dignity_analysis.functional_nature}</span></div>
            <div className="detail-row"><span>Strength Multiplier:</span> <span>{data.dignity_analysis.strength_multiplier}</span></div>
            <div className="detail-row"><span>Description:</span> <span>{typeof data.dignity_analysis.dignity_description === 'object' ? JSON.stringify(data.dignity_analysis.dignity_description) : data.dignity_analysis.dignity_description}</span></div>
            {data.dignity_analysis.states.length > 0 && <div className="detail-row"><span>States:</span> <span>{data.dignity_analysis.states.join(', ')}</span></div>}
          </div>
        );
      case 'strength':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Shadbala Rupas:</span> <span>{data.strength_analysis.shadbala_rupas.toFixed(2)}</span></div>
            <div className="detail-row"><span>Grade:</span> <span className={data.strength_analysis.shadbala_grade === 'Excellent' ? 'positive' : data.strength_analysis.shadbala_grade === 'Weak' ? 'negative' : 'neutral'}>{data.strength_analysis.shadbala_grade}</span></div>
            <div className="detail-row"><span>Interpretation:</span> <span>{typeof data.strength_analysis.strength_interpretation === 'object' ? JSON.stringify(data.strength_analysis.strength_interpretation) : data.strength_analysis.strength_interpretation}</span></div>
          </div>
        );
      case 'house':
        return (
          <div className="section-details">
            <div className="detail-row"><span>House Number:</span> <span>{data.house_position_analysis.house_number}</span></div>
            <div className="detail-row"><span>House Types:</span> <span>{data.house_position_analysis.house_types.join(', ') || 'Regular'}</span></div>
            <div className="detail-row"><span>House Strength:</span> <span>{typeof data.house_position_analysis.house_strength === 'object' ? JSON.stringify(data.house_position_analysis.house_strength) : data.house_position_analysis.house_strength}</span></div>
            <div className="detail-row"><span>Significance:</span> <span>{typeof data.house_position_analysis.house_significance === 'object' ? JSON.stringify(data.house_position_analysis.house_significance) : data.house_position_analysis.house_significance}</span></div>
          </div>
        );
      case 'friendship':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Sign Lord:</span> <span>{data.friendship_analysis.sign_lord} ({data.friendship_analysis.sign_friendship})</span></div>
            <div className="detail-row"><span>Nakshatra:</span> <span>{data.basic_info.nakshatra}</span></div>
            <div className="detail-row"><span>Nakshatra Lord:</span> <span>{data.friendship_analysis.nakshatra_lord} ({data.friendship_analysis.nakshatra_friendship})</span></div>
            <div className="detail-row"><span>Overall Status:</span> <span className={String(data.friendship_analysis.overall_friendship_status).includes('Favorable') ? 'positive' : String(data.friendship_analysis.overall_friendship_status).includes('Unfavorable') ? 'negative' : 'neutral'}>{typeof data.friendship_analysis.overall_friendship_status === 'object' ? JSON.stringify(data.friendship_analysis.overall_friendship_status) : data.friendship_analysis.overall_friendship_status}</span></div>
          </div>
        );
      case 'conjunctions':
        return (
          <div className="section-details">
            {data.conjunctions.has_conjunctions ? (
              <div>
                <div className="detail-row"><span>Count:</span> <span>{data.conjunctions.conjunction_count}</span></div>
                <div className="detail-row"><span>Overall Effect:</span> <span className={data.conjunctions.overall_conjunction_effect === 'beneficial' ? 'positive' : data.conjunctions.overall_conjunction_effect === 'harmful' ? 'negative' : 'neutral'}>{data.conjunctions.overall_conjunction_effect}</span></div>
                {data.conjunctions.conjunctions.map((conj, index) => (
                  <div key={index} className="detail-row"><span>{conj.planet}:</span> <span>{conj.type} - {conj.effect}</span></div>
                ))}
              </div>
            ) : (
              <div className="detail-row"><span>Status:</span> <span>No conjunctions</span></div>
            )}
          </div>
        );
      case 'aspects':
        return (
          <div className="section-details">
            {data.aspects_received.has_aspects ? (
              <div>
                <div className="detail-row"><span>Total Aspects:</span> <span>{data.aspects_received.aspect_count}</span></div>
                <div className="detail-row"><span>Benefic Aspects:</span> <span className="positive">{data.aspects_received.benefic_aspects.length}</span></div>
                <div className="detail-row"><span>Malefic Aspects:</span> <span className="negative">{data.aspects_received.malefic_aspects.length}</span></div>
                {data.aspects_received.aspects.map((aspect, index) => (
                  <div key={index} className="aspect-item">
                    <div className="aspect-header">
                      <strong>{aspect.aspecting_planet} - {aspect.aspect_type}</strong>
                      <span className={`effect-badge ${aspect.effect.toLowerCase().replace(' ', '-')}`}>
                        {aspect.effect} (Score: {aspect.effect_score})
                      </span>
                    </div>
                    {aspect.calculation_details && (
                      <div className="calculation-breakdown">
                        <h6>How this aspect effect is calculated:</h6>
                        <ul className="calculation-steps">
                          {aspect.calculation_details.map((detail, detailIndex) => (
                            <li key={detailIndex} className="calculation-step">{detail}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="detail-row"><span>Status:</span> <span>No aspects received</span></div>
            )}
          </div>
        );
      case 'overall':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Strength Score:</span> <span className={data.overall_assessment.overall_strength_score >= 70 ? 'positive' : data.overall_assessment.overall_strength_score <= 40 ? 'negative' : 'neutral'}>{data.overall_assessment.overall_strength_score}/100</span></div>
            <div className="detail-row"><span>Grade:</span> <span className={data.overall_assessment.overall_grade === 'Excellent' || data.overall_assessment.overall_grade === 'Very Good' ? 'positive' : data.overall_assessment.overall_grade === 'Weak' ? 'negative' : 'neutral'}>{data.overall_assessment.overall_grade}</span></div>
            {data.overall_assessment.key_strengths.length > 0 && (
              <div className="strengths-weaknesses">
                <h4>Key Strengths:</h4>
                {data.overall_assessment.key_strengths.map((strength, index) => <div key={index} className="positive">• {strength}</div>)}
              </div>
            )}
            {data.overall_assessment.key_weaknesses.length > 0 && (
              <div className="strengths-weaknesses">
                <h4>Key Weaknesses:</h4>
                {data.overall_assessment.key_weaknesses.map((weakness, index) => <div key={index} className="negative">• {weakness}</div>)}
              </div>
            )}
            <div className="strengths-weaknesses">
              <h4>Recommendations:</h4>
              {data.overall_assessment.recommendations.map((rec, index) => <div key={index}>• {rec}</div>)}
            </div>
          </div>
        );
      default:
        return <div>Section details not available</div>;
    }
  };

  const renderSectionDetails = (sectionKey) => {
    const data = completeAnalysisData['tenth-lord']?.lord_analysis;
    if (!data) return <div>No data available</div>;
    
    return renderSectionDetailsForPlanet(data, sectionKey);

    switch (sectionKey) {
      case 'dignity':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Dignity:</span> <span className={data.dignity_analysis.dignity === 'exalted' || data.dignity_analysis.dignity === 'own_sign' ? 'positive' : data.dignity_analysis.dignity === 'debilitated' ? 'negative' : 'neutral'}>{data.dignity_analysis.dignity}</span></div>
            <div className="detail-row"><span>Functional Nature:</span> <span>{data.dignity_analysis.functional_nature}</span></div>
            <div className="detail-row"><span>Strength Multiplier:</span> <span>{data.dignity_analysis.strength_multiplier}</span></div>
            <div className="detail-row"><span>Description:</span> <span>{data.dignity_analysis.dignity_description}</span></div>
            {data.dignity_analysis.states.length > 0 && <div className="detail-row"><span>States:</span> <span>{data.dignity_analysis.states.join(', ')}</span></div>}
          </div>
        );
      case 'strength':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Shadbala Rupas:</span> <span>{data.strength_analysis.shadbala_rupas.toFixed(2)}</span></div>
            <div className="detail-row"><span>Grade:</span> <span className={data.strength_analysis.shadbala_grade === 'Excellent' ? 'positive' : data.strength_analysis.shadbala_grade === 'Weak' ? 'negative' : 'neutral'}>{data.strength_analysis.shadbala_grade}</span></div>
            <div className="detail-row"><span>Interpretation:</span> <span>{data.strength_analysis.strength_interpretation}</span></div>
          </div>
        );
      case 'house':
        return (
          <div className="section-details">
            <div className="detail-row"><span>House Number:</span> <span>{data.house_position_analysis.house_number}</span></div>
            <div className="detail-row"><span>House Types:</span> <span>{data.house_position_analysis.house_types.join(', ') || 'Regular'}</span></div>
            <div className="detail-row"><span>House Strength:</span> <span>{data.house_position_analysis.house_strength}</span></div>
            <div className="detail-row"><span>Significance:</span> <span>{data.house_position_analysis.house_significance}</span></div>
          </div>
        );
      case 'friendship':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Sign Lord:</span> <span>{data.friendship_analysis.sign_lord} ({data.friendship_analysis.sign_friendship})</span></div>
            <div className="detail-row"><span>Nakshatra:</span> <span>{data.basic_info.nakshatra}</span></div>
            <div className="detail-row"><span>Nakshatra Lord:</span> <span>{data.friendship_analysis.nakshatra_lord} ({data.friendship_analysis.nakshatra_friendship})</span></div>
            <div className="detail-row"><span>Overall Status:</span> <span className={data.friendship_analysis.overall_friendship_status.includes('Favorable') ? 'positive' : data.friendship_analysis.overall_friendship_status.includes('Unfavorable') ? 'negative' : 'neutral'}>{data.friendship_analysis.overall_friendship_status}</span></div>
          </div>
        );
      case 'conjunctions':
        return (
          <div className="section-details">
            {data.conjunctions.has_conjunctions ? (
              <div>
                <div className="detail-row"><span>Count:</span> <span>{data.conjunctions.conjunction_count}</span></div>
                <div className="detail-row"><span>Overall Effect:</span> <span className={data.conjunctions.overall_conjunction_effect === 'beneficial' ? 'positive' : data.conjunctions.overall_conjunction_effect === 'harmful' ? 'negative' : 'neutral'}>{data.conjunctions.overall_conjunction_effect}</span></div>
                {data.conjunctions.conjunctions.map((conj, index) => (
                  <div key={index} className="detail-row"><span>{conj.planet}:</span> <span>{conj.type} - {conj.effect}</span></div>
                ))}
              </div>
            ) : (
              <div className="detail-row"><span>Status:</span> <span>No conjunctions</span></div>
            )}
          </div>
        );
      case 'aspects':
        return (
          <div className="section-details">
            {data.aspects_received.has_aspects ? (
              <div>
                <div className="detail-row"><span>Total Aspects:</span> <span>{data.aspects_received.aspect_count}</span></div>
                <div className="detail-row"><span>Benefic Aspects:</span> <span className="positive">{data.aspects_received.benefic_aspects.length}</span></div>
                <div className="detail-row"><span>Malefic Aspects:</span> <span className="negative">{data.aspects_received.malefic_aspects.length}</span></div>
                {data.aspects_received.aspects.map((aspect, index) => (
                  <div key={index} className="aspect-item">
                    <div className="aspect-header">
                      <strong>{aspect.aspecting_planet} - {aspect.aspect_type}</strong>
                      <span className={`effect-badge ${aspect.effect.toLowerCase().replace(' ', '-')}`}>
                        {aspect.effect} (Score: {aspect.effect_score})
                      </span>
                    </div>
                    {aspect.calculation_details && (
                      <div className="calculation-breakdown">
                        <h6>How this aspect effect is calculated:</h6>
                        <ul className="calculation-steps">
                          {aspect.calculation_details.map((detail, detailIndex) => (
                            <li key={detailIndex} className="calculation-step">{detail}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="detail-row"><span>Status:</span> <span>No aspects received</span></div>
            )}
          </div>
        );
      case 'combustion':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Status:</span> <span className={data.combustion_status.is_cazimi ? 'positive' : data.combustion_status.is_combust ? 'negative' : 'neutral'}>{data.combustion_status.status}</span></div>
            <div className="detail-row"><span>Effect:</span> <span>{data.combustion_status.effect}</span></div>
            <div className="detail-row"><span>Retrograde:</span> <span>{data.retrograde_analysis.is_retrograde ? 'Yes' : 'No'}</span></div>
            <div className="detail-row"><span>Retrograde Effect:</span> <span>{data.retrograde_analysis.effect}</span></div>
          </div>
        );
      case 'overall':
        return (
          <div className="section-details">
            <div className="detail-row"><span>Strength Score:</span> <span className={data.overall_assessment.overall_strength_score >= 70 ? 'positive' : data.overall_assessment.overall_strength_score <= 40 ? 'negative' : 'neutral'}>{data.overall_assessment.overall_strength_score}/100</span></div>
            <div className="detail-row"><span>Grade:</span> <span className={data.overall_assessment.overall_grade === 'Excellent' || data.overall_assessment.overall_grade === 'Very Good' ? 'positive' : data.overall_assessment.overall_grade === 'Weak' ? 'negative' : 'neutral'}>{data.overall_assessment.overall_grade}</span></div>
            {data.overall_assessment.key_strengths.length > 0 && (
              <div className="strengths-weaknesses">
                <h4>Key Strengths:</h4>
                {data.overall_assessment.key_strengths.map((strength, index) => <div key={index} className="positive">• {strength}</div>)}
              </div>
            )}
            {data.overall_assessment.key_weaknesses.length > 0 && (
              <div className="strengths-weaknesses">
                <h4>Key Weaknesses:</h4>
                {data.overall_assessment.key_weaknesses.map((weakness, index) => <div key={index} className="negative">• {weakness}</div>)}
              </div>
            )}
            <div className="strengths-weaknesses">
              <h4>Recommendations:</h4>
              {data.overall_assessment.recommendations.map((rec, index) => <div key={index}>• {rec}</div>)}
            </div>
          </div>
        );
      default:
        return <div>Section details not available</div>;
    }
  };

  const closeModal = () => {
    setModalData(null);
  };

  const renderCalculationDetails = (analysisType, calculationType) => {
    const data = completeAnalysisData[analysisType];
    if (!data) return <div>No calculation data available</div>;

    if (analysisType === 'tenth-lord') {
      const lordData = data.lord_analysis;
      if (calculationType === 'grade' || calculationType === 'score') {
        return (
          <div className="calculation-details">
            <h4>Overall Assessment Calculation</h4>
            <div className="calc-breakdown">
              <div className="calc-step">
                <span>Base Strength Score:</span>
                <span>{lordData.overall_assessment.overall_strength_score}/100</span>
              </div>
              <div className="calc-step">
                <span>Grade Assignment:</span>
                <span>{lordData.overall_assessment.overall_grade}</span>
              </div>
              <div className="calc-components">
                <h5>Score Components:</h5>
                <ul>
                  <li>Dignity Analysis: {lordData.dignity_analysis.strength_multiplier}x multiplier</li>
                  <li>Shadbala Strength: {lordData.strength_analysis.shadbala_rupas.toFixed(2)} rupas</li>
                  <li>House Position: {lordData.house_position_analysis.house_types.join(', ') || 'Regular'}</li>
                  <li>Friendship Status: {lordData.friendship_analysis.overall_friendship_status}</li>
                  <li>Conjunctions: {lordData.conjunctions.has_conjunctions ? lordData.conjunctions.overall_conjunction_effect : 'None'}</li>
                  <li>Aspects: {lordData.aspects_received.has_aspects ? `${lordData.aspects_received.aspect_count} aspects` : 'None'}</li>
                </ul>
              </div>
            </div>
          </div>
        );
      }
    } else if (analysisType === 'tenth-house') {
      if (calculationType === 'grade' || calculationType === 'strength') {
        return (
          <div className="calculation-details">
            <h4>10th House Strength Calculation</h4>
            <div className="calc-breakdown">
              <div className="calc-step">
                <span>Total Score:</span>
                <span>{data.overall_assessment.overall_strength_score}/100</span>
              </div>
              <div className="calc-step">
                <span>Grade:</span>
                <span>{data.overall_assessment.overall_grade}</span>
              </div>
              <div className="calc-components">
                <h5>Strength Components:</h5>
                <ul>
                  <li>Sign Lord Strength: {data.house_strength.components.sign_lord_strength}/100</li>
                  <li>Planets Strength: {data.house_strength.components.planets_strength}/100</li>
                  <li>Aspects Strength: {data.house_strength.components.aspects_strength}/100</li>
                  <li>Ashtakavarga Points: {data.ashtakavarga_points.total_points} points</li>
                </ul>
              </div>
            </div>
          </div>
        );
      }
    } else if (analysisType === 'saturn-karaka') {
      const saturnData = data.saturn_analysis;
      if (calculationType === 'grade' || calculationType === 'score') {
        return (
          <div className="calculation-details">
            <h4>Saturn Karma Karaka Assessment</h4>
            <div className="calc-breakdown">
              <div className="calc-step">
                <span>Strength Score:</span>
                <span>{saturnData.overall_assessment.overall_strength_score}/100</span>
              </div>
              <div className="calc-step">
                <span>Grade:</span>
                <span>{saturnData.overall_assessment.overall_grade}</span>
              </div>
              <div className="calc-components">
                <h5>Assessment Components:</h5>
                <ul>
                  <li>Dignity: {saturnData.dignity_analysis.dignity} ({saturnData.dignity_analysis.strength_multiplier}x)</li>
                  <li>Shadbala: {saturnData.strength_analysis.shadbala_rupas.toFixed(2)} rupas</li>
                  <li>House Position: H{saturnData.house_position_analysis.house_number}</li>
                  <li>Karmic Strength: {data.karma_interpretation.karmic_strength_level}</li>
                </ul>
              </div>
            </div>
          </div>
        );
      }
    } else if (analysisType === 'saturn-tenth') {
      if (calculationType === 'grade' || calculationType === 'strength') {
        return (
          <div className="calculation-details">
            <h4>10th from Saturn Strength Calculation</h4>
            <div className="calc-breakdown">
              <div className="calc-step">
                <span>Total Score:</span>
                <span>{data.overall_assessment.overall_strength_score}/100</span>
              </div>
              <div className="calc-step">
                <span>Grade:</span>
                <span>{data.overall_assessment.overall_grade}</span>
              </div>
              <div className="calc-components">
                <h5>Strength Components:</h5>
                <ul>
                  <li>Sign Lord Strength: {data.house_strength.components.sign_lord_strength}/100</li>
                  <li>Planets Strength: {data.house_strength.components.planets_strength}/100</li>
                  <li>Aspects Strength: {data.house_strength.components.aspects_strength}/100</li>
                  <li>Ashtakavarga Points: {data.ashtakavarga_points.total_points} points</li>
                </ul>
                <h5>Saturn's Perspective:</h5>
                <ul>
                  <li>Saturn in H{data.saturn_info.saturn_house} ({data.saturn_info.saturn_sign})</li>
                  <li>10th from Saturn: H{data.saturn_tenth_house_info.house_number} ({data.saturn_tenth_house_info.house_sign})</li>
                  <li>House Lord: {data.saturn_tenth_house_info.house_lord}</li>
                  <li>Career Potential: {data.overall_assessment.career_potential}</li>
                </ul>
                <h5>Calculation Method:</h5>
                <ul>
                  <li>Weighted Average: Sign Lord (30%) + Planets (30%) + Aspects (20%) + Ashtakavarga (20%)</li>
                  <li>Final Score: {data.house_strength.components.sign_lord_strength}×0.3 + {data.house_strength.components.planets_strength}×0.3 + {data.house_strength.components.aspects_strength}×0.2 + {data.house_strength.components.ashtakavarga_strength}×0.2 = {data.overall_assessment.overall_strength_score.toFixed(1)}</li>
                  <li>This represents Saturn's disciplined view of career potential through the 10th house from its position</li>
                </ul>
              </div>
            </div>
          </div>
        );
      }
    }

    return <div>Calculation details not available for this item</div>;
  };



  const renderCompleteAnalysis = () => {
    const sections = [
      {
        id: 'tenth-lord',
        icon: '🏠',
        title: '10th House Lord',
        status: 'active',
        summary: completeAnalysisData['tenth-lord'] ? 
          `${completeAnalysisData['tenth-lord'].tenth_house_info.house_lord} - ${completeAnalysisData['tenth-lord'].lord_analysis.overall_assessment.overall_grade}` : 
          'Click to analyze',
        color: '#4CAF50'
      },
      { id: 'tenth-house', icon: '🏢', title: '10th House Analysis', status: 'active', summary: completeAnalysisData['tenth-house'] ? 
        `${completeAnalysisData['tenth-house'].house_sign} - ${completeAnalysisData['tenth-house'].strength}` : 
        'Click to analyze', color: '#2196F3' },
      { id: 'd10-analysis', icon: '📋', title: 'D10 Dasamsa', status: 'active', summary: 'Career divisional chart', color: '#FF9800' },
      { id: 'saturn-karaka', icon: '⚙️', title: 'Saturn Karma Karaka', status: 'active', summary: 'Natural career significator', color: '#9C27B0' },
      { id: 'saturn-tenth', icon: '🧮', title: '10th from Saturn', status: 'active', summary: 'Career from Saturn perspective', color: '#607D8B' },
      { id: 'amatyakaraka', icon: '👑', title: 'Amatyakaraka', status: 'active', summary: 'Jaimini professional significator', color: '#E91E63' },
      { id: 'career-yogas', icon: '✨', title: 'Success Yogas', status: 'active', summary: 'Raj & Dhana yogas', color: '#FFC107' },
      { id: 'timing', icon: '⏰', title: 'Career Timing', status: 'pending', summary: 'Dasha & transit analysis', color: '#FF5722' }
    ];

    return (
      <div className="complete-analysis-modern">
        <div className="analysis-header">
          <h3>🔍 Complete Career Analysis</h3>
          <p>360-degree Vedic career analysis with detailed calculations</p>
        </div>
        
        <div className="analysis-grid">
          {sections.map((section) => (
            <div key={section.id} className={`analysis-card ${section.status}`}>
              <div className="card-header" onClick={() => toggleSection(section.id)}>
                <div className="card-icon" style={{ backgroundColor: section.color }}>
                  {section.icon}
                </div>
                <div className="card-info">
                  <h4>{section.title}</h4>
                  <p>{section.summary}</p>
                </div>
                <div className="card-status">
                  {completeAnalysisLoading[section.id] ? (
                    <div className="mini-spinner"></div>
                  ) : (
                    <span className={`expand-icon ${expandedSections[section.id] ? 'expanded' : ''}`}>▼</span>
                  )}
                </div>
              </div>
              
              {expandedSections[section.id] && (
                <div className="card-content">
                  {(section.id === 'tenth-lord' && completeAnalysisData['tenth-lord']) ? (
                    <div className="analysis-summary">
                      <div className="summary-grid">
                        {[
                          { label: 'Lord', value: completeAnalysisData['tenth-lord'].tenth_house_info.house_lord, type: 'neutral' },
                          { label: 'Grade', value: completeAnalysisData['tenth-lord'].lord_analysis.overall_assessment.overall_grade, type: completeAnalysisData['tenth-lord'].lord_analysis.overall_assessment.overall_grade === 'Excellent' || completeAnalysisData['tenth-lord'].lord_analysis.overall_assessment.overall_grade === 'Very Good' ? 'positive' : completeAnalysisData['tenth-lord'].lord_analysis.overall_assessment.overall_grade === 'Weak' ? 'negative' : 'neutral' },
                          { label: 'Score', value: `${Math.round(completeAnalysisData['tenth-lord'].lord_analysis.overall_assessment.overall_strength_score)}/100`, type: completeAnalysisData['tenth-lord'].lord_analysis.overall_assessment.overall_strength_score >= 70 ? 'positive' : completeAnalysisData['tenth-lord'].lord_analysis.overall_assessment.overall_strength_score <= 40 ? 'negative' : 'neutral' },
                          { label: 'Dignity', value: completeAnalysisData['tenth-lord'].lord_analysis.dignity_analysis.dignity, type: completeAnalysisData['tenth-lord'].lord_analysis.dignity_analysis.dignity === 'exalted' || completeAnalysisData['tenth-lord'].lord_analysis.dignity_analysis.dignity === 'own_sign' ? 'positive' : completeAnalysisData['tenth-lord'].lord_analysis.dignity_analysis.dignity === 'debilitated' ? 'negative' : 'neutral' },
                          { label: 'House', value: `${completeAnalysisData['tenth-lord'].lord_analysis.house_position_analysis.house_number} (${completeAnalysisData['tenth-lord'].lord_analysis.house_position_analysis.house_types.join(', ') || 'Regular'})`, type: completeAnalysisData['tenth-lord'].lord_analysis.house_position_analysis.house_types.includes('Kendra') || completeAnalysisData['tenth-lord'].lord_analysis.house_position_analysis.house_types.includes('Trikona') ? 'positive' : completeAnalysisData['tenth-lord'].lord_analysis.house_position_analysis.house_types.includes('Dusthana') ? 'negative' : 'neutral' },
                          { label: 'Friendship', value: completeAnalysisData['tenth-lord'].lord_analysis.friendship_analysis.overall_friendship_status, type: completeAnalysisData['tenth-lord'].lord_analysis.friendship_analysis.overall_friendship_status.includes('Favorable') ? 'positive' : completeAnalysisData['tenth-lord'].lord_analysis.friendship_analysis.overall_friendship_status.includes('Unfavorable') ? 'negative' : 'neutral' },
                          { label: 'Conjunctions', value: completeAnalysisData['tenth-lord'].lord_analysis.conjunctions.has_conjunctions ? `${completeAnalysisData['tenth-lord'].lord_analysis.conjunctions.conjunction_count} (${completeAnalysisData['tenth-lord'].lord_analysis.conjunctions.overall_conjunction_effect})` : 'None', type: completeAnalysisData['tenth-lord'].lord_analysis.conjunctions.overall_conjunction_effect === 'beneficial' ? 'positive' : completeAnalysisData['tenth-lord'].lord_analysis.conjunctions.overall_conjunction_effect === 'harmful' ? 'negative' : 'neutral' },
                          { label: 'Aspects', value: completeAnalysisData['tenth-lord'].lord_analysis.aspects_received.has_aspects ? (() => {
                            const aspects = completeAnalysisData['tenth-lord'].lord_analysis.aspects_received.aspects;
                            const totalScore = aspects.reduce((sum, aspect) => sum + (aspect.effect_score || 0), 0);
                            const avgScore = aspects.length > 0 ? (totalScore / aspects.length).toFixed(1) : 0;
                            return `${completeAnalysisData['tenth-lord'].lord_analysis.aspects_received.benefic_aspects.length}B/${completeAnalysisData['tenth-lord'].lord_analysis.aspects_received.malefic_aspects.length}M (${avgScore > 0 ? '+' : ''}${avgScore})`;
                          })() : 'None', type: completeAnalysisData['tenth-lord'].lord_analysis.aspects_received.has_aspects ? (() => {
                            const aspects = completeAnalysisData['tenth-lord'].lord_analysis.aspects_received.aspects;
                            const totalScore = aspects.reduce((sum, aspect) => sum + (aspect.effect_score || 0), 0);
                            const avgScore = aspects.length > 0 ? totalScore / aspects.length : 0;
                            return avgScore > 1 ? 'positive' : avgScore < -1 ? 'negative' : 'neutral';
                          })() : 'neutral' },
                          { label: 'Yogi Status', value: completeAnalysisData['tenth-lord'].yogi_significance ? (completeAnalysisData['tenth-lord'].yogi_significance.lord_significance.has_impact ? completeAnalysisData['tenth-lord'].yogi_significance.lord_significance.special_status.replace('_', ' ').toUpperCase() : 'Neutral') : 'N/A', type: completeAnalysisData['tenth-lord'].yogi_significance ? (completeAnalysisData['tenth-lord'].yogi_significance.lord_significance.special_status === 'yogi_lord' ? 'positive' : completeAnalysisData['tenth-lord'].yogi_significance.lord_significance.special_status === 'avayogi_lord' || completeAnalysisData['tenth-lord'].yogi_significance.lord_significance.special_status === 'dagdha_lord' ? 'negative' : 'neutral') : 'neutral' },
                          { label: 'Badhaka Status', value: completeAnalysisData['tenth-lord'].badhaka_impact ? (completeAnalysisData['tenth-lord'].badhaka_impact.lord_impact.has_impact ? (completeAnalysisData['tenth-lord'].badhaka_impact.lord_impact.is_badhaka_lord ? 'IS Badhaka Lord' : 'Affected by Badhaka') : 'No Impact') : 'N/A', type: completeAnalysisData['tenth-lord'].badhaka_impact ? (completeAnalysisData['tenth-lord'].badhaka_impact.lord_impact.has_impact ? 'negative' : 'positive') : 'neutral' }
                        ].map((item, index) => (
                          <div key={index} className="summary-item">
                            <span className="item-label">{item.label}</span>
                            {(item.label === 'Grade' || item.label === 'Score') ? (
                              <span 
                                className={`item-value ${item.type} clickable`}
                                onClick={() => openModal(
                                  `${item.label} Calculation - ${completeAnalysisData['tenth-lord'].tenth_house_info.house_lord}`,
                                  renderCalculationDetails('tenth-lord', item.label.toLowerCase())
                                )}
                              >
                                {item.value}
                              </span>
                            ) : (
                              <span className={`item-value ${item.type}`}>{item.value}</span>
                            )}
                          </div>
                        ))}
                      </div>
                      <div className="analysis-sections-grid">
                        {[
                          { key: 'dignity', title: 'Dignity Analysis', icon: '👑' },
                          { key: 'strength', title: 'Shadbala Strength', icon: '💪' },
                          { key: 'house', title: 'House Position', icon: '🏠' },
                          { key: 'friendship', title: '5-Fold Friendship', icon: '🤝' },
                          { key: 'conjunctions', title: 'Conjunctions', icon: '🔗' },
                          { key: 'aspects', title: 'Aspects Received', icon: '👁️' },
                          { key: 'yogi-analysis', title: 'Yogi Points', icon: '🌟' },
                          { key: 'badhaka-analysis', title: 'Badhaka Impact', icon: '⚠️' },
                          { key: 'overall', title: 'Overall Assessment', icon: '📊' }
                        ].map((section) => {
                          const data = completeAnalysisData['tenth-lord'].lord_analysis;
                          let status = 'neutral';
                          let score = '';
                          
                          if (section.key === 'dignity') {
                            const dignity = data.dignity_analysis.dignity;
                            status = dignity === 'exalted' || dignity === 'own_sign' ? 'positive' : dignity === 'debilitated' ? 'negative' : 'neutral';
                            score = `${data.dignity_analysis.strength_multiplier}x`;
                          } else if (section.key === 'strength') {
                            const rupas = data.strength_analysis.shadbala_rupas;
                            status = rupas >= 6 ? 'positive' : rupas <= 3 ? 'negative' : 'neutral';
                            score = `${rupas.toFixed(1)}`;
                          } else if (section.key === 'house') {
                            const types = data.house_position_analysis.house_types;
                            status = types.includes('Kendra') || types.includes('Trikona') ? 'positive' : types.includes('Dusthana') ? 'negative' : 'neutral';
                            score = `H${data.house_position_analysis.house_number}`;
                          } else if (section.key === 'friendship') {
                            const friendship = data.friendship_analysis.overall_friendship_status;
                            status = friendship.includes('Favorable') ? 'positive' : friendship.includes('Unfavorable') ? 'negative' : 'neutral';
                            score = friendship.includes('Favorable') ? '+' : friendship.includes('Unfavorable') ? '-' : '~';
                          } else if (section.key === 'conjunctions') {
                            const effect = data.conjunctions.overall_conjunction_effect;
                            status = effect === 'beneficial' ? 'positive' : effect === 'harmful' ? 'negative' : 'neutral';
                            score = data.conjunctions.has_conjunctions ? `${data.conjunctions.conjunction_count}` : '0';
                          } else if (section.key === 'aspects') {
                            const aspects = data.aspects_received.aspects;
                            const totalScore = aspects.reduce((sum, aspect) => sum + (aspect.effect_score || 0), 0);
                            const avgScore = aspects.length > 0 ? totalScore / aspects.length : 0;
                            status = avgScore > 1 ? 'positive' : avgScore < -1 ? 'negative' : 'neutral';
                            score = aspects.length > 0 ? `${avgScore > 0 ? '+' : ''}${avgScore.toFixed(1)}` : '0';
                          } else if (section.key === 'yogi-analysis') {
                            const yogiData = completeAnalysisData['tenth-lord'].yogi_significance;
                            if (yogiData && yogiData.lord_significance.has_impact) {
                              const specialStatus = yogiData.lord_significance.special_status;
                              status = specialStatus === 'yogi_lord' ? 'positive' : specialStatus === 'avayogi_lord' || specialStatus === 'dagdha_lord' ? 'negative' : 'neutral';
                              score = specialStatus === 'yogi_lord' ? 'Y+' : specialStatus === 'avayogi_lord' ? 'A-' : specialStatus === 'dagdha_lord' ? 'D-' : specialStatus === 'tithi_shunya_lord' ? 'T~' : '~';
                            } else {
                              status = 'neutral';
                              score = '~';
                            }
                          } else if (section.key === 'badhaka-analysis') {
                            const badhakaData = completeAnalysisData['tenth-lord'].badhaka_impact;
                            if (badhakaData && badhakaData.lord_impact.has_impact) {
                              status = 'negative';
                              score = badhakaData.lord_impact.is_badhaka_lord ? 'BL' : 'B-';
                            } else {
                              status = 'positive';
                              score = '✓';
                            }
                          } else if (section.key === 'overall') {
                            const overallScore = data.overall_assessment.overall_strength_score;
                            status = overallScore >= 70 ? 'positive' : overallScore <= 40 ? 'negative' : 'neutral';
                            score = `${Math.round(overallScore)}`;
                          }
                          
                          return (
                            <button 
                              key={section.key}
                              className={`section-btn section-btn-${status}`}
                              onClick={() => openModal(`${section.title} - ${completeAnalysisData['tenth-lord'].tenth_house_info.house_lord}`, section.key === 'yogi-analysis' ? renderYogiBadhakaDetails('tenth-lord', 'yogi', completeAnalysisData) : section.key === 'badhaka-analysis' ? renderYogiBadhakaDetails('tenth-lord', 'badhaka', completeAnalysisData) : renderSectionDetails(section.key))}
                            >
                              <span className="section-icon">{section.icon}</span>
                              <span className="section-title">{section.title}</span>
                              <span className="section-score">{score}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ) : (section.id === 'tenth-house' && completeAnalysisData['tenth-house']) ? (
                    <div className="analysis-summary">
                      <div className="summary-grid">
                        {[
                          { label: 'House Sign', value: completeAnalysisData['tenth-house'].house_sign, type: 'neutral' },
                          { label: 'Grade', value: completeAnalysisData['tenth-house'].strength, type: completeAnalysisData['tenth-house'].strength === 'A+' || completeAnalysisData['tenth-house'].strength === 'A' ? 'positive' : completeAnalysisData['tenth-house'].strength === 'F' ? 'negative' : 'neutral' },
                          { label: 'Strength', value: `${Math.round(completeAnalysisData['tenth-house'].strength_details.enhanced_strength)}/100`, type: completeAnalysisData['tenth-house'].strength_details.enhanced_strength >= 70 ? 'positive' : completeAnalysisData['tenth-house'].strength_details.enhanced_strength <= 40 ? 'negative' : 'neutral' },
                          { label: 'Planets', value: `${completeAnalysisData['tenth-house'].planets_in_house.length} planet(s)`, type: completeAnalysisData['tenth-house'].planets_in_house.length > 0 ? 'positive' : 'neutral' },
                          { label: 'Aspects', value: `${completeAnalysisData['tenth-house'].aspects.length} aspect(s)`, type: completeAnalysisData['tenth-house'].aspects.length > 0 ? 'positive' : 'neutral' },
                          { label: 'Ashtakavarga', value: 'N/A', type: 'neutral' },
                          { label: 'Yogi Impact', value: completeAnalysisData['tenth-house'].yogi_analysis ? `${Math.round(completeAnalysisData['tenth-house'].yogi_analysis.career_impact.total_impact)}%` : 'N/A', type: completeAnalysisData['tenth-house'].yogi_analysis && completeAnalysisData['tenth-house'].yogi_analysis.career_impact.total_impact > 70 ? 'positive' : completeAnalysisData['tenth-house'].yogi_analysis && completeAnalysisData['tenth-house'].yogi_analysis.career_impact.total_impact < 40 ? 'negative' : 'neutral' },
                          { label: 'Badhaka Impact', value: completeAnalysisData['tenth-house'].badhaka_analysis ? (completeAnalysisData['tenth-house'].badhaka_analysis.career_impact.has_impact ? `${Math.round(completeAnalysisData['tenth-house'].badhaka_analysis.career_impact.impact_score)}%` : 'None') : 'N/A', type: completeAnalysisData['tenth-house'].badhaka_analysis && completeAnalysisData['tenth-house'].badhaka_analysis.career_impact.has_impact && completeAnalysisData['tenth-house'].badhaka_analysis.career_impact.impact_score > 50 ? 'negative' : 'positive' }
                        ].map((item, index) => (
                          <div key={index} className="summary-item">
                            <span className="item-label">{item.label}</span>
                            {(item.label === 'Grade' || item.label === 'Strength') ? (
                              <span 
                                className={`item-value ${item.type} clickable`}
                                onClick={() => openModal(
                                  `${item.label} Calculation - 10th House`,
                                  renderCalculationDetails('tenth-house', item.label.toLowerCase())
                                )}
                              >
                                {item.value}
                              </span>
                            ) : (
                              <span className={`item-value ${item.type}`}>{item.value}</span>
                            )}
                          </div>
                        ))}
                      </div>
                      <div className="analysis-sections-grid">
                        {[
                          { key: 'house-sign', title: 'House Sign Analysis', icon: '🏠' },
                          { key: 'planets-in-house', title: 'Planets in House', icon: '🌟' },
                          { key: 'aspects-on-house', title: 'Aspects on House', icon: '👁️' },
                          { key: 'house-strength', title: 'House Strength', icon: '💪' },
                          { key: 'ashtakavarga', title: 'Ashtakavarga Points', icon: '🎯' },
                          { key: 'yogi-analysis', title: 'Yogi Points', icon: '🌟' },
                          { key: 'badhaka-analysis', title: 'Badhaka Obstacles', icon: '⚠️' },
                          { key: 'house-overall', title: 'Overall Assessment', icon: '📊' }
                        ].map((section) => {
                          const data = completeAnalysisData['tenth-house'];
                          let status = 'neutral';
                          let score = '';
                          
                          if (section.key === 'house-sign') {
                            status = 'neutral';
                            score = data.house_sign.substring(0, 3);
                          } else if (section.key === 'planets-in-house') {
                            const count = data.planets_in_house.length;
                            status = count > 0 ? 'positive' : 'neutral';
                            score = `${count}`;
                          } else if (section.key === 'aspects-on-house') {
                            const count = data.aspects.length;
                            status = count > 0 ? 'positive' : 'neutral';
                            score = `${count}`;
                          } else if (section.key === 'house-strength') {
                            const strength = data.strength_details.enhanced_strength;
                            status = strength >= 70 ? 'positive' : strength <= 40 ? 'negative' : 'neutral';
                            score = `${Math.round(strength)}`;
                          } else if (section.key === 'ashtakavarga') {
                            status = 'neutral';
                            score = 'N/A';
                          } else if (section.key === 'yogi-analysis') {
                            const yogiImpact = data.yogi_analysis ? data.yogi_analysis.career_impact.total_impact : 0;
                            status = yogiImpact > 70 ? 'positive' : yogiImpact < 40 ? 'negative' : 'neutral';
                            score = data.yogi_analysis ? `${Math.round(yogiImpact)}` : 'N/A';
                          } else if (section.key === 'badhaka-analysis') {
                            const badhakaImpact = data.badhaka_analysis ? (data.badhaka_analysis.career_impact.has_impact ? data.badhaka_analysis.career_impact.impact_score : 0) : 0;
                            status = badhakaImpact > 50 ? 'negative' : 'positive';
                            score = data.badhaka_analysis ? (data.badhaka_analysis.career_impact.has_impact ? `${Math.round(badhakaImpact)}` : '0') : 'N/A';
                          } else if (section.key === 'house-overall') {
                            const overallScore = data.strength_details.enhanced_strength;
                            status = overallScore >= 70 ? 'positive' : overallScore <= 40 ? 'negative' : 'neutral';
                            score = `${Math.round(overallScore)}`;
                          }
                          
                          return (
                            <button 
                              key={section.key}
                              className={`section-btn section-btn-${status}`}
                              onClick={() => openModal(`${section.title} - 10th House`, section.key === 'yogi-analysis' ? renderYogiBadhakaDetails('tenth-house', 'yogi', completeAnalysisData) : section.key === 'badhaka-analysis' ? renderYogiBadhakaDetails('tenth-house', 'badhaka', completeAnalysisData) : renderTenthHouseDetails(section.key))}
                            >
                              <span className="section-icon">{section.icon}</span>
                              <span className="section-title">{section.title}</span>
                              <span className="section-score">{score}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ) : (section.id === 'd10-analysis' && completeAnalysisData['d10-analysis']) ? (
                    <div className="analysis-summary">
                      <div className="summary-grid">
                        {[
                          { label: 'D10 Ascendant', value: completeAnalysisData['d10-analysis'].ascendant_analysis.sign, type: 'neutral' },
                          { label: 'Approach', value: completeAnalysisData['d10-analysis'].ascendant_analysis.strength, type: completeAnalysisData['d10-analysis'].ascendant_analysis.strength === 'Strong' ? 'positive' : completeAnalysisData['d10-analysis'].ascendant_analysis.strength === 'Weak' ? 'negative' : 'neutral' },
                          { label: '10th Lord', value: completeAnalysisData['d10-analysis'].tenth_lord_analysis.tenth_lord, type: 'neutral' },
                          { label: 'Lord Position', value: `${completeAnalysisData['d10-analysis'].tenth_lord_analysis.position_sign} (H${completeAnalysisData['d10-analysis'].tenth_lord_analysis.position_house})`, type: completeAnalysisData['d10-analysis'].tenth_lord_analysis.position_house <= 4 || completeAnalysisData['d10-analysis'].tenth_lord_analysis.position_house === 10 ? 'positive' : completeAnalysisData['d10-analysis'].tenth_lord_analysis.position_house >= 8 && completeAnalysisData['d10-analysis'].tenth_lord_analysis.position_house <= 12 ? 'negative' : 'neutral' },
                          { label: 'Professional Strength', value: `${completeAnalysisData['d10-analysis'].professional_strength.score}/100`, type: completeAnalysisData['d10-analysis'].professional_strength.score >= 70 ? 'positive' : completeAnalysisData['d10-analysis'].professional_strength.score <= 40 ? 'negative' : 'neutral' },
                          { label: 'Grade', value: completeAnalysisData['d10-analysis'].professional_strength.grade, type: completeAnalysisData['d10-analysis'].professional_strength.grade === 'Excellent' || completeAnalysisData['d10-analysis'].professional_strength.grade === 'Very Good' ? 'positive' : completeAnalysisData['d10-analysis'].professional_strength.grade === 'Needs Improvement' ? 'negative' : 'neutral' }
                        ].map((item, index) => (
                          <div key={index} className="summary-item">
                            <span className="item-label">{item.label}</span>
                            <span className={`item-value ${item.type}`}>{item.value}</span>
                          </div>
                        ))}
                      </div>
                      <div className="d10-details">
                        <h4>🎯 Career Approach</h4>
                        <p>{completeAnalysisData['d10-analysis'].ascendant_analysis.career_approach}</p>
                        
                        <h4>💼 10th Lord Impact</h4>
                        <p>{completeAnalysisData['d10-analysis'].tenth_lord_analysis.career_impact}</p>
                        
                        <h4>⭐ Career Indicators</h4>
                        <ul>
                          {completeAnalysisData['d10-analysis'].career_indicators.map((indicator, index) => (
                            <li key={index}>{indicator}</li>
                          ))}
                        </ul>
                        
                        <h4>📋 Career Recommendations</h4>
                        <ul>
                          {completeAnalysisData['d10-analysis'].career_recommendations.map((rec, index) => (
                            <li key={index}>{rec}</li>
                          ))}
                        </ul>
                        
                        <h4>🌟 Planet Analysis</h4>
                        <div className="planet-grid">
                          {Object.entries(completeAnalysisData['d10-analysis'].planet_analysis).map(([planet, data]) => (
                            <div key={planet} className="planet-item">
                              <strong>{planet}</strong> in {data.sign} (H{data.house})
                              <div className="planet-effect">{data.overall_effect}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (section.id === 'saturn-tenth' && completeAnalysisData['saturn-tenth']) ? (
                    <div className="analysis-summary">
                      <div className="summary-grid">
                        {[
                          { label: 'Saturn House', value: `H${completeAnalysisData['saturn-tenth'].saturn_info.saturn_house}`, type: 'neutral' },
                          { label: '10th from Saturn', value: `H${completeAnalysisData['saturn-tenth'].saturn_tenth_house_info.house_number}`, type: 'neutral' },
                          { label: 'House Sign', value: completeAnalysisData['saturn-tenth'].saturn_tenth_house_info.house_sign, type: 'neutral' },
                          { label: 'House Lord', value: completeAnalysisData['saturn-tenth'].saturn_tenth_house_info.house_lord, type: 'neutral' },
                          { label: 'Yogi Impact', value: completeAnalysisData['saturn-tenth'].saturn_tenth_yogi_analysis ? `${Math.round(completeAnalysisData['saturn-tenth'].saturn_tenth_yogi_analysis.house_impact.total_impact)}%` : 'N/A', type: completeAnalysisData['saturn-tenth'].saturn_tenth_yogi_analysis && completeAnalysisData['saturn-tenth'].saturn_tenth_yogi_analysis.house_impact.total_impact > 70 ? 'positive' : completeAnalysisData['saturn-tenth'].saturn_tenth_yogi_analysis && completeAnalysisData['saturn-tenth'].saturn_tenth_yogi_analysis.house_impact.total_impact < 40 ? 'negative' : 'neutral' },
                          { label: 'Badhaka Impact', value: completeAnalysisData['saturn-tenth'].saturn_tenth_badhaka_analysis ? (completeAnalysisData['saturn-tenth'].saturn_tenth_badhaka_analysis.house_impact.has_impact ? `${Math.round(completeAnalysisData['saturn-tenth'].saturn_tenth_badhaka_analysis.house_impact.impact_score)}%` : 'None') : 'N/A', type: completeAnalysisData['saturn-tenth'].saturn_tenth_badhaka_analysis && completeAnalysisData['saturn-tenth'].saturn_tenth_badhaka_analysis.house_impact.has_impact && completeAnalysisData['saturn-tenth'].saturn_tenth_badhaka_analysis.house_impact.impact_score > 50 ? 'negative' : 'positive' },
                          { label: 'Grade', value: completeAnalysisData['saturn-tenth'].overall_assessment.overall_grade, type: completeAnalysisData['saturn-tenth'].overall_assessment.overall_grade === 'Excellent' || completeAnalysisData['saturn-tenth'].overall_assessment.overall_grade === 'Very Good' ? 'positive' : completeAnalysisData['saturn-tenth'].overall_assessment.overall_grade === 'Weak' ? 'negative' : 'neutral' },
                          { label: 'Strength', value: `${Math.round(completeAnalysisData['saturn-tenth'].overall_assessment.overall_strength_score)}/100`, type: completeAnalysisData['saturn-tenth'].overall_assessment.overall_strength_score >= 70 ? 'positive' : completeAnalysisData['saturn-tenth'].overall_assessment.overall_strength_score <= 40 ? 'negative' : 'neutral' }
                        ].map((item, index) => (
                          <div key={index} className="summary-item">
                            <span className="item-label">{item.label}</span>
                            {(item.label === 'Grade' || item.label === 'Strength') ? (
                              <span 
                                className={`item-value ${item.type} clickable`}
                                onClick={() => openModal(
                                  `${item.label} Calculation - 10th from Saturn`,
                                  renderCalculationDetails('saturn-tenth', item.label.toLowerCase())
                                )}
                              >
                                {item.value}
                              </span>
                            ) : (
                              <span className={`item-value ${item.type}`}>{item.value}</span>
                            )}
                          </div>
                        ))}
                      </div>
                      <div className="analysis-sections-grid">
                        {[
                          { key: 'saturn-sign', title: 'Saturn Sign Analysis', icon: '🪐' },
                          { key: 'saturn-planets', title: 'Planets in House', icon: '🌟' },
                          { key: 'saturn-aspects', title: 'Aspects on House', icon: '👁️' },
                          { key: 'saturn-strength', title: 'House Strength', icon: '💪' },
                          { key: 'saturn-yogi', title: 'Yogi Points', icon: '🌟' },
                          { key: 'saturn-badhaka', title: 'Badhaka Impact', icon: '⚠️' },
                          { key: 'saturn-ashtakavarga', title: 'Ashtakavarga Points', icon: '🎯' },
                          { key: 'saturn-overall', title: 'Overall Assessment', icon: '📊' }
                        ].map((section) => {
                          const data = completeAnalysisData['saturn-tenth'];
                          let status = 'neutral';
                          let score = '';
                          
                          if (section.key === 'saturn-sign') {
                            status = 'neutral';
                            score = data.saturn_tenth_house_info.house_sign.substring(0, 3);
                          } else if (section.key === 'saturn-planets') {
                            const count = data.planets_in_house.planet_count;
                            status = count > 0 ? 'positive' : 'neutral';
                            score = `${count}`;
                          } else if (section.key === 'saturn-aspects') {
                            const netScore = data.aspects_on_house.net_aspect_score;
                            status = netScore > 0 ? 'positive' : netScore < 0 ? 'negative' : 'neutral';
                            score = `${netScore > 0 ? '+' : ''}${netScore.toFixed(1)}`;
                          } else if (section.key === 'saturn-strength') {
                            const strength = data.house_strength.total_score;
                            status = strength >= 70 ? 'positive' : strength <= 40 ? 'negative' : 'neutral';
                            score = `${Math.round(strength)}`;
                          } else if (section.key === 'saturn-yogi') {
                            const yogiData = completeAnalysisData['saturn-tenth'].saturn_tenth_yogi_analysis;
                            if (yogiData && yogiData.house_impact.total_impact) {
                              const impact = yogiData.house_impact.total_impact;
                              status = impact > 70 ? 'positive' : impact < 40 ? 'negative' : 'neutral';
                              score = `${Math.round(impact)}`;
                            } else {
                              status = 'neutral';
                              score = '~';
                            }
                          } else if (section.key === 'saturn-badhaka') {
                            const badhakaData = completeAnalysisData['saturn-tenth'].saturn_tenth_badhaka_analysis;
                            if (badhakaData && badhakaData.house_impact.has_impact) {
                              status = 'negative';
                              score = `${Math.round(badhakaData.house_impact.impact_score)}`;
                            } else {
                              status = 'positive';
                              score = '✓';
                            }
                          } else if (section.key === 'saturn-ashtakavarga') {
                            const points = data.ashtakavarga_points.total_points;
                            status = points >= 30 ? 'positive' : points <= 25 ? 'negative' : 'neutral';
                            score = `${points}`;
                          } else if (section.key === 'saturn-overall') {
                            const overallScore = data.overall_assessment.overall_strength_score;
                            status = overallScore >= 70 ? 'positive' : overallScore <= 40 ? 'negative' : 'neutral';
                            score = `${Math.round(overallScore)}`;
                          }
                          
                          return (
                            <button 
                              key={section.key}
                              className={`section-btn section-btn-${status}`}
                              onClick={() => openModal(`${section.title} - 10th from Saturn`, section.key === 'saturn-yogi' ? renderYogiBadhakaDetails('saturn-tenth', 'yogi', completeAnalysisData) : section.key === 'saturn-badhaka' ? renderYogiBadhakaDetails('saturn-tenth', 'badhaka', completeAnalysisData) : renderSaturnTenthSectionDetails(section.key))}
                            >
                              <span className="section-icon">{section.icon}</span>
                              <span className="section-title">{section.title}</span>
                              <span className="section-score">{score}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ) : (section.id === 'saturn-karaka' && completeAnalysisData['saturn-karaka']) ? (
                    <div className="analysis-summary">
                      <div className="summary-grid">
                        {[
                          { label: 'Saturn Sign', value: completeAnalysisData['saturn-karaka'].saturn_basic_info.sign_name, type: 'neutral' },
                          { label: 'Saturn House', value: `H${completeAnalysisData['saturn-karaka'].saturn_basic_info.house}`, type: 'neutral' },
                          { label: 'Grade', value: completeAnalysisData['saturn-karaka'].saturn_analysis.overall_assessment.overall_grade, type: completeAnalysisData['saturn-karaka'].saturn_analysis.overall_assessment.overall_grade === 'Excellent' || completeAnalysisData['saturn-karaka'].saturn_analysis.overall_assessment.overall_grade === 'Very Good' ? 'positive' : completeAnalysisData['saturn-karaka'].saturn_analysis.overall_assessment.overall_grade === 'Weak' ? 'negative' : 'neutral' },
                          { label: 'Score', value: `${Math.round(completeAnalysisData['saturn-karaka'].saturn_analysis.overall_assessment.overall_strength_score)}/100`, type: completeAnalysisData['saturn-karaka'].saturn_analysis.overall_assessment.overall_strength_score >= 70 ? 'positive' : completeAnalysisData['saturn-karaka'].saturn_analysis.overall_assessment.overall_strength_score <= 40 ? 'negative' : 'neutral' },
                          { label: 'Dignity', value: completeAnalysisData['saturn-karaka'].saturn_analysis.dignity_analysis.dignity, type: completeAnalysisData['saturn-karaka'].saturn_analysis.dignity_analysis.dignity === 'exalted' || completeAnalysisData['saturn-karaka'].saturn_analysis.dignity_analysis.dignity === 'own_sign' ? 'positive' : completeAnalysisData['saturn-karaka'].saturn_analysis.dignity_analysis.dignity === 'debilitated' ? 'negative' : 'neutral' },
                          { label: 'Yogi Status', value: completeAnalysisData['saturn-karaka'].saturn_yogi_significance ? (completeAnalysisData['saturn-karaka'].saturn_yogi_significance.saturn_significance.has_impact ? completeAnalysisData['saturn-karaka'].saturn_yogi_significance.saturn_significance.special_status.replace('_', ' ').toUpperCase() : 'Neutral') : 'N/A', type: completeAnalysisData['saturn-karaka'].saturn_yogi_significance ? (completeAnalysisData['saturn-karaka'].saturn_yogi_significance.saturn_significance.special_status === 'yogi_lord' ? 'positive' : completeAnalysisData['saturn-karaka'].saturn_yogi_significance.saturn_significance.special_status === 'avayogi_lord' || completeAnalysisData['saturn-karaka'].saturn_yogi_significance.saturn_significance.special_status === 'dagdha_lord' ? 'negative' : 'neutral') : 'neutral' },
                          { label: 'Badhaka Status', value: completeAnalysisData['saturn-karaka'].saturn_badhaka_impact ? (completeAnalysisData['saturn-karaka'].saturn_badhaka_impact.badhaka_impact.has_impact ? (completeAnalysisData['saturn-karaka'].saturn_badhaka_impact.badhaka_impact.is_badhaka_lord ? 'IS Badhaka Lord' : 'Affected by Badhaka') : 'No Impact') : 'N/A', type: completeAnalysisData['saturn-karaka'].saturn_badhaka_impact ? (completeAnalysisData['saturn-karaka'].saturn_badhaka_impact.badhaka_impact.has_impact ? 'negative' : 'positive') : 'neutral' }
                        ].map((item, index) => (
                          <div key={index} className="summary-item">
                            <span className="item-label">{item.label}</span>
                            {(item.label === 'Grade' || item.label === 'Score') ? (
                              <span 
                                className={`item-value ${item.type} clickable`}
                                onClick={() => openModal(
                                  `${item.label} Calculation - Saturn Karma Karaka`,
                                  renderCalculationDetails('saturn-karaka', item.label.toLowerCase())
                                )}
                              >
                                {item.value}
                              </span>
                            ) : (
                              <span className={`item-value ${item.type}`}>{item.value}</span>
                            )}
                          </div>
                        ))}
                      </div>
                      <div className="analysis-sections-grid">
                        {[
                          { key: 'dignity', title: 'Dignity Analysis', icon: '👑' },
                          { key: 'strength', title: 'Shadbala Strength', icon: '💪' },
                          { key: 'house', title: 'House Position', icon: '🏠' },
                          { key: 'friendship', title: '5-Fold Friendship', icon: '🤝' },
                          { key: 'conjunctions', title: 'Conjunctions', icon: '🔗' },
                          { key: 'aspects', title: 'Aspects Received', icon: '👁️' },
                          { key: 'yogi-analysis', title: 'Yogi Points', icon: '🌟' },
                          { key: 'badhaka-analysis', title: 'Badhaka Impact', icon: '⚠️' },
                          { key: 'karma', title: 'Career Karma', icon: '⚙️' },
                          { key: 'overall', title: 'Overall Assessment', icon: '📊' }
                        ].map((section) => {
                          const data = completeAnalysisData['saturn-karaka'].saturn_analysis;
                          let status = 'neutral';
                          let score = '';
                          
                          if (section.key === 'dignity') {
                            const dignity = data.dignity_analysis.dignity;
                            status = dignity === 'exalted' || dignity === 'own_sign' ? 'positive' : dignity === 'debilitated' ? 'negative' : 'neutral';
                            score = `${data.dignity_analysis.strength_multiplier}x`;
                          } else if (section.key === 'strength') {
                            const rupas = data.strength_analysis.shadbala_rupas;
                            status = rupas >= 6 ? 'positive' : rupas <= 3 ? 'negative' : 'neutral';
                            score = `${rupas.toFixed(1)}`;
                          } else if (section.key === 'house') {
                            const types = data.house_position_analysis.house_types;
                            status = types.includes('Kendra') || types.includes('Trikona') ? 'positive' : types.includes('Dusthana') ? 'negative' : 'neutral';
                            score = `H${data.house_position_analysis.house_number}`;
                          } else if (section.key === 'friendship') {
                            const friendship = data.friendship_analysis.overall_friendship_status;
                            status = friendship.includes('Favorable') ? 'positive' : friendship.includes('Unfavorable') ? 'negative' : 'neutral';
                            score = friendship.includes('Favorable') ? '+' : friendship.includes('Unfavorable') ? '-' : '~';
                          } else if (section.key === 'conjunctions') {
                            const effect = data.conjunctions.overall_conjunction_effect;
                            status = effect === 'beneficial' ? 'positive' : effect === 'harmful' ? 'negative' : 'neutral';
                            score = data.conjunctions.has_conjunctions ? `${data.conjunctions.conjunction_count}` : '0';
                          } else if (section.key === 'aspects') {
                            const aspects = data.aspects_received.aspects;
                            const totalScore = aspects.reduce((sum, aspect) => sum + (aspect.effect_score || 0), 0);
                            const avgScore = aspects.length > 0 ? totalScore / aspects.length : 0;
                            status = avgScore > 1 ? 'positive' : avgScore < -1 ? 'negative' : 'neutral';
                            score = aspects.length > 0 ? `${avgScore > 0 ? '+' : ''}${avgScore.toFixed(1)}` : '0';
                          } else if (section.key === 'yogi-analysis') {
                            const yogiData = completeAnalysisData['saturn-karaka'].saturn_yogi_significance;
                            if (yogiData && yogiData.saturn_significance.has_impact) {
                              const specialStatus = yogiData.saturn_significance.special_status;
                              status = specialStatus === 'yogi_lord' ? 'positive' : specialStatus === 'avayogi_lord' || specialStatus === 'dagdha_lord' ? 'negative' : 'neutral';
                              score = specialStatus === 'yogi_lord' ? 'Y+' : specialStatus === 'avayogi_lord' ? 'A-' : specialStatus === 'dagdha_lord' ? 'D-' : specialStatus === 'tithi_shunya_lord' ? 'T~' : '~';
                            } else {
                              status = 'neutral';
                              score = '~';
                            }
                          } else if (section.key === 'badhaka-analysis') {
                            const badhakaData = completeAnalysisData['saturn-karaka'].saturn_badhaka_impact;
                            if (badhakaData && badhakaData.badhaka_impact.has_impact) {
                              status = 'negative';
                              score = badhakaData.badhaka_impact.is_badhaka_lord ? 'BL' : 'B-';
                            } else {
                              status = 'positive';
                              score = '✓';
                            }
                          } else if (section.key === 'karma') {
                            status = 'neutral';
                            score = 'KK';
                          } else if (section.key === 'overall') {
                            const overallScore = data.overall_assessment.overall_strength_score;
                            status = overallScore >= 70 ? 'positive' : overallScore <= 40 ? 'negative' : 'neutral';
                            score = `${Math.round(overallScore)}`;
                          }
                          
                          return (
                            <button 
                              key={section.key}
                              className={`section-btn section-btn-${status}`}
                              onClick={() => openModal(`${section.title} - Saturn Karma Karaka`, section.key === 'yogi-analysis' ? renderYogiBadhakaDetails('saturn-karaka', 'yogi', completeAnalysisData) : section.key === 'badhaka-analysis' ? renderYogiBadhakaDetails('saturn-karaka', 'badhaka', completeAnalysisData) : section.key === 'karma' ? renderSaturnKarmaDetails() : renderSaturnSectionDetails(section.key))}
                            >
                              <span className="section-icon">{section.icon}</span>
                              <span className="section-title">{section.title}</span>
                              <span className="section-score">{score}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ) : (section.id === 'amatyakaraka' && completeAnalysisData['amatyakaraka']) ? (
                    <div className="analysis-summary">
                      <div className="summary-grid">
                        {[
                          { label: 'AmK Planet', value: completeAnalysisData['amatyakaraka'].amatyakaraka_planet, type: 'neutral' },
                          { label: 'AmK House', value: `H${completeAnalysisData['amatyakaraka'].amk_analysis.house}`, type: 'neutral' },
                          { label: 'AmK Sign', value: completeAnalysisData['amatyakaraka'].amk_analysis.sign_name, type: 'neutral' },
                          { label: 'Dignity', value: completeAnalysisData['amatyakaraka'].amk_analysis.dignity, type: completeAnalysisData['amatyakaraka'].amk_analysis.dignity === 'exalted' || completeAnalysisData['amatyakaraka'].amk_analysis.dignity === 'own_sign' ? 'positive' : completeAnalysisData['amatyakaraka'].amk_analysis.dignity === 'debilitated' ? 'negative' : 'neutral' },
                          { label: 'Yogi Status', value: completeAnalysisData['amatyakaraka'].amk_yogi_significance ? (completeAnalysisData['amatyakaraka'].amk_yogi_significance.amk_significance.has_impact ? completeAnalysisData['amatyakaraka'].amk_yogi_significance.amk_significance.special_status.replace('_', ' ').toUpperCase() : 'Neutral') : 'N/A', type: completeAnalysisData['amatyakaraka'].amk_yogi_significance ? (completeAnalysisData['amatyakaraka'].amk_yogi_significance.amk_significance.special_status === 'yogi_lord' ? 'positive' : completeAnalysisData['amatyakaraka'].amk_yogi_significance.amk_significance.special_status === 'avayogi_lord' || completeAnalysisData['amatyakaraka'].amk_yogi_significance.amk_significance.special_status === 'dagdha_lord' ? 'negative' : 'neutral') : 'neutral' },
                          { label: 'Badhaka Status', value: completeAnalysisData['amatyakaraka'].amk_badhaka_impact ? (completeAnalysisData['amatyakaraka'].amk_badhaka_impact.badhaka_impact.has_impact ? (completeAnalysisData['amatyakaraka'].amk_badhaka_impact.badhaka_impact.is_badhaka_lord ? 'IS Badhaka Lord' : 'Affected by Badhaka') : 'No Impact') : 'N/A', type: completeAnalysisData['amatyakaraka'].amk_badhaka_impact ? (completeAnalysisData['amatyakaraka'].amk_badhaka_impact.badhaka_impact.has_impact ? 'negative' : 'positive') : 'neutral' },
                          { label: 'AK-AmK Relation', value: completeAnalysisData['amatyakaraka'].ak_amk_relationship.relationship_type, type: completeAnalysisData['amatyakaraka'].ak_amk_relationship.relationship_type.includes('Harmonious') || completeAnalysisData['amatyakaraka'].ak_amk_relationship.relationship_type === 'Conjunction' ? 'positive' : completeAnalysisData['amatyakaraka'].ak_amk_relationship.relationship_type.includes('Friction') ? 'negative' : 'neutral' }
                        ].map((item, index) => (
                          <div key={index} className="summary-item">
                            <span className="item-label">{item.label}</span>
                            <span className={`item-value ${item.type}`}>{item.value}</span>
                          </div>
                        ))}
                      </div>
                      
                      <div className="jaimini-analysis">
                        <h4>👑 Jaimini Amatyakaraka Analysis</h4>
                        
                        <div className="amk-step">
                          <h5>Step 1: Planet Analysis</h5>
                          <div className="step-content">
                            <p><strong>Primary Field:</strong> {completeAnalysisData['amatyakaraka'].amk_analysis.profession_indications.primary_field}</p>
                            <p><strong>Work Style:</strong> {completeAnalysisData['amatyakaraka'].amk_analysis.profession_indications.work_style}</p>
                            <p><strong>Secondary Fields:</strong> {completeAnalysisData['amatyakaraka'].amk_analysis.profession_indications.secondary_fields.join(', ')}</p>
                          </div>
                        </div>
                        
                        <div className="amk-step">
                          <h5>Step 2: House & Sign Placement</h5>
                          <div className="step-content">
                            <p><strong>House Significance:</strong> {completeAnalysisData['amatyakaraka'].amk_analysis.house_significance}</p>
                            <p><strong>Sign Style:</strong> {completeAnalysisData['amatyakaraka'].amk_analysis.sign_style}</p>
                          </div>
                        </div>
                        
                        <div className="amk-step">
                          <h5>Step 3: AK-AmK Relationship</h5>
                          <div className="step-content">
                            <p><strong>Atmakaraka:</strong> {completeAnalysisData['amatyakaraka'].ak_amk_relationship.atmakaraka} (H{completeAnalysisData['amatyakaraka'].ak_amk_relationship.atmakaraka_house})</p>
                            <p><strong>Relationship:</strong> {completeAnalysisData['amatyakaraka'].ak_amk_relationship.relationship_type}</p>
                            <p><strong>Career Impact:</strong> {completeAnalysisData['amatyakaraka'].ak_amk_relationship.career_impact}</p>
                            {completeAnalysisData['amatyakaraka'].ak_amk_relationship.conjunction && <p className="positive">✓ Perfect conjunction - soul and career aligned</p>}
                            {completeAnalysisData['amatyakaraka'].ak_amk_relationship.mutual_aspect && <p className="positive">✓ Mutual aspect - supportive energy flow</p>}
                          </div>
                        </div>
                        
                        <div className="amk-step">
                          <h5>Step 4: Navamsa Analysis</h5>
                          <div className="step-content">
                            <p><strong>Navamsa Sign:</strong> {completeAnalysisData['amatyakaraka'].navamsa_analysis.navamsa_sign_name}</p>
                            <p><strong>Navamsa Lord:</strong> {completeAnalysisData['amatyakaraka'].navamsa_analysis.navamsa_lord}</p>
                            <p><strong>Work Environment:</strong> {completeAnalysisData['amatyakaraka'].navamsa_analysis.work_environment}</p>
                            <p><strong>Inner Drive:</strong> {completeAnalysisData['amatyakaraka'].navamsa_analysis.inner_drive}</p>
                          </div>
                        </div>
                        
                        <div className="amk-step">
                          <h5>Step 5: 10th from AmK (Karma Bhava)</h5>
                          <div className="step-content">
                            <p><strong>Karma Bhava:</strong> H{completeAnalysisData['amatyakaraka'].tenth_from_amk.karma_bhava_house} ({completeAnalysisData['amatyakaraka'].tenth_from_amk.karma_bhava_sign})</p>
                            <p><strong>Karma Bhava Lord:</strong> {completeAnalysisData['amatyakaraka'].tenth_from_amk.karma_bhava_lord}</p>
                            <p><strong>Career Refinement:</strong> {completeAnalysisData['amatyakaraka'].tenth_from_amk.career_refinement}</p>
                            {completeAnalysisData['amatyakaraka'].tenth_from_amk.planets_in_karma.length > 0 && (
                              <p><strong>Planets in Karma Bhava:</strong> {completeAnalysisData['amatyakaraka'].tenth_from_amk.planets_in_karma.join(', ')}</p>
                            )}
                            {completeAnalysisData['amatyakaraka'].tenth_from_amk.aspects_on_karma.length > 0 && (
                              <p><strong>Aspects on Karma Bhava:</strong> {completeAnalysisData['amatyakaraka'].tenth_from_amk.aspects_on_karma.join(', ')}</p>
                            )}
                          </div>
                        </div>
                        
                        <div className="amk-step">
                          <h5>Step 6: D10 Correlation</h5>
                          <div className="step-content">
                            <p>{completeAnalysisData['amatyakaraka'].d10_analysis.message}</p>
                          </div>
                        </div>
                        
                        <div className="analysis-sections-grid">
                          {[
                            { key: 'yogi-analysis', title: 'Yogi Points', icon: '🌟' },
                            { key: 'badhaka-analysis', title: 'Badhaka Impact', icon: '⚠️' }
                          ].map((section) => {
                            let status = 'neutral';
                            let score = '';
                            
                            if (section.key === 'yogi-analysis') {
                              const yogiData = completeAnalysisData['amatyakaraka'].amk_yogi_significance;
                              if (yogiData && yogiData.amk_significance.has_impact) {
                                const specialStatus = yogiData.amk_significance.special_status;
                                status = specialStatus === 'yogi_lord' ? 'positive' : specialStatus === 'avayogi_lord' || specialStatus === 'dagdha_lord' ? 'negative' : 'neutral';
                                score = specialStatus === 'yogi_lord' ? 'Y+' : specialStatus === 'avayogi_lord' ? 'A-' : specialStatus === 'dagdha_lord' ? 'D-' : specialStatus === 'tithi_shunya_lord' ? 'T~' : '~';
                              } else {
                                status = 'neutral';
                                score = '~';
                              }
                            } else if (section.key === 'badhaka-analysis') {
                              const badhakaData = completeAnalysisData['amatyakaraka'].amk_badhaka_impact;
                              if (badhakaData && badhakaData.badhaka_impact.has_impact) {
                                status = 'negative';
                                score = badhakaData.badhaka_impact.is_badhaka_lord ? 'BL' : 'B-';
                              } else {
                                status = 'positive';
                                score = '✓';
                              }
                            }
                            
                            return (
                              <button 
                                key={section.key}
                                className={`section-btn section-btn-${status}`}
                                onClick={() => openModal(`${section.title} - Amatyakaraka`, section.key === 'yogi-analysis' ? renderYogiBadhakaDetails('amatyakaraka', 'yogi', completeAnalysisData) : renderYogiBadhakaDetails('amatyakaraka', 'badhaka', completeAnalysisData))}
                              >
                                <span className="section-icon">{section.icon}</span>
                                <span className="section-title">{section.title}</span>
                                <span className="section-score">{score}</span>
                              </button>
                            );
                          })}
                        </div>
                        
                        <div className="profession-summary">
                          <h4>🎯 Professional Summary</h4>
                          <div className="summary-content">
                            <p><strong>Primary Field:</strong> {completeAnalysisData['amatyakaraka'].profession_summary.primary_field}</p>
                            <p><strong>Career Style:</strong> {completeAnalysisData['amatyakaraka'].profession_summary.career_style}</p>
                            <p><strong>Work Area:</strong> {completeAnalysisData['amatyakaraka'].profession_summary.work_area}</p>
                            
                            <div className="key-strengths">
                              <h5>Key Strengths:</h5>
                              <ul>
                                {completeAnalysisData['amatyakaraka'].profession_summary.key_strengths.map((strength, index) => (
                                  <li key={index}>{strength}</li>
                                ))}
                              </ul>
                            </div>
                            
                            <div className="recommended-paths">
                              <h5>Recommended Career Paths:</h5>
                              <ul>
                                {completeAnalysisData['amatyakaraka'].profession_summary.recommended_paths.map((path, index) => (
                                  <li key={index}>{path}</li>
                                ))}
                              </ul>
                            </div>
                            
                            <div className="success-factors">
                              <h5>Success Factors:</h5>
                              <ul>
                                {completeAnalysisData['amatyakaraka'].profession_summary.success_factors.map((factor, index) => (
                                  <li key={index}>{factor}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (section.id === 'career-yogas' && completeAnalysisData['career-yogas']) ? (
                    <div className="analysis-summary">
                      <div className="summary-grid">
                        {[
                          { label: 'Total Yogas', value: completeAnalysisData['career-yogas'].total_yogas, type: 'neutral' },
                          { label: 'Strong Yogas', value: completeAnalysisData['career-yogas'].strong_yogas, type: completeAnalysisData['career-yogas'].strong_yogas > 0 ? 'positive' : 'neutral' },
                          { label: 'Moderate Yogas', value: completeAnalysisData['career-yogas'].moderate_yogas, type: 'neutral' },
                          { label: 'Overall Grade', value: completeAnalysisData['career-yogas'].overall_yoga_strength.grade, type: completeAnalysisData['career-yogas'].overall_yoga_strength.grade === 'Excellent' || completeAnalysisData['career-yogas'].overall_yoga_strength.grade === 'Very Good' ? 'positive' : completeAnalysisData['career-yogas'].overall_yoga_strength.grade === 'Weak' ? 'negative' : 'neutral' },
                          { label: 'Overall Score', value: `${Math.round(completeAnalysisData['career-yogas'].overall_yoga_strength.score)}/100`, type: completeAnalysisData['career-yogas'].overall_yoga_strength.score >= 70 ? 'positive' : completeAnalysisData['career-yogas'].overall_yoga_strength.score <= 40 ? 'negative' : 'neutral' },
                          { label: 'Primary Strength', value: completeAnalysisData['career-yogas'].career_yoga_summary.primary_strength, type: 'neutral' }
                        ].map((item, index) => (
                          <div key={index} className="summary-item">
                            <span className="item-label">{item.label}</span>
                            <span className={`item-value ${item.type}`}>{item.value}</span>
                          </div>
                        ))}
                      </div>
                      
                      <div className="yogas-analysis">
                        <h4>✨ Career Success Yogas</h4>
                        
                        <div className="yoga-summary">
                          <p><strong>Overall Assessment:</strong> {completeAnalysisData['career-yogas'].overall_yoga_strength.interpretation}</p>
                          <p><strong>Primary Strength:</strong> {completeAnalysisData['career-yogas'].career_yoga_summary.primary_strength}</p>
                          <p><strong>Timing Focus:</strong> {completeAnalysisData['career-yogas'].career_yoga_summary.timing_focus}</p>
                        </div>
                        
                        <div className="yogas-list">
                          <h5>Top Career Yogas:</h5>
                          {completeAnalysisData['career-yogas'].yogas.slice(0, 6).map((yoga, index) => (
                            <div key={index} className="yoga-item">
                              <div className="yoga-header">
                                <span className="yoga-rank">#{index + 1}</span>
                                <strong>{yoga.name}</strong>
                                <span className={`yoga-type ${yoga.type.toLowerCase().replace(' ', '-')}`}>{yoga.type}</span>
                                <span className={`strength-badge ${yoga.strength_grade.toLowerCase().replace(' ', '-')}`}>
                                  {yoga.strength_grade} ({Math.round(yoga.strength_score)}%)
                                </span>
                              </div>
                              <div className="yoga-details">
                                <p><strong>Career Impact:</strong> {yoga.career_impact}</p>
                                <p><strong>Description:</strong> {yoga.description}</p>
                                <p><strong>Timing Relevance:</strong> {yoga.timing_relevance}</p>
                                {yoga.planets && <p><strong>Planets:</strong> {yoga.planets.join(', ')}</p>}
                                {yoga.planet && <p><strong>Planet:</strong> {yoga.planet}</p>}
                                {yoga.houses && <p><strong>Houses:</strong> {yoga.houses.map(h => `H${h}`).join(', ')}</p>}
                                {yoga.house && <p><strong>House:</strong> H{yoga.house}</p>}
                                {yoga.classical_reference && (
                                  <div className="classical-reference">
                                    <p><strong>📜 Classical Reference:</strong> {yoga.classical_reference}</p>
                                    {yoga.sanskrit_verse && <p><strong>🕉️ Sanskrit:</strong> <em>{yoga.sanskrit_verse}</em></p>}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                        
                        <div className="key-benefits">
                          <h5>Key Benefits:</h5>
                          <ul>
                            {completeAnalysisData['career-yogas'].career_yoga_summary.key_benefits.map((benefit, index) => (
                              <li key={index}>{benefit}</li>
                            ))}
                          </ul>
                        </div>
                        
                        <div className="recommendations">
                          <h5>Recommendations:</h5>
                          <ul>
                            {completeAnalysisData['career-yogas'].career_yoga_summary.recommendations.map((rec, index) => (
                              <li key={index}>{rec}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="coming-soon">
                      <p>Detailed analysis coming soon</p>
                      <div className="feature-preview">
                        {section.id === 'tenth-house' && (
                          <ul>
                            <li>Planets in 10th house analysis</li>
                            <li>Aspects on career house</li>
                            <li>Ashtakavarga strength points</li>
                            <li>Sign lord influence</li>
                          </ul>
                        )}
                        {section.id === 'd10-analysis' && (
                          <ul>
                            <li>D10 chart planetary positions</li>
                            <li>10th lord in D10</li>
                            <li>D10 ascendant analysis</li>
                            <li>Career-specific yogas in D10</li>
                          </ul>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
        
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

  
  const renderTabContent = () => {
    if (loading) {
      return (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Analyzing your career prospects...</p>
        </div>
      );
    }
    
    if (error) {
      return (
        <div className="error-state">
          <h3>⚠️ Analysis Error</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry Analysis</button>
        </div>
      );
    }
    
    switch (activeTab) {
      case 'personality':
        return renderCareerPersonality();
      case 'professions':
        return renderProfessions();
      case 'timing':
        return renderTiming();
      case 'strategy':
        return renderStrategy();
      case 'nakshatras':
        return renderNakshatraAnalysis();
      case 'complete':
        return renderCompleteAnalysis();
      default:
        return renderCareerPersonality();
    }
  };

  return (
    <div className="career-analysis-tab">
      <div className="tab-navigation">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default CareerAnalysisTab;