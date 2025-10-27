import React, { useState } from 'react';
import { careerService } from '../../services/careerService';

const CareerPersonality = ({ birthDetails }) => {
  const [leadershipData, setLeadershipData] = useState(null);
  const [leadershipLoading, setLeadershipLoading] = useState(false);
  const [workStyleData, setWorkStyleData] = useState(null);
  const [workStyleLoading, setWorkStyleLoading] = useState(false);
  const [soloTeamData, setSoloTeamData] = useState(null);
  const [soloTeamLoading, setSoloTeamLoading] = useState(false);
  const [expandedQuestions, setExpandedQuestions] = useState({});
  
  React.useEffect(() => {
    loadLeadershipAnalysis();
    loadWorkStyleAnalysis();
    loadSoloTeamAnalysis();
  }, [birthDetails]);

  const loadLeadershipAnalysis = async () => {
    if (!birthDetails || leadershipData || leadershipLoading) return;
    
    setLeadershipLoading(true);
    try {
      const data = await careerService.getLeadershipAnalysis(birthDetails);
      setLeadershipData(data.leadership_analysis || data);
    } catch (error) {
      console.error('Error loading leadership analysis:', error);
      setLeadershipData({ error: 'Failed to load analysis' });
    } finally {
      setLeadershipLoading(false);
    }
  };

  const loadWorkStyleAnalysis = async () => {
    if (!birthDetails || workStyleData || workStyleLoading) return;
    
    setWorkStyleLoading(true);
    try {
      const data = await careerService.getWorkStyleAnalysis(birthDetails);
      setWorkStyleData(data.work_style_analysis || data);
    } catch (error) {
      console.error('Error loading work style analysis:', error);
      setWorkStyleData({ error: 'Failed to load analysis' });
    } finally {
      setWorkStyleLoading(false);
    }
  };

  const loadSoloTeamAnalysis = async () => {
    if (!birthDetails || soloTeamData || soloTeamLoading) return;
    
    setSoloTeamLoading(true);
    try {
      const data = await careerService.getSoloTeamAnalysis(birthDetails);
      setSoloTeamData(data.solo_team_analysis || data);
    } catch (error) {
      console.error('Error loading solo vs team analysis:', error);
      setSoloTeamData({ error: 'Failed to load analysis' });
    } finally {
      setSoloTeamLoading(false);
    }
  };

  const toggleQuestion = (questionId) => {
    setExpandedQuestions(prev => ({
      ...prev,
      [questionId]: !prev[questionId]
    }));
  };

  const questions = [
    {
      id: 'leadership',
      icon: '🤔',
      question: 'Are You a Leader or Team Player?',
      bgColor: 'rgba(255, 107, 53, 0.05)',
      borderColor: 'rgba(255, 107, 53, 0.2)',
      hasAnalysis: true,
      loading: leadershipLoading,
      data: leadershipData
    },
    {
      id: 'creative',
      icon: '🎨',
      question: 'Do You Prefer Creative or Structured Work?',
      bgColor: 'rgba(156, 39, 176, 0.05)',
      borderColor: 'rgba(156, 39, 176, 0.2)',
      hasAnalysis: true,
      loading: workStyleLoading,
      data: workStyleData
    },
    {
      id: 'teamwork',
      icon: '💼',
      question: 'Do You Work Better Alone or in Teams?',
      bgColor: 'rgba(33, 150, 243, 0.05)',
      borderColor: 'rgba(33, 150, 243, 0.2)',
      hasAnalysis: true,
      loading: soloTeamLoading,
      data: soloTeamData
    }
  ];

  return (
    <div className="career-personality">
      <h3>👤 What Type of Worker Are You?</h3>
      <p>Based on your birth chart, here's how you naturally approach work and career</p>
      
      <div className="personality-questions">
        {questions.map((q) => (
          <div 
            key={q.id} 
            className="personality-question-card"
            style={{ 
              backgroundColor: q.bgColor,
              borderColor: q.borderColor
            }}
          >
            <div 
              className="question-header"
              onClick={() => toggleQuestion(q.id)}
            >
              <div className="question-title">
                <span className="question-icon">{q.icon}</span>
                <h4>{q.question}</h4>
              </div>
              <span className={`expand-arrow ${expandedQuestions[q.id] ? 'expanded' : ''}`}>▼</span>
            </div>
            
            {expandedQuestions[q.id] && (
              <div className="question-content">
                {q.hasAnalysis ? (
                  q.loading ? (
                    <div className="analysis-loading">
                      <div className="mini-spinner"></div>
                      <p>{q.id === 'leadership' ? 'Analyzing your leadership tendencies...' : 'Analyzing your work style preferences...'}</p>
                    </div>
                  ) : q.data && !q.data.error ? (
                    q.id === 'leadership' ? (
                      <div className="leadership-analysis">
                      <div className="tendency-header">
                        <span className="tendency-icon">
                          {q.data.primary_tendency === 'Leader' ? '👑' : 
                           q.data.primary_tendency === 'Team Player' ? '🤝' : '⚖️'}
                        </span>
                        <div className="tendency-info">
                          <h5>You are a {q.data.tendency_strength} {q.data.primary_tendency}</h5>
                          <div className="indices">
                            <span className="leadership-index">Leadership: {q.data.leadership_index}</span>
                            <span className="team-index">Team: {q.data.team_index}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="hierarchy-behaviors">
                        <h6>How You Behave in Different Roles:</h6>
                        
                        {q.data.hierarchy_behaviors?.as_subordinate && (
                          <div className="behavior-section">
                            <strong>👤 As a Subordinate:</strong>
                            <ul>
                              {q.data.hierarchy_behaviors.as_subordinate.map((item, index) => (
                                <li key={index}>
                                  <div className="behavior-text">{typeof item === 'string' ? item : item.behavior}</div>
                                  {typeof item === 'object' && item.reason && (
                                    <div className="behavior-reason">{item.reason}</div>
                                  )}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {q.data.hierarchy_behaviors?.as_peer && (
                          <div className="behavior-section">
                            <strong>🤝 As a Peer:</strong>
                            <ul>
                              {q.data.hierarchy_behaviors.as_peer.map((item, index) => (
                                <li key={index}>
                                  <div className="behavior-text">{typeof item === 'string' ? item : item.behavior}</div>
                                  {typeof item === 'object' && item.reason && (
                                    <div className="behavior-reason">{item.reason}</div>
                                  )}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {q.data.hierarchy_behaviors?.as_leader && (
                          <div className="behavior-section">
                            <strong>👑 As a Leader:</strong>
                            <ul>
                              {q.data.hierarchy_behaviors.as_leader.map((item, index) => (
                                <li key={index}>
                                  <div className="behavior-text">{typeof item === 'string' ? item : item.behavior}</div>
                                  {typeof item === 'object' && item.reason && (
                                    <div className="behavior-reason">{item.reason}</div>
                                  )}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                      
                      {q.data.yogi_analysis && (
                        <div className="yogi-badhaka-analysis">
                          <h6>🌟 Yogi & Badhaka Impact on Leadership:</h6>
                          
                          <div className="yogi-section">
                            <strong>Yogi Analysis:</strong>
                            <ul>
                              {q.data.yogi_analysis.interpretation?.map((item, index) => (
                                <li key={index}>{item}</li>
                              )) || []}
                            </ul>
                          </div>
                          
                          <div className="badhaka-section">
                            <strong>Badhaka Analysis:</strong>
                            <ul>
                              {q.data.badhaka_analysis.interpretation?.map((item, index) => (
                                <li key={index}>{item}</li>
                              )) || []}
                            </ul>
                          </div>
                        </div>
                      )}
                      
                      <div className="calculation-breakdown">
                        <h6>🔍 How This Was Calculated:</h6>
                        <div className="breakdown-grid">
                          <div className="leadership-factors">
                            <strong>Leadership Factors:</strong>
                            <ul>
                              {q.data.calculation_details.leadership_factors?.map((factor, index) => (
                                <li key={index}>{factor}</li>
                              )) || []}
                            </ul>
                          </div>
                          <div className="team-factors">
                            <strong>Team Factors:</strong>
                            <ul>
                              {q.data.calculation_details.team_factors?.map((factor, index) => (
                                <li key={index}>{factor}</li>
                              )) || []}
                            </ul>
                          </div>
                        </div>
                        
                        <div className="planetary-positions">
                          <strong>Key Planetary Positions:</strong>
                          <div className="planet-grid">
                            {Object.entries(q.data.calculation_details?.key_planetary_positions || {}).map(([planet, position]) => (
                              <span key={planet} className="planet-position">{planet}: {position}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                    ) : q.id === 'creative' ? (
                      <div className="workstyle-analysis">
                        <div className="tendency-header">
                          <span className="tendency-icon">
                            {q.data.primary_preference === 'Creative' ? '🎨' : 
                             q.data.primary_preference === 'Structured' ? '📊' : '⚖️'}
                          </span>
                          <div className="tendency-info">
                            <h5>You prefer {q.data.preference_strength} {q.data.primary_preference} Work</h5>
                            <div className="indices">
                              <span className="creative-index">Creative: {q.data.creative_index}</span>
                              <span className="structured-index">Structured: {q.data.structured_index}</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="work-preferences">
                          <div className="preference-section">
                            <strong>🎨 Creative Work Behaviors:</strong>
                            <ul>
                              {q.data.work_behaviors?.creative_behaviors?.map((item, index) => (
                                <li key={index}>
                                  <div className="behavior-text">{typeof item === 'string' ? item : item.behavior}</div>
                                  {typeof item === 'object' && item.reason && (
                                    <div className="behavior-reason">{item.reason}</div>
                                  )}
                                </li>
                              )) || []}
                            </ul>
                          </div>
                          
                          <div className="preference-section">
                            <strong>📊 Structured Work Behaviors:</strong>
                            <ul>
                              {q.data.work_behaviors?.structured_behaviors?.map((item, index) => (
                                <li key={index}>
                                  <div className="behavior-text">{typeof item === 'string' ? item : item.behavior}</div>
                                  {typeof item === 'object' && item.reason && (
                                    <div className="behavior-reason">{item.reason}</div>
                                  )}
                                </li>
                              )) || []}
                            </ul>
                          </div>
                          
                          <div className="preference-section">
                            <strong>💼 Ideal Work Environment:</strong>
                            <ul>
                              {q.data.work_behaviors?.work_environment?.map((env, index) => (
                                <li key={index}>{env}</li>
                              )) || []}
                            </ul>
                          </div>
                          
                          <div className="preference-section">
                            <strong>🎯 Project Approach:</strong>
                            <ul>
                              {q.data.work_behaviors?.project_approach?.map((approach, index) => (
                                <li key={index}>{approach}</li>
                              )) || []}
                            </ul>
                          </div>
                        </div>
                        
                        <div className="calculation-breakdown">
                          <h6>🔍 How This Was Calculated:</h6>
                          <div className="breakdown-grid">
                            <div className="creative-factors">
                              <strong>Creative Factors:</strong>
                              <ul>
                                {q.data.calculation_details?.creative_factors?.map((factor, index) => (
                                  <li key={index}>{factor}</li>
                                )) || []}
                              </ul>
                            </div>
                            <div className="structured-factors">
                              <strong>Structured Factors:</strong>
                              <ul>
                                {q.data.calculation_details?.structured_factors?.map((factor, index) => (
                                  <li key={index}>{factor}</li>
                                )) || []}
                              </ul>
                            </div>
                          </div>
                          
                          <div className="planetary-positions">
                            <strong>Key Planetary Influences:</strong>
                            <div className="planet-grid">
                              {Object.entries(q.data.calculation_details?.key_planetary_influences || {}).map(([planet, position]) => (
                                <span key={planet} className="planet-position">{planet}: {position}</span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : q.id === 'teamwork' ? (
                      <div className="soloteam-analysis">
                        <div className="tendency-header">
                          <span className="tendency-icon">
                            {q.data.primary_preference === 'Solo' ? '💻' : 
                             q.data.primary_preference === 'Team' ? '👥' : '⚖️'}
                          </span>
                          <div className="tendency-info">
                            <h5>You prefer {q.data.preference_strength} {q.data.primary_preference} Work</h5>
                            <div className="indices">
                              <span className="solo-index">Solo: {q.data.solo_index}</span>
                              <span className="team-index">Team: {q.data.team_index}</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="work-preferences">
                          <div className="preference-section">
                            <strong>💻 Solo Work Behaviors:</strong>
                            <ul>
                              {q.data.work_behaviors?.solo_behaviors?.map((item, index) => (
                                <li key={index}>
                                  <div className="behavior-text">{typeof item === 'string' ? item : item.behavior}</div>
                                  {typeof item === 'object' && item.reason && (
                                    <div className="behavior-reason">{item.reason}</div>
                                  )}
                                </li>
                              )) || []}
                            </ul>
                          </div>
                          
                          <div className="preference-section">
                            <strong>👥 Team Work Behaviors:</strong>
                            <ul>
                              {q.data.work_behaviors?.team_behaviors?.map((item, index) => (
                                <li key={index}>
                                  <div className="behavior-text">{typeof item === 'string' ? item : item.behavior}</div>
                                  {typeof item === 'object' && item.reason && (
                                    <div className="behavior-reason">{item.reason}</div>
                                  )}
                                </li>
                              )) || []}
                            </ul>
                          </div>
                          
                          <div className="preference-section">
                            <strong>🤝 Collaboration Style:</strong>
                            <ul>
                              {q.data.work_behaviors?.collaboration_style?.map((style, index) => (
                                <li key={index}>{style}</li>
                              )) || []}
                            </ul>
                          </div>
                          
                          <div className="preference-section">
                            <strong>💬 Communication Approach:</strong>
                            <ul>
                              {q.data.work_behaviors?.communication_approach?.map((approach, index) => (
                                <li key={index}>{approach}</li>
                              )) || []}
                            </ul>
                          </div>
                        </div>
                        
                        <div className="calculation-breakdown">
                          <h6>🔍 How This Was Calculated:</h6>
                          <div className="breakdown-grid">
                            <div className="solo-factors">
                              <strong>Solo Factors:</strong>
                              <ul>
                                {q.data.calculation_details?.solo_factors?.map((factor, index) => (
                                  <li key={index}>{factor}</li>
                                )) || []}
                              </ul>
                            </div>
                            <div className="team-factors">
                              <strong>Team Factors:</strong>
                              <ul>
                                {q.data.calculation_details?.team_factors?.map((factor, index) => (
                                  <li key={index}>{factor}</li>
                                )) || []}
                              </ul>
                            </div>
                          </div>
                          
                          <div className="planetary-positions">
                            <strong>Key Planetary Influences:</strong>
                            <div className="planet-grid">
                              {Object.entries(q.data.calculation_details?.key_planetary_influences || {}).map(([planet, position]) => (
                                <span key={planet} className="planet-position">{planet}: {position}</span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : null
                  ) : q.data && q.data.error ? (
                    <div className="analysis-error">
                      <p>Unable to load {q.id === 'leadership' ? 'leadership' : 'work style'} analysis. Please try refreshing the page.</p>
                    </div>
                  ) : (
                    <div className="analysis-loading">
                      <div className="mini-spinner"></div>
                      <p>Loading {q.id === 'leadership' ? 'leadership' : 'work style'} analysis...</p>
                    </div>
                  )
                ) : (
                  <div className="coming-soon">
                    <p>Coming soon - detailed analysis based on your birth chart.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default CareerPersonality;