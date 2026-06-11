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

const emptyForm = {
  name: '',
  title_template: '',
  body_template: '',
  question_template: '',
  channel_policy: 'waterfall',
  channels: ['push', 'whatsapp', 'email'],
  ai_personalize: false,
  ai_base_prompt: '',
  audience_type: 'all',
  audience_days: 7,
  audience_user_ids: '',
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
  const [preview, setPreview] = useState(null);
  const [previewUserId, setPreviewUserId] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [busyCampaignId, setBusyCampaignId] = useState(null);

  const setField = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));
  const showResult = (ok, msg) => {
    setResultOk(ok);
    setResultMsg(msg);
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
    return {
      name: form.name.trim(),
      title_template: form.title_template.trim(),
      body_template: form.body_template.trim(),
      question_template: form.question_template.trim(),
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
      setForm(emptyForm);
      setEditingId(null);
      setPreview(null);
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

  const handleEdit = (c) => {
    const audience = c.audience_filter || { type: 'all' };
    setEditingId(c.id);
    setPreview(null);
    setForm({
      name: c.name || '',
      title_template: c.title_template || '',
      body_template: c.body_template || '',
      question_template: c.question_template || '',
      channel_policy: c.channel_policy || 'waterfall',
      channels: (c.channels || []).length ? c.channels : ['push'],
      ai_personalize: !!c.ai_personalize,
      ai_base_prompt: c.ai_base_prompt || '',
      audience_type: audience.type || 'all',
      audience_days: audience.days || 7,
      audience_user_ids: (audience.user_ids || []).join(', '),
      landing_screen: c.landing_screen || 'chat',
      scheduled_at: c.scheduled_at ? c.scheduled_at.slice(0, 16) : '',
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
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
        const body = await apiFetch(`/api/nudge/admin/campaigns/${campaignId}/send-now`, { method: 'POST' });
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
        const ch = body.delivery?.channel || 'stored';
        showResult(true, `Test sent to you via "${ch}". Title: ${body.copy?.title || ''}`);
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

  const toggleChannel = (ch) => {
    setForm((prev) => {
      const has = prev.channels.includes(ch);
      return {
        ...prev,
        channels: has ? prev.channels.filter((c) => c !== ch) : [...prev.channels, ch],
      };
    });
  };

  const moveChannel = (ch, dir) => {
    setForm((prev) => {
      const idx = prev.channels.indexOf(ch);
      const next = idx + dir;
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
      sending: 'Sending…',
      sent: 'Sent',
      cancelled: 'Cancelled',
    }),
    []
  );

  if (loading) {
    return <p className="notifications-description">Loading campaigns…</p>;
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
      <p className="notifications-description">
        Multi-channel campaigns: message is framed per user from dynamic parameters and delivered via
        push, WhatsApp and email — waterfall (first reachable channel) or blast (all channels).
      </p>

      <div className="notifications-form nudge-scheduler-form">
        <h4 style={{ margin: '0 0 8px' }}>{editingId ? `Edit campaign #${editingId}` : 'New campaign'}</h4>
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
            placeholder="e.g. It's been {days_since_last_chat} days since we talked about {last_question_topic}…"
            value={form.body_template}
            onChange={(e) => setField('body_template', e.target.value)}
          />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
            {placeholders.map((p) => (
              <button
                key={p}
                type="button"
                className="notif-search-btn"
                style={{ padding: '2px 8px', fontSize: 12 }}
                onClick={() => insertPlaceholder(p)}
              >
                {'{' + p + '}'}
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

        <div className="nudge-scheduler-row">
          <div className="form-field">
            <label>Channel policy</label>
            <select value={form.channel_policy} onChange={(e) => setField('channel_policy', e.target.value)}>
              <option value="waterfall">Waterfall — stop at first successful channel</option>
              <option value="blast">Blast — send on every selected channel</option>
            </select>
          </div>
          <div className="form-field">
            <label>Landing screen</label>
            <select value={form.landing_screen} onChange={(e) => setField('landing_screen', e.target.value)}>
              {LANDING_OPTIONS.map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-field">
          <label>Channels (order matters for waterfall)</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {form.channels.map((ch, idx) => (
              <div key={ch} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ width: 110 }}>{idx + 1}. {ch}</span>
                <button type="button" className="notif-search-btn" style={{ padding: '0 8px' }} onClick={() => moveChannel(ch, -1)}>↑</button>
                <button type="button" className="notif-search-btn" style={{ padding: '0 8px' }} onClick={() => moveChannel(ch, 1)}>↓</button>
                <button type="button" className="delete-btn" style={{ padding: '0 8px' }} onClick={() => toggleChannel(ch)}>remove</button>
              </div>
            ))}
            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              {CHANNEL_OPTIONS.filter((c) => !form.channels.includes(c)).map((c) => (
                <button key={c} type="button" className="notif-search-btn" onClick={() => toggleChannel(c)}>
                  + {c}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="form-field">
          <label className="notif-inline-checkbox">
            <input
              type="checkbox"
              checked={form.ai_personalize}
              onChange={(e) => setField('ai_personalize', e.target.checked)}
            />
            <span>AI-personalize per user (Gemini frames title/body/question from the base prompt + user parameters)</span>
          </label>
          {form.ai_personalize && (
            <textarea
              rows={3}
              maxLength={2000}
              placeholder="Base prompt for Gemini, e.g. 'Nudge users to ask about career timing during their current dasha…'"
              value={form.ai_base_prompt}
              onChange={(e) => setField('ai_base_prompt', e.target.value)}
            />
          )}
        </div>

        <div className="nudge-scheduler-row">
          <div className="form-field">
            <label>Audience</label>
            <select value={form.audience_type} onChange={(e) => setField('audience_type', e.target.value)}>
              {AUDIENCE_OPTIONS.map((a) => (
                <option key={a.value} value={a.value}>{a.label}</option>
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

        <div className="nudge-scheduler-row">
          <div className="form-field">
            <label>Schedule (leave empty to keep as draft)</label>
            <input
              type="datetime-local"
              value={form.scheduled_at}
              onChange={(e) => setField('scheduled_at', e.target.value)}
            />
          </div>
          <div className="form-field">
            <label>Preview as user ID (optional)</label>
            <input
              type="number"
              placeholder="defaults to you"
              value={previewUserId}
              onChange={(e) => setPreviewUserId(e.target.value)}
            />
          </div>
        </div>

        <div className="form-buttons">
          <button type="button" className="create-btn" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : editingId ? 'Update campaign' : form.scheduled_at ? 'Save & schedule' : 'Save draft'}
          </button>
          <button type="button" className="notif-search-btn" onClick={handlePreview} disabled={previewing}>
            {previewing ? 'Rendering…' : 'Preview against sample user'}
          </button>
          {editingId && (
            <button
              type="button"
              className="notif-search-btn"
              onClick={() => {
                setEditingId(null);
                setForm(emptyForm);
                setPreview(null);
              }}
            >
              Cancel edit
            </button>
          )}
        </div>

        {preview && (
          <div className="notif-result success" style={{ marginTop: 10 }}>
            <div><strong>Preview for user #{preview.user_id}</strong></div>
            <div><strong>Title:</strong> {preview.rendered?.title}</div>
            <div><strong>Body:</strong> {preview.rendered?.body}</div>
            {preview.rendered?.question ? (
              <div><strong>Question:</strong> {preview.rendered.question}</div>
            ) : null}
            <details style={{ marginTop: 6 }}>
              <summary>Resolved parameters</summary>
              <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>{JSON.stringify(preview.params, null, 2)}</pre>
            </details>
          </div>
        )}
      </div>

      <div className="notif-user-list nudge-scheduler-list">
        <table className="notif-user-table">
          <thead>
            <tr>
              <th style={{ width: 50 }}>ID</th>
              <th>Campaign</th>
              <th style={{ width: 130 }}>Channels</th>
              <th style={{ width: 90 }}>Policy</th>
              <th style={{ width: 150 }}>Scheduled</th>
              <th style={{ width: 90 }}>Status</th>
              <th style={{ width: 90 }}>Targeted</th>
              <th style={{ width: 230 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {campaigns.length === 0 ? (
              <tr>
                <td colSpan={8} className="notif-td-name">No campaigns yet.</td>
              </tr>
            ) : (
              campaigns.map((c) => (
                <tr key={c.id}>
                  <td>{c.id}</td>
                  <td>
                    <strong>{c.name}</strong>
                    <div className="notif-td-phone">{c.title_template}</div>
                    {c.ai_personalize ? <div className="notif-td-phone">AI personalized</div> : null}
                  </td>
                  <td>{(c.channels || []).join(' → ')}</td>
                  <td>{c.channel_policy}</td>
                  <td>{c.scheduled_at ? new Date(c.scheduled_at).toLocaleString() : '—'}</td>
                  <td>{statusLabel[c.status] || c.status}</td>
                  <td>{c.total_targeted || 0}</td>
                  <td>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {(c.status === 'draft' || c.status === 'scheduled') && (
                        <>
                          <button type="button" className="notif-search-btn" style={{ padding: '2px 8px' }} onClick={() => handleEdit(c)}>
                            Edit
                          </button>
                          <button
                            type="button"
                            className="create-btn"
                            style={{ padding: '2px 8px' }}
                            disabled={busyCampaignId === c.id}
                            onClick={() => handleAction(c.id, 'send-now', `Send campaign "${c.name}" to its audience now?`)}
                          >
                            Send now
                          </button>
                          <button
                            type="button"
                            className="delete-btn"
                            style={{ padding: '2px 8px' }}
                            disabled={busyCampaignId === c.id}
                            onClick={() => handleAction(c.id, 'delete', `Delete campaign "${c.name}"?`)}
                          >
                            Delete
                          </button>
                        </>
                      )}
                      <button
                        type="button"
                        className="notif-search-btn"
                        style={{ padding: '2px 8px' }}
                        disabled={busyCampaignId === c.id}
                        onClick={() => handleAction(c.id, 'test-send')}
                      >
                        Test → me
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {resultMsg && (
        <div className={`notif-result ${resultOk ? 'success' : 'error'}`}>
          {resultMsg}
        </div>
      )}
    </div>
  );
}
