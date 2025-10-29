import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import BirthForm from '../BirthForm/BirthForm';
import './NativeSelector.css';

const NativeSelector = ({ birthData, onNativeChange }) => {
  const [showForm, setShowForm] = useState(false);

  const handleFormSubmit = () => {
    setShowForm(false);
    if (onNativeChange) onNativeChange();
  };

  const formatBirthDetails = (data) => {
    if (!data) return 'No native selected';
    return `${data.name || 'Unknown'} • ${data.date || ''} ${data.time || ''} • ${data.place || ''}`;
  };

  return (
    <div className="native-selector">
      <div className="current-native">
        <div className="native-info">
          <span className="native-label">Current Native:</span>
          <span className="native-details">{formatBirthDetails(birthData)}</span>
        </div>
        <button 
          className="change-native-btn"
          onClick={() => setShowForm(true)}
        >
          Change Native
        </button>
      </div>

      {showForm && createPortal(
        <div className="form-modal">
          <div className="form-modal-content">
            <div className="form-modal-header">
              <h3>Select Different Native</h3>
              <button 
                className="close-btn"
                onClick={() => setShowForm(false)}
              >
                ×
              </button>
            </div>
            <BirthForm onSubmit={handleFormSubmit} />
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default NativeSelector;