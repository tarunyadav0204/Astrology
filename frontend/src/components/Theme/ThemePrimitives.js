import React, { forwardRef, useEffect, useId, useRef } from 'react';
import { createPortal } from 'react-dom';
import './ThemePrimitives.css';

const cx = (...classes) => classes.filter(Boolean).join(' ');

export function ThemePage({
  as: Component = 'main',
  mode = 'editorial',
  tone = 'canvas',
  className,
  children,
  ...props
}) {
  return (
    <Component className={cx('ar-page', `ar-page--${mode}`, `ar-page--${tone}`, className)} {...props}>
      {children}
    </Component>
  );
}

export function ThemeContainer({ as: Component = 'div', size = 'wide', className, children, ...props }) {
  return (
    <Component className={cx('ar-container', `ar-container--${size}`, className)} {...props}>
      {children}
    </Component>
  );
}

export const ThemeButton = forwardRef(function ThemeButton({
  as: Component = 'button',
  variant = 'primary',
  size = 'md',
  className,
  children,
  type,
  ...props
}, ref) {
  const componentProps = Component === 'button' ? { type: type || 'button', ...props } : props;
  return (
    <Component
      ref={ref}
      className={cx('ar-button', `ar-button--${variant}`, `ar-button--${size}`, className)}
      {...componentProps}
    >
      {children}
    </Component>
  );
});

export function ThemeCard({
  as: Component = 'article',
  tone = 'surface',
  interactive = false,
  className,
  children,
  ...props
}) {
  return (
    <Component
      className={cx('ar-card', `ar-card--${tone}`, interactive && 'ar-card--interactive', className)}
      {...props}
    >
      {children}
    </Component>
  );
}

export function ThemeSectionHeading({ eyebrow, title, description, align = 'left', className, as = 'h2' }) {
  const Heading = as;
  return (
    <header className={cx('ar-section-heading', `ar-section-heading--${align}`, className)}>
      {eyebrow ? <p className="ar-section-heading__eyebrow">{eyebrow}</p> : null}
      <Heading>{title}</Heading>
      {description ? <p className="ar-section-heading__description">{description}</p> : null}
    </header>
  );
}

export function ThemeField({ label, hint, error, required, inputId, className, children }) {
  const generatedId = useId();
  const resolvedId = inputId || `ar-field-${generatedId.replace(/:/g, '')}`;
  const hintId = hint ? `${resolvedId}-hint` : undefined;
  const errorId = error ? `${resolvedId}-error` : undefined;
  const control = React.isValidElement(children)
    ? React.cloneElement(children, {
        id: children.props.id || resolvedId,
        'aria-describedby': [children.props['aria-describedby'], hintId, errorId].filter(Boolean).join(' ') || undefined,
        'aria-invalid': error ? true : children.props['aria-invalid'],
      })
    : children;

  return (
    <div className={cx('ar-field', error && 'ar-field--error', className)}>
      <label htmlFor={resolvedId}>{label}{required ? <span aria-hidden> *</span> : null}</label>
      {control}
      {hint ? <p className="ar-field__hint" id={hintId}>{hint}</p> : null}
      {error ? <p className="ar-field__error" id={errorId} role="alert">{error}</p> : null}
    </div>
  );
}

export const ThemeInput = forwardRef(function ThemeInput({ className, ...props }, ref) {
  return <input ref={ref} className={cx('ar-input', className)} {...props} />;
});

export const ThemeSelect = forwardRef(function ThemeSelect({ className, children, ...props }, ref) {
  return <select ref={ref} className={cx('ar-input', 'ar-select', className)} {...props}>{children}</select>;
});

export const ThemeTextarea = forwardRef(function ThemeTextarea({ className, ...props }, ref) {
  return <textarea ref={ref} className={cx('ar-input', 'ar-textarea', className)} {...props} />;
});

export function ThemeTabs({ className, label, children, ...props }) {
  return <div className={cx('ar-tabs', className)} role="tablist" aria-label={label} {...props}>{children}</div>;
}

export const ThemeTab = forwardRef(function ThemeTab({ active, className, children, ...props }, ref) {
  return (
    <button
      ref={ref}
      type="button"
      className={cx('ar-tab', active && 'is-active', className)}
      role="tab"
      aria-selected={Boolean(active)}
      {...props}
    >
      {children}
    </button>
  );
});

const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

export function ThemeModal({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  closeLabel = 'Close dialog',
  className,
}) {
  const titleId = useId();
  const descriptionId = useId();
  const panelRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return undefined;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const frame = window.requestAnimationFrame(() => {
      const preferred = panelRef.current?.querySelector('[autofocus], input, select, textarea, button');
      (preferred || panelRef.current)?.focus();
    });

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose?.();
        return;
      }
      if (event.key !== 'Tab' || !panelRef.current) return;
      const focusable = [...panelRef.current.querySelectorAll(FOCUSABLE)];
      if (focusable.length === 0) {
        event.preventDefault();
        panelRef.current.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      window.cancelAnimationFrame(frame);
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', handleKeyDown);
      previousFocus?.focus?.();
    };
  }, [isOpen, onClose]);

  if (!isOpen || typeof document === 'undefined') return null;

  return createPortal(
    <div className="ar-modal" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose?.();
    }}>
      <section
        ref={panelRef}
        className={cx('ar-modal__panel', `ar-modal__panel--${size}`, className)}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
      >
        <header className="ar-modal__header">
          <div>
            {title ? <h2 id={titleId}>{title}</h2> : null}
            {description ? <p id={descriptionId}>{description}</p> : null}
          </div>
          <button type="button" className="ar-modal__close" onClick={onClose} aria-label={closeLabel}>×</button>
        </header>
        <div className="ar-modal__body">{children}</div>
      </section>
    </div>,
    document.body
  );
}
