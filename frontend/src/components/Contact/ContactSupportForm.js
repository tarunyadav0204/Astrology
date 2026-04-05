import React, { useState } from 'react';
import './ContactSupportForm.css';
import { authService } from '../../services/authService';
import { sanitizeSupportBody, sanitizeSupportSubject } from '../../utils/supportText';

/**
 * Authenticated support ticket form. Reusable on Contact or other pages.
 * Uses same-origin /api proxy; server sanitizes all text.
 * Styles: ContactPage.css (.contact-support-form)
 */
const ContactSupportForm = () => {
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    const token = authService.getToken();
    if (!token) {
      setError('Please log in to open a support ticket.');
      return;
    }
    const sub = sanitizeSupportSubject(subject);
    const msg = sanitizeSupportBody(message);
    if (!sub || !msg) {
      setError('Please enter a subject and a message (plain text only).');
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch('/api/support/tickets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ subject: sub, message: msg, source: 'web' }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data.detail;
        const msgText =
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((d) => d.msg || d).join(' ')
              : 'Could not submit. Please try again.';
        throw new Error(msgText);
      }
      setSuccess('Your message was sent. We will get back to you soon.');
      setSubject('');
      setMessage('');
    } catch (err) {
      setError(err.message || 'Request failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="contact-support-form">
      <h3>Support ticket</h3>
      <p className="contact-support-lead">
        Logged-in users can send a secure message to our team. Do not include passwords or payment card numbers.
      </p>
      <form onSubmit={onSubmit}>
        <label htmlFor="contact-support-subject">Subject</label>
        <input
          id="contact-support-subject"
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          maxLength={220}
          autoComplete="off"
          placeholder="Brief summary"
        />
        <label htmlFor="contact-support-message">Message</label>
        <textarea
          id="contact-support-message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          maxLength={9000}
          rows={5}
          placeholder="Describe your question or issue"
        />
        {error ? <p className="contact-support-error">{error}</p> : null}
        {success ? <p className="contact-support-success">{success}</p> : null}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Sending…' : 'Send message'}
        </button>
      </form>
    </div>
  );
};

export default ContactSupportForm;
