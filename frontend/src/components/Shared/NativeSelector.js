import React, { useState } from 'react';
import BirthFormModal from '../BirthForm/BirthFormModal';
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

      <BirthFormModal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleFormSubmit}
        title="Select Different Native"
        description="Choose a different person's birth details for analysis"
      />
    </div>
  );
};

export default NativeSelector;