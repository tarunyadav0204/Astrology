import React, { useState } from 'react';
import { apiService } from '../../services/apiService';

const RuleSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const searchResults = await apiService.searchRules(query);
      setResults(searchResults);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2 style={{ color: '#e91e63', marginBottom: '20px' }}>Rule Engine Search</h2>
      
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Search by planet (Mars, Jupiter), house (1, 2, 3), or specification (marriage, health, wealth)..."
          style={{
            flex: 1,
            padding: '12px',
            border: '2px solid #e91e63',
            borderRadius: '8px',
            fontSize: '14px'
          }}
        />
        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          style={{
            padding: '12px 24px',
            backgroundColor: '#e91e63',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '600'
          }}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {results && (
        <div style={{ display: 'grid', gap: '20px' }}>
          {/* Rules Results */}
          {results.rules.length > 0 && (
            <div>
              <h3 style={{ color: '#333', marginBottom: '15px' }}>
                Rules ({results.rules.length})
              </h3>
              <div style={{ display: 'grid', gap: '15px' }}>
                {results.rules.map((rule) => (
                  <div
                    key={rule.id}
                    style={{
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      padding: '15px',
                      backgroundColor: '#f9f9f9'
                    }}
                  >
                    <h4 style={{ color: '#e91e63', margin: '0 0 10px 0' }}>
                      {rule.event_type.replace(/_/g, ' ').toUpperCase()}
                    </h4>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', fontSize: '13px' }}>
                      <div><strong>Primary Karaka:</strong> {rule.primary_karaka}</div>
                      <div><strong>Houses:</strong> {rule.house_significations.join(', ')}</div>
                      {rule.secondary_karakas && (
                        <div><strong>Secondary Karakas:</strong> {rule.secondary_karakas.join(', ')}</div>
                      )}
                      {rule.body_parts && (
                        <div><strong>Body Parts:</strong> {rule.body_parts.join(', ')}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* House Significations Results */}
          {results.house_significations.length > 0 && (
            <div>
              <h3 style={{ color: '#333', marginBottom: '15px' }}>
                House Significations ({results.house_significations.length})
              </h3>
              <div style={{ display: 'grid', gap: '15px' }}>
                {results.house_significations.map((house) => (
                  <div
                    key={house.house}
                    style={{
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      padding: '15px',
                      backgroundColor: '#f0f8ff'
                    }}
                  >
                    <h4 style={{ color: '#2196f3', margin: '0 0 10px 0' }}>
                      House {house.house}
                    </h4>
                    {typeof house.significations === 'object' ? (
                      <div style={{ fontSize: '13px' }}>
                        <div><strong>Primary:</strong> {house.significations.primary.join(', ')}</div>
                        <div><strong>Secondary:</strong> {house.significations.secondary.join(', ')}</div>
                        <div><strong>Tertiary:</strong> {house.significations.tertiary.join(', ')}</div>
                      </div>
                    ) : (
                      <div style={{ fontSize: '13px' }}>
                        {house.significations.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Planetary Karakas Results */}
          {results.planetary_karakas.length > 0 && (
            <div>
              <h3 style={{ color: '#333', marginBottom: '15px' }}>
                Planetary Karakas ({results.planetary_karakas.length})
              </h3>
              <div style={{ display: 'grid', gap: '15px' }}>
                {results.planetary_karakas.map((planet) => (
                  <div
                    key={planet.planet}
                    style={{
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      padding: '15px',
                      backgroundColor: '#fff8e1'
                    }}
                  >
                    <h4 style={{ color: '#ff9800', margin: '0 0 10px 0' }}>
                      {planet.planet}
                    </h4>
                    <div style={{ fontSize: '13px' }}>
                      <strong>Karakas:</strong> {planet.karakas.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Body Parts Results */}
          {results.body_parts.length > 0 && (
            <div>
              <h3 style={{ color: '#333', marginBottom: '15px' }}>
                Body Parts ({results.body_parts.length})
              </h3>
              <div style={{ display: 'grid', gap: '15px' }}>
                {results.body_parts.map((house) => (
                  <div
                    key={house.house}
                    style={{
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      padding: '15px',
                      backgroundColor: '#f3e5f5'
                    }}
                  >
                    <h4 style={{ color: '#9c27b0', margin: '0 0 10px 0' }}>
                      House {house.house} - Body Parts
                    </h4>
                    <div style={{ fontSize: '13px' }}>
                      <div><strong>Primary:</strong> {house.body_parts.primary.join(', ')}</div>
                      <div><strong>Secondary:</strong> {house.body_parts.secondary.join(', ')}</div>
                      <div><strong>Ruling Signs:</strong> {house.body_parts.ruling_signs.join(', ')}</div>
                      <div><strong>Karaka Planets:</strong> {house.body_parts.karaka_planets.join(', ')}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No Results */}
          {results.rules.length === 0 && 
           results.house_significations.length === 0 && 
           results.planetary_karakas.length === 0 && 
           results.body_parts.length === 0 && (
            <div style={{ 
              textAlign: 'center', 
              padding: '40px', 
              color: '#666',
              backgroundColor: '#f5f5f5',
              borderRadius: '8px'
            }}>
              <h3>No results found</h3>
              <p>Try searching for:</p>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                <li>• Planet names: Mars, Jupiter, Venus, Saturn</li>
                <li>• House numbers: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12</li>
                <li>• Life areas: marriage, health, wealth, career</li>
                <li>• Body parts: heart, head, teeth, liver</li>
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RuleSearch;