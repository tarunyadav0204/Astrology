import React, { useState } from 'react';
import NavigationHeader from '../Shared/NavigationHeader';
import { APP_CONFIG } from '../../config/app.config';

const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? APP_CONFIG.api.prod
  : APP_CONFIG.api.dev;

const getEndpoint = (path) => {
  if (API_BASE_URL.includes('localhost')) {
    return `${API_BASE_URL}/api${path}`;
  }
  return `/api${path}`;
};

const DeleteAccountPage = ({ user, onLogin, onLogout }) => {
  const [confirmChecked, setConfirmChecked] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleted, setDeleted] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  const handleDeleteAccount = async () => {
    if (!confirmChecked || deleting) return;
    const sure = window.confirm(
      'This will permanently delete your account and associated data. This action cannot be undone.\n\nAre you sure you want to continue?'
    );
    if (!sure) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(getEndpoint('/user/account'), {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Failed to delete account. Please try again.');
      }
      setDeleted(true);
      if (onLogout) onLogout();
    } catch (e) {
      setDeleteError(e.message || 'Failed to delete account. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 50%, #dee2e6 100%)',
      fontFamily: 'Arial, sans-serif'
    }}>
      <NavigationHeader />
      <div style={{ padding: '220px 20px 60px 20px', maxWidth: '720px', margin: '0 auto' }}>
        <h1 style={{ color: '#e91e63', marginBottom: '8px' }}>AstroRoshni – Request data deletion</h1>
        <p style={{ color: '#666', marginBottom: '32px' }}>
          You can delete some of your data (e.g. past questions and answers) without deleting your account, or request full account and data deletion. Use the steps below.
        </p>

        {/* Section: Self-serve account deletion (same API as the mobile app) */}
        <section style={{
          marginBottom: '32px',
          padding: '20px',
          background: '#fff',
          borderRadius: '12px',
          border: '1px solid #f1c4d4',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
        }}>
          <h2 style={{ color: '#c2185b', marginBottom: '12px', fontSize: '1.25rem' }}>
            Delete your account now
          </h2>
          {deleted ? (
            <div style={{
              padding: '14px 16px',
              background: '#e8f5e9',
              border: '1px solid #a5d6a7',
              borderRadius: '8px',
              color: '#1b5e20',
              lineHeight: 1.6
            }}>
              <strong>Your account has been deleted.</strong>
              <p style={{ margin: '8px 0 0 0' }}>
                Your profile, birth data, chat history and other personal data have been removed. You have been signed out. If you change your mind, you are welcome to create a new account anytime.
              </p>
            </div>
          ) : user ? (
            <>
              <p style={{ margin: '0 0 14px 0', lineHeight: 1.6, color: '#333' }}>
                You are signed in as <strong>{user.name || user.email || user.phone || `User ${user.userid || ''}`}</strong>. Deleting your account will permanently remove your profile, birth data, chat history, credits, subscriptions and settings. <strong>This cannot be undone.</strong>
              </p>
              <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '16px', color: '#333', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={confirmChecked}
                  onChange={(e) => setConfirmChecked(e.target.checked)}
                  style={{ marginTop: '3px' }}
                />
                <span>I understand this permanently deletes my account and all associated data.</span>
              </label>
              {deleteError && (
                <p style={{ color: '#b71c1c', margin: '0 0 12px 0' }}>{deleteError}</p>
              )}
              <button
                type="button"
                onClick={handleDeleteAccount}
                disabled={!confirmChecked || deleting}
                style={{
                  padding: '12px 20px',
                  background: !confirmChecked || deleting ? '#ccc' : '#c62828',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 'bold',
                  fontSize: '0.95rem',
                  cursor: !confirmChecked || deleting ? 'not-allowed' : 'pointer'
                }}
              >
                {deleting ? 'Deleting…' : 'Delete my account permanently'}
              </button>
            </>
          ) : (
            <>
              <p style={{ margin: '0 0 14px 0', lineHeight: 1.6, color: '#333' }}>
                To delete your account from here, please sign in first so we can verify it&apos;s really you.
              </p>
              <button
                type="button"
                onClick={() => onLogin && onLogin()}
                style={{
                  padding: '12px 20px',
                  background: '#e91e63',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 'bold',
                  fontSize: '0.95rem',
                  cursor: 'pointer'
                }}
              >
                Sign in to delete your account
              </button>
            </>
          )}
        </section>

        {/* Section A: Delete specific data (no account deletion) */}
        <section style={{
          marginBottom: '32px',
          padding: '20px',
          background: '#fff',
          borderRadius: '12px',
          border: '1px solid #e0e0e0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
        }}>
          <h2 style={{ color: '#e91e63', marginBottom: '12px', fontSize: '1.25rem' }}>
            Delete specific data (your account stays active)
          </h2>
          <p style={{ margin: '0 0 14px 0', lineHeight: 1.6, color: '#333' }}>
            You can delete <strong>individual past questions and the answers AstroRoshni provided</strong> in chat, without deleting your account.
          </p>
          <ol style={{ margin: '0 0 0 20px', padding: 0, lineHeight: 1.7, color: '#333' }}>
            <li>Open the <strong>AstroRoshni</strong> app (mobile or website).</li>
            <li>Go to <strong>Chat</strong> and find the conversation or message you want to remove.</li>
            <li>Use the <strong>delete</strong> option on that message (e.g. tap the delete action on the message bubble).</li>
            <li>Confirm deletion. That question and answer are permanently removed from our systems; your account and other data are unchanged.</li>
          </ol>
        </section>

        {/* Section B: Delete all data (full account deletion) */}
        <section style={{
          marginBottom: '32px',
          padding: '20px',
          background: '#fff',
          borderRadius: '12px',
          border: '1px solid #e0e0e0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
        }}>
          <h2 style={{ color: '#e91e63', marginBottom: '12px', fontSize: '1.25rem' }}>
            Delete your account and all data
          </h2>
          <p style={{ margin: '0 0 14px 0', lineHeight: 1.6, color: '#333' }}>
            To permanently delete your <strong>AstroRoshni</strong> account and all associated data:
          </p>
          <p style={{ margin: '0 0 8px 0', fontWeight: 'bold', color: '#333' }}>Option 1 – In the app</p>
          <p style={{ margin: '0 0 14px 0', lineHeight: 1.6, color: '#333' }}>
            Open the AstroRoshni mobile app → <strong>Profile</strong> → <strong>Delete Account &amp; Data</strong>. Confirm to remove your account and data.
          </p>
          <p style={{ margin: '0 0 8px 0', fontWeight: 'bold', color: '#333' }}>Option 2 – By email</p>
          <p style={{ margin: '0 0 12px 0', lineHeight: 1.6, color: '#333' }}>
            Email <a href="mailto:help@astroroshni.com?subject=Delete%20my%20AstroRoshni%20account" style={{ color: '#e91e63', fontWeight: 'bold' }}>help@astroroshni.com</a> with the subject line <em>&quot;Delete my AstroRoshni account&quot;</em>. We will process verified requests within 72 hours.
          </p>
          <a
            href="mailto:help@astroroshni.com?subject=Delete%20my%20AstroRoshni%20account"
            style={{
              display: 'inline-block',
              padding: '10px 18px',
              background: '#e91e63',
              color: '#fff',
              textDecoration: 'none',
              borderRadius: '8px',
              fontWeight: 'bold',
              fontSize: '0.95rem'
            }}
          >
            Email request to delete account
          </a>
        </section>

        {/* Section C: What is deleted / kept and retention */}
        <section style={{
          marginBottom: '24px',
          padding: '20px',
          background: '#f5f5f5',
          borderRadius: '12px',
          border: '1px solid #e0e0e0'
        }}>
          <h2 style={{ color: '#333', marginBottom: '12px', fontSize: '1.25rem' }}>
            What we delete and what we keep
          </h2>
          <ul style={{ margin: 0, paddingLeft: '20px', lineHeight: 1.7, color: '#333' }}>
            <li><strong>When you delete a message:</strong> That specific question and AstroRoshni’s answer are permanently deleted from our systems. No additional retention period for that content.</li>
            <li><strong>When you delete your account:</strong> We delete all data we hold for your account (e.g. profile, name, email, birth data, chat history, credits, subscriptions, settings). We do not retain this data after account deletion.</li>
            <li><strong>Legal requirements:</strong> We may retain minimal records only where required by law (e.g. for legal or tax purposes) for the period mandated by law. This does not include your chat content or personal astrological data.</li>
          </ul>
        </section>

        <p style={{ color: '#666', fontSize: '0.95em', marginTop: '8px' }}>
          For more on how we handle your data, see our{' '}
          <a href="/policy" style={{ color: '#e91e63' }}>Privacy Policy</a>.
        </p>
      </div>
    </div>
  );
};

export default DeleteAccountPage;
