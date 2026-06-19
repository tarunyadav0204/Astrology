import React from 'react';
import { ControlsContainer, DateDisplay, ButtonGroup, NavButton } from './TransitControls.styles';

const TransitControls = ({ date, onChange, onResetToToday, variant = 'default' }) => {
  const handleDateChange = (operation, unit) => {
    const newDate = new Date(date);
    
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
    
    onChange(newDate);
  };

  const resetToToday = () => {
    if (onResetToToday) {
      onResetToToday();
    } else {
      onChange(new Date());
    }
  };

  return (
    <ControlsContainer>
      <DateDisplay $variant={variant}>{window.innerWidth <= 768 ? date.toLocaleDateString('en-US', { month: 'short', day: '2-digit' }) : date.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })}</DateDisplay>
      
      <ButtonGroup>
        {window.innerWidth <= 768 ? (
          // Mobile - Only essential controls
          <>
            <NavButton $variant={variant} onClick={() => handleDateChange('sub', 'month')}>‹M</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('sub', 'day')}>‹D</NavButton>
            <NavButton $variant={variant} onClick={resetToToday} primary>Now</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('add', 'day')}>D›</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('add', 'month')}>M›</NavButton>
          </>
        ) : (
          // Desktop - Full controls
          <>
            <NavButton $variant={variant} onClick={() => handleDateChange('sub', 'year')}>‹‹Y</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('sub', 'month')}>‹M</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('sub', 'week')}>‹W</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('sub', 'day')}>‹D</NavButton>
            
            <NavButton $variant={variant} onClick={resetToToday} primary>Now</NavButton>
            
            <NavButton $variant={variant} onClick={() => handleDateChange('add', 'day')}>D›</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('add', 'week')}>W›</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('add', 'month')}>M›</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('add', 'year')}>Y››</NavButton>
          </>
        )}
      </ButtonGroup>
    </ControlsContainer>
  );
};

export default TransitControls;
