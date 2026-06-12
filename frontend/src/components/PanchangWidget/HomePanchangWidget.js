import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../../services/apiService';

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
      const date = today.toISOString().split('T')[0];

      const [panchang, sunrise] = await Promise.all([
        apiService.calculatePanchang({
          transit_date: date,
          birth_data: {
            name: 'Panchang',
            date,
            time: '12:00',
            latitude: 28.6139,
            longitude: 77.209,
            place: 'New Delhi, India',
          },
        }),
        apiService.calculateSunriseSunset(date, 28.6139, 77.209),
      ]);

      setPanchangData(panchang);
      setSunriseData(sunrise);
    } catch (error) {
      console.error('Error fetching panchang data:', error);
      setPanchangData({
        tithi: { name: 'Loading...' },
        nakshatra: { name: 'Loading...' },
        yoga: { name: 'Loading...' },
        karana: { name: 'Loading...' },
        vara: { name: new Date().toLocaleDateString('en-US', { weekday: 'long' }) },
      });
      setSunriseData({
        sunrise: null,
        sunset: null,
        moon_phase: 'Loading...',
      });
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (value) =>
    value
      ? new Date(value).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
        })
      : 'Loading...';

  return (
    <div className="panchang-card">
      <h3>Panchang</h3>
      {loading ? (
        <div className="panchang-loading">Loading today&apos;s Panchang...</div>
      ) : (
        <>
          <p className="panchang-location">New Delhi, India · Today</p>
          <div className="panchang-details">
            <p><strong>Tithi:</strong> {panchangData?.tithi?.name || 'Loading...'}</p>
            <p><strong>Nakshatra:</strong> {panchangData?.nakshatra?.name || 'Loading...'}</p>
            <p><strong>Yoga:</strong> {panchangData?.yoga?.name || 'Loading...'}</p>
            <p><strong>Karana:</strong> {panchangData?.karana?.name || 'Loading...'}</p>
            <p><strong>Vara:</strong> {panchangData?.vara?.name || new Date().toLocaleDateString('en-US', { weekday: 'long' })}</p>
            <p><strong>Sunrise:</strong> {formatTime(sunriseData?.sunrise)}</p>
            <p><strong>Sunset:</strong> {formatTime(sunriseData?.sunset)}</p>
            <p><strong>Moon phase:</strong> {sunriseData?.moon_phase || 'Loading...'}</p>
          </div>
          <button className="panchang-btn" type="button" onClick={() => navigate('/panchang')}>
            Open today&apos;s Panchang
          </button>
        </>
      )}
    </div>
  );
};

export default HomePanchangWidget;
