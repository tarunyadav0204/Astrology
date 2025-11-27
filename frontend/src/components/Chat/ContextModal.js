import React from 'react';
import './ContextModal.css';

const ContextModal = ({ isOpen, onClose, contextData }) => {
  if (!isOpen) return null;

  return (
    <div className="context-modal-overlay" onClick={onClose}>
      <div className="context-modal" onClick={e => e.stopPropagation()}>
        <div className="context-modal-header">
          <h3>Gemini Context Data</h3>
          <button className="context-modal-close" onClick={onClose}>×</button>
        </div>
        <div className="context-modal-content">
          {contextData ? (
            <pre className="context-json">{JSON.stringify(contextData, null, 2)}</pre>
          ) : (
            <p>No context data available</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ContextModal;