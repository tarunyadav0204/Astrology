import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { useAstrology } from '../../context/AstrologyContext';
import { apiService } from '../../services/apiService';
import { locationService } from '../../services/locationService';
import { FORM_FIELDS, VALIDATION_MESSAGES } from '../../config/form.config';
import { APP_CONFIG } from '../../config/app.config';
import { TwoPanelContainer, FormPanel, ChartsPanel, FormContainer, FormField, Input, Select, Label, Button, AutocompleteContainer, SuggestionList, SuggestionItem, SearchInput, ChartsList, ChartItem } from './BirthForm.styles';

const BirthForm = ({ onSubmit, onLogout }) => {
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
    loadExistingCharts();
    
    // Pre-populate form if birthData exists in context (from edit action)
    if (birthData && birthData.id) {
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
  }, [birthData]);

  const loadExistingCharts = async (search = '') => {
    try {
      const response = await apiService.getExistingCharts(search);
      setExistingCharts(response.charts || []);
    } catch (error) {
      console.error('Failed to load existing charts:', error);
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
      onSubmit();
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

    if (!formData.latitude || !formData.longitude) {
      newErrors.place = 'Please select a place from suggestions';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast.error('Please fix the errors in the form');
      return;
    }

    setLoading(true);
    
    try {
      if (editingChart) {
        await apiService.updateChart(editingChart.id, formData);
        toast.success('Chart updated successfully!');
        loadExistingCharts(searchQuery);
        cancelEdit();
      } else {
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

  return (
    <TwoPanelContainer style={{ overflow: 'visible' }}>
      <FormPanel>
        <FormContainer>
          <h2 style={{ marginBottom: '20px' }}>Birth Details</h2>
      

      <form onSubmit={handleSubmit}>
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
          <Label>{FORM_FIELDS.place.label}</Label>
          <AutocompleteContainer>
            <Input
              type="text"
              name="place"
              value={formData.place}
              onChange={handleInputChange}
              placeholder={FORM_FIELDS.place.placeholder}
              error={errors.place}
              autoComplete="off"
              onBlur={() => {
                setTimeout(() => setShowSuggestions(false), 200);
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
          </AutocompleteContainer>
          {errors.place && <span className="error">{errors.place}</span>}
        </FormField>

        <div style={{ display: 'flex', gap: '12px' }}>
          <Button type="submit">
            {editingChart ? 'Update Chart' : 'Calculate Birth Chart'}
          </Button>
          {editingChart && (
            <Button type="button" onClick={cancelEdit} style={{ background: '#6c757d' }}>
              Cancel
            </Button>
          )}
        </div>
      </form>
    </FormContainer>
      </FormPanel>
      
      <ChartsPanel>
        <h3>📊 Saved Charts</h3>
        <SearchInput
          type="text"
          placeholder="Search by name..."
          value={searchQuery}
          onChange={handleSearchChange}
        />
        <ChartsList>
          {existingCharts.map(chart => (
            <ChartItem key={chart.id}>
              <div onClick={() => selectExistingChart(chart)} style={{ flex: 1, cursor: 'pointer' }}>
                <strong>{chart.name}</strong><br/>
                {chart.date} at {chart.time}<br/>
                <small>Created: {new Date(chart.created_at).toLocaleDateString()}</small>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <button 
                  onClick={(e) => { e.stopPropagation(); editChart(chart); }}
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
            <div style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
              {searchQuery ? 'No charts found' : 'No saved charts'}
            </div>
          )}
        </ChartsList>
      </ChartsPanel>
    </TwoPanelContainer>
  );
};

export default BirthForm;