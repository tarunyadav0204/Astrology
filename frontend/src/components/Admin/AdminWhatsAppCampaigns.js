import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import AdminWhatsAppTemplates from './AdminWhatsAppTemplates';
import './AdminWhatsAppCampaigns.css';

const apiError = async (response, fallback) => {
  const data = await response.json().catch(() => ({}));
  return data.detail || data.message || fallback;
};

const fmtDate = (value) => {
  if (!value) return '—';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? '—' : parsed.toLocaleString('en-IN');
};

const titleCase = (value) => String(value || '—').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

export default function AdminWhatsAppCampaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [showComposer, setShowComposer] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [report, setReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportFilter, setReportFilter] = useState('all');

  const load = useCallback(async () => {
    setError('');
    try {
      const response = await fetch('/api/nudge/admin/campaigns?limit=500', { headers: getAdminAuthHeaders() });
      if (!response.ok) throw new Error(await apiError(response, 'Could not load campaigns'));
      const data = await response.json();
      setCampaigns((data.items || []).filter((item) => item.whatsapp_template));
    } catch (err) {
      setError(err.message || 'Could not load campaigns');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!campaigns.some((campaign) => campaign.status === 'sending')) return undefined;
    const timer = window.setInterval(load, 5000);
    return () => window.clearInterval(timer);
  }, [campaigns, load]);

  const action = async (campaign, kind) => {
    if (kind === 'delete' && !window.confirm(`Delete campaign #${campaign.id} “${campaign.name}”?`)) return;
    if (kind === 'send' && !window.confirm(`Start sending “${campaign.name}” now?`)) return;
    setBusyId(campaign.id);
    setError('');
    setNotice('');
    try {
      let path = `/api/nudge/admin/campaigns/${campaign.id}`;
      let options = { method: 'POST', headers: getAdminAuthHeaders() };
      if (kind === 'send') path += '/send-now';
      if (kind === 'retry') path += '/retry-failed';
      if (kind === 'duplicate') path += '/duplicate';
      if (kind === 'pause' || kind === 'resume') {
        path += '/status';
        options = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getAdminAuthHeaders() },
          body: JSON.stringify({ status: kind === 'pause' ? 'paused' : (campaign.scheduled_at ? 'scheduled' : 'draft') }),
        };
      }
      if (kind === 'delete') options = { method: 'DELETE', headers: getAdminAuthHeaders() };
      const response = await fetch(path, options);
      if (!response.ok) throw new Error(await apiError(response, `Could not ${kind} campaign`));
      setNotice(kind === 'duplicate' ? 'Campaign duplicated as a draft.' : `Campaign ${kind} action completed.`);
      await load();
    } catch (err) {
      setError(err.message || `Could not ${kind} campaign`);
    } finally {
      setBusyId(null);
    }
  };

  const openReport = async (campaign) => {
    setReport({ campaign, recipients: [], stats: null });
    setReportLoading(true);
    setReportFilter('all');
    try {
      const response = await fetch(`/api/nudge/admin/campaigns/${campaign.id}/recipients`, { headers: getAdminAuthHeaders() });
      if (!response.ok) throw new Error(await apiError(response, 'Could not load campaign activity'));
      setReport(await response.json());
    } catch (err) {
      setReport((current) => ({ ...current, error: err.message || 'Could not load campaign activity' }));
    } finally {
      setReportLoading(false);
    }
  };

  const filteredRecipients = useMemo(() => {
    const rows = report?.recipients || [];
    if (reportFilter === 'all') return rows;
    if (reportFilter === 'converted') return rows.filter((row) => row.converted);
    if (reportFilter === 'failed') return rows.filter((row) => row.meta_status === 'failed' || row.send_status === 'failed' || row.state === 'dead');
    return rows.filter((row) => row.meta_status === reportFilter);
  }, [report, reportFilter]);

  return (
    <div className="wa-campaign-admin">
      <header className="wa-campaign-hero">
        <div><span>Campaigns / WhatsApp campaigns</span><h2>WhatsApp campaigns</h2><p>Approved Meta templates, isolated audience reads, queued delivery and recipient-level outcomes.</p></div>
        <div><button type="button" onClick={load} disabled={loading}>Refresh</button><button type="button" className="is-primary" onClick={() => setShowComposer((value) => !value)}>{showComposer ? 'Close composer' : 'Create campaign'}</button></div>
      </header>
      {error && <div className="wa-campaign-alert is-error">{error}</div>}
      {notice && <div className="wa-campaign-alert is-success">{notice}</div>}
      {showComposer && <section className="wa-campaign-composer"><AdminWhatsAppTemplates campaignOnly onCampaignCreated={() => { setShowComposer(false); load(); }} /></section>}

      <section className="wa-campaign-list">
        <div className="wa-campaign-list-heading"><div><h3>Campaign history</h3><p>Meta delivery metrics appear as webhook receipts arrive.</p></div><strong>{campaigns.length}</strong></div>
        {loading && <div className="wa-campaign-empty">Loading campaigns…</div>}
        {!loading && !campaigns.length && <div className="wa-campaign-empty">No WhatsApp campaigns yet.</div>}
        {campaigns.map((campaign) => {
          const sends = campaign.stats?.sends || {};
          const audienceCount = campaign.audience_filter?.user_ids?.length || campaign.total_targeted || 0;
          return <article className="wa-campaign-card" key={campaign.id}>
            <div className="wa-campaign-card-top">
              <div><div className="wa-campaign-name"><h3>{campaign.name}</h3><span className={`status-${campaign.status}`}>{titleCase(campaign.status)}</span></div><p>#{campaign.id} · {campaign.whatsapp_template?.name} · {campaign.whatsapp_template?.language}</p></div>
              <button type="button" onClick={() => openReport(campaign)}>View performance</button>
            </div>
            <div className="wa-campaign-metrics">
              <div><strong>{audienceCount.toLocaleString()}</strong><span>Audience</span></div>
              <div><strong>{(sends.meta_accepted || 0).toLocaleString()}</strong><span>Accepted</span></div>
              <div><strong>{(sends.meta_delivered || 0).toLocaleString()}</strong><span>Delivered</span></div>
              <div><strong>{(sends.meta_read || 0).toLocaleString()}</strong><span>Read</span></div>
              <div><strong>{(sends.clicked || 0).toLocaleString()}</strong><span>Clicked</span></div>
              <div><strong>{(sends.meta_failed || sends.failed_attempts || 0).toLocaleString()}</strong><span>Failed</span></div>
            </div>
            <div className="wa-campaign-details"><span>Conversion: {titleCase(campaign.conversion_event)}</span><span>Frequency cap: {campaign.frequency_cap_days ? `${campaign.frequency_cap_days} days` : 'off'}</span><span>{campaign.scheduled_at ? `Scheduled ${fmtDate(campaign.scheduled_at)}` : `Created ${fmtDate(campaign.created_at)}`}</span></div>
            <div className="wa-campaign-actions">
              {['draft', 'scheduled'].includes(campaign.status) && <button type="button" onClick={() => action(campaign, 'send')} disabled={busyId === campaign.id}>Send now</button>}
              {campaign.status === 'scheduled' && <button type="button" onClick={() => action(campaign, 'pause')} disabled={busyId === campaign.id}>Pause</button>}
              {campaign.status === 'paused' && <button type="button" onClick={() => action(campaign, 'resume')} disabled={busyId === campaign.id}>Resume</button>}
              {campaign.status === 'sent' && (sends.meta_failed || sends.failed_attempts) > 0 && <button type="button" onClick={() => action(campaign, 'retry')} disabled={busyId === campaign.id}>Retry failed</button>}
              <button type="button" onClick={() => action(campaign, 'duplicate')} disabled={busyId === campaign.id}>Duplicate</button>
              {['draft', 'scheduled', 'paused', 'cancelled'].includes(campaign.status) && <button type="button" className="is-danger" onClick={() => action(campaign, 'delete')} disabled={busyId === campaign.id}>Delete</button>}
            </div>
          </article>;
        })}
      </section>

      {report && <div className="wa-report-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setReport(null); }}>
        <section className="wa-report-modal" role="dialog" aria-modal="true" aria-labelledby="wa-report-title">
          <header><div><span>Campaign #{report.campaign?.id}</span><h2 id="wa-report-title">{report.campaign?.name}</h2><p>{titleCase(report.campaign?.conversion_event)} conversion tracking</p></div><button type="button" onClick={() => setReport(null)}>Close</button></header>
          {report.stats && <div className="wa-report-summary">
            {[[report.stats.sends?.meta_accepted, 'Accepted'], [report.stats.sends?.meta_sent, 'Sent'], [report.stats.sends?.meta_delivered, 'Delivered'], [report.stats.sends?.meta_read, 'Read'], [report.stats.sends?.clicked, 'Clicked'], [report.stats.selected_conversions, 'Converted'], [report.stats.sends?.meta_failed, 'Failed']].map(([value, label]) => <div key={label}><strong>{value || 0}</strong><span>{label}</span></div>)}
          </div>}
          <div className="wa-report-filters">{['all', 'delivered', 'read', 'converted', 'failed'].map((filter) => <button type="button" className={reportFilter === filter ? 'is-active' : ''} key={filter} onClick={() => setReportFilter(filter)}>{titleCase(filter)}</button>)}</div>
          <div className="wa-report-body">
            {reportLoading && <div className="wa-campaign-empty">Loading recipient activity…</div>}
            {report.error && <div className="wa-campaign-alert is-error">{report.error}</div>}
            {!reportLoading && !report.error && <table><thead><tr><th>User</th><th>Delivery</th><th>Activity</th><th>Conversion</th><th>Detail</th></tr></thead><tbody>
              {filteredRecipients.map((row) => <tr key={row.userid}><td><strong>{row.name || `User ${row.userid}`}</strong><small>#{row.userid}{row.phone ? ` · ${row.phone}` : ''}</small></td><td><span className={`wa-report-status status-${row.meta_status || row.send_status || row.state}`}>{titleCase(row.meta_status || row.send_status || row.state)}</span></td><td><small>Delivered {fmtDate(row.delivered_at)}</small><small>Read {fmtDate(row.read_at)}</small><small>Clicked {fmtDate(row.clicked_at)}</small></td><td>{row.converted ? <><strong>Yes</strong><small>{fmtDate(row.conversion_at)}</small></> : 'No'}</td><td>{row.meta_error || row.last_error || '—'}</td></tr>)}
            </tbody></table>}
          </div>
        </section>
      </div>}
    </div>
  );
}
