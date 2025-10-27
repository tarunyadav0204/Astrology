import React from 'react';

const CareerStrategy = ({ careerData }) => {
  if (!careerData?.growth_strategy) return <div>Loading strategy...</div>;
  
  const strategy = careerData.growth_strategy;
  
  return (
    <div className="growth-strategy">
      <h3>🎯 Career Growth Strategy</h3>
      
      <div className="action-plan">
        <h4>📋 Action Plan</h4>
        <ol>
          {strategy.action_plan.map((action, index) => (
            <li key={index}>{action}</li>
          ))}
        </ol>
      </div>
      
      <div className="favorable-yogas">
        <h4>✨ Your Career Yogas</h4>
        {strategy.favorable_yogas.length > 0 ? (
          strategy.favorable_yogas.map((yoga, index) => (
            <div key={index} className="yoga-item">
              <strong>{yoga.name}</strong>
              <p>{yoga.description}</p>
              <span className="yoga-strength">{yoga.strength} strength</span>
            </div>
          ))
        ) : (
          <p>Focus on building career yogas through planetary strengthening</p>
        )}
      </div>
      
      <div className="obstacles">
        <h4>⚠️ Career Obstacles</h4>
        {strategy.career_obstacles.length > 0 ? (
          strategy.career_obstacles.map((obstacle, index) => (
            <div key={index} className="obstacle-item">
              <strong>{obstacle.type}</strong>
              <p>{obstacle.description}</p>
              <p><em>Remedy: {obstacle.remedy}</em></p>
            </div>
          ))
        ) : (
          <p>No major obstacles identified - clear path ahead!</p>
        )}
      </div>
      
      <div className="remedial-measures">
        <h4>🔧 Remedial Measures</h4>
        <ul>
          {strategy.remedial_measures.map((remedy, index) => (
            <li key={index}>{remedy}</li>
          ))}
        </ul>
      </div>
      
      {careerData.yogi_analysis && (
        <div className="yogi-analysis">
          <h4>🌟 Yogi Points Analysis</h4>
          <div className="yogi-summary">
            <div className="yogi-item">
              <strong>Yogi Lord:</strong> {careerData.yogi_analysis.career_impact.yogi_lord}
              <span className={`impact-score ${careerData.yogi_analysis.career_impact.yogi_impact > 60 ? 'positive' : 'neutral'}`}>
                Impact: {careerData.yogi_analysis.career_impact.yogi_impact}%
              </span>
            </div>
            <div className="yogi-item">
              <strong>Avayogi Lord:</strong> {careerData.yogi_analysis.career_impact.avayogi_lord}
              <span className={`impact-score ${careerData.yogi_analysis.career_impact.avayogi_impact > 60 ? 'negative' : 'neutral'}`}>
                Obstacle: {careerData.yogi_analysis.career_impact.avayogi_impact}%
              </span>
            </div>
            <div className="yogi-item">
              <strong>Dagdha Lord:</strong> {careerData.yogi_analysis.career_impact.dagdha_lord}
              <span className={`impact-score ${careerData.yogi_analysis.career_impact.dagdha_impact > 60 ? 'negative' : 'neutral'}`}>
                Destruction: {careerData.yogi_analysis.career_impact.dagdha_impact}%
              </span>
            </div>
            <div className="yogi-item">
              <strong>Tithi Shunya:</strong> {careerData.yogi_analysis.yogi_points.tithi_shunya_rashi.lord}
              <span className="impact-score neutral">
                Void: {careerData.yogi_analysis.yogi_points.tithi_shunya_rashi.sign_name}
              </span>
            </div>
          </div>
          <div className="yogi-interpretation">
            <h5>Career Impact:</h5>
            <ul>
              {careerData.yogi_analysis.interpretation.map((insight, index) => (
                <li key={index}>{insight}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
      
      {careerData.badhaka_analysis && (
        <div className="badhaka-analysis">
          <h4>⚠️ Badhaka (Career Obstacles)</h4>
          {careerData.badhaka_analysis.career_impact.has_impact ? (
            <div className="badhaka-details">
              <div className="badhaka-summary">
                <div className="badhaka-item">
                  <strong>Badhaka Lord:</strong> {careerData.badhaka_analysis.career_impact.badhaka_lord}
                  <span className={`impact-score ${careerData.badhaka_analysis.career_impact.impact_score > 50 ? 'negative' : 'neutral'}`}>
                    Impact: {careerData.badhaka_analysis.career_impact.impact_score}%
                  </span>
                </div>
                <div className="badhaka-item">
                  <strong>Obstacle Nature:</strong> {careerData.badhaka_analysis.career_impact.effects.nature}
                </div>
                <div className="badhaka-item">
                  <strong>Description:</strong> {careerData.badhaka_analysis.career_impact.effects.description}
                </div>
              </div>
              <div className="badhaka-interpretation">
                <h5>Career Obstacles:</h5>
                <ul>
                  {careerData.badhaka_analysis.interpretation.map((insight, index) => (
                    <li key={index}>{insight}</li>
                  ))}
                </ul>
              </div>
              <div className="badhaka-remedies">
                <h5>Remedial Approaches:</h5>
                <ul>
                  {careerData.badhaka_analysis.career_impact.effects.remedies.map((remedy, index) => (
                    <li key={index}>{remedy}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <p className="positive">✓ No significant Badhaka obstacles in career path</p>
          )}
        </div>
      )}
    </div>
  );
};

export default CareerStrategy;