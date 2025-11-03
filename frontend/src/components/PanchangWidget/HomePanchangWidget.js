import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../../services/apiService';
import styled from 'styled-components';

const PanchangContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 1rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(233, 30, 99, 0.2);
  height: 100%;
  
  h3 {
    color: #e91e63;
    margin-bottom: 1rem;
    font-size: 1.1rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    
    &::before {
      content: '📅';
      font-size: 1rem;
    }
  }
`;

const LocationText = styled.p`
  font-weight: bold;
  margin-bottom: 1rem;
  color: #333;
  font-size: 0.9rem;
`;

const PanchangDetails = styled.div`
  margin-bottom: 1rem;
  
  p {
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
    color: #555;
    
    strong {
      color: #e91e63;
      font-weight: 600;
    }
  }
`;

const PanchangButton = styled.button`
  width: 100%;
  background: linear-gradient(135deg, #e91e63, #ff6f00);
  color: white;
  border: none;
  padding: 0.75rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(233, 30, 99, 0.3);
  }
`;

const LoadingText = styled.div`
  text-align: center;
  color: #666;
  padding: 1rem;
  font-size: 0.9rem;
`;

const HomePanchangWidget = () => {
  const [panchangData, setPanchangData] = useState(null);
  const [sunriseData, setSunriseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchPanchangData();
  }, []);

  const fetchPanchangData = async () => {
    try {
      const today = new Date();
      const [panchang, sunrise] = await Promise.all([
        apiService.calculatePanchang({
          transit_date: today.toISOString().split('T')[0],
          birth_data: {
            name: 'Panchang',
            date: today.toISOString().split('T')[0],
            time: '12:00',
            latitude: 28.6139,
            longitude: 77.2090,
            timezone: 5.5,
            place: 'New Delhi, India'
          }
        }),
        apiService.calculateSunriseSunset(today.toISOString().split('T')[0], 28.6139, 77.2090)
      ]);
      setPanchangData(panchang);
      setSunriseData(sunrise);
    } catch (error) {
      console.error('Error fetching panchang data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <PanchangContainer>
        <h3>Panchang</h3>
        <LoadingText>Loading...</LoadingText>
      </PanchangContainer>
    );
  }

  return (
    <PanchangContainer>
      <h3>Panchang</h3>
      <LocationText>New Delhi, India (Today)</LocationText>
      <PanchangDetails>
        <p><strong>Tithi:</strong> {panchangData?.tithi?.name || 'N/A'}</p>
        <p><strong>Nakshatra:</strong> {panchangData?.nakshatra?.name || 'N/A'}</p>
        <p><strong>Yoga:</strong> {panchangData?.yoga?.name || 'N/A'}</p>
        <p><strong>Karana:</strong> {panchangData?.karana?.name || 'N/A'}</p>
        <p><strong>Vara:</strong> {panchangData?.vara?.name || new Date().toLocaleDateString('en-US', { weekday: 'long' })}</p>
        <p><strong>Sunrise:</strong> {sunriseData?.sunrise ? new Date(sunriseData.sunrise).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : 'N/A'}</p>
        <p><strong>Sunset:</strong> {sunriseData?.sunset ? new Date(sunriseData.sunset).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : 'N/A'}</p>
        <p><strong>Moon Phase:</strong> {sunriseData?.moon_phase || 'N/A'}</p>
      </PanchangDetails>
      <PanchangButton onClick={() => navigate('/panchang')}>
        Today's Panchang
      </PanchangButton>
    </PanchangContainer>
  );
};

export default HomePanchangWidget;