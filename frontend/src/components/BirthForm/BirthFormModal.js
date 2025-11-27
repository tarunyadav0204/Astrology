import React from 'react';
import { createPortal } from 'react-dom';
import BirthForm from './BirthForm';
import './BirthFormModal.css';

const BirthFormModal = ({ isOpen, onClose, onSubmit, title, description, prefilledData }) => {
  if (!isOpen) return null;

  const handleFormSubmit = () => {
    onSubmit();
    onClose();
  };

  return createPortal(
    <div className="birth-form-modal-overlay" style={{zIndex: 2147483647}} onClick={onClose}>
      <div className="birth-form-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="birth-form-modal-body">
          <BirthForm onSubmit={handleFormSubmit} prefilledData={prefilledData} onClose={onClose} />
        </div>
      </div>
    </div>,
    document.body
  );
};

export default BirthFormModal;