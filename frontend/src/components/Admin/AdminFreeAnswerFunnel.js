import React, { useCallback, useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminFreeAnswerFunnel.css';

function defaultRange() {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 30);
  const fmt = (d) => d.toISOString().slice(0, 10);
  return { from: fmt(from), to: fmt(to) };
}

export default function AdminFreeAnswerFunnel() {
  const initial = defaultRange();
  const [fromDate, setFromDate] = useState(initial.from);
  const [toDate, setToDate] = useState(initial.to);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams();
      if (fromDate) qs.set('from_date', fromDate);
      if (toDate) qs.set('to_date', toDate);
      const res = await fetch(`/api/credits/admin/free-answer-funnel?${qs}`, {
        headers: getAdminAuthHeaders(),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || body.message || 'Failed to load funnel');
      }
      setData(body);
    } catch (e) {
      setError(e.message || 'Failed to load');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [fromDate, toDate]);

  useEffect(() => {
    load();
  }, [load]);

  const steps = data?.steps || [];

  return (
    <div className="admin-free-answer-funnel">
      <div className="faf-header">
        <div>
          <h3>Free answer → reveal → purchase</h3>
          <p>
            Users who got a free standard answer with blurred detail, tapped reveal, then bought credits
            (within 7 days of reveal).
          </p>
        </div>
        <div className="faf-filters">
          <label>
            From
            <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
          </label>
          <label>
            To
            <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
          </label>
          <button type="button" onClick={load} disabled={loading}>
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && <div className="faf-error">{error}</div>}

      <div className="faf-steps">
        {steps.map((step, idx) => (
          <div className="faf-step" key={step.event_name}>
            <div className="faf-step-num">{idx + 1}</div>
            <div className="faf-step-body">
              <div className="faf-step-label">{step.label}</div>
              <div className="faf-step-users">{step.unique_users} users</div>
              <div className="faf-step-meta">
                {step.events} events
                {step.conversion_from_blur_pct != null
                  ? ` · ${step.conversion_from_blur_pct}% of blur viewers`
                  : ''}
              </div>
            </div>
            {idx < steps.length - 1 && <div className="faf-arrow">→</div>}
          </div>
        ))}
      </div>

      {data?.reveal_to_purchase_pct != null && (
        <div className="faf-summary">
          Reveal → purchase conversion:{' '}
          <strong>{data.reveal_to_purchase_pct}%</strong>
        </div>
      )}
    </div>
  );
}
