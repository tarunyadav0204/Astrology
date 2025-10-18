import React from 'react';

const GunaScoreCard = ({ gunaMilan, overallScore }) => {
  const getScoreColor = (score, maxScore) => {
    const percentage = (score / maxScore) * 100;
    if (percentage >= 80) return '#4caf50';
    if (percentage >= 60) return '#ff9800';
    return '#f44336';
  };

  const getGradeColor = (grade) => {
    switch (grade) {
      case 'Excellent': return '#4caf50';
      case 'Good': return '#8bc34a';
      case 'Average': return '#ff9800';
      default: return '#f44336';
    }
  };

  return (
    <div className="guna-score-card">
      <div className="guna-breakdown">
        <h4>Ashtakoot Guna Milan ({gunaMilan.total_score}/36)</h4>
        <div className="koots-grid">
          {Object.entries(gunaMilan.koots).map(([kootName, kootData]) => (
            <div key={kootName} className="koot-item">
              <div className="koot-header">
                <span className="koot-name">{kootName.replace('_', ' ').toUpperCase()}</span>
                <span 
                  className="koot-score"
                  style={{ color: getScoreColor(kootData.score, kootData.max_score) }}
                >
                  {kootData.score}/{kootData.max_score}
                </span>
              </div>
              <div className="koot-description">{kootData.description}</div>
              {kootData.interpretation && (
                <div className="koot-interpretation">
                  {kootData.interpretation.split('\n').map((line, idx) => (
                    <p key={idx} className={line.startsWith('**') ? 'interpretation-header' : 'interpretation-text'}>
                      {line.replace(/\*\*/g, '')}
                    </p>
                  ))}
                </div>
              )}
              <div className="koot-progress">
                <div 
                  className="koot-progress-bar"
                  style={{ 
                    width: `${(kootData.score / kootData.max_score) * 100}%`,
                    backgroundColor: getScoreColor(kootData.score, kootData.max_score)
                  }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {gunaMilan.critical_issues && gunaMilan.critical_issues.length > 0 && (
        <div className="critical-issues">
          <h4>⚠️ Critical Issues</h4>
          <ul>
            {gunaMilan.critical_issues.map((issue, index) => (
              <li key={index}>{issue}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default GunaScoreCard;