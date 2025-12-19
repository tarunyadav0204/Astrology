import React, { useState, useEffect } from 'react';
import './NameOptimizer.css';

const NameOptimizer = ({ initialName, onOptimize }) => {
  const [name, setName] = useState(initialName || '');
  const [system, setSystem] = useState('chaldean');
  const [result, setResult] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  // Debounce API call to avoid spamming while typing
  useEffect(() => {
    const timer = setTimeout(() => {
      if (name.length > 2) {
        handleOptimization(name);
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [name, system]);

  const handleOptimization = async (inputName) => {
    // In a real app, this calls your API: /numerology/optimize-name
    // Here I'm simulating the response structure from our Python backend logic
    if (onOptimize) {
      const data = await onOptimize(inputName, system);
      setResult(data);
    }
  };

  const getVerdictClass = (compound) => {
    // Lucky numbers list (matching python logic)
    const lucky = [1, 3, 5, 6, 10, 14, 15, 19, 21, 23, 24, 27, 32, 37, 41, 45, 46, 50];
    const unlucky = [12, 16, 18, 22, 26, 28, 29, 35, 38, 43, 44, 48];
    
    if (lucky.includes(compound)) return 'lucky';
    if (unlucky.includes(compound)) return 'unlucky';
    return 'neutral';
  };

  return (
    <div className="optimizer-card">
      <div className="optimizer-header">
        <h3>🎯 Name Impact Score</h3>
        <p>See how your name affects first impressions & opportunities</p>
      </div>

      <div className="system-toggle">
        <button 
          className={`toggle-btn ${system === 'chaldean' ? 'active' : ''}`}
          onClick={() => setSystem('chaldean')}
        >
          Chaldean (Ancient)
        </button>
        <button 
          className={`toggle-btn ${system === 'pythagorean' ? 'active' : ''}`}
          onClick={() => setSystem('pythagorean')}
        >
          Pythagorean (Modern)
        </button>
      </div>
      
      <details className="system-explanation">
        <summary>🤔 Why do the systems give different results?</summary>
        <div className="system-comparison">
          <p><strong>Two Different Calculation Methods:</strong></p>
          
          <p><strong>Chaldean (Ancient):</strong> Uses numbers 1-8, excludes 9 as sacred. Based on sound vibrations. More accurate for spiritual/personal analysis.</p>
          
          <p><strong>Pythagorean (Modern):</strong> Uses numbers 1-9, based on alphabetical order. Better for Western names and business purposes.</p>
          
          <p><strong>Which should you trust?</strong></p>
          <p>• For personal/spiritual guidance: <strong>Chaldean</strong> (more ancient wisdom)</p>
          <p>• For business/professional names: <strong>Pythagorean</strong> (modern context)</p>
          <p>• If results conflict: Go with the system that feels more accurate to your experience</p>
          
          <p><strong>Remember:</strong> Your name is just one factor. Your actions and intentions matter more than numerology scores.</p>
        </div>
      </details>

      <div className="name-input-container">
        <input 
          type="text" 
          className="name-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="ENTER FULL NAME..."
        />
      </div>

      {result && (
        <div className="name-analysis">
          <div className={`impact-score ${getVerdictClass(result.compound_number)}`}>
            <div className="score-circle">
              <span className="score">{result.compound_number}</span>
              <span className="label">Compound</span>
            </div>
            <div className="score-meaning">
              <h4>{getVerdictClass(result.compound_number) === 'lucky' ? '✅ Strong Name Energy' : 
                   getVerdictClass(result.compound_number) === 'unlucky' ? '❌ Challenging Energy' : 
                   '⚠️ Neutral Energy'}</h4>
              <p>{getVerdictClass(result.compound_number) === 'lucky' ? 
                'Your name creates positive first impressions and attracts opportunities.' : 
                getVerdictClass(result.compound_number) === 'unlucky' ?
                'Your name may create obstacles. Consider the variations below for better energy.' :
                'Your name has balanced energy. You can enhance it with the suggestions below.'}
              </p>
            </div>
          </div>
          
          <button 
            className="details-toggle"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? 'Hide' : 'Show'} Technical Details
          </button>
          
          {showDetails && (
            <div className="technical-details">
              <p><strong>Compound Number:</strong> {result.compound_number}</p>
              <p><strong>Root Number:</strong> {result.single_number}</p>
              {typeof result.verdict === 'object' && result.verdict.description && (
                <p><strong>Traditional Meaning:</strong> {result.verdict.description}</p>
              )}
            </div>
          )}
        </div>
      )}

      {result && getVerdictClass(result.compound_number) !== 'lucky' && result.remedial_suggestions && (
        <div className="name-suggestions">
          <h4>🚀 Stronger Name Variations</h4>
          <p className="suggestion-intro">These variations could improve your name's impact:</p>
          {result.remedial_suggestions.slice(0, 3).map((sug, i) => (
            <div 
              key={i} 
              className="suggestion-card"
              onClick={() => setName(sug.original)}
            >
              <div className="suggestion-name">{sug.original}</div>
              <div className="suggestion-benefit">
                <span className="new-score">{sug.compound}</span>
                <span className="improvement">{getVerdictClass(sug.compound) === 'lucky' ? 'Lucky' : getVerdictClass(sug.compound) === 'neutral' ? 'Neutral' : 'Challenging'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {result && getVerdictClass(result.compound_number) === 'lucky' && (
        <div className="name-strengths">
          <h4>💪 Your Name's Strengths</h4>
          <div className="strength-tags">
            <span className="strength-tag">Creates Trust</span>
            <span className="strength-tag">Memorable</span>
            <span className="strength-tag">Professional Appeal</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default NameOptimizer;