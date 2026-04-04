import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './MonthlyEventAccordion.css';

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function monthLabel(monthId) {
  if (!monthId || monthId < 1 || monthId > 12) return `Month ${monthId}`;
  return MONTH_NAMES[monthId - 1];
}

function intensityClass(intensity) {
  const v = String(intensity || '').toLowerCase();
  if (v.includes('high') || v.includes('strong')) return 'is-high';
  if (v.includes('low') || v.includes('mild')) return 'is-low';
  return 'is-mid';
}

/**
 * Single month block — mirrors mobile MonthlyAccordion structure.
 */
export default function MonthlyEventAccordion({ data, yearLabel, onDiveDeep }) {
  const [expanded, setExpanded] = useState(false);
  const navigate = useNavigate();

  if (!data) return null;

  const tags = data.focus_areas || [];
  const events = data.events || [];
  const monthTitle = data.month || monthLabel(data.month_id);

  const openChatWithMonth = () => {
    let text = `${monthTitle} ${yearLabel} — predictions:\n\n`;
    if (events.length) {
      events.forEach((event, idx) => {
        text += `${idx + 1}. ${event.type}\n${event.prediction || ''}\n`;
        if (event.start_date && event.end_date) text += `Period: ${event.start_date} → ${event.end_date}\n`;
        text += '\n';
      });
    }
    text += 'Please explain these in more detail for my chart.';
    navigate('/chat', {
      state: { openSingleChartChat: true, followUpQuestion: text.trim() }
    });
  };

  return (
    <div className="monthly-event-accordion">
      <button
        type="button"
        className={`monthly-event-accordion__header ${expanded ? 'is-open' : ''}`}
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <span className="monthly-event-accordion__month">{monthTitle}</span>
        <span className="monthly-event-accordion__chevron" aria-hidden>
          {expanded ? '▴' : '▾'}
        </span>
      </button>

      {!expanded && tags.length > 0 && (
        <div className="monthly-event-accordion__chips" aria-label="Focus areas">
          {tags.map((tag, i) => (
            <span key={i} className="monthly-event-accordion__chip">
              {tag}
            </span>
          ))}
        </div>
      )}

      {expanded && (
        <div className="monthly-event-accordion__body">
          {tags.length > 0 && (
            <div className="monthly-event-accordion__focus">
              <span className="monthly-event-accordion__focus-label">Focus</span>
              <div className="monthly-event-accordion__focus-tags">
                {tags.map((tag, i) => (
                  <span key={i} className="monthly-event-accordion__chip monthly-event-accordion__chip--full">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="monthly-event-accordion__events">
            {events.map((event, index) => (
              <div key={index} className="monthly-event-accordion__event">
                <span className={`monthly-event-accordion__dot ${intensityClass(event.intensity)}`} />
                <div className="monthly-event-accordion__event-main">
                  <h4 className="monthly-event-accordion__event-type">{event.type}</h4>
                  <p className="monthly-event-accordion__event-pred">{event.prediction}</p>
                  {event.possible_manifestations?.length > 0 && (
                    <div className="monthly-event-accordion__manifest">
                      <div className="monthly-event-accordion__manifest-title">
                        Possible scenarios ({event.possible_manifestations.length})
                      </div>
                      <ul className="monthly-event-accordion__manifest-list">
                        {event.possible_manifestations.map((item, idx) => {
                          const scenario = typeof item === 'string' ? item : item?.scenario;
                          const reasoning = typeof item === 'object' && item ? item.reasoning : null;
                          return (
                            <li key={idx} className="monthly-event-accordion__manifest-item">
                              <span className="monthly-event-accordion__manifest-num">{idx + 1}</span>
                              <div>
                                {scenario && <p className="monthly-event-accordion__manifest-text">{scenario}</p>}
                                {reasoning && (
                                  <p className="monthly-event-accordion__reasoning">
                                    <strong>Why:</strong> {reasoning}
                                  </p>
                                )}
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  )}
                  {event.start_date && event.end_date && (
                    <p className="monthly-event-accordion__dates">
                      📅 {event.start_date} → {event.end_date}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="monthly-event-accordion__actions">
            <button type="button" className="monthly-event-accordion__btn monthly-event-accordion__btn--chat" onClick={openChatWithMonth}>
              💬 Ask Tara about this month
            </button>
            {onDiveDeep && (
              <button
                type="button"
                className="monthly-event-accordion__btn monthly-event-accordion__btn--secondary"
                onClick={() => onDiveDeep(data)}
              >
                🔭 Explore this month in depth
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
