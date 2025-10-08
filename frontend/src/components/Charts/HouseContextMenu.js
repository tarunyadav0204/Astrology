import React, { useState, useEffect, useRef } from 'react';

const HouseContextMenu = ({ 
  isOpen, 
  position, 
  houseNumber, 
  signName, 
  onClose, 
  onMakeAscendant,
  onShowAspects,
  onHouseAnalysis,
  onHouseSignifications,
  onHouseStrength
}) => {
  const menuRef = useRef(null);
  const [backdropActive, setBackdropActive] = useState(false);

  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Delay backdrop activation to prevent immediate closure
      setTimeout(() => setBackdropActive(true), 300);
    } else {
      setBackdropActive(false);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const menuItems = [
    {
      icon: '🔄',
      label: 'Make Ascendant',
      action: onMakeAscendant,
      description: 'Rotate chart to this house'
    },
    {
      icon: '👁️',
      label: 'Show Aspects',
      action: onShowAspects,
      description: 'Highlight aspects to this house'
    },
    {
      icon: '📊',
      label: 'House Analysis',
      action: onHouseAnalysis,
      description: 'Detailed house analysis'
    },
    {
      icon: '🌟',
      label: 'Significations',
      action: onHouseSignifications,
      description: 'What this house represents'
    },
    {
      icon: '⚡',
      label: 'House Strength',
      action: onHouseStrength,
      description: 'Strength and influences'
    }
  ];

  const handleItemClick = (action) => {
    action(houseNumber, signName);
    onClose();
  };

  // Adjust position to keep menu within viewport
  const adjustedPosition = {
    left: Math.min(position.x, window.innerWidth - 220),
    top: Math.min(position.y, window.innerHeight - 300)
  };

  return (
    <>
      {/* Backdrop */}
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.1)',
          zIndex: 9998
        }}
        onClick={backdropActive ? onClose : undefined}
      />
      
      {/* Context Menu */}
      <div
        ref={menuRef}
        style={{
          position: 'fixed',
          left: adjustedPosition.left,
          top: adjustedPosition.top,
          backgroundColor: 'white',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08)',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          minWidth: '200px',
          zIndex: 9999,
          overflow: 'hidden',
          animation: 'contextMenuSlideIn 0.15s ease-out'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '12px 16px',
          borderBottom: '1px solid #f0f0f0',
          backgroundColor: '#fafafa'
        }}>
          <div style={{
            fontSize: '14px',
            fontWeight: '600',
            color: '#333',
            marginBottom: '2px'
          }}>
            House {houseNumber}
          </div>
          <div style={{
            fontSize: '12px',
            color: '#666'
          }}>
            {signName}
          </div>
        </div>

        {/* Menu Items */}
        <div style={{ padding: '8px 0' }}>
          {menuItems.map((item, index) => (
            <button
              key={index}
              onClick={() => handleItemClick(item.action)}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: 'none',
                background: 'none',
                textAlign: 'left',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                transition: 'background-color 0.15s ease',
                fontSize: '14px'
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = '#f8f9fa';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = 'transparent';
              }}
            >
              <span style={{ 
                fontSize: '16px',
                minWidth: '20px',
                textAlign: 'center'
              }}>
                {item.icon}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{
                  fontWeight: '500',
                  color: '#333',
                  marginBottom: '2px'
                }}>
                  {item.label}
                </div>
                <div style={{
                  fontSize: '12px',
                  color: '#666'
                }}>
                  {item.description}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes contextMenuSlideIn {
          from {
            opacity: 0;
            transform: translateY(-8px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
      `}</style>
    </>
  );
};

export default HouseContextMenu;