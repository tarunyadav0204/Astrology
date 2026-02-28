import React, { useEffect, useState } from 'react';

const AdminTerms = () => {
  const [terms, setTerms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);

  const [newTerm, setNewTerm] = useState({
    term_id: '',
    display_text: '',
    definition: '',
    language: 'english',
    aliases: '',
  });

  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({});

  const token = localStorage.getItem('token');

  const fetchTerms = async (pageToLoad = page, currentSearch = search) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(pageToLoad),
        limit: '50',
      });
      if (currentSearch.trim()) {
        params.append('search', currentSearch.trim());
      }
      const res = await fetch(`/api/admin/terms?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await res.json();
      setTerms(data.terms || []);
      setPage(data.pagination?.page || pageToLoad);
      setHasMore(!!data.pagination?.has_more);
      setTotal(data.pagination?.total || 0);
    } catch (e) {
      console.error('Error fetching glossary terms:', e);
      setTerms([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTerms(1, '');
  }, []);

  const handleCreate = async () => {
    if (!newTerm.term_id.trim() || !newTerm.display_text.trim() || !newTerm.definition.trim()) {
      alert('Please fill Term ID, Display Text and Definition.');
      return;
    }
    try {
      const body = {
        term_id: newTerm.term_id.trim(),
        display_text: newTerm.display_text.trim(),
        definition: newTerm.definition.trim(),
        language: newTerm.language.trim() || 'english',
        aliases: newTerm.aliases
          ? newTerm.aliases.split(',').map(a => a.trim()).filter(Boolean)
          : [],
      };
      const res = await fetch('/api/admin/terms', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Failed to save term');
        return;
      }
      setNewTerm({
        term_id: '',
        display_text: '',
        definition: '',
        language: 'english',
        aliases: '',
      });
      fetchTerms(1, search);
    } catch (e) {
      console.error('Error creating term:', e);
      alert('Error creating term');
    }
  };

  const startEdit = (term) => {
    setEditingId(term.term_id);
    setEditData({
      display_text: term.display_text,
      definition: term.definition,
      language: term.language || 'english',
      aliases: (term.aliases || []).join(', '),
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditData({});
  };

  const saveEdit = async (term_id) => {
    try {
      const body = {
        term_id,
        display_text: editData.display_text?.trim() || term_id,
        definition: editData.definition?.trim() || '',
        language: editData.language?.trim() || 'english',
        aliases: editData.aliases
          ? editData.aliases.split(',').map(a => a.trim()).filter(Boolean)
          : [],
      };
      if (!body.definition) {
        alert('Definition is required.');
        return;
      }
      const res = await fetch(`/api/admin/terms/${encodeURIComponent(term_id)}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Failed to update term');
        return;
      }
      cancelEdit();
      fetchTerms(page, search);
    } catch (e) {
      console.error('Error updating term:', e);
      alert('Error updating term');
    }
  };

  const deleteTerm = async (term_id) => {
    if (!window.confirm(`Delete term "${term_id}"?`)) return;
    try {
      const res = await fetch(`/api/admin/terms/${encodeURIComponent(term_id)}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Failed to delete term');
        return;
      }
      fetchTerms(page, search);
    } catch (e) {
      console.error('Error deleting term:', e);
      alert('Error deleting term');
    }
  };

  const handleSearch = () => {
    fetchTerms(1, search);
  };

  const nextPage = () => {
    if (hasMore) {
      const newPage = page + 1;
      fetchTerms(newPage, search);
    }
  };

  const prevPage = () => {
    if (page > 1) {
      const newPage = page - 1;
      fetchTerms(newPage, search);
    }
  };

  return (
    <div className="admin-terms">
      <h2>Glossary Terms</h2>

      <div className="terms-search">
        <input
          type="text"
          placeholder="Search by term id or display text..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button onClick={handleSearch}>Search</button>
      </div>

      <div className="terms-create">
        <h3>Create / Overwrite Term</h3>
        <div className="create-form">
          <div className="form-field">
            <label>Term ID (key)</label>
            <input
              type="text"
              value={newTerm.term_id}
              onChange={(e) => setNewTerm({ ...newTerm, term_id: e.target.value })}
              placeholder="e.g. rahu, shadbala"
            />
          </div>
          <div className="form-field">
            <label>Display Text</label>
            <input
              type="text"
              value={newTerm.display_text}
              onChange={(e) => setNewTerm({ ...newTerm, display_text: e.target.value })}
              placeholder="e.g. Rahu"
            />
          </div>
          <div className="form-field">
            <label>Language</label>
            <input
              type="text"
              value={newTerm.language}
              onChange={(e) => setNewTerm({ ...newTerm, language: e.target.value })}
              placeholder="english"
              style={{ width: '140px' }}
            />
          </div>
          <div className="form-field">
            <label>Aliases (comma separated)</label>
            <input
              type="text"
              value={newTerm.aliases}
              onChange={(e) => setNewTerm({ ...newTerm, aliases: e.target.value })}
              placeholder="e.g. North Node, Dragon's Head"
            />
          </div>
          <div className="form-field">
            <label>Definition</label>
            <textarea
              rows={3}
              value={newTerm.definition}
              onChange={(e) => setNewTerm({ ...newTerm, definition: e.target.value })}
              placeholder="Explain this term in your own words..."
            />
          </div>
          <div className="form-buttons">
            <button onClick={handleCreate} className="create-btn">
              Save Term
            </button>
          </div>
        </div>
      </div>

      <h3 style={{ marginTop: '24px' }}>
        Existing Terms {total ? `(${total})` : ''}
      </h3>

      {loading ? (
        <div className="loading">Loading terms...</div>
      ) : terms.length === 0 ? (
        <p>No terms found.</p>
      ) : (
        <div className="terms-table">
          <table>
            <thead>
              <tr>
                <th>Term ID</th>
                <th>Display Text</th>
                <th>Language</th>
                <th>Aliases</th>
                <th>Definition</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {terms.map((term) => (
                <tr key={term.term_id}>
                  <td><code>{term.term_id}</code></td>
                  <td>
                    {editingId === term.term_id ? (
                      <input
                        type="text"
                        value={editData.display_text}
                        onChange={(e) =>
                          setEditData({ ...editData, display_text: e.target.value })
                        }
                      />
                    ) : (
                      term.display_text
                    )}
                  </td>
                  <td>
                    {editingId === term.term_id ? (
                      <input
                        type="text"
                        style={{ width: '110px' }}
                        value={editData.language}
                        onChange={(e) =>
                          setEditData({ ...editData, language: e.target.value })
                        }
                      />
                    ) : (
                      term.language || 'english'
                    )}
                  </td>
                  <td>
                    {editingId === term.term_id ? (
                      <input
                        type="text"
                        value={editData.aliases}
                        onChange={(e) =>
                          setEditData({ ...editData, aliases: e.target.value })
                        }
                        placeholder="Comma separated"
                      />
                    ) : (
                      (term.aliases || []).join(', ')
                    )}
                  </td>
                  <td style={{ maxWidth: 400 }}>
                    {editingId === term.term_id ? (
                      <textarea
                        rows={3}
                        value={editData.definition}
                        onChange={(e) =>
                          setEditData({ ...editData, definition: e.target.value })
                        }
                      />
                    ) : (
                      term.definition
                    )}
                  </td>
                  <td>
                    {editingId === term.term_id ? (
                      <div>
                        <button
                          onClick={() => saveEdit(term.term_id)}
                          className="save-btn"
                        >
                          Save
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="cancel-btn"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div>
                        <button
                          onClick={() => startEdit(term)}
                          className="edit-btn"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => deleteTerm(term.term_id)}
                          className="delete-btn"
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="pagination" style={{ marginTop: '12px' }}>
            <button onClick={prevPage} disabled={page === 1}>
              Previous
            </button>
            <span style={{ margin: '0 8px' }}>Page {page}</span>
            <button onClick={nextPage} disabled={!hasMore}>
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminTerms;

