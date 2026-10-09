import React, { useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './ModelSettings.css';

export default function ModelSettings({ groups, advanced }) {
  const [saving, setSaving] = useState(null);
  const [feedback, setFeedback] = useState({});
  const renderGroup = group => <section className="model-settings-card" key={group.id} aria-labelledby={`model-group-${group.id}`}>
    <header><div><h3 id={`model-group-${group.id}`}>{group.title}</h3><p>{group.description}</p></div>{group.providerLabel && <span className="model-settings-provider">{group.providerLabel}</span>}</header>
    <div className="model-settings-fields">{group.fields.map(field => <label key={field.key}>
      <span>{field.label}</span>
      {field.type === 'checkbox' ? <input type="checkbox" checked={field.value} disabled={Boolean(saving)} onChange={event => field.set(event.target.checked)} /> : field.options ? <select value={field.value || ''} disabled={Boolean(saving)} onChange={event => field.set(event.target.value)}>
        {field.value && !field.options.some(option => option.value === field.value) && <option value={field.value}>{field.value} (current)</option>}
        {field.options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select> : <input type={field.type || 'text'} value={field.value || ''} disabled={Boolean(saving)} min={field.min} max={field.max} onChange={event => field.set(event.target.value)} />}
      {field.hint && <small>{field.hint}</small>}
    </label>)}</div>
    <footer><button type="button" disabled={Boolean(saving) || group.fields.some(field => field.required !== false && field.type !== 'checkbox' && !field.value)} onClick={async () => {
      setSaving(group.id); setFeedback(previous => ({ ...previous, [group.id]: null }));
      try {
        for (const field of group.fields) {
          const response = await fetch(`/api/admin/settings/${field.key}`, { method: 'PUT', headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ key: field.key, value: String(field.value ?? ''), description: `${group.title}: ${field.label}` }) });
          if (!response.ok) { const data = await response.json().catch(() => ({})); throw new Error(data.detail || `Could not save ${field.label}.`); }
        }
        setFeedback(previous => ({ ...previous, [group.id]: { ok: true, text: `${group.title} settings saved.` } }));
      } catch (error) { setFeedback(previous => ({ ...previous, [group.id]: { ok: false, text: error.message } })); }
      finally { setSaving(null); }
    }}>{saving === group.id ? 'Saving…' : `Save ${group.title.toLowerCase()}`}</button>
      {feedback[group.id] && <span role={feedback[group.id].ok ? 'status' : 'alert'}>{feedback[group.id].text}</span>}
    </footer>
  </section>;
  return <div className="model-settings"><div className="model-settings-intro"><h2>Models by feature</h2><p>Choose a provider and model for each feature. Save each card separately. Changes apply to new requests.</p></div>
    <div className="model-settings-grid">{groups.map(renderGroup)}</div>
    <details className="model-settings-advanced"><summary>Advanced: Verified routing and specialist branches</summary><p>These models prepare evidence or choose how to handle a question. They do not replace the final-answer models above.</p><div className="model-settings-grid">{advanced.map(renderGroup)}</div></details>
  </div>;
}
