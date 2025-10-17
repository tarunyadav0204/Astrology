import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/apiService';

const PlanetarySignificance = ({ planet, nakshatra, house }) => {
  const [interpretation, setInterpretation] = useState('Loading interpretation...');
  
  useEffect(() => {
    loadInterpretation();
  }, [planet, nakshatra, house]);
  
  const loadInterpretation = async () => {
    const result = await getPlanetNakshatraSignificance(planet, nakshatra, house);
    setInterpretation(result);
  };
  
  return <p style={{ fontSize: '15px', lineHeight: '24px', color: '#333', textAlign: 'justify' }}>{interpretation}</p>;
};

const getPlanetNakshatraSignificance = async (planet, nakshatra, house) => {
  try {
    const interpretation = await apiService.getPlanetNakshatraInterpretation(planet, nakshatra, house);
    if (interpretation) {
      return interpretation;
    }
  } catch (error) {
    console.error('Failed to fetch interpretation:', error);
  }
  
  // Fallback to base interpretation without house context
  return `Classical texts describe ${planet} in ${nakshatra} as bringing specific influences. This combination creates unique karmic patterns and life experiences that manifest according to the native's overall chart strength and planetary periods.`;
};

const NakshatrasTab = ({ chartData, birthData }) => {
  const [selectedNakshatra, setSelectedNakshatra] = useState(null);
  const [selectedPlanetPosition, setSelectedPlanetPosition] = useState(null);
  const [activeTab, setActiveTab] = useState('planets'); // 'planets' or 'nakshatras'
  const [nakshatras, setNakshatras] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadNakshatras();
  }, []);
  
  const loadNakshatras = async () => {
    try {
      const response = await apiService.getNakshatrasPublic();
      setNakshatras(response.nakshatras || []);
    } catch (error) {
      console.error('Failed to load nakshatras:', error);
      // Fallback to basic data if API fails
      setNakshatras([
        { name: 'Ashwini', lord: 'Ketu', deity: 'Ashwini Kumaras', nature: 'Light/Swift', guna: 'Rajas', description: 'First nakshatra ruled by Ketu', characteristics: 'Pioneering spirit', positive_traits: 'Leadership', negative_traits: 'Impatience', careers: 'Medicine', compatibility: 'Bharani' },
        // Add other basic nakshatras as fallback...
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getNakshatra = (longitude) => {
    const nakshatraIndex = Math.floor(longitude / 13.333333);
    const pada = Math.floor((longitude % 13.333333) / 3.333333) + 1;
    return { index: nakshatraIndex, pada };
  };

  const getPlanetaryPositions = () => {
    if (!chartData?.planets) return [];
    
    return Object.entries(chartData.planets).map(([name, data]) => {
      const nakshatra = getNakshatra(data.longitude);
      const nakshatraData = nakshatras[nakshatra.index];
      
      return {
        planet: name,
        longitude: data.longitude.toFixed(2),
        nakshatra: nakshatraData?.name || 'Unknown',
        pada: nakshatra.pada,
        lord: nakshatraData?.lord || 'Unknown',
        deity: nakshatraData?.deity || 'Unknown',
        nature: nakshatraData?.nature || 'Unknown',
        guna: nakshatraData?.guna || 'Unknown',
        house: data.house || 1
      };
    });
  };

  const planetaryPositions = getPlanetaryPositions();
  const isMobile = window.innerWidth <= 768;

  // Planet Position Detail View
  if (selectedPlanetPosition) {
    return (
      <div style={{ padding: '1rem', maxHeight: '80vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
          <button 
            onClick={() => setSelectedPlanetPosition(null)}
            style={{
              padding: '0.5rem 1rem',
              background: '#e91e63',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              marginRight: '1rem'
            }}
          >
            ← Back
          </button>
          <h3 style={{ color: '#e91e63', fontSize: '1.3rem', margin: 0 }}>
            🪐 {selectedPlanetPosition.planet} in {selectedPlanetPosition.nakshatra}
          </h3>
        </div>
        
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '20px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '20px',
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr',
            gap: '12px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#666' }}>Planet:</span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e91e63' }}>{selectedPlanetPosition.planet}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#666' }}>Nakshatra:</span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e91e63' }}>{selectedPlanetPosition.nakshatra}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#666' }}>Pada:</span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e91e63' }}>{selectedPlanetPosition.pada}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#666' }}>Lord:</span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e91e63' }}>{selectedPlanetPosition.lord}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#666' }}>House:</span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e91e63' }}>{selectedPlanetPosition.house}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#666' }}>Longitude:</span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e91e63' }}>{selectedPlanetPosition.longitude}°</span>
            </div>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ color: '#ff6f00', fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>🌟 Planetary Significance</h4>
            <PlanetarySignificance 
              planet={selectedPlanetPosition.planet}
              nakshatra={selectedPlanetPosition.nakshatra}
              house={selectedPlanetPosition.house}
            />
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ color: '#ff6f00', fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>📖 Nakshatra Overview</h4>
            <p style={{ fontSize: '15px', lineHeight: '24px', color: '#333', textAlign: 'justify' }}>
              {nakshatras.find(n => n.name === selectedPlanetPosition.nakshatra)?.description}
            </p>
          </div>
          
          <div>
            <h4 style={{ color: '#ff6f00', fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>🎯 Key Influences</h4>
            <div style={{ fontSize: '15px', lineHeight: '24px', color: '#333' }}>
              <p>• <strong>Nakshatra Lord:</strong> {selectedPlanetPosition.lord} influences this placement</p>
              <p>• <strong>Pada {selectedPlanetPosition.pada}:</strong> Specific sub-division effects</p>
              <p>• <strong>Planetary Combination:</strong> Creates unique life experiences</p>
              <p>• <strong>Life Areas:</strong> Affects personality, career, and relationships</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Nakshatra Detail View
  if (selectedNakshatra) {
    return (
      <div style={{ padding: '1rem', maxHeight: '80vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
          <button 
            onClick={() => setSelectedNakshatra(null)}
            style={{
              padding: '0.5rem 1rem',
              background: '#e91e63',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              marginRight: '1rem'
            }}
          >
            ← Back
          </button>
          <h3 style={{ color: '#e91e63', fontSize: '1.3rem', margin: 0 }}>
            🌟 {selectedNakshatra.name} Nakshatra
          </h3>
        </div>
        
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '20px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '20px',
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr',
            gap: '12px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#666' }}>Lord:</span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e91e63' }}>{selectedNakshatra.lord}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#666' }}>Deity:</span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e91e63' }}>{selectedNakshatra.deity}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#666' }}>Nature:</span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e91e63' }}>{selectedNakshatra.nature}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#666' }}>Guna:</span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e91e63' }}>{selectedNakshatra.guna}</span>
            </div>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ color: '#ff6f00', fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>📖 Description</h4>
            <p style={{ fontSize: '15px', lineHeight: '24px', color: '#333', textAlign: 'justify' }}>
              {selectedNakshatra.description}
            </p>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ color: '#ff6f00', fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>✨ Characteristics</h4>
            <p style={{ fontSize: '15px', lineHeight: '24px', color: '#333', textAlign: 'justify' }}>
              {selectedNakshatra.characteristics}
            </p>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ color: '#22c55e', fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>✅ Positive Traits</h4>
            <p style={{ fontSize: '15px', lineHeight: '24px', color: '#333', textAlign: 'justify' }}>
              {selectedNakshatra.positive_traits}
            </p>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ color: '#ef4444', fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>⚠️ Negative Traits</h4>
            <p style={{ fontSize: '15px', lineHeight: '24px', color: '#333', textAlign: 'justify' }}>
              {selectedNakshatra.negative_traits}
            </p>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ color: '#ff6f00', fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>💼 Career Options</h4>
            <p style={{ fontSize: '15px', lineHeight: '24px', color: '#333', textAlign: 'justify' }}>
              {selectedNakshatra.careers}
            </p>
          </div>
          
          <div>
            <h4 style={{ color: '#ff6f00', fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>🤝 Compatibility</h4>
            <p style={{ fontSize: '15px', lineHeight: '24px', color: '#333', textAlign: 'justify' }}>
              {selectedNakshatra.compatibility}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ fontSize: '18px', color: '#e91e63' }}>Loading Nakshatra details...</div>
      </div>
    );
  }
  
  // Main View with Tabs
  return (
    <div style={{ padding: '1rem', maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ color: '#e91e63', marginBottom: '1rem', fontSize: '1.4rem', textAlign: 'center' }}>
        🌟 Nakshatra Analysis
      </h3>
      
      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        marginBottom: '1.5rem',
        borderBottom: '2px solid #f0f0f0',
        gap: '0'
      }}>
        <button
          onClick={() => setActiveTab('planets')}
          style={{
            flex: 1,
            padding: '12px 16px',
            border: 'none',
            background: activeTab === 'planets' ? '#e91e63' : 'transparent',
            color: activeTab === 'planets' ? 'white' : '#666',
            fontSize: '16px',
            fontWeight: '600',
            cursor: 'pointer',
            borderRadius: '8px 8px 0 0',
            borderBottom: activeTab === 'planets' ? '3px solid #e91e63' : '3px solid transparent',
            transition: 'all 0.3s ease'
          }}
        >
          🪐 Your Planets ({planetaryPositions.length})
        </button>
        <button
          onClick={() => setActiveTab('nakshatras')}
          style={{
            flex: 1,
            padding: '12px 16px',
            border: 'none',
            background: activeTab === 'nakshatras' ? '#e91e63' : 'transparent',
            color: activeTab === 'nakshatras' ? 'white' : '#666',
            fontSize: '16px',
            fontWeight: '600',
            cursor: 'pointer',
            borderRadius: '8px 8px 0 0',
            borderBottom: activeTab === 'nakshatras' ? '3px solid #e91e63' : '3px solid transparent',
            transition: 'all 0.3s ease'
          }}
        >
          📚 All Nakshatras (27)
        </button>
      </div>
      
      {/* Tab Content */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {activeTab === 'planets' && planetaryPositions.length > 0 && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '12px'
          }}>
            {planetaryPositions.map((pos, index) => (
              <div 
                key={pos.planet} 
                style={{
                  backgroundColor: 'white',
                  borderRadius: '12px',
                  padding: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  borderLeft: '4px solid #e91e63',
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s'
                }}
                onClick={() => setSelectedPlanetPosition(pos)}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#e91e63', marginBottom: '4px' }}>
                    {pos.planet}
                  </div>
                  <div style={{ fontSize: '15px', color: '#0066cc', marginBottom: '4px' }}>
                    {pos.nakshatra} - Pada {pos.pada}
                  </div>
                  <div style={{ fontSize: '13px', color: '#666' }}>
                    Lord: {pos.lord}
                  </div>
                </div>
                <div style={{ fontSize: '24px', color: '#e91e63', fontWeight: 'bold' }}>
                  →
                </div>
              </div>
            ))}
          </div>
        )}
        
        {activeTab === 'nakshatras' && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '12px'
          }}>
            {nakshatras.map((nak, index) => (
              <div key={nak.name} 
                   onClick={() => setSelectedNakshatra(nak)}
                   style={{
                     backgroundColor: 'white',
                     borderRadius: '12px',
                     padding: '16px',
                     boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                     borderLeft: '4px solid #ff6f00',
                     cursor: 'pointer',
                     transition: 'transform 0.2s, box-shadow 0.2s'
                   }}
                   onMouseEnter={(e) => {
                     e.target.style.transform = 'translateY(-2px)';
                     e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                   }}
                   onMouseLeave={(e) => {
                     e.target.style.transform = 'translateY(0)';
                     e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                   }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ fontSize: '17px', fontWeight: 'bold', color: '#e91e63', flex: 1 }}>
                    {index + 1}. {nak.name}
                  </div>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#ff6f00',
                    backgroundColor: '#fff8e1',
                    paddingLeft: '10px',
                    paddingRight: '10px',
                    paddingTop: '4px',
                    paddingBottom: '4px',
                    borderRadius: '6px'
                  }}>
                    {nak.lord}
                  </div>
                </div>
                <div style={{ fontSize: '14px', color: '#666', marginBottom: '6px' }}>
                  {((index * 13.33).toFixed(1))}° - {(((index + 1) * 13.33).toFixed(1))}°
                </div>
                <div style={{ fontSize: '13px', color: '#0066cc', fontStyle: 'italic' }}>
                  Deity: {nak.deity}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NakshatrasTab;