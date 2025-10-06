import React, { useState } from 'react';
import { apiService } from '../../services/apiService';

const EventAnalyzer = ({ birthChart }) => {
  const [eventType, setEventType] = useState('dental_procedure');
  const [eventDate, setEventDate] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const eventTypes = [
    { id: 'dental_procedure', name: 'Dental Procedure' },
    { id: 'job_promotion', name: 'Job Promotion' },
    { id: 'marriage', name: 'Marriage' },
    { id: 'property_purchase', name: 'Property Purchase' },
    { id: 'health_issue', name: 'Health Issue' }
  ];

  const analyzeEvent = async () => {
    if (!eventDate || !birthChart) {
      alert('Please provide event date and birth chart');
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.analyzeEvent(birthChart, eventDate, eventType);
      setAnalysis(response);
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return '#4caf50';
    if (confidence >= 60) return '#ff9800';
    return '#f44336';
  };

  return (
    <div style={{ 
      padding: window.innerWidth <= 768 ? '10px' : '20px', 
      background: 'white', 
      borderRadius: '10px', 
      margin: window.innerWidth <= 768 ? '10px 0' : '20px 0',
      fontSize: window.innerWidth <= 768 ? '14px' : '16px'
    }}>
      <h3>Event Analysis</h3>
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: window.innerWidth <= 768 ? '1fr' : '1fr 1fr 1fr', 
        gap: '15px', 
        marginBottom: '20px' 
      }}>
        <div>
          <label>Event Type:</label>
          <select
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          >
            {eventTypes.map(type => (
              <option key={type.id} value={type.id}>{type.name}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label>Event Date:</label>
          <input
            type="date"
            value={eventDate}
            onChange={(e) => setEventDate(e.target.value)}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>
        
        <div style={{ display: 'flex', alignItems: 'end' }}>
          <button
            onClick={analyzeEvent}
            disabled={loading}
            style={{
              width: '100%',
              padding: '10px',
              background: '#e91e63',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Analyzing...' : 'Analyze Event'}
          </button>
        </div>
      </div>

      {analysis && (
        <div style={{ marginTop: '20px' }}>
          <div style={{
            background: '#f5f5f5',
            padding: '15px',
            borderRadius: '8px',
            marginBottom: '20px'
          }}>
            <h4 style={{ margin: '0 0 10px 0' }}>Analysis Summary</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span>Confidence Score:</span>
              <div style={{
                background: getConfidenceColor(analysis.total_confidence),
                color: 'white',
                padding: '5px 10px',
                borderRadius: '15px',
                fontWeight: 'bold'
              }}>
                {analysis.total_confidence}%
              </div>
            </div>
            <p style={{ marginTop: '10px' }}>{analysis.detailed_explanation}</p>
          </div>

          {analysis.primary_factors.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h4>Primary Factors</h4>
              {analysis.primary_factors.map((factor, index) => (
                <div key={index} style={{
                  background: '#e8f5e8',
                  padding: '10px',
                  borderRadius: '5px',
                  marginBottom: '10px'
                }}>
                  <strong>{factor.description}</strong>
                  <div style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
                    Weight: {factor.weight} | Confidence: {factor.confidence}%
                  </div>
                  <div style={{ fontSize: '14px', marginTop: '5px' }}>
                    {factor.explanation}
                  </div>
                </div>
              ))}
            </div>
          )}

          {analysis.dasha_activations.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h4>Dasha Activations</h4>
              {analysis.dasha_activations.map((factor, index) => (
                <div key={index} style={{
                  background: '#fff3e0',
                  padding: '10px',
                  borderRadius: '5px',
                  marginBottom: '10px'
                }}>
                  <strong>{factor.description}</strong>
                  <div style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
                    Weight: {factor.weight} | Confidence: {factor.confidence}%
                  </div>
                  <div style={{ fontSize: '14px', marginTop: '5px' }}>
                    {factor.explanation}
                  </div>
                </div>
              ))}
            </div>
          )}

          {analysis.transit_confirmations.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h4>Transit Confirmations</h4>
              {analysis.transit_confirmations.map((factor, index) => (
                <div key={index} style={{
                  background: '#e3f2fd',
                  padding: '10px',
                  borderRadius: '5px',
                  marginBottom: '10px'
                }}>
                  <strong>{factor.description}</strong>
                  <div style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
                    Weight: {factor.weight} | Confidence: {factor.confidence}%
                  </div>
                  <div style={{ fontSize: '14px', marginTop: '5px' }}>
                    {factor.explanation}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={{
            background: '#f0f0f0',
            padding: '15px',
            borderRadius: '8px',
            marginTop: '20px'
          }}>
            <h4>Classical Support</h4>
            <p style={{ fontStyle: 'italic' }}>{analysis.classical_support}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventAnalyzer;