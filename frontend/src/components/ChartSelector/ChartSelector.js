import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { apiService } from '../../services/apiService';
import { useAstrology } from '../../context/AstrologyContext';

const ChartSelector = ({ onSelectChart, onCreateNew, onLogout }) => {
  const { setBirthData, setChartData } = useAstrology();
  const [charts, setCharts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadCharts();
  }, []);

  const loadCharts = async (search = '') => {
    try {
      setLoading(true);
      const response = await apiService.getExistingCharts(search);
      setCharts(response.charts || []);
    } catch (error) {
      toast.error('Failed to load charts');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    setTimeout(() => loadCharts(query), 300);
  };

  const selectChart = async (chart) => {
    try {
      setLoading(true);
      const chartData = await apiService.calculateChart({
        name: chart.name,
        date: chart.date,
        time: chart.time,
        latitude: chart.latitude,
        longitude: chart.longitude,
        timezone: chart.timezone
      });
      
      setBirthData({
        name: chart.name,
        date: chart.date,
        time: chart.time,
        place: `${chart.latitude}, ${chart.longitude}`,
        latitude: chart.latitude,
        longitude: chart.longitude,
        timezone: chart.timezone
      });
      
      setChartData(chartData);
      onSelectChart();
    } catch (error) {
      toast.error('Failed to load chart');
    } finally {
      setLoading(false);
    }
  };

  const deleteChart = async (chartId, e) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this chart?')) {
      try {
        await apiService.deleteChart(chartId);
        toast.success('Chart deleted successfully!');
        loadCharts(searchQuery);
      } catch (error) {
        toast.error('Failed to delete chart');
      }
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 50%, #ffcc80 100%)',
      padding: '20px',
      color: '#333'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '30px',
          padding: '20px',
          background: 'rgba(255, 255, 255, 0.9)',
          borderRadius: '15px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
        }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '2.5rem', color: '#ff6b35' }}>
              ✨ Your Astrology Charts
            </h1>
            <p style={{ margin: '5px 0 0 0', opacity: 0.8 }}>Select a chart to view or create a new one</p>
          </div>
          <button 
            onClick={onLogout}
            style={{
              padding: '12px 24px',
              background: 'linear-gradient(45deg, #dc3545, #c82333)',
              color: 'white',
              border: 'none',
              borderRadius: '25px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '600',
              boxShadow: '0 4px 15px rgba(220, 53, 69, 0.3)'
            }}
          >
            Logout
          </button>
        </div>

        <div style={{
          display: 'flex',
          gap: '20px',
          marginBottom: '30px',
          flexWrap: 'wrap'
        }}>
          <input
            type="text"
            placeholder="🔍 Search your charts..."
            value={searchQuery}
            onChange={handleSearch}
            style={{
              flex: 1,
              minWidth: '300px',
              padding: '15px 20px',
              fontSize: '16px',
              border: '2px solid #ff6b35',
              borderRadius: '25px',
              background: 'white',
              color: '#333'
            }}
          />
          <button
            onClick={onCreateNew}
            style={{
              padding: '15px 30px',
              background: 'linear-gradient(45deg, #ff6b35, #f7931e)',
              color: 'white',
              border: 'none',
              borderRadius: '25px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '600',
              boxShadow: '0 4px 15px rgba(255, 107, 53, 0.3)',
              whiteSpace: 'nowrap'
            }}
          >
            ➕ Create New Chart
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <div style={{ fontSize: '2rem', marginBottom: '10px' }}>🔮</div>
            <p>Loading your charts...</p>
          </div>
        ) : charts.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '50px',
            background: 'rgba(255, 255, 255, 0.9)',
            borderRadius: '15px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🌟</div>
            <h3>No charts found</h3>
            <p style={{ opacity: 0.8, marginBottom: '20px' }}>
              {searchQuery ? 'Try a different search term' : 'Create your first astrology chart to get started'}
            </p>
            <button
              onClick={onCreateNew}
              style={{
                padding: '15px 30px',
                background: 'linear-gradient(45deg, #ff6b35, #f7931e)',
                color: 'white',
                border: 'none',
                borderRadius: '25px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: '600'
              }}
            >
              Create Your First Chart
            </button>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: '20px'
          }}>
            {charts.map(chart => (
              <div
                key={chart.id}
                onClick={() => selectChart(chart)}
                style={{
                  background: 'white',
                  borderRadius: '15px',
                  padding: '20px',
                  cursor: 'pointer',
                  border: '2px solid #ff6b35',
                  boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
                  transition: 'all 0.3s ease',
                  position: 'relative'
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateY(-5px)';
                  e.target.style.boxShadow = '0 10px 25px rgba(255, 107, 53, 0.2)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = 'none';
                }}
              >
                <button
                  onClick={(e) => deleteChart(chart.id, e)}
                  style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    background: 'rgba(220, 53, 69, 0.8)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '50%',
                    width: '30px',
                    height: '30px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  ×
                </button>
                
                <div style={{ marginBottom: '15px' }}>
                  <h3 style={{ 
                    margin: '0 0 10px 0', 
                    fontSize: '1.5rem',
                    color: '#ff6b35'
                  }}>
                    {chart.name}
                  </h3>
                  <div style={{ opacity: 0.8, fontSize: '14px' }}>
                    <div>📅 {new Date(chart.date).toLocaleDateString()}</div>
                    <div>🕐 {chart.time}</div>
                    <div>📍 {chart.latitude.toFixed(2)}, {chart.longitude.toFixed(2)}</div>
                  </div>
                </div>
                
                <div style={{
                  padding: '10px',
                  background: 'rgba(255, 107, 53, 0.2)',
                  borderRadius: '10px',
                  textAlign: 'center',
                  fontSize: '14px',
                  fontWeight: '600'
                }}>
                  Click to view chart
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChartSelector;