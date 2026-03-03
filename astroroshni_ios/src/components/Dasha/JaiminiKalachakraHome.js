import React, { useState, useEffect, useRef } from 'react';
import './JaiminiKalachakraHome.css';

const JaiminiKalachakraHome = ({ dashadata }) => {
  const [selectedMaha, setSelectedMaha] = useState(null);
  const [antardashas, setAntardashas] = useState([]);
  const [selectedAntar, setSelectedAntar] = useState(null);
  const [showBottomSheet, setShowBottomSheet] = useState(false);
  const mahaScrollRef = useRef(null);

  useEffect(() => {
    if (dashadata?.current_mahadasha) {
      setSelectedMaha(dashadata.current_mahadasha);
      loadAntardashas(dashadata.current_mahadasha);
      
      // Auto-scroll to current mahadasha
      setTimeout(() => {
        scrollToCurrentMaha();
      }, 100);
    }
  }, [dashadata]);

  const loadAntardashas = async (maha) => {
    try {
      const response = await fetch('/api/jaimini-antardashas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          maha_sign: maha.sign,
          maha_start_jd: maha.start_jd,
          maha_end_jd: maha.end_jd
        })
      });
      const data = await response.json();
      setAntardashas(data.antardashas || []);
    } catch (error) {
      console.error('Failed to load antardashas:', error);
    }
  };

  const scrollToCurrentMaha = () => {
    if (!mahaScrollRef.current || !dashadata?.mahadashas) return;
    
    const currentIndex = dashadata.mahadashas.findIndex(m => m.current);
    if (currentIndex >= 0) {
      const chipWidth = 120;
      const scrollPosition = currentIndex * chipWidth - 100;
      mahaScrollRef.current.scrollLeft = scrollPosition;
    }
  };

  const handleMahaClick = (maha) => {
    setSelectedMaha(maha);
    loadAntardashas(maha);
  };

  const handleAntarClick = async (antar) => {
    try {
      const response = await fetch('/api/jaimini-antar-details', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          maha_sign: selectedMaha.sign,
          antar_sign: antar.sign
        })
      });
      const data = await response.json();
      setSelectedAntar({ ...antar, ...data });
      setShowBottomSheet(true);
    } catch (error) {
      console.error('Failed to load antar details:', error);
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

  const getTimeRemaining = (endDate) => {
    const end = new Date(endDate);
    const now = new Date();
    const diff = end - now;
    
    if (diff <= 0) return 'Ended';
    
    const years = Math.floor(diff / (365.25 * 24 * 60 * 60 * 1000));
    const months = Math.floor((diff % (365.25 * 24 * 60 * 60 * 1000)) / (30.44 * 24 * 60 * 60 * 1000));
    
    if (years > 0) return `${years}y ${months}m`;
    return `${months}m`;
  };

  if (!dashadata) return <div className="loading">Loading...</div>;

  const currentMaha = dashadata.current_mahadasha;
  const currentAntar = dashadata.current_antardasha;

  return (
    <div className="jaimini-home">
      {/* Current Summary Card */}
      <div className="current-summary">
        <div className="current-header">
          <h3>Current Period</h3>
          <div className="today-date">{new Date().toLocaleDateString()}</div>
        </div>
        
        <div className="current-periods">
          <div className="period-info">
            <div className="period-main">
              {currentMaha?.sign_name} Mahadasha → {currentAntar?.sign_name} Antardasha
            </div>
            <div className="period-details">
              <span className="chakra-badge chakra-{currentMaha?.chakra}">
                Chakra {currentMaha?.chakra}
              </span>
              <span className="direction-arrow">
                {currentMaha?.direction === 'Forward' ? '→' : '←'}
              </span>
            </div>
          </div>
          
          <div className="progress-section">
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${calculateProgress(currentMaha?.start_iso, currentMaha?.end_iso)}%` }}
              ></div>
            </div>
            <div className="progress-text">
              {calculateProgress(currentMaha?.start_iso, currentMaha?.end_iso)}% • 
              Ends: {formatDate(currentMaha?.end_iso)}
            </div>
          </div>
        </div>
      </div>

      {/* Mahadasha Row */}
      <div className="section">
        <h4>Mahadasha Timeline</h4>
        <div className="maha-scroll" ref={mahaScrollRef}>
          {dashadata.mahadashas?.map((maha, index) => (
            <div
              key={`${maha.sign}-${maha.cycle}`}
              className={`maha-chip ${selectedMaha?.sign === maha.sign && selectedMaha?.cycle === maha.cycle ? 'selected' : ''} ${maha.current ? 'current' : ''} chakra-${maha.chakra}`}
              onClick={() => handleMahaClick(maha)}
            >
              <div className="chip-header">
                <span className="sign-name">{maha.sign_name}</span>
                <span className="chakra-badge">C{maha.chakra}</span>
              </div>
              <div className="chip-details">
                <span className="direction-arrow">
                  {maha.direction === 'Forward' ? '→' : '←'}
                </span>
                <span className="years">{maha.years}y</span>
              </div>
              <div className="chip-dates">
                {formatDate(maha.start_iso)} - {formatDate(maha.end_iso)}
              </div>
              {maha.cycle > 1 && (
                <div className="cycle-indicator">Cycle {maha.cycle}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Antardasha Row */}
      {selectedMaha && (
        <div className="section">
          <h4>Antardasha for {selectedMaha.sign_name}</h4>
          <div className="antar-scroll">
            {antardashas.map((antar, index) => (
              <div
                key={`${antar.sign}-${index}`}
                className={`antar-chip ${antar.current ? 'current' : ''}`}
                onClick={() => handleAntarClick(antar)}
              >
                <div className="antar-name">{antar.sign_name}</div>
                <div className="antar-duration">
                  {Math.round(antar.duration_days / 30.44)}m
                </div>
                <div className="antar-dates">
                  {formatDate(antar.start_date)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottom Sheet */}
      {showBottomSheet && selectedAntar && (
        <div className="bottom-sheet-overlay" onClick={() => setShowBottomSheet(false)}>
          <div className="bottom-sheet" onClick={e => e.stopPropagation()}>
            <div className="sheet-header">
              <h3>{selectedAntar.sign_name} Antardasha</h3>
              <button 
                className="close-btn"
                onClick={() => setShowBottomSheet(false)}
              >×</button>
            </div>
            
            <div className="sheet-content">
              <div className="detail-section">
                <h4>Duration</h4>
                <p>{formatDate(selectedAntar.start_date)} - {formatDate(selectedAntar.end_date)}</p>
                <p>Duration: {Math.round(selectedAntar.duration_days / 30.44)} months</p>
              </div>

              <div className="detail-section">
                <h4>Strength Score</h4>
                <div className="strength-bar">
                  <div 
                    className="strength-fill"
                    style={{ width: `${selectedAntar.strength_score || 70}%` }}
                  ></div>
                </div>
                <p>{selectedAntar.strength_score || 70}/100</p>
              </div>

              <div className="detail-section">
                <h4>Keywords</h4>
                <div className="keywords">
                  {selectedAntar.keywords?.map((keyword, i) => (
                    <span key={i} className="keyword-tag">{keyword}</span>
                  ))}
                </div>
              </div>

              <div className="detail-section">
                <h4>House Impact</h4>
                <p><strong>From Lagna:</strong> {selectedAntar.house_impact?.from_lagna}</p>
                <p><strong>From Moon:</strong> {selectedAntar.house_impact?.from_moon}</p>
              </div>

              <div className="detail-section">
                <h4>Events Likely</h4>
                <ul>
                  {selectedAntar.events_likely?.map((event, i) => (
                    <li key={i}>{event}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JaiminiKalachakraHome;