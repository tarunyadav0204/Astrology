import React, { useEffect } from 'react';
import './AuthModalShell.css';

/**
 * Mobile-safe auth dialog: scrollable body, sticky close so × stays visible on tall forms.
 * @param {boolean} [themed] Use AstroRoshni design-token styling (not limited to the homepage).
 */
export default function AuthModalShell({ isOpen, onClose, children, themed = false }) {
    useEffect(() => {
        if (!isOpen) return undefined;
        const prev = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        return () => {
            document.body.style.overflow = prev;
        };
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div
            className={themed ? 'auth-modal-shell auth-modal-shell--themed' : 'auth-modal-shell'}
            role="presentation"
            onClick={onClose}
        >
            <div
                className="auth-modal-shell__panel"
                role="dialog"
                aria-modal="true"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="auth-modal-shell__scroll">
                    <div className="auth-modal-shell__sticky-close">
                        <button
                            type="button"
                            className="auth-modal-shell__close"
                            onClick={onClose}
                            aria-label="Close"
                        >
                            ×
                        </button>
                    </div>
                    <div className="auth-modal-shell__body">{children}</div>
                </div>
            </div>
        </div>
    );
}
