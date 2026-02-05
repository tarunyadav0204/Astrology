import React, { useState, useEffect } from 'react';
import './ChatConfig.css';

const ChatConfig = () => {
  const [categories, setCategories] = useState([]);
  const [tiers, setTiers] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('career');
  const [selectedTier, setSelectedTier] = useState('normal');
  const [activeTab, setActiveTab] = useState('context');
  const [layers, setLayers] = useState([]);
  const [charts, setCharts] = useState([]);
  const [instructionModules, setInstructionModules] = useState([]);
  const [categoryLayers, setCategoryLayers] = useState([]);
  const [categoryCharts, setCategoryCharts] = useState([]);
  const [categoryModules, setCategoryModules] = useState([]);
  const [tierContextConfig, setTierContextConfig] = useState({});
  const [transitLimits, setTransitLimits] = useState({});
  const [sizeInfo, setSizeInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedModule, setExpandedModule] = useState(null);
  const [editingText, setEditingText] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveNotification, setSaveNotification] = useState('');

  useEffect(() => {
    fetchCategories();
    fetchTiers();
    fetchLayers();
    fetchCharts();
    fetchInstructionModules();
  }, []);

  useEffect(() => {
    if (selectedCategory && selectedTier) {
      fetchCategoryConfig();
    }
  }, [selectedCategory, selectedTier]);

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/admin/chat-config/categories', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setCategories(data.categories || []);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchTiers = async () => {
    try {
      const response = await fetch('/api/admin/chat-config/tiers', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setTiers(data.tiers || []);
    } catch (error) {
      console.error('Error fetching tiers:', error);
    }
  };

  const fetchLayers = async () => {
    try {
      const response = await fetch('/api/admin/chat-config/layers', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setLayers(data.layers || []);
    } catch (error) {
      console.error('Error fetching layers:', error);
    }
  };

  const fetchInstructionModules = async () => {
    try {
      const response = await fetch('/api/admin/chat-config/instruction-modules', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setInstructionModules(data.modules || []);
    } catch (error) {
      console.error('Error fetching instruction modules:', error);
    }
  };

  const fetchCharts = async () => {
    try {
      const response = await fetch('/api/admin/chat-config/charts', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setCharts(data.charts || []);
    } catch (error) {
      console.error('Error fetching charts:', error);
    }
  };

  const fetchCategoryConfig = async () => {
    setLoading(true);
    try {
      const [layersRes, chartsRes, modulesRes, configRes] = await Promise.all([
        fetch(`/api/admin/chat-config/category/${selectedCategory}/layers?tier_key=${selectedTier}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(`/api/admin/chat-config/category/${selectedCategory}/charts?tier_key=${selectedTier}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(`/api/admin/chat-config/category/${selectedCategory}/instruction-modules?tier_key=${selectedTier}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(`/api/admin/chat-config/category/${selectedCategory}?tier_key=${selectedTier}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      const layersData = await layersRes.json();
      const chartsData = await chartsRes.json();
      const modulesData = await modulesRes.json();
      const configData = await configRes.json();

      setCategoryLayers(layersData.layers || []);
      setCategoryCharts(chartsData.charts || []);
      setCategoryModules(modulesData.modules || []);
      setTierContextConfig(modulesData.tier_context_config || {});
      setSizeInfo(configData.size_info || null);
      
      if (configData.config?.transit_limits) {
        setTransitLimits(configData.config.transit_limits);
      }
    } catch (error) {
      console.error('Error fetching category config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLayerToggle = async (layerKey, isRequired) => {
    setCategoryLayers(prev => prev.map(l => 
      l.layer_key === layerKey ? {...l, is_required: isRequired ? 1 : 0} : l
    ));
    
    setSaveNotification('✓ Saved');
    setTimeout(() => setSaveNotification(''), 2000);
    
    try {
      await fetch('/api/admin/chat-config/category/layer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          category_key: selectedCategory,
          tier_key: selectedTier,
          layer_key: layerKey,
          is_required: isRequired
        })
      });
    } catch (error) {
      console.error('Error updating layer:', error);
    }
  };

  const handleChartToggle = async (chartKey, isRequired) => {
    setCategoryCharts(prev => prev.map(c => 
      c.chart_key === chartKey ? {...c, is_required: isRequired ? 1 : 0} : c
    ));
    
    setSaveNotification('✓ Saved');
    setTimeout(() => setSaveNotification(''), 2000);
    
    try {
      await fetch('/api/admin/chat-config/category/chart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          category_key: selectedCategory,
          tier_key: selectedTier,
          chart_key: chartKey,
          is_required: isRequired
        })
      });
    } catch (error) {
      console.error('Error updating chart:', error);
    }
  };

  const handleModuleToggle = async (moduleKey, isRequired) => {
    const updatedModules = categoryModules.map(m => 
      m.module_key === moduleKey ? {...m, is_required: isRequired} : m
    );
    setCategoryModules(updatedModules);
    
    setSaveNotification('✓ Saved');
    setTimeout(() => setSaveNotification(''), 2000);
    
    const selectedKeys = updatedModules.filter(m => m.is_required).map(m => m.module_key);
    
    try {
      await fetch('/api/admin/chat-config/category/instruction-modules', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          category_key: selectedCategory,
          tier_key: selectedTier,
          module_keys: selectedKeys
        })
      });
    } catch (error) {
      console.error('Error updating modules:', error);
    }
  };

  const handleModuleExpand = async (moduleKey) => {
    if (expandedModule === moduleKey) {
      setExpandedModule(null);
      return;
    }
    
    try {
      const response = await fetch(`/api/admin/chat-config/instruction-module/${moduleKey}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setEditingText(data.module.instruction_text);
      setExpandedModule(moduleKey);
    } catch (error) {
      console.error('Error fetching module text:', error);
    }
  };

  const handleSaveInstruction = async (moduleKey) => {
    setSaving(true);
    try {
      const response = await fetch('/api/admin/chat-config/instruction-module/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          module_key: moduleKey,
          instruction_text: editingText
        })
      });
      const data = await response.json();
      alert('Instruction saved successfully');
      
      // Update character count in list
      setCategoryModules(categoryModules.map(m => 
        m.module_key === moduleKey ? {...m, character_count: data.character_count} : m
      ));
    } catch (error) {
      console.error('Error saving instruction:', error);
      alert('Failed to save instruction');
    } finally {
      setSaving(false);
    }
  };

  const handleTransitUpdate = async () => {
    try {
      await fetch('/api/admin/chat-config/category/transit-limits', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          category_key: selectedCategory,
          tier_key: selectedTier,
          max_transit_activations: parseInt(transitLimits.max_transit_activations) || 20,
          include_macro_transits: !!transitLimits.include_macro_transits,
          include_navatara_warnings: !!transitLimits.include_navatara_warnings
        })
      });
      alert('Transit limits updated successfully');
      fetchCategoryConfig();
    } catch (error) {
      console.error('Error updating transit limits:', error);
      alert('Failed to update transit limits');
    }
  };

  const handleCopyToAll = async () => {
    if (!confirm(`Copy system instruction config from ${categories.find(c => c.key === selectedCategory)?.name} to ALL other categories for ${selectedTier} tier?`)) {
      return;
    }
    
    setSaving(true);
    try {
      const response = await fetch('/api/admin/chat-config/copy-to-all', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          source_category: selectedCategory,
          tier_key: selectedTier
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        alert('✓ Configuration copied to all categories successfully!');
      } else {
        alert(`Failed: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error copying config:', error);
      alert('Network error: Failed to copy configuration');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="chat-config">
      {saveNotification && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          background: '#4CAF50',
          color: 'white',
          padding: '12px 24px',
          borderRadius: '4px',
          zIndex: 1000,
          fontWeight: 'bold',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
        }}>
          {saveNotification}
        </div>
      )}
      <h2>Chat Configuration</h2>
      <p className="subtitle">Manage prompt optimization for AI chat (instructions + context data)</p>

      <div className="category-selector">
        <label>Select Category:</label>
        <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
          {categories.map(cat => (
            <option key={cat.key} value={cat.key}>{cat.name}</option>
          ))}
        </select>
        
        <label style={{marginLeft: '20px'}}>Select Tier:</label>
        <select value={selectedTier} onChange={(e) => setSelectedTier(e.target.value)}>
          {tiers.map(tier => (
            <option key={tier.tier_key} value={tier.tier_key}>
              {tier.tier_name} (Max: {tier.max_instruction_size / 1000}KB instructions + {tier.max_context_size / 1000}KB context)
            </option>
          ))}
        </select>
      </div>

      {tiers.find(t => t.tier_key === selectedTier) && (
        <div className="tier-info-banner">
          <strong>🎯 {tiers.find(t => t.tier_key === selectedTier).tier_name} Tier:</strong> {tiers.find(t => t.tier_key === selectedTier).description}
        </div>
      )}

      <div className="tab-selector">
        <button 
          className={activeTab === 'instructions' ? 'active' : ''}
          onClick={() => setActiveTab('instructions')}
        >
          System Instructions (192KB)
        </button>
        <button 
          className={activeTab === 'context' ? 'active' : ''}
          onClick={() => setActiveTab('context')}
        >
          Context Data (150KB)
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading configuration...</div>
      ) : (
        <>
          {activeTab === 'instructions' && (
            <div className="instructions-config">
              <div className="info-banner">
                <strong>System Instructions ({selectedTier} tier):</strong> Configure which of the 41 modular instruction sections to include for <strong>{categories.find(c => c.key === selectedCategory)?.name}</strong> queries.
                {tierContextConfig.layers && (
                  <div style={{marginTop: '8px', fontSize: '0.9em'}}>
                    📦 Context Config: Layers={Array.isArray(tierContextConfig.layers) ? tierContextConfig.layers.join(', ') : tierContextConfig.layers}, 
                    Charts={Array.isArray(tierContextConfig.charts) ? tierContextConfig.charts.join(', ') : tierContextConfig.charts}, 
                    Transits={tierContextConfig.transits ? 'Yes' : 'No'}
                  </div>
                )}
              </div>
              
              <div style={{marginBottom: '20px', padding: '15px', background: '#fff3cd', borderRadius: '8px', border: '1px solid #ffc107'}}>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                  <div>
                    <strong>🔄 Copy to All Categories</strong>
                    <p style={{margin: '5px 0 0 0', fontSize: '13px', color: '#666'}}>
                      Copy the current module selection to all other categories for the {selectedTier} tier
                    </p>
                  </div>
                  <button onClick={handleCopyToAll} className="copy-all-btn">
                    Copy to All
                  </button>
                </div>
              </div>
              
              <div className="module-list">
                {categoryModules.map(module => (
                  <div key={module.module_key} className="module-item">
                    <div className="module-header">
                      <label className="checkbox-label">
                        <input
                          type="checkbox"
                          checked={!!module.is_required}
                          onChange={(e) => handleModuleToggle(module.module_key, e.target.checked)}
                        />
                        <div className="module-info">
                          <span className="module-name">{module.module_name}</span>
                          <span className="module-size">{((module.character_count || 0) / 1024).toFixed(1)} KB</span>
                        </div>
                      </label>
                      <button 
                        className="expand-btn"
                        onClick={() => handleModuleExpand(module.module_key)}
                      >
                        {expandedModule === module.module_key ? '▼ Hide' : '▶ Edit'}
                      </button>
                    </div>
                    {expandedModule === module.module_key && (
                      <div className="module-editor">
                        <textarea
                          value={editingText}
                          onChange={(e) => setEditingText(e.target.value)}
                          rows={15}
                        />
                        <div className="editor-actions">
                          <span className="char-count">{editingText.length} characters</span>
                          <button 
                            onClick={() => handleSaveInstruction(module.module_key)}
                            disabled={saving}
                            className="save-btn"
                          >
                            {saving ? 'Saving...' : 'Save Changes'}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'context' && (
            <>
          <div className="info-banner">
            <strong>Context Data ({selectedTier} tier):</strong> Configure which context data to send for <strong>{categories.find(c => c.key === selectedCategory)?.name}</strong> queries.
            <div style={{marginTop: '8px', fontSize: '0.9em'}}>
              📊 Layers are ordered by priority (1=most essential). Lower priority = included first.
            </div>
          </div>
          {sizeInfo && (
            <div className="size-info-card">
              <h3>Estimated Context Size</h3>
              <div className="size-stats">
                <div className="stat">
                  <span className="label">Total Size:</span>
                  <span className="value">{sizeInfo.total_size_kb} KB</span>
                </div>
                <div className="stat">
                  <span className="label">Reduction:</span>
                  <span className={`value ${sizeInfo.reduction_percent > 0 ? 'positive' : 'negative'}`}>
                    {sizeInfo.reduction_percent}%
                  </span>
                </div>
                <div className="stat">
                  <span className="label">Fields:</span>
                  <span className="value">{(sizeInfo.field_size_bytes / 1024).toFixed(1)} KB</span>
                </div>
                <div className="stat">
                  <span className="label">Charts:</span>
                  <span className="value">{(sizeInfo.chart_size_bytes / 1024).toFixed(1)} KB</span>
                </div>
                <div className="stat">
                  <span className="label">Transits:</span>
                  <span className="value">{(sizeInfo.transit_size_bytes / 1024).toFixed(1)} KB</span>
                </div>
              </div>
            </div>
          )}

          <div className="config-sections">
            <div className="config-section">
              <h3>Astrological Layers</h3>
              <p className="section-desc">Select which calculation layers to include</p>
              <div className="layer-list">
                {categoryLayers.map(layer => (
                  <div key={layer.layer_key} className="layer-item">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={!!layer.is_required}
                        onChange={(e) => handleLayerToggle(layer.layer_key, e.target.checked)}
                      />
                      <div className="layer-details">
                        <div className="layer-header">
                          <span className="layer-name">{layer.layer_name}</span>
                          <span className="layer-priority">Priority: {layer.priority}</span>
                        </div>
                        {layer.description && (
                          <div className="layer-description">{layer.description}</div>
                        )}
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div className="config-section">
              <h3>Divisional Charts</h3>
              <p className="section-desc">Select which D-charts to include</p>
              <div className="chart-list">
                {categoryCharts.map(chart => (
                  <div key={chart.chart_key} className="chart-item">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={!!chart.is_required}
                        onChange={(e) => handleChartToggle(chart.chart_key, e.target.checked)}
                      />
                      <span className="chart-name">{chart.chart_name}</span>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div className="config-section">
              <h3>Transit Configuration</h3>
              <p className="section-desc">Configure transit data limits</p>
              <div className="transit-config">
                <div className="form-field">
                  <label>Max Transit Activations:</label>
                  <input
                    type="number"
                    min="0"
                    max="50"
                    value={transitLimits.max_transit_activations || 20}
                    onChange={(e) => setTransitLimits({...transitLimits, max_transit_activations: e.target.value})}
                  />
                </div>
                <div className="form-field">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={!!transitLimits.include_macro_transits}
                      onChange={(e) => setTransitLimits({...transitLimits, include_macro_transits: e.target.checked})}
                    />
                    <span>Include Macro Transits</span>
                  </label>
                </div>
                <div className="form-field">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={!!transitLimits.include_navatara_warnings}
                      onChange={(e) => setTransitLimits({...transitLimits, include_navatara_warnings: e.target.checked})}
                    />
                    <span>Include Navatara Warnings</span>
                  </label>
                </div>
                <button onClick={handleTransitUpdate} className="update-btn">
                  Update Transit Limits
                </button>
              </div>
            </div>
          </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default ChatConfig;
