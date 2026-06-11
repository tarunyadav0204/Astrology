import React from 'react';
import { createPortal } from 'react-dom';
import BirthForm from './BirthForm';
import './BirthFormModal.css';

const BirthFormModal = ({
  isOpen,
  onClose,
  onSubmit,
  onChartPick,
  title,
  description,
  prefilledData,
  defaultActiveTab = 'saved',
}) => {
  if (!isOpen) return null;

  const handleFormSubmit = (selectedChart) => {
    onSubmit?.(selectedChart);
    onClose();
  };

  const handleChartPick = (chart) => {
    onChartPick?.(chart);
    onClose();
  };

  return createPortal(
    <div className="birth-form-modal-overlay" style={{ zIndex: 2147483647 }} onClick={onClose}>
      <div className="birth-form-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="birth-form-modal-body">
          <BirthForm
            onSubmit={handleFormSubmit}
            onChartPick={onChartPick ? handleChartPick : undefined}
            pickModeTitle={title}
            pickModeDescription={description}
            prefilledData={prefilledData}
            onClose={onClose}
            defaultActiveTab={defaultActiveTab}
          />
        </div>
      </div>
    </div>,
    document.body
  );
};

export default BirthFormModal;
