import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  Platform,
  FlatList,
  KeyboardAvoidingView,
  Modal,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import DateTimePicker from '@react-native-community/datetimepicker';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import { storage } from '../../services/storage';
import { chartAPI } from '../../services/api';
import { COLORS } from '../../utils/constants';

export default function BirthFormScreen({ navigation }) {
  const addWelcomeMessage = navigation.getParent()?.getState()?.routes?.find(r => r.name === 'Chat')?.params?.addWelcomeMessage;
  const [activeTab, setActiveTab] = useState('new');
  const [formData, setFormData] = useState({
    name: '',
    date: new Date(),
    time: new Date(),
    place: '',
    latitude: null,
    longitude: null,
    timezone: 'Asia/Kolkata',
    gender: '',
  });
  
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [loading, setLoading] = useState(false);
  const [existingCharts, setExistingCharts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [editingChart, setEditingChart] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState(null);

  useEffect(() => {
    loadSavedData();
    loadExistingCharts();
  }, []);

  const loadSavedData = async () => {
    try {
      const savedData = await storage.getBirthDetails();
      if (savedData) {
        setFormData({
          ...savedData,
          date: new Date(savedData.date),
          time: new Date(savedData.time),
        });
      }
    } catch (error) {
      console.error('Error loading saved data:', error);
    }
  };

  const loadExistingCharts = async (search = '') => {
    try {
      const response = await chartAPI.getExistingCharts(search);
      setExistingCharts(response.data.charts || []);
    } catch (error) {
      console.error('Failed to load existing charts:', error);
      setExistingCharts([]);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    if (field === 'place') {
      // Clear coordinates when manually typing
      setFormData(prev => ({ 
        ...prev, 
        [field]: value,
        latitude: null,
        longitude: null
      }));
      
      // Debounced search
      if (searchTimeout) clearTimeout(searchTimeout);
      
      const timeout = setTimeout(() => {
        if (value.length >= 3) {
          searchPlaces(value);
        } else {
          setSuggestions([]);
          setShowSuggestions(false);
        }
      }, 300);
      
      setSearchTimeout(timeout);
    }
  };

  const handleDateChange = (event, selectedDate) => {
    setShowDatePicker(false);
    if (selectedDate) {
      handleInputChange('date', selectedDate);
    }
  };

  const handleTimeChange = (event, selectedTime) => {
    setShowTimePicker(false);
    if (selectedTime) {
      handleInputChange('time', selectedTime);
    }
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      Alert.alert('Error', 'Please enter your name');
      return false;
    }
    if (!formData.place.trim()) {
      Alert.alert('Error', 'Please enter birth place');
      return false;
    }
    if (!formData.gender) {
      Alert.alert('Error', 'Please select gender');
      return false;
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      const birthData = {
        name: formData.name,
        date: formData.date.toISOString().split('T')[0],
        time: formData.time.toTimeString().split(' ')[0],
        place: formData.place,
        latitude: formData.latitude || 0,
        longitude: formData.longitude || 0,
        timezone: formData.timezone,
        gender: formData.gender,
      };

      if (editingChart) {
        await chartAPI.updateChart(editingChart.id, birthData);
        Alert.alert('Success', 'Chart updated successfully!');
        loadExistingCharts(searchQuery);
        setEditingChart(null);
        setActiveTab('saved');
      } else {
        // Save birth details locally
        await storage.setBirthDetails(formData);
        
        // Calculate chart
        const [chartData, yogiData] = await Promise.all([
          chartAPI.calculateChart(birthData),
          chartAPI.calculateYogi(birthData)
        ]);

        Alert.alert(
          'Success',
          'Birth chart calculated successfully!',
          [
            {
              text: 'OK',
              onPress: () => navigation.navigate('Chat'),
            },
          ]
        );
      }
    } catch (error) {
      Alert.alert('Error', error.response?.data?.message || 'Failed to process birth details');
    } finally {
      setLoading(false);
    }
  };

  const selectExistingChart = async (chart) => {
    try {
      const birthData = {
        name: chart.name,
        date: chart.date,
        time: chart.time,
        latitude: chart.latitude,
        longitude: chart.longitude,
        timezone: chart.timezone,
        place: chart.place || '',
        gender: chart.gender || ''
      };
      
      const [chartData, yogiData] = await Promise.all([
        chartAPI.calculateChart(birthData),
        chartAPI.calculateYogi(birthData)
      ]);
      
      await storage.setBirthDetails({
        ...birthData,
        date: new Date(chart.date),
        time: chart.time // Keep original time format
      });

      // Add welcome message to chat if callback exists
      if (addWelcomeMessage) {
        const welcomeMessage = {
          id: Date.now(),
          text: `Welcome ${chart.name}! 🌟 Your birth chart has been loaded. I'm here to help you understand your astrological insights. What would you like to know about your chart?`,
          isUser: false,
          timestamp: new Date().toISOString()
        };
        
        addWelcomeMessage(prev => [...prev, welcomeMessage]);
      }
      navigation.navigate('Chat');
    } catch (error) {
      Alert.alert('Error', 'Failed to load chart');
    }
  };

  const editChart = (chart) => {
    setEditingChart(chart);
    setFormData({
      name: chart.name,
      date: new Date(chart.date),
      time: chart.time.includes(':') ? new Date(`1970-01-01T${chart.time}`) : new Date(chart.time),
      place: chart.place || `${chart.latitude}, ${chart.longitude}`,
      latitude: chart.latitude,
      longitude: chart.longitude,
      timezone: chart.timezone,
      gender: chart.gender || ''
    });
    setActiveTab('new');
  };

  const searchPlaces = async (query) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&addressdetails=1`,
        {
          headers: {
            'User-Agent': 'AstrologyApp/1.0'
          }
        }
      );
      
      if (!response.ok) {
        throw new Error('Location search failed');
      }
      
      const data = await response.json();
      
      const places = data.map(item => ({
        id: item.place_id,
        name: item.display_name,
        latitude: parseFloat(item.lat),
        longitude: parseFloat(item.lon),
        timezone: 'Asia/Kolkata' // Default timezone
      }));
      
      setSuggestions(places);
      setShowSuggestions(true);
    } catch (error) {
      console.error('Location search error:', error);
    }
  };

  const handlePlaceSelect = (place) => {
    setFormData(prev => ({
      ...prev,
      place: place.name,
      latitude: place.latitude,
      longitude: place.longitude,
      timezone: place.timezone
    }));
    setShowSuggestions(false);
    setSuggestions([]);
  };

  const deleteChart = async (chartId) => {
    Alert.alert(
      'Delete Chart',
      'Are you sure you want to delete this chart?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await chartAPI.deleteChart(chartId);
              Alert.alert('Success', 'Chart deleted successfully!');
              loadExistingCharts(searchQuery);
            } catch (error) {
              Alert.alert('Error', 'Failed to delete chart');
            }
          },
        },
      ]
    );
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const formatTime = (time) => {
    return time.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  const renderChartItem = ({ item }) => (
    <View style={styles.chartItem}>
      <TouchableOpacity
        style={styles.chartInfo}
        onPress={() => selectExistingChart(item)}
      >
        <Text style={styles.chartName}>{item.name}</Text>
        <Text style={styles.chartDetails}>
          {item.date} at {item.time}
        </Text>
        <Text style={styles.chartCreated}>
          Created: {new Date(item.created_at).toLocaleDateString()}
        </Text>
      </TouchableOpacity>
      <View style={styles.chartActions}>
        <TouchableOpacity
          style={[styles.actionButton, styles.editButton]}
          onPress={() => editChart(item)}
        >
          <Text style={styles.actionButtonText}>Edit</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, styles.deleteButton]}
          onPress={() => deleteChart(item.id)}
        >
          <Text style={styles.actionButtonText}>Delete</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <LinearGradient 
      colors={[COLORS.gradientStart, COLORS.gradientEnd]} 
      style={styles.container}
    >
      <View style={styles.safeArea}>
        <KeyboardAvoidingView 
          style={styles.keyboardAvoid}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
        {/* Tab Navigation */}
        <View style={styles.tabNavigation}>
          <TouchableOpacity
            style={[styles.tabButton, activeTab === 'new' && styles.activeTab]}
            onPress={() => setActiveTab('new')}
          >
            <Text style={[styles.tabText, activeTab === 'new' && styles.activeTabText]}>
              📝 New Chart
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tabButton, activeTab === 'saved' && styles.activeTab]}
            onPress={() => setActiveTab('saved')}
          >
            <Text style={[styles.tabText, activeTab === 'saved' && styles.activeTabText]}>
              📊 Saved Charts
            </Text>
          </TouchableOpacity>
        </View>

        {activeTab === 'new' ? (
          <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
            <View style={styles.formContainer}>
              <Text style={styles.title}>Birth Details</Text>
              
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Name</Text>
                <TextInput
                  style={styles.input}
                  value={formData.name}
                  onChangeText={(value) => handleInputChange('name', value)}
                  placeholder="Full name"
                  placeholderTextColor={COLORS.gray}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Gender</Text>
                <View style={styles.genderButtons}>
                  <TouchableOpacity
                    style={[styles.genderButton, formData.gender === 'Male' && styles.genderButtonSelected]}
                    onPress={() => handleInputChange('gender', 'Male')}
                  >
                    <Text style={[styles.genderButtonText, formData.gender === 'Male' && styles.genderButtonTextSelected]}>Male</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.genderButton, formData.gender === 'Female' && styles.genderButtonSelected]}
                    onPress={() => handleInputChange('gender', 'Female')}
                  >
                    <Text style={[styles.genderButtonText, formData.gender === 'Female' && styles.genderButtonTextSelected]}>Female</Text>
                  </TouchableOpacity>
                </View>
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Date of Birth</Text>
                {Platform.OS === 'web' ? (
                  <TextInput
                    style={styles.input}
                    value={formData.date.toISOString().split('T')[0]}
                    onChangeText={(value) => {
                      if (value) {
                        handleInputChange('date', new Date(value));
                      }
                    }}
                    placeholder="YYYY-MM-DD"
                    placeholderTextColor={COLORS.gray}
                  />
                ) : (
                  <TouchableOpacity
                    style={styles.dateTimeButton}
                    onPress={() => setShowDatePicker(true)}
                  >
                    <Text style={styles.dateTimeText}>{formatDate(formData.date)}</Text>
                    <Ionicons name="calendar" size={16} color={COLORS.accent} />
                  </TouchableOpacity>
                )}
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Time of Birth</Text>
                {Platform.OS === 'web' ? (
                  <TextInput
                    style={styles.input}
                    value={formData.time.toTimeString().slice(0, 5)}
                    onChangeText={(value) => {
                      if (value && value.includes(':')) {
                        const [hours, minutes] = value.split(':');
                        const newTime = new Date();
                        newTime.setHours(parseInt(hours) || 0, parseInt(minutes) || 0, 0, 0);
                        handleInputChange('time', newTime);
                      }
                    }}
                    placeholder="HH:MM"
                    placeholderTextColor={COLORS.gray}
                  />
                ) : (
                  <TouchableOpacity
                    style={styles.dateTimeButton}
                    onPress={() => setShowTimePicker(true)}
                  >
                    <Text style={styles.dateTimeText}>{formatTime(formData.time)}</Text>
                    <Ionicons name="time" size={16} color={COLORS.accent} />
                  </TouchableOpacity>
                )}
              </View>

              {showSuggestions && suggestions.length > 0 && (
                <View style={styles.suggestionsList}>
                  {suggestions.map(suggestion => (
                    <TouchableOpacity
                      key={suggestion.id}
                      style={styles.suggestionItem}
                      onPress={() => handlePlaceSelect(suggestion)}
                    >
                      <Text style={styles.suggestionText}>{suggestion.name}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              )}

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Place of Birth</Text>
                <TextInput
                  style={styles.input}
                  value={formData.place}
                  onChangeText={(value) => handleInputChange('place', value)}
                  placeholder="City, State, Country"
                  placeholderTextColor={COLORS.gray}
                  onBlur={() => {
                    setTimeout(() => setShowSuggestions(false), 200);
                  }}
                />
              </View>



              <TouchableOpacity
                style={[styles.submitButton, loading && styles.submitButtonDisabled]}
                onPress={handleSubmit}
                disabled={loading}
              >
                <Text style={styles.submitButtonText}>
                  {loading ? 'Processing...' : (editingChart ? 'Update Chart' : 'Calculate Birth Chart')}
                </Text>
              </TouchableOpacity>

              {editingChart && (
                <TouchableOpacity
                  style={[styles.submitButton, styles.cancelButton]}
                  onPress={() => {
                    setEditingChart(null);
                    setActiveTab('saved');
                  }}
                >
                  <Text style={styles.submitButtonText}>Cancel</Text>
                </TouchableOpacity>
              )}
            </View>
          </ScrollView>
        ) : (
          <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
            <View style={styles.savedChartsContainer}>
              <TextInput
                style={styles.searchInput}
                placeholder="Search by name..."
                placeholderTextColor={COLORS.gray}
                value={searchQuery}
                onChangeText={(text) => {
                  setSearchQuery(text);
                  loadExistingCharts(text);
                }}
              />
              {existingCharts.length > 0 ? (
                existingCharts.map((item) => (
                  <View key={item.id.toString()} style={styles.chartItem}>
                    <TouchableOpacity
                      style={styles.chartInfo}
                      onPress={() => selectExistingChart(item)}
                    >
                      <Text style={styles.chartName}>{item.name}</Text>
                      <Text style={styles.chartDetails}>
                        {item.date} at {item.time}
                      </Text>
                      <Text style={styles.chartCreated}>
                        Created: {new Date(item.created_at).toLocaleDateString()}
                      </Text>
                    </TouchableOpacity>
                    <View style={styles.chartActions}>
                      <TouchableOpacity
                        style={[styles.actionButton, styles.editButton]}
                        onPress={() => editChart(item)}
                      >
                        <Text style={styles.actionButtonText}>Edit</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.actionButton, styles.deleteButton]}
                        onPress={() => deleteChart(item.id)}
                      >
                        <Text style={styles.actionButtonText}>Delete</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                ))
              ) : (
                <View style={styles.emptyContainer}>
                  <Text style={styles.emptyText}>
                    {searchQuery ? 'No charts found' : 'No saved charts'}
                  </Text>
                </View>
              )}
            </View>
          </ScrollView>
        )}

        {/* Date Picker Modal */}
        {showDatePicker && Platform.OS !== 'web' && (
          <Modal visible={showDatePicker} transparent animationType="slide">
            <View style={styles.pickerModal}>
              <View style={styles.pickerContainer}>
                <DateTimePicker
                  value={formData.date}
                  mode="date"
                  display="spinner"
                  onChange={handleDateChange}
                  maximumDate={new Date()}
                />
                <TouchableOpacity
                  style={styles.pickerDone}
                  onPress={() => setShowDatePicker(false)}
                >
                  <Text style={styles.pickerDoneText}>Done</Text>
                </TouchableOpacity>
              </View>
            </View>
          </Modal>
        )}

        {/* Time Picker Modal */}
        {showTimePicker && Platform.OS !== 'web' && (
          <Modal visible={showTimePicker} transparent animationType="slide">
            <View style={styles.pickerModal}>
              <View style={styles.pickerContainer}>
                <DateTimePicker
                  value={formData.time}
                  mode="time"
                  display="spinner"
                  onChange={handleTimeChange}
                />
                <TouchableOpacity
                  style={styles.pickerDone}
                  onPress={() => setShowTimePicker(false)}
                >
                  <Text style={styles.pickerDoneText}>Done</Text>
                </TouchableOpacity>
              </View>
            </View>
          </Modal>
        )}

        {/* Place Suggestions Modal */}
        <Modal visible={showSuggestions && suggestions.length > 0} transparent animationType="slide">
          <View style={styles.pickerModal}>
            <View style={styles.pickerContainer}>
              <Text style={styles.modalTitle}>Select Place</Text>
              <ScrollView style={{ maxHeight: 200 }}>
                {suggestions.map(suggestion => (
                  <TouchableOpacity
                    key={suggestion.id}
                    style={styles.suggestionItem}
                    onPress={() => handlePlaceSelect(suggestion)}
                  >
                    <Text style={styles.suggestionText}>{suggestion.name}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
              <TouchableOpacity
                style={styles.pickerDone}
                onPress={() => setShowSuggestions(false)}
              >
                <Text style={styles.pickerDoneText}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>

        </KeyboardAvoidingView>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    height: Platform.OS === 'web' ? '100vh' : undefined,
  },
  safeArea: {
    flex: 1,
    height: Platform.OS === 'web' ? '100%' : undefined,
    paddingTop: 0,
  },
  keyboardAvoid: {
    flex: 1,
    height: Platform.OS === 'web' ? '100%' : undefined,
    paddingTop: 0,
  },
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    margin: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 10,
  },
  activeTab: {
    backgroundColor: COLORS.accent,
  },
  tabText: {
    color: COLORS.textPrimary,
    fontSize: 14,
    fontWeight: '600',
  },
  activeTabText: {
    color: COLORS.white,
  },
  scrollView: {
    flex: 1,
  },
  formContainer: {
    padding: 20,
    backgroundColor: COLORS.surface,
    margin: 15,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.accent,
    textAlign: 'center',
    marginBottom: 20,
  },
  inputGroup: {
    marginBottom: 15,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  input: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: COLORS.textPrimary,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  dateTimeButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    borderRadius: 8,
    padding: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  dateTimeText: {
    fontSize: 16,
    color: COLORS.textPrimary,
  },
  genderButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  genderButton: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  genderButtonSelected: {
    backgroundColor: COLORS.accent,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 5,
  },
  genderButtonText: {
    fontSize: 16,
    color: COLORS.textPrimary,
  },
  genderButtonTextSelected: {
    color: COLORS.white,
  },

  suggestionItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 107, 53, 0.2)',
  },
  suggestionText: {
    fontSize: 14,
    color: COLORS.textPrimary,
  },
  submitButton: {
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
    marginTop: 15,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 8,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  cancelButton: {
    backgroundColor: COLORS.gray,
    marginTop: 10,
  },
  submitButtonText: {
    color: COLORS.white,
    fontSize: 18,
    fontWeight: 'bold',
  },
  savedChartsContainer: {
    padding: 20,
  },

  searchInput: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 15,
    color: COLORS.textPrimary,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },

  chartItem: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.2)',
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
  chartInfo: {
    flex: 1,
  },
  chartName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: 5,
  },
  chartDetails: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 3,
  },
  chartCreated: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  chartActions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  editButton: {
    backgroundColor: COLORS.accent,
  },
  deleteButton: {
    backgroundColor: COLORS.error,
  },
  actionButtonText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: 'bold',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
  },
  emptyText: {
    color: COLORS.textSecondary,
    fontSize: 16,
  },
  pickerModal: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  pickerContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
  pickerDone: {
    backgroundColor: COLORS.accent,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10,
  },
  pickerDoneText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: 'bold',
  },
});