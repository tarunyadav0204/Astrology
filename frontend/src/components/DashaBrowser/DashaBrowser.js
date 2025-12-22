import React, { useState, useEffect } from 'react';
import VimshottariTab from './VimshottariTab';
import KalachakraTab from './KalachakraTab';
import YoginiTab from './YoginiTab';
import CharaTab from './CharaTab';
import './DashaBrowser.css';

const DashaBrowser = ({ birthData, chartData }) => {
  const [activeTab, setActiveTab] = useState('vimshottari');
  const [transitDate, setTransitDate] = useState(new Date());

  const adjustDate = (days) => {
    const newDate = new Date(transitDate);
    newDate.setDate(newDate.getDate() + days);
    setTransitDate(newDate);
  };

  const resetToToday = () => {
    setTransitDate(new Date());
  };

  if (!birthData) {
    return (
      <div className="dasha-browser-loading">
        <p>Please select a birth chart to view dasha periods</p>
      </div>
    );
  }

  return (
    <div className="dasha-browser">
      {/* Integrated Header */}
      <div className="integrated-header">
        {/* Date Navigator Section */}
        <div className="nav-section">
          <div className="nav-buttons">
            <button onClick={() => adjustDate(-365)} style={{
              borderRadius: 0,
              fontSize: '0.9rem',
              height: '48px',
              padding: '0.8rem 1.2rem',
              background: 'rgba(249, 115, 22, 0.1)',
              border: '1px solid #f97316',
              color: '#f97316',
              fontWeight: 600,
              cursor: 'pointer',
              minWidth: '45px'
            }}>-1Y</button>
            <button onClick={() => adjustDate(-30)} style={{
              borderRadius: 0,
              fontSize: '0.9rem',
              height: '48px',
              padding: '0.8rem 1.2rem',
              background: 'rgba(249, 115, 22, 0.1)',
              border: '1px solid #f97316',
              color: '#f97316',
              fontWeight: 600,
              cursor: 'pointer',
              minWidth: '45px'
            }}>-1M</button>
            <button onClick={() => adjustDate(-7)} style={{
              borderRadius: 0,
              fontSize: '0.9rem',
              height: '48px',
              padding: '0.8rem 1.2rem',
              background: 'rgba(249, 115, 22, 0.1)',
              border: '1px solid #f97316',
              color: '#f97316',
              fontWeight: 600,
              cursor: 'pointer',
              minWidth: '45px'
            }}>-1W</button>
            <button onClick={() => adjustDate(-1)} style={{
              borderRadius: 0,
              fontSize: '0.9rem',
              height: '48px',
              padding: '0.8rem 1.2rem',
              background: 'rgba(249, 115, 22, 0.1)',
              border: '1px solid #f97316',
              color: '#f97316',
              fontWeight: 600,
              cursor: 'pointer',
              minWidth: '45px'
            }}>-1D</button>
          </div>
          
          <div className="date-display" style={{marginBottom: 0}}>
            <button onClick={resetToToday} style={{
              borderRadius: 0,
              padding: '0.8rem 1.2rem',
              height: '48px',
              background: 'linear-gradient(135deg, #ec4899 0%, #be185d 100%)',
              color: 'white',
              border: 'none',
              fontWeight: 700,
              cursor: 'pointer',
              fontSize: '0.9rem',
              whiteSpace: 'nowrap'
            }}>
              📅 {transitDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </button>
          </div>
          
          <div className="nav-buttons">
            <button onClick={() => adjustDate(1)} style={{
              borderRadius: 0,
              fontSize: '0.9rem',
              height: '48px',
              padding: '0.8rem 1.2rem',
              background: 'rgba(249, 115, 22, 0.1)',
              border: '1px solid #f97316',
              color: '#f97316',
              fontWeight: 600,
              cursor: 'pointer',
              minWidth: '45px'
            }}>+1D</button>
            <button onClick={() => adjustDate(7)} style={{
              borderRadius: 0,
              fontSize: '0.9rem',
              height: '48px',
              padding: '0.8rem 1.2rem',
              background: 'rgba(249, 115, 22, 0.1)',
              border: '1px solid #f97316',
              color: '#f97316',
              fontWeight: 600,
              cursor: 'pointer',
              minWidth: '45px'
            }}>+1W</button>
            <button onClick={() => adjustDate(30)} style={{
              borderRadius: 0,
              fontSize: '0.9rem',
              height: '48px',
              padding: '0.8rem 1.2rem',
              background: 'rgba(249, 115, 22, 0.1)',
              border: '1px solid #f97316',
              color: '#f97316',
              fontWeight: 600,
              cursor: 'pointer',
              minWidth: '45px'
            }}>+1M</button>
            <button onClick={() => adjustDate(365)} style={{
              borderRadius: 0,
              fontSize: '0.9rem',
              height: '48px',
              padding: '0.8rem 1.2rem',
              background: 'rgba(249, 115, 22, 0.1)',
              border: '1px solid #f97316',
              color: '#f97316',
              fontWeight: 600,
              cursor: 'pointer',
              minWidth: '45px'
            }}>+1Y</button>
          </div>
        </div>

        {/* Dasha Type Tabs Section */}
        <div className="tabs-section">
          <button
            className={`dasha-tab ${activeTab === 'vimshottari' ? 'active' : ''}`}
            onClick={() => setActiveTab('vimshottari')}
            style={{borderRadius: 0}}
          >
            Vimshottari
          </button>
          <button
            className={`dasha-tab ${activeTab === 'kalachakra' ? 'active' : ''}`}
            onClick={() => setActiveTab('kalachakra')}
            style={{borderRadius: 0}}
          >
            Kalachakra
          </button>
          <button
            className={`dasha-tab ${activeTab === 'yogini' ? 'active' : ''}`}
            onClick={() => setActiveTab('yogini')}
            style={{borderRadius: 0}}
          >
            Yogini
          </button>
          <button
            className={`dasha-tab ${activeTab === 'chara' ? 'active' : ''}`}
            onClick={() => setActiveTab('chara')}
            style={{borderRadius: 0}}
          >
            Chara
          </button>
        </div>
      </div>

      {/* Current Dasha Section - Below Header */}
      <div className="current-dasha-container">
        {activeTab === 'vimshottari' && (
          <VimshottariTab 
            birthData={birthData} 
            transitDate={transitDate}
            onDateChange={setTransitDate}
            showOnlyCurrentStatus={true}
          />
        )}
        {activeTab === 'kalachakra' && (
          <KalachakraTab 
            birthData={birthData} 
            transitDate={transitDate}
            onDateChange={setTransitDate}
            showOnlyCurrentStatus={true}
          />
        )}
        {activeTab === 'yogini' && (
          <YoginiTab 
            birthData={birthData} 
            transitDate={transitDate}
            onDateChange={setTransitDate}
            showOnlyCurrentStatus={true}
          />
        )}
        {activeTab === 'chara' && (
          <CharaTab 
            birthData={birthData}
            showOnlyCurrentStatus={true}
          />
        )}
      </div>

      {/* Tab Content */}
      <div className="dasha-content">
        {activeTab === 'vimshottari' && (
          <VimshottariTab 
            birthData={birthData} 
            transitDate={transitDate}
            onDateChange={setTransitDate}
            showOnlyCurrentStatus={false}
          />
        )}
        {activeTab === 'kalachakra' && (
          <KalachakraTab 
            birthData={birthData} 
            transitDate={transitDate}
            onDateChange={setTransitDate}
            showOnlyCurrentStatus={false}
          />
        )}
        {activeTab === 'yogini' && (
          <YoginiTab 
            birthData={birthData} 
            transitDate={transitDate}
            onDateChange={setTransitDate}
            showOnlyCurrentStatus={false}
          />
        )}
        {activeTab === 'chara' && (
          <CharaTab 
            birthData={birthData}
            showOnlyCurrentStatus={false}
          />
        )}
      </div>
    </div>
  );
};

export default DashaBrowser;