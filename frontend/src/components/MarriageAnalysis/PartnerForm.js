import React, { useState, useEffect } from 'react';
import { locationService } from '../../services/locationService';
import { APP_CONFIG } from '../../config/app.config';
import BirthFormModal from '../BirthForm/BirthFormModal';

const emptyPartner = () => ({
  name: '',
  date: '',
  time: '',
  place: '',
  latitude: null,
  longitude: null
});

const mergePartnerState = (base, initial) => {
  if (!initial || typeof initial !== 'object') return base;
  return {
    ...base,
    name: initial.name ?? base.name,
    date: initial.date ?? base.date,
    time: initial.time ?? base.time,
    place: initial.place ?? base.place,
    latitude: initial.latitude !== undefined && initial.latitude !== '' ? initial.latitude : base.latitude,
    longitude: initial.longitude !== undefined && initial.longitude !== '' ? initial.longitude : base.longitude
  };
};

const chartToPartnerData = (chart) => {
  const time = chart.time != null ? String(chart.time) : '';
  const timeShort =
    time.length >= 8 && time[5] === ':' && time[7] === ':'
      ? time.slice(0, 5)
      : time;
  return {
    name: chart.name || '',
    date: chart.date || '',
    time: timeShort,
    place:
      chart.place ||
      (chart.latitude != null && chart.longitude != null
        ? `${chart.latitude}, ${chart.longitude}`
        : ''),
    latitude: chart.latitude ?? null,
    longitude: chart.longitude ?? null,
    timezone: chart.timezone
  };
};

const PartnerForm = ({ onSubmit, user, onLogin, initialBoy, initialGirl }) => {
  const [boyData, setBoyData] = useState(() => mergePartnerState(emptyPartner(), initialBoy));
  const [girlData, setGirlData] = useState(() => mergePartnerState(emptyPartner(), initialGirl));

  const [boySuggestions, setBoySuggestions] = useState([]);
  const [girlSuggestions, setGirlSuggestions] = useState([]);
  const [showBoySuggestions, setShowBoySuggestions] = useState(false);
  const [showGirlSuggestions, setShowGirlSuggestions] = useState(false);
  const [chartPickerTarget, setChartPickerTarget] = useState(null);

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
    if (!user) {
      setChartPickerTarget(null);
      return;
    }
    const pending = sessionStorage.getItem('kundli_pending_chart_select');
    if (pending === 'boy' || pending === 'girl') {
      sessionStorage.removeItem('kundli_pending_chart_select');
      setChartPickerTarget(pending);
    }
  }, [user]);

  const openChartPicker = (partner) => {
    if (!user) {
      sessionStorage.setItem('kundli_pending_chart_select', partner);
      onLogin?.();
      return;
    }
    setChartPickerTarget(partner);
  };

  const handleChartPick = (chart) => {
    const data = chartToPartnerData(chart);
    if (chartPickerTarget === 'boy') {
      setBoyData(data);
    } else if (chartPickerTarget === 'girl') {
      setGirlData(data);
    }
    setChartPickerTarget(null);
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
    } else if (name === 'place') {
      setGirlData(prev => ({
        ...prev,
        [name]: value,
        latitude: null,
        longitude: null
      }));
    } else {
      setGirlData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(boyData, girlData);
  };

  const isFormValid = () =>
    boyData.name &&
    boyData.date &&
    boyData.time &&
    boyData.latitude &&
    boyData.longitude &&
    girlData.name &&
    girlData.date &&
    girlData.time &&
    girlData.latitude &&
    girlData.longitude;

  const pickerTitle =
    chartPickerTarget === 'boy'
      ? "Select boy's chart"
      : chartPickerTarget === 'girl'
        ? "Select girl's chart"
        : 'Select Saved Chart';

  const pickerDescription =
    chartPickerTarget === 'boy'
      ? "Choose a saved birth chart for the boy's details."
      : chartPickerTarget === 'girl'
        ? "Choose a saved birth chart for the girl's details."
        : 'Choose from your previously saved birth charts';

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
                onClick={() => openChartPicker('boy')}
              >
                Select Saved Chart
              </button>
            </div>
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
            <div className="form-row">
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
                onClick={() => openChartPicker('girl')}
              >
                Select Saved Chart
              </button>
            </div>
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
            <div className="form-row">
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
          <button type="submit" className="btn-analyze" disabled={!isFormValid()}>
            Analyze Compatibility
          </button>
        </div>
      </form>

      <BirthFormModal
        isOpen={chartPickerTarget != null}
        onClose={() => setChartPickerTarget(null)}
        onSubmit={() => setChartPickerTarget(null)}
        onChartPick={handleChartPick}
        defaultActiveTab="saved"
        title={pickerTitle}
        description={pickerDescription}
      />
    </div>
  );
};

export default PartnerForm;
