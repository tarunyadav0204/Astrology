import React from 'react';

const TransitDateControls = ({ transitDate, onTransitDateChange, onResetToToday }) => {
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
    background: 'rgba(233, 30, 99, 0.1)',
    color: '#e91e63',
    border: '1px solid #e91e63',
    padding: isMobile ? '4px 6px' : '6px 8px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: isMobile ? '11px' : '12px',
    fontWeight: '600',
    minWidth: isMobile ? '28px' : '32px',
    flexShrink: 0
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: isMobile ? '4px' : '6px',
      padding: '8px 12px',
      background: '#f8f9fa',
      borderRadius: '8px',
      border: '1px solid #e91e63',
      marginBottom: '12px',
      flexWrap: 'wrap',
      justifyContent: 'center'
    }}>
      {/* Date Display */}
      <div style={{
        color: '#e91e63',
        fontSize: isMobile ? '12px' : '14px',
        fontWeight: '600',
        padding: isMobile ? '4px 8px' : '6px 10px',
        background: 'white',
        borderRadius: '4px',
        border: '1px solid #e91e63',
        minWidth: isMobile ? '80px' : '120px',
        textAlign: 'center',
        flexShrink: 0
      }}>
        {isMobile 
          ? transitDate?.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: '2-digit' })
          : transitDate?.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
        }
      </div>
      
      {/* Navigation Buttons */}
      {isMobile ? (
        // Mobile - Essential controls only
        <>
          <button onClick={() => handleDateChange('sub', 'month')} style={navButtonStyle}>‹M</button>
          <button onClick={() => handleDateChange('sub', 'day')} style={navButtonStyle}>‹D</button>
          <button onClick={onResetToToday} style={{...navButtonStyle, background: '#e91e63', color: 'white'}}>Now</button>
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
          <button onClick={onResetToToday} style={{...navButtonStyle, background: '#e91e63', color: 'white'}}>Now</button>
          <button onClick={() => handleDateChange('add', 'day')} style={navButtonStyle}>D›</button>
          <button onClick={() => handleDateChange('add', 'week')} style={navButtonStyle}>W›</button>
          <button onClick={() => handleDateChange('add', 'month')} style={navButtonStyle}>M›</button>
          <button onClick={() => handleDateChange('add', 'year')} style={navButtonStyle}>Y››</button>
        </>
      )}
    </div>
  );
};

export default TransitDateControls;