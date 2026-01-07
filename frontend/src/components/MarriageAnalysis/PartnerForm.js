import React, { useState, useEffect } from 'react';
import { locationService } from '../../services/locationService';
import { apiService } from '../../services/apiService';
import { APP_CONFIG } from '../../config/app.config';

const PartnerForm = ({ onSubmit, user, onLogin }) => {
  const [boyData, setBoyData] = useState({
    name: '',
    date: '',
    time: '',
    place: '',
    latitude: null,
    longitude: null
  });

  const [girlData, setGirlData] = useState({
    name: '',
    date: '',
    time: '',
    place: '',
    latitude: null,
    longitude: null
  });

  const [boySuggestions, setBoySuggestions] = useState([]);
  const [girlSuggestions, setGirlSuggestions] = useState([]);
  const [showBoySuggestions, setShowBoySuggestions] = useState(false);
  const [showGirlSuggestions, setShowGirlSuggestions] = useState(false);
  const [savedCharts, setSavedCharts] = useState([]);
  const [showBoyCharts, setShowBoyCharts] = useState(false);
  const [showGirlCharts, setShowGirlCharts] = useState(false);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (boyData.place.length >= APP_CONFIG.location.minSearchLength && !boyData.latitude) {
        searchPlaces(boyData.place, 'boy');
      } else {
        setBoySuggestions([]);
        setShowBoySuggestions(false);
      }
    }, APP_CONFIG.location.debounceMs);

    return () => clearTimeout(debounceTimer);
  }, [boyData.place]);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (girlData.place.length >= APP_CONFIG.location.minSearchLength && !girlData.latitude) {
        searchPlaces(girlData.place, 'girl');
      } else {
        setGirlSuggestions([]);
        setShowGirlSuggestions(false);
      }
    }, APP_CONFIG.location.debounceMs);

    return () => clearTimeout(debounceTimer);
  }, [girlData.place]);

  useEffect(() => {
    // Only load saved charts if user is authenticated
    const token = localStorage.getItem('token');
    if (token) {
      loadSavedCharts();
    }
  }, []);

  const loadSavedCharts = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setSavedCharts([]);
      return;
    }
    
    try {
      const response = await apiService.getExistingCharts();
      setSavedCharts(response.charts || []);
    } catch (error) {
      console.error('Failed to load saved charts:', error);
      setSavedCharts([]);
    }
  };

  const selectSavedChart = (chart, partner) => {
    const chartData = {
      name: chart.name,
      date: chart.date,
      time: chart.time,
      place: `${chart.latitude}, ${chart.longitude}`,
      latitude: chart.latitude,
      longitude: chart.longitude,
      timezone: chart.timezone
    };
    
    if (partner === 'boy') {
      setBoyData(chartData);
      setShowBoyCharts(false);
    } else {
      setGirlData(chartData);
      setShowGirlCharts(false);
    }
  };

  const searchPlaces = async (query, partner) => {
    try {
      const results = await locationService.searchPlaces(query);
      if (partner === 'boy') {
        setBoySuggestions(results);
        setShowBoySuggestions(true);
      } else {
        setGirlSuggestions(results);
        setShowGirlSuggestions(true);
      }
    } catch (error) {
      console.error('Failed to search locations:', error);
    }
  };

  const handlePlaceSelect = (place, partner) => {
    if (partner === 'boy') {
      setBoyData(prev => ({
        ...prev,
        place: place.name,
        latitude: place.latitude,
        longitude: place.longitude,
        timezone: place.timezone
      }));
      setShowBoySuggestions(false);
      setBoySuggestions([]);
    } else {
      setGirlData(prev => ({
        ...prev,
        place: place.name,
        latitude: place.latitude,
        longitude: place.longitude,
        timezone: place.timezone
      }));
      setShowGirlSuggestions(false);
      setGirlSuggestions([]);
    }
  };

  const handleInputChange = (e, partner) => {
    const { name, value } = e.target;
    
    if (partner === 'boy') {
      if (name === 'place') {
        setBoyData(prev => ({ 
          ...prev, 
          [name]: value,
          latitude: null,
          longitude: null
        }));
      } else {
        setBoyData(prev => ({ ...prev, [name]: value }));
      }
    } else {
      if (name === 'place') {
        setGirlData(prev => ({ 
          ...prev, 
          [name]: value,
          latitude: null,
          longitude: null
        }));
      } else {
        setGirlData(prev => ({ ...prev, [name]: value }));
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(boyData, girlData);
  };

  const isFormValid = () => {
    return boyData.name && boyData.date && boyData.time && boyData.latitude && boyData.longitude &&
           girlData.name && girlData.date && girlData.time && girlData.latitude && girlData.longitude;
  };

  return (
    <div className="partner-form">
      <h3>👫 Enter Partner Details</h3>
      <p>Please provide birth details for both partners to analyze compatibility</p>
      
      <form onSubmit={handleSubmit}>
        <div className="partners-container">
          <div className="partner-section">
            <div className="partner-header">
              <h4>👨 Boy's Details</h4>
              <button 
                type="button" 
                className="btn-select-chart"
                onClick={() => {
                  if (!user) {
                    onLogin && onLogin();
                  } else {
                    setShowBoyCharts(!showBoyCharts);
                  }
                }}
              >
                Select Saved Chart
              </button>
            </div>
            {showBoyCharts && (
              <div className="saved-charts-dropdown">
                <h5>Select Boy's Chart:</h5>
                <div className="charts-list">
                  {savedCharts.map(chart => (
                    <div 
                      key={chart.id} 
                      className="chart-item"
                      onClick={() => selectSavedChart(chart, 'boy')}
                    >
                      <strong>{chart.name}</strong><br/>
                      <small>{chart.date} at {chart.time}</small>
                    </div>
                  ))}
                  {savedCharts.length === 0 && (
                    <div className="no-charts">No saved charts found</div>
                  )}
                </div>
              </div>
            )}
            <div className="form-group">
              <label>Name</label>
              <input
                type="text"
                name="name"
                value={boyData.name}
                onChange={(e) => handleInputChange(e, 'boy')}
                placeholder="Enter name"
                required
              />
            </div>
            <div className="form-group">
              <label>Date of Birth</label>
              <input
                type="date"
                name="date"
                value={boyData.date}
                onChange={(e) => handleInputChange(e, 'boy')}
                required
              />
            </div>
            <div className="form-group">
              <label>Time of Birth</label>
              <input
                type="time"
                name="time"
                value={boyData.time}
                onChange={(e) => handleInputChange(e, 'boy')}
                required
              />
            </div>
            <div className="form-group">
              <label>Place of Birth</label>
              <div className="autocomplete-container">
                <input
                  type="text"
                  name="place"
                  value={boyData.place}
                  onChange={(e) => handleInputChange(e, 'boy')}
                  placeholder="Search for city..."
                  autoComplete="off"
                  required
                  onBlur={() => {
                    setTimeout(() => setShowBoySuggestions(false), 200);
                  }}
                />
                {showBoySuggestions && boySuggestions.length > 0 && (
                  <div className="suggestion-list">
                    {boySuggestions.map(suggestion => (
                      <div
                        key={suggestion.id}
                        className="suggestion-item"
                        onClick={() => handlePlaceSelect(suggestion, 'boy')}
                      >
                        {suggestion.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="partner-section">
            <div className="partner-header">
              <h4>👩 Girl's Details</h4>
              <button 
                type="button" 
                className="btn-select-chart"
                onClick={() => {
                  if (!user) {
                    onLogin && onLogin();
                  } else {
                    setShowGirlCharts(!showGirlCharts);
                  }
                }}
              >
                Select Saved Chart
              </button>
            </div>
            {showGirlCharts && (
              <div className="saved-charts-dropdown">
                <h5>Select Girl's Chart:</h5>
                <div className="charts-list">
                  {savedCharts.map(chart => (
                    <div 
                      key={chart.id} 
                      className="chart-item"
                      onClick={() => selectSavedChart(chart, 'girl')}
                    >
                      <strong>{chart.name}</strong><br/>
                      <small>{chart.date} at {chart.time}</small>
                    </div>
                  ))}
                  {savedCharts.length === 0 && (
                    <div className="no-charts">No saved charts found</div>
                  )}
                </div>
              </div>
            )}
            <div className="form-group">
              <label>Name</label>
              <input
                type="text"
                name="name"
                value={girlData.name}
                onChange={(e) => handleInputChange(e, 'girl')}
                placeholder="Enter name"
                required
              />
            </div>
            <div className="form-group">
              <label>Date of Birth</label>
              <input
                type="date"
                name="date"
                value={girlData.date}
                onChange={(e) => handleInputChange(e, 'girl')}
                required
              />
            </div>
            <div className="form-group">
              <label>Time of Birth</label>
              <input
                type="time"
                name="time"
                value={girlData.time}
                onChange={(e) => handleInputChange(e, 'girl')}
                required
              />
            </div>
            <div className="form-group">
              <label>Place of Birth</label>
              <div className="autocomplete-container">
                <input
                  type="text"
                  name="place"
                  value={girlData.place}
                  onChange={(e) => handleInputChange(e, 'girl')}
                  placeholder="Search for city..."
                  autoComplete="off"
                  required
                  onBlur={() => {
                    setTimeout(() => setShowGirlSuggestions(false), 200);
                  }}
                />
                {showGirlSuggestions && girlSuggestions.length > 0 && (
                  <div className="suggestion-list">
                    {girlSuggestions.map(suggestion => (
                      <div
                        key={suggestion.id}
                        className="suggestion-item"
                        onClick={() => handlePlaceSelect(suggestion, 'girl')}
                      >
                        {suggestion.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button 
            type="submit" 
            className="btn-analyze"
            disabled={!isFormValid()}
          >
            Analyze Compatibility
          </button>
        </div>
      </form>
    </div>
  );
};

export default PartnerForm;