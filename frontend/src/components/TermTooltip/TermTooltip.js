import React, { useState, useRef, useEffect } from 'react';
import './TermTooltip.css';

const TermTooltip = ({ termId, children, definition, glossary }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const termRef = useRef(null);
  const tooltipRef = useRef(null);

  const getDefinition = () => {
    let def = definition || glossary?.[termId];
    
    // Decode HTML entities if present
    if (def) {
      const textarea = document.createElement('textarea');
      textarea.innerHTML = def;
      def = textarea.value;
    }
    
    return def || `Definition for ${termId}`;
  };

  const updatePosition = () => {
    if (termRef.current && tooltipRef.current) {
      const termRect = termRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      
      // Position tooltip above the term
      let top = termRect.top - tooltipRect.height - 8;
      let left = termRect.left + (termRect.width / 2) - (tooltipRect.width / 2);
      
      // Keep tooltip in viewport
      if (left < 8) left = 8;
      if (left + tooltipRect.width > window.innerWidth - 8) {
        left = window.innerWidth - tooltipRect.width - 8;
      }
      // If no space above, show below
      if (top < 8) {
        top = termRect.bottom + 8;
      }
      
      setPosition({ top, left });
    }
  };

  useEffect(() => {
    if (isVisible) {
      updatePosition();
    }
  }, [isVisible]);

  const handleMouseEnter = () => {
    setIsVisible(true);
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
  };

  const handleClick = () => {
    setIsVisible(!isVisible);
  };

  return (
    <>
      <span
        ref={termRef}
        className="term-tooltip-trigger"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
      >
        {children}
      </span>
      
      {isVisible && (
        <div
          ref={tooltipRef}
          className="term-tooltip"
          style={{
            position: 'fixed',
            top: `${position.top}px`,
            left: `${position.left}px`,
            zIndex: 9999,
            visibility: 'visible',
            opacity: 1,
            backgroundColor: 'black',
            color: 'white',
            padding: '8px',
            borderRadius: '4px',
            fontSize: '14px',
            maxWidth: '300px'
          }}
        >
          <div className="term-tooltip-content">
            {getDefinition()}
          </div>
        </div>
      )}
    </>
  );
};

export default TermTooltip;