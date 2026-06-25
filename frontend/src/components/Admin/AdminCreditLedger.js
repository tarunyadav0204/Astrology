import React, { useState, useEffect, useLayoutEffect, useRef, useCallback, useMemo } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminCreditLedger.css';

const isoToday = () => new Date().toISOString().slice(0, 10);

const USER_LEDGER_LIMIT = 1500;
const ACTION_MENU_WIDTH = 260;

function computeActionMenuPosition(triggerRect) {
  const pad = 8;
  const w = Math.min(ACTION_MENU_WIDTH, window.innerWidth - 2 * pad);
  const left = Math.max(pad, Math.min(triggerRect.left, window.innerWidth - w - pad));
  const top = triggerRect.bottom + 4;
  return { top, left, width: w };
}

function isBuyTransaction(tx) {
  return tx?.type === 'earned' || tx?.type === 'refund';
}

const AdminCreditLedger = ({ onOpenUserProfile, ledgerJumpContext }) => {
  const [searchFromDate, setSearchFromDate] = useState('');
  const [searchToDate, setSearchToDate] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchSummary, setSearchSummary] = useState({
    purchased_credits: 0,
    user_spend_credits: 0,
    admin_added_credits: 0,
    admin_deducted_credits: 0,
    refund_reversal_credits: 0,
    free_questions_count: 0,
  });
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [searchRange, setSearchRange] = useState({ from_date: null, to_date: null });
  const [buyOnly, setBuyOnly] = useState(false);
  /** Server-side filter: hides free / zero-credit ledger rows (no extra rows fetched). */
  const [excludeZeroAmount, setExcludeZeroAmount] = useState(false);

  /** Row-specific ⋮ menu: which transaction row opened it (one dropdown at a time). */
  const [actionMenu, setActionMenu] = useState(null);
  /** Modal: filtered full-user ledger from admin API. */
  const [userBreakdown, setUserBreakdown] = useState(null);
  const menuContainerRef = useRef(null);
  const menuDropdownRef = useRef(null);
  const ledgerContentRef = useRef(null);

  const visibleSearchResults = useMemo(
    () => (buyOnly ? searchResults.filter(isBuyTransaction) : searchResults),
    [searchResults, buyOnly]
  );
  const loadTransactions = async (fromDate = '', toDate = '', query = '', excludeZero = excludeZeroAmount) => {
    setSearchLoading(true);
    setSearchError(null);
    try {
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);
      if (query.trim()) params.append('query', query.trim());
      if (excludeZero) params.append('exclude_zero_amount', 'true');
      const response = await fetch(`/api/credits/admin/search?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      if (!response.ok) throw new Error(`Search failed with status ${response.status}`);
      const data = await response.json();
      setSearchResults(data.transactions || []);
      setSearchSummary(data.summary || {
        purchased_credits: 0,
        user_spend_credits: 0,
        admin_added_credits: 0,
        admin_deducted_credits: 0,
        refund_reversal_credits: 0,
        free_questions_count: 0,
      });
      setSearchRange({ from_date: data.from_date || null, to_date: data.to_date || null });
    } catch (err) {
      console.error('Error loading transactions:', err);
      setSearchError('Failed to load transactions. Please try again.');
      setSearchResults([]);
      setSearchSummary({
        purchased_credits: 0,
        user_spend_credits: 0,
        admin_added_credits: 0,
        admin_deducted_credits: 0,
        refund_reversal_credits: 0,
        free_questions_count: 0,
      });
    } finally {
      setSearchLoading(false);
    }
  };

  const ledgerJumpNonce = ledgerJumpContext?.nonce;

  useEffect(() => {
    const today = isoToday();
    setSearchFromDate(today);
    setSearchToDate(today);
    const hasJump = ledgerJumpContext != null && ledgerJumpNonce != null;
    const q = hasJump ? String(ledgerJumpContext.query ?? '').trim() : '';
    setSearchQuery(q);
    loadTransactions(today, today, q, false);
  }, [ledgerJumpNonce]);

  const handleSearch = () => {
    loadTransactions(searchFromDate, searchToDate, searchQuery, excludeZeroAmount);
  };

  const closeActionMenu = useCallback(() => setActionMenu(null), []);

  useEffect(() => {
    if (!actionMenu) return undefined;
    const onPointerDown = (e) => {
      if (menuDropdownRef.current?.contains(e.target)) return;
      if (e.target.closest?.('.ledger-menu-trigger')) return;
      closeActionMenu();
    };
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [actionMenu, closeActionMenu]);

  useLayoutEffect(() => {
    if (!actionMenu?.anchorTxId) return undefined;
    const id = actionMenu.anchorTxId;
    let rafId = 0;
    const runMeasure = () => {
      const btn = document.querySelector(`[data-ledger-menu-tx="${id}"]`);
      if (!btn) return;
      const pos = computeActionMenuPosition(btn.getBoundingClientRect());
      setActionMenu((m) => {
        if (m?.anchorTxId !== id) return m;
        if (m.top === pos.top && m.left === pos.left && m.width === pos.width) return m;
        return { ...m, ...pos };
      });
    };
    const scheduleMeasure = () => {
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        rafId = 0;
        runMeasure();
      });
    };
    runMeasure();
    window.addEventListener('resize', scheduleMeasure);
    window.addEventListener('scroll', scheduleMeasure, true);
    const ledgerEl = ledgerContentRef.current;
    if (ledgerEl) ledgerEl.addEventListener('scroll', scheduleMeasure);
    return () => {
      if (rafId) cancelAnimationFrame(rafId);
      window.removeEventListener('resize', scheduleMeasure);
      window.removeEventListener('scroll', scheduleMeasure, true);
      if (ledgerEl) ledgerEl.removeEventListener('scroll', scheduleMeasure);
    };
  }, [actionMenu?.anchorTxId]);

  useEffect(() => {
    const anchorId = actionMenu?.anchorTxId;
    if (anchorId == null) return undefined;
    if (!visibleSearchResults.some((t) => t.id === anchorId)) closeActionMenu();
    return undefined;
  }, [actionMenu?.anchorTxId, visibleSearchResults, closeActionMenu]);

  useEffect(() => {
    if (!userBreakdown) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') setUserBreakdown(null);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [userBreakdown]);

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFeatureName = (source, referenceId) => {
    if (source === 'promo_code') return 'Promo Code';
    if (source === 'admin_adjustment') return 'Admin Adjustment';
    if (source === 'credit_request_approval') return 'Credit Request Approved';
    if (source === 'feature_usage') {
      const names = {
        chat_question: 'Chat Question',
        marriage_analysis: 'Marriage Analysis',
        wealth_analysis: 'Wealth Analysis',
        health_analysis: 'Health Analysis',
        education_analysis: 'Education Analysis',
        career_analysis: 'Career Analysis',
        progeny_analysis: 'Progeny Analysis',
        trading_daily: 'Trading Daily',
        trading_calendar: 'Trading Calendar',
        childbirth_planner: 'Childbirth Planner',
        vehicle_purchase: 'Vehicle Purchase Muhurat',
        griha_pravesh: 'Griha Pravesh',
        gold_purchase: 'Gold Purchase Muhurat',
        business_opening: 'Business Opening Muhurat',
        event_timeline: 'Event Timeline',
        partnership_analysis: 'Partnership Analysis',
        karma_analysis: 'Karma Analysis',
        mundane_chat: 'Mundane Chat',
      };
      return names[referenceId] || referenceId || 'Feature';
    }
    return source;
  };

  const openUserBreakdown = async (mode, tx) => {
    const uid = tx?.userid;
    if (uid == null) return;
    closeActionMenu();
    const label = `${tx.user_name || 'User'} · ${tx.user_phone || ''}`.trim();
    const title = mode === 'purchases' ? 'Purchases by user' : 'Spend by user';
    setUserBreakdown({
      mode,
      title,
      userLabel: label,
      userid: uid,
      rows: [],
      loading: true,
      error: null,
    });
    try {
      const params = new URLSearchParams({
        ledger_filter: mode === 'purchases' ? 'purchases' : 'spend',
        limit: String(USER_LEDGER_LIMIT),
      });
      if (excludeZeroAmount) params.append('exclude_zero_amount', 'true');
      const res = await fetch(`/api/credits/admin/user-history/${uid}?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || res.statusText || 'Request failed');
      }
      const data = await res.json();
      setUserBreakdown((prev) => ({
        ...prev,
        rows: data.transactions || [],
        loading: false,
        error: null,
      }));
    } catch (e) {
      setUserBreakdown((prev) => ({
        ...prev,
        rows: [],
        loading: false,
        error: e?.message || 'Failed to load',
      }));
    }
  };

  const openLedgerUserProfile = () => {
    const uid = menuContextTx?.userid;
    if (uid == null || typeof onOpenUserProfile !== 'function') return;
    closeActionMenu();
    onOpenUserProfile({
      userId: uid,
      dateFrom: searchFromDate,
      dateTo: searchToDate,
    });
  };

  const toggleRowMenu = (tx, e) => {
    e.stopPropagation();
    const id = tx?.id;
    const trigger = e.currentTarget;
    if (tx?.userid == null || id == null || !trigger) return;
    // Measure synchronously: React may run the setState updater after the event is recycled,
    // so e.currentTarget can be null inside the functional updater.
    const openRect = trigger.getBoundingClientRect();
    setActionMenu((prev) => {
      if (prev?.anchorTxId === id) return null;
      return {
        anchorTxId: id,
        userid: tx.userid,
        userName: tx.user_name,
        userPhone: tx.user_phone,
        ...computeActionMenuPosition(openRect),
      };
    });
  };

  const formatModalAmount = (row) => {
    const t = row?.type;
    const n = Number(row?.amount);
    if (t === 'earned' || t === 'refund') return n > 0 ? `+${n}` : String(n);
    return String(n);
  };

  const menuContextTx = useMemo(() => {
    const anchorId = actionMenu?.anchorTxId;
    if (anchorId == null) return null;
    return visibleSearchResults.find((t) => t.id === anchorId) ?? null;
  }, [actionMenu?.anchorTxId, visibleSearchResults]);

  return (
    <div className="admin-credit-ledger">
      <main className="ledger-main">
        <section className="search-bar">
          <div className="search-row">
            <label>
              <span className="label-text">From</span>
              <input
                type="date"
                value={searchFromDate}
                onChange={(e) => setSearchFromDate(e.target.value)}
              />
            </label>
            <label>
              <span className="label-text">To</span>
              <input
                type="date"
                value={searchToDate}
                onChange={(e) => setSearchToDate(e.target.value)}
              />
            </label>
            <label>
              <span className="label-text">Name / Phone</span>
              <input
                type="text"
                placeholder="Optional filter..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </label>
            <button className="search-btn" onClick={handleSearch} disabled={searchLoading}>
              {searchLoading ? 'Searching…' : 'Search'}
            </button>
          </div>
          <p className="search-hint">Default: today's records. Change dates and click Search for a custom range.</p>
          {searchError && <div className="search-error">{searchError}</div>}
        </section>

        <section className="ledger-content" ref={ledgerContentRef}>
          {searchLoading && (
            <div className="loading">Loading transactions…</div>
          )}
          {!searchLoading && (
            <div className="results-block">
              <h2 className="results-title">
                Transactions ({visibleSearchResults.length}{buyOnly ? ` of ${searchResults.length}` : ''})
                {searchRange.from_date && searchRange.to_date && (
                  <span className="results-range">
                    {' '}· {formatDate(searchRange.from_date)} – {formatDate(searchRange.to_date)}
                  </span>
                )}
                {searchQuery.trim() && (
                  <span className="results-filter"> · matching &quot;{searchQuery.trim()}&quot;</span>
                )}
              </h2>
              <div className="ledger-summary">
                <span className="ledger-summary-chip ledger-summary-chip--bought">
                  Purchased Credits: {searchSummary.purchased_credits}
                </span>
                <span className="ledger-summary-chip ledger-summary-chip--spent">
                  User Spend: {searchSummary.user_spend_credits}
                </span>
                <span className="ledger-summary-chip ledger-summary-chip--admin">
                  Admin Adjustments: +{searchSummary.admin_added_credits} / -{searchSummary.admin_deducted_credits}
                </span>
                <span className="ledger-summary-chip ledger-summary-chip--refund">
                  Refund / Reversals: {searchSummary.refund_reversal_credits}
                </span>
                <span className="ledger-summary-chip ledger-summary-chip--free">
                  Free Questions: {searchSummary.free_questions_count}
                </span>
                <label className="ledger-buy-only-toggle">
                  <input
                    type="checkbox"
                    checked={buyOnly}
                    onChange={(e) => setBuyOnly(e.target.checked)}
                  />
                  <span>Buy only transactions</span>
                </label>
                <label className="ledger-buy-only-toggle">
                  <input
                    type="checkbox"
                    checked={excludeZeroAmount}
                    onChange={(e) => {
                      const v = e.target.checked;
                      setExcludeZeroAmount(v);
                      loadTransactions(searchFromDate, searchToDate, searchQuery, v);
                    }}
                  />
                  <span>Hide zero-credit rows</span>
                </label>
              </div>
              {visibleSearchResults.length > 0 ? (
              <div className="transactions-table wrap" ref={menuContainerRef}>
                <table>
                  <thead>
                    <tr>
                      <th className="ledger-col-actions" aria-label="Actions" />
                      <th>Date</th>
                      <th>User</th>
                      <th>Phone</th>
                      <th>Type</th>
                      <th>Feature</th>
                      <th>Amount</th>
                      <th>Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleSearchResults.map((tx) => (
                      <tr key={tx.id} className={tx.type}>
                        <td className="ledger-actions-cell">
                          {tx.userid != null && tx.id != null ? (
                            <div className="ledger-menu-wrap">
                              <button
                                type="button"
                                className="ledger-menu-trigger"
                                data-ledger-menu-tx={tx.id}
                                aria-expanded={actionMenu?.anchorTxId === tx.id}
                                aria-haspopup="menu"
                                aria-label="User ledger actions"
                                onClick={(e) => toggleRowMenu(tx, e)}
                              >
                                <span className="ledger-menu-icon" aria-hidden>⋮</span>
                              </button>
                            </div>
                          ) : null}
                        </td>
                        <td className="date-cell">{formatDate(tx.created_at)}</td>
                        <td>{tx.user_name}</td>
                        <td>{tx.user_phone}</td>
                        <td className="type-cell">
                          <span className={`type-badge ${tx.type}`}>
                            {tx.type === 'earned' || tx.type === 'refund' ? '↑ Earned' : '↓ Spent'}
                          </span>
                        </td>
                        <td className="feature-cell">
                          {tx.description || getFeatureName(tx.source, tx.reference_id)}
                        </td>
                        <td className={`amount-cell ${tx.type}`}>
                          {tx.amount > 0 ? `+${tx.amount}` : tx.amount}
                        </td>
                        <td className="balance-cell">{tx.balance_after}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              ) : (
                <p className="no-results-msg">
                  {buyOnly
                    ? 'No buy transactions for this period. Turn off Buy only or adjust filters.'
                    : excludeZeroAmount
                      ? 'No non-zero credit transactions for this period. Turn off Hide zero-credit rows or adjust filters.'
                      : 'No transactions for this period. Adjust dates or name/phone and click Search.'}
                </p>
              )}
            </div>
          )}
        </section>
      </main>

      {actionMenu && menuContextTx ? (
        <ul
          ref={menuDropdownRef}
          className="ledger-action-menu ledger-action-menu--fixed"
          role="menu"
          style={{
            position: 'fixed',
            top: `${actionMenu.top}px`,
            left: `${actionMenu.left}px`,
            width: `${actionMenu.width}px`,
            zIndex: 1600,
          }}
        >
          <li role="none">
            <button
              type="button"
              role="menuitem"
              className="ledger-action-menu-item"
              onClick={() => openUserBreakdown('purchases', menuContextTx)}
            >
              Purchases by user
            </button>
          </li>
          <li role="none">
            <button
              type="button"
              role="menuitem"
              className="ledger-action-menu-item"
              onClick={() => openUserBreakdown('spend', menuContextTx)}
            >
              Spend by user
            </button>
          </li>
          {typeof onOpenUserProfile === 'function' ? (
            <li role="none">
              <button
                type="button"
                role="menuitem"
                className="ledger-action-menu-item"
                onClick={openLedgerUserProfile}
              >
                User profile
              </button>
            </li>
          ) : null}
        </ul>
      ) : null}

      {userBreakdown ? (
        <div
          className="ledger-user-modal-backdrop"
          role="presentation"
          onClick={() => setUserBreakdown(null)}
        >
          <div
            className="ledger-user-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="ledger-user-modal-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="ledger-user-modal-header">
              <h2 id="ledger-user-modal-title">{userBreakdown.title}</h2>
              <p className="ledger-user-modal-sub">{userBreakdown.userLabel}</p>
              <button type="button" className="ledger-user-modal-close" onClick={() => setUserBreakdown(null)}>
                Close
              </button>
            </div>
            {userBreakdown.loading ? (
              <div className="loading">Loading…</div>
            ) : userBreakdown.error ? (
              <div className="search-error">{userBreakdown.error}</div>
            ) : userBreakdown.rows.length === 0 ? (
              <p className="no-results-msg">No matching transactions for this user.</p>
            ) : (
              <div className="transactions-table wrap ledger-user-modal-table">
                <p className="ledger-user-modal-meta">
                  Showing {userBreakdown.rows.length} row{userBreakdown.rows.length === 1 ? '' : 's'}
                  {userBreakdown.mode === 'purchases' ? ' (credits in: earned + refund)' : ' (spent rows, including zero-credit usage if any)'}
                  {excludeZeroAmount ? ' · zero-credit rows hidden' : ''}
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Type</th>
                      <th>Feature</th>
                      <th>Amount</th>
                      <th>Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userBreakdown.rows.map((row) => (
                      <tr key={row.id} className={row.type}>
                        <td className="date-cell">{formatDate(row.date)}</td>
                        <td className="type-cell">
                          <span className={`type-badge ${row.type}`}>
                            {row.type === 'earned'
                              ? '↑ Earned'
                              : row.type === 'refund'
                                ? '↩ Refund'
                                : '↓ Spent'}
                          </span>
                        </td>
                        <td className="feature-cell">
                          {row.description || getFeatureName(row.source, row.reference_id)}
                        </td>
                        <td className={`amount-cell ${row.type}`}>{formatModalAmount(row)}</td>
                        <td className="balance-cell">{row.balance_after}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default AdminCreditLedger;
