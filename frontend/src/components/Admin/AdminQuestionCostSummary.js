import React, { useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

function toLocalDateStr(date) {
  const y = date.getFullYear();
  const mo = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${mo}-${d}`;
}

function todayRange() {
  const now = new Date();
  return {
    from: toLocalDateStr(now),
    to: toLocalDateStr(now),
  };
}

export default function AdminQuestionCostSummary() {
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);

  const load = async (from, to) => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (from) params.set('from_date', from);
      if (to) params.set('to_date', to);
      const res = await fetch(`/api/credits/admin/question-cost-summary?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
      }
      setData(await res.json());
    } catch (e) {
      setError(e.message || 'Failed to load question cost summary');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const r = todayRange();
    setFromDate(r.from);
    setToDate(r.to);
    load(r.from, r.to);
  }, []);

  const s = data?.summary || {};
  const models = data?.model_breakdown || [];
  const questionSplitRows = [
    {
      key: 'paid',
      type: 'Paid questions',
      count: Number(s.questions_paid || 0),
      credits: Number(s.credits_charged || 0),
      money: Number(s.money_charged_inr || 0),
    },
    {
      key: 'free',
      type: 'Free first questions (estimated)',
      count: Number(s.questions_free_estimated || 0),
      credits: Number(s.credits_free_equivalent || 0),
      money: Number(s.money_free_equivalent_inr || 0),
    },
  ];

  return (
    <div className="credits-dashboard">
      <h2>Question Cost Summary</h2>
      <p className="credit-settings-hint">
        Includes paid questions and estimated free-first questions. Default range is <strong>today</strong>. Rule: <strong>1 credit = INR 1</strong>.
      </p>

      <div className="dashboard-controls">
        <div className="custom-dates">
          <label>
            From <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
          </label>
          <label>
            To <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
          </label>
          <button type="button" className="preset-btn active" onClick={() => load(fromDate, toDate)} disabled={loading}>
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && <div className="credits-dashboard-error">{error}</div>}

      {data && (
        <>
          <div className="metrics-grid question-cost-metrics-grid">
            <div className="metric-card">
              <h4>Questions</h4>
              <p>{s.questions_total ?? 0}</p>
              <small>Paid: {s.questions_paid ?? 0} | Free: {s.questions_free_estimated ?? 0}</small>
            </div>
            <div className="metric-card">
              <h4>Credits Charged</h4>
              <p>{s.credits_charged ?? 0}</p>
              <small>Free eq: {s.credits_free_equivalent ?? 0}</small>
            </div>
            <div className="metric-card">
              <h4>Money Charged</h4>
              <p>INR {(s.money_charged_inr ?? 0).toFixed(2)}</p>
              <small>Total eq: INR {(s.money_total_equivalent_inr ?? 0).toFixed(2)}</small>
            </div>
            <div className="metric-card">
              <h4>AI Cost (rough)</h4>
              <p>INR {(s.ai_cost_inr_estimate ?? 0).toFixed(4)}</p>
              <small>
                NC In: INR {(s.input_cost_non_cached_inr_estimate ?? 0).toFixed(4)} | C In: INR{' '}
                {(s.input_cost_cached_inr_estimate ?? 0).toFixed(4)}
              </small>
              <small>
                Cache setup: INR {(s.cache_setup_cost_inr_estimate ?? 0).toFixed(4)} | Out: INR{' '}
                {(s.output_cost_inr_estimate ?? 0).toFixed(4)}
              </small>
              <small>Gross margin est: INR {(s.gross_margin_inr_estimate ?? 0).toFixed(4)}</small>
            </div>
          </div>

          <div className="transactions-table wrap question-cost-table-wrap">
            <h3 className="question-cost-section-title">Paid vs Free Question Split</h3>
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Questions</th>
                  <th>Credits</th>
                  <th>Money (INR)</th>
                </tr>
              </thead>
              <tbody>
                {questionSplitRows.map((row) => (
                  <tr key={row.key}>
                    <td>{row.type}</td>
                    <td>{row.count}</td>
                    <td>{row.credits.toFixed(2)}</td>
                    <td>INR {row.money.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="transactions-table wrap question-cost-table-wrap">
            <h3 className="question-cost-section-title">Model Cost Breakdown</h3>
            <table>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Questions</th>
                  <th>Question tokens (total)</th>
                  <th>Question tokens (cached)</th>
                  <th>Question tokens (non-cached)</th>
                  <th>Cache setup tokens</th>
                  <th>Answer tokens (est)</th>
                  <th>NC In Cost (INR)</th>
                  <th>C In Cost (INR)</th>
                  <th>Cache Setup Cost (INR)</th>
                  <th>Out Cost (INR)</th>
                  <th>AI Cost (INR, est)</th>
                </tr>
              </thead>
              <tbody>
                {models.length === 0 ? (
                  <tr>
                    <td colSpan={12}>No model data for selected range.</td>
                  </tr>
                ) : (
                  models.map((m) => (
                    <tr key={m.model}>
                      <td>{m.model}</td>
                      <td>{m.questions}</td>
                      <td>{m.input_tokens_estimate}</td>
                      <td>{Number(m.cached_input_tokens || 0)}</td>
                      <td>{Number(m.non_cached_input_tokens || 0)}</td>
                      <td>{Number(m.cache_setup_input_tokens || 0)}</td>
                      <td>{m.output_tokens_estimate}</td>
                      <td>INR {Number(m.input_cost_non_cached_inr_estimate || 0).toFixed(4)}</td>
                      <td>INR {Number(m.input_cost_cached_inr_estimate || 0).toFixed(4)}</td>
                      <td>INR {Number(m.cache_setup_cost_inr_estimate || 0).toFixed(4)}</td>
                      <td>INR {Number(m.output_cost_inr_estimate || 0).toFixed(4)}</td>
                      <td>INR {Number(m.ai_cost_inr_estimate || 0).toFixed(4)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <p className="credit-settings-hint question-cost-note">
            {data.note} Token columns are question-vs-answer content estimates, so answer tokens can be higher.
          </p>
        </>
      )}
    </div>
  );
}

