import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import AdminAudienceBuilder from './AdminAudienceBuilder';
import './AdminCreditCampaigns.css';

function parseIds(value) {
  const invalid = [];
  const ids = [];
  String(value || '').split(/[\s,]+/).filter(Boolean).forEach((token) => {
    if (/^\d+$/.test(token) && Number(token) > 0) ids.push(Number(token));
    else invalid.push(token);
  });
  return { ids: [...new Set(ids)], invalid };
}

async function request(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json', ...(options.headers || {}) } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

export default function AdminCreditGrantCampaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [configured, setConfigured] = useState(false);
  const [form, setForm] = useState({ name: '', credits: '10', recipients: '' });
  const [busy, setBusy] = useState(false);
  const [sending, setSending] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [audienceBuilderOpen, setAudienceBuilderOpen] = useState(false);
  const parsed = useMemo(() => parseIds(form.recipients), [form.recipients]);

  const load = useCallback(async () => {
    try {
      const data = await request('/api/admin/campaigns/credit-grants');
      setCampaigns(data.campaigns || []);
      setConfigured(Boolean(data.whatsapp_configured));
    } catch (err) { setError(err.message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const create = async (event) => {
    event.preventDefault(); setError(''); setNotice('');
    const credits = Number(form.credits);
    if (!form.name.trim() || !Number.isInteger(credits) || credits < 1 || !parsed.ids.length || parsed.invalid.length) {
      setError('Enter a campaign name, whole positive credit amount, and valid user IDs only.'); return;
    }
    if (!window.confirm(`Add ${credits} permanent credits to ${parsed.ids.length} user${parsed.ids.length === 1 ? '' : 's'}? This changes their live balance immediately.`)) return;
    setBusy(true);
    try {
      const data = await request('/api/admin/campaigns/credit-grants', { method: 'POST', body: JSON.stringify({ name: form.name.trim(), credits, recipient_ids: parsed.ids }) });
      setNotice(`Granted credits to ${data.campaign.credited_count} account(s).${data.campaign.failed_count ? ` ${data.campaign.failed_count} failed.` : ''}`);
      setForm({ name: '', credits: '10', recipients: '' });
      await load();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };
  const send = async (campaign) => {
    setSending(campaign.id); setError(''); setNotice('');
    try {
      const data = await request(`/api/admin/campaigns/credit-grants/${campaign.id}/send-whatsapp`, { method: 'POST', body: '{}' });
      setNotice(data.queued ? `${data.queued} WhatsApp notice(s) queued on the isolated worker.` : data.detail);
      await load();
    } catch (err) { setError(err.message); } finally { setSending(null); }
  };

  const addAudienceToGrant = useCallback(({ userIds }) => {
    if (parsed.invalid.length) {
      return {
        ok: false,
        error: 'Fix the invalid IDs in the recipient box before adding a built audience.',
      };
    }
    const existing = new Set(parsed.ids);
    const selectedIds = [...new Set((userIds || []).map(Number)
      .filter((id) => Number.isInteger(id) && id > 0))];
    const additions = selectedIds.filter((id) => !existing.has(id));
    const merged = [...parsed.ids, ...additions];
    if (merged.length > 1000) {
      return {
        ok: false,
        error: `This grant would contain ${merged.length.toLocaleString()} recipients. Select no more than ${(1000 - parsed.ids.length).toLocaleString()} additional users.`,
      };
    }
    if (!additions.length) {
      return { ok: false, error: 'Every selected user is already in this grant audience.' };
    }
    setForm((current) => ({ ...current, recipients: merged.join(', ') }));
    setNotice(`Added ${additions.length.toLocaleString()} audience user${additions.length === 1 ? '' : 's'} to this grant.`);
    setAudienceBuilderOpen(false);
    return { ok: true };
  }, [parsed]);

  useEffect(() => {
    if (!audienceBuilderOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setAudienceBuilderOpen(false);
    };
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [audienceBuilderOpen]);

  return <section className="credit-campaign-admin">
    <div className="credit-campaign-hero">
      <div><div className="credit-campaign-eyebrow">Permanent balance grants</div><h2>Grant credits to selected users</h2><p>Credits are added to the real account balance immediately and never expire. Each recipient has an auditable ledger entry.</p></div>
    </div>
    {error && <div className="credit-campaign-alert credit-campaign-alert--error">{error}</div>}
    {notice && <div className="credit-campaign-alert credit-campaign-alert--success">{notice}</div>}
    {!configured && <div className="credit-campaign-alert credit-campaign-alert--error">WhatsApp is not configured yet. Grants still work; set the approved Meta template name in <code>CREDIT_GRANT_WHATSAPP_TEMPLATE_NAME</code> before queueing notices. The template must include a dynamic “Chat Now” URL button so each grant is measurable.</div>}
    <form className="credit-campaign-builder" onSubmit={create}>
      <div className="credit-campaign-builder__heading"><span>New grant</span><strong>Add permanent credits</strong></div>
      <label><span>Internal campaign name</span><input value={form.name} maxLength="120" placeholder="Diwali goodwill credits" onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
      <label><span>Credits per user</span><input type="number" min="1" max="10000" step="1" value={form.credits} onChange={(e) => setForm({ ...form, credits: e.target.value })} required /></label>
      <div className="credit-campaign-recipients"><div className="credit-campaign-recipients__header"><label htmlFor="credit-grant-recipient-ids">User IDs</label><button type="button" onClick={() => setAudienceBuilderOpen(true)}>Build an audience</button><strong>{parsed.ids.length} valid recipient{parsed.ids.length === 1 ? '' : 's'}</strong></div><textarea id="credit-grant-recipient-ids" rows="5" value={form.recipients} placeholder="One user ID per line, or comma-separated" onChange={(e) => setForm({ ...form, recipients: e.target.value })} required />{parsed.invalid.length > 0 && <small>Invalid values: {parsed.invalid.slice(0, 8).join(', ')}</small>}<small>Maximum 1,000 recipients per grant. Duplicate IDs are removed.</small></div>
      <div className="credit-campaign-rule-note"><strong>No expiry, no hidden conditions</strong><span>This is a real balance grant, not a multiplier or coupon. A confirmation is required before the live balance is updated.</span></div>
      <button className="create-btn" type="submit" disabled={busy}>{busy ? 'Granting credits…' : 'Grant permanent credits'}</button>
    </form>
    {audienceBuilderOpen && <div className="credit-campaign-audience-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) setAudienceBuilderOpen(false);
    }}>
      <section className="credit-campaign-audience-modal" role="dialog" aria-modal="true" aria-labelledby="credit-grant-audience-title">
        <header className="credit-campaign-audience-header">
          <div><span>Grant audience</span><h3 id="credit-grant-audience-title">Find and add recipients</h3><p>{parsed.ids.length.toLocaleString()} users are currently in this grant. New selections are appended and duplicates removed.</p></div>
          <button type="button" onClick={() => setAudienceBuilderOpen(false)} aria-label="Close audience builder">Close</button>
        </header>
        <div className="credit-campaign-audience-body">
          <AdminAudienceBuilder audienceOnly onAudienceSelected={addAudienceToGrant} selectionActionLabel="Add selected to credit grant" />
        </div>
      </section>
    </div>}
    <div className="credit-campaign-list"><div className="credit-campaign-list__heading"><h3>Recent grants</h3></div>{campaigns.length === 0 ? <div className="credit-campaign-empty">No permanent credit grants yet.</div> : campaigns.map((campaign) => { const metrics = campaign.metrics || {}; return <article className="credit-campaign-card" key={campaign.id}><div className="credit-campaign-card__top"><div><div className="credit-campaign-card__title-row"><h4>{campaign.name}</h4><span className="credit-campaign-status credit-campaign-status--completed">{campaign.status}</span></div><p>{campaign.credits} credits per user · {campaign.credited_count}/{campaign.recipient_count} credited</p></div><div className="credit-campaign-multiplier"><strong>+{campaign.credits}</strong><small>credits</small></div></div><div className="credit-campaign-metrics"><div><strong>{metrics.queued || 0}</strong><span>Queued</span></div><div><strong>{metrics.accepted || 0}</strong><span>Accepted</span></div><div><strong>{metrics.delivered || 0}</strong><span>Delivered</span></div><div><strong>{metrics.read || 0}</strong><span>Read</span></div><div><strong>{metrics.chat_opened || 0}</strong><span>Chat opened</span></div><div><strong>{metrics.failed || 0}</strong><span>Failed</span></div></div><div className="credit-campaign-actions"><button type="button" className="credit-campaign-report-button" disabled={!configured || sending === campaign.id} onClick={() => send(campaign)}>{sending === campaign.id ? 'Queueing…' : 'Send WhatsApp notice'}</button></div></article>})}</div>
  </section>;
}
