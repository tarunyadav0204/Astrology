import React, { useState, useEffect } from 'react';
import './NameOptimizer.css';

const NameOptimizer = ({ initialName, onOptimize }) => {
  const [name, setName] = useState(initialName || '');
  const [system, setSystem] = useState('chaldean'); // 'chaldean' or 'pythagorean'
  const [result, setResult] = useState(null);
  const [isTyping, setIsTyping] = useState(false);

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
        <h3>Name Alchemist</h3>
        <p>Test the vibration of your name spelling</p>
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
        <div className={`verdict-box ${getVerdictClass(result.compound_number)}`}>
          <div className="verdict-number">
            {result.compound_number}
          </div>
          <div className="verdict-text">
            <h4>{typeof result.verdict === 'object' ? result.verdict.title : result.verdict}</h4>
            <span>Reduced to Single Digit: {result.single_number}</span>
            {typeof result.verdict === 'object' && result.verdict.reason && (
              <small style={{display: 'block', marginTop: '5px', color: 'white'}}>{result.verdict.reason}</small>
            )}
          </div>
        </div>
      )}

      {/* Show suggestions only if current name is NOT lucky */}
      {result && !result.is_lucky && result.remedial_suggestions && (
        <div className="suggestions-list">
          <h5 style={{color: '#4caf50', margin: '0 0 10px 0'}}>✨ Lucky Variations found:</h5>
          {result.remedial_suggestions.map((sug, i) => (
            <div 
              key={i} 
              className="suggestion-chip"
              onClick={() => setName(sug.original)}
            >
              <span style={{fontWeight: 'bold', letterSpacing: '1px'}}>{sug.original}</span>
              <span style={{color: '#4caf50', fontWeight: 'bold'}}>
                {sug.compound} ({typeof sug.verdict === 'object' ? sug.verdict.title : sug.verdict.split('(')[0]})
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NameOptimizer;