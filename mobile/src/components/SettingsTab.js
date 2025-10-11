import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { apiService } from '../services/apiService';

const SettingsTab = ({ user, onSettingsUpdate }) => {
  const [settings, setSettings] = useState({
    node_type: 'mean',
    default_chart_style: 'north'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

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
    if (!user?.phone) {
      setMessage('User phone not found');
      setTimeout(() => setMessage(''), 3000);
      return;
    }
    
    setSaving(true);
    try {
      await apiService.updateUserSettings(user.phone, settings);
      setMessage('✅ Settings saved successfully!');
      setTimeout(() => setMessage(''), 3000);
      if (onSettingsUpdate) {
        await onSettingsUpdate();
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      setMessage('❌ Failed to save settings');
      setTimeout(() => setMessage(''), 3000);
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
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading settings...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Text style={styles.title}>⚙️ User Settings</Text>
      
      <View style={styles.settingsGrid}>
        {/* Node Type Setting */}
        <View style={styles.settingCard}>
          <Text style={styles.settingTitle}>Node Calculation</Text>
          <Text style={styles.settingDescription}>
            Choose between Mean Nodes (average position) or True Nodes (actual oscillating position)
          </Text>
          <View style={styles.radioGroup}>
            <TouchableOpacity
              style={styles.radioOption}
              onPress={() => handleChange('node_type', 'mean')}
            >
              <View style={[
                styles.radioCircle,
                settings.node_type === 'mean' && styles.radioSelected
              ]}>
                {settings.node_type === 'mean' && <View style={styles.radioDot} />}
              </View>
              <Text style={styles.radioLabel}>Mean Nodes</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.radioOption}
              onPress={() => handleChange('node_type', 'true')}
            >
              <View style={[
                styles.radioCircle,
                settings.node_type === 'true' && styles.radioSelected
              ]}>
                {settings.node_type === 'true' && <View style={styles.radioDot} />}
              </View>
              <Text style={styles.radioLabel}>True Nodes</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Chart Style Setting */}
        <View style={styles.settingCard}>
          <Text style={styles.settingTitle}>Default Chart Style</Text>
          <Text style={styles.settingDescription}>
            Choose your preferred chart style for new charts
          </Text>
          <View style={styles.radioGroup}>
            <TouchableOpacity
              style={styles.radioOption}
              onPress={() => handleChange('default_chart_style', 'north')}
            >
              <View style={[
                styles.radioCircle,
                settings.default_chart_style === 'north' && styles.radioSelected
              ]}>
                {settings.default_chart_style === 'north' && <View style={styles.radioDot} />}
              </View>
              <Text style={styles.radioLabel}>North Indian</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.radioOption}
              onPress={() => handleChange('default_chart_style', 'south')}
            >
              <View style={[
                styles.radioCircle,
                settings.default_chart_style === 'south' && styles.radioSelected
              ]}>
                {settings.default_chart_style === 'south' && <View style={styles.radioDot} />}
              </View>
              <Text style={styles.radioLabel}>South Indian</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Save Button */}
      <View style={styles.saveContainer}>
        <TouchableOpacity
          onPress={handleSave}
          disabled={saving}
          style={[styles.saveButton, saving && styles.saveButtonDisabled]}
        >
          <Text style={styles.saveButtonText}>
            {saving ? 'Saving...' : 'Save Settings'}
          </Text>
        </TouchableOpacity>
        {message ? (
          <View style={styles.messageContainer}>
            <Text style={styles.messageText}>{message}</Text>
          </View>
        ) : null}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#e91e63',
    marginBottom: 30,
    textAlign: 'center',
  },
  settingsGrid: {
    gap: 25,
  },
  settingCard: {
    padding: 20,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    backgroundColor: '#f9f9f9',
  },
  settingTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  settingDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15,
    lineHeight: 20,
  },
  radioGroup: {
    gap: 15,
  },
  radioOption: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  radioCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#ddd',
    marginRight: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioSelected: {
    borderColor: '#e91e63',
  },
  radioDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#e91e63',
  },
  radioLabel: {
    fontSize: 16,
    color: '#333',
  },
  saveContainer: {
    marginTop: 30,
    alignItems: 'center',
  },
  saveButton: {
    paddingVertical: 12,
    paddingHorizontal: 30,
    backgroundColor: '#e91e63',
    borderRadius: 8,
  },
  saveButtonDisabled: {
    opacity: 0.7,
  },
  saveButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  messageContainer: {
    marginTop: 15,
    padding: 10,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    alignItems: 'center',
  },
  messageText: {
    fontSize: 14,
    color: '#333',
    textAlign: 'center',
  },
});

export default SettingsTab;