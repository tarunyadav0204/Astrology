import React, { useState, useEffect } from 'react';
import './HouseCombinations.css';

const HouseCombinations = () => {
  const [combinations, setCombinations] = useState([]);
  const [specifications, setSpecifications] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [selectedHouses, setSelectedHouses] = useState([]);
  const [searchText, setSearchText] = useState('');
  const [houseLogic, setHouseLogic] = useState('AND');
  const [formData, setFormData] = useState({
    houses: [],
    positive_prediction: '',
    negative_prediction: '',
    combination_name: '',
    is_active: true
  });

  useEffect(() => {
    fetchCombinations();
    fetchSpecifications();
  }, []);

  const fetchCombinations = async () => {
    try {
      const response = await fetch('/api/house-combinations', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setCombinations(data.combinations);
    } catch (error) {
      console.error('Error fetching combinations:', error);
    }
  };

  const fetchSpecifications = async () => {
    try {
      const response = await fetch('/api/house-specifications', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setSpecifications(data.specifications);
    } catch (error) {
      console.error('Error fetching specifications:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const url = editingId 
      ? `/api/house-combinations/${editingId}`
      : '/api/house-combinations';
    
    const method = editingId ? 'PUT' : 'POST';
    
    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        fetchCombinations();
        resetForm();
      }
    } catch (error) {
      console.error('Error saving combination:', error);
    }
  };

  const handleEdit = (combination) => {
    setFormData(combination);
    setEditingId(combination.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this combination?')) {
      try {
        await fetch(`/api/house-combinations/${id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        fetchCombinations();
      } catch (error) {
        console.error('Error deleting combination:', error);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      houses: [],
      positive_prediction: '',
      negative_prediction: '',
      combination_name: '',
      is_active: true
    });
    setEditingId(null);
    setShowForm(false);
  };

  const generateCombinations = async (massive = false) => {
    const message = massive 
      ? 'Generate ALL possible house combinations? This will create 70+ combinations automatically.'
      : 'Generate new combinations from house specifications? This will create multiple combinations automatically.';
    
    if (!window.confirm(message)) return;
    
    try {
      const response = await fetch('/api/generate-combinations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ 
          max_per_theme: massive ? 50 : 8,
          massive: massive
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Generated ${result.generated_count} combinations, saved ${result.saved_count} new ones to database`);
        fetchCombinations();
      } else {
        alert('Failed to generate combinations');
      }
    } catch (error) {
      console.error('Error generating combinations:', error);
      alert('Error generating combinations');
    }
  };

  const handleSearchHouseToggle = (house) => {
    setSelectedHouses(prev => 
      prev.includes(house) 
        ? prev.filter(h => h !== house)
        : [...prev, house].sort((a, b) => a - b)
    );
  };

  const searchCombinations = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedHouses.length > 0) {
        params.append('houses', selectedHouses.join(','));
        params.append('house_logic', houseLogic);
      }
      if (searchText.trim()) {
        params.append('search_text', searchText.trim());
      }
      
      const response = await fetch(`/api/search-combinations?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCombinations(data.combinations);
      }
    } catch (error) {
      console.error('Error searching combinations:', error);
    }
  };

  const clearSearch = () => {
    setSelectedHouses([]);
    setSearchText('');
    setHouseLogic('AND');
    fetchCombinations();
  };

  const handleHouseToggle = (houseNum) => {
    const newHouses = formData.houses.includes(houseNum)
      ? formData.houses.filter(h => h !== houseNum)
      : [...formData.houses, houseNum].sort((a, b) => a - b);
    
    setFormData({ ...formData, houses: newHouses });
  };

  const getHouseSpecs = (houseNum) => {
    const spec = specifications.find(s => s.house_number === houseNum);
    return spec ? spec.specifications.join(', ') : '';
  };

  return (
    <div className="house-combinations">
      <div className="header">
        <h2>House Combinations Management</h2>
        <div className="header-actions">
          <button 
            className="add-btn"
            onClick={() => setShowForm(true)}
          >
            Add New Combination
          </button>
          <button 
            className="generate-btn"
            onClick={() => generateCombinations(false)}
          >
            🤖 Generate Themed
          </button>
          <button 
            className="massive-btn"
            onClick={() => generateCombinations(true)}
          >
            🚀 Generate ALL Combos
          </button>
        </div>
      </div>

      <div className="search-section">
        <div className="search-controls">
          <div className="house-selector">
            <label>Filter by Houses:</label>
            <div className="house-logic-selector">
              <label>
                <input
                  type="radio"
                  name="houseLogic"
                  value="AND"
                  checked={houseLogic === 'AND'}
                  onChange={(e) => setHouseLogic(e.target.value)}
                />
                AND (contains all selected houses)
              </label>
              <label>
                <input
                  type="radio"
                  name="houseLogic"
                  value="OR"
                  checked={houseLogic === 'OR'}
                  onChange={(e) => setHouseLogic(e.target.value)}
                />
                OR (contains any selected house)
              </label>
            </div>
            <div className="house-checkboxes">
              {[1,2,3,4,5,6,7,8,9,10,11,12].map(house => (
                <label key={house} className="house-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedHouses.includes(house)}
                    onChange={() => handleSearchHouseToggle(house)}
                  />
                  {house}
                </label>
              ))}
            </div>
          </div>
          <div className="text-search">
            <label>Search Text:</label>
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="Search in names and predictions..."
            />
          </div>
          <button className="search-btn" onClick={searchCombinations}>
            🔍 Search
          </button>
          <button className="clear-btn" onClick={clearSearch}>
            Clear
          </button>
        </div>
      </div>

      {showForm && (
        <div className="form-overlay">
          <div className="form-container">
            <h3>{editingId ? 'Edit' : 'Add'} House Combination</h3>
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Combination Name:</label>
                <input
                  type="text"
                  value={formData.combination_name}
                  onChange={(e) => setFormData({...formData, combination_name: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label>Select Houses:</label>
                <div className="house-grid">
                  {[1,2,3,4,5,6,7,8,9,10,11,12].map(houseNum => (
                    <div key={houseNum} className="house-item">
                      <label>
                        <input
                          type="checkbox"
                          checked={formData.houses.includes(houseNum)}
                          onChange={() => handleHouseToggle(houseNum)}
                        />
                        <span className="house-label">
                          House {houseNum}
                          <small>{getHouseSpecs(houseNum)}</small>
                        </span>
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>Positive Prediction:</label>
                <textarea
                  value={formData.positive_prediction}
                  onChange={(e) => setFormData({...formData, positive_prediction: e.target.value})}
                  rows="3"
                  required
                />
              </div>

              <div className="form-group">
                <label>Negative Prediction:</label>
                <textarea
                  value={formData.negative_prediction}
                  onChange={(e) => setFormData({...formData, negative_prediction: e.target.value})}
                  rows="3"
                  required
                />
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                  />
                  Active
                </label>
              </div>

              <div className="form-actions">
                <button type="submit">
                  {editingId ? 'Update' : 'Create'}
                </button>
                <button type="button" onClick={resetForm}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="combinations-list">
        {combinations.map(combo => (
          <div key={combo.id} className="combination-card">
            <div className="combo-header">
              <h4>{combo.combination_name}</h4>
              <div className="combo-actions">
                <button onClick={() => handleEdit(combo)}>Edit</button>
                <button onClick={() => handleDelete(combo.id)}>Delete</button>
              </div>
            </div>
            
            <div className="combo-houses">
              <strong>Houses:</strong> {combo.houses.join(', ')}
            </div>
            
            <div className="combo-predictions">
              <div className="positive">
                <strong>Positive:</strong> {combo.positive_prediction}
              </div>
              <div className="negative">
                <strong>Negative:</strong> {combo.negative_prediction}
              </div>
            </div>
            
            <div className="combo-status">
              Status: <span className={combo.is_active ? 'active' : 'inactive'}>
                {combo.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HouseCombinations;