import React from 'react';

const SimpleHomePage = ({ onGetStarted }) => {
  const handleGetStarted = (action) => {
    if (onGetStarted) {
      onGetStarted(action);
    }
  };

  return (
    <div style={{
      fontFamily: 'Arial, sans-serif',
      margin: 0,
      padding: 0,
      background: '#fff'
    }}>
      {/* Header */}
      <header style={{
        background: '#d32f2f',
        color: 'white',
        padding: '12px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
          🌟 AstroVedic
        </div>
        <button 
          onClick={() => handleGetStarted('signin')}
          style={{
            background: '#fff',
            color: '#d32f2f',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '4px',
            fontWeight: 'bold',
            cursor: 'pointer'
          }}
        >
          Sign In
        </button>
      </header>

      {/* Top Banner */}
      <div style={{
        background: 'linear-gradient(90deg, #ff9800, #f57c00)',
        color: 'white',
        padding: '15px 20px',
        textAlign: 'center',
        fontSize: '18px',
        fontWeight: 'bold',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute',
          left: '20px',
          top: '50%',
          transform: 'translateY(-50%)',
          fontSize: '24px',
          animation: 'sparkle 2s infinite'
        }}>✨</div>
        <div style={{
          position: 'absolute',
          right: '20px',
          top: '50%',
          transform: 'translateY(-50%)',
          fontSize: '24px',
          animation: 'sparkle 2s infinite 1s'
        }}>🌟</div>
        Get Your Free Horoscope • Talk to Astrologers • Instant Predictions
        <style>{`
          @keyframes sparkle {
            0%, 100% { opacity: 0.3; transform: translateY(-50%) scale(1); }
            50% { opacity: 1; transform: translateY(-50%) scale(1.2); }
          }
        `}</style>
      </div>

      {/* Main Content */}
      <div style={{ display: 'flex', maxWidth: '1400px', margin: '0 auto', gap: '20px', padding: '20px' }}>
        
        {/* Left Sidebar */}
        <div style={{ width: '280px', flexShrink: 0 }}>
          <div style={{
            background: '#f5f5f5',
            border: '1px solid #ddd',
            borderRadius: '8px',
            padding: '15px',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: '0 0 15px 0', color: '#d32f2f', fontSize: '16px' }}>Quick Services</h3>
            {[
              'Free Birth Chart',
              'Daily Horoscope',
              'Love Compatibility',
              'Career Predictions',
              'Ask Astrologer',
              'Gemstone Guide'
            ].map((service, i) => (
              <div key={i} style={{
                padding: '8px 12px',
                margin: '5px 0',
                background: '#fff',
                border: '1px solid #eee',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => e.target.style.background = '#fff3e0'}
              onMouseOut={(e) => e.target.style.background = '#fff'}
              onClick={() => handleGetStarted(service.toLowerCase())}>
                {service}
              </div>
            ))}
          </div>

          <div style={{
            background: 'linear-gradient(135deg, #e8f5e8, #c8e6c9)',
            border: '2px solid #4caf50',
            borderRadius: '12px',
            padding: '15px',
            textAlign: 'center',
            position: 'relative',
            boxShadow: '0 4px 15px rgba(76, 175, 80, 0.2)'
          }}>
            <div style={{
              position: 'absolute',
              top: '-5px',
              right: '-5px',
              background: '#ff5722',
              color: 'white',
              borderRadius: '50%',
              width: '20px',
              height: '20px',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              animation: 'pulse 2s infinite'
            }}>🔥</div>
            <style>{`
              @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
              }
            `}</style>
            <div style={{ 
              fontSize: '40px', 
              marginBottom: '10px',
              animation: 'rotate 4s linear infinite'
            }}>🔮</div>
            <style>{`
              @keyframes rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
              }
            `}</style>
            <h4 style={{ margin: '0 0 10px 0', color: '#2e7d32' }}>Talk to Expert</h4>
            <p style={{ margin: '0 0 15px 0', fontSize: '12px', color: '#555' }}>
              Get personalized guidance from verified astrologers
            </p>
            <button style={{
              background: '#4caf50',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '20px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}>
              Consult Now
            </button>
          </div>
        </div>

        {/* Main Content Area */}
        <div style={{ flex: 1, minWidth: '600px' }}>
          
          {/* Hero Section */}
          <div style={{
            background: 'linear-gradient(135deg, #1976d2, #1565c0)',
            color: 'white',
            padding: '40px',
            borderRadius: '12px',
            textAlign: 'center',
            marginBottom: '30px',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <div style={{
              position: 'absolute',
              top: '10px',
              left: '10px',
              fontSize: '30px',
              animation: 'float 3s ease-in-out infinite'
            }}>🌙</div>
            <div style={{
              position: 'absolute',
              top: '10px',
              right: '10px',
              fontSize: '25px',
              animation: 'float 3s ease-in-out infinite 1.5s'
            }}>⭐</div>
            <div style={{
              position: 'absolute',
              bottom: '10px',
              left: '50px',
              fontSize: '20px',
              animation: 'float 3s ease-in-out infinite 0.5s'
            }}>✨</div>
            <div style={{
              position: 'absolute',
              bottom: '10px',
              right: '50px',
              fontSize: '22px',
              animation: 'float 3s ease-in-out infinite 2s'
            }}>🪐</div>
            <style>{`
              @keyframes float {
                0%, 100% { transform: translateY(0px); opacity: 0.7; }
                50% { transform: translateY(-10px); opacity: 1; }
              }
            `}</style>
            <h1 style={{ fontSize: '2.5rem', margin: '0 0 15px 0' }}>
              Discover Your Future
            </h1>
            <p style={{ fontSize: '1.2rem', margin: '0 0 25px 0', opacity: 0.9 }}>
              Authentic Vedic Astrology • Scientific Calculations • Expert Predictions
            </p>
            <button 
              onClick={() => handleGetStarted('birth-chart')}
              style={{
                background: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '2px solid rgba(255,255,255,0.3)',
                padding: '15px 30px',
                fontSize: '1.1rem',
                borderRadius: '25px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              Get Free Birth Chart
            </button>
          </div>

          {/* Services Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '20px',
            marginBottom: '30px'
          }}>
            
            {/* Horoscope Section */}
            <div style={{
              background: '#fff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <div style={{
                background: 'linear-gradient(90deg, #9c27b0, #7b1fa2)',
                color: 'white',
                padding: '15px',
                textAlign: 'center'
              }}>
                <div style={{ 
                  fontSize: '35px', 
                  marginBottom: '8px',
                  filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                }}>📊</div>
                <h3 style={{ margin: 0, fontSize: '18px' }}>Horoscope & Charts</h3>
              </div>
              <div style={{ padding: '15px' }}>
                {['Birth Chart Analysis', 'Daily Horoscope', 'Weekly Predictions', 'Monthly Forecast', 'Yearly Overview', 'Planetary Positions'].map((item, i) => (
                  <div key={i} style={{
                    padding: '8px 0',
                    borderBottom: i < 5 ? '1px solid #f0f0f0' : 'none',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                  onClick={() => handleGetStarted(item.toLowerCase())}>
                    • {item}
                  </div>
                ))}
              </div>
            </div>

            {/* Love & Marriage */}
            <div style={{
              background: '#fff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <div style={{
                background: 'linear-gradient(90deg, #e91e63, #c2185b)',
                color: 'white',
                padding: '15px',
                textAlign: 'center'
              }}>
                <div style={{ 
                  fontSize: '35px', 
                  marginBottom: '8px',
                  animation: 'heartbeat 2s ease-in-out infinite',
                  filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                }}>💕</div>
                <style>{`
                  @keyframes heartbeat {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                  }
                `}</style>
                <h3 style={{ margin: 0, fontSize: '18px' }}>Love & Marriage</h3>
              </div>
              <div style={{ padding: '15px' }}>
                {['Love Compatibility', 'Marriage Prediction', 'Relationship Advice', 'Soulmate Analysis', 'Wedding Muhurat', 'Love Problems'].map((item, i) => (
                  <div key={i} style={{
                    padding: '8px 0',
                    borderBottom: i < 5 ? '1px solid #f0f0f0' : 'none',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                  onClick={() => handleGetStarted(item.toLowerCase())}>
                    • {item}
                  </div>
                ))}
              </div>
            </div>

            {/* Career & Money */}
            <div style={{
              background: '#fff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <div style={{
                background: 'linear-gradient(90deg, #2196f3, #1976d2)',
                color: 'white',
                padding: '15px',
                textAlign: 'center'
              }}>
                <div style={{ 
                  fontSize: '35px', 
                  marginBottom: '8px',
                  animation: 'bounce 2s infinite',
                  filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                }}>💰</div>
                <style>{`
                  @keyframes bounce {
                    0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                    40% { transform: translateY(-10px); }
                    60% { transform: translateY(-5px); }
                  }
                `}</style>
                <h3 style={{ margin: 0, fontSize: '18px' }}>Career & Money</h3>
              </div>
              <div style={{ padding: '15px' }}>
                {['Career Horoscope', 'Job Predictions', 'Business Success', 'Financial Forecast', 'Investment Timing', 'Promotion Analysis'].map((item, i) => (
                  <div key={i} style={{
                    padding: '8px 0',
                    borderBottom: i < 5 ? '1px solid #f0f0f0' : 'none',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                  onClick={() => handleGetStarted(item.toLowerCase())}>
                    • {item}
                  </div>
                ))}
              </div>
            </div>

            {/* Remedies & Solutions */}
            <div style={{
              background: '#fff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <div style={{
                background: 'linear-gradient(90deg, #ff9800, #f57c00)',
                color: 'white',
                padding: '15px',
                textAlign: 'center'
              }}>
                <div style={{ 
                  fontSize: '35px', 
                  marginBottom: '8px',
                  animation: 'glow 3s ease-in-out infinite',
                  filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                }}>🕉️</div>
                <style>{`
                  @keyframes glow {
                    0%, 100% { filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)); }
                    50% { filter: drop-shadow(0 0 20px rgba(255,193,7,0.8)); }
                  }
                `}</style>
                <h3 style={{ margin: 0, fontSize: '18px' }}>Remedies & Solutions</h3>
              </div>
              <div style={{ padding: '15px' }}>
                {['Gemstone Guide', 'Mantra Suggestions', 'Puja Remedies', 'Yantra Power', 'Rudraksha Benefits', 'Spiritual Healing'].map((item, i) => (
                  <div key={i} style={{
                    padding: '8px 0',
                    borderBottom: i < 5 ? '1px solid #f0f0f0' : 'none',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                  onClick={() => handleGetStarted(item.toLowerCase())}>
                    • {item}
                  </div>
                ))}
              </div>
            </div>

            {/* Health & Wellness */}
            <div style={{
              background: '#fff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <div style={{
                background: 'linear-gradient(90deg, #4caf50, #388e3c)',
                color: 'white',
                padding: '15px',
                textAlign: 'center'
              }}>
                <div style={{ 
                  fontSize: '35px', 
                  marginBottom: '8px',
                  filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                }}>🏥</div>
                <h3 style={{ margin: 0, fontSize: '18px' }}>Health & Wellness</h3>
              </div>
              <div style={{ padding: '15px' }}>
                {['Health Predictions', 'Medical Astrology', 'Wellness Guide', 'Disease Prevention', 'Recovery Timing', 'Mental Health'].map((item, i) => (
                  <div key={i} style={{
                    padding: '8px 0',
                    borderBottom: i < 5 ? '1px solid #f0f0f0' : 'none',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                  onClick={() => handleGetStarted(item.toLowerCase())}>
                    • {item}
                  </div>
                ))}
              </div>
            </div>

            {/* Vastu & Numerology */}
            <div style={{
              background: '#fff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <div style={{
                background: 'linear-gradient(90deg, #795548, #5d4037)',
                color: 'white',
                padding: '15px',
                textAlign: 'center'
              }}>
                <div style={{ 
                  fontSize: '35px', 
                  marginBottom: '8px',
                  animation: 'shake 3s infinite',
                  filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                }}>🏠</div>
                <style>{`
                  @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-2px); }
                    75% { transform: translateX(2px); }
                  }
                `}</style>
                <h3 style={{ margin: 0, fontSize: '18px' }}>Vastu & Numerology</h3>
              </div>
              <div style={{ padding: '15px' }}>
                {['Home Vastu', 'Lucky Numbers', 'Name Analysis', 'Business Names', 'Direction Analysis', 'Color Therapy'].map((item, i) => (
                  <div key={i} style={{
                    padding: '8px 0',
                    borderBottom: i < 5 ? '1px solid #f0f0f0' : 'none',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                  onClick={() => handleGetStarted(item.toLowerCase())}>
                    • {item}
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Bottom CTA */}
          <div style={{
            background: 'linear-gradient(135deg, #fff3e0, #ffe0b2)',
            border: '3px solid #ff9800',
            borderRadius: '12px',
            padding: '25px',
            textAlign: 'center',
            position: 'relative',
            boxShadow: '0 8px 25px rgba(255, 152, 0, 0.2)'
          }}>
            <div style={{
              position: 'absolute',
              top: '-10px',
              left: '20px',
              background: '#ff5722',
              color: 'white',
              padding: '5px 10px',
              borderRadius: '15px',
              fontSize: '12px',
              fontWeight: 'bold',
              animation: 'wiggle 2s infinite'
            }}>HOT 🔥</div>
            <style>{`
              @keyframes wiggle {
                0%, 100% { transform: rotate(0deg); }
                25% { transform: rotate(-3deg); }
                75% { transform: rotate(3deg); }
              }
            `}</style>
            <h3 style={{ 
              margin: '0 0 10px 0', 
              color: '#e65100',
              animation: 'colorChange 3s infinite'
            }}>
              <span style={{ fontSize: '25px', marginRight: '8px' }}>🎯</span>
              Get Personalized Predictions
            </h3>
            <style>{`
              @keyframes colorChange {
                0%, 100% { color: #e65100; }
                50% { color: #ff5722; }
              }
            `}</style>
            <p style={{ margin: '0 0 15px 0', color: '#555' }}>
              Chat with expert astrologers for detailed analysis and guidance
            </p>
            <button 
              onClick={() => handleGetStarted('expert-chat')}
              style={{
                background: '#ff9800',
                color: 'white',
                border: 'none',
                padding: '12px 25px',
                borderRadius: '20px',
                fontWeight: 'bold',
                cursor: 'pointer',
                fontSize: '16px'
              }}
            >
              Start Chat Now
            </button>
          </div>

        </div>

        {/* Right Sidebar */}
        <div style={{ width: '280px', flexShrink: 0 }}>
          
          {/* Today's Panchang */}
          <div style={{
            background: 'linear-gradient(135deg, #673ab7, #9c27b0)',
            color: 'white',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '20px',
            textAlign: 'center'
          }}>
            <h3 style={{ margin: '0 0 15px 0', fontSize: '18px' }}>📅 Today's Panchang</h3>
            <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
              <div><strong>Tithi:</strong> Shukla Paksha 8</div>
              <div><strong>Nakshatra:</strong> Rohini</div>
              <div><strong>Yoga:</strong> Siddha</div>
              <div><strong>Karana:</strong> Bava</div>
              <div style={{ marginTop: '10px', color: '#ffeb3b' }}>
                <strong>🌟 Auspicious Time:</strong><br/>06:30 - 08:15 AM
              </div>
            </div>
          </div>

          {/* Live Planetary Positions */}
          <div style={{
            background: '#fff',
            border: '2px solid #2196f3',
            borderRadius: '12px',
            padding: '15px',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: '0 0 15px 0', color: '#1976d2', fontSize: '16px', textAlign: 'center' }}>
              🪐 Live Planetary Positions
            </h3>
            <div style={{ fontSize: '13px' }}>
              {[
                { planet: '☉ Sun', sign: 'Sagittarius 15°', color: '#ff9800' },
                { planet: '☽ Moon', sign: 'Taurus 8°', color: '#2196f3' },
                { planet: '♂ Mars', sign: 'Leo 22°', color: '#f44336' },
                { planet: '☿ Mercury', sign: 'Scorpio 3°', color: '#4caf50' },
                { planet: '♃ Jupiter', sign: 'Aries 12°', color: '#ff9800' },
                { planet: '♀ Venus', sign: 'Capricorn 28°', color: '#e91e63' }
              ].map((item, i) => (
                <div key={i} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '5px 0',
                  borderBottom: i < 5 ? '1px solid #f0f0f0' : 'none'
                }}>
                  <span style={{ color: item.color, fontWeight: 'bold' }}>{item.planet}</span>
                  <span>{item.sign}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Testimonials */}
          <div style={{
            background: 'linear-gradient(135deg, #4caf50, #8bc34a)',
            color: 'white',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: '0 0 15px 0', fontSize: '16px', textAlign: 'center' }}>⭐ User Reviews</h3>
            <div style={{
              background: 'rgba(255,255,255,0.2)',
              borderRadius: '8px',
              padding: '12px',
              marginBottom: '10px',
              fontSize: '13px'
            }}>
              "Predictions were 100% accurate! Got promotion exactly when predicted."
              <div style={{ textAlign: 'right', marginTop: '5px', fontSize: '11px' }}>- Priya S.</div>
            </div>
            <div style={{
              background: 'rgba(255,255,255,0.2)',
              borderRadius: '8px',
              padding: '12px',
              fontSize: '13px'
            }}>
              "Marriage compatibility report helped us understand each other better."
              <div style={{ textAlign: 'right', marginTop: '5px', fontSize: '11px' }}>- Raj M.</div>
            </div>
          </div>

          {/* Lucky Numbers Today */}
          <div style={{
            background: 'linear-gradient(135deg, #ff5722, #ff9800)',
            color: 'white',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '20px',
            textAlign: 'center'
          }}>
            <h3 style={{ margin: '0 0 15px 0', fontSize: '16px' }}>🍀 Lucky Numbers Today</h3>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '8px'
            }}>
              {[7, 14, 23, 31, 45, 52].map((num, i) => (
                <div key={i} style={{
                  background: 'rgba(255,255,255,0.3)',
                  borderRadius: '50%',
                  width: '35px',
                  height: '35px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '14px'
                }}>
                  {num}
                </div>
              ))}
            </div>
          </div>

          {/* Astro News */}
          <div style={{
            background: '#fff',
            border: '1px solid #e0e0e0',
            borderRadius: '12px',
            padding: '15px'
          }}>
            <h3 style={{ margin: '0 0 15px 0', color: '#333', fontSize: '16px', textAlign: 'center' }}>
              📰 Astro News
            </h3>
            <div style={{ fontSize: '13px', lineHeight: '1.5' }}>
              <div style={{ marginBottom: '12px', paddingBottom: '8px', borderBottom: '1px solid #f0f0f0' }}>
                <strong>Jupiter Transit Alert:</strong> Major changes in career sector expected this month.
              </div>
              <div style={{ marginBottom: '12px', paddingBottom: '8px', borderBottom: '1px solid #f0f0f0' }}>
                <strong>Full Moon Effect:</strong> Emotional decisions should be avoided on Dec 15th.
              </div>
              <div>
                <strong>Mercury Retrograde:</strong> Communication issues likely from Dec 20-30.
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Footer */}
      <footer style={{
        background: '#333',
        color: 'white',
        padding: '30px 20px',
        textAlign: 'center',
        marginTop: '40px'
      }}>
        <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '10px' }}>
          🌟 AstroVedic
        </div>
        <p style={{ margin: 0, color: '#ccc' }}>
          © 2024 AstroVedic. Authentic Vedic Astrology Solutions.
        </p>
      </footer>
    </div>
  );
};

export default SimpleHomePage;