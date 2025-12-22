import React, { useState, useEffect } from 'react';

const VimshottariTab = ({ birthData, transitDate, onDateChange, showOnlyCurrentStatus = false }) => {
  const [cascadingData, setCascadingData] = useState(null);
  const [selectedDashas, setSelectedDashas] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (birthData && transitDate) {
      loadCascadingDashas();
    }
  }, [birthData, transitDate]);

  const loadCascadingDashas = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'UTC+5:30',
        place: birthData.place || 'Unknown'
      };

      const response = await fetch('/api/calculate-cascading-dashas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          birth_data: formattedBirthData,
          target_date: transitDate.toISOString().split('T')[0]
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        setError(`Calculation failed: ${data.error}`);
        return;
      }

      setCascadingData(data);
      autoSelectCurrentDashas(data);
    } catch (err) {
      setError('Failed to load dasha data');
      console.error('Dasha calculation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const autoSelectCurrentDashas = (data) => {
    if (!data) return;
    
    const selections = {};
    
    const currentMaha = data.maha_dashas?.find(d => d.current);
    if (currentMaha) selections.maha = currentMaha.planet;
    
    const currentAntar = data.antar_dashas?.find(d => d.current);
    if (currentAntar) selections.antar = currentAntar.planet;
    
    const currentPratyantar = data.pratyantar_dashas?.find(d => d.current);
    if (currentPratyantar) selections.pratyantar = currentPratyantar.planet;
    
    const currentSookshma = data.sookshma_dashas?.find(d => d.current);
    if (currentSookshma) selections.sookshma = currentSookshma.planet;
    
    const currentPrana = data.prana_dashas?.find(d => d.current);
    if (currentPrana) selections.prana = currentPrana.planet;
    
    setSelectedDashas(selections);
  };

  const formatPeriodDuration = (years) => {
    if (!years) return '';
    
    const totalDays = years * 365.25;
    const totalMonths = years * 12;
    
    if (totalDays < 90) {
      return `${Math.round(totalDays)}d`;
    } else if (totalMonths < 12) {
      return `${Math.round(totalMonths)}m`;
    } else {
      const wholeYears = Math.floor(years);
      const remainingMonths = Math.round((years - wholeYears) * 12);
      
      if (remainingMonths === 0) {
        return `${wholeYears}y`;
      } else {
        return `${wholeYears}y ${remainingMonths}m`;
      }
    }
  };

  const getPlanetEffects = (planet) => {
    const effects = {
      'Sun': 'Authority, Leadership, Government',
      'Moon': 'Emotions, Travel, Public',
      'Mars': 'Energy, Courage, Property',
      'Mercury': 'Communication, Business, Learning',
      'Jupiter': 'Wisdom, Teaching, Spirituality',
      'Venus': 'Relationships, Arts, Luxury',
      'Saturn': 'Discipline, Hard work, Delays',
      'Rahu': 'Innovation, Foreign, Technology',
      'Ketu': 'Spirituality, Research, Detachment'
    };
    return effects[planet] || 'General influences';
  };

  const calculateProgress = (startDate, endDate) => {
    const start = new Date(startDate).getTime();
    const end = new Date(endDate).getTime();
    const current = transitDate.getTime();
    
    if (current < start) return 0;
    if (current > end) return 100;
    
    return Math.round(((current - start) / (end - start)) * 100);
  };

  const getRemainingTime = (endDate) => {
    const end = new Date(endDate);
    const now = transitDate;
    const diff = end - now;
    
    if (diff <= 0) return 'Period ended';
    
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    const years = Math.floor(days / 365);
    const months = Math.floor((days % 365) / 30);
    const remainingDays = days % 30;
    
    if (years > 0) return `${years}y ${months}m remaining`;
    if (months > 0) return `${months}m ${remainingDays}d remaining`;
    return `${remainingDays}d remaining`;
  };

  const renderCurrentStatus = () => {
    if (!cascadingData) return null;
    
    const currentMaha = cascadingData.maha_dashas?.find(d => d.current);
    const currentAntar = cascadingData.antar_dashas?.find(d => d.current);
    const currentPratyantar = cascadingData.pratyantar_dashas?.find(d => d.current);
    const currentSookshma = cascadingData.sookshma_dashas?.find(d => d.current);
    const currentPrana = cascadingData.prana_dashas?.find(d => d.current);
    
    const currentDashas = [
      currentMaha?.planet,
      currentAntar?.planet,
      currentPratyantar?.planet,
      currentSookshma?.planet,
      currentPrana?.planet
    ].filter(Boolean);
    
    if (currentDashas.length === 0) return null;
    
    return (
      <div className={showOnlyCurrentStatus ? "current-dasha-inline" : "current-status-card"}>
        {!showOnlyCurrentStatus && (
          <div className="status-header">
            <h3>🪐 Current Dasha Hierarchy</h3>
          </div>
        )}
        
        <div className="current-dasha-chain">
          {currentDashas.map((planet, index) => (
            <React.Fragment key={`current-${index}`}>
              <span className="current-dasha-planet">{planet}</span>
              {index < currentDashas.length - 1 && (
                <span className="dasha-arrow">→</span>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    );
  };

  const scrollCards = (level, direction) => {
    const container = document.querySelector(`.vimshottari-tab .dasha-level:nth-child(${level}) .dasha-cards`);
    if (container) {
      const scrollAmount = 200;
      container.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  const renderDashaLevel = (title, dashaType, dashas, levelIndex) => {
    if (!dashas || dashas.length === 0) return null;
    
    return (
      <div className="dasha-level">
        <div className="dasha-level-header">
          <h4 className="dasha-level-title">{title}</h4>
          <div className="scroll-arrows">
            <button className="scroll-arrow" onClick={() => scrollCards(levelIndex, 'left')}>‹</button>
            <button className="scroll-arrow" onClick={() => scrollCards(levelIndex, 'right')}>›</button>
          </div>
        </div>
        <div className="dasha-cards">
          {dashas.map((dasha, index) => {
            const isSelected = selectedDashas[dashaType] === dasha.planet;
            const isCurrent = dasha.current;
            const progress = calculateProgress(dasha.start, dasha.end);
            
            return (
              <div
                key={`${dasha.planet}-${index}`}
                className={`dasha-card ${isSelected ? 'selected' : ''} ${isCurrent ? 'current' : ''}`}
                onClick={() => setSelectedDashas(prev => ({ ...prev, [dashaType]: dasha.planet }))}
              >
                <div className="dasha-planet">{dasha.planet}</div>
                <div className="dasha-period">{formatPeriodDuration(dasha.years)}</div>
                <div className="dasha-dates">
                  {new Date(dasha.start).toLocaleDateString('en-US', {
                    day: 'numeric', month: 'short', year: '2-digit'
                  })} - {new Date(dasha.end).toLocaleDateString('en-US', {
                    day: 'numeric', month: 'short', year: '2-digit'
                  })}
                </div>
                {isCurrent && (
                  <div className="dasha-progress">
                    <div className="dasha-progress-fill" style={{ width: `${progress}%` }}></div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="vimshottari-loading">
        <div className="loading-spinner"></div>
        <p>Loading Vimshottari Dasha periods...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="vimshottari-error">
        <p>⚠️ {error}</p>
        <button onClick={loadCascadingDashas} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  if (showOnlyCurrentStatus) {
    return renderCurrentStatus();
  }

  return (
    <div className="vimshottari-tab">
      <div className="dasha-levels">
        {renderDashaLevel('Maha Dasha', 'maha', cascadingData?.maha_dashas, 1)}
        {renderDashaLevel('Antar Dasha', 'antar', cascadingData?.antar_dashas, 2)}
        {renderDashaLevel('Pratyantar Dasha', 'pratyantar', cascadingData?.pratyantar_dashas, 3)}
        {renderDashaLevel('Sookshma Dasha', 'sookshma', cascadingData?.sookshma_dashas, 4)}
        {renderDashaLevel('Prana Dasha', 'prana', cascadingData?.prana_dashas, 5)}
      </div>
    </div>
  );
};

export default VimshottariTab;