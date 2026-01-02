import React, { useState, useEffect } from 'react';

const KalachakraTab = ({ birthData, transitDate, onDateChange, showOnlyCurrentStatus = false }) => {
  const [kalchakraData, setKalchakraData] = useState(null);
  const [selectedDashas, setSelectedDashas] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);


  useEffect(() => {
    if (birthData) {
      loadKalachakraDashas();
    }
  }, [birthData, transitDate]);

  const loadKalachakraDashas = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        place: birthData.place || 'Unknown'
      };

      const endpoint = '/api/calculate-kalchakra-dasha';
      
      console.log('Loading Kalachakra dashas');
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          birth_data: formattedBirthData,
          target_date: transitDate.toISOString().split('T')[0]
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      
      if (data.error) {
        setError(`Calculation failed: ${data.error}`);
        return;
      }

      setKalchakraData(data);
      autoSelectCurrentDashas(data);
    } catch (err) {
      setError('Failed to load Kalachakra data');
      console.error('Kalachakra calculation error:', err);
    } finally {
      setLoading(false);
    }
  };



  const autoSelectCurrentDashas = (data) => {
    if (!data?.mahadashas) return;
    
    // Find current mahadasha
    const currentMaha = data.current_mahadasha || data.mahadashas.find(period => {
      const startDate = new Date(period.start);
      const endDate = new Date(period.end);
      const now = new Date();
      return now >= startDate && now <= endDate;
    });
    
    if (currentMaha) {
      const selections = { maha: currentMaha.name };
      
      // Auto-select current antardasha if available
      if (data.current_antardasha) {
        selections.antar = data.current_antardasha.name;
      }
      
      console.log('Auto-selecting dashas:', selections);
      console.log('Current maha from data:', currentMaha);
      setSelectedDashas(selections);
    }
  };

  const handleMahaSelection = (signName) => {
    setSelectedDashas({ maha: signName });
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short' 
    });
  };

  const calculateProgress = (start, end, current = new Date()) => {
    const startTime = new Date(start).getTime();
    const endTime = new Date(end).getTime();
    const currentTime = current.getTime();
    
    if (currentTime < startTime) return 0;
    if (currentTime > endTime) return 100;
    
    return Math.round(((currentTime - startTime) / (endTime - startTime)) * 100);
  };

  const renderCurrentStatus = () => {
    if (!kalchakraData) return null;
    
    const currentMaha = kalchakraData.current_mahadasha || kalchakraData.mahadashas?.find(period => {
      const startDate = new Date(period.start);
      const endDate = new Date(period.end);
      const now = new Date();
      return now >= startDate && now <= endDate;
    });
    
    const currentAntar = kalchakraData.current_antardasha;
    
    if (!currentMaha) return null;
    
    return (
      <div className={showOnlyCurrentStatus ? "current-dasha-inline" : "current-status-card"}>
        {!showOnlyCurrentStatus && (
          <div className="status-header">
            <h3>🎯 Current Kalachakra Period</h3>
            <div className="system-badge">BPHS</div>
          </div>
        )}
        
        {kalchakraData.deha && (
          <div className="kalachakra-pillars">
            <div className="pillar">
              <span className="pillar-label">Deha</span>
              <span className="pillar-value">{kalchakraData.deha}</span>
            </div>
            <div className="pillar-center">
              <span className="direction">{kalchakraData.direction}</span>
              <span className="cycle">{kalchakraData.cycle_len}y</span>
            </div>
            <div className="pillar">
              <span className="pillar-label">Jeeva</span>
              <span className="pillar-value">{kalchakraData.jeeva}</span>
            </div>
          </div>
        )}
        
        <div className="current-dasha-chain">
          <span className="current-dasha-planet">{currentMaha.name}</span>
          {currentAntar && (
            <>
              <span className="dasha-arrow">→</span>
              <span className="current-dasha-planet">{currentAntar.name}</span>
            </>
          )}
        </div>
        
        {currentMaha.gati && (
          <div className="gati-indicator">
            <span className="gati-badge">{currentMaha.gati}</span>
          </div>
        )}
      </div>
    );
  };



  const scrollCards = (level, direction) => {
    const container = document.querySelector(`.kalachakra-tab .dasha-level:nth-child(${level}) .dasha-cards`);
    if (container) {
      const scrollAmount = 200;
      container.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  const renderMahadashaLevel = () => {
    const mahadashas = kalchakraData?.mahadashas;
    if (!mahadashas || mahadashas.length === 0) return null;
    
    return (
      <div className="dasha-level">
        <div className="dasha-level-header">
          <h4 className="dasha-level-title">Kalachakra Mahadasha</h4>
          <div className="scroll-arrows">
            <button className="scroll-arrow" onClick={() => scrollCards(1, 'left')}>‹</button>
            <button className="scroll-arrow" onClick={() => scrollCards(1, 'right')}>›</button>
          </div>
        </div>
        <div className="dasha-cards">
          {mahadashas.map((dasha, index) => {
            const isSelected = selectedDashas.maha === dasha.name;
            const currentDate = new Date();
            const startDate = new Date(dasha.start);
            const endDate = new Date(dasha.end);
            const isCurrent = currentDate >= startDate && currentDate <= endDate;
            const progress = calculateProgress(dasha.start, dasha.end);
            
            return (
              <div
                key={`${dasha.name}-${index}`}
                className={`dasha-card ${isSelected ? 'selected' : ''} ${isCurrent ? 'current' : ''}`}
                onClick={() => handleMahaSelection(dasha.name)}
              >
                <div className="dasha-planet">{dasha.name}</div>
                <div className="dasha-period">{formatPeriodDuration(dasha.years)}</div>
                <div className="dasha-dates">
                  {formatDate(dasha.start)} - {formatDate(dasha.end)}
                </div>
                {dasha.gati && dasha.gati !== 'Start' && (
                  <div className="gati-icon">{dasha.gati_icon || '⚡'}</div>
                )}
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

  const renderAntardashaLevel = () => {
    if (!selectedDashas.maha || !kalchakraData?.all_antardashas) return null;
    
    // Filter antardashas for selected mahadasha from all_antardashas
    const antarPeriods = kalchakraData.all_antardashas.filter(antar => 
      antar.maha_name === selectedDashas.maha
    );
    
    if (!antarPeriods || antarPeriods.length === 0) return null;
    
    return (
      <div className="dasha-level">
        <div className="dasha-level-header">
          <h4 className="dasha-level-title">Kalachakra Antardasha</h4>
          <div className="scroll-arrows">
            <button className="scroll-arrow" onClick={() => scrollCards(2, 'left')}>‹</button>
            <button className="scroll-arrow" onClick={() => scrollCards(2, 'right')}>›</button>
          </div>
        </div>
        <div className="dasha-cards">
          {antarPeriods.map((period, index) => {
            const isSelected = selectedDashas.antar === period.name;
            const isCurrent = new Date() >= new Date(period.start) && new Date() <= new Date(period.end);
            const progress = calculateProgress(period.start, period.end);
            
            return (
              <div
                key={`antar-${period.name}-${index}`}
                className={`dasha-card ${isSelected ? 'selected' : ''} ${isCurrent ? 'current' : ''}`}
                onClick={() => setSelectedDashas(prev => ({ ...prev, antar: period.name }))}
              >
                <div className="dasha-planet">{period.name}</div>
                <div className="dasha-period">{formatPeriodDuration(period.years)}</div>
                <div className="dasha-dates">
                  {formatDate(period.start)} - {formatDate(period.end)}
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

  if (loading) {
    return (
      <div className="kalachakra-loading">
        <div className="loading-spinner"></div>
        <p>Loading Kalachakra Dasha periods...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="kalachakra-error">
        <p>⚠️ {error}</p>
        <button onClick={loadKalachakraDashas} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  if (showOnlyCurrentStatus) {
    return renderCurrentStatus();
  }

  return (
    <div className="kalachakra-tab">
      <div className="dasha-levels">
        {renderMahadashaLevel()}
        {renderAntardashaLevel()}
      </div>
    </div>
  );
};

export default KalachakraTab;