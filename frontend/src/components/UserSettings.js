import React, { useState, useEffect } from 'react';
import { apiService } from '../services/apiService';

const UserSettings = ({ user, onSettingsUpdate }) => {
  const [settings, setSettings] = useState({
    node_type: 'mean',
    default_chart_style: 'north'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, [user]);

  const loadSettings = async () => {
    if (!user?.phone) return;
    
    try {
      const userSettings = await apiService.getUserSettings(user.phone);
      setSettings(userSettings);
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!user?.phone) return;
    
    setSaving(true);
    try {
      await apiService.updateUserSettings(user.phone, settings);
      alert('Settings saved successfully!');
      if (onSettingsUpdate) {
        await onSettingsUpdate();
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  if (loading) {
    return <div style={{ padding: '20px' }}>Loading settings...</div>;
  }

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h2 style={{ color: '#e91e63', marginBottom: '30px' }}>User Settings</h2>
      
      <div style={{ display: 'grid', gap: '25px' }}>
        {/* Node Type Setting */}
        <div style={{ 
          padding: '20px', 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          backgroundColor: '#f9f9f9'
        }}>
          <h3 style={{ margin: '0 0 15px 0', color: '#333' }}>Node Calculation</h3>
          <p style={{ margin: '0 0 15px 0', color: '#666', fontSize: '14px' }}>
            Choose between Mean Nodes (average position) or True Nodes (actual oscillating position)
          </p>
          <div style={{ display: 'flex', gap: '15px' }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="radio"
                name="node_type"
                value="mean"
                checked={settings.node_type === 'mean'}
                onChange={(e) => handleChange('node_type', e.target.value)}
                style={{ marginRight: '8px' }}
              />
              <span>Mean Nodes</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="radio"
                name="node_type"
                value="true"
                checked={settings.node_type === 'true'}
                onChange={(e) => handleChange('node_type', e.target.value)}
                style={{ marginRight: '8px' }}
              />
              <span>True Nodes</span>
            </label>
          </div>
        </div>

        {/* Chart Style Setting */}
        <div style={{ 
          padding: '20px', 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          backgroundColor: '#f9f9f9'
        }}>
          <h3 style={{ margin: '0 0 15px 0', color: '#333' }}>Default Chart Style</h3>
          <p style={{ margin: '0 0 15px 0', color: '#666', fontSize: '14px' }}>
            Choose your preferred chart style for new charts
          </p>
          <div style={{ display: 'flex', gap: '15px' }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="radio"
                name="chart_style"
                value="north"
                checked={settings.default_chart_style === 'north'}
                onChange={(e) => handleChange('default_chart_style', e.target.value)}
                style={{ marginRight: '8px' }}
              />
              <span>North Indian</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="radio"
                name="chart_style"
                value="south"
                checked={settings.default_chart_style === 'south'}
                onChange={(e) => handleChange('default_chart_style', e.target.value)}
                style={{ marginRight: '8px' }}
              />
              <span>South Indian</span>
            </label>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div style={{ marginTop: '30px', textAlign: 'center' }}>
        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            padding: '12px 30px',
            backgroundColor: '#e91e63',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: saving ? 'not-allowed' : 'pointer',
            fontSize: '16px',
            fontWeight: '600',
            opacity: saving ? 0.7 : 1
          }}
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
};

export default UserSettings;