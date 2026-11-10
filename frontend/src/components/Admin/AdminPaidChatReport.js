import React, { useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminPaidChatReport.css';

const todayIso = () => new Date().toISOString().slice(0, 10);
const monthStartIso = () => `${todayIso().slice(0, 8)}01`;
const number = (value) => Number(value || 0).toLocaleString('en-IN');

const SORT_LABELS = {
  username: 'Username',
  chat_type: 'Chat type',
  questions: '# of questions',
  credits_charged: 'Credits charged',
};

export default function AdminPaidChatReport() {
  const [startDate, setStartDate] = useState(monthStartIso);
  const [endDate, setEndDate] = useState(todayIso);
  const [username, setUsername] = useState('');
  const [chatType, setChatType] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sort, setSort] = useState({ key: 'credits_charged', direction: 'desc' });

  const load = async () => {
    if (startDate && endDate && startDate > endDate) {
      setError('Start date must be on or before end date.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (startDate) params.set('start_date', startDate);
      if (endDate) params.set('end_date', endDate);
      if (username.trim()) params.set('username', username.trim());
      if (chatType) params.set('chat_type', chatType);
      const response = await fetch(`/api/admin/chat/paid-answers-report?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || 'Could not load paid chat report.');
      setData(payload);
    } catch (requestError) {
      setError(requestError.message || 'Could not load paid chat report.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []); // Initial default month load only.

  const userRows = useMemo(() => {
    const rows = Array.isArray(data?.by_user) ? [...data.by_user] : [];
    const factor = sort.direction === 'asc' ? 1 : -1;
    return rows.sort((left, right) => {
      const a = left[sort.key];
      const b = right[sort.key];
      if (typeof a === 'number' || typeof b === 'number') return (Number(a) - Number(b)) * factor;
      return String(a || '').localeCompare(String(b || ''), 'en', { sensitivity: 'base' }) * factor;
    });
  }, [data, sort]);

  const toggleSort = (key) => setSort((previous) => ({
    key,
    direction: previous.key === key && previous.direction === 'desc' ? 'asc' : 'desc',
  }));

  const sortButton = (key) => (
    <button type="button" className="paid-chat-report__sort" onClick={() => toggleSort(key)}>
      {SORT_LABELS[key]} {sort.key === key ? (sort.direction === 'asc' ? '↑' : '↓') : ''}
    </button>
  );

  return (
    <section className="paid-chat-report">
      <header className="paid-chat-report__header">
        <div>
          <h2>Paid chat report</h2>
          <p>Charged, completed answers only. Instant and Talk To Tara are counted as billed sessions because they are time-metered.</p>
        </div>
      </header>

      <form className="paid-chat-report__filters" onSubmit={(event) => { event.preventDefault(); load(); }}>
        <label><span>Start</span><input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
        <label><span>End</span><input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} /></label>
        <label className="paid-chat-report__username"><span>Username</span><input type="search" value={username} placeholder="Name, phone, or user ID" onChange={(event) => setUsername(event.target.value)} /></label>
        <label><span>Chat type</span>
          <select value={chatType} onChange={(event) => setChatType(event.target.value)}>
            <option value="">All chat types</option>
            <option value="standard">Standard</option>
            <option value="premium">Premium</option>
            <option value="verified">Verified</option>
            <option value="instant">Instant</option>
            <option value="speech">Speech</option>
          </select>
        </label>
        <button type="submit" disabled={loading}>{loading ? 'Loading…' : 'Apply filters'}</button>
      </form>

      {error ? <p className="paid-chat-report__error">{error}</p> : null}

      <div className="paid-chat-report__summary">
        <div><span>Paid users</span><strong>{number(data?.summary?.users)}</strong></div>
        <div><span>Questions / sessions</span><strong>{number(data?.summary?.questions)}</strong></div>
        <div><span>Credits charged</span><strong>{number(data?.summary?.credits_charged)}</strong></div>
      </div>

      <div className="paid-chat-report__grid">
        <section className="paid-chat-report__panel">
          <h3>By chat type</h3>
          <div className="paid-chat-report__table-wrap">
            <table>
              <thead><tr><th>Chat type</th><th># of questions</th><th>Credits charged</th></tr></thead>
              <tbody>{(data?.by_type || []).map((row) => (
                <tr key={row.chat_type}><td>{row.chat_type}{row.metered_sessions ? <small>{row.metered_sessions} metered session{row.metered_sessions === 1 ? '' : 's'}</small> : null}</td><td>{number(row.questions)}</td><td>{number(row.credits_charged)}</td></tr>
              ))}</tbody>
            </table>
            {!loading && !(data?.by_type || []).length ? <p className="paid-chat-report__empty">No charged answers match these filters.</p> : null}
          </div>
        </section>

        <section className="paid-chat-report__panel paid-chat-report__panel--wide">
          <h3>By user</h3>
          <div className="paid-chat-report__table-wrap">
            <table>
              <thead><tr><th>{sortButton('username')}</th><th>{sortButton('chat_type')}</th><th>{sortButton('questions')}</th><th>{sortButton('credits_charged')}</th></tr></thead>
              <tbody>{userRows.map((row) => (
                <tr key={`${row.user_id}-${row.chat_type}`}><td>{row.username}<small>User #{row.user_id}</small></td><td>{row.chat_type}{row.metered_sessions ? <small>{row.metered_sessions} metered session{row.metered_sessions === 1 ? '' : 's'}</small> : null}</td><td>{number(row.questions)}</td><td>{number(row.credits_charged)}</td></tr>
              ))}</tbody>
            </table>
            {!loading && !userRows.length ? <p className="paid-chat-report__empty">No users match these filters.</p> : null}
          </div>
        </section>
      </div>
    </section>
  );
}
