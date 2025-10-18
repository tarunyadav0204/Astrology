import React, { useState, useEffect } from 'react';
import './MarriageAnalysisTab.css';
import { apiService } from '../../services/apiService';

const MarriageAnalysisTab = ({ chartData, birthDetails }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisType, setAnalysisType] = useState('single');

  useEffect(() => {
    if (chartData && birthDetails) {
      fetchMarriageAnalysis();
    }
  }, [chartData, birthDetails, analysisType]);

  const fetchMarriageAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.getMarriageAnalysis({
        chart_data: chartData,
        birth_details: birthDetails,
        analysis_type: analysisType
      });
      setAnalysis(response);
    } catch (err) {
      setError('Failed to fetch marriage analysis');
      console.error('Marriage analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="marriage-analysis-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Analyzing marriage prospects...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="marriage-analysis-container">
        <div className="error-state">
          <p>{error}</p>
          <button onClick={fetchMarriageAnalysis} className="retry-btn">
            Retry Analysis
          </button>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="marriage-analysis-container">
        <div className="no-data-state">
          <p>No marriage analysis available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="marriage-analysis-container">
      <div className="analysis-header">
        <h2>💍 Marriage Analysis</h2>
        <div className="analysis-type-selector">
          <button 
            className={`type-btn ${analysisType === 'single' ? 'active' : ''}`}
            onClick={() => setAnalysisType('single')}
          >
            Single Chart
          </button>
          <button 
            className={`type-btn ${analysisType === 'compatibility' ? 'active' : ''}`}
            onClick={() => setAnalysisType('compatibility')}
          >
            Compatibility
          </button>
        </div>
      </div>

      {analysisType === 'single' && (
        <SingleChartAnalysis analysis={analysis} chartData={chartData} birthDetails={birthDetails} />
      )}

      {analysisType === 'compatibility' && (
        <CompatibilityAnalysis analysis={analysis} />
      )}
    </div>
  );
};

const SingleChartAnalysis = ({ analysis, chartData, birthDetails }) => {
  const [activeTab, setActiveTab] = useState('scoring');

  return (
    <div className="single-chart-analysis">
      <div className="analysis-tabs">
        <button 
          className={`tab-btn ${activeTab === 'scoring' ? 'active' : ''}`}
          onClick={() => setActiveTab('scoring')}
        >
          📊 Scoring Analysis
        </button>
        <button 
          className={`tab-btn ${activeTab === 'spouse' ? 'active' : ''}`}
          onClick={() => setActiveTab('spouse')}
        >
          💕 Know Your Spouse
        </button>
      </div>

      {activeTab === 'scoring' && (
        <div className="tab-content scoring-tab">
          <div className="analysis-section">
            <h3>Marriage Analysis Results</h3>
            <p>Analysis results will be displayed here...</p>
          </div>
        </div>
      )}

      {activeTab === 'spouse' && (
        <div className="tab-content spouse-tab">
          <div className="analysis-section">
            <h3>Spouse Analysis</h3>
            <p>Spouse analysis will be displayed here...</p>
          </div>
        </div>
      )}
    </div>
  );
};

const CompatibilityAnalysis = ({ analysis }) => {
  return (
    <div className="compatibility-analysis">
      <div className="coming-soon">
        <h3>🔄 Compatibility Analysis</h3>
        <p>Two-chart compatibility analysis coming soon...</p>
        <p>This will include Guna Milan (Ashtakoot) scoring and detailed compatibility assessment.</p>
      </div>
    </div>
  );
};

export default MarriageAnalysisTab;