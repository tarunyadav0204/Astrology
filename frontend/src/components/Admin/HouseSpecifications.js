import React, { useState, useEffect } from 'react';
import './HouseSpecifications.css';

const HouseSpecifications = () => {
  const [specifications, setSpecifications] = useState([]);
  const [editingHouse, setEditingHouse] = useState(null);
  const [formData, setFormData] = useState({
    house_number: 1,
    specifications: []
  });
  const [newSpec, setNewSpec] = useState('');

  useEffect(() => {
    fetchSpecifications();
  }, []);

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

  const handleEdit = (spec) => {
    setEditingHouse(spec.house_number);
    setFormData({
      house_number: spec.house_number,
      specifications: [...spec.specifications]
    });
  };

  const handleSave = async () => {
    try {
      const response = await fetch(`/api/house-specifications/${formData.house_number}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          house_number: formData.house_number,
          specifications: formData.specifications
        })
      });
      
      if (response.ok) {
        fetchSpecifications();
        setEditingHouse(null);
        setFormData({ house_number: 1, specifications: [] });
      }
    } catch (error) {
      console.error('Error saving specification:', error);
    }
  };

  const handleCancel = () => {
    setEditingHouse(null);
    setFormData({ house_number: 1, specifications: [] });
    setNewSpec('');
  };

  const addSpecification = () => {
    if (newSpec.trim()) {
      setFormData({
        ...formData,
        specifications: [...formData.specifications, newSpec.trim()]
      });
      setNewSpec('');
    }
  };

  const removeSpecification = (index) => {
    setFormData({
      ...formData,
      specifications: formData.specifications.filter((_, i) => i !== index)
    });
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      addSpecification();
    }
  };

  return (
    <div className="house-specifications">
      <div className="header">
        <h2>House Specifications Management</h2>
        <p>Manage the meanings and significations for each of the 12 houses</p>
      </div>

      <div className="specifications-grid">
        {specifications.map(spec => (
          <div key={spec.house_number} className="spec-card">
            <div className="spec-header">
              <h3>House {spec.house_number}</h3>
              <button 
                className="edit-btn"
                onClick={() => handleEdit(spec)}
                disabled={editingHouse !== null}
              >
                Edit
              </button>
            </div>
            
            <div className="spec-content">
              {editingHouse === spec.house_number ? (
                <div className="edit-form">
                  <div className="current-specs">
                    <h4>Current Specifications:</h4>
                    <div className="spec-tags">
                      {formData.specifications.map((specification, index) => (
                        <span key={index} className="spec-tag">
                          {specification}
                          <button 
                            className="remove-spec"
                            onClick={() => removeSpecification(index)}
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div className="add-spec">
                    <input
                      type="text"
                      value={newSpec}
                      onChange={(e) => setNewSpec(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Add new specification..."
                    />
                    <button onClick={addSpecification}>Add</button>
                  </div>
                  
                  <div className="form-actions">
                    <button className="save-btn" onClick={handleSave}>
                      Save Changes
                    </button>
                    <button className="cancel-btn" onClick={handleCancel}>
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="spec-display">
                  <div className="spec-tags">
                    {spec.specifications.map((specification, index) => (
                      <span key={index} className="spec-tag readonly">
                        {specification}
                      </span>
                    ))}
                  </div>
                  <div className="spec-count">
                    {spec.specifications.length} specifications
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HouseSpecifications;