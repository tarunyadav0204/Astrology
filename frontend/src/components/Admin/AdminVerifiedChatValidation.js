import React, { useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

export default function AdminVerifiedChatValidation() {
  const [items, setItems] = useState([]);
  const [failuresOnly, setFailuresOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const query = new URLSearchParams({ limit: '100', failures_only: String(failuresOnly) });
      const response = await fetch(`/api/admin/chat/verified-validations?${query}`, {
        headers: getAdminAuthHeaders(),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || 'Could not load validation results');
      setItems(Array.isArray(body.items) ? body.items : []);
    } catch (err) {
      setError(err.message || 'Could not load validation results');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [failuresOnly]);

  return (
    <div className="admin-chat-analysis">
      <header className="admin-chat-analysis-header">
        <h2>Verified Chat validation</h2>
        <p className="admin-chat-analysis-lead">Audits run after delivery and never change a user response.</p>
      </header>
      <div className="form-buttons" style={{ marginBottom: 14 }}>
        <button type="button" className="create-btn" onClick={() => setFailuresOnly((value) => !value)}>
          {failuresOnly ? 'Show all audits' : 'Show failures only'}
        </button>
        <button type="button" className="secondary-btn" onClick={load}>Refresh</button>
      </div>
      {loading ? <div className="admin-chat-analysis-loading">Loading validation audits…</div> : null}
      {error ? <div className="admin-chat-analysis-error">{error}</div> : null}
      {!loading && !error ? (
        <div className="admin-chat-analysis-table-wrap">
          <table className="admin-table">
            <thead><tr><th>When</th><th>Message</th><th>Status</th><th>Failures</th><th>Model-requested calculations</th><th>Response preview</th></tr></thead>
            <tbody>
              {items.length === 0 ? <tr><td colSpan={6} className="admin-chat-analysis-empty">No validation audits yet.</td></tr> : items.map((item) => (
                <tr key={item.message_id}>
                  <td>{item.created_at ? new Date(item.created_at).toLocaleString() : '—'}</td>
                  <td>#{item.message_id}<br />User {item.user_id}</td>
                  <td>{item.status}</td>
                  <td>
                    {(item.failures || []).length ? (
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap', maxWidth: 360 }}>
                        {JSON.stringify(item.failures, null, 2)}
                      </pre>
                    ) : '—'}
                  </td>
                  <td>
                    {(() => {
                      const packet = (item.evidence_summary || {}).packet_validation || {};
                      const toolEvents = Array.isArray(packet.tool_events) ? packet.tool_events : [];
                      const requested = toolEvents.filter((event) => event?.tool && event.tool !== 'get_instant_baseline');
                      const updates = Array.isArray(packet.calculation_trace) ? packet.calculation_trace : [];
                      return (
                        <>
                          <div style={{ fontWeight: 700 }}>Baseline: Instant deterministic context</div>
                          {requested.length ? requested.map((event, index) => (
                            <div key={`${event.tool}-${index}`} style={{ marginTop: 4 }}>
                              {event.success ? '✓' : '⚠'} Round {event.round}: {event.tool}
                            </div>
                          )) : <div style={{ marginTop: 4 }}>No additional calculator requested.</div>}
                          {updates.length ? (
                            <details style={{ marginTop: 8 }}>
                              <summary>Model calculation updates ({updates.length})</summary>
                              {updates.map((update) => (
                                <div key={update.id} style={{ marginTop: 6 }}>
                                  <strong>{update.title}</strong><br />{update.detail}
                                </div>
                              ))}
                            </details>
                          ) : null}
                          <details style={{ marginTop: 8 }}>
                            <summary>Raw calculation audit</summary>
                            <pre style={{ margin: '6px 0 0', whiteSpace: 'pre-wrap', maxWidth: 360 }}>
                              {JSON.stringify(packet, null, 2)}
                            </pre>
                          </details>
                        </>
                      );
                    })()}
                  </td>
                  <td>{item.response_preview || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
