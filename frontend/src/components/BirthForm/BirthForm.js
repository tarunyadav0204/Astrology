import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { useAstrology } from '../../context/AstrologyContext';
import { apiService } from '../../services/apiService';
import { locationService } from '../../services/locationService';
import { FORM_FIELDS, VALIDATION_MESSAGES } from '../../config/form.config';
import { APP_CONFIG } from '../../config/app.config';
import { FormContainer, FormField, Input, Select, Label, Button, AutocompleteContainer, SuggestionList, SuggestionItem, SearchInput, ChartsList, ChartItem, TabContainer, TabNavigation, TabButton, TabContent } from './BirthForm.styles';

const BirthForm = ({ onSubmit, onLogout, prefilledData, showCloseButton, onClose }) => {
  const { birthData, setBirthData, setChartData, setLoading, setError } = useAstrology();
  
  const [formData, setFormData] = useState({
    name: '',
    date: '',
    time: '',
    place: '',
    latitude: null,
    longitude: null,
    timezone: '',
    gender: ''
  });
  
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [errors, setErrors] = useState({});
  const [existingCharts, setExistingCharts] = useState([]);
  const [editingChart, setEditingChart] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchDebounce, setSearchDebounce] = useState(null);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (formData.place.length >= APP_CONFIG.location.minSearchLength && !formData.latitude) {
        searchPlaces(formData.place);
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, APP_CONFIG.location.debounceMs);

    return () => clearTimeout(debounceTimer);
  }, [formData.place]);

  useEffect(() => {
    // Only load existing charts if user is authenticated
    const token = localStorage.getItem('token');
    if (token) {
      loadExistingCharts();
    }
    
    // Pre-populate form if prefilledData is provided (from homepage matching)
    if (prefilledData && prefilledData.person1) {
      setFormData({
        name: prefilledData.person1.name || '',
        date: prefilledData.person1.date || '',
        time: prefilledData.person1.time || '',
        place: prefilledData.person1.place || '',
        latitude: null,
        longitude: null,
        timezone: '',
        gender: 'Male'
      });
    }
    // Pre-populate form if birthData exists in context (from edit action)
    else if (birthData && birthData.id) {
      setEditingChart(birthData);
      setFormData({
        name: birthData.name || '',
        date: birthData.date || '',
        time: birthData.time || '',
        place: birthData.place || '',
        latitude: birthData.latitude || null,
        longitude: birthData.longitude || null,
        timezone: birthData.timezone || '',
        gender: birthData.gender || ''
      });
    }
  }, [birthData, prefilledData]);

  const loadExistingCharts = async (search = '') => {
    const token = localStorage.getItem('token');
    if (!token) {
      setExistingCharts([]);
      return;
    }
    
    try {
      const response = await apiService.getExistingCharts(search);
      setExistingCharts(response.charts || []);
    } catch (error) {
      console.error('Failed to load existing charts:', error);
      setExistingCharts([]);
    }
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    if (searchDebounce) clearTimeout(searchDebounce);
    
    const timeout = setTimeout(() => {
      loadExistingCharts(query);
    }, 300);
    
    setSearchDebounce(timeout);
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
        apiService.calculateChart(birthData),
        apiService.calculateYogi(birthData)
      ]);
      
      // Merge Yogi data into chart data
      const enhancedChartData = {
        ...chartData,
        yogiData: yogiData
      };
      
      setBirthData({
        name: chart.name,
        date: chart.date,
        time: chart.time,
        place: `${chart.latitude}, ${chart.longitude}`,
        latitude: chart.latitude,
        longitude: chart.longitude,
        timezone: chart.timezone
      });
      
      setChartData(enhancedChartData);
      toast.success('Chart loaded successfully!');
      
      // Close modal directly without triggering onSubmit callback
      if (onClose) {
        onClose();
      }
    } catch (error) {
      toast.error('Failed to load chart');
    }
  };

  const editChart = (chart) => {
    setEditingChart(chart);
    setFormData({
      name: chart.name,
      date: chart.date,
      time: chart.time,
      place: chart.place || `${chart.latitude}, ${chart.longitude}`,
      latitude: chart.latitude,
      longitude: chart.longitude,
      timezone: chart.timezone,
      gender: chart.gender || ''
    });
  };

  const deleteChart = async (chartId) => {
    if (window.confirm('Are you sure you want to delete this chart?')) {
      try {
        await apiService.deleteChart(chartId);
        toast.success('Chart deleted successfully!');
        loadExistingCharts(searchQuery);
      } catch (error) {
        toast.error('Failed to delete chart');
      }
    }
  };

  const cancelEdit = () => {
    setEditingChart(null);
    setFormData({
      name: '',
      date: '',
      time: '',
      place: '',
      latitude: null,
      longitude: null,
      timezone: '',
      gender: ''
    });
  };

  const searchPlaces = async (query) => {
    try {
      const results = await locationService.searchPlaces(query);
      setSuggestions(results);
      setShowSuggestions(true);
    } catch (error) {
      toast.error('Failed to search locations');
    }
  };

  const validateField = (name, value) => {
    const field = FORM_FIELDS[name];
    if (!field) return '';

    if (field.required && !value) {
      return VALIDATION_MESSAGES.required;
    }

    if (field.validation) {
      const { minLength, maxLength, pattern, min, max } = field.validation;
      
      if (minLength && value.length < minLength) {
        return field.validation.message;
      }
      
      if (maxLength && value.length > maxLength) {
        return field.validation.message;
      }
      
      if (pattern && !pattern.test(value)) {
        return field.validation.message;
      }
      
      if (name === 'date') {
        const date = new Date(value);
        const minDate = new Date(min);
        const maxDate = new Date(max);
        
        if (date < minDate || date > maxDate) {
          return field.validation.message;
        }
      }
    }

    return '';
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'place') {
      // Clear coordinates when manually typing
      setFormData(prev => ({ 
        ...prev, 
        [name]: value,
        latitude: null,
        longitude: null,
        timezone: ''
      }));
      // Clear place error when typing to search
      setErrors(prev => ({ ...prev, place: '' }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
    
    const error = validateField(name, value);
    setErrors(prev => ({ ...prev, [name]: error }));
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
    
    // Clear any place validation errors
    setErrors(prev => ({ ...prev, place: '' }));
  };

  const validateForm = () => {
    const newErrors = {};
    Object.keys(FORM_FIELDS).forEach(field => {
      const error = validateField(field, formData[field]);
      if (error) newErrors[field] = error;
    });

    // Strict validation: coordinates must exist
    if (!formData.latitude || !formData.longitude || formData.latitude === null || formData.longitude === null) {
      newErrors.place = 'You must select a place from the suggestions list to get accurate coordinates';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('Form submission attempt:', formData);
    
    // ABSOLUTE BLOCK: Multiple validation layers
    const hasValidCoordinates = formData.latitude && 
                               formData.longitude && 
                               formData.latitude !== null && 
                               formData.longitude !== null &&
                               typeof formData.latitude === 'number' && 
                               typeof formData.longitude === 'number' &&
                               !isNaN(formData.latitude) &&
                               !isNaN(formData.longitude);
    
    if (!hasValidCoordinates) {
      console.log('BLOCKED: No valid coordinates');
      toast.error('🚫 BLOCKED: You must select a location from the dropdown suggestions!');
      setErrors(prev => ({ ...prev, place: 'REQUIRED: Must select from suggestions' }));
      return false;
    }
    
    if (!validateForm()) {
      toast.error('Please fix the errors in the form');
      return false;
    }

    setLoading(true);
    
    try {
      if (editingChart) {
        await apiService.updateChart(editingChart.id, formData);
        toast.success('Chart updated successfully!');
        loadExistingCharts(searchQuery);
        cancelEdit();
      } else {
        // FINAL CHECK: Absolutely prevent API call without coordinates
        if (!formData.latitude || !formData.longitude || formData.latitude === null || formData.longitude === null) {
          throw new Error('Coordinates missing - select from suggestions required');
        }
        
        const [chartData, yogiData] = await Promise.all([
          apiService.calculateChart(formData),
          apiService.calculateYogi(formData)
        ]);
        
        // Merge Yogi data into chart data
        const enhancedChartData = {
          ...chartData,
          yogiData: yogiData
        };
        
        setBirthData(formData);
        setChartData(enhancedChartData);
        toast.success('Birth chart calculated successfully!');
        onSubmit();
      }
    } catch (error) {
      setError(error.message);
      toast.error(error.message);
    }
  };

  const [activeTab, setActiveTab] = useState('new');

  return (
    <TabContainer key="fixed-tabs-v2">
      {onClose && (
        <div style={{
          padding: '24px 70px 20px 24px',
          borderBottom: '1px solid #e2e8f0',
          background: '#f8fafc',
          position: 'relative',
          borderRadius: '24px 24px 0 0'
        }}>
          <h2 style={{
            margin: '0 0 8px 0',
            color: '#1e1b4b',
            fontSize: '24px',
            fontWeight: '700',
            textAlign: 'center'
          }}>
            {activeTab === 'new' ? 'Enter Birth Details' : 'Select Saved Chart'}
          </h2>
          <p style={{
            margin: 0,
            color: '#64748b',
            fontSize: '14px',
            textAlign: 'center',
            fontWeight: '400'
          }}>
            {activeTab === 'new' ? 'Please provide birth information to generate chart' : 'Choose from your previously saved birth charts'}
          </p>
          <button
            onClick={onClose}
            style={{
              position: 'absolute',
              top: '20px',
              right: '20px',
              background: '#f1f5f9',
              border: 'none',
              fontSize: '20px',
              color: '#64748b',
              cursor: 'pointer',
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '50%',
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = '#e2e8f0';
              e.target.style.color = '#1e293b';
            }}
            onMouseLeave={(e) => {
              e.target.style.background = '#f1f5f9';
              e.target.style.color = '#64748b';
            }}
          >
            ×
          </button>
        </div>
      )}
      <TabNavigation>
        <TabButton
          type="button"
          onClick={() => setActiveTab('new')}
          active={activeTab === 'new'}
          isFirst={true}
        >
          📝 New Chart
        </TabButton>
        <TabButton
          type="button"
          onClick={() => setActiveTab('saved')}
          active={activeTab === 'saved'}
          isLast={true}
        >
          📊 Saved Charts
        </TabButton>
      </TabNavigation>

      {/* Tab Content */}
      {activeTab === 'new' ? (
        <TabContent style={{ height: 'fit-content', overflow: 'visible' }}>
        <FormContainer style={{ flex: 1, overflow: 'visible', height: 'fit-content' }}>
          <div style={{ position: 'relative', zIndex: 3, padding: '0px 24px 16px 24px' }}>
          <h2>
            {prefilledData ? 'Marriage Analysis - Enter Details' : 'Birth Details'}
          </h2>
          {prefilledData && (
            <div style={{ marginBottom: '15px', padding: '10px', background: 'rgba(76, 175, 80, 0.1)', border: '1px solid #4caf50', borderRadius: '8px', color: '#4caf50', fontSize: '0.9rem' }}>
              ✓ Form pre-filled from homepage. Please verify and complete the details.
            </div>
          )}
          <form onSubmit={(e) => {
            // Additional form-level validation
            if (!formData.latitude || !formData.longitude || formData.latitude === null || formData.longitude === null) {
              e.preventDefault();
              e.stopPropagation();
              toast.error('🚫 Form blocked: Select location from suggestions!');
              return false;
            }
            handleSubmit(e);
          }}>
        <FormField>
          <Label>{FORM_FIELDS.name.label}</Label>
          <Input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleInputChange}
            placeholder={FORM_FIELDS.name.placeholder}
            error={errors.name}
          />
          {errors.name && <span className="error">{errors.name}</span>}
        </FormField>

        <FormField>
          <Label>Gender</Label>
          <Select
            name="gender"
            value={formData.gender}
            onChange={handleInputChange}
          >
            <option value="">Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </Select>
        </FormField>

        <FormField>
          <Label>{FORM_FIELDS.date.label}</Label>
          <Input
            type="date"
            name="date"
            value={formData.date}
            onChange={handleInputChange}
            min={FORM_FIELDS.date.validation.min}
            max={FORM_FIELDS.date.validation.max}
            error={errors.date}
          />
          {errors.date && <span className="error">{errors.date}</span>}
        </FormField>

        <FormField>
          <Label>{FORM_FIELDS.time.label}</Label>
          <Input
            type="time"
            name="time"
            value={formData.time}
            onChange={handleInputChange}
            error={errors.time}
          />
          {errors.time && <span className="error">{errors.time}</span>}
        </FormField>

        <FormField>
          <Label>{FORM_FIELDS.place.label} *</Label>
          <AutocompleteContainer>
            <Input
              type="text"
              name="place"
              value={formData.place}
              onChange={handleInputChange}
              placeholder="Type to search and select from suggestions..."
              error={errors.place}
              autoComplete="off"
              onBlur={() => {
                setTimeout(() => setShowSuggestions(false), 200);
              }}
              style={{
                borderColor: formData.latitude && formData.longitude ? '#4caf50' : (errors.place ? '#f44336' : '#ddd')
              }}
            />
            {showSuggestions && suggestions.length > 0 && (
              <SuggestionList>
                {suggestions.map(suggestion => (
                  <SuggestionItem
                    key={suggestion.id}
                    onClick={() => handlePlaceSelect(suggestion)}
                  >
                    {suggestion.name}
                  </SuggestionItem>
                ))}
              </SuggestionList>
            )}
            {formData.place && (!formData.latitude || formData.latitude === null) && (
              <div style={{ color: '#f44336', fontSize: '12px', marginTop: '4px', fontWeight: '500' }}>
                ⚠️ You must select from suggestions - manual entry will not work
              </div>
            )}
            {formData.latitude && formData.longitude && (
              <div style={{ color: '#4caf50', fontSize: '12px', marginTop: '4px' }}>
                ✓ Location confirmed: {formData.latitude.toFixed(4)}, {formData.longitude.toFixed(4)}
              </div>
            )}
          </AutocompleteContainer>
          {errors.place && <span className="error">{errors.place}</span>}
        </FormField>

        <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
          <Button 
            type="submit"
            disabled={!formData.latitude || !formData.longitude || formData.latitude === null || formData.longitude === null}
            style={{
              opacity: (!formData.latitude || !formData.longitude || formData.latitude === null || formData.longitude === null) ? 0.5 : 1,
              cursor: (!formData.latitude || !formData.longitude || formData.latitude === null || formData.longitude === null) ? 'not-allowed' : 'pointer'
            }}
          >
            {editingChart ? 'Update Chart' : prefilledData ? 'Generate Marriage Analysis' : 'Calculate Birth Chart'}
          </Button>
          {editingChart && (
            <Button type="button" onClick={cancelEdit} style={{ background: '#6c757d' }}>
              Cancel
            </Button>
          )}
          </div>
          </form>
          </div>
        </FormContainer>
        </TabContent>
      ) : (
        <div style={{ padding: '10px', height: '600px', overflow: 'auto' }}>
          <SearchInput
            type="text"
            placeholder="Search by name..."
            value={searchQuery}
            onChange={handleSearchChange}
            style={{ marginBottom: '10px' }}
          />
          <ChartsList style={{ height: '520px', overflow: 'auto' }}>
            {existingCharts.map(chart => (
              <ChartItem key={chart.id}>
                <div onClick={() => selectExistingChart(chart)} style={{ flex: 1, cursor: 'pointer' }}>
                  <strong>{chart.name}</strong><br/>
                  {chart.date} at {chart.time}<br/>
                  <small>Created: {new Date(chart.created_at).toLocaleDateString()}</small>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <button 
                    onClick={(e) => { e.stopPropagation(); editChart(chart); setActiveTab('new'); }}
                    style={{ padding: '4px 8px', fontSize: '12px', background: '#ff6f00', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                  >
                    Edit
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); deleteChart(chart.id); }}
                    style={{ padding: '4px 8px', fontSize: '12px', background: '#e91e63', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                  >
                    Delete
                  </button>
                </div>
              </ChartItem>
            ))}
            {existingCharts.length === 0 && (
              <div style={{ textAlign: 'center', color: 'rgba(255, 255, 255, 0.7)', padding: '1rem' }}>
                {searchQuery ? 'No charts found' : 'No saved charts'}
              </div>
            )}
          </ChartsList>
        </div>
      )}
    </TabContainer>
  );
};

export default BirthForm;