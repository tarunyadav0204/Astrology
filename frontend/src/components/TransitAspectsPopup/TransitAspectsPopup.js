import React from 'react';
import VedicTransitAspects from '../TransitAspects/VedicTransitAspects';

const TransitAspectsPopup = ({ isOpen, onClose, birthData, natalChart, onTimelineClick }) => {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 10000,
      padding: '1rem'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        width: '90%',
        maxWidth: '800px',
        height: '80%',
        maxHeight: '600px',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1rem',
          borderBottom: '2px solid #e91e63',
          backgroundColor: '#f8f9fa',
          borderRadius: '12px 12px 0 0'
        }}>
          <h3 style={{
            margin: 0,
            color: '#e91e63',
            fontSize: '1.2rem',
            fontWeight: '600'
          }}>
            Transit Aspects Analysis
          </h3>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: '#666',
              padding: '0.5rem',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <VedicTransitAspects 
            birthData={birthData}
            natalChart={natalChart}
            onTimelineClick={onTimelineClick}
          />
        </div>
      </div>
    </div>
  );
};

export default TransitAspectsPopup;