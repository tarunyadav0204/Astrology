import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/apiService';

export default function DeskTopicSelector({ value = 'whole_chart', onChange, compact = false }) {
  const [topics, setTopics] = useState([]);

  useEffect(() => {
    let cancelled = false;
    apiService.getParashariTopics()
      .then((result) => {
        if (!cancelled) setTopics((result?.topics || []).filter((topic) => topic.status === 'active'));
      })
      .catch(() => {
        if (!cancelled) setTopics([{ key: 'health', label: 'Health', short_label: 'Health' }]);
      });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className={`parashari-topic-selector${compact ? ' parashari-topic-selector--compact' : ''}`}>
      <span className="parashari-topic-selector__label">Studying</span>
      <div className="parashari-topic-selector__options" role="radiogroup" aria-label="Choose a chart topic">
        <button
          type="button"
          role="radio"
          aria-checked={value === 'whole_chart'}
          className={value === 'whole_chart' ? 'is-active' : ''}
          onClick={() => onChange?.('whole_chart', null)}
        >
          Whole chart
        </button>
        {topics.map((topic) => (
          <button
            type="button"
            role="radio"
            aria-checked={value === topic.key}
            className={value === topic.key ? 'is-active' : ''}
            onClick={() => onChange?.(topic.key, topic)}
            key={topic.key}
            title={topic.description}
          >
            {topic.short_label || topic.label}
          </button>
        ))}
      </div>
      {value !== 'whole_chart' ? <span className="parashari-topic-selector__mode">Topic Lens</span> : null}
    </div>
  );
}
