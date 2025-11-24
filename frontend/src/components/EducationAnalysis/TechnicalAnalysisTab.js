import React from 'react';

const TechnicalAnalysisTab = ({ analysisData, onRefresh }) => {
  if (!analysisData) {
    return (
      <div className="no-data">
        <p>No analysis data available</p>
        <button onClick={onRefresh} className="refresh-btn">
          🔄 Refresh Analysis
        </button>
      </div>
    );
  }

  const { overall_score, house_analysis, planetary_analysis, yoga_analysis, ashtakavarga_analysis, shadbala_analysis, timing_analysis, subject_recommendations, remedies } = analysisData;

  return (
    <div className="technical-analysis">
      {/* Overall Score Section */}
      <div className="analysis-section overall-score">
        <h2>📈 Overall Education Strength</h2>
        <div className="score-display">
          <div className="score-circle">
            <span className="score-number">{overall_score.total_score}</span>
            <span className="score-grade">{overall_score.grade}</span>
          </div>
          <div className="score-breakdown">
            <div className="breakdown-item">
              <span className="label">House Strength:</span>
              <span className="value">{overall_score.breakdown.house_strength}/100</span>
            </div>
            <div className="breakdown-item">
              <span className="label">Planetary Strength:</span>
              <span className="value">{overall_score.breakdown.planetary_strength}/100</span>
            </div>
            <div className="breakdown-item">
              <span className="label">Yoga Strength:</span>
              <span className="value">{overall_score.breakdown.yoga_strength}/100</span>
            </div>
            <div className="breakdown-item">
              <span className="label">Ashtakavarga:</span>
              <span className="value">{overall_score.breakdown.ashtakavarga_strength}/100</span>
            </div>
          </div>
        </div>
      </div>

      {/* House Analysis Section */}
      <div className="analysis-section house-analysis">
        <h2>🏠 House Analysis</h2>
        <div className="houses-grid">
          {Object.entries(house_analysis).map(([houseNum, data]) => (
            <div key={houseNum} className="house-card">
              <div className="house-header">
                <h3>{houseNum}th House - {data.name}</h3>
                <span className={`grade-badge grade-${data.grade.toLowerCase()}`}>
                  {data.grade}
                </span>
              </div>
              <p className="house-description">{data.description}</p>
              <div className="strength-bar">
                <div 
                  className="strength-fill" 
                  style={{ width: `${data.strength}%` }}
                ></div>
                <span className="strength-text">{data.strength}/100</span>
              </div>
              <p className="interpretation">{data.interpretation}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Planetary Analysis Section */}
      <div className="analysis-section planetary-analysis">
        <h2>🪐 Planetary Analysis</h2>
        <div className="planets-grid">
          {Object.entries(planetary_analysis).map(([planet, data]) => (
            <div key={planet} className="planet-card">
              <div className="planet-header">
                <h3>{planet}</h3>
                <span className="planet-score">{data.score}/100</span>
              </div>
              <p className="planet-significance">{data.significance}</p>
              <div className="planet-details">
                <div className="detail-item">
                  <span className="label">Dignity:</span>
                  <span className={`dignity ${data.dignity}`}>{data.dignity}</span>
                </div>
                <div className="detail-item">
                  <span className="label">House:</span>
                  <span className="value">{data.house}</span>
                </div>
                {data.shadbala_grade && (
                  <div className="detail-item">
                    <span className="label">Shadbala:</span>
                    <span className={`shadbala-grade ${data.shadbala_grade.toLowerCase()}`}>
                      {data.shadbala_grade} ({data.shadbala_rupas} rupas)
                    </span>
                  </div>
                )}
                {data.states.length > 0 && (
                  <div className="planet-states">
                    {data.states.map((state, index) => (
                      <span key={index} className="state-tag">{state}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Yoga Analysis Section */}
      <div className="analysis-section yoga-analysis">
        <h2>🕉️ Educational Yogas</h2>
        {yoga_analysis.yogas_found.length > 0 ? (
          <div className="yogas-list">
            {yoga_analysis.yogas_found.map((yoga, index) => (
              <div key={index} className="yoga-card">
                <div className="yoga-header">
                  <h3>{yoga.name}</h3>
                  <span className={`strength-badge ${yoga.strength?.toLowerCase()}`}>
                    {yoga.strength}
                  </span>
                </div>
                <p className="yoga-description">{yoga.description}</p>
                {yoga.planets && (
                  <div className="yoga-planets">
                    <span className="label">Planets:</span>
                    <span className="planets">{yoga.planets.join(', ')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="no-yogas">
            <p>No specific educational yogas found in your chart.</p>
            <p>Focus on strengthening individual planetary positions.</p>
          </div>
        )}
      </div>

      {/* Ashtakavarga Analysis Section */}
      <div className="analysis-section ashtakavarga-analysis">
        <h2>📊 Ashtakavarga Analysis</h2>
        <div className="ashtakavarga-houses">
          {Object.entries(ashtakavarga_analysis).map(([houseNum, data]) => (
            <div key={houseNum} className="ashtakavarga-house-card">
              <div className="ashtakavarga-house-header">
                <h3>{houseNum}th House - {data.house_name}</h3>
                <div className="bindus-display">
                  <span className="bindus-count">{data.bindus}</span>
                  <span className={`bindus-strength ${data.strength.toLowerCase()}`}>
                    {data.strength}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Shadbala Analysis Section */}
      {shadbala_analysis && Object.keys(shadbala_analysis).length > 0 && (
        <div className="analysis-section shadbala-analysis">
          <h2>⚖️ Shadbala Analysis</h2>
          <div className="shadbala-grid">
            {Object.entries(shadbala_analysis).map(([planet, data]) => (
              <div key={planet} className="shadbala-card">
                <div className="shadbala-header">
                  <h3>{planet}</h3>
                  <span className={`grade-badge grade-${data.grade.toLowerCase()}`}>
                    {data.grade}
                  </span>
                </div>
                <div className="rupas-display">
                  <span className="rupas-count">{data.total_rupas}</span>
                  <span className="rupas-label">Rupas</span>
                </div>
                <p className="shadbala-interpretation">{data.interpretation}</p>
                <div className="components-summary">
                  <div className="component-item">
                    <span className="label">Positional:</span>
                    <span className="value">{data.components.sthana_bala}</span>
                  </div>
                  <div className="component-item">
                    <span className="label">Directional:</span>
                    <span className="value">{data.components.dig_bala}</span>
                  </div>
                  <div className="component-item">
                    <span className="label">Temporal:</span>
                    <span className="value">{data.components.kala_bala}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Subject Recommendations Section */}
      <div className="analysis-section subject-recommendations">
        <h2>📚 Subject Recommendations</h2>
        {Object.keys(subject_recommendations).length > 0 ? (
          <div className="subjects-grid">
            {Object.entries(subject_recommendations).map(([planet, data]) => (
              <div key={planet} className="subject-card">
                <div className="subject-header">
                  <h3>{planet}</h3>
                  <span className="strength-score">{data.strength}/100</span>
                </div>
                <p className="subject-reason">{data.reason}</p>
                <div className="subjects-list">
                  {data.subjects.map((subject, index) => (
                    <span key={index} className="subject-tag">{subject}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-recommendations">
            <p>Work on strengthening planetary positions for clearer subject recommendations.</p>
          </div>
        )}
      </div>



      {/* Remedies Section */}
      <div className="analysis-section remedies">
        <h2>🔮 Remedies & Recommendations</h2>
        {remedies.length > 0 ? (
          <div className="remedies-list">
            {remedies.map((remedy, index) => (
              <div key={index} className="remedy-card">
                <p>{remedy}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-remedies">
            <p>Your educational indicators are strong. Continue your current path with confidence.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TechnicalAnalysisTab;