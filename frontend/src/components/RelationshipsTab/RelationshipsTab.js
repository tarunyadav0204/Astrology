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
      case 'BF': return '#22c55e'; // Best Friend - Green
      case 'F': return '#3b82f6';  // Friend - Blue
      case 'N': return '#f59e0b';  // Neutral - Orange
      case 'E': return '#ef4444';  // Enemy - Red
      case 'GE': return '#7c2d12'; // Great Enemy - Dark Red
      case '-': return '#e5e7eb'; // Self - Gray
      default: return '#6b7280';
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
        <div style={{ overflowX: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            fontSize: '0.8rem',
            border: '1px solid #e91e63'
          }}>
            <thead>
              <tr>
                <th style={{ 
                  padding: '0.5rem', 
                  background: '#e91e63', 
                  color: 'white',
                  border: '1px solid #e91e63',
                  minWidth: '60px'
                }}></th>
                {planets.map(planet => (
                  <th key={planet} style={{ 
                    padding: '0.5rem', 
                    background: '#e91e63', 
                    color: 'white',
                    border: '1px solid #e91e63',
                    minWidth: '60px',
                    fontSize: '0.7rem'
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
                    padding: '0.5rem', 
                    background: '#e91e63', 
                    color: 'white',
                    border: '1px solid #e91e63',
                    fontWeight: '600',
                    fontSize: '0.7rem'
                  }}>
                    {planet1}
                  </td>
                  {planets.map(planet2 => {
                    const relationship = matrix[planet1]?.[planet2] || 'N';
                    return (
                      <td key={planet2} style={{ 
                        padding: '0.3rem', 
                        textAlign: 'center',
                        background: getRelationshipColor(relationship),
                        color: 'white',
                        border: '1px solid #ddd',
                        fontWeight: '600',
                        fontSize: '0.7rem'
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
        gap: '1rem', 
        marginBottom: '1rem',
        flexWrap: 'wrap',
        padding: '0.5rem',
        background: '#f8f9fa',
        borderRadius: '4px'
      }}>
        {selectedMatrix === 'fiveFold' ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#22c55e' }}></div>
              <span style={{ fontSize: '0.7rem' }}>BF - Best Friend</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#3b82f6' }}></div>
              <span style={{ fontSize: '0.7rem' }}>F - Friend</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#f59e0b' }}></div>
              <span style={{ fontSize: '0.7rem' }}>N - Neutral</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#ef4444' }}></div>
              <span style={{ fontSize: '0.7rem' }}>E - Enemy</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#7c2d12' }}></div>
              <span style={{ fontSize: '0.7rem' }}>GE - Great Enemy</span>
            </div>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#3b82f6' }}></div>
              <span style={{ fontSize: '0.7rem' }}>F - Friend</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#f59e0b' }}></div>
              <span style={{ fontSize: '0.7rem' }}>N - Neutral</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <div style={{ width: '15px', height: '15px', background: '#ef4444' }}></div>
              <span style={{ fontSize: '0.7rem' }}>E - Enemy</span>
            </div>
          </>
        )}
      </div>

      {/* Matrix Display */}
      <div style={{ 
        maxHeight: '60vh', 
        overflowY: 'auto',
        border: '1px solid #e91e63',
        borderRadius: '8px',
        padding: '1rem',
        background: 'white'
      }}>
        {selectedMatrix === 'permanent' && renderMatrix(matrices.permanent, '🤝 Permanent Friendship Matrix')}
        {selectedMatrix === 'temporal' && renderMatrix(matrices.temporal, '⏰ Temporal Friendship Matrix (Based on Chart Positions)')}
        {selectedMatrix === 'fiveFold' && renderMatrix(matrices.fiveFold, '🌟 Five Fold Friendship Matrix (Combined Result)')}
        
        <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: '#666' }}>
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