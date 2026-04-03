import React, { useEffect } from 'react';
import './AuthModalShell.css';

/**
 * Mobile-safe auth dialog: scrollable body, sticky close so × stays visible on tall forms.
 */
export default function AuthModalShell({ isOpen, onClose, children }) {
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
            className="auth-modal-shell"
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
