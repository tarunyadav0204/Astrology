import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminCreditCampaigns.css';

const PACKS = [50, 100, 250, 999];

function localDateTime(date) {
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60000).toISOString().slice(0, 16);
}

function parseIds(value) {
  const invalid = [];
  const ids = [];
  String(value || '').split(/[\s,]+/).filter(Boolean).forEach((token) => {
    if (!/^\d+$/.test(token) || Number(token) <= 0) invalid.push(token);
    else ids.push(Number(token));
  });
  return { ids: [...new Set(ids)], invalid };
}

function formatMultiplier(value) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 3 });
}

function formatMoment(value) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'Asia/Kolkata',
  }).format(new Date(value));
}

async function errorText(response, fallback) {
  const data = await response.json().catch(() => ({}));
  return typeof data.detail === 'string' ? data.detail : fallback;
}

function campaignTemplateCompatibility(template) {
  const variables = template.variables || [];
  const tokens = new Set(variables.map((variable) => String(variable.token || '').toLowerCase()));
  const bodyTokens = new Set(variables
    .filter((variable) => variable.component === 'BODY')
    .map((variable) => String(variable.token || '').toLowerCase()));
  const missing = [];
  if (!template.supported) missing.push(template.unsupported_reason || 'unsupported component');
  if (!['multiplier', 'credit_multiplier', 'offer_multiplier'].some((token) => tokens.has(token)) && !bodyTokens.has('2')) {
    missing.push('body {{2}} (multiplier)');
  }
  if (!['expires_at', 'expiry', 'offer_end', 'end_time', 'valid_until'].some((token) => tokens.has(token)) && !bodyTokens.has('3')) {
    missing.push('body {{3}} (expiry)');
  }
  if (!variables.some((variable) => variable.component === 'BUTTON' && variable.sub_type === 'url')) {
    missing.push('dynamic URL button');
  }
  return { compatible: missing.length === 0, missing };
}

export default function AdminCreditCampaigns() {
  const now = useMemo(() => new Date(), []);
  const [campaigns, setCampaigns] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [templateError, setTemplateError] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [sendBusy, setSendBusy] = useState(null);
  const [sendResult, setSendResult] = useState(null);
  const [templateSelections, setTemplateSelections] = useState({});
  const [includeUnlinked, setIncludeUnlinked] = useState({});
  const [form, setForm] = useState({
    name: '',
    multiplier: '2',
    startsAt: localDateTime(now),
    endsAt: localDateTime(new Date(now.getTime() + 24 * 60 * 60 * 1000)),
    recipientText: '',
    productIds: PACKS.map((credits) => `credits_${credits}`),
    status: 'active',
  });

  const parsedRecipients = useMemo(() => parseIds(form.recipientText), [form.recipientText]);
  const campaignTemplates = useMemo(
    () => templates.filter((template) => campaignTemplateCompatibility(template).compatible),
    [templates],
  );

  const loadCampaigns = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/admin/campaigns/credits', { headers: getAdminAuthHeaders() });
      if (!response.ok) throw new Error(await errorText(response, 'Could not load campaigns'));
      const data = await response.json();
      setCampaigns(data.campaigns || []);
    } catch (err) {
      setError(err.message || 'Could not load campaigns');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadTemplates = useCallback(async () => {
    setTemplatesLoading(true);
    setTemplateError('');
    try {
      const response = await fetch('/api/admin/whatsapp/templates', { headers: getAdminAuthHeaders() });
      if (!response.ok) throw new Error(await errorText(response, 'Could not fetch templates from Meta'));
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (err) {
      setTemplates([]);
      setTemplateError(err.message || 'Could not fetch templates from Meta');
    } finally {
      setTemplatesLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCampaigns();
    loadTemplates();
  }, [loadCampaigns, loadTemplates]);

  useEffect(() => {
    const jobId = sendResult?.job_id;
    const campaignId = sendResult?.campaignId;
    if (!jobId || !campaignId || ['completed', 'completed_with_errors', 'failed'].includes(sendResult.status)) return undefined;
    const timer = window.setTimeout(async () => {
      try {
        const response = await fetch(
          `/api/admin/campaigns/credits/${campaignId}/whatsapp-jobs/${jobId}`,
          { headers: getAdminAuthHeaders() },
        );
        if (!response.ok) throw new Error(await errorText(response, 'Could not refresh WhatsApp job'));
        const data = await response.json();
        setSendResult((current) => (
          current?.job_id === jobId ? { ...current, ...(data.job || {}) } : current
        ));
        if (['completed', 'completed_with_errors', 'failed'].includes(data.job?.status)) loadCampaigns();
      } catch (err) {
        setError(err.message || 'Could not refresh WhatsApp job');
      }
    }, 2000);
    return () => window.clearTimeout(timer);
  }, [sendResult, loadCampaigns]);

  const updateForm = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  const togglePack = (productId) => {
    setForm((current) => ({
      ...current,
      productIds: current.productIds.includes(productId)
        ? current.productIds.filter((value) => value !== productId)
        : [...current.productIds, productId],
    }));
  };

  const createCampaign = async (event) => {
    event.preventDefault();
    setError('');
    setNotice('');
    if (parsedRecipients.invalid.length) {
      setError(`Invalid user IDs: ${parsedRecipients.invalid.slice(0, 8).join(', ')}`);
      return;
    }
    if (!parsedRecipients.ids.length) {
      setError('Enter at least one recipient user ID.');
      return;
    }
    const multiplier = Number(form.multiplier);
    if (!Number.isFinite(multiplier) || multiplier <= 1 || multiplier > 5) {
      setError('Multiplier must be greater than 1 and no more than 5.');
      return;
    }
    setSaving(true);
    try {
      const response = await fetch('/api/admin/campaigns/credits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAdminAuthHeaders() },
        body: JSON.stringify({
          name: form.name.trim(),
          multiplier,
          starts_at: new Date(form.startsAt).toISOString(),
          ends_at: new Date(form.endsAt).toISOString(),
          recipient_ids: parsedRecipients.ids,
          product_ids: form.productIds,
          status: form.status,
        }),
      });
      if (!response.ok) throw new Error(await errorText(response, 'Could not create campaign'));
      setNotice('Credit campaign created. Eligible users will see the offer in Credits during its active period.');
      setForm((current) => ({ ...current, name: '', recipientText: '' }));
      await loadCampaigns();
    } catch (err) {
      setError(err.message || 'Could not create campaign');
    } finally {
      setSaving(false);
    }
  };

  const changeStatus = async (campaign, status) => {
    setError('');
    try {
      const response = await fetch(`/api/admin/campaigns/credits/${campaign.id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', ...getAdminAuthHeaders() },
        body: JSON.stringify({ status }),
      });
      if (!response.ok) throw new Error(await errorText(response, 'Could not update campaign'));
      await loadCampaigns();
    } catch (err) {
      setError(err.message || 'Could not update campaign');
    }
  };

  const selectedTemplateKey = (campaign) => templateSelections[campaign.id]
    || (campaign.whatsapp_template_name && campaign.whatsapp_template_language
      ? `${campaign.whatsapp_template_name}::${campaign.whatsapp_template_language}`
      : '');

  const sendWhatsApp = async (campaign) => {
    const selected = selectedTemplateKey(campaign);
    const [templateName, language] = selected.split('::');
    if (!templateName || !language) {
      setError('Select an approved Meta template for this campaign.');
      return;
    }
    if (!window.confirm(`Send this WhatsApp campaign to up to ${campaign.summary?.recipients || 0} selected users?`)) return;
    setSendBusy(campaign.id);
    setSendResult(null);
    setError('');
    try {
      const response = await fetch(`/api/admin/campaigns/credits/${campaign.id}/send-whatsapp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAdminAuthHeaders() },
        body: JSON.stringify({
          template_name: templateName,
          language,
          include_unlinked: Boolean(includeUnlinked[campaign.id]),
        }),
      });
      if (!response.ok) throw new Error(await errorText(response, 'WhatsApp send failed'));
      const data = await response.json();
      setSendResult({ campaignId: campaign.id, ...(data.job || {}), message: data.message });
      await loadCampaigns();
    } catch (err) {
      setError(err.message || 'WhatsApp send failed');
    } finally {
      setSendBusy(null);
    }
  };

  return (
    <div className="credit-campaign-admin">
      <header className="credit-campaign-hero">
        <div>
          <span className="credit-campaign-eyebrow">Campaigns / Credit campaigns</span>
          <h2>Targeted credit multipliers</h2>
          <p>Guarantee selected users a multiplier such as 1.5× or 2× during a controlled purchase window.</p>
        </div>
        <button type="button" className="create-btn" onClick={loadCampaigns} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </header>

      {error && <div className="credit-campaign-alert credit-campaign-alert--error">{error}</div>}
      {notice && <div className="credit-campaign-alert credit-campaign-alert--success">{notice}</div>}

      <form className="credit-campaign-builder" onSubmit={createCampaign}>
        <div className="credit-campaign-builder__heading">
          <span>New campaign</span>
          <strong>Configure the promise</strong>
        </div>
        <label>
          <span>Campaign name</span>
          <input value={form.name} onChange={(e) => updateForm('name', e.target.value)} placeholder="September 1.5× retention offer" required minLength={3} />
        </label>
        <label>
          <span>Total multiplier</span>
          <div className="credit-campaign-multiplier-input">
            <input type="number" min="1.01" max="5" step="0.01" value={form.multiplier} onChange={(e) => updateForm('multiplier', e.target.value)} />
            <b>×</b>
          </div>
          <small>1.5× means 100 purchased credits are topped up to at least 150 total.</small>
        </label>
        <div className="credit-campaign-date-grid">
          <label><span>Starts</span><input type="datetime-local" value={form.startsAt} onChange={(e) => updateForm('startsAt', e.target.value)} required /></label>
          <label><span>Ends</span><input type="datetime-local" value={form.endsAt} onChange={(e) => updateForm('endsAt', e.target.value)} required /></label>
        </div>
        <fieldset>
          <legend>Eligible packs</legend>
          <small>Leave every pack unchecked to apply to all normal web packs.</small>
          <div className="credit-campaign-pack-grid">
            {PACKS.map((credits) => {
              const productId = `credits_${credits}`;
              return (
                <label key={productId} className="credit-campaign-check">
                  <input type="checkbox" checked={form.productIds.includes(productId)} onChange={() => togglePack(productId)} />
                  <span>{credits} credits</span>
                </label>
              );
            })}
          </div>
        </fieldset>
        <label className="credit-campaign-recipients">
          <span>Eligible AstroRoshni user IDs</span>
          <textarea value={form.recipientText} onChange={(e) => updateForm('recipientText', e.target.value)} placeholder="18, 42, 105" rows={5} />
          <small>{parsedRecipients.ids.length} unique valid ID{parsedRecipients.ids.length === 1 ? '' : 's'} · maximum 1,000</small>
        </label>
        <label>
          <span>Initial status</span>
          <select value={form.status} onChange={(e) => updateForm('status', e.target.value)}>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
          </select>
        </label>
        <div className="credit-campaign-rule-note">
          <strong>How bonuses combine</strong>
          <span>Normal pack and web bonuses count toward the promise. The campaign adds only the remaining credits needed to reach the multiplier.</span>
        </div>
        <button type="submit" className="create-btn" disabled={saving}>{saving ? 'Creating…' : 'Create campaign'}</button>
      </form>

      <section className="credit-campaign-list">
        <div className="credit-campaign-list__heading">
          <h3>Credit campaigns</h3>
          <span>{campaigns.length} total</span>
        </div>
        {!loading && !campaigns.length && <div className="credit-campaign-empty">No credit campaigns yet.</div>}
        {campaigns.map((campaign) => {
          const summary = campaign.summary || {};
          const activeSendJob = sendResult?.campaignId === campaign.id
            ? sendResult
            : campaign.whatsapp_job;
          const sendInProgress = ['queued', 'running'].includes(activeSendJob?.status);
          const isExpired = new Date(campaign.ends_at) <= new Date();
          return (
            <article className="credit-campaign-card" key={campaign.id}>
              <div className="credit-campaign-card__top">
                <div>
                  <div className="credit-campaign-card__title-row">
                    <h4>{campaign.name}</h4>
                    <span className={`credit-campaign-status credit-campaign-status--${campaign.status}`}>{isExpired ? 'ended' : campaign.status}</span>
                  </div>
                  <p>{formatMoment(campaign.starts_at)} → {formatMoment(campaign.ends_at)}</p>
                </div>
                <div className="credit-campaign-multiplier">{formatMultiplier(campaign.multiplier)}<small>× total</small></div>
              </div>
              <div className="credit-campaign-metrics">
                <div><strong>{summary.recipients || 0}</strong><span>Recipients</span></div>
                <div><strong>{activeSendJob?.accepted ?? summary.notified ?? 0}</strong><span>Notified</span></div>
                <div><strong>{summary.opened || 0}</strong><span>Opened</span></div>
                <div><strong>{summary.buyers || 0}</strong><span>Buyers</span></div>
                <div><strong>{summary.campaign_bonus_credits || 0}</strong><span>Bonus credits</span></div>
              </div>
              <div className="credit-campaign-packs">
                {(campaign.product_ids || []).length ? campaign.product_ids.map((id) => <span key={id}>{id.replace('credits_', '')}</span>) : <span>All packs</span>}
              </div>
              <div className="credit-campaign-actions">
                {campaign.status !== 'active' && !isExpired && <button type="button" onClick={() => changeStatus(campaign, 'active')}>Activate</button>}
                {campaign.status === 'active' && <button type="button" onClick={() => changeStatus(campaign, 'paused')}>Pause</button>}
                {!isExpired && campaign.status !== 'completed' && <button type="button" onClick={() => changeStatus(campaign, 'completed')}>Complete</button>}
              </div>
              <div className="credit-campaign-whatsapp">
                <div>
                  <strong>Notify recipients on WhatsApp</strong>
                  <span>
                    Positional body mapping: <code>{'{{1}}'}</code> customer name, <code>{'{{2}}'}</code> multiplier,
                    {' '}<code>{'{{3}}'}</code> expiry. The dynamic URL button uses its own <code>{'{{1}}'}</code> secure token.
                  </span>
                </div>
                <button type="button" onClick={loadTemplates} disabled={templatesLoading}>
                  {templatesLoading ? 'Refreshing templates…' : 'Refresh templates from Meta'}
                </button>
                <select
                  value={selectedTemplateKey(campaign)}
                  onChange={(e) => setTemplateSelections((current) => ({ ...current, [campaign.id]: e.target.value }))}
                  disabled={templatesLoading || !templates.length}
                >
                  <option value="">Choose approved template…</option>
                  {templates.map((template) => {
                    const compatibility = campaignTemplateCompatibility(template);
                    return (
                      <option
                        key={`${template.name}::${template.language}`}
                        value={`${template.name}::${template.language}`}
                        disabled={!compatibility.compatible}
                      >
                        {template.name} · {template.language} · {template.category}
                        {!compatibility.compatible ? ` — missing ${compatibility.missing.join(', ')}` : ''}
                      </option>
                    );
                  })}
                </select>
                {templateError && <span className="credit-campaign-template-error">{templateError}</span>}
                {!campaignTemplates.length && (
                  <span>
                    {templates.length
                      ? `${templates.length} approved template${templates.length === 1 ? ' is' : 's are'} available, but none match this campaign. Open the list above to see what each one is missing.`
                      : (!templatesLoading && !templateError ? 'No approved Meta templates were returned.' : '')}
                  </span>
                )}
                <label className="credit-campaign-check credit-campaign-check--warning">
                  <input
                    type="checkbox"
                    checked={Boolean(includeUnlinked[campaign.id])}
                    onChange={(e) => setIncludeUnlinked((current) => ({ ...current, [campaign.id]: e.target.checked }))}
                  />
                  <span>Also send to phone-only users without linked WhatsApp consent</span>
                </label>
                <button
                  type="button"
                  className="create-btn"
                  disabled={campaign.status !== 'active' || isExpired || sendBusy === campaign.id || sendInProgress}
                  onClick={() => sendWhatsApp(campaign)}
                >
                  {sendBusy === campaign.id
                    ? 'Queueing…'
                    : (sendInProgress ? 'WhatsApp campaign processing…' : 'Send WhatsApp campaign')}
                </button>
                {activeSendJob && (
                  <div className="credit-campaign-send-result">
                    <strong>
                      {activeSendJob.status} · Accepted {activeSendJob.accepted || 0} · Failed {activeSendJob.failed || 0} · Skipped {activeSendJob.skipped || 0}
                    </strong>
                    <span>{activeSendJob.accepted + activeSendJob.failed + activeSendJob.skipped || 0}/{activeSendJob.total || 0} recipients processed on the isolated worker.</span>
                    {activeSendJob.error && <span>{activeSendJob.error}</span>}
                    {!!(activeSendJob.issues || []).length && (
                      <span>
                        {activeSendJob.issues.map((issue) => (
                          `User ${issue.user_id}: ${issue.reason || issue.error || issue.status}`
                        )).join(' · ')}
                        {activeSendJob.issues_truncated ? ' · Additional excluded IDs are not shown.' : ''}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </section>
    </div>
  );
}
