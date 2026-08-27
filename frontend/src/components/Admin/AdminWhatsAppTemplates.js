import React, { useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import AdminAudienceBuilder from './AdminAudienceBuilder';
import './AdminWhatsAppTemplates.css';

const parseUserIds = (value) => {
  const tokens = String(value || '').split(/[\s,]+/).filter(Boolean);
  const invalid = tokens.filter((token) => !/^\d+$/.test(token) || Number(token) <= 0);
  const ids = [...new Set(tokens.filter((token) => /^\d+$/.test(token) && Number(token) > 0).map(Number))];
  return { ids, invalid };
};

const apiError = async (response, fallback) => {
  const data = await response.json().catch(() => ({}));
  const detail = data.detail || data.message || fallback;
  return typeof detail === 'string' ? detail : JSON.stringify(detail);
};

const componentText = (template, type) => {
  const component = (template?.components || []).find(
    (item) => String(item.type || '').toUpperCase() === type
  );
  return component?.text || '';
};

const humanize = (value) => String(value || '')
  .replace(/[_-]+/g, ' ')
  .replace(/\b\w/g, (letter) => letter.toUpperCase());

const previewText = (text, component, parameters) => String(text || '').replace(
  /{{\s*([^{}]+?)\s*}}/g,
  (match, token) => String(parameters[`${component.toLowerCase()}.${token}`] || '').trim() || match
);

const mappingDefaults = (template) => Object.fromEntries(
  (template?.variables || []).map((variable) => [
    variable.key,
    {
      ...(variable.suggested_mapping || { source: 'fixed', value: '' }),
      valuesText: '',
    },
  ])
);

const parsePerUserValues = (text) => {
  const values = {};
  String(text || '').split(/\r?\n/).forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    const match = trimmed.match(/^(\d+)\s*[,=\t]\s*(.+)$/);
    if (match) values[match[1]] = match[2].trim();
  });
  return values;
};

const mappingsPayload = (mappings) => Object.fromEntries(
  Object.entries(mappings || {}).map(([key, mapping]) => [
    key,
    {
      source: mapping.source,
      value: mapping.value || null,
      field: mapping.field || null,
      fallback: mapping.fallback || null,
      generator: mapping.generator || null,
      values: mapping.source === 'per_user' ? parsePerUserValues(mapping.valuesText) : {},
    },
  ])
);

const localPreviewValues = (template, mappings) => Object.fromEntries(
  (template?.variables || []).map((variable) => {
    const mapping = mappings[variable.key] || {};
    let value = mapping.value || '';
    if (mapping.source === 'user_field') value = `[${humanize(mapping.field || 'user field')}]`;
    if (mapping.source === 'per_user') value = '[Per-recipient value]';
    if (mapping.source === 'generator') value = '[Generated securely]';
    return [variable.key, value];
  })
);

export default function AdminWhatsAppTemplates({
  initialMode = 'quick',
  campaignOnly = false,
  onCampaignCreated = null,
}) {
  const [mode, setMode] = useState(campaignOnly ? 'campaign' : initialMode);
  const [templates, setTemplates] = useState([]);
  const [selectedKey, setSelectedKey] = useState('');
  const [mappings, setMappings] = useState({});
  const [userIdsText, setUserIdsText] = useState('');
  const [includeUnlinked, setIncludeUnlinked] = useState(false);
  const [validation, setValidation] = useState(null);
  const [sendResult, setSendResult] = useState(null);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [validating, setValidating] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [previewUserId, setPreviewUserId] = useState('');
  const [audienceBuilderOpen, setAudienceBuilderOpen] = useState(false);
  const [campaignName, setCampaignName] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  const [conversionEvent, setConversionEvent] = useState('click');
  const [frequencyCapDays, setFrequencyCapDays] = useState('0');

  const selectedTemplate = useMemo(
    () => templates.find((item) => `${item.name}::${item.language}` === selectedKey) || null,
    [selectedKey, templates]
  );
  const parsed = useMemo(() => parseUserIds(userIdsText), [userIdsText]);
  const recipientLimit = mode === 'campaign' ? 10000 : 100;

  const loadTemplates = async () => {
    setLoadingTemplates(true);
    setError('');
    try {
      const response = await fetch('/api/admin/whatsapp/templates', {
        headers: getAdminAuthHeaders(),
      });
      if (!response.ok) throw new Error(await apiError(response, 'Failed to fetch templates'));
      const data = await response.json();
      const rows = Array.isArray(data.templates) ? data.templates : [];
      setTemplates(rows);
      setSelectedKey((current) => {
        if (current && rows.some((item) => `${item.name}::${item.language}` === current && item.supported)) {
          return current;
        }
        const firstSupported = rows.find((item) => item.supported);
        return firstSupported ? `${firstSupported.name}::${firstSupported.language}` : '';
      });
    } catch (err) {
      setTemplates([]);
      setError(err.message || 'Failed to fetch templates');
    } finally {
      setLoadingTemplates(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  useEffect(() => {
    setMappings(mappingDefaults(selectedTemplate));
    setValidation(null);
    setSendResult(null);
    setPreviewUserId('');
  }, [selectedKey, selectedTemplate]);

  const updateMapping = (key, updates) => {
    setMappings((current) => ({
      ...current,
      [key]: { ...(current[key] || {}), ...updates },
    }));
    setValidation(null);
    setSendResult(null);
  };

  const validate = async () => {
    setError('');
    setSendResult(null);
    if (parsed.invalid.length) {
      setError(`Invalid user ID values: ${parsed.invalid.join(', ')}`);
      return;
    }
    if (!parsed.ids.length) {
      setError('Enter at least one user ID.');
      return;
    }
    if (parsed.ids.length > recipientLimit) {
      setError(`A ${mode === 'campaign' ? 'campaign' : 'quick send'} can contain at most ${recipientLimit.toLocaleString()} users.`);
      return;
    }
    setValidating(true);
    try {
      if (!selectedTemplate) {
        setError('Select an approved template.');
        return;
      }
      const response = await fetch('/api/admin/whatsapp/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAdminAuthHeaders() },
        body: JSON.stringify({
          user_ids: mode === 'campaign' ? parsed.ids.slice(0, 100) : parsed.ids,
          template_name: selectedTemplate.name,
          language: selectedTemplate.language,
          mappings: mappingsPayload(mappings),
          include_unlinked: includeUnlinked,
        }),
      });
      if (!response.ok) throw new Error(await apiError(response, 'Recipient validation failed'));
      const data = await response.json();
      setValidation(data);
      setPreviewUserId(data.preview?.[0] ? String(data.preview[0].user_id) : '');
    } catch (err) {
      setValidation(null);
      setError(err.message || 'Recipient validation failed');
    } finally {
      setValidating(false);
    }
  };

  const send = async () => {
    setError('');
    if (!selectedTemplate) {
      setError('Select an approved template.');
      return;
    }
    if (!validation) {
      setError('Validate recipients before sending.');
      return;
    }
    if ((validation.coverage?.blocked || 0) > 0) {
      setError('Resolve all missing template variables before sending.');
      return;
    }
    const summary = validation.summary || {};
    const intended = (summary.linked || 0) + (includeUnlinked ? summary.phone_only || 0 : 0);
    if (!intended) {
      setError('No recipients are eligible under the selected recipient option.');
      return;
    }
    const warning = includeUnlinked && summary.phone_only
      ? `\n\n${summary.phone_only} recipient(s) have a phone number but no linked WhatsApp account or recorded consent. Meta may reject delivery.`
      : '';
    if (!window.confirm(`Send “${selectedTemplate.name}” to ${intended} recipient(s)?${warning}`)) return;

    setSending(true);
    setSendResult(null);
    try {
      const response = await fetch('/api/admin/whatsapp/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAdminAuthHeaders() },
        body: JSON.stringify({
          user_ids: parsed.ids,
          template_name: selectedTemplate.name,
          language: selectedTemplate.language,
          mappings: mappingsPayload(mappings),
          include_unlinked: includeUnlinked,
        }),
      });
      if (!response.ok) throw new Error(await apiError(response, 'WhatsApp send failed'));
      setSendResult(await response.json());
    } catch (err) {
      setError(err.message || 'WhatsApp send failed');
    } finally {
      setSending(false);
    }
  };

  const createCampaign = async (status) => {
    setError('');
    if (!selectedTemplate) {
      setError('Select an approved template.');
      return;
    }
    if (!campaignName.trim()) {
      setError('Enter a campaign name.');
      return;
    }
    if (parsed.invalid.length || !parsed.ids.length || parsed.ids.length > 10000) {
      setError(parsed.ids.length > 10000 ? 'A campaign can contain at most 10,000 users.' : 'Enter valid campaign user IDs.');
      return;
    }
    if (!validation) {
      setError('Check recipients and values before saving the campaign.');
      return;
    }
    if (status === 'scheduled' && !scheduledAt) {
      setError('Choose a schedule date and time.');
      return;
    }
    setSending(true);
    setSendResult(null);
    try {
      const response = await fetch('/api/admin/whatsapp/campaigns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAdminAuthHeaders() },
        body: JSON.stringify({
          name: campaignName.trim(),
          user_ids: parsed.ids,
          template_name: selectedTemplate.name,
          language: selectedTemplate.language,
          mappings: mappingsPayload(mappings),
          include_unlinked: includeUnlinked,
          status,
          scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
          conversion_event: conversionEvent,
          frequency_cap_days: Number(frequencyCapDays) || 0,
        }),
      });
      if (!response.ok) throw new Error(await apiError(response, 'Could not create WhatsApp campaign'));
      const result = await response.json();
      setSendResult({ ...result, campaignCreated: true });
      if (typeof onCampaignCreated === 'function') onCampaignCreated(result);
    } catch (err) {
      setError(err.message || 'Could not create WhatsApp campaign');
    } finally {
      setSending(false);
    }
  };

  const addAudience = ({ userIds }) => {
    const merged = [...new Set([...parsed.ids, ...(userIds || []).map(Number).filter(Boolean)])];
    if (merged.length > 10000) {
      return { ok: false, error: `This audience would contain ${merged.length.toLocaleString()} users; the limit is 10,000.` };
    }
    setUserIdsText(merged.join(', '));
    setValidation(null);
    setSendResult(null);
    setAudienceBuilderOpen(false);
    return { ok: true };
  };

  useEffect(() => {
    if (!audienceBuilderOpen) return undefined;
    const close = (event) => {
      if (event.key === 'Escape') setAudienceBuilderOpen(false);
    };
    document.addEventListener('keydown', close);
    return () => document.removeEventListener('keydown', close);
  }, [audienceBuilderOpen]);

  const summary = validation?.summary || {};
  const selectedPreview = (validation?.preview || []).find(
    (row) => String(row.user_id) === String(previewUserId)
  );
  const activePreviewValues = selectedPreview?.values || localPreviewValues(selectedTemplate, mappings);

  return (
    <div className="wa-template-admin">
      <div className="wa-template-heading-row">
        <div>
          <div className="wa-title-eyebrow">Outbound messaging</div>
          <h3>WhatsApp message templates</h3>
          <p className="notifications-description">
            {mode === 'campaign'
              ? 'Build a saved, scheduled and measurable campaign from an approved Meta template.'
              : 'Fetch approved templates from Meta and send one immediately to specific AstroRoshni user IDs.'}
          </p>
        </div>
        <button type="button" className="notif-search-btn" onClick={loadTemplates} disabled={loadingTemplates}>
          {loadingTemplates ? 'Refreshing…' : 'Refresh from Meta'}
        </button>
      </div>

      {error && <div className="notif-result error">{error}</div>}

      {!campaignOnly && (
        <div className="wa-mode-switch" role="tablist" aria-label="WhatsApp send mode">
          <button type="button" role="tab" aria-selected={mode === 'quick'} className={mode === 'quick' ? 'is-active' : ''} onClick={() => { setMode('quick'); setValidation(null); setSendResult(null); }}>
            Quick send <span>Send now to up to 100 users</span>
          </button>
          <button type="button" role="tab" aria-selected={mode === 'campaign'} className={mode === 'campaign' ? 'is-active' : ''} onClick={() => { setMode('campaign'); setValidation(null); setSendResult(null); }}>
            Create campaign <span>Audience, scheduling and analytics</span>
          </button>
        </div>
      )}

      <div className="notifications-form notifications-form--wide wa-template-grid">
        <section className="wa-template-card">
          <div className="wa-card-heading">
            <span className="wa-step">1</span>
            <div>
              <h4>Choose a template</h4>
              <p>Select an approved Meta template and complete its variables.</p>
            </div>
          </div>
          <div className="form-field">
            <label>Template</label>
            <select value={selectedKey} onChange={(event) => setSelectedKey(event.target.value)} disabled={loadingTemplates}>
              {!templates.length && <option value="">No approved templates loaded</option>}
              {templates.map((template) => (
                <option
                  key={`${template.id || template.name}-${template.language}`}
                  value={`${template.name}::${template.language}`}
                  disabled={!template.supported}
                >
                  {template.name} · {template.language} · {template.category || 'uncategorized'}
                  {!template.supported ? ` · unavailable (${template.unsupported_reason})` : ''}
                </option>
              ))}
            </select>
          </div>

          {selectedTemplate && (
            <div className="wa-template-preview">
              <div className="wa-preview-topline">
                <div className="wa-preview-meta">
                  <span>{selectedTemplate.status}</span><span>{selectedTemplate.category}</span><span>{selectedTemplate.language}</span>
                </div>
                {!!validation?.preview?.length && (
                  <select
                    className="wa-preview-user-select"
                    value={previewUserId}
                    onChange={(event) => setPreviewUserId(event.target.value)}
                    aria-label="Preview recipient"
                  >
                    {validation.preview.map((row) => (
                      <option key={row.user_id} value={row.user_id}>
                        Preview: {row.name || `User ${row.user_id}`}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              {componentText(selectedTemplate, 'HEADER') && (
                <strong>{previewText(componentText(selectedTemplate, 'HEADER'), 'HEADER', activePreviewValues)}</strong>
              )}
              <p>
                {previewText(componentText(selectedTemplate, 'BODY'), 'BODY', activePreviewValues)
                  || 'This template has no text body.'}
              </p>
              {componentText(selectedTemplate, 'FOOTER') && <small>{componentText(selectedTemplate, 'FOOTER')}</small>}
            </div>
          )}

          {!!(selectedTemplate?.variables || []).length && (
            <div className="wa-variables-section">
              <div className="wa-section-heading">
                <div className="wa-section-label">Variable mapping</div>
                <small>Personalized separately for every user ID.</small>
              </div>
              <div className="wa-personalization-note">
                Each recipient gets their own values. For this template, AstroRoshni looks up their name and creates a different secure Credits link for them.
              </div>
              <div className="wa-mapping-list">
                {selectedTemplate.variables.map((variable) => (
                  <div className="wa-mapping-row" key={variable.key}>
                    <div className="wa-mapping-name">
                      <strong>{variable.label || humanize(variable.token)}</strong>
                      <span>{variable.component.toLowerCase()} · {`{{${variable.token}}}`}</span>
                    </div>
                    <div className="wa-mapping-controls">
                      <label className="wa-control-group">
                        <span>How should this value be filled?</span>
                        <select
                          value={mappings[variable.key]?.source || 'fixed'}
                          onChange={(event) => updateMapping(variable.key, { source: event.target.value })}
                          aria-label={`Source for ${variable.key}`}
                        >
                          <option value="fixed">Use the same value for everyone</option>
                          <option value="user_field">Look it up from each user’s account</option>
                          <option value="per_user">I will provide a different value for each user</option>
                          <option value="generator">Generate a secure value for each user</option>
                        </select>
                      </label>

                      {(mappings[variable.key]?.source || 'fixed') === 'fixed' && (
                        <label className="wa-control-group">
                          <span>Value everyone will receive</span>
                          <input
                            type="text"
                            value={mappings[variable.key]?.value || ''}
                            onChange={(event) => updateMapping(variable.key, { value: event.target.value })}
                            placeholder="Value sent to every recipient"
                            maxLength={2000}
                          />
                        </label>
                      )}

                      {mappings[variable.key]?.source === 'user_field' && (
                        <>
                          <div className="wa-mapping-inline">
                            <label className="wa-control-group">
                              <span>Look up this field</span>
                              <select
                                value={mappings[variable.key]?.field || 'name'}
                                onChange={(event) => updateMapping(variable.key, { field: event.target.value })}
                              >
                                <option value="name">Name from the users table</option>
                                <option value="userid">User ID</option>
                                <option value="phone">Phone number</option>
                                <option value="email">Email address</option>
                              </select>
                            </label>
                            <label className="wa-control-group">
                              <span>If that field is empty, use</span>
                              <input
                                type="text"
                                value={mappings[variable.key]?.fallback || ''}
                                onChange={(event) => updateMapping(variable.key, { fallback: event.target.value })}
                                placeholder="Fallback value"
                              />
                            </label>
                          </div>
                          <div className="wa-mapping-explanation">
                            For every entered user ID, the backend fetches that user’s {mappings[variable.key]?.field || 'name'} from the users table.
                          </div>
                        </>
                      )}

                      {mappings[variable.key]?.source === 'per_user' && (
                        <label className="wa-control-group">
                          <span>Enter one “user ID, value” pair per line</span>
                          <textarea
                            className="wa-per-user-values"
                            value={mappings[variable.key]?.valuesText || ''}
                            onChange={(event) => updateMapping(variable.key, { valuesText: event.target.value })}
                            placeholder={'123, Value for user 123\n456, Value for user 456'}
                          />
                        </label>
                      )}

                      {mappings[variable.key]?.source === 'generator' && (
                        <>
                          <label className="wa-control-group">
                            <span>Generate this value</span>
                            <select
                              value={mappings[variable.key]?.generator || 'credits_continue_token'}
                              onChange={(event) => updateMapping(variable.key, { generator: event.target.value })}
                            >
                              <option value="credits_continue_token">Unique secure Credits-link token</option>
                              <option value="credits_continue_url">Unique full secure Credits URL</option>
                            </select>
                          </label>
                          <div className="wa-mapping-explanation">
                            A different secure value is created for each user when the message is sent.
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        <section className="wa-template-card">
          <div className="wa-card-heading">
            <span className="wa-step">2</span>
            <div>
              <h4>Add recipients</h4>
              <p>Paste AstroRoshni user IDs, validate them, then review the send.</p>
            </div>
          </div>
          {mode === 'campaign' && (
            <div className="wa-campaign-settings">
              <div className="form-field">
                <label>Campaign name</label>
                <input value={campaignName} onChange={(event) => setCampaignName(event.target.value)} placeholder="September credit win-back" maxLength={200} />
              </div>
              <div className="form-field">
                <label>Schedule time (optional)</label>
                <input type="datetime-local" value={scheduledAt} onChange={(event) => setScheduledAt(event.target.value)} />
              </div>
              <div className="form-field">
                <label>Conversion</label>
                <select value={conversionEvent} onChange={(event) => setConversionEvent(event.target.value)}>
                  <option value="click">Tracked link clicked</option>
                  <option value="credit_purchase">Credits purchased</option>
                  <option value="subscription_purchase">Subscription purchased</option>
                  <option value="question">Question asked</option>
                  <option value="none">Delivery only</option>
                </select>
              </div>
              <div className="form-field">
                <label>WhatsApp frequency cap</label>
                <select value={frequencyCapDays} onChange={(event) => setFrequencyCapDays(event.target.value)}>
                  <option value="0">No campaign-level cap</option>
                  <option value="1">Exclude users messaged in 1 day</option>
                  <option value="3">Exclude users messaged in 3 days</option>
                  <option value="7">Exclude users messaged in 7 days</option>
                  <option value="14">Exclude users messaged in 14 days</option>
                  <option value="30">Exclude users messaged in 30 days</option>
                </select>
              </div>
            </div>
          )}
          <div className="form-field">
            <div className="wa-field-heading">
              <label>User IDs</label>
              <div className="wa-recipient-heading-actions">
                <span>{parsed.ids.length.toLocaleString()}/{recipientLimit.toLocaleString()}</span>
                {mode === 'campaign' && <button type="button" onClick={() => setAudienceBuilderOpen(true)}>Build an audience</button>}
              </div>
            </div>
            <textarea
              className="notif-paste-ids-input"
              value={userIdsText}
              onChange={(event) => {
                setUserIdsText(event.target.value);
                setValidation(null);
                setSendResult(null);
              }}
              placeholder="123, 456, 789"
            />
            <small>Separate IDs with commas, spaces, or new lines.{mode === 'campaign' && parsed.ids.length > 100 ? ' Validation previews the first 100; campaign creation validates the complete audience.' : ''}</small>
          </div>

          <label className="wa-unlinked-option">
            <input
              type="checkbox"
              checked={includeUnlinked}
              onChange={(event) => {
                setIncludeUnlinked(event.target.checked);
                setValidation(null);
                setSendResult(null);
              }}
            />
            <span className="wa-warning-mark" aria-hidden="true">!</span>
            <span>
              <strong>Send to users who only have a phone number</strong>
              <small>Turn this on when an entered user is not linked to WhatsApp yet. Meta will attempt delivery using the phone number in the users table.</small>
            </span>
          </label>

          <div className="wa-actions">
            <button type="button" className="wa-button wa-button--secondary" onClick={validate} disabled={validating || sending}>
              {validating ? 'Checking…' : 'Check recipients and values'}
            </button>
            {mode === 'quick' ? (
              <button
                type="button"
                className="wa-button wa-button--primary"
                onClick={send}
                disabled={!validation || sending || loadingTemplates || (validation.coverage?.blocked || 0) > 0 || !(validation.coverage?.eligible > 0)}
              >
                {sending ? 'Sending…' : 'Review and send'}
              </button>
            ) : (
              <>
                <button type="button" className="wa-button wa-button--secondary" onClick={() => createCampaign('draft')} disabled={!validation || sending || !campaignName.trim()}>
                  {sending ? 'Saving…' : 'Save draft'}
                </button>
                <button type="button" className="wa-button wa-button--secondary" onClick={() => createCampaign('send_now')} disabled={!validation || sending || !campaignName.trim()}>
                  {sending ? 'Starting…' : 'Send now'}
                </button>
                <button type="button" className="wa-button wa-button--primary" onClick={() => createCampaign('scheduled')} disabled={!validation || sending || !campaignName.trim() || !scheduledAt}>
                  {sending ? 'Scheduling…' : 'Schedule campaign'}
                </button>
              </>
            )}
          </div>

          {validation && (
            <>
              <div className="wa-coverage-banner">
                <div>
                  <strong>{validation.coverage?.resolved || 0}/{validation.coverage?.eligible || 0}</strong>
                  <span>recipients will receive this message</span>
                </div>
                <span className={
                  !validation.coverage?.eligible || validation.coverage?.blocked
                    ? 'is-blocked'
                    : 'is-ready'
                }>
                  {!validation.coverage?.eligible
                    ? 'No recipients included'
                    : validation.coverage?.blocked
                    ? `${validation.coverage.blocked} need attention`
                    : 'Ready to send'}
                </span>
              </div>
              {!!summary.phone_only && !includeUnlinked && (
                <div className="wa-exclusion-note">
                  <strong>{summary.phone_only} phone-only user{summary.phone_only === 1 ? ' is' : 's are'} currently excluded.</strong>
                  <span>Turn on “Send to users who only have a phone number,” then check recipients again.</span>
                </div>
              )}
              <div className="wa-recipient-summary">
                <div><strong>{summary.linked || 0}</strong><span>Linked and included</span></div>
                <div><strong>{summary.phone_only || 0}</strong><span>{includeUnlinked ? 'Phone only and included' : 'Phone only and excluded'}</span></div>
                <div><strong>{summary.no_phone || 0}</strong><span>No phone</span></div>
                <div><strong>{summary.not_found || 0}</strong><span>Not found</span></div>
              </div>
              {!!validation.coverage?.blocked && (
                <div className="wa-missing-list">
                  {validation.preview.filter((row) => !row.resolved).slice(0, 8).map((row) => (
                    <div key={row.user_id}>
                      <strong>User {row.user_id}</strong>
                      <span>Missing: {row.missing.join(', ')}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </section>
      </div>

      {sendResult && (
        <section className="wa-template-card wa-send-results">
          <h4>{sendResult.campaignCreated ? 'Campaign created' : 'Send result'}</h4>
          {sendResult.campaignCreated ? (
            <p>Campaign #{sendResult.campaign_id} is {sendResult.status}.{sendResult.scheduled_at ? ` Scheduled for ${new Date(sendResult.scheduled_at).toLocaleString()}.` : ''}</p>
          ) : <p>Accepted: {sendResult.accepted} · Failed: {sendResult.failed} · Skipped: {sendResult.skipped}</p>}
          {!sendResult.campaignCreated && <div className="wa-results-table-wrap">
            <table>
              <thead><tr><th>User ID</th><th>Result</th><th>Detail</th></tr></thead>
              <tbody>
                {(sendResult.results || []).map((row) => (
                  <tr key={row.user_id}>
                    <td>{row.user_id}</td><td>{row.status}</td><td>{row.error || 'Accepted by Meta'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>}
        </section>
      )}
      {audienceBuilderOpen && (
        <div className="wa-audience-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget) setAudienceBuilderOpen(false);
        }}>
          <section className="wa-audience-modal" role="dialog" aria-modal="true" aria-labelledby="wa-audience-title">
            <header className="wa-audience-header">
              <div><span>WhatsApp campaign</span><h3 id="wa-audience-title">Build recipient audience</h3><p>Selections append to manual IDs and duplicates are removed.</p></div>
              <button type="button" onClick={() => setAudienceBuilderOpen(false)}>Close</button>
            </header>
            <div className="wa-audience-body">
              <AdminAudienceBuilder audienceOnly onAudienceSelected={addAudience} selectionActionLabel="Add selected to WhatsApp campaign" />
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
