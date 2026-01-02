import React, { useState, useEffect } from 'react';

const SIGN_CONFIG = {
  Aries: { element: 'Fire', color: '#FF6B6B', icon: '♈' },
  Taurus: { element: 'Earth', color: '#8B7355', icon: '♉' },
  Gemini: { element: 'Air', color: '#FFD93D', icon: '♊' },
  Cancer: { element: 'Water', color: '#6C5CE7', icon: '♋' },
  Leo: { element: 'Fire', color: '#FD79A8', icon: '♌' },
  Virgo: { element: 'Earth', color: '#6AB04C', icon: '♍' },
  Libra: { element: 'Air', color: '#4ECDC4', icon: '♎' },
  Scorpio: { element: 'Water', color: '#5F27CD', icon: '♏' },
  Sagittarius: { element: 'Fire', color: '#FF9F43', icon: '♐' },
  Capricorn: { element: 'Earth', color: '#2C3E50', icon: '♑' },
  Aquarius: { element: 'Air', color: '#00B894', icon: '♒' },
  Pisces: { element: 'Water', color: '#A29BFE', icon: '♓' }
};

const CharaTab = ({ birthData, showOnlyCurrentStatus = false }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    if (birthData) {
      loadCharaDasha();
    }
  }, [birthData]);

  const loadCharaDasha = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const formattedData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        place: birthData.place || 'Unknown'
      };

      const response = await fetch('/api/chara-dasha/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formattedData)
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const result = await response.json();
      
      if (result.status === 'success') {
        setData(result);
        const currentIdx = result.periods.findIndex(p => p.is_current);
        if (currentIdx >= 0) {
          setExpandedId(currentIdx);
          loadAntardashas(result.periods[currentIdx].sign_id, currentIdx);
        }
      }
    } catch (err) {
      setError('Failed to load Chara Dasha data');
      console.error('Chara Dasha error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadAntardashas = async (signId, index) => {
    try {
      const formattedData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        place: birthData.place || 'Unknown',
        maha_sign_id: signId
      };

      const response = await fetch('/api/chara-dasha/antardasha', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formattedData)
      });

      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success') {
          setData(prev => {
            const updated = { ...prev };
            updated.periods[index].sub_periods = result.antar_periods;
            return updated;
          });
        }
      }
    } catch (err) {
      console.error('Antardasha error:', err);
    }
  };

  const formatPeriodDuration = (years) => {
    if (!years) return '';
    const wholeYears = Math.floor(years);
    const months = Math.round((years - wholeYears) * 12);
    return months === 0 ? `${wholeYears}y` : `${wholeYears}y ${months}m`;
  };

  const calculateProgress = (startDate, endDate) => {
    const start = new Date(startDate).getTime();
    const end = new Date(endDate).getTime();
    const current = new Date().getTime();
    if (current < start) return 0;
    if (current > end) return 100;
    return Math.round(((current - start) / (end - start)) * 100);
  };

  const renderCurrentStatus = () => {
    if (!data) return null;
    const currentPeriod = data.periods.find(p => p.is_current);
    if (!currentPeriod) return null;

    const config = SIGN_CONFIG[currentPeriod.sign_name];
    
    // Find current antardasha
    let currentAntar = null;
    if (currentPeriod.sub_periods) {
      const now = new Date();
      currentAntar = currentPeriod.sub_periods.find(sub => {
        const start = new Date(sub.start_date);
        const end = new Date(sub.end_date);
        return now >= start && now <= end;
      });
    }
    
    return (
      <div className={showOnlyCurrentStatus ? "current-dasha-inline" : "current-status-card"}>
        {!showOnlyCurrentStatus && (
          <div className="status-header">
            <h3>🪐 Current Chara Dasha</h3>
          </div>
        )}
        <div className="current-dasha-chain">
          <span className="current-dasha-planet" style={{ backgroundColor: config?.color }}>
            {config?.icon} {currentPeriod.sign_name}
          </span>
          {currentAntar && (
            <>
              <span className="dasha-arrow">→</span>
              <span className="current-dasha-planet" style={{ backgroundColor: SIGN_CONFIG[currentAntar.sign]?.color }}>
                {SIGN_CONFIG[currentAntar.sign]?.icon} {currentAntar.sign}
              </span>
            </>
          )}
        </div>
      </div>
    );
  };

  const renderSignCard = (item, index) => {
    const config = SIGN_CONFIG[item.sign_name];
    const isCurrent = item.is_current;
    const isExpanded = expandedId === index;
    const progress = calculateProgress(item.start_date, item.end_date);

    return (
      <div key={index} className="chara-sign-card">
        <div
          className={`sign-card-main ${isCurrent ? 'current' : ''}`}
          onClick={() => {
            if (expandedId === index) {
              setExpandedId(null);
            } else {
              setExpandedId(index);
              if (!item.sub_periods) {
                loadAntardashas(item.sign_id, index);
              }
            }
          }}
          style={{ borderLeftColor: config?.color }}
        >
          <div className="sign-icon" style={{ color: config?.color }}>
            {config?.icon}
          </div>
          <div className="sign-info">
            <div className="sign-name">{item.sign_name}</div>
            <div className="sign-meta">
              {config?.element} • {item.duration_years} Years
            </div>
          </div>
          <div className="sign-dates">
            {new Date(item.start_date).toLocaleDateString('en-US', {
              month: 'short', day: 'numeric', year: '2-digit'
            })} - {new Date(item.end_date).toLocaleDateString('en-US', {
              month: 'short', day: 'numeric', year: '2-digit'
            })}
          </div>
          {isCurrent && (
            <div className="sign-progress">
              <div className="progress-fill" style={{ width: `${progress}%`, backgroundColor: config?.color }}></div>
            </div>
          )}
        </div>

        {isExpanded && item.sub_periods && (
          <div className="sub-periods">
            {item.sub_periods.map((sub, idx) => {
              const subConfig = SIGN_CONFIG[sub.sign];
              return (
                <div key={idx} className="sub-period-item" style={{ borderLeftColor: subConfig?.color }}>
                  <span className="sub-icon" style={{ color: subConfig?.color }}>{subConfig?.icon}</span>
                  <span className="sub-name">{sub.sign}</span>
                  <span className="sub-duration">{formatPeriodDuration(sub.years)}</span>
                  <span className="sub-dates">
                    {new Date(sub.start_date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })} - 
                    {new Date(sub.end_date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="chara-loading">
        <div className="loading-spinner"></div>
        <p>Loading Chara Dasha periods...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chara-error">
        <p>⚠️ {error}</p>
        <button onClick={loadCharaDasha} className="retry-btn">Retry</button>
      </div>
    );
  }

  if (showOnlyCurrentStatus) {
    return renderCurrentStatus();
  }

  return (
    <div className="chara-tab">
      <div className="chara-periods">
        {data?.periods.map((item, index) => renderSignCard(item, index))}
      </div>
    </div>
  );
};

export default CharaTab;
