import React, { useState, useEffect } from 'react';
import './LocationFinder.css';

const LocationFinder = ({ isOpen, onClose, onLocationSelect, currentLocation }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredLocations, setFilteredLocations] = useState([]);

  const locations = [
    { name: 'New Delhi, India', latitude: 28.6139, longitude: 77.2090 },
    { name: 'Mumbai, India', latitude: 19.0760, longitude: 72.8777 },
    { name: 'Bangalore, India', latitude: 12.9716, longitude: 77.5946 },
    { name: 'Chennai, India', latitude: 13.0827, longitude: 80.2707 },
    { name: 'Kolkata, India', latitude: 22.5726, longitude: 88.3639 },
    { name: 'Hyderabad, India', latitude: 17.3850, longitude: 78.4867 },
    { name: 'Pune, India', latitude: 18.5204, longitude: 73.8567 },
    { name: 'Ahmedabad, India', latitude: 23.0225, longitude: 72.5714 },
    { name: 'Jaipur, India', latitude: 26.9124, longitude: 75.7873 },
    { name: 'Lucknow, India', latitude: 26.8467, longitude: 80.9462 },
    { name: 'Kanpur, India', latitude: 26.4499, longitude: 80.3319 },
    { name: 'Nagpur, India', latitude: 21.1458, longitude: 79.0882 },
    { name: 'Indore, India', latitude: 22.7196, longitude: 75.8577 },
    { name: 'Thane, India', latitude: 19.2183, longitude: 72.9781 },
    { name: 'Bhopal, India', latitude: 23.2599, longitude: 77.4126 },
    { name: 'Visakhapatnam, India', latitude: 17.6868, longitude: 83.2185 },
    { name: 'Pimpri-Chinchwad, India', latitude: 18.6298, longitude: 73.7997 },
    { name: 'Patna, India', latitude: 25.5941, longitude: 85.1376 },
    { name: 'Vadodara, India', latitude: 22.3072, longitude: 73.1812 },
    { name: 'Ghaziabad, India', latitude: 28.6692, longitude: 77.4538 }
  ];

  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredLocations(locations);
    } else {
      const filtered = locations.filter(location =>
        location.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredLocations(filtered);
    }
  }, [searchTerm]);

  const handleLocationSelect = (location) => {
    onLocationSelect({
      name: location.name,
      latitude: location.latitude,
      longitude: location.longitude,
      timezone: 'UTC+5:30'
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="location-finder-overlay">
      <div className="location-finder-modal">
        <div className="modal-header">
          <h3>Select Location</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="search-section">
          <input
            type="text"
            placeholder="Search for a city..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
            autoFocus
          />
        </div>

        <div className="locations-list">
          {filteredLocations.map((location, index) => (
            <div
              key={index}
              className={`location-item ${currentLocation.name === location.name ? 'current' : ''}`}
              onClick={() => handleLocationSelect(location)}
            >
              <div className="location-name">{location.name}</div>
              <div className="location-coords">
                {location.latitude.toFixed(2)}°, {location.longitude.toFixed(2)}°
              </div>
              {currentLocation.name === location.name && (
                <div className="current-badge">Current</div>
              )}
            </div>
          ))}
          
          {filteredLocations.length === 0 && (
            <div className="no-results">
              No locations found for "{searchTerm}"
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LocationFinder;