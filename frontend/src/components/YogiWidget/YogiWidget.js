import React, { useState, useEffect } from 'react';
import { useAstrology } from '../../context/AstrologyContext';
import { apiService } from '../../services/apiService';
import styled from 'styled-components';

const YogiContainer = styled.div`
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
      content: '🔮';
      font-size: 0.8rem;
    }
  }
`;

const YogiItem = styled.div`
  margin-bottom: 0.3rem;
  padding: 0.3rem;
  background: linear-gradient(135deg, rgba(233, 30, 99, 0.1) 0%, rgba(255, 111, 0, 0.1) 100%);
  border-radius: 6px;
  border: 1px solid rgba(233, 30, 99, 0.2);
  
  .label {
    font-weight: 600;
    color: #e91e63;
    font-size: 0.65rem;
    margin-bottom: 0.1rem;
  }
  
  .value {
    color: #333;
    font-size: 0.6rem;
    line-height: 1.2;
  }
`;

const YogiWidget = () => {
  const { birthData } = useAstrology();
  const [yogiData, setYogiData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (birthData) {
      calculateYogi();
    }
  }, [birthData]);

  const calculateYogi = async () => {
    if (!birthData) return;
    
    setLoading(true);
    try {
      const data = await apiService.calculateYogi(birthData);
      setYogiData(data);
    } catch (error) {
      console.error('Failed to calculate Yogi data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <YogiContainer>
        <h3>Yogi Points</h3>
        <div style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
          Calculating...
        </div>
      </YogiContainer>
    );
  }

  if (!yogiData) {
    return (
      <YogiContainer>
        <h3>Yogi Points</h3>
        <div style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
          No data available
        </div>
      </YogiContainer>
    );
  }

  return (
    <YogiContainer>
      <h3>Yogi Points</h3>
      
      <YogiItem>
        <div className="label">Yogi</div>
        <div className="value">
          {yogiData.yogi.sign_name} {yogiData.yogi.degree}°
        </div>
      </YogiItem>
      
      <YogiItem>
        <div className="label">Avayogi</div>
        <div className="value">
          {yogiData.avayogi.sign_name} {yogiData.avayogi.degree}°
        </div>
      </YogiItem>
      
      <YogiItem>
        <div className="label">Dagdha Rashi</div>
        <div className="value">
          {yogiData.dagdha_rashi.sign_name} {yogiData.dagdha_rashi.degree}°
        </div>
      </YogiItem>
      
      <YogiItem>
        <div className="label">Tithi Shunya Rashi</div>
        <div className="value">
          {yogiData.tithi_shunya_rashi?.sign_name || 'N/A'} {yogiData.tithi_shunya_rashi?.degree ? `${yogiData.tithi_shunya_rashi.degree}°` : ''}
        </div>
      </YogiItem>
    </YogiContainer>
  );
};

export default YogiWidget;