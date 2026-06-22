import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

const CHANNEL_OPTIONS = ['push', 'whatsapp', 'email'];
const AUDIENCE_OPTIONS = [
  { value: 'all', label: 'All users' },
  { value: 'has_device_token', label: 'Users with push enabled' },
  { value: 'no_device_token', label: 'Users without push (WhatsApp/email reachable)' },
  { value: 'active_chat_days', label: 'Asked a question in last N days' },
  { value: 'inactive_chat_days', label: 'No question in last N days' },
  { value: 'user_ids', label: 'Specific user IDs' },
];
const LANDING_OPTIONS = [
  'chat', 'information', 'event_screen', 'past_life_karma',
  'career', 'marriage', 'health', 'wealth', 'progeny', 'education',
];
const LIFECYCLE_STEPS = [
  {
    title: '1. Define audience',
    text: 'Start with a broad audience, then narrow it with activity, credit, or astrological filters.',
  },
  {
    title: '2. Estimate reach',
    text: 'Check how many users can actually receive the campaign on push, WhatsApp, and email.',
  },
  {
    title: '3. Write the message',
    text: 'Compose the title, body, and optional follow-up question using placeholders when useful.',
  },
  {
    title: '4. Preview it',
    text: 'Render the campaign for yourself or a sample user before anything goes live.',
  },
  {
    title: '5. Launch safely',
    text: 'Save as draft, schedule it, or send it now. To stop a draft or scheduled campaign, delete it below.',
  },
];

const emptyForm = {
  name: '',
  title_template: '',
  body_template: '',
  question_template: '',
  image_url: '',
  channel_policy: 'waterfall',
  channels: ['push', 'whatsapp', 'email'],
  ai_personalize: false,
  ai_base_prompt: '',
  audience_type: 'all',
  audience_days: 7,
  audience_user_ids: '',
  require_self_chart: true,
  has_email: '',
  has_whatsapp: '',
  free_question_available: '',
  signup_clients: '',
  min_days_since_last_chat: '',
  max_days_since_last_chat: '',
  min_questions_asked: '',
  max_questions_asked: '',
  min_credits_balance: '',
  max_credits_balance: '',
  sun_signs: '',
  moon_signs: '',
  ascendant_signs: '',
  mahadashas: '',
  antardashas: '',
  current_dasha_contains: '',
  landing_screen: 'chat',
  scheduled_at: '',
};

async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      ...getAdminAuthHeaders(),
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return body;
}

export default function AdminNudgeCampaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [placeholders, setPlaceholders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [resultMsg, setResultMsg] = useState('');
  const [resultOk, setResultOk] = useState(true);
  const [saving, setSaving] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [imageUploading, setImageUploading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [previewUserId, setPreviewUserId] = useState('');
  const [audienceEstimate, setAudienceEstimate] = useState(null);
  const [estimatingAudience, setEstimatingAudience] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [busyCampaignId, setBusyCampaignId] = useState(null);

  const setField = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));
  const showResult = (ok, msg) => {
    setResultOk(ok);
    setResultMsg(msg);
  };

  const resetEditor = () => {
    setEditingId(null);
    setForm(emptyForm);
    setPreview(null);
    setAudienceEstimate(null);
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const body = await apiFetch('/api/nudge/admin/campaigns');
      setCampaigns(body.items || []);
      setPlaceholders(body.allowed_placeholders || []);
    } catch (e) {
      setError(e.message || 'Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const buildPayload = () => {
    const audience = { type: form.audience_type };
    if (form.audience_type === 'active_chat_days' || form.audience_type === 'inactive_chat_days') {
      audience.days = Math.max(1, Number(form.audience_days) || 7);
    }
    if (form.audience_type === 'user_ids') {
      audience.user_ids = String(form.audience_user_ids || '')
        .split(/[\s,]+/)
        .map((x) => Number(x))
        .filter((n) => Number.isInteger(n) && n > 0);
    }

    const splitCsv = (value) =>
      String(value || '')
        .split(',')
        .map((x) => x.trim())
        .filter(Boolean);

    const boolOrUndefined = (value) => {
      if (value === 'yes') return true;
      if (value === 'no') return false;
      return undefined;
    };

    audience.criteria = {
      require_self_chart: !!form.require_self_chart,
      has_email: boolOrUndefined(form.has_email),
      has_whatsapp: boolOrUndefined(form.has_whatsapp),
      free_question_available: boolOrUndefined(form.free_question_available),
      signup_clients: splitCsv(form.signup_clients),
      min_days_since_last_chat:
        form.min_days_since_last_chat === '' ? undefined : Number(form.min_days_since_last_chat),
      max_days_since_last_chat:
        form.max_days_since_last_chat === '' ? undefined : Number(form.max_days_since_last_chat),
      min_questions_asked: form.min_questions_asked === '' ? undefined : Number(form.min_questions_asked),
      max_questions_asked: form.max_questions_asked === '' ? undefined : Number(form.max_questions_asked),
      min_credits_balance: form.min_credits_balance === '' ? undefined : Number(form.min_credits_balance),
      max_credits_balance: form.max_credits_balance === '' ? undefined : Number(form.max_credits_balance),
      sun_signs: splitCsv(form.sun_signs),
      moon_signs: splitCsv(form.moon_signs),
      ascendant_signs: splitCsv(form.ascendant_signs),
      mahadashas: splitCsv(form.mahadashas),
      antardashas: splitCsv(form.antardashas),
      current_dasha_contains: String(form.current_dasha_contains || '').trim() || undefined,
    };

    return {
      name: form.name.trim(),
      title_template: form.title_template.trim(),
      body_template: form.body_template.trim(),
      question_template: form.question_template.trim(),
      image_url: String(form.image_url || '').trim(),
      channel_policy: form.channel_policy,
      channels: form.channels,
      ai_personalize: !!form.ai_personalize,
      ai_base_prompt: form.ai_base_prompt.trim(),
      audience_filter: audience,
      landing_screen: form.landing_screen,
      scheduled_at: form.scheduled_at ? new Date(form.scheduled_at).toISOString() : null,
      status: form.scheduled_at ? 'scheduled' : 'draft',
    };
  };

  const handleEstimateAudience = async () => {
    setEstimatingAudience(true);
    setAudienceEstimate(null);
    showResult(true, '');
    try {
      const payload = buildPayload();
      const body = await apiFetch('/api/nudge/admin/campaigns/audience-estimate', {
        method: 'POST',
        body: JSON.stringify({ audience_filter: payload.audience_filter }),
      });
      setAudienceEstimate(body);
    } catch (e) {
      showResult(false, e.message || 'Audience estimate failed');
    } finally {
      setEstimatingAudience(false);
    }
  };

  const handleSave = async () => {
    if (!form.name.trim() || !form.title_template.trim() || !form.body_template.trim()) {
      showResult(false, 'Name, title and body are required.');
      return;
    }
    if (!form.channels.length) {
      showResult(false, 'Select at least one channel.');
      return;
    }

    setSaving(true);
    showResult(true, '');
    try {
      if (editingId) {
        await apiFetch(`/api/nudge/admin/campaigns/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify(buildPayload()),
        });
        showResult(true, 'Campaign updated.');
      } else {
        await apiFetch('/api/nudge/admin/campaigns', {
          method: 'POST',
          body: JSON.stringify(buildPayload()),
        });
        showResult(true, form.scheduled_at ? 'Campaign scheduled.' : 'Campaign saved as draft.');
      }
      resetEditor();
      await load();
    } catch (e) {
      showResult(false, e.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handlePreview = async () => {
    if (!form.title_template.trim() || !form.body_template.trim()) {
      showResult(false, 'Enter title and body first.');
      return;
    }
    setPreviewing(true);
    setPreview(null);
    showResult(true, '');
    try {
      const body = await apiFetch('/api/nudge/admin/campaigns/preview', {
        method: 'POST',
        body: JSON.stringify({
          title_template: form.title_template.trim(),
          body_template: form.body_template.trim(),
          question_template: form.question_template.trim(),
          image_url: String(form.image_url || '').trim(),
          ai_personalize: !!form.ai_personalize,
          ai_base_prompt: form.ai_base_prompt.trim(),
          ...(previewUserId ? { user_id: Number(previewUserId) } : {}),
        }),
      });
      setPreview(body);
    } catch (e) {
      showResult(false, e.message || 'Preview failed');
    } finally {
      setPreviewing(false);
    }
  };

  const handleEdit = (campaign) => {
    const audience = campaign.audience_filter || { type: 'all' };
    const criteria = audience.criteria || {};
    setEditingId(campaign.id);
    setPreview(null);
    setAudienceEstimate(null);
    setForm({
      name: campaign.name || '',
      title_template: campaign.title_template || '',
      body_template: campaign.body_template || '',
      question_template: campaign.question_template || '',
      image_url: campaign.image_url || '',
      channel_policy: campaign.channel_policy || 'waterfall',
      channels: (campaign.channels || []).length ? campaign.channels : ['push'],
      ai_personalize: !!campaign.ai_personalize,
      ai_base_prompt: campaign.ai_base_prompt || '',
      audience_type: audience.type || 'all',
      audience_days: audience.days || 7,
      audience_user_ids: (audience.user_ids || []).join(', '),
      require_self_chart: criteria.require_self_chart !== false,
      has_email: criteria.has_email === true ? 'yes' : criteria.has_email === false ? 'no' : '',
      has_whatsapp:
        criteria.has_whatsapp === true ? 'yes' : criteria.has_whatsapp === false ? 'no' : '',
      free_question_available:
        criteria.free_question_available === true
          ? 'yes'
          : criteria.free_question_available === false
            ? 'no'
            : '',
      signup_clients: (criteria.signup_clients || []).join(', '),
      min_days_since_last_chat: criteria.min_days_since_last_chat ?? '',
      max_days_since_last_chat: criteria.max_days_since_last_chat ?? '',
      min_questions_asked: criteria.min_questions_asked ?? '',
      max_questions_asked: criteria.max_questions_asked ?? '',
      min_credits_balance: criteria.min_credits_balance ?? '',
      max_credits_balance: criteria.max_credits_balance ?? '',
      sun_signs: (criteria.sun_signs || []).join(', '),
      moon_signs: (criteria.moon_signs || []).join(', '),
      ascendant_signs: (criteria.ascendant_signs || []).join(', '),
      mahadashas: (criteria.mahadashas || []).join(', '),
      antardashas: (criteria.antardashas || []).join(', '),
      current_dasha_contains: criteria.current_dasha_contains || '',
      landing_screen: campaign.landing_screen || 'chat',
      scheduled_at: campaign.scheduled_at ? campaign.scheduled_at.slice(0, 16) : '',
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCampaignImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageUploading(true);
    showResult(true, '');
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('alt_text', form.name?.trim() || 'Campaign image');
      const res = await fetch('/api/nudge/admin/campaigns/upload-image', {
        method: 'POST',
        headers: getAdminAuthHeaders(),
        body: formData,
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || 'Failed to upload image');
      }
      setField('image_url', body.url || '');
      showResult(true, 'Campaign image uploaded.');
    } catch (err) {
      showResult(false, err.message || 'Failed to upload image');
    } finally {
      setImageUploading(false);
      e.target.value = '';
    }
  };

  const handleAction = async (campaignId, action, confirmText) => {
    if (confirmText && !window.confirm(confirmText)) return;
    setBusyCampaignId(campaignId);
    showResult(true, '');
    try {
      if (action === 'delete') {
        await apiFetch(`/api/nudge/admin/campaigns/${campaignId}`, { method: 'DELETE' });
        showResult(true, 'Campaign deleted.');
      } else if (action === 'send-now') {
        const body = await apiFetch(`/api/nudge/admin/campaigns/${campaignId}/send-now`, {
          method: 'POST',
        });
        showResult(
          true,
          `Dispatched: ${body.users_targeted || 0} users in ${body.batches || 0} batch(es)` +
            (body.queued ? ' (queued via Cloud Tasks).' : '.')
        );
      } else if (action === 'test-send') {
        const body = await apiFetch(`/api/nudge/admin/campaigns/${campaignId}/test-send`, {
          method: 'POST',
          body: JSON.stringify({}),
        });
        const channel = body.delivery?.channel || 'stored';
        showResult(true, `Test sent to you via "${channel}". Title: ${body.copy?.title || ''}`);
      } else if (action === 'pause' || action === 'resume-scheduled' || action === 'resume-draft') {
        const nextStatus = action === 'pause' ? 'paused' : action === 'resume-scheduled' ? 'scheduled' : 'draft';
        await apiFetch(`/api/nudge/admin/campaigns/${campaignId}/status`, {
          method: 'POST',
          body: JSON.stringify({ status: nextStatus }),
        });
        showResult(
          true,
          action === 'pause'
            ? 'Campaign paused.'
            : nextStatus === 'scheduled'
              ? 'Campaign resumed and scheduled again.'
              : 'Campaign resumed as draft.'
        );
      }
      await load();
    } catch (e) {
      showResult(false, e.message || 'Action failed');
    } finally {
      setBusyCampaignId(null);
    }
  };

  const insertPlaceholder = (name) => {
    setField('body_template', `${form.body_template}{${name}}`);
  };

  const toggleChannel = (channel) => {
    setForm((prev) => {
      const has = prev.channels.includes(channel);
      return {
        ...prev,
        channels: has ? prev.channels.filter((c) => c !== channel) : [...prev.channels, channel],
      };
    });
  };

  const moveChannel = (channel, direction) => {
    setForm((prev) => {
      const idx = prev.channels.indexOf(channel);
      const next = idx + direction;
      if (idx < 0 || next < 0 || next >= prev.channels.length) return prev;
      const channels = [...prev.channels];
      [channels[idx], channels[next]] = [channels[next], channels[idx]];
      return { ...prev, channels };
    });
  };

  const statusLabel = useMemo(
    () => ({
      draft: 'Draft',
      scheduled: 'Scheduled',
      paused: 'Paused',
      sending: 'Sending...',
      sent: 'Sent',
      cancelled: 'Cancelled',
    }),
    []
  );

  const statusTone = useMemo(
    () => ({
      draft: 'neutral',
      scheduled: 'info',
      paused: 'warn',
      sending: 'warn',
      sent: 'success',
      cancelled: 'neutral',
    }),
    []
  );

  const primaryActionLabel = (campaign) => {
    if (campaign.status === 'draft') return 'Send now';
    if (campaign.status === 'scheduled') return 'Send now instead';
    if (campaign.status === 'paused') return 'Resume';
    return 'Test to me';
  };

  if (loading) {
    return <p className="notifications-description">Loading campaigns...</p>;
  }

  if (error) {
    return (
      <div className="notif-result error">
        <strong>Could not load campaigns.</strong> {error}
      </div>
    );
  }

  return (
    <div className="nudge-campaigns-admin">
      <div className="nudge-console-header">
        <div>
          <div className="nudge-console-eyebrow">Campaign control</div>
          <h3 className="nudge-console-title">User re-engagement campaigns</h3>
          <p className="notifications-description nudge-console-description">
            Build nudges with real audience filters, message previews, and channel reach checks before
            you launch anything.
          </p>
        </div>
        <div className="nudge-console-legend">
          <div><strong>Draft:</strong> saved, not live yet</div>
          <div><strong>Scheduled:</strong> will launch at the chosen time</div>
          <div><strong>Sent:</strong> already dispatched</div>
          <div><strong>Pause:</strong> temporarily stop a scheduled or draft campaign without deleting it</div>
        </div>
      </div>

      <div className="nudge-lifecycle-grid">
        {LIFECYCLE_STEPS.map((step) => (
          <div key={step.title} className="nudge-lifecycle-card">
            <strong>{step.title}</strong>
            <p>{step.text}</p>
          </div>
        ))}
      </div>

      <div className="notifications-form notifications-form--wide nudge-campaign-builder">
        <section className="nudge-builder-section">
          <div className="nudge-section-header">
            <div>
              <div className="nudge-section-eyebrow">
                {editingId ? `Editing campaign #${editingId}` : 'New campaign'}
              </div>
              <h4 className="nudge-builder-section__title">Campaign basics</h4>
            </div>
            <p className="nudge-section-tip">
              Start with the campaign name, where users should land, and which channels should be used.
            </p>
          </div>

          <div className="nudge-scheduler-row nudge-scheduler-row--3">
            <div className="form-field">
              <label>Campaign name</label>
              <input
                type="text"
                maxLength={200}
                placeholder="e.g. Saturn transit re-engagement"
                value={form.name}
                onChange={(e) => setField('name', e.target.value)}
              />
            </div>
            <div className="form-field">
              <label>Channel policy</label>
              <select value={form.channel_policy} onChange={(e) => setField('channel_policy', e.target.value)}>
                <option value="waterfall">Waterfall - stop at first successful channel</option>
                <option value="blast">Blast - send on every selected channel</option>
              </select>
            </div>
            <div className="form-field">
              <label>Landing screen</label>
              <select value={form.landing_screen} onChange={(e) => setField('landing_screen', e.target.value)}>
                {LANDING_OPTIONS.map((landing) => (
                  <option key={landing} value={landing}>{landing}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-field">
            <label>Channel order</label>
            <div className="nudge-channel-stack">
              {form.channels.map((channel, idx) => (
                <div key={channel} className="nudge-channel-row">
                  <div className="nudge-channel-order">{idx + 1}</div>
                  <div className="nudge-channel-name">{channel}</div>
                  <div className="nudge-channel-actions">
                    <button type="button" className="notif-search-btn" onClick={() => moveChannel(channel, -1)}>
                      Move up
                    </button>
                    <button type="button" className="notif-search-btn" onClick={() => moveChannel(channel, 1)}>
                      Move down
                    </button>
                    <button type="button" className="delete-btn" onClick={() => toggleChannel(channel)}>
                      Remove
                    </button>
                  </div>
                </div>
              ))}
              <div className="nudge-channel-add">
                {CHANNEL_OPTIONS.filter((channel) => !form.channels.includes(channel)).map((channel) => (
                  <button key={channel} type="button" className="notif-search-btn" onClick={() => toggleChannel(channel)}>
                    Add {channel}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="nudge-builder-section">
          <div className="nudge-section-header">
            <div>
              <div className="nudge-section-eyebrow">Audience</div>
              <h4 className="nudge-builder-section__title">Who should receive this?</h4>
            </div>
            <p className="nudge-section-tip">
              Pick the base group first. Use advanced filters only when you want a sharper, more intentional cohort.
            </p>
          </div>

          <div className="nudge-scheduler-row">
            <div className="form-field">
              <label>Base audience</label>
              <select value={form.audience_type} onChange={(e) => setField('audience_type', e.target.value)}>
                {AUDIENCE_OPTIONS.map((audience) => (
                  <option key={audience.value} value={audience.value}>{audience.label}</option>
                ))}
              </select>
            </div>
            {(form.audience_type === 'active_chat_days' || form.audience_type === 'inactive_chat_days') && (
              <div className="form-field">
                <label>Days (N)</label>
                <input
                  type="number"
                  min={1}
                  max={365}
                  value={form.audience_days}
                  onChange={(e) => setField('audience_days', e.target.value)}
                />
              </div>
            )}
          </div>

          {form.audience_type === 'user_ids' && (
            <div className="form-field">
              <label>User IDs (comma or space separated)</label>
              <textarea
                rows={2}
                placeholder="e.g. 12, 56, 102"
                value={form.audience_user_ids}
                onChange={(e) => setField('audience_user_ids', e.target.value)}
              />
            </div>
          )}

          <label className="notif-inline-checkbox">
            <input
              type="checkbox"
              checked={!!form.require_self_chart}
              onChange={(e) => setField('require_self_chart', e.target.checked)}
            />
            <span>Only include users who have their own birth chart saved</span>
          </label>

          <details className="nudge-advanced-block">
            <summary>Advanced audience filters</summary>
            <div className="nudge-advanced-block__body">
              <div className="nudge-scheduler-row nudge-scheduler-row--3">
                <div className="form-field">
                  <label>Has email</label>
                  <select value={form.has_email} onChange={(e) => setField('has_email', e.target.value)}>
                    <option value="">Any</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </div>
                <div className="form-field">
                  <label>Has WhatsApp</label>
                  <select value={form.has_whatsapp} onChange={(e) => setField('has_whatsapp', e.target.value)}>
                    <option value="">Any</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </div>
                <div className="form-field">
                  <label>Free question available</label>
                  <select value={form.free_question_available} onChange={(e) => setField('free_question_available', e.target.value)}>
                    <option value="">Any</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </div>
              </div>

              <div className="nudge-scheduler-row nudge-scheduler-row--3">
                <div className="form-field">
                  <label>Inactive from day</label>
                  <input type="number" min={0} value={form.min_days_since_last_chat} onChange={(e) => setField('min_days_since_last_chat', e.target.value)} />
                </div>
                <div className="form-field">
                  <label>Inactive until day</label>
                  <input type="number" min={0} value={form.max_days_since_last_chat} onChange={(e) => setField('max_days_since_last_chat', e.target.value)} />
                </div>
                <div className="form-field">
                  <label>Signup clients</label>
                  <input type="text" placeholder="web, mobile, whatsapp" value={form.signup_clients} onChange={(e) => setField('signup_clients', e.target.value)} />
                </div>
              </div>

              <div className="nudge-scheduler-row nudge-scheduler-row--3">
                <div className="form-field">
                  <label>Min questions asked</label>
                  <input type="number" min={0} value={form.min_questions_asked} onChange={(e) => setField('min_questions_asked', e.target.value)} />
                </div>
                <div className="form-field">
                  <label>Max questions asked</label>
                  <input type="number" min={0} value={form.max_questions_asked} onChange={(e) => setField('max_questions_asked', e.target.value)} />
                </div>
                <div className="form-field">
                  <label>Credits balance range</label>
                  <div className="nudge-split-inputs">
                    <input type="number" min={0} placeholder="min" value={form.min_credits_balance} onChange={(e) => setField('min_credits_balance', e.target.value)} />
                    <input type="number" min={0} placeholder="max" value={form.max_credits_balance} onChange={(e) => setField('max_credits_balance', e.target.value)} />
                  </div>
                </div>
              </div>

              <div className="nudge-scheduler-row nudge-scheduler-row--3">
                <div className="form-field">
                  <label>Sun signs</label>
                  <input type="text" placeholder="Aries, Taurus" value={form.sun_signs} onChange={(e) => setField('sun_signs', e.target.value)} />
                </div>
                <div className="form-field">
                  <label>Moon signs</label>
                  <input type="text" placeholder="Cancer, Pisces" value={form.moon_signs} onChange={(e) => setField('moon_signs', e.target.value)} />
                </div>
                <div className="form-field">
                  <label>Ascendant signs</label>
                  <input type="text" placeholder="Leo, Virgo" value={form.ascendant_signs} onChange={(e) => setField('ascendant_signs', e.target.value)} />
                </div>
              </div>

              <div className="nudge-scheduler-row nudge-scheduler-row--3">
                <div className="form-field">
                  <label>Mahadasha planets</label>
                  <input type="text" placeholder="Saturn, Venus" value={form.mahadashas} onChange={(e) => setField('mahadashas', e.target.value)} />
                </div>
                <div className="form-field">
                  <label>Antardasha planets</label>
                  <input type="text" placeholder="Mercury, Jupiter" value={form.antardashas} onChange={(e) => setField('antardashas', e.target.value)} />
                </div>
                <div className="form-field">
                  <label>Current dasha contains</label>
                  <input type="text" placeholder="Saturn-Rahu" value={form.current_dasha_contains} onChange={(e) => setField('current_dasha_contains', e.target.value)} />
                </div>
              </div>
            </div>
          </details>

          <div className="nudge-builder-toolbar">
            <button type="button" className="notif-search-btn" onClick={handleEstimateAudience} disabled={estimatingAudience}>
              {estimatingAudience ? 'Estimating...' : 'Estimate audience'}
            </button>
            <span className="nudge-toolbar-hint">
              Run this before scheduling or sending so you understand scale and channel reach.
            </span>
          </div>

          {audienceEstimate && (
            <div className="nudge-estimate-card">
              <strong>Audience estimate</strong>
              <div className="nudge-estimate-metrics">
                <div><span>Total users</span><strong>{audienceEstimate.total_users || 0}</strong></div>
                <div><span>Push reachable</span><strong>{audienceEstimate.reachable?.push || 0}</strong></div>
                <div><span>WhatsApp reachable</span><strong>{audienceEstimate.reachable?.whatsapp || 0}</strong></div>
                <div><span>Email reachable</span><strong>{audienceEstimate.reachable?.email || 0}</strong></div>
                <div><span>Has self chart</span><strong>{audienceEstimate.has_self_chart || 0}</strong></div>
              </div>
              {Array.isArray(audienceEstimate.sample_user_ids) && audienceEstimate.sample_user_ids.length > 0 ? (
                <div className="nudge-estimate-sample">
                  Sample user IDs: {audienceEstimate.sample_user_ids.join(', ')}
                </div>
              ) : null}
            </div>
          )}
        </section>

        <section className="nudge-builder-section">
          <div className="nudge-section-header">
            <div>
              <div className="nudge-section-eyebrow">Message</div>
              <h4 className="nudge-builder-section__title">What will users see?</h4>
            </div>
            <p className="nudge-section-tip">
              Keep the copy specific and useful. Use placeholders or AI framing when you want stronger personalization.
            </p>
          </div>

          <div className="form-field">
            <label>Title template (max 200)</label>
            <input
              type="text"
              maxLength={200}
              placeholder="e.g. {name}, your {current_dasha} period needs attention"
              value={form.title_template}
              onChange={(e) => setField('title_template', e.target.value)}
            />
          </div>

          <div className="form-field">
            <label>Body template (max 600)</label>
            <textarea
              rows={3}
              maxLength={600}
              placeholder="e.g. It's been {days_since_last_chat} days since we talked about {last_question_topic}..."
              value={form.body_template}
              onChange={(e) => setField('body_template', e.target.value)}
            />
            <div className="nudge-placeholder-list">
              {placeholders.map((placeholder) => (
                <button
                  key={placeholder}
                  type="button"
                  className="notif-search-btn"
                  onClick={() => insertPlaceholder(placeholder)}
                >
                  {'{' + placeholder + '}'}
                </button>
              ))}
            </div>
          </div>

          <div className="form-field">
            <label>Suggested chat question template (optional, max 900)</label>
            <textarea
              rows={2}
              maxLength={900}
              placeholder="Pre-fills the chat input when the user taps the nudge"
              value={form.question_template}
              onChange={(e) => setField('question_template', e.target.value)}
            />
          </div>

          <div className="form-field">
            <label>Campaign image for Android push (optional)</label>
            <input
              type="text"
              placeholder="https://... or upload below"
              value={form.image_url}
              onChange={(e) => setField('image_url', e.target.value)}
            />
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 10, flexWrap: 'wrap' }}>
              <label className="notif-search-btn" style={{ cursor: imageUploading ? 'wait' : 'pointer' }}>
                {imageUploading ? 'Uploading...' : 'Upload image'}
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleCampaignImageUpload}
                  style={{ display: 'none' }}
                  disabled={imageUploading}
                />
              </label>
              {form.image_url ? (
                <button type="button" className="delete-btn" onClick={() => setField('image_url', '')}>
                  Remove image
                </button>
              ) : null}
            </div>
            {form.image_url ? (
              <div style={{ marginTop: 12 }}>
                <img
                  src={form.image_url}
                  alt="Campaign preview"
                  style={{ width: 180, maxWidth: '100%', borderRadius: 10, border: '1px solid #e8d7dd' }}
                />
              </div>
            ) : null}
          </div>

          <div className="form-field">
            <label className="notif-inline-checkbox">
              <input
                type="checkbox"
                checked={form.ai_personalize}
                onChange={(e) => setField('ai_personalize', e.target.checked)}
              />
              <span>Use AI to reframe the message per user using your base prompt and the resolved user parameters</span>
            </label>
            {form.ai_personalize && (
              <textarea
                rows={3}
                maxLength={2000}
                placeholder="Base prompt for Gemini, e.g. 'Nudge users to ask about career timing during their current dasha...'"
                value={form.ai_base_prompt}
                onChange={(e) => setField('ai_base_prompt', e.target.value)}
              />
            )}
          </div>

          <div className="nudge-scheduler-row">
            <div className="form-field">
              <label>Preview as user ID (optional)</label>
              <input
                type="number"
                placeholder="defaults to you"
                value={previewUserId}
                onChange={(e) => setPreviewUserId(e.target.value)}
              />
            </div>
            <div className="form-field nudge-preview-action">
              <label>&nbsp;</label>
              <button type="button" className="notif-search-btn" onClick={handlePreview} disabled={previewing}>
                {previewing ? 'Rendering...' : 'Preview campaign'}
              </button>
            </div>
          </div>

          {preview && (
            <div className="nudge-preview-card">
              <div><strong>Preview for user #{preview.user_id}</strong></div>
              <div><strong>Title:</strong> {preview.rendered?.title}</div>
              <div><strong>Body:</strong> {preview.rendered?.body}</div>
              {preview.rendered?.question ? (
                <div><strong>Question:</strong> {preview.rendered.question}</div>
              ) : null}
              <details>
                <summary>Resolved parameters</summary>
                <pre>{JSON.stringify(preview.params, null, 2)}</pre>
              </details>
            </div>
          )}
        </section>

        <section className="nudge-builder-section">
          <div className="nudge-section-header">
            <div>
              <div className="nudge-section-eyebrow">Launch</div>
              <h4 className="nudge-builder-section__title">Save, schedule, or send later</h4>
            </div>
            <p className="nudge-section-tip">
              Leaving the time empty keeps this as a draft. Scheduled or draft campaigns can be stopped by deleting them from the list below.
            </p>
          </div>

          <div className="nudge-scheduler-row">
            <div className="form-field">
              <label>Schedule time (optional)</label>
              <input
                type="datetime-local"
                value={form.scheduled_at}
                onChange={(e) => setField('scheduled_at', e.target.value)}
              />
            </div>
          </div>

          <div className="form-buttons nudge-builder-toolbar">
            <button type="button" className="create-btn" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : editingId ? 'Update campaign' : form.scheduled_at ? 'Save and schedule' : 'Save draft'}
            </button>
            {editingId && (
              <button type="button" className="notif-search-btn" onClick={resetEditor}>
                Cancel edit
              </button>
            )}
          </div>
        </section>
      </div>

      <div className="nudge-campaign-list">
        {campaigns.length === 0 ? (
          <div className="nudge-empty-state">
            No campaigns yet. Create one above, estimate the audience, and save it as a draft or schedule it.
          </div>
        ) : (
          campaigns.map((campaign) => (
            <article key={campaign.id} className="nudge-campaign-card">
              <div className="nudge-campaign-card__top">
                <div className="nudge-campaign-card__meta">
                  <div className="nudge-campaign-card__id">Campaign #{campaign.id}</div>
                  <h4>{campaign.name}</h4>
                  <p>{campaign.title_template}</p>
                </div>
                <span className={`nudge-status-pill nudge-status-pill--${statusTone[campaign.status] || 'neutral'}`}>
                  {statusLabel[campaign.status] || campaign.status}
                </span>
              </div>

              <div className="nudge-campaign-card__facts">
                <div><span>Channels</span><strong>{(campaign.channels || []).join(' -> ')}</strong></div>
                <div><span>Policy</span><strong>{campaign.channel_policy}</strong></div>
                <div><span>Scheduled</span><strong>{campaign.scheduled_at ? new Date(campaign.scheduled_at).toLocaleString() : 'Draft only'}</strong></div>
                <div><span>Targeted</span><strong>{campaign.total_targeted || 0}</strong></div>
                <div><span>Mode</span><strong>{campaign.ai_personalize ? 'AI personalized' : 'Template only'}</strong></div>
              </div>

              <div className="nudge-campaign-card__copy">
                {campaign.status === 'scheduled'
                  ? 'This campaign is queued for later. Delete it below if you want to stop it before launch.'
                  : campaign.status === 'paused'
                    ? 'This campaign is paused. Resume it as scheduled if it has a send time, or resume it as a draft for further editing.'
                  : campaign.status === 'draft'
                    ? 'This campaign is saved but not live yet. You can edit it, test it, or send it immediately.'
                    : 'This campaign has already been dispatched. You can still test it to yourself for a quick check.'}
              </div>

              {campaign.stats?.sends ? (
                <div className="nudge-campaign-card__facts" style={{ marginTop: '12px' }}>
                  <div><span>Push sent</span><strong>{campaign.stats.sends.push || 0}</strong></div>
                  <div><span>WhatsApp direct</span><strong>{campaign.stats.sends.whatsapp_direct || 0}</strong></div>
                  <div><span>WhatsApp template</span><strong>{campaign.stats.sends.whatsapp_template || 0}</strong></div>
                  <div><span>Continue clicked</span><strong>{campaign.stats.sends.whatsapp_template_clicked || 0}</strong></div>
                  <div><span>Msg after continue</span><strong>{campaign.stats.sends.whatsapp_after_continue || 0}</strong></div>
                  <div><span>Email sent</span><strong>{campaign.stats.sends.email || 0}</strong></div>
                </div>
              ) : null}

              <div className="nudge-campaign-card__actions">
                {(campaign.status === 'draft' || campaign.status === 'scheduled' || campaign.status === 'paused') && (
                  <button type="button" className="notif-search-btn" onClick={() => handleEdit(campaign)}>
                    Edit
                  </button>
                )}
                <button
                  type="button"
                  className="create-btn"
                  disabled={busyCampaignId === campaign.id}
                  onClick={() =>
                    campaign.status === 'draft' || campaign.status === 'scheduled'
                      ? handleAction(campaign.id, 'send-now', `Send campaign "${campaign.name}" to its audience now?`)
                      : campaign.status === 'paused'
                        ? handleAction(
                            campaign.id,
                            campaign.scheduled_at ? 'resume-scheduled' : 'resume-draft',
                            campaign.scheduled_at
                              ? `Resume scheduled campaign "${campaign.name}"?`
                              : `Resume paused campaign "${campaign.name}" as a draft?`
                          )
                        : handleAction(campaign.id, 'test-send')
                  }
                >
                  {busyCampaignId === campaign.id
                    ? 'Working...'
                    : campaign.status === 'paused'
                      ? (campaign.scheduled_at ? 'Resume schedule' : 'Resume draft')
                      : primaryActionLabel(campaign)}
                </button>
                {(campaign.status === 'draft' || campaign.status === 'scheduled') && (
                  <button
                    type="button"
                    className="notif-search-btn"
                    disabled={busyCampaignId === campaign.id}
                    onClick={() =>
                      handleAction(
                        campaign.id,
                        'pause',
                        `Pause campaign "${campaign.name}"? You can resume it later.`
                      )
                    }
                  >
                    Pause
                  </button>
                )}
                {(campaign.status === 'draft' || campaign.status === 'scheduled' || campaign.status === 'paused') && (
                  <button
                    type="button"
                    className="delete-btn"
                    disabled={busyCampaignId === campaign.id}
                    onClick={() =>
                      handleAction(
                        campaign.id,
                        'delete',
                        campaign.status === 'scheduled'
                          ? `Delete paused campaign "${campaign.name}"?`
                          : campaign.status === 'scheduled'
                            ? `Stop scheduled campaign "${campaign.name}" by deleting it?`
                            : `Delete draft campaign "${campaign.name}"?`
                      )
                    }
                  >
                    {campaign.status === 'paused'
                      ? 'Delete paused'
                      : campaign.status === 'scheduled'
                        ? 'Stop schedule'
                        : 'Delete draft'}
                  </button>
                )}
                <button
                  type="button"
                  className="notif-search-btn"
                  disabled={busyCampaignId === campaign.id}
                  onClick={() => handleAction(campaign.id, 'test-send')}
                >
                  Test to me
                </button>
              </div>
            </article>
          ))
        )}
      </div>

      {resultMsg ? <div className={`notif-result ${resultOk ? 'success' : 'error'}`}>{resultMsg}</div> : null}
    </div>
  );
}
