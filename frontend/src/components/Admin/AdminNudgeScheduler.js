import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

const todayIso = () => new Date().toISOString().slice(0, 10);
const defaultTimes = ['07:00', '13:00', '17:00', '20:00'];

export default function AdminNudgeScheduler() {
  const [templates, setTemplates] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [resultMsg, setResultMsg] = useState('');
  const [resultOk, setResultOk] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dispatching, setDispatching] = useState(false);
  const [creatingTemplate, setCreatingTemplate] = useState(false);

  const [templateId, setTemplateId] = useState('');
  const [sendDate, setSendDate] = useState(todayIso());
  const [sendTime, setSendTime] = useState('07:00');
  const [rangeStart, setRangeStart] = useState(todayIso());
  const [rangeEnd, setRangeEnd] = useState('');
  const [newTitle, setNewTitle] = useState('');
  const [newBody, setNewBody] = useState('');
  const [newCategory, setNewCategory] = useState('general');

  const selectedTemplate = useMemo(
    () => templates.find((t) => String(t.id) === String(templateId)),
    [templates, templateId]
  );

  const showResult = (ok, msg) => {
    setResultOk(ok);
    setResultMsg(msg);
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const templateRes = await fetch('/api/nudge/admin/broadcast/templates', {
        headers: getAdminAuthHeaders(),
      });
      const templateBody = await templateRes.json().catch(() => ({}));
      if (!templateRes.ok) {
        throw new Error(templateBody.detail || 'Failed to load nudge templates');
      }
      const templateList = templateBody.templates || [];
      setTemplates(templateList);
      if (!templateId && templateList.length > 0) {
        setTemplateId(String(templateList[0].id));
      }

      const params = new URLSearchParams();
      if (rangeStart) params.set('start_date', rangeStart);
      if (rangeEnd) params.set('end_date', rangeEnd);
      const scheduleRes = await fetch(`/api/nudge/admin/broadcast/schedule?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      const scheduleBody = await scheduleRes.json().catch(() => ({}));
      if (!scheduleRes.ok) {
        throw new Error(scheduleBody.detail || 'Failed to load schedule');
      }
      setItems(scheduleBody.items || []);
    } catch (e) {
      setError(e.message || 'Failed to load nudge schedule');
      setTemplates([]);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [rangeStart, rangeEnd, templateId]);

  useEffect(() => {
    load();
  }, [load]);

  const createOne = async (payload) => {
    const res = await fetch('/api/nudge/admin/broadcast/schedule', {
      method: 'POST',
      headers: {
        ...getAdminAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(body.detail || 'Failed to save schedule item');
  };

  const createTemplate = async (payload) => {
    const res = await fetch('/api/nudge/admin/broadcast/templates', {
      method: 'POST',
      headers: {
        ...getAdminAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(body.detail || 'Failed to create nudge template');
    return body;
  };

  const handleAddOne = async () => {
    if (!templateId || !sendDate || !sendTime) {
      showResult(false, 'Please select a nudge, date and time.');
      return;
    }
    setSaving(true);
    showResult(true, '');
    try {
      await createOne({
        template_id: Number(templateId),
        send_date: sendDate,
        send_time: sendTime,
        is_active: true,
      });
      showResult(true, 'Scheduled successfully.');
      await load();
    } catch (e) {
      showResult(false, e.message || 'Failed to create schedule');
    } finally {
      setSaving(false);
    }
  };

  const handleAddDaySlots = async () => {
    if (!templateId || !sendDate) {
      showResult(false, 'Please select a nudge and date first.');
      return;
    }
    setSaving(true);
    showResult(true, '');
    try {
      for (const t of defaultTimes) {
        await createOne({
          template_id: Number(templateId),
          send_date: sendDate,
          send_time: t,
          is_active: true,
        });
      }
      showResult(true, 'Added 4 daily slots for selected date.');
      await load();
    } catch (e) {
      showResult(false, e.message || 'Failed to add daily slots');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this scheduled nudge?')) return;
    try {
      const res = await fetch(`/api/nudge/admin/broadcast/schedule/${id}`, {
        method: 'DELETE',
        headers: getAdminAuthHeaders(),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || 'Delete failed');
      }
      showResult(true, 'Deleted schedule item.');
      await load();
    } catch (e) {
      showResult(false, e.message || 'Delete failed');
    }
  };

  const handleDispatchDueNow = async () => {
    setDispatching(true);
    showResult(true, '');
    try {
      const res = await fetch('/api/nudge/admin/broadcast/dispatch-due?limit=200', {
        method: 'POST',
        headers: getAdminAuthHeaders(),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || 'Dispatch failed');
      }
      showResult(
        true,
        `Dispatch run complete. Due: ${body.due_items || 0}, Users targeted: ${body.users_targeted || 0}, Push sent: ${body.push_sent || 0}.`
      );
      await load();
    } catch (e) {
      showResult(false, e.message || 'Dispatch failed');
    } finally {
      setDispatching(false);
    }
  };

  const handleCreateTemplate = async () => {
    const title = newTitle.trim();
    const body = newBody.trim();
    const category = (newCategory || 'general').trim();
    if (!title || !body) {
      showResult(false, 'Please enter title and description for new nudge.');
      return;
    }
    setCreatingTemplate(true);
    showResult(true, '');
    try {
      const created = await createTemplate({
        title,
        body,
        category,
        is_active: true,
      });
      setNewTitle('');
      setNewBody('');
      setNewCategory('general');
      await load();
      if (created?.id) {
        setTemplateId(String(created.id));
      }
      showResult(true, 'New nudge template created.');
    } catch (e) {
      showResult(false, e.message || 'Template creation failed');
    } finally {
      setCreatingTemplate(false);
    }
  };

  if (loading) {
    return <p className="notifications-description">Loading nudge planner…</p>;
  }
  if (error) {
    return (
      <div className="notif-result error">
        <strong>Could not load nudge planner.</strong> {error}
      </div>
    );
  }

  return (
    <div className="nudge-scheduler-admin">
      <p className="notifications-description">
        Plan which nudge goes out on which date and time. The system is pre-seeded on first run with 50 nudges and
        a rolling schedule of 4 nudges/day at 07:00, 13:00, 17:00 and 20:00.
      </p>

      <div className="notifications-form nudge-scheduler-form">
        <div className="form-field">
          <label>Create new nudge — Title (max 200)</label>
          <input
            type="text"
            maxLength={200}
            placeholder="Nudge title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
          />
        </div>
        <div className="form-field">
          <label>Create new nudge — Description (max 600)</label>
          <textarea
            rows={3}
            maxLength={600}
            placeholder="Nudge description/body"
            value={newBody}
            onChange={(e) => setNewBody(e.target.value)}
          />
        </div>
        <div className="nudge-scheduler-row">
          <div className="form-field">
            <label>Category</label>
            <input
              type="text"
              maxLength={80}
              placeholder="e.g. wealth_prosperity"
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value)}
            />
          </div>
          <div className="form-buttons" style={{ alignItems: 'end' }}>
            <button
              type="button"
              className="create-btn"
              onClick={handleCreateTemplate}
              disabled={creatingTemplate}
            >
              {creatingTemplate ? 'Creating…' : 'Add new nudge'}
            </button>
          </div>
        </div>
      </div>

      <div className="notifications-form nudge-scheduler-form">
        <div className="form-field">
          <label>Nudge</label>
          <select value={templateId} onChange={(e) => setTemplateId(e.target.value)}>
            <option value="">Select nudge…</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.title}
              </option>
            ))}
          </select>
          {selectedTemplate && (
            <small className="form-hint">
              {selectedTemplate.body}
            </small>
          )}
        </div>
        <div className="nudge-scheduler-row">
          <div className="form-field">
            <label>Date</label>
            <input type="date" value={sendDate} onChange={(e) => setSendDate(e.target.value)} />
          </div>
          <div className="form-field">
            <label>Time</label>
            <input type="time" value={sendTime} onChange={(e) => setSendTime(e.target.value)} />
          </div>
        </div>
        <div className="form-buttons">
          <button type="button" className="create-btn" onClick={handleAddOne} disabled={saving || !templateId}>
            {saving ? 'Saving…' : 'Schedule nudge'}
          </button>
          <button type="button" className="notif-search-btn" onClick={handleAddDaySlots} disabled={saving || !templateId}>
            Add 4 slots (07/13/17/20)
          </button>
        </div>
      </div>

      <div className="nudge-scheduler-filter">
        <div className="form-field">
          <label>From</label>
          <input type="date" value={rangeStart} onChange={(e) => setRangeStart(e.target.value)} />
        </div>
        <div className="form-field">
          <label>To</label>
          <input type="date" value={rangeEnd} onChange={(e) => setRangeEnd(e.target.value)} />
        </div>
        <button type="button" className="notif-search-btn" onClick={load}>
          Refresh
        </button>
        <button
          type="button"
          className="create-btn"
          onClick={handleDispatchDueNow}
          disabled={dispatching}
        >
          {dispatching ? 'Dispatching…' : 'Dispatch due now'}
        </button>
      </div>

      <div className="notif-user-list nudge-scheduler-list">
        <table className="notif-user-table">
          <thead>
            <tr>
              <th style={{ width: 130 }}>Date</th>
              <th style={{ width: 80 }}>Time</th>
              <th>Nudge</th>
              <th style={{ width: 120 }}>Category</th>
              <th style={{ width: 110 }}>Status</th>
              <th style={{ width: 80 }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={6} className="notif-td-name">No scheduled nudges in this range.</td>
              </tr>
            ) : (
              items.map((it) => (
                <tr key={it.id}>
                  <td>{it.send_date}</td>
                  <td>{it.send_time}</td>
                  <td>
                    <strong>{it.title}</strong>
                    <div className="notif-td-phone">{it.body}</div>
                  </td>
                  <td>{it.category}</td>
                  <td>{it.dispatched_at ? 'Dispatched' : 'Pending'}</td>
                  <td>
                    <button type="button" className="delete-btn" onClick={() => handleDelete(it.id)}>
                      Delete
                    </button>
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
