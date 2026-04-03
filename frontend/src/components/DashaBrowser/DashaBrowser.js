import React, { useState, useRef, useCallback } from 'react';
import VimshottariTab from './VimshottariTab';
import KalachakraTab from './KalachakraTab';
import YoginiTab from './YoginiTab';
import CharaTab from './CharaTab';
import './DashaBrowser.css';

function formatLocalDateForInput(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/** Shared date controls: mobile = one full-width row; desktop = grouped inside header card */
const DashaDateNavigation = ({ transitDate, adjustDate, resetToToday, setTransitDate, variant }) => {
  const dateInputRef = useRef(null);
  const dateLabel = transitDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const dateShort = transitDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
  const dateValue = formatLocalDateForInput(transitDate);

  const handleNativeDateChange = useCallback(
    (e) => {
      const v = e.target.value;
      if (!v) return;
      const [yy, mm, dd] = v.split('-').map(Number);
      setTransitDate(new Date(yy, mm - 1, dd));
    },
    [setTransitDate]
  );

  const openDatePicker = useCallback((e) => {
    e?.preventDefault?.();
    const el = dateInputRef.current;
    if (!el) return;
    try {
      if (typeof el.showPicker === 'function') {
        el.showPicker();
      } else {
        el.click();
      }
    } catch {
      el.click();
    }
  }, []);

  const datePickerTitle = 'Choose date — double-click for today';

  const dateHiddenInput = (
    <input
      ref={dateInputRef}
      type="date"
      className="dasha-date-input-native"
      value={dateValue}
      onChange={handleNativeDateChange}
      tabIndex={-1}
    />
  );

  if (variant === 'mobile') {
    return (
      <div className="dasha-date-toolbar dasha-date-toolbar--mobile" aria-label="Date navigation">
        {dateHiddenInput}
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(-365)}>-1Y</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(-30)}>-1M</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(-7)}>-1W</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(-1)}>-1D</button>
        <button
          type="button"
          className="dasha-date-btn dasha-date-btn--compact"
          onClick={openDatePicker}
          onDoubleClick={(e) => {
            e.preventDefault();
            resetToToday();
          }}
          title={datePickerTitle}
        >
          <span className="dasha-date-btn__icon" aria-hidden>📅</span>
          <span className="dasha-date-btn__text dasha-date-btn__text--long">{dateLabel}</span>
          <span className="dasha-date-btn__text dasha-date-btn__text--short">{dateShort}</span>
        </button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(1)}>+1D</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(7)}>+1W</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(30)}>+1M</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(365)}>+1Y</button>
      </div>
    );
  }

  return (
    <div className="nav-section nav-section--desktop">
      {dateHiddenInput}
      <div className="nav-buttons nav-buttons--cluster" aria-label="Go backward in time">
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(-365)}>-1Y</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(-30)}>-1M</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(-7)}>-1W</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(-1)}>-1D</button>
      </div>

      <div className="date-display">
        <button
          type="button"
          className="dasha-date-btn"
          onClick={openDatePicker}
          onDoubleClick={(e) => {
            e.preventDefault();
            resetToToday();
          }}
          title={datePickerTitle}
        >
          <span className="dasha-date-btn__icon" aria-hidden>📅</span>
          <span className="dasha-date-btn__text">{dateLabel}</span>
        </button>
      </div>

      <div className="nav-buttons nav-buttons--cluster" aria-label="Go forward in time">
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(1)}>+1D</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(7)}>+1W</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(30)}>+1M</button>
        <button type="button" className="dasha-nav-btn" onClick={() => adjustDate(365)}>+1Y</button>
      </div>
    </div>
  );
};

const DashaTabBar = ({ activeTab, setActiveTab, variant }) => {
  const sectionClass =
    variant === 'mobile' ? 'tabs-section tabs-section--mobile' : 'tabs-section tabs-section--desktop';
  return (
    <div className={sectionClass} role="tablist" aria-label="Dasha system">
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'vimshottari'}
        className={`dasha-tab ${activeTab === 'vimshottari' ? 'active' : ''}`}
        onClick={() => setActiveTab('vimshottari')}
      >
        Vimshottari
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'kalachakra'}
        className={`dasha-tab ${activeTab === 'kalachakra' ? 'active' : ''}`}
        onClick={() => setActiveTab('kalachakra')}
      >
        Kalachakra
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'yogini'}
        className={`dasha-tab ${activeTab === 'yogini' ? 'active' : ''}`}
        onClick={() => setActiveTab('yogini')}
      >
        Yogini
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'chara'}
        className={`dasha-tab ${activeTab === 'chara' ? 'active' : ''}`}
        onClick={() => setActiveTab('chara')}
      >
        Chara
      </button>
    </div>
  );
};

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

  const dateNavProps = { transitDate, adjustDate, resetToToday, setTransitDate };

  const tabBarProps = { activeTab, setActiveTab };

  return (
    <div className="dasha-browser">
      <DashaTabBar {...tabBarProps} variant="mobile" />
      <DashaDateNavigation {...dateNavProps} variant="mobile" />

      <div className="integrated-header">
        <DashaDateNavigation {...dateNavProps} variant="desktop" />
        <DashaTabBar {...tabBarProps} variant="desktop" />
      </div>

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
          <CharaTab birthData={birthData} showOnlyCurrentStatus={true} />
        )}
      </div>

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
          <CharaTab birthData={birthData} showOnlyCurrentStatus={false} />
        )}
      </div>
    </div>
  );
};

export default DashaBrowser;
