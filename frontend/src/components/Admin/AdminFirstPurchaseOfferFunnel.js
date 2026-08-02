import React, { useCallback, useEffect, useRef, useState } from 'react';
import { getAdminAuthHeaders, getAdminEndpoint } from '../../services/adminService';
import './AdminFreeAnswerFunnel.css';

function dateValue(offset = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata' }).formatToParts(d);
  const values = Object.fromEntries(parts.map((p) => [p.type, p.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

export default function AdminFirstPurchaseOfferFunnel() {
  const [fromDate, setFromDate] = useState(dateValue(-30));
  const [toDate, setToDate] = useState(dateValue());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const requestId = useRef(0);

  const load = useCallback(async () => {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams({ _ts: String(Date.now()) });
      if (fromDate) qs.set('from_date', fromDate);
      if (toDate) qs.set('to_date', toDate);
      const response = await fetch(`${getAdminEndpoint('/credits/admin/first-purchase-offer-funnel')}?${qs}`, {
        headers: { ...getAdminAuthHeaders(), 'Cache-Control': 'no-cache', Pragma: 'no-cache' },
        cache: 'no-store',
      });
      const body = await response.json().catch(() => ({}));
      if (id !== requestId.current) return;
      if (!response.ok) throw new Error(body.detail || 'Failed to load offer funnel');
      setData(body);
    } catch (e) {
      if (id === requestId.current) { setError(e.message || 'Failed to load'); setData(null); }
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }, [fromDate, toDate]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="admin-free-answer-funnel">
      <div className="faf-header">
        <div>
          <h3>First-purchase offer funnel</h3>
          <p>Offer shown → credits opened → completed purchase. Dates define when the offer was shown; later conversions stay attributed to that offer.</p>
        </div>
        <div className="faf-filters">
          <label>From<input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} /></label>
          <label>To<input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} /></label>
          <button type="button" onClick={load} disabled={loading}>{loading ? 'Loading…' : 'Refresh'}</button>
        </div>
      </div>
      <div className="faf-summary">Applied IST range: <strong>{data?.from_date || fromDate}</strong> → <strong>{data?.to_date || toDate}</strong></div>
      {error && <div className="faf-error">{error}</div>}
      <div className="faf-steps">
        {(data?.steps || []).map((step, index) => (
          <div className="faf-step" key={step.event_name}>
            <div className="faf-step-num">{index + 1}</div>
            <div className="faf-step-body">
              <div className="faf-step-label">{step.label}</div>
              <div className="faf-step-users">{step.unique_users} users</div>
              <div className="faf-step-meta">{step.events} events{step.conversion_from_offer_pct != null ? ` · ${step.conversion_from_offer_pct}% of offer viewers` : ''}</div>
            </div>
            {index < (data?.steps || []).length - 1 && <div className="faf-arrow">→</div>}
          </div>
        ))}
      </div>
      {data?.click_to_purchase_pct != null && <div className="faf-summary">Click → purchase conversion: <strong>{data.click_to_purchase_pct}%</strong></div>}
    </div>
  );
}
