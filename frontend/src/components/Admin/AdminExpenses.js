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

function todayInIST() {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date());
  const get = (type) => parts.find((part) => part.type === type)?.value;
  return `${get('year')}-${get('month')}-${get('day')}`;
}

const AdminExpenses = () => {
  const [expenseView, setExpenseView] = useState('log');

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState({ count: 0, totals_by_currency: [] });
  const [page, setPage] = useState(1);
  const [limit] = useState(50);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [categoryApplied, setCategoryApplied] = useState('');
  const [vendorFilter, setVendorFilter] = useState('');
  const [paidByFilter, setPaidByFilter] = useState('');
  const [exporting, setExporting] = useState(false);

  const [vendors, setVendors] = useState([]);
  const [paidByList, setPaidByList] = useState([]);
  const [mastersLoading, setMastersLoading] = useState(false);
  const [newVendorLabel, setNewVendorLabel] = useState('');
  const [newPaidByLabel, setNewPaidByLabel] = useState('');

  const [spentDate, setSpentDate] = useState(todayInIST);
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('INR');
  const [vendorId, setVendorId] = useState('');
  const [paidById, setPaidById] = useState('');
  const [category, setCategory] = useState('');
  const [notes, setNotes] = useState('');
  const [invoiceFile, setInvoiceFile] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editingHasInvoice, setEditingHasInvoice] = useState(false);
  const [removeInvoice, setRemoveInvoice] = useState(false);
  const [saving, setSaving] = useState(false);

  const loadMasters = useCallback(async (includeInactive) => {
    setMastersLoading(true);
    try {
      const [v, p] = await Promise.all([
        adminService.getExpenseMasterVendors({ include_inactive: includeInactive }),
        adminService.getExpenseMasterPaidBy({ include_inactive: includeInactive }),
      ]);
      setVendors(v.items || []);
      setPaidByList(p.items || []);
    } catch (e) {
      console.error(e);
      setVendors([]);
      setPaidByList([]);
    } finally {
      setMastersLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMasters(true);
  }, [expenseView, loadMasters]);

  const load = useCallback(async (pageOverride) => {
    setLoading(true);
    setError('');
    try {
      const params = { page: pageOverride || page, limit };
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (categoryApplied.trim()) params.category = categoryApplied.trim();
      if (vendorFilter) params.vendor_id = vendorFilter;
      if (paidByFilter) params.paid_by_id = paidByFilter;
      const data = await adminService.getAdminExpenses(params);
      setItems(data.items || []);
      setTotal(Number(data.total) || 0);
      setSummary(data.summary || { count: Number(data.total) || 0, totals_by_currency: [] });
    } catch (e) {
      setError(e?.message || 'Failed to load');
      setItems([]);
      setTotal(0);
      setSummary({ count: 0, totals_by_currency: [] });
    } finally {
      setLoading(false);
    }
  }, [page, limit, dateFrom, dateTo, categoryApplied, vendorFilter, paidByFilter]);

  useEffect(() => {
    if (expenseView === 'log') {
      load();
    }
  }, [load, expenseView]);

  const activeVendors = vendors.filter((x) => x.is_active);
  const activePaidBy = paidByList.filter((x) => x.is_active);
  const selectedInactiveVendor = editingId
    ? vendors.find((x) => !x.is_active && String(x.id) === String(vendorId))
    : null;
  const selectedInactivePaidBy = editingId
    ? paidByList.find((x) => !x.is_active && String(x.id) === String(paidById))
    : null;

  const totalPages = Math.max(1, Math.ceil(total / limit));

  const resetExpenseForm = () => {
    setEditingId(null);
    setEditingHasInvoice(false);
    setRemoveInvoice(false);
    setSpentDate(todayInIST());
    setAmount('');
    setCurrency('INR');
    setVendorId('');
    setPaidById('');
    setCategory('');
    setNotes('');
    setInvoiceFile(null);
    const el = document.getElementById('admin-expense-invoice-input');
    if (el) el.value = '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!vendorId || !paidById) {
      setError('Select vendor and paid by (add them under “Vendors & paid by” if empty).');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('spent_date', spentDate);
      fd.append('amount', amount.trim());
      fd.append('currency', currency);
      fd.append('vendor_id', String(vendorId));
      fd.append('paid_by_id', String(paidById));
      fd.append('category', category.trim());
      fd.append('notes', notes.trim());
      fd.append('remove_invoice', removeInvoice ? 'true' : 'false');
      if (invoiceFile) fd.append('invoice', invoiceFile);
      if (editingId) {
        await adminService.updateAdminExpense(editingId, fd);
      } else {
        await adminService.createAdminExpense(fd);
      }
      resetExpenseForm();
      setPage(1);
      await loadMasters(true);
      await load(1);
    } catch (err) {
      setError(err?.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (row) => {
    setEditingId(row.id);
    setEditingHasInvoice(Boolean(row.has_invoice));
    setRemoveInvoice(false);
    setSpentDate(row.spent_date || todayInIST());
    setAmount(String(row.amount || ''));
    setCurrency(row.currency || 'INR');
    setVendorId(row.vendor_id ? String(row.vendor_id) : '');
    setPaidById(row.paid_by_id ? String(row.paid_by_id) : '');
    setCategory(row.category || '');
    setNotes(row.notes || '');
    setInvoiceFile(null);
    const input = document.getElementById('admin-expense-invoice-input');
    if (input) input.value = '';
    window.setTimeout(() => {
      document.getElementById('admin-expense-entry-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 0);
  };

  const handleExport = async () => {
    setExporting(true);
    setError('');
    try {
      await adminService.exportAdminExpenses({
        date_from: dateFrom,
        date_to: dateTo,
        category: categoryApplied.trim(),
        vendor_id: vendorFilter,
        paid_by_id: paidByFilter,
      });
    } catch (e) {
      setError(e?.message || 'Export failed');
    } finally {
      setExporting(false);
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

  const addVendor = async () => {
    const label = newVendorLabel.trim();
    if (!label) return;
    try {
      await adminService.createExpenseMasterVendor({ label, sort_order: 0 });
      setNewVendorLabel('');
      await loadMasters(true);
    } catch (e) {
      alert(e?.message || 'Failed to add vendor');
    }
  };

  const addPaidBy = async () => {
    const label = newPaidByLabel.trim();
    if (!label) return;
    try {
      await adminService.createExpenseMasterPaidBy({ label, sort_order: 0 });
      setNewPaidByLabel('');
      await loadMasters(true);
    } catch (e) {
      alert(e?.message || 'Failed to add paid-by');
    }
  };

  const toggleVendorActive = async (row) => {
    try {
      await adminService.patchExpenseMasterVendor(row.id, { is_active: !row.is_active });
      await loadMasters(true);
    } catch (e) {
      alert(e?.message || 'Update failed');
    }
  };

  const togglePaidByActive = async (row) => {
    try {
      await adminService.patchExpenseMasterPaidBy(row.id, { is_active: !row.is_active });
      await loadMasters(true);
    } catch (e) {
      alert(e?.message || 'Update failed');
    }
  };

  const deleteVendorRow = async (row) => {
    if (!window.confirm(`Delete vendor “${row.label}”? (Only if no expenses use it.)`)) return;
    try {
      await adminService.deleteExpenseMasterVendor(row.id);
      await loadMasters(expenseView === 'masters');
    } catch (e) {
      alert(e?.message || 'Delete failed');
    }
  };

  const deletePaidByRow = async (row) => {
    if (!window.confirm(`Delete paid-by “${row.label}”? (Only if no expenses use it.)`)) return;
    try {
      await adminService.deleteExpenseMasterPaidBy(row.id);
      await loadMasters(expenseView === 'masters');
    } catch (e) {
      alert(e?.message || 'Delete failed');
    }
  };

  return (
    <div className="users-management">
      <h2 style={{ marginBottom: 8 }}>Internal expenses</h2>

      <div className="admin-subtabs" style={{ marginBottom: 16 }}>
        <button
          type="button"
          className={`subtab ${expenseView === 'log' ? 'active' : ''}`}
          onClick={() => setExpenseView('log')}
        >
          Expense log
        </button>
        <button
          type="button"
          className={`subtab ${expenseView === 'masters' ? 'active' : ''}`}
          onClick={() => setExpenseView('masters')}
        >
          Vendors &amp; paid by
        </button>
      </div>

      {expenseView === 'masters' && (
        <div style={{ marginBottom: 24 }}>
          <p style={{ color: '#555', fontSize: 14, marginBottom: 16 }}>
            Add vendors (who you paid) and paid-by options (card, bank account, UPI, etc.). They appear as dropdowns
            when you record an expense.
          </p>
          {mastersLoading ? (
            <div className="loading">Loading lists…</div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: 24,
                alignItems: 'start',
              }}
            >
              <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 14 }}>
                <h3 style={{ marginTop: 0, fontSize: 16 }}>Vendors</h3>
                <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
                  <input
                    type="text"
                    placeholder="New vendor name"
                    value={newVendorLabel}
                    onChange={(e) => setNewVendorLabel(e.target.value)}
                    style={{ flex: 1, minWidth: 140, padding: 8, borderRadius: 4, border: '1px solid #ddd' }}
                  />
                  <button type="button" className="users-search-btn" onClick={addVendor}>
                    Add
                  </button>
                </div>
                <div className="users-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Active</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {vendors.length === 0 ? (
                        <tr>
                          <td colSpan={3} className="users-table-empty">
                            No vendors yet.
                          </td>
                        </tr>
                      ) : (
                        vendors.map((row) => (
                          <tr key={row.id}>
                            <td>{row.label}</td>
                            <td>
                              <input
                                type="checkbox"
                                checked={row.is_active}
                                onChange={() => toggleVendorActive(row)}
                                aria-label={`Active ${row.label}`}
                              />
                            </td>
                            <td>
                              <button
                                type="button"
                                className="users-pagination-btn"
                                style={{ padding: '4px 10px', fontSize: 12, background: '#666' }}
                                onClick={() => deleteVendorRow(row)}
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
              </div>

              <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 14 }}>
                <h3 style={{ marginTop: 0, fontSize: 16 }}>Paid by</h3>
                <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
                  <input
                    type="text"
                    placeholder="e.g. Company HDFC · Personal card"
                    value={newPaidByLabel}
                    onChange={(e) => setNewPaidByLabel(e.target.value)}
                    style={{ flex: 1, minWidth: 140, padding: 8, borderRadius: 4, border: '1px solid #ddd' }}
                  />
                  <button type="button" className="users-search-btn" onClick={addPaidBy}>
                    Add
                  </button>
                </div>
                <div className="users-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Active</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {paidByList.length === 0 ? (
                        <tr>
                          <td colSpan={3} className="users-table-empty">
                            No paid-by entries yet.
                          </td>
                        </tr>
                      ) : (
                        paidByList.map((row) => (
                          <tr key={row.id}>
                            <td>{row.label}</td>
                            <td>
                              <input
                                type="checkbox"
                                checked={row.is_active}
                                onChange={() => togglePaidByActive(row)}
                                aria-label={`Active ${row.label}`}
                              />
                            </td>
                            <td>
                              <button
                                type="button"
                                className="users-pagination-btn"
                                style={{ padding: '4px 10px', fontSize: 12, background: '#666' }}
                                onClick={() => deletePaidByRow(row)}
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
              </div>
            </div>
          )}
        </div>
      )}

      {expenseView === 'log' && (
        <>
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
            <label>
              <span>Vendor</span>
              <select
                value={vendorFilter}
                onChange={(e) => {
                  setPage(1);
                  setVendorFilter(e.target.value);
                }}
              >
                <option value="">All vendors</option>
                {vendors.map((vendor) => (
                  <option key={vendor.id} value={String(vendor.id)}>
                    {vendor.label}{vendor.is_active ? '' : ' (inactive)'}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Paid by</span>
              <select
                value={paidByFilter}
                onChange={(e) => {
                  setPage(1);
                  setPaidByFilter(e.target.value);
                }}
              >
                <option value="">All paid-by entries</option>
                {paidByList.map((payer) => (
                  <option key={payer.id} value={String(payer.id)}>
                    {payer.label}{payer.is_active ? '' : ' (inactive)'}
                  </option>
                ))}
              </select>
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
            <button
              type="button"
              className="users-search-btn"
              onClick={handleExport}
              disabled={exporting}
              style={{ background: '#217346' }}
            >
              {exporting ? 'Exporting…' : 'Export to Excel'}
            </button>
          </div>

          <form
            id="admin-expense-entry-form"
            onSubmit={handleSubmit}
            style={{
              border: '1px solid #e5e7eb',
              borderRadius: 8,
              padding: 16,
              marginBottom: 24,
              background: '#fafafa',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: 12,
                marginBottom: 12,
              }}
            >
              <h3 style={{ margin: 0, fontSize: 16 }}>
                {editingId ? `Edit expense #${editingId}` : 'Add expense'}
              </h3>
              {editingId ? (
                <button
                  type="button"
                  className="users-pagination-btn"
                  onClick={resetExpenseForm}
                  disabled={saving}
                >
                  Cancel edit
                </button>
              ) : null}
            </div>
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
                <select
                  value={vendorId}
                  onChange={(e) => setVendorId(e.target.value)}
                  required
                  style={{ minWidth: 160 }}
                >
                  <option value="">Select vendor…</option>
                  {selectedInactiveVendor ? (
                    <option value={String(selectedInactiveVendor.id)}>
                      {selectedInactiveVendor.label} (inactive)
                    </option>
                  ) : null}
                  {activeVendors.map((v) => (
                    <option key={v.id} value={String(v.id)}>
                      {v.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>Paid by</span>
                <select
                  value={paidById}
                  onChange={(e) => setPaidById(e.target.value)}
                  required
                  style={{ minWidth: 160 }}
                >
                  <option value="">Select paid by…</option>
                  {selectedInactivePaidBy ? (
                    <option value={String(selectedInactivePaidBy.id)}>
                      {selectedInactivePaidBy.label} (inactive)
                    </option>
                  ) : null}
                  {activePaidBy.map((p) => (
                    <option key={p.id} value={String(p.id)}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>Category</span>
                <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. hosting" />
              </label>
            </div>
            {(activeVendors.length === 0 || activePaidBy.length === 0) && (
              <p style={{ color: '#b45309', fontSize: 13, marginBottom: 8 }}>
                Add at least one active vendor and one active paid-by entry under <strong>Vendors &amp; paid by</strong>{' '}
                before saving expenses.
              </p>
            )}
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: '#555' }}>Notes</span>
              <textarea
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                style={{ padding: 8, borderRadius: 4, border: '1px solid #ddd', maxWidth: '100%' }}
              />
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: '#555' }}>Invoice (optional)</span>
              <input
                id="admin-expense-invoice-input"
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*"
                onChange={(e) => setInvoiceFile(e.target.files?.[0] || null)}
              />
              {editingId && editingHasInvoice ? (
                <span style={{ fontSize: 12, color: '#555' }}>
                  A new file will replace the current invoice.
                  <label style={{ display: 'inline-flex', flexDirection: 'row', gap: 6, marginLeft: 12 }}>
                    <input
                      type="checkbox"
                      checked={removeInvoice}
                      disabled={Boolean(invoiceFile)}
                      onChange={(e) => setRemoveInvoice(e.target.checked)}
                    />
                    Remove current invoice
                  </label>
                </span>
              ) : null}
            </div>
            <button type="submit" className="users-search-btn" disabled={saving}>
              {saving ? 'Saving…' : editingId ? 'Update expense' : 'Save expense'}
            </button>
          </form>

          {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}

          {loading ? (
            <div className="loading">Loading…</div>
          ) : (
            <>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 12,
                  marginBottom: 16,
                }}
              >
                <div
                  style={{
                    minWidth: 170,
                    border: '1px solid #e5e7eb',
                    borderRadius: 8,
                    padding: '12px 14px',
                    background: '#fff',
                  }}
                >
                  <div style={{ color: '#666', fontSize: 12 }}>Filtered expenses</div>
                  <div style={{ fontSize: 22, fontWeight: 700 }}>{summary.count || 0}</div>
                </div>
                {(summary.totals_by_currency || []).map((entry) => (
                  <div
                    key={entry.currency}
                    style={{
                      minWidth: 170,
                      border: '1px solid #e5e7eb',
                      borderRadius: 8,
                      padding: '12px 14px',
                      background: '#fff',
                    }}
                  >
                    <div style={{ color: '#666', fontSize: 12 }}>
                      Filtered total · {entry.currency}
                    </div>
                    <div style={{ fontSize: 22, fontWeight: 700 }}>
                      {formatInr(entry.amount, entry.currency)}
                    </div>
                    <div style={{ color: '#888', fontSize: 12 }}>{entry.count} entries</div>
                  </div>
                ))}
              </div>
              <div className="users-table">
                <table>
                  <thead>
                    <tr>
                      <th>Spent date</th>
                      <th>Vendor</th>
                      <th>Paid by</th>
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
                        <td colSpan={9} className="users-table-empty">
                          No expenses yet.
                        </td>
                      </tr>
                    ) : (
                      items.map((row) => (
                        <tr key={row.id}>
                          <td>{row.spent_date || '—'}</td>
                          <td>{row.vendor || '—'}</td>
                          <td>{row.paid_by || '—'}</td>
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
                          <td style={{ fontSize: 12 }}>
                            {row.created_at ? new Date(row.created_at).toLocaleString('en-IN') : '—'}
                          </td>
                          <td>
                            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                              <button
                                type="button"
                                className="users-pagination-btn"
                                style={{ padding: '4px 10px', fontSize: 12 }}
                                onClick={() => startEdit(row)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="users-pagination-btn"
                                style={{ padding: '4px 10px', fontSize: 12, background: '#666' }}
                                onClick={() => handleDelete(row.id)}
                              >
                                Delete
                              </button>
                            </div>
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
        </>
      )}
    </div>
  );
};

export default AdminExpenses;
