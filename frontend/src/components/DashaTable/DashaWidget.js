import React, { useState, useEffect } from 'react';
import { DASHA_CONFIG } from '../../config/dashboard.config';
import { APP_CONFIG } from '../../config/app.config';
import { apiService } from '../../services/apiService';
import { WidgetContainer, WidgetHeader, WidgetTitle, DashaContainer, DashaTable, DashaRow, DashaCell } from './DashaWidget.styles';

const DashaWidget = ({ title, dashaType, birthData, onDashaClick, selectedDashas, onDashaSelection, transitDate, cascadingData }) => {
  const [selectedDasha, setSelectedDasha] = useState(null);
  const [dashaData, setDashaData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // Debounce dasha clicks to prevent rapid API calls
  const debounceTimeout = React.useRef(null);

  useEffect(() => {
    if (cascadingData) {
      loadCascadingData();
    }
  }, [cascadingData, dashaType]);

  const loadCascadingData = () => {
    if (!cascadingData) return;
    
    let data = [];
    switch (dashaType) {
      case 'maha':
        data = cascadingData.maha_dashas || [];
        break;
      case 'antar':
        data = cascadingData.antar_dashas || [];
        break;
      case 'pratyantar':
        data = cascadingData.pratyantar_dashas || [];
        break;
      case 'sookshma':
        data = cascadingData.sookshma_dashas || [];
        break;
      case 'prana':
        data = cascadingData.prana_dashas || [];
        break;
    }
    
    setDashaData(data);
    const currentDasha = data.find(d => d.current);
    if (currentDasha) {
      setSelectedDasha(currentDasha);
      if (!selectedDashas[dashaType]) {
        onDashaSelection(dashaType, currentDasha);
      }
      setTimeout(() => scrollToCurrentDasha(data.findIndex(d => d.current)), 100);
    }
  };



  const scrollToCurrentDasha = (currentIndex) => {
    if (currentIndex >= 0) {
      const container = document.querySelector(`[data-dasha-type="${dashaType}"] .dasha-container`);
      const rows = container?.querySelectorAll('tbody tr');
      if (rows && rows[currentIndex]) {
        rows[currentIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  };

  const handleDashaClick = (dasha) => {
    setSelectedDasha(dasha);
    onDashaClick(dasha.start);
    onDashaSelection(dashaType, dasha);
  };

  const isMobile = window.innerWidth <= 768;
  
  return (
    <WidgetContainer data-dasha-type={dashaType}>
      <WidgetHeader>
        <WidgetTitle>{title}</WidgetTitle>
      </WidgetHeader>
      
      <DashaContainer className="dasha-container">
        {isMobile ? (
          // Mobile card layout
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            {dashaData.map((dasha, idx) => (
              <div
                key={idx}
                onClick={() => handleDashaClick(dasha)}
                style={{
                  background: dasha.selected ? 'rgba(233, 30, 99, 0.15)' : 
                             dasha.current ? 'rgba(255, 111, 0, 0.15)' : 
                             idx % 2 === 0 ? 'rgba(255, 243, 224, 0.3)' : 'white',
                  border: '1px solid rgba(116, 185, 255, 0.2)',
                  borderRadius: '8px',
                  padding: '0.4rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: dasha.current ? '0 2px 8px rgba(255, 111, 0, 0.3)' : '0 1px 3px rgba(0,0,0,0.1)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontWeight: '700', fontSize: '0.7rem', color: '#2d3436' }}>
                    🪐 {dasha.planet}
                  </div>
                  <div style={{ fontSize: '0.55rem', color: '#636e72' }}>
                    {new Date(dasha.start).getDate()}/{(new Date(dasha.start).getMonth() + 1).toString().padStart(2, '0')}/{new Date(dasha.start).getFullYear().toString().slice(-2)} - {new Date(dasha.end).getDate()}/{(new Date(dasha.end).getMonth() + 1).toString().padStart(2, '0')}/{new Date(dasha.end).getFullYear().toString().slice(-2)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          // Desktop table layout
          <DashaTable>
            <thead>
              <tr>
                <DashaCell as="th">Planet</DashaCell>
                <DashaCell as="th">Start</DashaCell>
                <DashaCell as="th">End</DashaCell>
              </tr>
            </thead>
            <tbody>
              {dashaData.map((dasha, idx) => (
                <DashaRow 
                  key={idx} 
                  current={dasha.current}
                  selected={selectedDasha && selectedDasha.planet === dasha.planet && selectedDasha.start === dasha.start}
                  onClick={() => handleDashaClick(dasha)}
                >
                  <DashaCell>{dasha.planet}</DashaCell>
                  <DashaCell>{new Date(dasha.start).getDate()}/{(new Date(dasha.start).getMonth() + 1).toString().padStart(2, '0')}/{new Date(dasha.start).getFullYear().toString().slice(-2)}</DashaCell>
                  <DashaCell>{new Date(dasha.end).getDate()}/{(new Date(dasha.end).getMonth() + 1).toString().padStart(2, '0')}/{new Date(dasha.end).getFullYear().toString().slice(-2)}</DashaCell>
                </DashaRow>
              ))}
            </tbody>
          </DashaTable>
        )}
      </DashaContainer>
    </WidgetContainer>
  );
};

export default DashaWidget;