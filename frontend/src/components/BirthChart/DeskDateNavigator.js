import React, { useState } from 'react';
import './DeskDateNavigator.css';

/**
 * Compact as-of stepper (mobile ChartsHub / CascadingDasha pattern).
 * Year/month/day steppers with optional ±H and Today reset.
 */
export default function DeskDateNavigator({
  date,
  onChange,
  onResetToToday,
  showTime = true,
}) {
  const [picking, setPicking] = useState(false);
  const safe = date instanceof Date && !Number.isNaN(date.getTime()) ? date : new Date();

  const emit = (next) => {
    if (typeof onChange === 'function') onChange(next);
  };

  const shift = (amount, unit = 'day') => {
    const next = new Date(safe);
    if (unit === 'hour') {
      next.setHours(next.getHours() + amount);
    } else if (unit === 'month' || unit === 'year') {
      // Clamp month/year jumps so Jan 31 → Feb 28/29 instead of spilling into March.
      const wantedDay = next.getDate();
      next.setDate(1);
      if (unit === 'month') next.setMonth(next.getMonth() + amount);
      else next.setFullYear(next.getFullYear() + amount);
      const lastDay = new Date(next.getFullYear(), next.getMonth() + 1, 0).getDate();
      next.setDate(Math.min(wantedDay, lastDay));
    } else {
      next.setDate(next.getDate() + amount);
    }
    emit(next);
  };

  const dateLabel = safe.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: '2-digit',
  });
  const timeLabel = safe.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });

  const toInputDate = () => {
    const y = safe.getFullYear();
    const m = String(safe.getMonth() + 1).padStart(2, '0');
    const d = String(safe.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  };

  const toInputTime = () => {
    const h = String(safe.getHours()).padStart(2, '0');
    const m = String(safe.getMinutes()).padStart(2, '0');
    return `${h}:${m}`;
  };

  return (
    <div className="desk-date-nav">
      <div className="desk-date-nav__row desk-date-nav__row--jump" aria-label="Month and year navigation">
        <button type="button" className="desk-date-nav__step" onClick={() => shift(-1, 'year')} title="Previous year">
          ‹Y
        </button>
        <button type="button" className="desk-date-nav__step" onClick={() => shift(-1, 'month')} title="Previous month">
          ‹M
        </button>
        <span className="desk-date-nav__period">
          {safe.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}
        </span>
        <button type="button" className="desk-date-nav__step" onClick={() => shift(1, 'month')} title="Next month">
          M›
        </button>
        <button type="button" className="desk-date-nav__step" onClick={() => shift(1, 'year')} title="Next year">
          Y›
        </button>
      </div>
      <div className="desk-date-nav__row">
        <button type="button" className="desk-date-nav__step" onClick={() => shift(-1)} title="Previous day">
          ‹D
        </button>
        <button
          type="button"
          className="desk-date-nav__value"
          onClick={() => setPicking((open) => !open)}
          title="Pick date"
        >
          {dateLabel}
        </button>
        <button type="button" className="desk-date-nav__step" onClick={() => shift(1)} title="Next day">
          D›
        </button>
        <button
          type="button"
          className="desk-date-nav__today"
          onClick={() => (onResetToToday ? onResetToToday() : emit(new Date()))}
        >
          Today
        </button>
      </div>
      {showTime ? (
        <div className="desk-date-nav__row desk-date-nav__row--time">
          <button type="button" className="desk-date-nav__step" onClick={() => shift(-1, 'hour')} title="−1 hour">
            ‹H
          </button>
          <span className="desk-date-nav__value desk-date-nav__value--static">{timeLabel}</span>
          <button type="button" className="desk-date-nav__step" onClick={() => shift(1, 'hour')} title="+1 hour">
            H›
          </button>
        </div>
      ) : null}
      {picking ? (
        <div className="desk-date-nav__pickers">
          <label>
            <span>Date</span>
            <input
              type="date"
              value={toInputDate()}
              onChange={(e) => {
                const [y, m, d] = e.target.value.split('-').map(Number);
                if (!y) return;
                const next = new Date(safe);
                next.setFullYear(y, m - 1, d);
                emit(next);
              }}
            />
          </label>
          {showTime ? (
            <label>
              <span>Time</span>
              <input
                type="time"
                value={toInputTime()}
                onChange={(e) => {
                  const [h, mi] = e.target.value.split(':').map(Number);
                  const next = new Date(safe);
                  next.setHours(h || 0, mi || 0, 0, 0);
                  emit(next);
                }}
              />
            </label>
          ) : null}
          <button type="button" onClick={() => setPicking(false)}>Done</button>
        </div>
      ) : null}
    </div>
  );
}
