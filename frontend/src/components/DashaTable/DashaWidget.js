import React, { useState, useEffect } from 'react';
import { DASHA_CONFIG } from '../../config/dashboard.config';
import { WidgetContainer, WidgetHeader, WidgetTitle, DashaContainer, DashaTable, DashaRow, DashaCell } from './DashaWidget.styles';

const DashaWidget = ({ title, dashaType, birthData, onDashaClick, selectedDashas, onDashaSelection, transitDate }) => {
  const [selectedDasha, setSelectedDasha] = useState(null);
  const [dashaData, setDashaData] = useState([]);

  useEffect(() => {
    if (birthData) {
      fetchDashaData();
    }
  }, [birthData, dashaType, selectedDashas, transitDate]);

  const fetchDashaData = async () => {
    try {
      const response = await fetch('http://localhost:8001/calculate-dasha', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(birthData)
      });
      const data = await response.json();
      
      if (dashaType === 'maha') {
        const targetDate = transitDate || new Date();
        const processedDashas = data.maha_dashas.map(dasha => ({
          ...dasha,
          current: new Date(dasha.start) <= targetDate && targetDate <= new Date(dasha.end)
        }));
        setDashaData(processedDashas);
        const currentDasha = processedDashas.find(d => d.current);
        if (currentDasha) {
          setSelectedDasha(currentDasha);
          if (!selectedDashas.maha) {
            onDashaSelection('maha', currentDasha);
          }
          setTimeout(() => scrollToCurrentDasha(processedDashas.findIndex(d => d.current)), 100);
        }
      } else {
        // Calculate hierarchical sub-dashas using backend
        const targetDate = transitDate || new Date();
        const currentMaha = data.maha_dashas.find(d => {
          return new Date(d.start) <= targetDate && targetDate <= new Date(d.end);
        });
        
        if (currentMaha) {
          let parentDasha = currentMaha;
          
          // Use selected dashas or current dashas for hierarchy
          if (dashaType === 'antar') {
            parentDasha = (selectedDashas && selectedDashas.maha) ? selectedDashas.maha : currentMaha;
          } else if (dashaType === 'pratyantar') {
            const mahaForAntar = (selectedDashas && selectedDashas.maha) ? selectedDashas.maha : currentMaha;
            const antarDashas = await calculateSubDashas(mahaForAntar, 'antar', targetDate);
            parentDasha = (selectedDashas && selectedDashas.antar) ? selectedDashas.antar : antarDashas.find(d => d.current) || antarDashas[0];
          } else if (dashaType === 'sookshma') {
            const mahaForAntar = (selectedDashas && selectedDashas.maha) ? selectedDashas.maha : currentMaha;
            const antarDashas = await calculateSubDashas(mahaForAntar, 'antar', targetDate);
            const antarForPratyantar = (selectedDashas && selectedDashas.antar) ? selectedDashas.antar : antarDashas.find(d => d.current) || antarDashas[0];
            const pratyantarDashas = await calculateSubDashas(antarForPratyantar, 'pratyantar', targetDate);
            parentDasha = (selectedDashas && selectedDashas.pratyantar) ? selectedDashas.pratyantar : pratyantarDashas.find(d => d.current) || pratyantarDashas[0];
          } else if (dashaType === 'prana') {
            const mahaForAntar = (selectedDashas && selectedDashas.maha) ? selectedDashas.maha : currentMaha;
            const antarDashas = await calculateSubDashas(mahaForAntar, 'antar', targetDate);
            const antarForPratyantar = (selectedDashas && selectedDashas.antar) ? selectedDashas.antar : antarDashas.find(d => d.current) || antarDashas[0];
            const pratyantarDashas = await calculateSubDashas(antarForPratyantar, 'pratyantar', targetDate);
            const pratyantarForSookshma = (selectedDashas && selectedDashas.pratyantar) ? selectedDashas.pratyantar : pratyantarDashas.find(d => d.current) || pratyantarDashas[0];
            const sookshmaDashas = await calculateSubDashas(pratyantarForSookshma, 'sookshma', targetDate);
            parentDasha = (selectedDashas && selectedDashas.sookshma) ? selectedDashas.sookshma : sookshmaDashas.find(d => d.current) || sookshmaDashas[0];
          }
          
          const subDashas = await calculateSubDashas(parentDasha, dashaType, targetDate);
          
          setDashaData(subDashas);
          const currentSubDasha = subDashas.find(d => d.current);
          if (currentSubDasha) {
            setSelectedDasha(currentSubDasha);
            if (!selectedDashas || !selectedDashas[dashaType]) {
              onDashaSelection(dashaType, currentSubDasha);
            }
            setTimeout(() => scrollToCurrentDasha(subDashas.findIndex(d => d.current)), 100);
          }
        }
      }
    } catch (error) {
      console.error('Error fetching dasha data:', error);
    }
  };

  const calculateSubDashas = async (parentDasha, type, targetDate = null) => {
    try {
      // Prepare request data with hierarchy information
      const requestData = {
        birth_data: birthData,
        parent_dasha: parentDasha,
        dasha_type: type,
        target_date: (targetDate || transitDate || new Date()).toISOString().split('T')[0]
      };
      
      // Add hierarchy information for proper calculation
      if (type === 'pratyantar' && selectedDashas.maha) {
        requestData.maha_lord = selectedDashas.maha.planet;
      } else if (type === 'sookshma' && selectedDashas.maha && selectedDashas.antar) {
        requestData.maha_lord = selectedDashas.maha.planet;
        requestData.antar_lord = selectedDashas.antar.planet;
      } else if (type === 'prana' && selectedDashas.maha && selectedDashas.antar && selectedDashas.pratyantar) {
        requestData.maha_lord = selectedDashas.maha.planet;
        requestData.antar_lord = selectedDashas.antar.planet;
        requestData.pratyantar_lord = selectedDashas.pratyantar.planet;
      }
      
      const response = await fetch('http://localhost:8001/calculate-sub-dashas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      });
      
      const data = await response.json();
      return data.sub_dashas || [];
    } catch (error) {
      console.error('Error calculating sub-dashas:', error);
      return [];
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

  return (
    <WidgetContainer data-dasha-type={dashaType}>
      <WidgetHeader>
        <WidgetTitle>{title}</WidgetTitle>
      </WidgetHeader>
      
      <DashaContainer className="dasha-container">
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
      </DashaContainer>
    </WidgetContainer>
  );
};

export default DashaWidget;