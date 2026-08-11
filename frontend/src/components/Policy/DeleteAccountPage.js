import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import { APP_CONFIG } from '../../config/app.config';
import './DeleteAccountPage.css';

const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? APP_CONFIG.api.prod
  : APP_CONFIG.api.dev;

const getEndpoint = (path) => {
  if (API_BASE_URL.includes('localhost')) return `${API_BASE_URL}/api${path}`;
  return `/api${path}`;
};

const DeleteAccountPage = ({ user, onLogin, onLogout, onAdminClick }) => {
  const [confirmChecked, setConfirmChecked] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleted, setDeleted] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  const accountName = user?.name || user?.email || user?.phone || `User ${user?.userid || ''}`;

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
    } catch (error) {
      setDeleteError(error.message || 'Failed to delete account. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="delete-account-page">
      <ModernNavigationHeader
        sticky
        user={user}
        onLogin={onLogin}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
      />

      <main className="delete-account-main">
        <header className="delete-account-hero">
          <p className="delete-account-eyebrow">Privacy controls</p>
          <div className="delete-account-hero__body">
            <div>
              <h1>Your data,<br /><em>your decision.</em></h1>
              <p>
                Remove individual conversations while keeping your account, or permanently delete
                your AstroRoshni account and its associated personal data.
              </p>
            </div>
            <dl className="delete-account-hero__meta">
              <div><dt>Identity</dt><dd>Verified before deletion</dd></div>
              <div><dt>Account deletion</dt><dd>Permanent</dd></div>
              <div><dt>Email requests</dt><dd>Processed within 72 hours</dd></div>
            </dl>
          </div>
        </header>

        <section className="delete-account-action" aria-labelledby="delete-account-action-title">
          <div className="delete-account-action__intro">
            <p className="delete-account-section-label">Permanent action</p>
            <h2 id="delete-account-action-title">Delete your entire account</h2>
            <p>
              This removes the account—not just one reading. Review the affected data and confirm
              your identity before continuing.
            </p>
          </div>

          <div className="delete-account-impact" aria-label="Data affected by account deletion">
            <span>Profile &amp; identity</span>
            <span>Birth data</span>
            <span>Chat history</span>
            <span>Credits</span>
            <span>Subscriptions</span>
            <span>Settings</span>
          </div>

          {deleted ? (
            <div className="delete-account-success" role="status">
              <strong>Your account has been deleted.</strong>
              <p>
                Your profile, birth data, chat history and other personal data have been removed.
                You have been signed out. You may create a new account at any time.
              </p>
            </div>
          ) : user ? (
            <div className="delete-account-confirmation">
              <div className="delete-account-identity">
                <span aria-hidden>{accountName.charAt(0).toUpperCase()}</span>
                <div><small>Signed in as</small><strong>{accountName}</strong></div>
              </div>
              <p>
                Deleting this account permanently removes the data listed above.
                <strong> This cannot be undone.</strong>
              </p>
              <label className="delete-account-check">
                <input
                  type="checkbox"
                  checked={confirmChecked}
                  onChange={(event) => setConfirmChecked(event.target.checked)}
                />
                <span>
                  <strong>I understand this is permanent.</strong>
                  Delete my account and all associated data.
                </span>
              </label>
              {deleteError && <p className="delete-account-error" role="alert">{deleteError}</p>}
              <button
                type="button"
                className="delete-account-danger-button"
                onClick={handleDeleteAccount}
                disabled={!confirmChecked || deleting}
              >
                {deleting ? 'Deleting account…' : 'Delete my account permanently'}
              </button>
            </div>
          ) : (
            <div className="delete-account-signin">
              <h3>Confirm it’s really you</h3>
              <p>Sign in to the AstroRoshni account you want to delete before this action becomes available.</p>
              <button type="button" className="delete-account-primary-button" onClick={() => onLogin?.()}>
                Sign in to continue
              </button>
            </div>
          )}
        </section>

        <section className="delete-account-options" aria-labelledby="delete-less-title">
          <div className="delete-account-section-heading">
            <p className="delete-account-section-label">Keep your account</p>
            <h2 id="delete-less-title">Only want to remove a conversation?</h2>
            <p>Delete individual past questions and AstroRoshni answers without affecting your birth charts, credits, or account.</p>
          </div>
          <ol className="delete-account-steps">
            <li><span>01</span><p>Open AstroRoshni on mobile or the website.</p></li>
            <li><span>02</span><p>Go to <strong>Chat</strong> and find the conversation or message.</p></li>
            <li><span>03</span><p>Use the delete action on that message.</p></li>
            <li><span>04</span><p>Confirm deletion. That question and answer are removed; everything else stays active.</p></li>
          </ol>
        </section>

        <section className="delete-account-request" aria-labelledby="other-delete-title">
          <div className="delete-account-section-heading">
            <p className="delete-account-section-label">Alternative routes</p>
            <h2 id="other-delete-title">Request full deletion another way</h2>
          </div>
          <div className="delete-account-request__grid">
            <article>
              <span>01</span>
              <h3>In the mobile app</h3>
              <p>Open AstroRoshni, then go to <strong>Profile → Delete Account &amp; Data</strong> and confirm.</p>
            </article>
            <article>
              <span>02</span>
              <h3>By verified email</h3>
              <p>Email us with the subject “Delete my AstroRoshni account.” Verified requests are processed within 72 hours.</p>
              <a href="mailto:help@astroroshni.com?subject=Delete%20my%20AstroRoshni%20account">
                Email deletion request <b aria-hidden>↗</b>
              </a>
            </article>
          </div>
        </section>

        <section className="delete-account-retention" aria-labelledby="retention-title">
          <p className="delete-account-section-label">Data lifecycle</p>
          <h2 id="retention-title">What is deleted—and what may be kept</h2>
          <div className="delete-account-retention__grid">
            <article>
              <span>Message deletion</span>
              <p>That specific question and AstroRoshni’s answer are permanently deleted. There is no additional retention period for that content.</p>
            </article>
            <article>
              <span>Account deletion</span>
              <p>We delete the profile, name, email, birth data, chat history, credits, subscriptions, and settings held for the account.</p>
            </article>
            <article>
              <span>Legal requirements</span>
              <p>Minimal records may be retained only where required by law, such as legal or tax records. This does not include chat content or personal astrological data.</p>
            </article>
          </div>
        </section>

        <footer className="delete-account-footer">
          <span>Learn how AstroRoshni handles personal data</span>
          <Link to="/policy">Read the Privacy Policy <b aria-hidden>↗</b></Link>
        </footer>
      </main>
    </div>
  );
};

export default DeleteAccountPage;
