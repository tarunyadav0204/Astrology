import React, { useCallback, useRef } from 'react';
import { ControlsContainer, DateDisplay, ButtonGroup, NavButton, DatePickerInput } from './TransitControls.styles';

function formatLocalDateForInput(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

const TransitControls = ({ date, onChange, onResetToToday, variant = 'default' }) => {
  const dateInputRef = useRef(null);
  const isMobile = typeof window !== 'undefined' && window.innerWidth <= 768;

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

  const handleNativeDateChange = useCallback(
    (e) => {
      const v = e.target.value;
      if (!v) return;
      const [yy, mm, dd] = v.split('-').map(Number);
      onChange(new Date(yy, mm - 1, dd, 12, 0, 0, 0));
    },
    [onChange]
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

  const dateLabel = isMobile
    ? date.toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
    : date.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });

  return (
    <ControlsContainer>
      <DatePickerInput
        ref={dateInputRef}
        type="date"
        value={formatLocalDateForInput(date)}
        onChange={handleNativeDateChange}
        tabIndex={-1}
        aria-hidden="true"
      />
      <DateDisplay
        as="button"
        type="button"
        $variant={variant}
        $clickable
        onClick={openDatePicker}
        onDoubleClick={(e) => {
          e.preventDefault();
          resetToToday();
        }}
        title="Open calendar — double-click for today"
        aria-label={`As-of date ${dateLabel}. Open calendar to pick a date.`}
      >
        {dateLabel}
      </DateDisplay>
      
      <ButtonGroup>
        {isMobile ? (
          <>
            <NavButton $variant={variant} onClick={() => handleDateChange('sub', 'month')}>‹M</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('sub', 'day')}>‹D</NavButton>
            <NavButton $variant={variant} onClick={resetToToday} primary>Now</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('add', 'day')}>D›</NavButton>
            <NavButton $variant={variant} onClick={() => handleDateChange('add', 'month')}>M›</NavButton>
          </>
        ) : (
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
