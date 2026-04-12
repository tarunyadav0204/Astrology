import React, { useCallback, useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

const PLANETS = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn'];

const TRIGGER_LABELS = {
  natal_planet_return: 'Natal degree return',
  natal_whole_sign_return: 'Natal whole-sign return',
};

/**
 * Admin: edit automated daily nudge copy and parameters (natal return triggers).
 * Backed by GET/PUT /api/nudge/admin/trigger-definitions.
 */
export default function AdminNudgeTriggerDefinitions() {
  const [triggers, setTriggers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [saving, setSaving] = useState({});
  const [saveMsg, setSaveMsg] = useState({});
  const [priorityStr, setPriorityStr] = useState({});

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const res = await fetch('/api/nudge/admin/trigger-definitions', {
        headers: getAdminAuthHeaders(),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || res.statusText || 'Failed to load');
      }
      const list = body.triggers || [];
      setTriggers(list);
      const ps = {};
      list.forEach((t) => {
        ps[t.trigger_key] = String(t.priority ?? '');
      });
      setPriorityStr(ps);
    } catch (e) {
      setErr(e.message || 'Failed to load');
      setTriggers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const updateTrigger = (key, partial) => {
    setTriggers((prev) =>
      prev.map((t) => (t.trigger_key === key ? { ...t, ...partial } : t))
    );
  };

  const updateConfig = (key, cfgPartial) => {
    setTriggers((prev) =>
      prev.map((t) =>
        t.trigger_key === key ? { ...t, config: { ...t.config, ...cfgPartial } } : t
      )
    );
  };

  const togglePlanet = (key, planet) => {
    const t = triggers.find((x) => x.trigger_key === key);
    if (!t) return;
    const cur = new Set(t.config?.planets || []);
    if (cur.has(planet)) {
      cur.delete(planet);
    } else {
      cur.add(planet);
    }
    updateConfig(key, { planets: Array.from(cur) });
  };

  const save = async (key) => {
    const t = triggers.find((x) => x.trigger_key === key);
    if (!t) return;
    const plist = t.config?.planets || [];
    if (plist.length < 1) {
      setSaveMsg((m) => ({
        ...m,
        [key]: 'Select at least one planet.',
      }));
      return;
    }
    const pRaw = (priorityStr[key] ?? '').trim();
    let priority = null;
    if (pRaw !== '') {
      const n = Number(pRaw);
      if (Number.isNaN(n) || n < 0 || n > 200) {
        setSaveMsg((m) => ({
          ...m,
          [key]: 'Priority must be empty (for default) or a number from 0 to 200.',
        }));
        return;
      }
      priority = n;
    }

    setSaving((s) => ({ ...s, [key]: true }));
    setSaveMsg((m) => ({ ...m, [key]: null }));
    try {
      const res = await fetch(
        `/api/nudge/admin/trigger-definitions/${encodeURIComponent(key)}`,
        {
          method: 'PUT',
          headers: {
            ...getAdminAuthHeaders(),
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            enabled: Boolean(t.enabled),
            priority,
            title_template: t.title_template,
            body_template: t.body_template,
            question_template: t.question_template || '',
            config: t.config || {},
          }),
        }
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          typeof body.detail === 'string'
            ? body.detail
            : Array.isArray(body.detail)
              ? body.detail.map((x) => x.msg || x).join('; ')
              : 'Save failed'
        );
      }
      setSaveMsg((m) => ({ ...m, [key]: 'Saved successfully.' }));
      await load();
    } catch (e) {
      setSaveMsg((m) => ({ ...m, [key]: e.message || 'Error' }));
    } finally {
      setSaving((s) => ({ ...s, [key]: false }));
    }
  };

  if (loading) {
    return (
      <p className="notifications-description nudge-def-status">Loading trigger definitions…</p>
    );
  }
  if (err) {
    return (
      <div className="notif-result error nudge-def-status">
        <strong>Could not load definitions.</strong> {err}
        <button type="button" className="notif-search-btn" style={{ marginLeft: 12 }} onClick={load}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="nudge-trigger-definitions">
      <p className="notifications-description">
        Configure copy and timing parameters for personalized daily nudges (natal planetary returns).
        Placeholders in templates must match the allowed set for each trigger. Leave priority empty to
        use each trigger&apos;s built-in default (shown on the field).
      </p>

      {triggers.map((t) => {
        const key = t.trigger_key;
        const label = TRIGGER_LABELS[key] || key;
        const isPlanetReturn = key === 'natal_planet_return';
        return (
          <div key={key} className="nudge-def-card">
            <div className="nudge-def-card-header">
              <h3>{label}</h3>
              <code className="nudge-def-key">{key}</code>
            </div>

            <div className="notifications-form">
              <div className="form-field nudge-def-row">
                <label>
                  <input
                    type="checkbox"
                    checked={Boolean(t.enabled)}
                    onChange={(e) => updateTrigger(key, { enabled: e.target.checked })}
                  />
                  <span style={{ marginLeft: 8 }}>Enabled</span>
                </label>
              </div>

              <div className="form-field">
                <label>
                  Priority (0–200, empty = default {t.default_priority})
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder={`Default: ${t.default_priority}`}
                  value={priorityStr[key] ?? ''}
                  onChange={(e) =>
                    setPriorityStr((prev) => ({ ...prev, [key]: e.target.value }))
                  }
                  className="nudge-def-priority-input"
                />
              </div>

              <div className="form-field">
                <label>Allowed placeholders</label>
                <div className="nudge-def-chips">
                  {(t.allowed_placeholders || []).map((p) => (
                    <span key={p} className="nudge-def-chip">
                      {`{${p}}`}
                    </span>
                  ))}
                </div>
              </div>

              <div className="form-field">
                <label>Title template (max 200)</label>
                <input
                  type="text"
                  maxLength={200}
                  value={t.title_template}
                  onChange={(e) => updateTrigger(key, { title_template: e.target.value })}
                />
              </div>

              <div className="form-field">
                <label>Body template (max 600)</label>
                <textarea
                  rows={4}
                  maxLength={600}
                  value={t.body_template}
                  onChange={(e) => updateTrigger(key, { body_template: e.target.value })}
                />
              </div>

              <div className="form-field">
                <label>Question template (max 900, optional)</label>
                <textarea
                  rows={4}
                  maxLength={900}
                  value={t.question_template || ''}
                  onChange={(e) => updateTrigger(key, { question_template: e.target.value })}
                />
              </div>

              <div className="form-field">
                <label>Parameters</label>
                <div className="nudge-def-config-grid">
                  {isPlanetReturn && (
                    <div className="nudge-def-config-item">
                      <span className="nudge-def-config-label">Orb (degrees)</span>
                      <input
                        type="number"
                        step="0.05"
                        min={0.25}
                        max={5}
                        value={t.config?.orb_deg ?? ''}
                        onChange={(e) =>
                          updateConfig(key, {
                            orb_deg: e.target.value === '' ? 1 : Number(e.target.value),
                          })
                        }
                      />
                      <small className="form-hint">{t.config_schema?.orb_deg}</small>
                    </div>
                  )}
                  <div className="nudge-def-config-item">
                    <span className="nudge-def-config-label">Advance notice (days)</span>
                    <input
                      type="number"
                      min={1}
                      max={90}
                      value={t.config?.advance_notice_days ?? ''}
                      onChange={(e) =>
                        updateConfig(key, {
                          advance_notice_days:
                            e.target.value === '' ? 30 : Number(e.target.value),
                        })
                      }
                    />
                    <small className="form-hint">{t.config_schema?.advance_notice_days}</small>
                  </div>
                  <div className="nudge-def-config-item">
                    <span className="nudge-def-config-label">Horizon (days)</span>
                    <input
                      type="number"
                      min={30}
                      max={2500}
                      value={t.config?.horizon_days ?? ''}
                      onChange={(e) =>
                        updateConfig(key, {
                          horizon_days: e.target.value === '' ? 800 : Number(e.target.value),
                        })
                      }
                    />
                    <small className="form-hint">{t.config_schema?.horizon_days}</small>
                  </div>
                </div>
                <div className="nudge-def-planets">
                  <span className="nudge-def-config-label">Planets</span>
                  <div className="nudge-def-planet-grid">
                    {PLANETS.map((planet) => (
                      <label key={planet} className="nudge-def-planet-label">
                        <input
                          type="checkbox"
                          checked={(t.config?.planets || []).includes(planet)}
                          onChange={() => togglePlanet(key, planet)}
                        />
                        <span>{planet}</span>
                      </label>
                    ))}
                  </div>
                  <small className="form-hint">{t.config_schema?.planets}</small>
                </div>
              </div>

              <div className="form-buttons">
                <button
                  type="button"
                  className="create-btn"
                  disabled={saving[key]}
                  onClick={() => save(key)}
                >
                  {saving[key] ? 'Saving…' : 'Save changes'}
                </button>
              </div>
                {saveMsg[key] && (
                <div
                  className={`notif-result ${
                    /success/i.test(saveMsg[key]) ? 'success' : 'error'
                  }`}
                  style={{ marginTop: 8 }}
                >
                  {saveMsg[key]}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
