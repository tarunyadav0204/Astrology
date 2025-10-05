import React, { useState, useEffect } from 'react';

const RelationshipsTab = ({ chartData, birthData }) => {
  const [selectedMatrix, setSelectedMatrix] = useState('permanent');
  const [loading, setLoading] = useState(true);
  const [matrices, setMatrices] = useState(null);

  const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

  useEffect(() => {
    if (chartData && birthData) {
      calculateRelationshipMatrices();
    }
  }, [chartData, birthData]);

  const calculateRelationshipMatrices = () => {
    setLoading(true);
    
    if (!chartData?.planets) {
      setMatrices(null);
      setLoading(false);
      return;
    }

    const permanent = getPermanentFriendships();
    const temporal = getTemporalFriendships();
    const fiveFold = getFiveFoldFriendships(permanent, temporal);

    setMatrices({ permanent, temporal, fiveFold });
    setLoading(false);
  };

  const getPermanentFriendships = () => {
    return {
      'Sun': { 'Moon': 'F', 'Mars': 'F', 'Mercury': 'N', 'Jupiter': 'F', 'Venus': 'E', 'Saturn': 'E' },
      'Moon': { 'Sun': 'F', 'Mars': 'N', 'Mercury': 'F', 'Jupiter': 'N', 'Venus': 'N', 'Saturn': 'N' },
      'Mars': { 'Sun': 'F', 'Moon': 'N', 'Mercury': 'N', 'Jupiter': 'F', 'Venus': 'N', 'Saturn': 'E' },
      'Mercury': { 'Sun': 'F', 'Moon': 'E', 'Mars': 'N', 'Jupiter': 'N', 'Venus': 'F', 'Saturn': 'N' },
      'Jupiter': { 'Sun': 'F', 'Moon': 'N', 'Mars': 'F', 'Mercury': 'E', 'Venus': 'E', 'Saturn': 'N' },
      'Venus': { 'Sun': 'E', 'Moon': 'E', 'Mars': 'E', 'Mercury': 'F', 'Jupiter': 'N', 'Saturn': 'F' },
      'Saturn': { 'Sun': 'E', 'Moon': 'E', 'Mars': 'E', 'Mercury': 'F', 'Jupiter': 'E', 'Venus': 'F' }
    };
  };

  const getTemporalFriendships = () => {
    const temporal = {};
    const chartPlanets = chartData.planets;
    
    planets.forEach(planet1 => {
      temporal[planet1] = {};
      
      planets.forEach(planet2 => {
        if (planet1 === planet2) {
          temporal[planet1][planet2] = '-';
          return;
        }
        
        if (!chartPlanets[planet1] || !chartPlanets[planet2]) {
          temporal[planet1][planet2] = 'N';
          return;
        }
        
        const planet1Sign = chartPlanets[planet1].sign;
        const planet2Sign = chartPlanets[planet2].sign;
        
        // Calculate house position of planet2 from planet1
        let houseFromPlanet1 = planet2Sign - planet1Sign + 1;
        if (houseFromPlanet1 <= 0) houseFromPlanet1 += 12;
        
        // Temporal friendship: 2,3,4,10,11,12 are friends, others are enemies
        const friendHouses = [2, 3, 4, 10, 11, 12];
        temporal[planet1][planet2] = friendHouses.includes(houseFromPlanet1) ? 'F' : 'E';
      });
    });
    
    return temporal;
  };

  const getFiveFoldFriendships = (permanent, temporal) => {
    const fiveFold = {};
    
    planets.forEach(planet1 => {
      fiveFold[planet1] = {};
      
      planets.forEach(planet2 => {
        if (planet1 === planet2) {
          fiveFold[planet1][planet2] = '-';
          return;
        }
        
        const perm = permanent[planet1][planet2];
        const temp = temporal[planet1][planet2];
        
        // Five-fold relationship calculation
        if (perm === 'F' && temp === 'F') fiveFold[planet1][planet2] = 'BF'; // Best Friend
        else if (perm === 'F' && temp === 'E') fiveFold[planet1][planet2] = 'N';  // Neutral
        else if (perm === 'F' && temp === 'N') fiveFold[planet1][planet2] = 'F';  // Friend
        else if (perm === 'E' && temp === 'F') fiveFold[planet1][planet2] = 'N';  // Neutral
        else if (perm === 'E' && temp === 'E') fiveFold[planet1][planet2] = 'GE'; // Great Enemy
        else if (perm === 'E' && temp === 'N') fiveFold[planet1][planet2] = 'E';  // Enemy
        else if (perm === 'N' && temp === 'F') fiveFold[planet1][planet2] = 'F';  // Friend
        else if (perm === 'N' && temp === 'E') fiveFold[planet1][planet2] = 'E';  // Enemy
        else fiveFold[planet1][planet2] = 'N'; // Neutral
      });
    });
    
    return fiveFold;
  };

  const getRelationshipColor = (relationship) => {
    switch (relationship) {
      case 'BF': return '#d1fae5'; // Best Friend - Light Green
      case 'F': return '#dbeafe';  // Friend - Light Blue
      case 'N': return '#fef3c7';  // Neutral - Light Yellow
      case 'E': return '#fee2e2';  // Enemy - Light Red
      case 'GE': return '#fecaca'; // Great Enemy - Light Pink
      case '-': return '#f3f4f6'; // Self - Light Gray
      default: return '#f9fafb';
    }
  };

  const getRelationshipTextColor = (relationship) => {
    switch (relationship) {
      case 'BF': return '#065f46'; // Best Friend - Dark Green
      case 'F': return '#1e40af';  // Friend - Dark Blue
      case 'N': return '#92400e';  // Neutral - Dark Yellow
      case 'E': return '#991b1b';  // Enemy - Dark Red
      case 'GE': return '#7f1d1d'; // Great Enemy - Darker Red
      case '-': return '#6b7280'; // Self - Gray
      default: return '#374151';
    }
  };

  const getRelationshipText = (relationship) => {
    switch (relationship) {
      case 'BF': return 'Best Friend';
      case 'F': return 'Friend';
      case 'N': return 'Neutral';
      case 'E': return 'Enemy';
      case 'GE': return 'Great Enemy';
      case '-': return 'Self';
      default: return 'Unknown';
    }
  };

  const renderMatrix = (matrix, title) => {
    return (
      <div style={{ marginBottom: '2rem' }}>
        <h4 style={{ color: '#e91e63', marginBottom: '1rem', fontSize: '1rem' }}>
          {title}
        </h4>
        <div style={{ 
          overflowX: 'auto',
          WebkitOverflowScrolling: 'touch'
        }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            fontSize: window.innerWidth <= 768 ? '0.65rem' : '0.8rem',
            border: '1px solid #e5e7eb',
            minWidth: window.innerWidth <= 768 ? '400px' : 'auto'
          }}>
            <thead>
              <tr>
                <th style={{ 
                  padding: window.innerWidth <= 768 ? '0.3rem' : '0.5rem', 
                  background: 'white', 
                  color: '#e91e63',
                  border: '1px solid #e5e7eb',
                  minWidth: window.innerWidth <= 768 ? '45px' : '60px',
                  fontWeight: '600'
                }}></th>
                {planets.map(planet => (
                  <th key={planet} style={{ 
                    padding: window.innerWidth <= 768 ? '0.3rem' : '0.5rem', 
                    background: 'white', 
                    color: '#e91e63',
                    border: '1px solid #e5e7eb',
                    minWidth: window.innerWidth <= 768 ? '45px' : '60px',
                    fontSize: window.innerWidth <= 768 ? '0.6rem' : '0.7rem',
                    fontWeight: '600'
                  }}>
                    {planet}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {planets.map(planet1 => (
                <tr key={planet1}>
                  <td style={{ 
                    padding: window.innerWidth <= 768 ? '0.3rem' : '0.5rem', 
                    background: 'white', 
                    color: '#e91e63',
                    border: '1px solid #e5e7eb',
                    fontWeight: '600',
                    fontSize: window.innerWidth <= 768 ? '0.6rem' : '0.7rem'
                  }}>
                    {planet1}
                  </td>
                  {planets.map(planet2 => {
                    const relationship = matrix[planet1]?.[planet2] || 'N';
                    return (
                      <td key={planet2} style={{ 
                        padding: window.innerWidth <= 768 ? '0.2rem' : '0.3rem', 
                        textAlign: 'center',
                        background: getRelationshipColor(relationship),
                        color: getRelationshipTextColor(relationship),
                        border: '1px solid #e5e7eb',
                        fontWeight: '600',
                        fontSize: window.innerWidth <= 768 ? '0.6rem' : '0.7rem'
                      }}>
                        {relationship}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '2rem' }}>Calculating Friendship Matrices...</div>;
  }

  if (!matrices) {
    return <div style={{ textAlign: 'center', padding: '2rem' }}>Unable to calculate relationships. Please check chart data.</div>;
  }

  return (
    <div style={{ height: '100%' }}>
      {/* Matrix Selection Tabs */}
      <div style={{ 
        display: 'flex', 
        gap: '0.5rem', 
        marginBottom: '1rem',
        borderBottom: '1px solid #e91e63'
      }}>
        {[
          { key: 'permanent', label: 'Permanent Friendship' },
          { key: 'temporal', label: 'Temporal Friendship' },
          { key: 'fiveFold', label: 'Five Fold Friendship' }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setSelectedMatrix(tab.key)}
            style={{
              padding: '0.5rem 1rem',
              background: selectedMatrix === tab.key ? '#e91e63' : 'transparent',
              color: selectedMatrix === tab.key ? 'white' : '#e91e63',
              border: '1px solid #e91e63',
              borderBottom: 'none',
              borderRadius: '8px 8px 0 0',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: '600'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Legend */}
      <div style={{ 
        display: 'flex', 
        gap: window.innerWidth <= 768 ? '0.5rem' : '1rem', 
        marginBottom: '1rem',
        flexWrap: 'wrap',
        padding: window.innerWidth <= 768 ? '0.3rem' : '0.5rem',
        background: '#f8f9fa',
        borderRadius: '4px'
      }}>
        {selectedMatrix === 'fiveFold' ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#d1fae5', border: '1px solid #065f46' }}></div>
              <span style={{ fontSize: window.innerWidth <= 768 ? '0.65rem' : '0.7rem' }}>BF - Best Friend</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#dbeafe', border: '1px solid #1e40af' }}></div>
              <span style={{ fontSize: '0.7rem' }}>F - Friend</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#fef3c7', border: '1px solid #92400e' }}></div>
              <span style={{ fontSize: '0.7rem' }}>N - Neutral</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#fee2e2', border: '1px solid #991b1b' }}></div>
              <span style={{ fontSize: '0.7rem' }}>E - Enemy</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#fecaca', border: '1px solid #7f1d1d' }}></div>
              <span style={{ fontSize: '0.7rem' }}>GE - Great Enemy</span>
            </div>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#dbeafe', border: '1px solid #1e40af' }}></div>
              <span style={{ fontSize: '0.7rem' }}>F - Friend</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#fef3c7', border: '1px solid #92400e' }}></div>
              <span style={{ fontSize: '0.7rem' }}>N - Neutral</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#fee2e2', border: '1px solid #991b1b' }}></div>
              <span style={{ fontSize: '0.7rem' }}>E - Enemy</span>
            </div>
          </>
        )}
      </div>

      {/* Matrix Display */}
      <div style={{ 
        maxHeight: window.innerWidth <= 768 ? '65vh' : '60vh', 
        overflowY: 'auto',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: window.innerWidth <= 768 ? '0.5rem' : '1rem',
        background: 'white',
        WebkitOverflowScrolling: 'touch'
      }}>
        {selectedMatrix === 'permanent' && renderMatrix(matrices.permanent, '🤝 Permanent Friendship Matrix')}
        {selectedMatrix === 'temporal' && renderMatrix(matrices.temporal, '⏰ Temporal Friendship Matrix (Based on Chart Positions)')}
        {selectedMatrix === 'fiveFold' && renderMatrix(matrices.fiveFold, '🌟 Five Fold Friendship Matrix (Combined Result)')}
        
        <div style={{ marginTop: '1rem', fontSize: window.innerWidth <= 768 ? '0.75rem' : '0.8rem', color: '#666' }}>
          <p><strong>Note:</strong> Relationships are shown from row planet to column planet.</p>
          {selectedMatrix === 'temporal' && (
            <p><strong>Temporal Friendship:</strong> Based on house positions in the birth chart. Houses 2,3,4,10,11,12 from a planet are friends.</p>
          )}
          {selectedMatrix === 'fiveFold' && (
            <p><strong>Five Fold Friendship:</strong> Combines permanent and temporal relationships to give the final compound relationship.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default RelationshipsTab;