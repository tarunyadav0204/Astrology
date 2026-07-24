import React, { useCallback, useEffect, useRef, useState } from 'react';
import { getAdminAuthHeaders, getAdminEndpoint } from '../../services/adminService';
import './AdminFreeAnswerFunnel.css';

function formatLocalDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function defaultRange() {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 30);
  return { from: formatLocalDate(from), to: formatLocalDate(to) };
}

export default function AdminRemedyFunnel() {
  const initial = defaultRange();
  const [fromDate, setFromDate] = useState(initial.from);
  const [toDate, setToDate] = useState(initial.to);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const requestIdRef = useRef(0);

  const load = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams();
      if (fromDate) qs.set('from_date', fromDate);
      if (toDate) qs.set('to_date', toDate);
      qs.set('_ts', String(Date.now()));
      const res = await fetch(`${getAdminEndpoint('/credits/admin/remedy-funnel')}?${qs}`, {
        headers: {
          ...getAdminAuthHeaders(),
          'Cache-Control': 'no-cache',
          Pragma: 'no-cache',
        },
        cache: 'no-store',
      });
      const body = await res.json().catch(() => ({}));
      if (requestId !== requestIdRef.current) return;
      if (!res.ok) {
        throw new Error(body.detail || body.message || 'Failed to load funnel');
      }
      setData(body);
    } catch (e) {
      if (requestId !== requestIdRef.current) return;
      setError(e.message || 'Failed to load');
      setData(null);
    } finally {
      if (requestId === requestIdRef.current) setLoading(false);
    }
  }, [fromDate, toDate]);

  useEffect(() => {
    load();
  }, [load]);

  const steps = data?.steps || [];
  const appliedFrom = data?.from_date || fromDate;
  const appliedTo = data?.to_date || toDate;

  return (
    <div className="admin-free-answer-funnel">
      <div className="faf-header">
        <div>
          <h3>Remedy card → tap → remedy answer</h3>
          <p>
            Counts answers that included a remedy CTA (next_action type = remedy), then taps and
            remedy-only follow-ups for those same messages. Date range filters by answer completion
            date.
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

      <div className="faf-summary" style={{ marginBottom: 12 }}>
        Applied range: <strong>{appliedFrom || '—'}</strong> → <strong>{appliedTo || '—'}</strong>
        {data?.impression_source ? ` · source: ${data.impression_source}` : ''}
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
                {step.conversion_from_card_shown_pct != null
                  ? ` · ${step.conversion_from_card_shown_pct}% of card viewers`
                  : ''}
              </div>
            </div>
            {idx < steps.length - 1 && <div className="faf-arrow">→</div>}
          </div>
        ))}
      </div>

      {data?.click_to_delivered_pct != null && (
        <div className="faf-summary">
          Tap → remedy answer conversion:{' '}
          <strong>{data.click_to_delivered_pct}%</strong>
        </div>
      )}
    </div>
  );
}
