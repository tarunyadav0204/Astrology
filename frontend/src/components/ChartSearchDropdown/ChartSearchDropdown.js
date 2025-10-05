import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { apiService } from '../../services/apiService';

const ChartSearchDropdown = ({ currentChart, onSelectChart, onViewAll }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 200 });
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (searchQuery.length >= 2) {
      searchCharts();
    } else {
      setSearchResults([]);
    }
  }, [searchQuery]);

  const searchCharts = async () => {
    try {
      setLoading(true);
      const response = await apiService.getExistingCharts(searchQuery, 10);
      setSearchResults(response.charts || []);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = () => {
    if (!isOpen && dropdownRef.current) {
      const rect = dropdownRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom,
        left: rect.left,
        width: rect.width
      });
    }
    setIsOpen(!isOpen);
  };

  const handleSelect = (chart) => {
    onSelectChart(chart);
    setIsOpen(false);
    setSearchQuery('');
  };

  const handleViewAll = () => {
    onViewAll();
    setIsOpen(false);
    setSearchQuery('');
  };

  return (
    <div ref={dropdownRef} style={{ position: 'relative', minWidth: window.innerWidth <= 768 ? '120px' : '200px' }}>
      <div
        onClick={handleToggle}
        style={{
          padding: window.innerWidth <= 768 ? '6px 8px' : '8px 12px',
          border: '2px solid #e91e63',
          borderRadius: '8px',
          background: 'white',
          color: '#e91e63',
          fontSize: window.innerWidth <= 768 ? '12px' : '14px',
          fontWeight: '600',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <span style={{ 
          overflow: 'hidden', 
          textOverflow: 'ellipsis', 
          whiteSpace: 'nowrap',
          maxWidth: window.innerWidth <= 768 ? '80px' : 'none'
        }}>
          {currentChart?.name || 'Select Chart'}
        </span>
        <span style={{ marginLeft: '8px' }}>{isOpen ? '▲' : '▼'}</span>
      </div>

      {isOpen && createPortal(
        <div style={{
          position: 'fixed',
          top: dropdownPosition.top,
          left: dropdownPosition.left,
          width: dropdownPosition.width,
          background: 'white',
          border: '2px solid #e91e63',
          borderTop: 'none',
          borderRadius: '0 0 8px 8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 9999,
          maxHeight: '300px',
          overflow: 'hidden'
        }}>
          <input
            type="text"
            placeholder="🔍 Search charts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              border: 'none',
              borderBottom: '1px solid #eee',
              fontSize: '14px',
              outline: 'none'
            }}
            autoFocus
          />

          <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
            {loading ? (
              <div style={{ padding: '12px', textAlign: 'center', color: '#666' }}>
                Searching...
              </div>
            ) : searchQuery.length < 2 ? (
              <div style={{ padding: '12px', color: '#666', fontSize: '13px' }}>
                Type 2+ characters to search
              </div>
            ) : searchResults.length === 0 ? (
              <div style={{ padding: '12px', color: '#666' }}>
                No charts found
              </div>
            ) : (
              searchResults.map(chart => (
                <div
                  key={chart.id}
                  onClick={() => handleSelect(chart)}
                  style={{
                    padding: '10px 12px',
                    cursor: 'pointer',
                    borderBottom: '1px solid #f0f0f0',
                    fontSize: '13px'
                  }}
                  onMouseEnter={(e) => e.target.style.background = '#f8f9fa'}
                  onMouseLeave={(e) => e.target.style.background = 'white'}
                >
                  <div style={{ fontWeight: '600', color: '#333' }}>{chart.name}</div>
                  <div style={{ color: '#666', fontSize: '12px' }}>
                    {new Date(chart.date).toLocaleDateString()} • {chart.time}
                  </div>
                </div>
              ))
            )}

            <div
              onClick={handleViewAll}
              style={{
                padding: '12px',
                cursor: 'pointer',
                borderTop: '2px solid #e91e63',
                background: '#f8f9fa',
                color: '#e91e63',
                fontWeight: '600',
                textAlign: 'center',
                fontSize: '13px'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#e91e63';
                e.target.style.color = 'white';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = '#f8f9fa';
                e.target.style.color = '#e91e63';
              }}
            >
              📊 View All Charts
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default ChartSearchDropdown;