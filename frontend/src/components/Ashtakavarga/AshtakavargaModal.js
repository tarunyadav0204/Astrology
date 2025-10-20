import React, { useState, useEffect } from 'react';
import './AshtakavargaModal.css';
import { API_BASE_URL } from '../../config';

const AshtakavargaModal = ({ isOpen, onClose, birthData, chartType, transitDate }) => {
  const [ashtakavargaData, setAshtakavargaData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('sarva');

  const signNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

  useEffect(() => {
    if (isOpen && birthData) {
      fetchAshtakavarga();
    }
  }, [isOpen, birthData, chartType]);

  const fetchAshtakavarga = async () => {
    setLoading(true);
    const apiUrl = `${API_BASE_URL}/api/calculate-ashtakavarga`;
    console.log('Fetching Ashtakavarga data...', { birthData, chartType, apiUrl });
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: birthData,
          chart_type: chartType,
          transit_date: transitDate
        })
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Ashtakavarga data received:', data);
      setAshtakavargaData(data);
    } catch (error) {
      console.error('Error fetching Ashtakavarga:', error);
      setAshtakavargaData(null);
    } finally {
      setLoading(false);
    }
  };

  const getTabsForChartType = () => {
    const baseTabs = [
      { id: 'sarva', label: 'Sarvashtakavarga' },
      { id: 'individual', label: 'Individual Charts' }
    ];

    if (chartType === 'lagna') {
      return [...baseTabs, { id: 'analysis', label: 'Life Analysis' }];
    } else if (chartType === 'navamsa') {
      return [...baseTabs, { id: 'analysis', label: 'Marriage Analysis' }];
    } else if (chartType === 'transit') {
      return [...baseTabs, { id: 'analysis', label: 'Timing Analysis' }];
    }
    
    return [...baseTabs, { id: 'analysis', label: 'General Analysis' }];
  };

  const renderSarvashtakavarga = () => {
    if (!ashtakavargaData) return null;

    const { sarvashtakavarga, total_bindus } = ashtakavargaData.ashtakavarga;

    return (
      <div className="sarva-chart">
        <h3>Sarvashtakavarga ({total_bindus} total bindus)</h3>
        <div className="bindu-grid">
          {signNames.map((sign, index) => (
            <div key={index} className={`bindu-cell ${sarvashtakavarga[index] >= 30 ? 'strong' : sarvashtakavarga[index] <= 25 ? 'weak' : 'average'}`}>
              <div className="sign-name">{sign}</div>
              <div className="bindu-count">{sarvashtakavarga[index]}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderIndividualCharts = () => {
    if (!ashtakavargaData) return null;

    const { individual_charts } = ashtakavargaData.ashtakavarga;

    return (
      <div className="individual-charts">
        <h3>Individual Planet Charts</h3>
        {Object.entries(individual_charts).map(([planet, data]) => (
          <div key={planet} className="planet-chart">
            <h4>{planet} ({data.total} bindus)</h4>
            <div className="bindu-row">
              {signNames.map((sign, index) => {
                const count = data.bindus[index];
                let className = 'mini-bindu ';
                if (count >= 4) className += 'high-bindu';
                else if (count >= 2) className += 'medium-bindu';
                else className += 'low-bindu';
                
                return (
                  <div key={index} className={className}>
                    <span className="mini-sign">{sign.slice(0, 3)}</span>
                    <span className="mini-count">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
        <div style={{ height: '120px' }}></div>
      </div>
    );
  };

  const renderAnalysis = () => {
    if (!ashtakavargaData) return null;

    const { analysis } = ashtakavargaData;

    return (
      <div className="analysis-content">
        <h3>Analysis</h3>
        {analysis.strongest_sign && (
          <div className="strength-analysis">
            <div className="strong-sign">
              <strong>Strongest Sign:</strong> {analysis.strongest_sign.name} ({analysis.strongest_sign.bindus} bindus)
            </div>
            <div className="weak-sign">
              <strong>Weakest Sign:</strong> {analysis.weakest_sign.name} ({analysis.weakest_sign.bindus} bindus)
            </div>
          </div>
        )}
        
        {analysis.recommendations && (
          <div className="recommendations">
            <h4>Recommendations:</h4>
            <ul>
              {analysis.recommendations.map((rec, index) => (
                <li key={index}>{rec}</li>
              ))}
            </ul>
          </div>
        )}

        {analysis.focus && (
          <div className="focus-area">
            <h4>Focus Area:</h4>
            <p>{analysis.focus}</p>
            <p>{analysis.analysis}</p>
          </div>
        )}
        <div style={{ height: '120px' }}></div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="ashtakavarga-modal-overlay" onClick={onClose}>
      <div className="ashtakavarga-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Ashtakavarga Analysis - {chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-tabs">
          {getTabsForChartType().map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="modal-content">
          {loading ? (
            <div className="loading">Calculating Ashtakavarga...</div>
          ) : !ashtakavargaData ? (
            <div className="loading">
              <p>Failed to load Ashtakavarga data. Please try again.</p>
              <p style={{fontSize: '0.8rem', color: '#666', marginTop: '10px'}}>
                Debug: Check browser console for errors
              </p>
            </div>
          ) : (
            <>
              {activeTab === 'sarva' && renderSarvashtakavarga()}
              {activeTab === 'individual' && renderIndividualCharts()}
              {activeTab === 'analysis' && renderAnalysis()}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AshtakavargaModal;