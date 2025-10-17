import React, { useState } from 'react';
import RuleManager from '../RuleEngine/RuleManager';
import EventAnalyzer from '../RuleEngine/EventAnalyzer';
import HouseCombinations from '../Admin/HouseCombinations';
import HouseSpecifications from '../Admin/HouseSpecifications';
import NakshatraManager from '../NakshatraManager/NakshatraManager';

const AdminTab = ({ chartData, birthData }) => {
  const [activeSubTab, setActiveSubTab] = useState('rule-engine');
  const isMobile = window.innerWidth <= 768;

  const adminTabs = [
    { id: 'rule-engine', label: '⚙️ Rule Engine', component: RuleManager },
    { id: 'event-analyzer', label: '🔍 Event Analyzer', component: EventAnalyzer },
    { id: 'house-combinations', label: '🏠 House Combos', component: HouseCombinations },
    { id: 'house-specifications', label: '📝 House Specs', component: HouseSpecifications },
    { id: 'nakshatra-manager', label: '🌟 Nakshatras', component: NakshatraManager }
  ];

  const ActiveComponent = adminTabs.find(tab => tab.id === activeSubTab)?.component;

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ 
        color: '#e91e63', 
        marginBottom: '1rem', 
        fontSize: '1.4rem', 
        textAlign: 'center' 
      }}>
        🛠️ Admin Panel
      </h3>
      
      {/* Sub-tab Navigation */}
      <div style={{
        display: 'flex',
        marginBottom: '1.5rem',
        borderBottom: '2px solid #f0f0f0',
        gap: '0',
        overflowX: 'auto',
        scrollbarWidth: 'none',
        msOverflowStyle: 'none'
      }}>
        {adminTabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id)}
            style={{
              flex: isMobile ? 'none' : 1,
              padding: isMobile ? '8px 12px' : '12px 16px',
              border: 'none',
              background: activeSubTab === tab.id ? '#e91e63' : 'transparent',
              color: activeSubTab === tab.id ? 'white' : '#666',
              fontSize: isMobile ? '14px' : '16px',
              fontWeight: '600',
              cursor: 'pointer',
              borderRadius: '8px 8px 0 0',
              borderBottom: activeSubTab === tab.id ? '3px solid #e91e63' : '3px solid transparent',
              transition: 'all 0.3s ease',
              whiteSpace: 'nowrap',
              minWidth: 'fit-content'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Sub-tab Content */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {ActiveComponent && (
          <ActiveComponent 
            chartData={chartData} 
            birthData={birthData}
            birthChart={chartData}
          />
        )}
      </div>
    </div>
  );
};

export default AdminTab;