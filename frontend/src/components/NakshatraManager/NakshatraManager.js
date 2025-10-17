import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/apiService';

const NakshatraManager = () => {
  const [nakshatras, setNakshatras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingNakshatra, setEditingNakshatra] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    lord: '',
    deity: '',
    nature: '',
    guna: '',
    description: '',
    characteristics: '',
    positive_traits: '',
    negative_traits: '',
    careers: '',
    compatibility: ''
  });

  useEffect(() => {
    loadNakshatras();
  }, []);

  const loadNakshatras = async () => {
    try {
      const response = await apiService.getNakshatras();
      setNakshatras(response.nakshatras);
    } catch (error) {
      console.error('Failed to load nakshatras:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingNakshatra) {
        await apiService.updateNakshatra(editingNakshatra.id, formData);
      } else {
        await apiService.createNakshatra(formData);
      }
      resetForm();
      loadNakshatras();
    } catch (error) {
      console.error('Failed to save nakshatra:', error);
      alert('Failed to save nakshatra');
    }
  };

  const handleEdit = (nakshatra) => {
    setEditingNakshatra(nakshatra);
    setFormData({
      name: nakshatra.name,
      lord: nakshatra.lord,
      deity: nakshatra.deity,
      nature: nakshatra.nature,
      guna: nakshatra.guna,
      description: nakshatra.description,
      characteristics: nakshatra.characteristics,
      positive_traits: nakshatra.positive_traits,
      negative_traits: nakshatra.negative_traits,
      careers: nakshatra.careers,
      compatibility: nakshatra.compatibility
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this nakshatra?')) {
      try {
        await apiService.deleteNakshatra(id);
        loadNakshatras();
      } catch (error) {
        console.error('Failed to delete nakshatra:', error);
        alert('Failed to delete nakshatra');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      lord: '',
      deity: '',
      nature: '',
      guna: '',
      description: '',
      characteristics: '',
      positive_traits: '',
      negative_traits: '',
      careers: '',
      compatibility: ''
    });
    setEditingNakshatra(null);
    setShowForm(false);
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div style={{ padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ color: '#e91e63', margin: 0 }}>🌟 Nakshatra Management</h3>
        <button
          onClick={() => setShowForm(true)}
          style={{
            padding: '0.5rem 1rem',
            background: '#e91e63',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Add Nakshatra
        </button>
      </div>

      {showForm && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            padding: '2rem',
            borderRadius: '12px',
            width: '90%',
            maxWidth: '600px',
            maxHeight: '90vh',
            overflowY: 'auto'
          }}>
            <h4 style={{ color: '#e91e63', marginBottom: '1rem' }}>
              {editingNakshatra ? 'Edit Nakshatra' : 'Add New Nakshatra'}
            </h4>
            
            <form onSubmit={handleSubmit}>
              <div style={{ display: 'grid', gap: '1rem' }}>
                <input
                  type="text"
                  placeholder="Name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                  style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
                
                <input
                  type="text"
                  placeholder="Lord"
                  value={formData.lord}
                  onChange={(e) => setFormData({...formData, lord: e.target.value})}
                  required
                  style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
                
                <input
                  type="text"
                  placeholder="Deity"
                  value={formData.deity}
                  onChange={(e) => setFormData({...formData, deity: e.target.value})}
                  required
                  style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
                
                <input
                  type="text"
                  placeholder="Nature"
                  value={formData.nature}
                  onChange={(e) => setFormData({...formData, nature: e.target.value})}
                  required
                  style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
                
                <input
                  type="text"
                  placeholder="Guna"
                  value={formData.guna}
                  onChange={(e) => setFormData({...formData, guna: e.target.value})}
                  required
                  style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
                
                <textarea
                  placeholder="Description"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  required
                  rows={3}
                  style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
                
                <textarea
                  placeholder="Characteristics"
                  value={formData.characteristics}
                  onChange={(e) => setFormData({...formData, characteristics: e.target.value})}
                  required
                  rows={3}
                  style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
                
                <textarea
                  placeholder="Positive Traits"
                  value={formData.positive_traits}
                  onChange={(e) => setFormData({...formData, positive_traits: e.target.value})}
                  required
                  rows={2}
                  style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
                
                <textarea
                  placeholder="Negative Traits"
                  value={formData.negative_traits}
                  onChange={(e) => setFormData({...formData, negative_traits: e.target.value})}
                  required
                  rows={2}
                  style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
                
                <textarea
                  placeholder="Careers"
                  value={formData.careers}
                  onChange={(e) => setFormData({...formData, careers: e.target.value})}
                  required
                  rows={2}
                  style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
                
                <textarea
                  placeholder="Compatibility"
                  value={formData.compatibility}
                  onChange={(e) => setFormData({...formData, compatibility: e.target.value})}
                  required
                  rows={2}
                  style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button
                  type="submit"
                  style={{
                    padding: '0.5rem 1rem',
                    background: '#e91e63',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  {editingNakshatra ? 'Update' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={resetForm}
                  style={{
                    padding: '0.5rem 1rem',
                    background: '#666',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gap: '1rem' }}>
        {nakshatras.map((nakshatra, index) => (
          <div
            key={nakshatra.id}
            style={{
              background: 'white',
              padding: '1rem',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              borderLeft: '4px solid #e91e63'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ color: '#e91e63', margin: 0 }}>
                {index + 1}. {nakshatra.name}
              </h4>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => handleEdit(nakshatra)}
                  style={{
                    padding: '0.25rem 0.5rem',
                    background: '#ff6f00',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.8rem'
                  }}
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(nakshatra.id)}
                  style={{
                    padding: '0.25rem 0.5rem',
                    background: '#f44336',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.8rem'
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
            
            <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#666' }}>
              <strong>Lord:</strong> {nakshatra.lord} | <strong>Deity:</strong> {nakshatra.deity}
            </div>
            
            <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#333' }}>
              {nakshatra.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NakshatraManager;