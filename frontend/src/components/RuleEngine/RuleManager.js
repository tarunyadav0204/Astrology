import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/apiService';

const RuleManager = () => {
  const [rules, setRules] = useState([]);
  const [selectedRule, setSelectedRule] = useState(null);
  const [showEditor, setShowEditor] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [activeView, setActiveView] = useState('manage');
  const [ruleType, setRuleType] = useState('event'); // 'event' or 'daily'
  const [dailyRules, setDailyRules] = useState([]);

  useEffect(() => {
    if (ruleType === 'event') {
      loadRules();
    } else {
      loadDailyRules();
    }
  }, [ruleType]);

  const loadRules = async () => {
    try {
      const response = await apiService.getRules();
      setRules(response);
    } catch (error) {
      console.error('Failed to load rules:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const loadDailyRules = async () => {
    setLoading(true);
    try {
      const response = await apiService.getDailyPredictionRules();
      setDailyRules(response.rules);
    } catch (error) {
      console.error('Failed to load daily rules:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setSearchLoading(true);
    try {
      const results = await apiService.searchRules(searchQuery);
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleCreateRule = () => {
    setSelectedRule({
      id: '',
      event_type: '',
      primary_karaka: 'Saturn',
      secondary_karakas: [],
      house_significations: [],
      activation_methods: [],
      transit_triggers: [],
      orb_settings: { conjunction: 3.0, aspect: 5.0 },
      weightage_factors: {},
      classical_references: [],
      is_active: true
    });
    setShowEditor(true);
  };

  const handleEditRule = (rule) => {
    setSelectedRule(rule);
    setShowEditor(true);
  };

  const handleDeleteRule = async (ruleId) => {
    if (window.confirm('Are you sure you want to delete this rule?')) {
      try {
        await apiService.deleteRule(ruleId);
        loadRules();
      } catch (error) {
        console.error('Failed to delete rule:', error);
      }
    }
  };
  
  const handleCreateDailyRule = () => {
    setSelectedRule({
      id: '',
      rule_type: 'general',
      conditions: {},
      prediction_template: '',
      confidence_base: 50,
      life_areas: [],
      timing_advice: '',
      colors: [],
      is_active: true
    });
    setShowEditor(true);
  };
  
  const handleEditDailyRule = (rule) => {
    setSelectedRule(rule);
    setShowEditor(true);
  };
  
  const handleDeleteDailyRule = async (ruleId) => {
    if (window.confirm('Are you sure you want to delete this daily rule?')) {
      try {
        await apiService.deleteDailyPredictionRule(ruleId);
        loadDailyRules();
      } catch (error) {
        console.error('Failed to delete daily rule:', error);
      }
    }
  };

  if (loading) return <div>Loading rules...</div>;

  return (
    <div style={{ padding: window.innerWidth <= 768 ? '10px' : '20px', fontSize: window.innerWidth <= 768 ? '14px' : '16px' }}>
      <div style={{ 
        display: 'flex', 
        flexDirection: window.innerWidth <= 768 ? 'column' : 'row',
        justifyContent: 'space-between', 
        alignItems: window.innerWidth <= 768 ? 'stretch' : 'center', 
        marginBottom: '20px',
        gap: '10px'
      }}>
        <h2 style={{ margin: 0, fontSize: window.innerWidth <= 768 ? '1.2rem' : '1.5rem' }}>Rule Engine Management</h2>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
          <button
            onClick={() => setRuleType('event')}
            style={{
              padding: '6px 12px',
              backgroundColor: ruleType === 'event' ? '#ff9800' : 'transparent',
              color: ruleType === 'event' ? 'white' : '#ff9800',
              border: '2px solid #ff9800',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: '600'
            }}
          >
            Event Rules
          </button>
          <button
            onClick={() => setRuleType('daily')}
            style={{
              padding: '6px 12px',
              backgroundColor: ruleType === 'daily' ? '#ff9800' : 'transparent',
              color: ruleType === 'daily' ? 'white' : '#ff9800',
              border: '2px solid #ff9800',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: '600'
            }}
          >
            Daily Prediction Rules
          </button>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => setActiveView('manage')}
            style={{
              padding: '8px 16px',
              backgroundColor: activeView === 'manage' ? '#e91e63' : 'transparent',
              color: activeView === 'manage' ? 'white' : '#e91e63',
              border: '2px solid #e91e63',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            Manage Rules
          </button>
          <button
            onClick={() => setActiveView('search')}
            style={{
              padding: '8px 16px',
              backgroundColor: activeView === 'search' ? '#e91e63' : 'transparent',
              color: activeView === 'search' ? 'white' : '#e91e63',
              border: '2px solid #e91e63',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            Search Rules
          </button>
          {activeView === 'manage' && (
            <button
              onClick={ruleType === 'event' ? handleCreateRule : handleCreateDailyRule}
              style={{
                padding: '8px 16px',
                backgroundColor: '#4caf50',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              Create New {ruleType === 'event' ? 'Event' : 'Daily'} Rule
            </button>
          )}
        </div>
      </div>

      {activeView === 'manage' ? (
        <div style={{ display: 'grid', gap: '15px' }}>
          {ruleType === 'event' ? (
            rules.map(rule => (
              <div key={rule.id} style={{
                border: '1px solid #ddd',
                borderRadius: '8px',
                padding: '15px',
                background: 'white'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div>
                    <h3 style={{ margin: '0 0 10px 0', color: '#e91e63' }}>
                      {rule.event_type.replace('_', ' ').toUpperCase()}
                    </h3>
                    <p><strong>Primary Karaka:</strong> {rule.primary_karaka}</p>
                    <p><strong>Houses:</strong> {rule.house_significations.join(', ')}</p>
                    <p><strong>Status:</strong> {rule.is_active ? '✅ Active' : '❌ Inactive'}</p>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      onClick={() => handleEditRule(rule)}
                      style={{
                        padding: '5px 10px',
                        background: '#2196f3',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer'
                      }}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteRule(rule.id)}
                      style={{
                        padding: '5px 10px',
                        background: '#f44336',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer'
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            dailyRules.map(rule => (
              <div key={rule.id} style={{
                border: '1px solid #ddd',
                borderRadius: '8px',
                padding: '15px',
                background: 'white'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div>
                    <h3 style={{ margin: '0 0 10px 0', color: '#e91e63' }}>
                      {rule.id.replace('_', ' ').toUpperCase()}
                    </h3>
                    <p><strong>Type:</strong> {rule.rule_type.replace('_', ' ')}</p>
                    <p><strong>Confidence:</strong> {rule.confidence_base}%</p>
                    <p><strong>Prediction:</strong> {rule.prediction_template.substring(0, 100)}...</p>
                    <p><strong>Status:</strong> {rule.is_active ? '✅ Active' : '❌ Inactive'}</p>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      onClick={() => handleEditDailyRule(rule)}
                      style={{
                        padding: '5px 10px',
                        background: '#2196f3',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer'
                      }}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteDailyRule(rule.id)}
                      style={{
                        padding: '5px 10px',
                        background: '#f44336',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer'
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        <div>
          <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
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
              disabled={searchLoading || !searchQuery.trim()}
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
              {searchLoading ? 'Searching...' : 'Search'}
            </button>
          </div>

          {searchResults && (
            <div style={{ display: 'grid', gap: '20px' }}>
              {searchResults.rules.length > 0 && (
                <div>
                  <h3 style={{ color: '#333', marginBottom: '15px' }}>Rules ({searchResults.rules.length})</h3>
                  <div style={{ display: 'grid', gap: '15px' }}>
                    {searchResults.rules.map((rule) => (
                      <div key={rule.id} style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '15px', backgroundColor: '#f9f9f9' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                          <h4 style={{ color: '#e91e63', margin: 0 }}>{rule.event_type.replace(/_/g, ' ').toUpperCase()}</h4>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                              onClick={() => handleEditRule(rule)}
                              style={{
                                padding: '4px 8px',
                                backgroundColor: '#2196f3',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '12px'
                              }}
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleDeleteRule(rule.id)}
                              style={{
                                padding: '4px 8px',
                                backgroundColor: '#f44336',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '12px'
                              }}
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', fontSize: '13px' }}>
                          <div><strong>Primary Karaka:</strong> {rule.primary_karaka}</div>
                          <div><strong>Houses:</strong> {rule.house_significations.join(', ')}</div>
                          {rule.secondary_karakas && <div><strong>Secondary Karakas:</strong> {rule.secondary_karakas.join(', ')}</div>}
                          {rule.body_parts && <div><strong>Body Parts:</strong> {rule.body_parts.join(', ')}</div>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {searchResults.house_significations.length > 0 && (
                <div>
                  <h3 style={{ color: '#333', marginBottom: '15px' }}>House Significations ({searchResults.house_significations.length})</h3>
                  <div style={{ display: 'grid', gap: '15px' }}>
                    {searchResults.house_significations.map((house) => (
                      <div key={house.house} style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '15px', backgroundColor: '#f0f8ff' }}>
                        <h4 style={{ color: '#2196f3', margin: '0 0 10px 0' }}>House {house.house}</h4>
                        {typeof house.significations === 'object' ? (
                          <div style={{ fontSize: '13px' }}>
                            <div><strong>Primary:</strong> {house.significations.primary.join(', ')}</div>
                            <div><strong>Secondary:</strong> {house.significations.secondary.join(', ')}</div>
                            <div><strong>Tertiary:</strong> {house.significations.tertiary.join(', ')}</div>
                          </div>
                        ) : (
                          <div style={{ fontSize: '13px' }}>{house.significations.join(', ')}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {searchResults.planetary_karakas.length > 0 && (
                <div>
                  <h3 style={{ color: '#333', marginBottom: '15px' }}>Planetary Karakas ({searchResults.planetary_karakas.length})</h3>
                  <div style={{ display: 'grid', gap: '15px' }}>
                    {searchResults.planetary_karakas.map((planet) => (
                      <div key={planet.planet} style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '15px', backgroundColor: '#fff8e1' }}>
                        <h4 style={{ color: '#ff9800', margin: '0 0 10px 0' }}>{planet.planet}</h4>
                        <div style={{ fontSize: '13px' }}><strong>Karakas:</strong> {planet.karakas.join(', ')}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {searchResults.body_parts.length > 0 && (
                <div>
                  <h3 style={{ color: '#333', marginBottom: '15px' }}>Body Parts ({searchResults.body_parts.length})</h3>
                  <div style={{ display: 'grid', gap: '15px' }}>
                    {searchResults.body_parts.map((house) => (
                      <div key={house.house} style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '15px', backgroundColor: '#f3e5f5' }}>
                        <h4 style={{ color: '#9c27b0', margin: '0 0 10px 0' }}>House {house.house} - Body Parts</h4>
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

              {searchResults.rules.length === 0 && searchResults.house_significations.length === 0 && searchResults.planetary_karakas.length === 0 && searchResults.body_parts.length === 0 && (
                <div style={{ textAlign: 'center', padding: '40px', color: '#666', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
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
      )}

      {showEditor && (
        <RuleEditor
          rule={selectedRule}
          ruleType={ruleType}
          onSave={() => {
            setShowEditor(false);
            if (ruleType === 'event') {
              loadRules();
            } else {
              loadDailyRules();
            }
            if (searchResults) {
              handleSearch();
            }
          }}
          onCancel={() => setShowEditor(false)}
        />
      )}
    </div>
  );
};

const RuleEditor = ({ rule, ruleType, onSave, onCancel }) => {
  const [formData, setFormData] = useState(rule);

  const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
  const houses = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
  const activationMethods = [
    'planet_in_house',
    'planet_aspects_house',
    'planet_owns_house',
    'planet_aspects_karaka',
    'planet_conjunct_karaka'
  ];
  const transitTriggers = [
    'transit_over_natal_position',
    'transit_aspects_natal_position',
    'transit_over_house_cusp'
  ];

  const handleSave = async () => {
    try {
      if (ruleType === 'event') {
        if (formData.id) {
          await apiService.updateRule(formData.id, formData);
        } else {
          formData.id = `${formData.event_type}_rule`;
          await apiService.createRule(formData);
        }
      } else {
        if (formData.id && formData.created_at) {
          await apiService.updateDailyPredictionRule(formData.id, formData);
        } else {
          formData.id = `${formData.rule_type}_${Date.now()}`;
          await apiService.createDailyPredictionRule(formData);
        }
      }
      onSave();
    } catch (error) {
      console.error('Failed to save rule:', error);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '10px',
        width: '80%',
        maxWidth: '600px',
        maxHeight: '80vh',
        overflow: 'auto'
      }}>
        <h3>{ruleType === 'event' ? 'Event' : 'Daily Prediction'} Rule Editor</h3>
        
        {ruleType === 'event' ? (
          <>
            <div style={{ marginBottom: '15px' }}>
              <label>Event Type:</label>
              <input
                type="text"
                value={formData.event_type}
                onChange={(e) => setFormData({...formData, event_type: e.target.value})}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label>Primary Karaka:</label>
              <select
                value={formData.primary_karaka}
                onChange={(e) => setFormData({...formData, primary_karaka: e.target.value})}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              >
                {planets.map(planet => (
                  <option key={planet} value={planet}>{planet}</option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label>House Significations:</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '5px' }}>
                {houses.map(house => (
                  <label key={house} style={{ display: 'flex', alignItems: 'center' }}>
                    <input
                      type="checkbox"
                      checked={formData.house_significations.includes(house)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData({
                            ...formData,
                            house_significations: [...formData.house_significations, house]
                          });
                        } else {
                          setFormData({
                            ...formData,
                            house_significations: formData.house_significations.filter(h => h !== house)
                          });
                        }
                      }}
                    />
                    <span style={{ marginLeft: '5px' }}>{house}</span>
                  </label>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label>Activation Methods:</label>
              <div style={{ marginTop: '5px' }}>
                {activationMethods.map(method => (
                  <label key={method} style={{ display: 'block', marginBottom: '5px' }}>
                    <input
                      type="checkbox"
                      checked={formData.activation_methods.includes(method)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData({
                            ...formData,
                            activation_methods: [...formData.activation_methods, method]
                          });
                        } else {
                          setFormData({
                            ...formData,
                            activation_methods: formData.activation_methods.filter(m => m !== method)
                          });
                        }
                      }}
                    />
                    <span style={{ marginLeft: '5px' }}>{method.replace(/_/g, ' ')}</span>
                  </label>
                ))}
              </div>
            </div>
          </>
        ) : (
          <>
            <div style={{ marginBottom: '15px' }}>
              <label>Rule Type:</label>
              <select
                value={formData.rule_type}
                onChange={(e) => setFormData({...formData, rule_type: e.target.value})}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              >
                <option value="general">General</option>
                <option value="dasha_nakshatra_combo">Dasha + Nakshatra</option>
                <option value="antar_dasha">Antar Dasha</option>
                <option value="transit_aspect">Transit Aspect</option>
                <option value="dasha_energy">Dasha Energy</option>
                <option value="moon_influence">Moon Influence</option>
              </select>
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label>Prediction Text:</label>
              <textarea
                value={formData.prediction_template}
                onChange={(e) => setFormData({...formData, prediction_template: e.target.value})}
                style={{ width: '100%', padding: '8px', marginTop: '5px', minHeight: '80px' }}
                placeholder="Enter the prediction text that will be shown to users..."
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label>Confidence Base (%):</label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.confidence_base}
                onChange={(e) => setFormData({...formData, confidence_base: parseInt(e.target.value)})}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label>Life Areas (comma-separated):</label>
              <input
                type="text"
                value={formData.life_areas.join(', ')}
                onChange={(e) => setFormData({...formData, life_areas: e.target.value.split(',').map(s => s.trim()).filter(s => s)})}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
                placeholder="relationships, career, health, wealth"
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label>Timing Advice:</label>
              <input
                type="text"
                value={formData.timing_advice}
                onChange={(e) => setFormData({...formData, timing_advice: e.target.value})}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
                placeholder="Best time: 10 AM - 2 PM"
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label>Lucky Colors (comma-separated):</label>
              <input
                type="text"
                value={formData.colors.join(', ')}
                onChange={(e) => setFormData({...formData, colors: e.target.value.split(',').map(s => s.trim()).filter(s => s)})}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
                placeholder="red, blue, green, yellow"
              />
            </div>
          </>
        )}

        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            style={{
              padding: '10px 20px',
              background: '#ccc',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            style={{
              padding: '10px 20px',
              background: '#e91e63',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            Save {ruleType === 'event' ? 'Event' : 'Daily'} Rule
          </button>
        </div>
      </div>
    </div>
  );
};

export default RuleManager;