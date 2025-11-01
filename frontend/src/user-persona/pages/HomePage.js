import React, { useState, useEffect } from 'react';
import './HomePage.css';

const HomePage = ({ onGetStarted }) => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [todayHoroscope, setTodayHoroscope] = useState(null);
  const [userSign, setUserSign] = useState(null);

  const heroSlides = [
    {
      title: "Discover Your Cosmic Journey",
      subtitle: "Authentic Vedic Astrology with Scientific Precision",
      image: "🌟",
      cta: "Get Free Birth Chart"
    },
    {
      title: "Find Your Perfect Match",
      subtitle: "Advanced Compatibility Analysis Based on Classical Texts",
      image: "💕",
      cta: "Check Compatibility"
    },
    {
      title: "Plan Your Future",
      subtitle: "Precise Timing for Life's Important Decisions",
      image: "🔮",
      cta: "View Predictions"
    }
  ];

  const features = [
    {
      icon: "📊",
      title: "Free Birth Chart",
      description: "Complete Vedic chart with all divisional charts",
      popular: true
    },
    {
      icon: "💝",
      title: "Love Compatibility",
      description: "Deep synastry analysis for relationships",
      popular: true
    },
    {
      icon: "🎯",
      title: "Daily Predictions",
      description: "Personalized forecasts based on transits",
      popular: false
    },
    {
      icon: "💎",
      title: "Gemstone Guide",
      description: "Scientific recommendations with rationale",
      popular: false
    },
    {
      icon: "🏥",
      title: "Health Analysis",
      description: "Complete Vedic health assessment with remedies",
      popular: true
    },
    {
      icon: "🕉️",
      title: "Spiritual Remedies",
      description: "Mantras, yantras, and ritual timing",
      popular: false
    },
    {
      icon: "👥",
      title: "Ask Astrologer",
      description: "Connect with verified Vedic experts",
      popular: true
    }
  ];

  const testimonials = [
    {
      name: "Priya Sharma",
      location: "Mumbai",
      text: "Most accurate predictions I've ever received. The marriage timing was spot on!",
      rating: 5,
      image: "👩"
    },
    {
      name: "Rajesh Kumar",
      location: "Delhi",
      text: "Finally found an app that explains the 'why' behind predictions. Authentic Vedic astrology.",
      rating: 5,
      image: "👨"
    },
    {
      name: "Anita Patel",
      location: "Bangalore",
      text: "The compatibility analysis saved my relationship. Detailed and scientifically explained.",
      rating: 5,
      image: "👩‍💼"
    }
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % heroSlides.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleGetStarted = (feature) => {
    if (onGetStarted) {
      onGetStarted(feature);
    } else {
      console.log(`Navigate to ${feature}`);
    }
  };

  return (
    <div style={{
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
      lineHeight: 1.6,
      color: '#333',
      margin: 0,
      padding: 0
    }}>
      {/* Navigation */}
      <nav style={{
        position: 'fixed',
        top: 0,
        width: '100%',
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(233, 30, 99, 0.1)',
        zIndex: 1000,
        padding: '0 20px'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          height: '70px'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontWeight: 700,
            fontSize: '24px',
            color: '#e91e63'
          }}>
            <span style={{ fontSize: '28px' }}>🌟</span>
            <span>AstroRoshni</span>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '30px'
          }}>
            <a href="#features" style={{ textDecoration: 'none', color: '#333', fontWeight: 500 }}>Features</a>
            <a href="#horoscope" style={{ textDecoration: 'none', color: '#333', fontWeight: 500 }}>Horoscope</a>
            <a href="#compatibility" style={{ textDecoration: 'none', color: '#333', fontWeight: 500 }}>Compatibility</a>
            <button 
              onClick={() => handleGetStarted('signin')}
              style={{
                background: 'linear-gradient(135deg, #e91e63, #ff6f00)',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '25px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Sign In
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section style={{
        position: 'relative',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        textAlign: 'center'
      }}>
        <div style={{
          maxWidth: '800px',
          padding: '0 20px',
          zIndex: 2
        }}>
          <div style={{ fontSize: '80px', marginBottom: '20px' }}>
            {heroSlides[currentSlide].image}
          </div>
          <h1 style={{
            fontSize: '3.5rem',
            fontWeight: 700,
            marginBottom: '20px',
            margin: 0
          }}>
            {heroSlides[currentSlide].title}
          </h1>
          <p style={{
            fontSize: '1.3rem',
            marginBottom: '40px',
            opacity: 0.9,
            fontWeight: 300
          }}>
            {heroSlides[currentSlide].subtitle}
          </p>
          <button 
            onClick={() => handleGetStarted('birth-chart')}
            style={{
              background: 'linear-gradient(135deg, #e91e63, #ff6f00)',
              color: 'white',
              border: 'none',
              padding: '18px 40px',
              fontSize: '1.1rem',
              fontWeight: 600,
              borderRadius: '50px',
              cursor: 'pointer',
              boxShadow: '0 8px 30px rgba(0, 0, 0, 0.3)'
            }}
          >
            {heroSlides[currentSlide].cta}
          </button>
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '10px',
            marginTop: '40px'
          }}>
            {heroSlides.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentSlide(index)}
                style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  border: '2px solid rgba(255, 255, 255, 0.5)',
                  background: index === currentSlide ? 'white' : 'transparent',
                  cursor: 'pointer'
                }}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Quick Actions */}
      <section style={{
        padding: '80px 0',
        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '0 20px'
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '30px'
          }}>
            <div className="quick-card" onClick={() => handleGetStarted('birth-chart')}>
              <div className="quick-icon">📊</div>
              <h3>Free Birth Chart</h3>
              <p>Get your complete Vedic chart instantly</p>
            </div>
            <div className="quick-card" onClick={() => handleGetStarted('daily-horoscope')}>
              <div className="quick-icon">🌅</div>
              <h3>Today's Horoscope</h3>
              <p>Personalized daily predictions</p>
            </div>
            <div className="quick-card" onClick={() => handleGetStarted('compatibility')}>
              <div className="quick-icon">💕</div>
              <h3>Love Match</h3>
              <p>Find your perfect astrological match</p>
            </div>
            <div className="quick-card" onClick={() => handleGetStarted('health-analysis')}>
              <div className="quick-icon">🏥</div>
              <h3>Health Analysis</h3>
              <p>Complete Vedic health assessment</p>
            </div>
            <div className="quick-card" onClick={() => handleGetStarted('ask-astrologer')}>
              <div className="quick-icon">🔮</div>
              <h3>Ask Expert</h3>
              <p>Chat with verified astrologers</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="features">
        <div className="container">
          <div className="section-header">
            <h2>Comprehensive Astrological Services</h2>
            <p>Everything you need for your spiritual and life journey</p>
          </div>
          <div className="features-grid">
            {features.map((feature, index) => (
              <div key={index} className={`feature-card ${feature.popular ? 'popular' : ''}`}>
                {feature.popular && <div className="popular-badge">Most Popular</div>}
                <div className="feature-icon">{feature.icon}</div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
                <button className="feature-btn" onClick={() => handleGetStarted(feature.title.toLowerCase())}>
                  Try Now
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Daily Horoscope Preview */}
      <section id="horoscope" className="horoscope-preview">
        <div className="container">
          <div className="section-header">
            <h2>Today's Cosmic Insights</h2>
            <p>Personalized predictions based on current planetary transits</p>
          </div>
          <div className="zodiac-wheel">
            {['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'].map((sign, index) => (
              <div key={index} className={`zodiac-sign ${userSign === index ? 'active' : ''}`} 
                   onClick={() => setUserSign(index)}>
                <span className="sign-symbol">{sign}</span>
                <span className="sign-name">
                  {['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'][index]}
                </span>
              </div>
            ))}
          </div>
          {userSign !== null && (
            <div className="horoscope-card">
              <h3>{['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'][userSign]} Today</h3>
              <div className="horoscope-content">
                <div className="horoscope-section">
                  <h4>🌟 Overall</h4>
                  <p>Jupiter's favorable transit brings opportunities for growth and expansion in your life.</p>
                </div>
                <div className="horoscope-section">
                  <h4>💝 Love</h4>
                  <p>Venus in your 7th house enhances romantic connections and partnerships.</p>
                </div>
                <div className="horoscope-section">
                  <h4>💰 Career</h4>
                  <p>Mars energy supports professional advancement and leadership opportunities.</p>
                </div>
              </div>
              <button className="detailed-btn">Get Detailed Reading</button>
            </div>
          )}
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials">
        <div className="container">
          <div className="section-header">
            <h2>What Our Users Say</h2>
            <p>Real experiences from our astrological community</p>
          </div>
          <div className="testimonials-grid">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="testimonial-card">
                <div className="testimonial-header">
                  <div className="user-avatar">{testimonial.image}</div>
                  <div className="user-info">
                    <h4>{testimonial.name}</h4>
                    <p>{testimonial.location}</p>
                  </div>
                  <div className="rating">
                    {'⭐'.repeat(testimonial.rating)}
                  </div>
                </div>
                <p className="testimonial-text">"{testimonial.text}"</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Start Your Astrological Journey Today</h2>
            <p>Join thousands who trust our authentic Vedic predictions</p>
            <div className="cta-buttons">
              <button className="cta-primary" onClick={() => handleGetStarted('birth-chart')}>
                Get Free Birth Chart
              </button>
              <button className="cta-secondary" onClick={() => handleGetStarted('compatibility')}>
                Check Compatibility
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-section">
              <div className="footer-logo">
                <span className="logo-icon">🌟</span>
                <span className="logo-text">AstroRoshni</span>
              </div>
              <p>Authentic Vedic Astrology with Scientific Precision</p>
            </div>
            <div className="footer-section">
              <h4>Services</h4>
              <ul>
                <li><a href="#birth-chart">Birth Chart</a></li>
                <li><a href="#horoscope">Daily Horoscope</a></li>
                <li><a href="#compatibility">Compatibility</a></li>
                <li><a href="#health-analysis">Health Analysis</a></li>
                <li><a href="#predictions">Predictions</a></li>
              </ul>
            </div>
            <div className="footer-section">
              <h4>Support</h4>
              <ul>
                <li><a href="#help">Help Center</a></li>
                <li><a href="#contact">Contact Us</a></li>
                <li><a href="#privacy">Privacy Policy</a></li>
                <li><a href="#terms">Terms of Service</a></li>
              </ul>
            </div>
            <div className="footer-section">
              <h4>Connect</h4>
              <div className="social-links">
                <a href="#facebook">📘</a>
                <a href="#twitter">🐦</a>
                <a href="#instagram">📷</a>
                <a href="#youtube">📺</a>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2024 AstroRoshni. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;