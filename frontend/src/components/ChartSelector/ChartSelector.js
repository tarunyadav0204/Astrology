import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { apiService } from '../../services/apiService';
import { useAstrology } from '../../context/AstrologyContext';

// Add CSS for cosmic background
const cosmicStyles = `
  .cosmic-background {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
  }
  
  .zodiac-wheel {
    position: absolute;
    top: 5%;
    right: 3%;
    width: 300px;
    height: 300px;
    border: 4px solid rgba(255, 107, 53, 0.8);
    border-radius: 50%;
    animation: rotate 30s linear infinite;
    z-index: 5;
  }
  
  .zodiac-wheel::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 150px;
    height: 150px;
    border: 3px solid rgba(247, 147, 30, 0.7);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    animation: rotate 20s linear infinite reverse;
  }
  
  .zodiac-wheel::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 100px;
    height: 100px;
    border: 2px solid rgba(255, 204, 128, 0.8);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    animation: rotate 15s linear infinite;
  }
  
  .stars-field {
    position: absolute;
    width: 100%;
    height: 100%;
  }
  
  .star {
    position: absolute;
    width: 4px;
    height: 4px;
    background: rgba(255, 255, 255, 0.9);
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
    border-radius: 50%;
    animation: twinkle 2s ease-in-out infinite alternate;
  }
  
  .star-0 { background: rgba(255, 107, 53, 0.8); }
  .star-1 { background: rgba(247, 147, 30, 0.8); }
  .star-2 { background: rgba(255, 204, 128, 0.8); }
  .star-3 { background: rgba(255, 255, 255, 0.9); }
  .star-4 { background: rgba(255, 183, 77, 0.8); }
  
  .floating-planets {
    position: absolute;
    width: 100%;
    height: 100%;
  }
  
  .planet {
    position: absolute;
    border-radius: 50%;
    animation: orbit 25s linear infinite;
  }
  
  .planet-1 {
    top: 20%;
    left: 10%;
    width: 12px;
    height: 12px;
    background: radial-gradient(circle, rgba(255, 107, 53, 0.8), rgba(255, 107, 53, 0.3));
    animation-duration: 20s;
  }
  
  .planet-2 {
    bottom: 30%;
    right: 20%;
    width: 8px;
    height: 8px;
    background: radial-gradient(circle, rgba(247, 147, 30, 0.8), rgba(247, 147, 30, 0.3));
    animation-duration: 35s;
    animation-direction: reverse;
  }
  
  .planet-3 {
    top: 60%;
    left: 20%;
    width: 6px;
    height: 6px;
    background: radial-gradient(circle, rgba(255, 204, 128, 0.8), rgba(255, 204, 128, 0.3));
    animation-duration: 40s;
  }
  
  @keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  @keyframes twinkle {
    0% { opacity: 0.3; transform: scale(1); }
    100% { opacity: 1; transform: scale(1.2); }
  }
  
  @keyframes orbit {
    0% { transform: translateX(0) translateY(0) rotate(0deg); }
    25% { transform: translateX(50px) translateY(-30px) rotate(90deg); }
    50% { transform: translateX(0) translateY(-60px) rotate(180deg); }
    75% { transform: translateX(-50px) translateY(-30px) rotate(270deg); }
    100% { transform: translateX(0) translateY(0) rotate(360deg); }
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = cosmicStyles;
  document.head.appendChild(styleSheet);
}

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
      background: 'linear-gradient(135deg, #ff6b35 0%, #f7931e 50%, #ffcc80 100%)',
      padding: '20px',
      color: '#333',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Cosmic Background Elements */}
      <div className="cosmic-background">
        <div className="zodiac-wheel"></div>
        <div className="stars-field">
          {[...Array(50)].map((_, i) => (
            <div key={i} className={`star star-${i % 5}`} style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`
            }}></div>
          ))}
        </div>
        <div className="floating-planets">
          <div className="planet planet-1"></div>
          <div className="planet planet-2"></div>
          <div className="planet planet-3"></div>
        </div>
      </div>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '40px',
          padding: '30px',
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '20px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.2)'
        }}>
          <div>
            <div>
              <h1 style={{ 
                margin: 0, 
                fontSize: '3rem', 
                background: 'linear-gradient(45deg, #ff6b35, #f7931e)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                textShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}>
                🌌 Welcome to AstroClick
              </h1>
              <p style={{ 
                margin: '10px 0 0 0', 
                fontSize: '1.2rem',
                color: '#666',
                fontWeight: '500'
              }}>Professional Vedic Astrology Platform</p>
            </div>
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
            padding: '60px 40px',
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '20px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.2)'
          }}>
            <div style={{ fontSize: '4rem', marginBottom: '30px' }}>🌌</div>
            <h3 style={{ fontSize: '2rem', color: '#ff6b35', marginBottom: '15px' }}>Begin Your Cosmic Journey</h3>
            <p style={{ opacity: 0.8, marginBottom: '30px', fontSize: '1.1rem', lineHeight: '1.6' }}>
              {searchQuery ? 'Try a different search term to find your charts' : 'The stars are waiting to reveal your destiny. Create your first astrology chart and unlock the mysteries of your birth.'}
            </p>
            <button
              onClick={onCreateNew}
              style={{
                padding: '18px 40px',
                background: 'linear-gradient(45deg, #ff6b35, #f7931e)',
                color: 'white',
                border: 'none',
                borderRadius: '30px',
                cursor: 'pointer',
                fontSize: '18px',
                fontWeight: '700',
                boxShadow: '0 6px 20px rgba(255, 107, 53, 0.4)',
                transform: 'translateY(0)',
                transition: 'all 0.3s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 8px 25px rgba(255, 107, 53, 0.5)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 6px 20px rgba(255, 107, 53, 0.4)';
              }}
            >
🌟 Create Your Cosmic Blueprint
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
                  background: 'rgba(255, 255, 255, 0.95)',
                  borderRadius: '20px',
                  padding: '25px',
                  cursor: 'pointer',
                  border: '2px solid rgba(255, 107, 53, 0.3)',
                  boxShadow: '0 6px 25px rgba(0,0,0,0.1)',
                  backdropFilter: 'blur(10px)',
                  transition: 'all 0.3s ease',
                  position: 'relative'
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateY(-8px)';
                  e.target.style.boxShadow = '0 12px 35px rgba(255, 107, 53, 0.3)';
                  e.target.style.borderColor = '#ff6b35';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 6px 25px rgba(0,0,0,0.1)';
                  e.target.style.borderColor = 'rgba(255, 107, 53, 0.3)';
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
                  padding: '12px',
                  background: 'linear-gradient(45deg, rgba(255, 107, 53, 0.2), rgba(247, 147, 30, 0.2))',
                  borderRadius: '12px',
                  textAlign: 'center',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#ff6b35',
                  border: '1px solid rgba(255, 107, 53, 0.3)'
                }}>
                  🔮 View Cosmic Insights
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