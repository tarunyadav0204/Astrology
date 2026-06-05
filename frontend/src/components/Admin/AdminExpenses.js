import React, { useCallback, useEffect, useState } from 'react';
import { adminService, getDeviceId } from '../../services/adminService';

function formatInr(amountStr, currency) {
  const n = Number(amountStr);
  if (Number.isNaN(n)) return amountStr;
  const cur = (currency || 'INR').toUpperCase();
  try {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: cur, maximumFractionDigits: 2 }).format(n);
  } catch (_) {
    return `${cur} ${n.toFixed(2)}`;
  }
}

const AdminExpenses = () => {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(50);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [categoryApplied, setCategoryApplied] = useState('');

  const [spentDate, setSpentDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('INR');
  const [vendor, setVendor] = useState('');
  const [category, setCategory] = useState('');
  const [notes, setNotes] = useState('');
  const [invoiceFile, setInvoiceFile] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = { page, limit };
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (categoryApplied.trim()) params.category = categoryApplied.trim();
      const data = await adminService.getAdminExpenses(params);
      setItems(data.items || []);
      setTotal(Number(data.total) || 0);
    } catch (e) {
      setError(e?.message || 'Failed to load');
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, limit, dateFrom, dateTo, categoryApplied]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('spent_date', spentDate);
      fd.append('amount', amount.trim());
      fd.append('currency', currency);
      fd.append('vendor', vendor.trim());
      fd.append('category', category.trim());
      fd.append('notes', notes.trim());
      if (invoiceFile) fd.append('invoice', invoiceFile);
      await adminService.createAdminExpense(fd);
      setAmount('');
      setVendor('');
      setCategory('');
      setNotes('');
      setInvoiceFile(null);
      const el = document.getElementById('admin-expense-invoice-input');
      if (el) el.value = '';
      setPage(1);
      await load();
    } catch (err) {
      setError(err?.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const downloadInvoice = async (id, filename) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(adminService.getAdminExpenseInvoiceUrl(id), {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Device-Id': getDeviceId(),
        },
      });
      if (!res.ok) {
        const t = await res.text().catch(() => '');
        throw new Error(t || 'Download failed');
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `invoice-${id}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(e?.message || 'Download failed');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this expense and its invoice file (if any)?')) return;
    try {
      await adminService.deleteAdminExpense(id);
      await load();
    } catch (e) {
      alert(e?.message || 'Delete failed');
    }
  };

  return (
    <div className="users-management">
      <h2 style={{ marginBottom: 8 }}>Internal expenses</h2>
      <p style={{ color: '#555', marginBottom: 16, fontSize: 14 }}>
        Internal expense log. Invoices are stored in{' '}
        <strong>Google Cloud Storage</strong> (private objects): set env{' '}
        <code>EXPENSE_INVOICE_GCS_BUCKET</code> and the same <code>GOOGLE_SERVICE_ACCOUNT_KEY</code> as blog uploads.
        For local-only testing without a bucket, set <code>EXPENSE_INVOICE_ALLOW_LOCAL=1</code> (writes under{' '}
        <code>storage/admin_expense_invoices</code> — not for production).
      </p>

      <div className="users-management-filters" style={{ marginBottom: 20 }}>
        <label>
          <span>Spent from</span>
          <input type="date" value={dateFrom} onChange={(e) => { setPage(1); setDateFrom(e.target.value); }} />
        </label>
        <label>
          <span>Spent to</span>
          <input type="date" value={dateTo} onChange={(e) => { setPage(1); setDateTo(e.target.value); }} />
        </label>
        <label>
          <span>Category contains</span>
          <input
            type="text"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            placeholder="e.g. infra"
          />
        </label>
        <button
          type="button"
          className="users-search-btn"
          onClick={() => {
            setCategoryApplied(categoryFilter.trim());
            setPage(1);
          }}
        >
          Refresh
        </button>
      </div>

      <form
        onSubmit={handleSubmit}
        style={{
          border: '1px solid #e5e7eb',
          borderRadius: 8,
          padding: 16,
          marginBottom: 24,
          background: '#fafafa',
        }}
      >
        <h3 style={{ marginTop: 0, marginBottom: 12, fontSize: 16 }}>Add expense</h3>
        <div className="users-management-filters">
          <label>
            <span>Spent date</span>
            <input type="date" value={spentDate} onChange={(e) => setSpentDate(e.target.value)} required />
          </label>
          <label>
            <span>Amount</span>
            <input
              type="text"
              inputMode="decimal"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="e.g. 2499.50"
              required
            />
          </label>
          <label>
            <span>Currency</span>
            <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
              <option value="INR">INR</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
            </select>
          </label>
          <label>
            <span>Vendor</span>
            <input type="text" value={vendor} onChange={(e) => setVendor(e.target.value)} placeholder="Who you paid" required />
          </label>
          <label>
            <span>Category</span>
            <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. hosting" />
          </label>
        </div>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: '#555' }}>Notes</span>
          <textarea
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            style={{ padding: 8, borderRadius: 4, border: '1px solid #ddd', maxWidth: '100%' }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: '#555' }}>Invoice (optional)</span>
          <input
            id="admin-expense-invoice-input"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*"
            onChange={(e) => setInvoiceFile(e.target.files?.[0] || null)}
          />
        </label>
        <button type="submit" className="users-search-btn" disabled={saving}>
          {saving ? 'Saving…' : 'Save expense'}
        </button>
      </form>

      {error ? <p style={{ color: '#c2185b' }}>{error}</p> : null}

      {loading ? (
        <div className="loading">Loading…</div>
      ) : (
        <>
          <div className="users-table">
            <table>
              <thead>
                <tr>
                  <th>Spent date</th>
                  <th>Vendor</th>
                  <th>Category</th>
                  <th>Amount</th>
                  <th>Notes (preview)</th>
                  <th>Invoice</th>
                  <th>Created</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="users-table-empty">
                      No expenses yet.
                    </td>
                  </tr>
                ) : (
                  items.map((row) => (
                    <tr key={row.id}>
                      <td>{row.spent_date || '—'}</td>
                      <td>{row.vendor}</td>
                      <td>{row.category || '—'}</td>
                      <td>{formatInr(row.amount, row.currency)}</td>
                      <td style={{ maxWidth: 200, wordBreak: 'break-word' }}>{row.notes_preview || '—'}</td>
                      <td>
                        {row.has_invoice ? (
                          <button
                            type="button"
                            className="users-pagination-btn"
                            style={{ padding: '4px 10px', fontSize: 12 }}
                            onClick={() => downloadInvoice(row.id, row.invoice_original_name)}
                          >
                            Download
                          </button>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td style={{ fontSize: 12 }}>{row.created_at ? new Date(row.created_at).toLocaleString('en-IN') : '—'}</td>
                      <td>
                        <button
                          type="button"
                          className="users-pagination-btn"
                          style={{ padding: '4px 10px', fontSize: 12, background: '#666' }}
                          onClick={() => handleDelete(row.id)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 16, flexWrap: 'wrap' }}>
            <span className="users-pagination-info">
              Page {page} of {totalPages} · {total} total
            </span>
            <button type="button" className="users-pagination-btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <button
              type="button"
              className="users-pagination-btn"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default AdminExpenses;
