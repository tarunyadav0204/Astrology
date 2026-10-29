import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
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

  return <section className="credit-campaign-admin">
    <div className="credit-campaign-hero">
      <div><div className="credit-campaign-eyebrow">Permanent balance grants</div><h2>Grant credits to selected users</h2><p>Credits are added to the real account balance immediately and never expire. Each recipient has an auditable ledger entry.</p></div>
    </div>
    {error && <div className="credit-campaign-alert credit-campaign-alert--error">{error}</div>}
    {notice && <div className="credit-campaign-alert credit-campaign-alert--success">{notice}</div>}
    {!configured && <div className="credit-campaign-alert credit-campaign-alert--error">WhatsApp is not configured yet. Grants still work; set the approved Meta template name in <code>CREDIT_GRANT_WHATSAPP_TEMPLATE_NAME</code> before queueing notices. The template must include a “Chat Now” URL button to the chat screen.</div>}
    <form className="credit-campaign-builder" onSubmit={create}>
      <div className="credit-campaign-builder__heading"><span>New grant</span><strong>Add permanent credits</strong></div>
      <label><span>Internal campaign name</span><input value={form.name} maxLength="120" placeholder="Diwali goodwill credits" onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
      <label><span>Credits per user</span><input type="number" min="1" max="10000" step="1" value={form.credits} onChange={(e) => setForm({ ...form, credits: e.target.value })} required /></label>
      <div className="credit-campaign-recipients"><div className="credit-campaign-recipients__header"><label>User IDs</label><strong>{parsed.ids.length} valid recipient{parsed.ids.length === 1 ? '' : 's'}</strong></div><textarea rows="5" value={form.recipients} placeholder="One user ID per line, or comma-separated" onChange={(e) => setForm({ ...form, recipients: e.target.value })} required />{parsed.invalid.length > 0 && <small>Invalid values: {parsed.invalid.slice(0, 8).join(', ')}</small>}<small>Maximum 1,000 recipients per grant. Duplicate IDs are removed.</small></div>
      <div className="credit-campaign-rule-note"><strong>No expiry, no hidden conditions</strong><span>This is a real balance grant, not a multiplier or coupon. A confirmation is required before the live balance is updated.</span></div>
      <button className="create-btn" type="submit" disabled={busy}>{busy ? 'Granting credits…' : 'Grant permanent credits'}</button>
    </form>
    <div className="credit-campaign-list"><div className="credit-campaign-list__heading"><h3>Recent grants</h3></div>{campaigns.length === 0 ? <div className="credit-campaign-empty">No permanent credit grants yet.</div> : campaigns.map((campaign) => <article className="credit-campaign-card" key={campaign.id}><div className="credit-campaign-card__top"><div><div className="credit-campaign-card__title-row"><h4>{campaign.name}</h4><span className="credit-campaign-status credit-campaign-status--completed">{campaign.status}</span></div><p>{campaign.credits} credits per user · {campaign.credited_count}/{campaign.recipient_count} credited</p></div><div className="credit-campaign-multiplier"><strong>+{campaign.credits}</strong><small>credits</small></div></div><div className="credit-campaign-actions"><button type="button" className="credit-campaign-report-button" disabled={!configured || sending === campaign.id} onClick={() => send(campaign)}>{sending === campaign.id ? 'Queueing…' : 'Send WhatsApp notice'}</button></div></article>)}</div>
  </section>;
}
