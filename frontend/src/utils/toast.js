// Simple toast notification utility
export const showToast = (message, type = 'success', duration = 2000) => {
    // Remove existing toast if any
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.textContent = message;
    
    // Keep the toast surface theme-aware; the semantic side accent communicates
    // status without replacing the active theme with a fixed bright panel.
    let accentColor;
    switch(type) {
        case 'success':
            accentColor = 'var(--color-success)';
            break;
        case 'error':
            accentColor = 'var(--color-danger)';
            break;
        case 'info':
            accentColor = 'var(--color-info)';
            break;
        default:
            accentColor = 'var(--color-success)';
    }
    
    // Style the toast
    Object.assign(toast.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        background: 'var(--color-surface-raised)',
        color: 'var(--color-text)',
        border: '1px solid var(--color-border)',
        borderLeft: `4px solid ${accentColor}`,
        padding: '12px 20px',
        borderRadius: '8px',
        fontSize: '14px',
        fontWeight: '500',
        zIndex: '100000',
        boxShadow: 'var(--shadow-card)',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease',
        maxWidth: '300px',
        wordWrap: 'break-word'
    });
    
    // Add to document
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 10);
    
    // Animate out and remove
    setTimeout(() => {
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, duration);
};

export default { showToast };
