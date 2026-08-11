import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import { useAstrology } from '../../context/AstrologyContext';
import { apiService } from '../../services/apiService';
import { locationService } from '../../services/locationService';
import { FORM_FIELDS, VALIDATION_MESSAGES } from '../../config/form.config';
import { APP_CONFIG } from '../../config/app.config';
import { FormContainer, FormField, Input, Select, Label, Button, AutocompleteContainer, SuggestionList, SuggestionItem, SearchInput, ChartsList, ChartItem, LoadMoreButton, TabContainer, TabNavigation, TabButton, TabContent } from './BirthForm.styles';

const SAVED_CHARTS_PAGE_SIZE = 10;

const BirthForm = ({
  onSubmit,
  onLogout,
  onChartPick,
  pickModeTitle,
  pickModeDescription,
  prefilledData,
  showCloseButton,
  onClose,
  defaultActiveTab = 'saved',
}) => {
  const isPickMode = Boolean(onChartPick);
  const { birthData, setBirthData, setChartData, setLoading, setError } = useAstrology();
  
  const [formData, setFormData] = useState({
    name: '',
    date: '',
    time: '',
    place: '',
    latitude: null,
    longitude: null,
    gender: ''
  });
  
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [errors, setErrors] = useState({});
  const [existingCharts, setExistingCharts] = useState([]);
  const [editingChart, setEditingChart] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchDebounce, setSearchDebounce] = useState(null);
  const [chartsListLoading, setChartsListLoading] = useState(false);
  const [chartsLoadingMore, setChartsLoadingMore] = useState(false);
  const [chartsHasMore, setChartsHasMore] = useState(false);
  const [chartsTotal, setChartsTotal] = useState(0);
  const chartsOffsetRef = useRef(0);

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
      loadExistingCharts('', { reset: true });
    }
    
    // Pre-populate form if prefilledData is provided (from homepage matching)
    if (prefilledData && prefilledData.person1) {
      setFormData({
        name: prefilledData.person1.name || '',
        date: prefilledData.person1.date || '',
        time: prefilledData.person1.time || '',
        place: prefilledData.person1.place || '',
        latitude: prefilledData.person1.latitude ?? null,
        longitude: prefilledData.person1.longitude ?? null,
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
        gender: birthData.gender || ''
      });
    }
  }, [birthData, prefilledData]);

  const loadExistingCharts = async (search = '', { reset = true } = {}) => {
    const token = localStorage.getItem('token');
    if (!token) {
      setExistingCharts([]);
      setChartsHasMore(false);
      setChartsTotal(0);
      chartsOffsetRef.current = 0;
      return;
    }

    const nextOffset = reset ? 0 : chartsOffsetRef.current;

    try {
      if (reset) {
        setChartsListLoading(true);
      } else {
        setChartsLoadingMore(true);
      }

      const response = await apiService.getExistingCharts(
        search,
        SAVED_CHARTS_PAGE_SIZE,
        nextOffset
      );
      const charts = response.charts || [];

      if (reset) {
        setExistingCharts(charts);
      } else {
        setExistingCharts((prev) => [...prev, ...charts]);
      }

      chartsOffsetRef.current = nextOffset + charts.length;
      setChartsHasMore(Boolean(response.has_more));
      setChartsTotal(response.total ?? 0);
    } catch (error) {
      console.error('Failed to load existing charts:', error);
      if (reset) {
        setExistingCharts([]);
        chartsOffsetRef.current = 0;
        setChartsHasMore(false);
        setChartsTotal(0);
      }
    } finally {
      setChartsListLoading(false);
      setChartsLoadingMore(false);
    }
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);

    if (searchDebounce) clearTimeout(searchDebounce);

    const timeout = setTimeout(() => {
      loadExistingCharts(query, { reset: true });
    }, 300);

    setSearchDebounce(timeout);
  };

  const handleLoadMoreCharts = () => {
    if (chartsLoadingMore || chartsListLoading || !chartsHasMore) return;
    loadExistingCharts(searchQuery, { reset: false });
  };

  const selectExistingChart = async (chart) => {
    if (onChartPick) {
      onChartPick(chart);
      return;
    }

    try {
      const birthData = {
        name: chart.name,
        date: chart.date,
        time: chart.time,
        latitude: chart.latitude,
        longitude: chart.longitude,
        place: chart.place || '',
        gender: chart.gender || '',
        chart_id: chart.id
      };
      
      const [chartData, yogiData] = await Promise.all([
        apiService.calculateChartOnly(birthData),
        apiService.calculateYogi(birthData)
      ]);
      
      // Merge Yogi data into chart data
      const enhancedChartData = {
        ...chartData,
        yogiData: yogiData,
        id: chart.id
      };
      
      const selectedBirthData = {
        name: chart.name,
        date: chart.date,
        time: chart.time,
        place: chart.place || `${chart.latitude}, ${chart.longitude}`,
        latitude: chart.latitude,
        longitude: chart.longitude,
        gender: chart.gender || '',
        chart_id: chart.id
      };
      setBirthData(selectedBirthData);
      
      setChartData(enhancedChartData);
      toast.success('Chart loaded successfully!');
      
      // Call onSubmit to trigger parent component logic
      if (onSubmit) {
        onSubmit(selectedBirthData);
      } else if (onClose) {
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
      gender: chart.gender || ''
    });
  };

  const deleteChart = async (chartId) => {
    if (window.confirm('Are you sure you want to delete this chart?')) {
      try {
        await apiService.deleteChart(chartId);
        toast.success('Chart deleted successfully!');
        loadExistingCharts(searchQuery, { reset: true });
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
        longitude: null
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
      longitude: place.longitude
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
        const chartData = await apiService.calculateChartOnly(formData);
        await apiService.updateChart(editingChart.id, formData);

        // Keep in-memory context synced with edited values (especially gender) for analysis pages.
        const editedBirthData = {
          ...formData,
          chart_id: editingChart.id,
        };
        setBirthData(editedBirthData);
        setChartData({
          ...chartData,
          id: editingChart.id,
        });

        toast.success('Chart updated successfully!');
        loadExistingCharts(searchQuery, { reset: true });

        // Close modal after successful edit; do not reset form first.
        if (onSubmit) {
          onSubmit(editedBirthData);
        } else if (onClose) {
          onClose();
        }
        return;
      } else {
        if (!formData.latitude || !formData.longitude || formData.latitude === null || formData.longitude === null) {
          throw new Error('Coordinates missing - select from suggestions required');
        }
        
        const [chartData, yogiData] = await Promise.all([
          apiService.calculateChart(formData),
          apiService.calculateYogi(formData)
        ]);
        
        const enhancedChartData = {
          ...chartData,
          yogiData: yogiData
        };
        
        setBirthData(birthData);
        setChartData(enhancedChartData);
        toast.success('Birth chart calculated successfully!');
        onSubmit(birthData);
      }
    } catch (error) {
      setError(error.message);
      toast.error(error.message);
    }
  };

  const [activeTab, setActiveTab] = useState(() => {
    if (isPickMode) return 'saved';
    return defaultActiveTab === 'new' ? 'new' : 'saved';
  });

  const headerTitle = isPickMode
    ? (pickModeTitle || 'Select Saved Chart')
    : (activeTab === 'new' ? 'Create Birth Chart' : 'Select Saved Chart');
  const headerSubtitle = isPickMode
    ? (pickModeDescription || 'Choose from your previously saved birth charts')
    : (activeTab === 'new'
      ? 'Add accurate birth information to generate your Vedic chart'
      : 'Choose from your previously saved birth charts');

  return (
    <TabContainer key="fixed-tabs-v2">
      {onClose && (
        <div className="birth-form-shell__header">
          <span className="birth-form-shell__eyebrow">
            {isPickMode ? 'Your charts' : 'Birth chart workspace'}
          </span>
          <h2>{headerTitle}</h2>
          <p>{headerSubtitle}</p>
          <button
            type="button"
            className="birth-form-shell__close"
            onClick={onClose}
            aria-label="Close birth chart dialog"
          >
            <span aria-hidden>×</span>
          </button>
        </div>
      )}
      {!isPickMode && (
        <TabNavigation>
          <TabButton
            type="button"
            onClick={() => setActiveTab('new')}
            active={activeTab === 'new'}
            isFirst={true}
          >
            <span aria-hidden>＋</span> New Chart
          </TabButton>
          <TabButton
            type="button"
            onClick={() => setActiveTab('saved')}
            active={activeTab === 'saved'}
            isLast={true}
          >
            <span aria-hidden>▤</span> Saved Charts
          </TabButton>
        </TabNavigation>
      )}

      {/* Tab Content */}
      {!isPickMode && activeTab === 'new' ? (
        <TabContent>
        <FormContainer>
          <div className="birth-form-panel">
          <div className="birth-form-panel__intro">
            <p>Use the exact birth time and select a place from search for an accurate chart.</p>
            <span className="birth-form-panel__required">* Required</span>
          </div>
          {prefilledData && (
            <div className="birth-form-notice birth-form-notice--success">
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
          }} className="birth-form-grid">
        <FormField className="birth-form-field birth-form-field--name">
          <Label>{FORM_FIELDS.name.label}{FORM_FIELDS.name.required ? ' *' : ''}</Label>
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

        <FormField className="birth-form-field birth-form-field--gender">
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

        <FormField className="birth-form-field">
          <Label>{FORM_FIELDS.date.label}{FORM_FIELDS.date.required ? ' *' : ''}</Label>
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

        <FormField className="birth-form-field">
          <Label>{FORM_FIELDS.time.label}{FORM_FIELDS.time.required ? ' *' : ''}</Label>
          <Input
            type="time"
            name="time"
            value={formData.time}
            onChange={handleInputChange}
            error={errors.time}
          />
          {errors.time && <span className="error">{errors.time}</span>}
        </FormField>

        <FormField className="birth-form-field birth-form-field--place">
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
              className={formData.latitude && formData.longitude ? 'is-confirmed' : ''}
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
            {formData.place && (!formData.latitude || formData.latitude === null) && !errors.place && (
              <div className="birth-form-location-status birth-form-location-status--warning">
                Select a result from the suggestions to confirm this location.
              </div>
            )}
            {formData.latitude && formData.longitude && (
              <div className="birth-form-location-status birth-form-location-status--success">
                ✓ Location confirmed
              </div>
            )}
          </AutocompleteContainer>
          {errors.place && <span className="error">{errors.place}</span>}
        </FormField>

        <div className="birth-form-actions">
          <Button 
            type="submit"
            disabled={!formData.latitude || !formData.longitude || formData.latitude === null || formData.longitude === null}
          >
            {editingChart ? 'Update Chart' : prefilledData ? 'Generate Marriage Analysis' : 'Calculate Birth Chart'}
          </Button>
          {editingChart && (
            <Button type="button" onClick={cancelEdit} className="birth-form-button--secondary">
              Cancel
            </Button>
          )}
          </div>
          </form>
          </div>
        </FormContainer>
        </TabContent>
      ) : (
        <div className="saved-charts-panel">
          <div className="saved-charts-panel__toolbar">
            <SearchInput
              type="search"
              aria-label="Search saved charts"
              placeholder="Search saved charts by name"
              value={searchQuery}
              onChange={handleSearchChange}
            />
            <span className="saved-charts-panel__count">
              {chartsTotal || existingCharts.length} {(chartsTotal || existingCharts.length) === 1 ? 'chart' : 'charts'}
            </span>
          </div>
          {chartsListLoading && existingCharts.length === 0 ? (
            <div className="saved-charts-state">
              <span className="saved-charts-state__loader" aria-hidden />
              Loading your charts…
            </div>
          ) : null}
          <ChartsList>
            {existingCharts.map(chart => (
              <ChartItem key={chart.id} className="saved-chart-card">
                <button
                  type="button"
                  className="saved-chart-main"
                  onClick={() => selectExistingChart(chart)}
                  aria-label={`Open chart for ${chart.name}`}
                >
                  <span className="saved-chart-avatar" aria-hidden>
                    {String(chart.name || '?').trim().charAt(0).toUpperCase()}
                  </span>
                  <span className="saved-chart-copy">
                    <strong>{chart.name}</strong>
                    <span>{chart.date} · {chart.time}</span>
                    <small>{chart.place || 'Birth place not saved'}</small>
                  </span>
                  <span className="saved-chart-open" aria-hidden>→</span>
                </button>
                {!isPickMode && (
                  <div className="saved-chart-actions">
                    <button
                      type="button"
                      className="saved-chart-action saved-chart-action--edit"
                      onClick={(e) => { e.stopPropagation(); editChart(chart); setActiveTab('new'); }}
                      aria-label={`Edit ${chart.name}`}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="saved-chart-action saved-chart-action--delete"
                      onClick={(e) => { e.stopPropagation(); deleteChart(chart.id); }}
                      aria-label={`Delete ${chart.name}`}
                    >
                      Delete
                    </button>
                  </div>
                )}
                <span className="saved-chart-created">
                  Saved {new Date(chart.created_at).toLocaleDateString()}
                </span>
              </ChartItem>
            ))}
            {!chartsListLoading && existingCharts.length === 0 && (
              <div className="saved-charts-state saved-charts-state--empty">
                <span aria-hidden>{searchQuery ? '⌕' : '◇'}</span>
                <strong>{searchQuery ? 'No matching charts' : 'No saved charts yet'}</strong>
                <p>{searchQuery ? 'Try a different name.' : 'Create a new chart to see it here.'}</p>
              </div>
            )}
          </ChartsList>
          {chartsHasMore && !chartsListLoading && (
            <LoadMoreButton
              type="button"
              onClick={handleLoadMoreCharts}
              disabled={chartsLoadingMore}
            >
              {chartsLoadingMore
                ? 'Loading...'
                : `Load more (${existingCharts.length}/${chartsTotal || '?'})`}
            </LoadMoreButton>
          )}
        </div>
      )}
    </TabContainer>
  );
};

export default BirthForm;
