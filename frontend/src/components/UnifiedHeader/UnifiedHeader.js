import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import ChartSearchDropdown from '../ChartSearchDropdown/ChartSearchDropdown';

const UnifiedHeader = ({ 
  currentChart, 
  onSelectChart, 
  onViewAllCharts, 
  onNewChart, 
  onLogout,
  user,
  showTransitControls = false,
  transitDate,
  onTransitDateChange,
  onResetToToday
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isMobile = window.innerWidth <= 768;

  const handleDateChange = (operation, unit) => {
    const newDate = new Date(transitDate);
    
    switch (operation) {
      case 'add':
        switch (unit) {
          case 'day': newDate.setDate(newDate.getDate() + 1); break;
          case 'week': newDate.setDate(newDate.getDate() + 7); break;
          case 'month': newDate.setMonth(newDate.getMonth() + 1); break;
          case 'year': newDate.setFullYear(newDate.getFullYear() + 1); break;
          default: return;
        }
        break;
      case 'sub':
        switch (unit) {
          case 'day': newDate.setDate(newDate.getDate() - 1); break;
          case 'week': newDate.setDate(newDate.getDate() - 7); break;
          case 'month': newDate.setMonth(newDate.getMonth() - 1); break;
          case 'year': newDate.setFullYear(newDate.getFullYear() - 1); break;
          default: return;
        }
        break;
      default:
        return;
    }
    
    onTransitDateChange(newDate);
  };

  const navButtonStyle = {
    background: 'rgba(255, 255, 255, 0.2)',
    color: 'white',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    padding: isMobile ? '3px 4px' : '4px 6px',
    borderRadius: '3px',
    cursor: 'pointer',
    fontSize: isMobile ? '10px' : '11px',
    fontWeight: '600',
    minWidth: isMobile ? '22px' : '28px',
    flexShrink: 0
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, #ff6b35 0%, #f7931e 100%)',
      borderBottom: '3px solid #d4691a',
      padding: isMobile ? '8px 12px' : '12px 16px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      overflowX: 'hidden',
      minHeight: isMobile ? '50px' : '60px'
    }}>
      {/* Left Side */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {isMobile ? (
          // Mobile: Hamburger Menu
          <div ref={menuRef} style={{ position: 'relative' }}>
            <button
              onClick={() => {
                if (!showMenu && menuRef.current) {
                  const rect = menuRef.current.getBoundingClientRect();
                  setMenuPosition({
                    top: rect.bottom,
                    left: rect.left
                  });
                }
                setShowMenu(!showMenu);
              }}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '20px',
                cursor: 'pointer',
                padding: '8px',
                borderRadius: '4px',
                color: 'white'
              }}
            >
              ☰
            </button>
            
            {showMenu && createPortal(
              <div style={{
                position: 'fixed',
                top: menuPosition.top,
                left: menuPosition.left,
                background: 'white',
                border: '2px solid #e91e63',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                minWidth: '180px',
                zIndex: 99999
              }}>
                <div
                  onClick={() => { onViewAllCharts(); setShowMenu(false); }}
                  style={{
                    padding: '12px 16px',
                    cursor: 'pointer',
                    borderBottom: '1px solid #f0f0f0',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                  onMouseEnter={(e) => e.target.style.background = '#f8f9fa'}
                  onMouseLeave={(e) => e.target.style.background = 'white'}
                >
                  🏠 Home
                </div>
                <div
                  onClick={() => { onNewChart(); setShowMenu(false); }}
                  style={{
                    padding: '12px 16px',
                    cursor: 'pointer',
                    borderBottom: '1px solid #f0f0f0',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                  onMouseEnter={(e) => e.target.style.background = '#f8f9fa'}
                  onMouseLeave={(e) => e.target.style.background = 'white'}
                >
                  ➕ New Chart
                </div>
                <div
                  style={{
                    padding: '12px 16px',
                    color: '#666',
                    fontSize: '14px',
                    borderBottom: '1px solid #f0f0f0'
                  }}
                >
                  👤 {user?.name || 'Profile'}
                </div>
                <div
                  onClick={() => { onLogout(); setShowMenu(false); }}
                  style={{
                    padding: '12px 16px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    color: '#dc3545',
                    fontWeight: '600'
                  }}
                  onMouseEnter={(e) => e.target.style.background = '#f8f9fa'}
                  onMouseLeave={(e) => e.target.style.background = 'white'}
                >
                  🚪 Logout
                </div>
              </div>,
              document.body
            )}
          </div>
        ) : (
          // Desktop: Full Navigation
          <>
            <button
              onClick={onViewAllCharts}
              style={{
                background: 'rgba(255, 255, 255, 0.2)',
                border: '2px solid rgba(255, 255, 255, 0.3)',
                color: 'white',
                padding: '8px 12px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              🏠 Home
            </button>
            <button
              onClick={onNewChart}
              style={{
                background: 'rgba(255, 255, 255, 0.2)',
                border: '2px solid rgba(255, 255, 255, 0.3)',
                color: 'white',
                padding: '8px 12px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              ➕ New Chart
            </button>
          </>
        )}

        {/* Chart Selector - Always Visible */}
        {currentChart && (
          <ChartSearchDropdown
            currentChart={currentChart}
            onSelectChart={onSelectChart}
            onViewAll={onViewAllCharts}
          />
        )}
      </div>

      {/* Center: Title (Desktop Only) */}
      {!isMobile && (
        <div style={{
          fontSize: '18px',
          fontWeight: '600',
          color: 'white',
          textAlign: 'center',
          flex: 1,
          margin: '0 20px',
          textShadow: '0 1px 2px rgba(0,0,0,0.2)'
        }}>
          {showTransitControls ? 'Dashboard' : 'Birth Chart Dashboard'}
        </div>
      )}

      {/* Right Side */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: isMobile ? '8px' : '12px',
        flexShrink: 0,
        minWidth: 0
      }}>
        {/* Transit Controls */}
        {showTransitControls && (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: isMobile ? '2px' : '4px',
            flexShrink: 0,
            overflow: 'hidden'
          }}>
            {/* Date Display */}
            <div style={{
              color: 'white',
              fontSize: isMobile ? '10px' : '12px',
              fontWeight: '600',
              padding: isMobile ? '3px 6px' : '4px 8px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '4px',
              minWidth: isMobile ? '50px' : '80px',
              textAlign: 'center',
              flexShrink: 0
            }}>
              {isMobile 
                ? transitDate?.toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
                : transitDate?.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
              }
            </div>
            
            {/* Navigation Buttons */}
            {isMobile ? (
              // Mobile - Essential controls only
              <>
                <button onClick={() => handleDateChange('sub', 'month')} style={navButtonStyle}>‹M</button>
                <button onClick={() => handleDateChange('sub', 'day')} style={navButtonStyle}>‹D</button>
                <button onClick={onResetToToday} style={{...navButtonStyle, background: 'rgba(255, 255, 255, 0.3)'}}>Now</button>
                <button onClick={() => handleDateChange('add', 'day')} style={navButtonStyle}>D›</button>
                <button onClick={() => handleDateChange('add', 'month')} style={navButtonStyle}>M›</button>
              </>
            ) : (
              // Desktop - Full controls
              <>
                <button onClick={() => handleDateChange('sub', 'year')} style={navButtonStyle}>‹‹Y</button>
                <button onClick={() => handleDateChange('sub', 'month')} style={navButtonStyle}>‹M</button>
                <button onClick={() => handleDateChange('sub', 'week')} style={navButtonStyle}>‹W</button>
                <button onClick={() => handleDateChange('sub', 'day')} style={navButtonStyle}>‹D</button>
                <button onClick={onResetToToday} style={{...navButtonStyle, background: 'rgba(255, 255, 255, 0.3)'}}>Now</button>
                <button onClick={() => handleDateChange('add', 'day')} style={navButtonStyle}>D›</button>
                <button onClick={() => handleDateChange('add', 'week')} style={navButtonStyle}>W›</button>
                <button onClick={() => handleDateChange('add', 'month')} style={navButtonStyle}>M›</button>
                <button onClick={() => handleDateChange('add', 'year')} style={navButtonStyle}>Y››</button>
              </>
            )}
          </div>
        )}

        {/* User Menu (Desktop) */}
        {!isMobile && (
          <div style={{
            padding: '8px 12px',
            background: 'rgba(255, 255, 255, 0.2)',
            borderRadius: '6px',
            fontSize: '14px',
            color: 'white',
            fontWeight: '600'
          }}>
            👤 {user?.name || 'User'}
          </div>
        )}

        {/* Logout Button (Desktop Only) */}
        {!isMobile && (
          <button
            onClick={onLogout}
            style={{
              background: '#dc3545',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            🚪 Logout
          </button>
        )}
      </div>
    </div>
  );
};

export default UnifiedHeader;