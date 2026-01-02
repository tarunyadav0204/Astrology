import React, { useState, useEffect } from 'react';

const YoginiTab = ({ birthData, transitDate, onDateChange, showOnlyCurrentStatus = false }) => {
  const [yoginiData, setYoginiData] = useState(null);
  const [selectedDashas, setSelectedDashas] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedIndex, setExpandedIndex] = useState(null);

  const YOGINI_CONFIG = {
    Mangala: { color: '#11998e', icon: '🌙', label: 'Success' },
    Pingala: { color: '#ff9966', icon: '☀️', label: 'Aggression' },
    Dhanya: { color: '#f2994a', icon: '💰', label: 'Wealth' },
    Bhramari: { color: '#cb2d3e', icon: '✈️', label: 'Travel' },
    Bhadrika: { color: '#56ab2f', icon: '👥', label: 'Career' },
    Ulka: { color: '#2980b9', icon: '⚡', label: 'Workload' },
    Siddha: { color: '#8E2DE2', icon: '⭐', label: 'Victory' },
    Sankata: { color: '#833ab4', icon: '⚠️', label: 'Crisis' },
  };

  useEffect(() => {
    if (birthData) {
      loadYoginiDashas();
    }
  }, [birthData, transitDate]);

  const loadYoginiDashas = async () => {
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

      const response = await fetch('/api/yogini-dasha', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formattedBirthData,
          years: 5,
          target_date: transitDate.toISOString().split('T')[0]
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      
      if (data.error) {
        setError(`Calculation failed: ${data.error}`);
        return;
      }

      setYoginiData(data);
      autoSelectCurrentDashas(data);
    } catch (err) {
      setError('Failed to load Yogini data');
      console.error('Yogini calculation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const autoSelectCurrentDashas = (data) => {
    if (!data?.timeline) return;
    
    const currentIndex = data.timeline.findIndex(item => 
      item.name === data.current?.mahadasha?.name && 
      item.start === data.current?.mahadasha?.start && 
      item.end === data.current?.mahadasha?.end
    );
    
    if (currentIndex >= 0) {
      setExpandedIndex(currentIndex);
      setSelectedDashas({
        maha: data.current.mahadasha.name,
        antar: data.current.antardasha?.name
      });
    }
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
    if (!yoginiData?.current) return null;
    
    const { mahadasha, antardasha } = yoginiData.current;
    const progress = calculateProgress(antardasha.start, antardasha.end);
    
    return (
      <div className={showOnlyCurrentStatus ? "current-dasha-inline" : "current-status-card"}>
        {!showOnlyCurrentStatus && (
          <div className="status-header">
            <h3>🎯 Current Yogini Period</h3>
            <div className="system-badge">YOGINI</div>
          </div>
        )}
        
        <div className="current-dasha-chain">
          <span className="current-dasha-planet" style={{ backgroundColor: YOGINI_CONFIG[mahadasha.name]?.color || '#8E2DE2' }}>
            {YOGINI_CONFIG[mahadasha.name]?.icon} {mahadasha.name}
          </span>
          {antardasha && (
            <>
              <span className="dasha-arrow">→</span>
              <span className="current-dasha-planet" style={{ backgroundColor: YOGINI_CONFIG[antardasha.name]?.color || '#8E2DE2' }}>
                {YOGINI_CONFIG[antardasha.name]?.icon} {antardasha.name}
              </span>
            </>
          )}
        </div>
        
        {!showOnlyCurrentStatus && (
          <div className="progress-container">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <div className="progress-text">{progress}% Complete</div>
          </div>
        )}
      </div>
    );
  };

  const scrollCards = (direction) => {
    const container = document.querySelector('.yogini-tab .dasha-cards');
    if (container) {
      const scrollAmount = 200;
      container.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  const renderMahadashaLevel = () => {
    if (!yoginiData?.timeline) return null;
    
    return (
      <div className="dasha-level">
        <div className="dasha-level-header">
          <h4 className="dasha-level-title">Yogini Mahadasha (36 Year Cycle)</h4>
          <div className="scroll-arrows">
            <button className="scroll-arrow" onClick={() => scrollCards('left')}>‹</button>
            <button className="scroll-arrow" onClick={() => scrollCards('right')}>›</button>
          </div>
        </div>
        <div className="dasha-cards">
          {yoginiData.timeline.map((dasha, index) => {
            const config = YOGINI_CONFIG[dasha.name] || YOGINI_CONFIG['Mangala'];
            const isSelected = expandedIndex === index;
            const isCurrent = dasha.name === yoginiData.current?.mahadasha?.name &&
                             dasha.start === yoginiData.current?.mahadasha?.start &&
                             dasha.end === yoginiData.current?.mahadasha?.end;
            const progress = calculateProgress(dasha.start, dasha.end);
            
            return (
              <div
                key={`${dasha.name}-${index}`}
                className={`dasha-card yogini-card ${isSelected ? 'selected' : ''} ${isCurrent ? 'current' : ''}`}
                onClick={async () => {
                  setExpandedIndex(index);
                  setSelectedDashas({ maha: dasha.name });
                  
                  if (!dasha.sub_periods) {
                    try {
                      const formattedBirthData = {
                        name: birthData.name,
                        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
                        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
                        latitude: parseFloat(birthData.latitude),
                        longitude: parseFloat(birthData.longitude),
                        place: birthData.place || 'Unknown'
                      };

                      const startDate = new Date(dasha.start);
                      const endDate = new Date(dasha.end);
                      const midDate = new Date((startDate.getTime() + endDate.getTime()) / 2);
                      const targetDate = midDate.toISOString().split('T')[0];

                      const response = await fetch('/api/yogini-dasha', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          ...formattedBirthData,
                          years: 5,
                          target_date: targetDate
                        })
                      });

                      if (response.ok) {
                        const data = await response.json();
                        const mahaWithSubPeriods = data.timeline?.find(t => 
                          t.name === dasha.name && 
                          t.start === dasha.start && 
                          t.sub_periods
                        );
                        
                        if (mahaWithSubPeriods?.sub_periods) {
                          setYoginiData(prev => ({
                            ...prev,
                            timeline: prev.timeline.map((item, i) => 
                              i === index ? { ...item, sub_periods: mahaWithSubPeriods.sub_periods } : item
                            )
                          }));
                        }
                      }
                    } catch (err) {
                      console.error('Failed to fetch sub_periods:', err);
                    }
                  }
                }}
                style={{ borderColor: config.color }}
              >
                <div className="yogini-header" style={{ backgroundColor: config.color }}>
                  <span className="yogini-icon">{config.icon}</span>
                </div>
                <div className="dasha-planet">{dasha.name}</div>
                <div className="yogini-label" style={{ color: config.color }}>{config.label}</div>
                <div className="dasha-period">{dasha.years} Years</div>
                <div className="dasha-dates">
                  {formatDate(dasha.start)} - {formatDate(dasha.end)}
                </div>
                {isCurrent && (
                  <div className="dasha-progress">
                    <div className="dasha-progress-fill" style={{ width: `${progress}%`, backgroundColor: config.color }}></div>
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
    if (expandedIndex === null) return null;
    
    const selectedMaha = yoginiData?.timeline[expandedIndex];
    if (!selectedMaha) return null;
    
    const antarPeriods = selectedMaha.sub_periods;
    if (!antarPeriods || antarPeriods.length === 0) return null;
    
    return (
      <div className="dasha-level">
        <h4 className="dasha-level-title">Yogini Antardasha</h4>
        <div className="dasha-cards">
          {antarPeriods.map((period, index) => {
            const config = YOGINI_CONFIG[period.name] || YOGINI_CONFIG['Mangala'];
            const isSelected = selectedDashas.antar === period.name;
            const isCurrent = period.name === yoginiData.current?.antardasha?.name &&
                             period.start === yoginiData.current?.antardasha?.start &&
                             period.end === yoginiData.current?.antardasha?.end;
            const progress = calculateProgress(period.start, period.end);
            
            return (
              <div
                key={`antar-${period.name}-${index}`}
                className={`dasha-card yogini-card ${isSelected ? 'selected' : ''} ${isCurrent ? 'current' : ''}`}
                onClick={() => setSelectedDashas(prev => ({ ...prev, antar: period.name }))}
                style={{ borderColor: config.color }}
              >
                <div className="yogini-header" style={{ backgroundColor: config.color }}>
                  <span className="yogini-icon">{config.icon}</span>
                </div>
                <div className="dasha-planet">{period.name}</div>
                <div className="yogini-label" style={{ color: config.color }}>{config.label}</div>
                <div className="dasha-period">{period.years} Years</div>
                <div className="dasha-dates">
                  {formatDate(period.start)} - {formatDate(period.end)}
                </div>
                {isCurrent && (
                  <div className="dasha-progress">
                    <div className="dasha-progress-fill" style={{ width: `${progress}%`, backgroundColor: config.color }}></div>
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
      <div className="yogini-loading">
        <div className="loading-spinner"></div>
        <p>Loading Yogini Dasha periods...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="yogini-error">
        <p>⚠️ {error}</p>
        <button onClick={loadYoginiDashas} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  if (showOnlyCurrentStatus) {
    return renderCurrentStatus();
  }

  return (
    <div className="yogini-tab">
      <div className="dasha-levels">
        {renderMahadashaLevel()}
        {renderAntardashaLevel()}
      </div>
    </div>
  );
};

export default YoginiTab;