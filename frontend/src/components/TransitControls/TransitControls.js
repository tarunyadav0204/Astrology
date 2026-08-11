import React, { useCallback, useRef } from 'react';
import { ControlsContainer, DateDisplay, ButtonGroup, NavButton, DatePickerInput, TimeInput } from './TransitControls.styles';

function formatLocalDateForInput(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function formatLocalTimeForInput(date) {
  const h = String(date.getHours()).padStart(2, '0');
  const m = String(date.getMinutes()).padStart(2, '0');
  return `${h}:${m}`;
}

function withPreservedTime(base, year, monthIndex, day) {
  return new Date(
    year,
    monthIndex,
    day,
    base.getHours(),
    base.getMinutes(),
    base.getSeconds(),
    base.getMilliseconds()
  );
}

const TransitControls = ({
  date,
  onChange,
  onResetToToday,
  variant = 'default',
  textColor,
  primaryColor,
  /** When true, show HH:MM and ±H — used by Parashari desk shared clock */
  showTime = false,
}) => {
  const dateInputRef = useRef(null);
  const isMobile = typeof window !== 'undefined' && window.innerWidth <= 768;

  const handleDateChange = (operation, unit) => {
    const newDate = new Date(date);

    switch (operation) {
      case 'add':
        switch (unit) {
          case 'hour': newDate.setHours(newDate.getHours() + 1); break;
          case 'day': newDate.setDate(newDate.getDate() + 1); break;
          case 'week': newDate.setDate(newDate.getDate() + 7); break;
          case 'month': newDate.setMonth(newDate.getMonth() + 1); break;
          case 'year': newDate.setFullYear(newDate.getFullYear() + 1); break;
          default: return;
        }
        break;
      case 'sub':
        switch (unit) {
          case 'hour': newDate.setHours(newDate.getHours() - 1); break;
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
      if (showTime) {
        onChange(withPreservedTime(date, yy, mm - 1, dd));
      } else {
        onChange(new Date(yy, mm - 1, dd, 12, 0, 0, 0));
      }
    },
    [onChange, date, showTime]
  );

  const handleNativeTimeChange = useCallback(
    (e) => {
      const v = e.target.value;
      if (!v) return;
      const [hh, mm] = v.split(':').map(Number);
      const next = new Date(date);
      next.setHours(hh || 0, mm || 0, 0, 0);
      onChange(next);
    },
    [onChange, date]
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

  const timeLabel = formatLocalTimeForInput(date);

  return (
    <ControlsContainer style={primaryColor ? { '--transit-primary-color': primaryColor } : undefined}>
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
        $textColor={textColor}
        $clickable
        onClick={openDatePicker}
        onDoubleClick={(e) => {
          e.preventDefault();
          resetToToday();
        }}
        title="Open calendar — double-click for now"
        aria-label={`As-of date ${dateLabel}. Open calendar to pick a date.`}
      >
        {dateLabel}
      </DateDisplay>

      {showTime ? (
        <TimeInput
          type="time"
          value={timeLabel}
          onChange={handleNativeTimeChange}
          $variant={variant}
          $textColor={textColor}
          title="As-of time"
          aria-label={`As-of time ${timeLabel}`}
        />
      ) : null}

      <ButtonGroup>
        {isMobile ? (
          <>
            {showTime ? (
              <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('sub', 'hour')}>‹H</NavButton>
            ) : null}
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('sub', 'month')}>‹M</NavButton>
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('sub', 'day')}>‹D</NavButton>
            <NavButton $variant={variant} $textColor={textColor} onClick={resetToToday} primary>Now</NavButton>
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('add', 'day')}>D›</NavButton>
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('add', 'month')}>M›</NavButton>
            {showTime ? (
              <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('add', 'hour')}>H›</NavButton>
            ) : null}
          </>
        ) : (
          <>
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('sub', 'year')}>‹‹Y</NavButton>
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('sub', 'month')}>‹M</NavButton>
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('sub', 'week')}>‹W</NavButton>
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('sub', 'day')}>‹D</NavButton>
            {showTime ? (
              <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('sub', 'hour')}>‹H</NavButton>
            ) : null}

            <NavButton $variant={variant} $textColor={textColor} onClick={resetToToday} primary>Now</NavButton>

            {showTime ? (
              <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('add', 'hour')}>H›</NavButton>
            ) : null}
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('add', 'day')}>D›</NavButton>
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('add', 'week')}>W›</NavButton>
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('add', 'month')}>M›</NavButton>
            <NavButton $variant={variant} $textColor={textColor} onClick={() => handleDateChange('add', 'year')}>Y››</NavButton>
          </>
        )}
      </ButtonGroup>
    </ControlsContainer>
  );
};

export default TransitControls;
