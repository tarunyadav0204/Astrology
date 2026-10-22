import React, { useCallback, useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import AdminAudienceBuilder from './AdminAudienceBuilder';
import './AdminSmsCampaigns.css';

const approvedTemplate = {
  key: 'partner_portrait',
  id: '1077020640025488277',
  copy: 'Hi {name}, curious about the relationship patterns and partner qualities reflected in your birth chart? Explore your personalised Partner Portrait on AstroRoshni: https://astroroshni.com/go/partner-portrait',
};

const errorFrom = async (response, fallback) => {
  const body = await response.json().catch(() => ({}));
  return body.detail || body.message || fallback;
};

const emptyForm = { name: 'Partner Portrait — SMS', userIds: '', scheduledAt: '', frequencyCapDays: 30 };

export default function AdminSmsCampaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [config, setConfig] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [audienceBuilderOpen, setAudienceBuilderOpen] = useState(false);
  const [report, setReport] = useState(null);

  const load = useCallback(async ({ includeStats = true } = {}) => {
    setError('');
    try {
      const [campaignResponse, configResponse] = await Promise.all([
        fetch(`/api/nudge/admin/campaigns?limit=500&channel=sms&include_stats=${includeStats}`, { headers: getAdminAuthHeaders() }),
        fetch('/api/nudge/admin/sms-campaigns/config', { headers: getAdminAuthHeaders() }),
      ]);
      if (!campaignResponse.ok) throw new Error(await errorFrom(campaignResponse, 'Could not load SMS campaigns'));
      if (!configResponse.ok) throw new Error(await errorFrom(configResponse, 'Could not load SMS configuration'));
      const [campaignData, configData] = await Promise.all([campaignResponse.json(), configResponse.json()]);
      setCampaigns((current) => (campaignData.items || [])
        .filter((campaign) => campaign.sms_template?.key === approvedTemplate.key)
        // Lightweight refreshes intentionally skip expensive delivery
        // aggregates. Preserve the last known counts until a full refresh.
        .map((campaign) => ({
          ...campaign,
          stats: campaign.stats ?? current.find((item) => item.id === campaign.id)?.stats,
        })));
      setConfig(configData);
    } catch (err) {
      setError(err.message || 'Could not load SMS campaigns');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!campaigns.some((campaign) => campaign.status === 'sending')) return undefined;
    const timer = window.setInterval(() => load({ includeStats: false }), 5000);
    return () => window.clearInterval(timer);
  }, [campaigns, load]);

  const audience = () => {
    const ids = form.userIds.split(',').map((value) => value.trim()).filter((value) => /^\d+$/.test(value)).map(Number);
    return ids.length ? { type: 'user_ids', user_ids: ids, criteria: { require_self_chart: true } } : { type: 'all', criteria: { require_self_chart: true } };
  };

  const addAudienceToDraft = ({ userIds }) => {
    const existing = new Set(
      form.userIds.split(',').map((value) => value.trim()).filter((value) => /^\d+$/.test(value)).map(Number),
    );
    const additions = [...new Set((userIds || []).map(Number).filter((id) => Number.isInteger(id) && id > 0))]
      .filter((id) => !existing.has(id));
    if (!additions.length) return { ok: false, error: 'Every selected user is already in this SMS audience.' };
    const merged = [...existing, ...additions];
    if (merged.length > 5000) return { ok: false, error: 'An SMS campaign can include up to 5,000 selected users.' };
    setForm((current) => ({ ...current, userIds: merged.join(', ') }));
    setAudienceBuilderOpen(false);
    setEstimate(null);
    setNotice(`Added ${additions.length.toLocaleString()} selected user${additions.length === 1 ? '' : 's'} to the SMS audience.`);
    return { ok: true };
  };

  const payload = () => ({
    name: form.name.trim(),
    title_template: 'Partner Portrait',
    body_template: approvedTemplate.copy,
    question_template: '',
    channel_policy: 'blast',
    channels: ['sms'],
    audience_filter: audience(),
    landing_screen: 'chat',
    sms_template: { key: approvedTemplate.key },
    conversion_event: 'click',
    frequency_cap_days: Number(form.frequencyCapDays) || 30,
    scheduled_at: form.scheduledAt ? new Date(form.scheduledAt).toISOString() : null,
    status: form.scheduledAt ? 'scheduled' : 'draft',
  });

  const estimateAudience = async () => {
    setError(''); setNotice(''); setEstimate(null);
    try {
      const response = await fetch('/api/nudge/admin/campaigns/audience-estimate', {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...getAdminAuthHeaders() },
        body: JSON.stringify({ audience_filter: audience() }),
      });
      if (!response.ok) throw new Error(await errorFrom(response, 'Could not estimate SMS audience'));
      setEstimate(await response.json());
    } catch (err) { setError(err.message || 'Could not estimate SMS audience'); }
  };

  const save = async () => {
    setSaving(true); setError(''); setNotice('');
    try {
      if (!form.name.trim()) throw new Error('Campaign name is required');
      const response = await fetch('/api/nudge/admin/campaigns', {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...getAdminAuthHeaders() }, body: JSON.stringify(payload()),
      });
      if (!response.ok) throw new Error(await errorFrom(response, 'Could not save SMS campaign'));
      setNotice(form.scheduledAt ? 'SMS campaign scheduled.' : 'SMS campaign saved as a draft.');
      setForm(emptyForm); setEstimate(null); await load();
    } catch (err) { setError(err.message || 'Could not save SMS campaign'); }
    finally { setSaving(false); }
  };

  const action = async (campaign, actionName) => {
    if (actionName === 'send' && !window.confirm(`Send “${campaign.name}” to its consented SMS audience now?`)) return;
    if (actionName === 'delete' && !window.confirm(`Delete “${campaign.name}”?`)) return;
    setBusyId(campaign.id); setError(''); setNotice('');
    try {
      let path = `/api/nudge/admin/campaigns/${campaign.id}`;
      let options = { method: 'POST', headers: getAdminAuthHeaders() };
      if (actionName === 'send') path += '/send-now';
      if (actionName === 'test') {
        path += '/test-send';
        options = { method: 'POST', headers: { 'Content-Type': 'application/json', ...getAdminAuthHeaders() }, body: JSON.stringify({}) };
      }
      if (actionName === 'retry') path += '/retry-failed';
      if (actionName === 'delete') options = { method: 'DELETE', headers: getAdminAuthHeaders() };
      if (actionName === 'pause' || actionName === 'resume') {
        path += '/status'; options = { method: 'POST', headers: { 'Content-Type': 'application/json', ...getAdminAuthHeaders() }, body: JSON.stringify({ status: actionName === 'pause' ? 'paused' : (campaign.scheduled_at ? 'scheduled' : 'draft') }) };
      }
      const response = await fetch(path, options);
      if (!response.ok) throw new Error(await errorFrom(response, `Could not ${actionName} campaign`));
      setNotice(actionName === 'test' ? 'Test SMS submitted to your consented admin number.' : 'Campaign updated.');
      await load();
    } catch (err) { setError(err.message || `Could not ${actionName} campaign`); }
    finally { setBusyId(null); }
  };

  const openReport = async (campaign) => {
    setReport({ campaign, loading: true, error: '', recipients: [], stats: null });
    try {
      const response = await fetch(`/api/nudge/admin/campaigns/${campaign.id}/recipients`, { headers: getAdminAuthHeaders() });
      if (!response.ok) throw new Error(await errorFrom(response, 'Could not load SMS delivery report'));
      const data = await response.json();
      setReport({ campaign: data.campaign || campaign, loading: false, error: '', recipients: data.recipients || [], stats: data.stats || null });
    } catch (err) {
      setReport({ campaign, loading: false, error: err.message || 'Could not load SMS delivery report', recipients: [], stats: null });
    }
  };

  return <div className="sms-campaign-admin">
    <header className="sms-campaign-hero"><div><span>Campaigns / SMS campaigns</span><h2>SMS campaigns</h2><p>Approved DLT templates only. SMS is sent solely to users who have expressly opted in to marketing messages.</p></div><button type="button" onClick={load}>Refresh</button></header>
    {config && <><div className={`sms-campaign-readiness ${config.configured ? 'is-ready' : 'is-blocked'}`}><strong>{config.configured ? 'SMS provider ready' : 'SMS sending is blocked'}</strong><span>{config.configured ? `Primary: ${config.primary_provider || '—'}${config.fallback_provider ? ` · fallback: ${config.fallback_provider}` : ''}.` : 'Configure MTalkz or MSG91 before sending.'}</span></div><section className="sms-provider-card"><div><span>Delivery configuration</span><h3>Provider routing</h3><p>Secrets are intentionally hidden.</p></div><dl><div><dt>Primary</dt><dd>{config.primary_provider || 'Not configured'}</dd></div><div><dt>Fallback</dt><dd>{config.fallback_provider || 'Not configured'}</dd></div><div><dt>MTalkz sender / PE ID</dt><dd>{config.providers?.mtalkz?.configured ? `${config.providers.mtalkz.sender_id} · ${config.providers.mtalkz.pe_id}` : 'Not configured'}</dd></div><div><dt>MSG91 Flow template</dt><dd>{config.providers?.msg91?.template_id || 'Not configured'}</dd></div><div><dt>Airtel DLT template</dt><dd>{approvedTemplate.id}</dd></div></dl></section></>}
    {error && <div className="sms-campaign-alert is-error">{error}</div>}
    {notice && <div className="sms-campaign-alert is-success">{notice}</div>}
    <section className="sms-campaign-composer"><div><span className="sms-eyebrow">Approved DLT template</span><h3>Partner Portrait</h3><p className="sms-template-id">DLT Template ID {approvedTemplate.id}</p><div className="sms-copy-lock">{approvedTemplate.copy}</div><small>The name is the only variable. The copy and destination are locked to the approved template.</small></div><div className="sms-fields"><label>Campaign name<input value={form.name} maxLength={200} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label><div className="sms-audience-field"><strong>Campaign audience</strong><p>{form.userIds ? `${form.userIds.split(',').filter(Boolean).length.toLocaleString()} selected users. Consent and valid-number checks still apply.` : 'No explicit selection — all eligible users with a self chart will be considered.'}</p><button type="button" onClick={() => setAudienceBuilderOpen(true)}>Build an audience</button><label>Specific user IDs <small>Optional override, comma-separated.</small><input value={form.userIds} placeholder="e.g. 120, 121" onChange={(event) => { setForm({ ...form, userIds: event.target.value }); setEstimate(null); }} /></label></div><label>Frequency cap (days)<input type="number" min="1" max="365" value={form.frequencyCapDays} onChange={(event) => setForm({ ...form, frequencyCapDays: event.target.value })} /></label><label>Schedule (optional)<input type="datetime-local" value={form.scheduledAt} onChange={(event) => setForm({ ...form, scheduledAt: event.target.value })} /></label><div className="sms-actions"><button type="button" onClick={estimateAudience}>Estimate consented audience</button><button type="button" className="is-primary" disabled={saving} onClick={save}>{saving ? 'Saving…' : form.scheduledAt ? 'Save and schedule' : 'Save draft'}</button></div>{estimate && <div className="sms-estimate"><strong>{estimate.reachable?.sms || 0}</strong><span>consented SMS recipients · {estimate.has_self_chart || 0} users with self charts in this audience</span></div>}</div></section>
    <section className="sms-campaign-list"><h3>Campaign history</h3>{loading && <div className="sms-empty">Loading SMS campaigns…</div>}{!loading && !campaigns.length && <div className="sms-empty">No SMS campaigns yet.</div>}{campaigns.map((campaign) => { const sends = campaign.stats?.sends || {}; return <article className="sms-campaign-card" key={campaign.id}><div><h4>{campaign.name}</h4><p>#{campaign.id} · {campaign.status} · {campaign.scheduled_at ? `scheduled ${new Date(campaign.scheduled_at).toLocaleString('en-IN')}` : 'draft'}</p></div><div className="sms-metrics"><span><strong>{campaign.total_targeted || 0}</strong>Audience</span><span><strong>{sends.sms || 0}</strong>Submitted</span><span><strong>{sends.failed_attempts || 0}</strong>Failed</span><span><strong>{sends.clicked || 0}</strong>Clicked</span></div><div className="sms-actions"><button type="button" onClick={() => openReport(campaign)}>View performance</button>{['draft', 'scheduled'].includes(campaign.status) && <button type="button" className="is-primary" disabled={busyId === campaign.id || !config?.configured} onClick={() => action(campaign, 'send')}>Send now</button>}{campaign.status === 'scheduled' && <button type="button" disabled={busyId === campaign.id} onClick={() => action(campaign, 'pause')}>Pause</button>}{campaign.status === 'paused' && <button type="button" disabled={busyId === campaign.id} onClick={() => action(campaign, 'resume')}>Resume</button>}<button type="button" disabled={busyId === campaign.id || !config?.configured} onClick={() => action(campaign, 'test')}>Test to me</button>{campaign.status === 'sent' && sends.failed_attempts > 0 && <button type="button" onClick={() => action(campaign, 'retry')}>Retry failed</button>}{['draft', 'scheduled', 'paused'].includes(campaign.status) && <button type="button" className="is-danger" onClick={() => action(campaign, 'delete')}>Delete</button>}</div></article>; })}</section>
    {report && <div className="sms-report-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setReport(null); }}><section className="sms-report-modal" role="dialog" aria-modal="true" aria-labelledby="sms-report-title"><header><div><span>SMS delivery report</span><h3 id="sms-report-title">{report.campaign?.name}</h3><p>Provider acceptance is not the same as handset delivery. Provider errors are retained for review.</p></div><button type="button" onClick={() => setReport(null)}>Close</button></header>{report.loading && <div className="sms-empty">Loading delivery activity…</div>}{report.error && <div className="sms-campaign-alert is-error">{report.error}</div>}{!report.loading && !report.error && <><div className="sms-report-summary"><span><strong>{report.stats?.sends?.sms || 0}</strong>Submitted</span><span><strong>{report.stats?.sends?.failed_attempts || 0}</strong>Failed attempts</span><span><strong>{report.stats?.sends?.clicked || 0}</strong>Clicks</span></div><div className="sms-report-table-wrap"><table><thead><tr><th>User</th><th>Status</th><th>Provider</th><th>Message ID</th><th>Failure detail</th></tr></thead><tbody>{report.recipients.map((recipient) => <tr key={recipient.userid}><td><strong>{recipient.name || `User #${recipient.userid}`}</strong><span>#{recipient.userid}</span></td><td>{recipient.send_status || recipient.state || 'Not sent'}</td><td>{recipient.provider || '—'}{recipient.fallback_from ? ` (fallback from ${recipient.fallback_from})` : ''}</td><td>{recipient.meta_message_id || '—'}</td><td>{recipient.provider_error || recipient.last_error || recipient.meta_error || '—'}</td></tr>)}</tbody></table>{!report.recipients.length && <div className="sms-empty">No delivery attempts yet.</div>}</div></>}</section></div>}
    {audienceBuilderOpen && <div className="sms-audience-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setAudienceBuilderOpen(false); }}><section className="sms-audience-modal" role="dialog" aria-modal="true" aria-labelledby="sms-audience-title"><header><div><span>Campaign audience</span><h3 id="sms-audience-title">Find SMS recipients</h3><p>Choose a cohort using the existing audience builder. SMS consent and number validation are enforced again when the campaign is sent.</p></div><button type="button" onClick={() => setAudienceBuilderOpen(false)}>Close</button></header><div className="sms-audience-modal__body"><AdminAudienceBuilder audienceOnly onAudienceSelected={addAudienceToDraft} selectionActionLabel="Use selected SMS audience" /></div></section></div>}
  </div>;
}
