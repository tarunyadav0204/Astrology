import React, { useState, useEffect } from 'react';
import { useAstrology } from '../../context/AstrologyContext';
import { apiService } from '../../services/apiService';
import styled from 'styled-components';

const PanchangContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 0.5rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(233, 30, 99, 0.2);
  height: 100%;
  overflow: hidden;
  
  h3 {
    color: #e91e63;
    margin-bottom: 0.5rem;
    font-size: 0.8rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.3rem;
    
    &::before {
      content: '📅';
      font-size: 0.8rem;
    }
  }
`;

const PanchangItem = styled.div`
  margin-bottom: 0.2rem;
  padding: 0.25rem;
  background: linear-gradient(135deg, rgba(233, 30, 99, 0.1) 0%, rgba(255, 111, 0, 0.1) 100%);
  border-radius: 4px;
  border: 1px solid rgba(233, 30, 99, 0.2);
  
  .label {
    font-weight: 600;
    color: #e91e63;
    font-size: 0.6rem;
    margin-bottom: 0.1rem;
  }
  
  .value {
    color: #333;
    font-size: 0.55rem;
    line-height: 1.1;
  }
`;

const PanchangWidget = ({ transitDate }) => {
  const { birthData } = useAstrology();
  const [panchangData, setPanchangData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (birthData && transitDate) {
      calculatePanchang();
    }
  }, [birthData, transitDate]);

  const calculatePanchang = async () => {
    if (!birthData || !transitDate) return;
    
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/calculate-panchang', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          birth_data: birthData,
          transit_date: transitDate.toISOString().split('T')[0]
        })
      });
      const data = await response.json();
      setPanchangData(data);
    } catch (error) {
      console.error('Failed to calculate Panchang:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <PanchangContainer>
        <h3>Panchang</h3>
        <div style={{ textAlign: 'center', color: '#666', padding: '1rem' }}>
          Calculating...
        </div>
      </PanchangContainer>
    );
  }

  if (!panchangData) {
    return (
      <PanchangContainer>
        <h3>Panchang</h3>
        <div style={{ textAlign: 'center', color: '#666', padding: '1rem' }}>
          No data available
        </div>
      </PanchangContainer>
    );
  }

  return (
    <PanchangContainer>
      <h3>Panchang</h3>
      
      <PanchangItem>
        <div className="label">Tithi</div>
        <div className="value">
          {panchangData.tithi.name} ({panchangData.tithi.number})
        </div>
      </PanchangItem>
      
      <PanchangItem>
        <div className="label">Vara</div>
        <div className="value">
          {panchangData.vara.name}
        </div>
      </PanchangItem>
      
      <PanchangItem>
        <div className="label">Nakshatra</div>
        <div className="value">
          {panchangData.nakshatra.name} ({panchangData.nakshatra.number})
        </div>
      </PanchangItem>
      
      <PanchangItem>
        <div className="label">Yoga</div>
        <div className="value">
          {panchangData.yoga.name} ({panchangData.yoga.number})
        </div>
      </PanchangItem>
      
      <PanchangItem>
        <div className="label">Karana</div>
        <div className="value">
          {panchangData.karana.name} ({panchangData.karana.number})
        </div>
      </PanchangItem>
    </PanchangContainer>
  );
};

export default PanchangWidget;