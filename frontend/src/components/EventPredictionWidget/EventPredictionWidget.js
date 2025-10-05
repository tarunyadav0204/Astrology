import React, { useState, useEffect } from 'react';
import { useAstrology } from '../../context/AstrologyContext';
import { apiService } from '../../services/apiService';
import styled from 'styled-components';

const EventContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 1rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(233, 30, 99, 0.2);
  height: 100%;
  overflow-y: auto;
  
  h3 {
    color: #e91e63;
    margin-bottom: 1rem;
    font-size: 1.1rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    
    &::before {
      content: '💍';
      font-size: 1.2rem;
    }
  }
`;

const StrengthMeter = styled.div`
  margin-bottom: 1rem;
  
  .label {
    font-size: 0.8rem;
    color: #e91e63;
    font-weight: 600;
    margin-bottom: 0.25rem;
  }
  
  .meter {
    width: 100%;
    height: 8px;
    background: #f0f0f0;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .fill {
    height: 100%;
    background: linear-gradient(90deg, #ff6b6b 0%, #feca57 50%, #48dbfb 100%);
    transition: width 0.3s ease;
  }
  
  .value {
    font-size: 0.75rem;
    color: #333;
    margin-top: 0.25rem;
  }
`;

const EventItem = styled.div`
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: linear-gradient(135deg, rgba(233, 30, 99, 0.1) 0%, rgba(255, 111, 0, 0.1) 100%);
  border-radius: 12px;
  border: 1px solid rgba(233, 30, 99, 0.2);
  
  .year {
    font-weight: 700;
    color: #e91e63;
    font-size: 0.9rem;
  }
  
  .probability {
    font-size: 0.75rem;
    padding: 2px 6px;
    border-radius: 8px;
    margin-left: 0.5rem;
    
    &.high {
      background: #48dbfb;
      color: white;
    }
    
    &.medium {
      background: #feca57;
      color: white;
    }
  }
  
  .description {
    font-size: 0.75rem;
    color: #333;
    margin-top: 0.25rem;
  }
`;

const EventPredictionWidget = () => {
  const { birthData } = useAstrology();
  const [eventData, setEventData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (birthData) {
      loadEventPredictions();
    }
  }, [birthData]);

  const loadEventPredictions = async () => {
    if (!birthData) return;
    
    setLoading(true);
    try {
      const data = await apiService.calculateHouse7Events(birthData);
      setEventData(data);
    } catch (error) {
      console.error('Failed to load event predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <EventContainer>
        <h3>Marriage Predictions</h3>
        <div style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
          Analyzing...
        </div>
      </EventContainer>
    );
  }

  if (!eventData) {
    return (
      <EventContainer>
        <h3>Marriage Predictions</h3>
        <div style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
          No data available
        </div>
      </EventContainer>
    );
  }

  const { house_analysis, event_predictions } = eventData;

  return (
    <EventContainer>
      <h3>Marriage Predictions</h3>
      
      <StrengthMeter>
        <div className="label">7th House Strength</div>
        <div className="meter">
          <div 
            className="fill" 
            style={{ width: `${house_analysis.strength_analysis.total_strength}%` }}
          />
        </div>
        <div className="value">
          {house_analysis.strength_analysis.total_strength}% - {house_analysis.strength_analysis.interpretation}
        </div>
      </StrengthMeter>

      <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '1rem' }}>
        House Lord: {house_analysis.house_lord}
      </div>

      {event_predictions.map((prediction, index) => (
        <EventItem key={index}>
          <div>
            <span className="year">{prediction.year}</span>
            <span className={`probability ${prediction.probability.toLowerCase()}`}>
              {prediction.probability}
            </span>
          </div>
          <div className="description">{prediction.description}</div>
        </EventItem>
      ))}

      {event_predictions.length === 0 && (
        <div style={{ textAlign: 'center', color: '#666', fontSize: '0.8rem' }}>
          No significant events predicted in next 10 years
        </div>
      )}
    </EventContainer>
  );
};

export default EventPredictionWidget;