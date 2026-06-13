import React, { useEffect, useRef, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

const FAQ_LIMIT = 25;

function resolveFaqPage(page, allRows, paginationMeta) {
  if (paginationMeta != null && paginationMeta.total != null) {
    const total = Number(paginationMeta.total) || 0;
    const totalPages = Math.max(
      Number(paginationMeta.total_pages) || 0,
      total > 0 ? Math.ceil(total / FAQ_LIMIT) : 0,
    );
    return { rows: allRows, total, totalPages };
  }

  // Legacy API returned the full FAQ list in one response.
  const total = allRows.length;
  const totalPages = total > 0 ? Math.ceil(total / FAQ_LIMIT) : 0;
  const start = (page - 1) * FAQ_LIMIT;
  return {
    rows: allRows.slice(start, start + FAQ_LIMIT),
    total,
    totalPages,
  };
}

export default function AdminChatAnalysis() {
  const [byCategory, setByCategory] = useState([]);
  const [byFaq, setByFaq] = useState([]);
  const [faqPage, setFaqPage] = useState(1);
  const [faqTotal, setFaqTotal] = useState(0);
  const [faqTotalPages, setFaqTotalPages] = useState(0);
  const [initialLoading, setInitialLoading] = useState(true);
  const [faqLoading, setFaqLoading] = useState(false);
  const [error, setError] = useState(null);
  const initialLoadDone = useRef(false);

  useEffect(() => {
    let cancelled = false;

    async function load(page) {
      setError(null);
      if (!initialLoadDone.current) {
        setInitialLoading(true);
      } else {
        setFaqLoading(true);
      }

      try {
        const params = new URLSearchParams({
          faq_page: String(page),
          faq_limit: String(FAQ_LIMIT),
        });
        const res = await fetch(`/api/admin/chat/analysis-stats?${params}`, {
          headers: getAdminAuthHeaders(),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || res.statusText || 'Failed to load');
        }
        const data = await res.json();
        if (cancelled) return;

        setByCategory(data.by_category || []);
        const { rows, total, totalPages } = resolveFaqPage(
          page,
          data.by_faq || [],
          data.faq_pagination,
        );
        setByFaq(rows);
        setFaqTotal(total);
        setFaqTotalPages(totalPages);
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load chat analysis');
        }
      } finally {
        if (!cancelled) {
          initialLoadDone.current = true;
          setInitialLoading(false);
          setFaqLoading(false);
        }
      }
    }

    load(faqPage);
    return () => {
      cancelled = true;
    };
  }, [faqPage]);

  const faqRangeStart = faqTotal === 0 ? 0 : (faqPage - 1) * FAQ_LIMIT + 1;
  const faqRangeEnd = Math.min(faqPage * FAQ_LIMIT, faqTotal);
  const showFaqPagination = faqTotal > FAQ_LIMIT;

  if (initialLoading) return <div className="admin-chat-analysis-loading">Loading chat analysis…</div>;
  if (error) return <div className="admin-chat-analysis-error">{error}</div>;

  return (
    <div className="admin-chat-analysis">
      <h2>Chat analysis</h2>

      <div className="admin-chat-analysis-section">
        <h3>By category</h3>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Count</th>
            </tr>
          </thead>
          <tbody>
            {byCategory.length === 0 ? (
              <tr><td colSpan={2}>No categorized questions yet.</td></tr>
            ) : (
              byCategory.map((row) => (
                <tr key={row.category}>
                  <td>{row.category}</td>
                  <td>{row.count}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="admin-chat-analysis-section">
        <h3>By FAQ (frequently asked)</h3>
        {faqLoading ? (
          <div className="admin-chat-analysis-loading">Loading FAQ page…</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Canonical question</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              {byFaq.length === 0 ? (
                <tr><td colSpan={2}>No FAQ data yet.</td></tr>
              ) : (
                byFaq.map((row, i) => (
                  <tr key={`${row.canonical_question || 'row'}-${i}`}>
                    <td>{row.canonical_question}</td>
                    <td>{row.count}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}

        {showFaqPagination && (
          <div className="admin-chat-analysis-pagination">
            <span className="admin-chat-analysis-pagination-info">
              Showing {faqRangeStart}–{faqRangeEnd} of {faqTotal}
            </span>
            <button
              type="button"
              className="admin-chat-analysis-pagination-btn"
              disabled={faqPage <= 1 || faqLoading}
              onClick={() => setFaqPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <span className="admin-chat-analysis-pagination-page">
              Page {faqPage} of {faqTotalPages}
            </span>
            <button
              type="button"
              className="admin-chat-analysis-pagination-btn"
              disabled={faqPage >= faqTotalPages || faqLoading}
              onClick={() => setFaqPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
