import React, { useState } from 'react';
import { KP_CONFIG } from '../../../config/kpConfig';
import kpService from '../../../services/kpService';
import './EventTiming.css';

const EventTiming = ({ birthData }) => {
  const [selectedEvent, setSelectedEvent] = useState('marriage');
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const eventOptions = [
    { value: 'marriage', label: 'Marriage', houses: KP_CONFIG.EVENT_HOUSES.MARRIAGE },
    { value: 'career', label: 'Career Change', houses: KP_CONFIG.EVENT_HOUSES.CAREER },
    { value: 'health', label: 'Health Issues', houses: KP_CONFIG.EVENT_HOUSES.HEALTH },
    { value: 'education', label: 'Education', houses: KP_CONFIG.EVENT_HOUSES.EDUCATION },
    { value: 'children', label: 'Children', houses: KP_CONFIG.EVENT_HOUSES.CHILDREN },
    { value: 'travel', label: 'Foreign Travel', houses: KP_CONFIG.EVENT_HOUSES.TRAVEL },
    { value: 'property', label: 'Property', houses: KP_CONFIG.EVENT_HOUSES.PROPERTY },
    { value: 'litigation', label: 'Legal Issues', houses: KP_CONFIG.EVENT_HOUSES.LITIGATION }
  ];

  const handlePredict = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await kpService.predictEventTiming(birthData, selectedEvent);
      setPredictions(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const selectedEventData = eventOptions.find(event => event.value === selectedEvent);

  return (
    <div className="event-timing-container">
      <div className="timing-header">
        <h3>Event Timing Predictions</h3>
        <div className="timing-info">
          KP-based precise event timing
        </div>
      </div>
      
      <div className="event-selector">
        <label>Select Event Type</label>
        <select 
          value={selectedEvent}
          onChange={(e) => setSelectedEvent(e.target.value)}
          className="event-select"
        >
          {eventOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        
        {selectedEventData && (
          <div className="event-houses">
            <span>Significator Houses: </span>
            {selectedEventData.houses.map((house, index) => (
              <span key={house} className="house-number">
                {house}{index < selectedEventData.houses.length - 1 ? ', ' : ''}
              </span>
            ))}
          </div>
        )}
      </div>
      
      <button 
        onClick={handlePredict}
        disabled={loading}
        className="predict-btn"
      >
        {loading ? 'Calculating...' : 'Predict Timing'}
      </button>
      
      {error && (
        <div className="timing-error">{error}</div>
      )}
      
      {predictions && (
        <div className="predictions-result">
          <div className="result-header">
            <h4>Timing Predictions for {selectedEventData.label}</h4>
          </div>
          
          {predictions.favorable_periods && predictions.favorable_periods.length > 0 && (
            <div className="favorable-periods">
              <h5>Favorable Periods</h5>
              <div className="periods-list">
                {predictions.favorable_periods.map((period, index) => (
                  <div key={index} className="period-item favorable">
                    <div className="period-date">
                      {period.start_date} - {period.end_date}
                    </div>
                    <div className="period-strength">
                      Strength: {period.strength}%
                    </div>
                    {period.description && (
                      <div className="period-description">
                        {period.description}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {predictions.challenging_periods && predictions.challenging_periods.length > 0 && (
            <div className="challenging-periods">
              <h5>Challenging Periods</h5>
              <div className="periods-list">
                {predictions.challenging_periods.map((period, index) => (
                  <div key={index} className="period-item challenging">
                    <div className="period-date">
                      {period.start_date} - {period.end_date}
                    </div>
                    <div className="period-strength">
                      Difficulty: {period.difficulty}%
                    </div>
                    {period.description && (
                      <div className="period-description">
                        {period.description}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {predictions.best_timing && (
            <div className="best-timing">
              <h5>Most Favorable Time</h5>
              <div className="best-period">
                <div className="best-date">{predictions.best_timing.date}</div>
                <div className="best-description">{predictions.best_timing.description}</div>
              </div>
            </div>
          )}
          
          {predictions.general_advice && (
            <div className="general-advice">
              <h5>General Advice</h5>
              <p>{predictions.general_advice}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EventTiming;