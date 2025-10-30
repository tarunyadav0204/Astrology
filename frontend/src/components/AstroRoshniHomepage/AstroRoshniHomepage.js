import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { APP_CONFIG } from '../../config/app.config';
import NavigationHeader from '../Shared/NavigationHeader';
import './AstroRoshniHomepage.css';

const AstroRoshniHomepage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [selectedZodiac, setSelectedZodiac] = useState('aries');
  const [horoscopeData, setHoroscopeData] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('daily');

  const bannerSlides = [
    { id: 1, image: '/images/banner-ai-astrologers.jpg', title: 'AI Astrologers Available 24/7' },
    { id: 2, image: '/images/banner-premium-reports.jpg', title: 'Premium Astrology Reports' },
    { id: 3, image: '/images/banner-live-consultation.jpg', title: 'Live Consultation with Experts' }
  ];

  const aiAstrologers = [
    { id: 1, name: 'Acharya Joshi', expertise: 'Vedic, KP System', experience: '15+ Years', rate: '₹21/min', rating: 4.8, image: 'https://images.unsplash.com/photo-1566753323558-f4e0952af115?w=150&h=150&fit=crop&crop=face', status: 'online' },
    { id: 2, name: 'Dr. Priya Sharma', expertise: 'Numerology, Tarot', experience: '12+ Years', rate: '₹18/min', rating: 4.9, image: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=face', status: 'online' },
    { id: 3, name: 'Pandit Raj Kumar', expertise: 'Vedic, Palmistry', experience: '20+ Years', rate: '₹25/min', rating: 4.7, image: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150&h=150&fit=crop&crop=face', status: 'busy' },
    { id: 4, name: 'Astro Ananya', expertise: 'Love, Career', experience: '8+ Years', rate: '₹15/min', rating: 4.6, image: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&h=150&fit=crop&crop=face', status: 'online' },
    { id: 5, name: 'Guru Vikash', expertise: 'Vastu, Remedies', experience: '18+ Years', rate: '₹22/min', rating: 4.8, image: 'https://images.unsplash.com/photo-1582233479366-6d38bc390a08?w=150&h=150&fit=crop&crop=face', status: 'online' }
  ];

  const zodiacSigns = [
    { name: 'aries', symbol: '♈', displayName: 'Aries' },
    { name: 'taurus', symbol: '♉', displayName: 'Taurus' },
    { name: 'gemini', symbol: '♊', displayName: 'Gemini' },
    { name: 'cancer', symbol: '♋', displayName: 'Cancer' },
    { name: 'leo', symbol: '♌', displayName: 'Leo' },
    { name: 'virgo', symbol: '♍', displayName: 'Virgo' },
    { name: 'libra', symbol: '♎', displayName: 'Libra' },
    { name: 'scorpio', symbol: '♏', displayName: 'Scorpio' },
    { name: 'sagittarius', symbol: '♐', displayName: 'Sagittarius' },
    { name: 'capricorn', symbol: '♑', displayName: 'Capricorn' },
    { name: 'aquarius', symbol: '♒', displayName: 'Aquarius' },
    { name: 'pisces', symbol: '♓', displayName: 'Pisces' }
  ];

  const services = [
    { icon: '📊', title: 'Free Kundli', desc: 'Complete birth chart analysis' },
    { icon: '💕', title: 'Horoscope Matching', desc: 'Compatibility for marriage' },
    { icon: '🔮', title: 'Daily Horoscope', desc: 'Your daily predictions' },
    { icon: '📞', title: 'Talk to Astrologer', desc: 'Live consultation' },
    { icon: '💎', title: 'Gemstone Report', desc: 'Personalized recommendations' },
    { icon: '🏠', title: 'Vastu Consultation', desc: 'Home & office guidance' },
    { icon: '📈', title: 'Career Report', desc: 'Professional guidance' },
    { icon: '💰', title: 'Finance Report', desc: 'Money & wealth analysis' }
  ];

  const premiumServices = [
    { title: 'Brihat Kundli', price: '₹299', desc: '250+ pages detailed report', icon: '📋' },
    { title: 'Marriage Report', price: '₹199', desc: 'Complete marriage analysis', icon: '💒' },
    { title: 'Career Guidance', price: '₹249', desc: 'Professional path analysis', icon: '💼' },
    { title: 'Health Report', price: '₹179', desc: 'Medical astrology insights', icon: '🏥' },
    { title: 'Finance Report', price: '₹229', desc: 'Wealth & money analysis', icon: '💰' },
    { title: 'Love & Relationship', price: '₹189', desc: 'Romance compatibility guide', icon: '💕' },
    { title: 'Business Report', price: '₹279', desc: 'Enterprise success analysis', icon: '🏢' },
    { title: 'Children Report', price: '₹159', desc: 'Child birth & upbringing', icon: '👶' },
    { title: 'Education Report', price: '₹169', desc: 'Academic success guidance', icon: '🎓' }
  ];

  const testimonials = [
    { name: 'Priya Sharma', location: 'Mumbai', rating: 5, text: 'Accurate predictions helped me find my soulmate!', image: 'https://images.unsplash.com/photo-1494790108755-2616c9c0e8e0?w=80&h=80&fit=crop&crop=face' },
    { name: 'Rajesh Kumar', location: 'Delhi', rating: 5, text: 'Career guidance was spot on. Got promotion within 3 months!', image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&crop=face' },
    { name: 'Anita Patel', location: 'Ahmedabad', rating: 5, text: 'Marriage compatibility report saved my relationship.', image: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=80&h=80&fit=crop&crop=face' }
  ];

  const vipTiers = [
    { name: 'Gold', price: '₹999/month', features: ['Priority Support', '50% Off Reports', 'Monthly Consultation'], icon: '🥇' },
    { name: 'Platinum', price: '₹1999/month', features: ['Celebrity Astrologer Access', 'Unlimited Reports', 'Weekly Consultation'], icon: '🏆' },
    { name: 'Diamond', price: '₹4999/month', features: ['Personal Astrologer', 'Custom Remedies', 'Daily Guidance'], icon: '💎' }
  ];

  const liveOffers = [
    { title: 'First Consultation FREE', desc: 'Limited time offer for new users', timer: '23:45:12', color: '#f44336' },
    { title: '50% OFF Premium Reports', desc: 'Valid till midnight today', timer: '11:23:45', color: '#ff9800' }
  ];

  const todaysData = {
    luckyNumbers: [3, 7, 21, 45],
    luckyColors: ['Golden', 'Green', 'Blue'],
    planetaryPositions: [
      { planet: 'Sun', sign: 'Capricorn', degree: '15°23\'', house: 10 },
      { planet: 'Moon', sign: 'Pisces', degree: '8°45\'', house: 12 },
      { planet: 'Mars', sign: 'Aries', degree: '22°10\'', house: 1 }
    ]
  };

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % bannerSlides.length);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetchHoroscopes();
  }, []);

  const fetchHoroscopes = async () => {
    setLoading(true);
    try {
      const API_BASE_URL = process.env.NODE_ENV === 'production' 
        ? APP_CONFIG.api.prod 
        : APP_CONFIG.api.dev;
      const endpoint = `${API_BASE_URL}/api/horoscope/all-signs`;
      const response = await fetch(endpoint);
      const data = await response.json();
      setHoroscopeData(data);
    } catch (error) {
      console.error('Error fetching horoscopes:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentHoroscope = () => {
    if (!horoscopeData[selectedZodiac]) {
      return {
        prediction: {
          overall: 'Loading your personalized horoscope...',
          love: 'Love predictions loading...',
          career: 'Career insights loading...',
          health: 'Health guidance loading...',
          finance: 'Financial outlook loading...'
        },
        lucky_number: '...',
        lucky_color: '...',
        rating: 0
      };
    }
    return horoscopeData[selectedZodiac];
  };

  const handleAdminClick = () => {
    if (onAdminClick) {
      onAdminClick();
    }
  };

  const handlePeriodChange = (period) => {
    setSelectedPeriod(period);
    // Scroll to horoscope section
    const horoscopeSection = document.querySelector('.horoscope-section');
    if (horoscopeSection) {
      horoscopeSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="investor-homepage">
      {/* Animated Solar System */}
      <div className="solar-system">
        <div className="sun"></div>
        <div className="orbit orbit-1">
          <div className="planet planet-1"></div>
        </div>
        <div className="orbit orbit-2">
          <div className="planet planet-2"></div>
        </div>
        <div className="orbit orbit-3">
          <div className="planet planet-3"></div>
        </div>
      </div>
      
      {/* Floating Constellation */}
      <div className="constellation">
        <div className="constellation-star"></div>
        <div className="constellation-star"></div>
        <div className="constellation-star"></div>
        <div className="constellation-star"></div>
        <div className="constellation-star"></div>
        <div className="constellation-line line-1"></div>
        <div className="constellation-line line-2"></div>
      </div>
      
      <NavigationHeader 
        onPeriodChange={handlePeriodChange}
        showZodiacSelector={false}
        zodiacSigns={zodiacSigns}
        selectedZodiac={selectedZodiac}
        onZodiacChange={setSelectedZodiac}
        user={user}
        onAdminClick={handleAdminClick}
        onLogout={onLogout}
        onLogin={onLogin}
        showLoginButton={showLoginButton}
      />

      {/* Your Life Categories */}
      <section className="life-categories">
        <div className="container">
          <div className="life-categories-header">
            <h3>✨ Discover Your Life Path</h3>
            <p>Unlock the secrets of your destiny with best in class Vedic Astrology</p>
          </div>
          <div className="life-categories-grid">
            <div className="life-category" onClick={() => user ? navigate('/career-guidance') : onLogin()}>
              <div className="category-icon">💼</div>
              <div className="category-content">
                <h4>Your Career</h4>
                <p>Professional success & growth</p>
              </div>
              <div className="category-arrow">→</div>
            </div>
            <div className="life-category" onClick={() => user ? navigate('/marriage-analysis') : onLogin()}>
              <div className="category-icon">💕</div>
              <div className="category-content">
                <h4>Your Marriage</h4>
                <p>Love, compatibility & relationships</p>
              </div>
              <div className="category-arrow">→</div>
            </div>
            <div className="life-category">
              <div className="category-icon">🎓</div>
              <div className="category-content">
                <h4>Your Education</h4>
                <p>Learning path & academic success</p>
              </div>
              <div className="category-arrow">→</div>
            </div>
            <div className="life-category">
              <div className="category-icon">🌿</div>
              <div className="category-content">
                <h4>Your Health</h4>
                <p>Wellness & vitality insights</p>
              </div>
              <div className="category-arrow">→</div>
            </div>
            <div className="life-category">
              <div className="category-icon">💎</div>
              <div className="category-content">
                <h4>Your Wealth</h4>
                <p>Financial prosperity & abundance</p>
              </div>
              <div className="category-arrow">→</div>
            </div>
          </div>
        </div>
      </section>

      {/* Banner Slider */}
      <section className="banner-slider">
        <div className="slider-container">
          {bannerSlides.map((slide, index) => (
            <div 
              key={slide.id}
              className={`slide ${index === currentSlide ? 'active' : ''}`}
            >
              <div className="slide-content">
                <h2>{slide.title}</h2>
                <button className="cta-btn">Get Started</button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* AI Astrologers Section */}
      <section className="ai-astrologers">
        <div className="container">
          <div className="section-header">
            <h2>AI Astrologers</h2>
            <a href="#all-astrologers" className="view-all">View All →</a>
          </div>
          
          <div className="astrologers-scroll">
            {aiAstrologers.map(astrologer => (
              <div key={astrologer.id} className="astrologer-card">
                <div className="astrologer-image">
                  <div 
                    className="placeholder-img" 
                    style={{
                      backgroundImage: `url(${astrologer.image})`,
                      backgroundSize: 'cover',
                      backgroundPosition: 'center'
                    }}
                  >
                  </div>
                  <span className={`status-dot ${astrologer.status}`}></span>
                </div>
                <div className="astrologer-info">
                  <h4>{astrologer.name}</h4>
                  <p className="expertise">{astrologer.expertise}</p>
                  <p className="experience">{astrologer.experience}</p>
                  <div className="rating">
                    ⭐ {astrologer.rating}
                  </div>
                  <div className="rate">{astrologer.rate}</div>
                  <div className="action-buttons">
                    <button className="call-btn">📞 Call</button>
                    <button className="chat-btn">💬 Chat</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AstroRoshni Software Advertisement */}
      <section className="astroroshni-ad">
        <div className="container">
          <div className="astroroshni-banner">
            <div className="astroroshni-content">
              <div className="astroroshni-badge">🌟 WORLD'S #1 ASTROLOGY SOFTWARE</div>
              <h2>AstroVishnu Professional</h2>
              <p className="astroroshni-tagline">The Most Advanced Vedic Astrology Software Globally</p>
              <div className="astroroshni-features">
                <span>✨ Swiss Ephemeris Precision</span>
                <span>🎯 Highest Automation Level</span>
                <span>📊 Feature Rich Charts</span>
                <span>🔮 Advanced Dasha Systems</span>
              </div>
              <div className="astroroshni-pricing">
                <span className="old-price">₹4,999</span>
                <span className="new-price">₹2,999</span>
                <span className="discount">40% OFF</span>
              </div>
              <button className="astroroshni-btn" onClick={() => window.open('/astroroshni', '_blank')}>
                🚀 EXPLORE ASTROVISHNU
              </button>
            </div>
            <div className="astroroshni-visual">
              <div className="software-mockup">
                <div className="mockup-screen">
                  <div className="chart-preview">📊</div>
                  <div className="feature-icons">
                    <span>🌙</span><span>⭐</span><span>🪐</span><span>🔮</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Premium Services - Moved Higher */}
      <section className="premium-services">
        <div className="container">
          <h2>Astrological Services for Accurate Answers</h2>
          <div className="premium-grid">
            <div className="featured-service">
              <div className="ribbon">33% OFF</div>
              <div className="service-image">
                <div className="placeholder-img">📊</div>
              </div>
              <h3>AstroVishnu Software - 1 Year</h3>
              <p>Advanced astrology software with cloud features</p>
              <button className="buy-btn">BUY NOW</button>
            </div>
            
            {premiumServices.map((service, index) => (
              <div key={index} className="premium-card">
                <div className="service-image">
                  <div className="placeholder-img">{service.icon}</div>
                </div>
                <h4>{service.title}</h4>
                <p>{service.desc}</p>
                <div className="price">{service.price}</div>
                <button 
                  className="check-btn" 
                  onClick={() => {
                    if (service.title === 'Marriage Report') {
                      navigate('/marriage-analysis');
                    } else if (service.title === 'Career Guidance') {
                      navigate('/career-guidance');
                    }
                  }}
                >
                  Check Now
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Main Content */}
      <div className="main-content">
        <div className="container">
          <div className="content-grid">
            {/* Column 1 - Kundli Form (25%) */}
            <div className="form-card">
              <h3>Kundli / Birth Chart</h3>
              <form className="birth-form">
                <input type="text" placeholder="Name" />
                <select>
                  <option>Male</option>
                  <option>Female</option>
                </select>
                <div className="date-inputs">
                  <input type="number" placeholder="Day" />
                  <input type="number" placeholder="Month" />
                  <input type="number" placeholder="Year" />
                </div>
                <div className="time-inputs">
                  <input type="number" placeholder="Hours" />
                  <input type="number" placeholder="Minutes" />
                  <input type="number" placeholder="Seconds" />
                </div>
                <input type="text" placeholder="Birth Place" />
                <button type="submit" className="submit-btn">Get Kundli</button>
              </form>
            </div>

            {/* Column 2 - Matching Form (50%) */}
            <div className="form-card">
              <h3>Kundli Matching</h3>
              <form className="matching-form">
                <div className="matching-container">
                  <div className="boy-section">
                    <h4>Boy's Details</h4>
                    <input type="text" placeholder="Name" />
                    <div className="date-inputs">
                      <input type="number" placeholder="Day" />
                      <input type="number" placeholder="Month" />
                      <input type="number" placeholder="Year" />
                    </div>
                    <div className="time-inputs">
                      <input type="number" placeholder="Hours" />
                      <input type="number" placeholder="Minutes" />
                      <input type="number" placeholder="Seconds" />
                    </div>
                    <input type="text" placeholder="Birth Place" />
                  </div>
                  
                  <div className="girl-section">
                    <h4>Girl's Details</h4>
                    <input type="text" placeholder="Name" />
                    <div className="date-inputs">
                      <input type="number" placeholder="Day" />
                      <input type="number" placeholder="Month" />
                      <input type="number" placeholder="Year" />
                    </div>
                    <div className="time-inputs">
                      <input type="number" placeholder="Hours" />
                      <input type="number" placeholder="Minutes" />
                      <input type="number" placeholder="Seconds" />
                    </div>
                    <input type="text" placeholder="Birth Place" />
                  </div>
                </div>
                <button type="submit" className="submit-btn">Check Compatibility</button>
              </form>
            </div>

            {/* Column 3 - Panchang (25%) */}
            <div className="panchang-card">
              <h3>Panchang</h3>
              <p><strong>New Delhi, India (Today)</strong></p>
              <div className="panchang-details">
                <p><strong>Tithi:</strong> Krishna Amavasya</p>
                <p><strong>Nakshatra:</strong> Chitra</p>
                <p><strong>Yoga:</strong> Vishkambha</p>
                <p><strong>Karan:</strong> Naaga</p>
              </div>
              <button className="panchang-btn">Today Panchang</button>
            </div>
          </div>
        </div>
      </div>

      {/* Services Grid */}
      <section className="services-section">
        <div className="container">
          <h2>Free Horoscope and Astrology Services</h2>
          <div className="services-grid">
            {services.map((service, index) => (
              <div key={index} className="service-card">
                <div className="service-icon">{service.icon}</div>
                <h4>{service.title}</h4>
                <p>{service.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Horoscope Section */}
      <section className="horoscope-section">
        <div className="container">
          <div className="section-header">
            <h2>Western Horoscopes</h2>
          </div>
          <div className="horoscope-grid">
            <div className="horoscope-content">
              <div className="horoscope-tabs">
                <button className={`tab ${selectedPeriod === 'daily' ? 'active' : ''}`} onClick={() => setSelectedPeriod('daily')}>Daily</button>
                <button className={`tab ${selectedPeriod === 'weekly' ? 'active' : ''}`} onClick={() => setSelectedPeriod('weekly')}>Weekly</button>
                <button className={`tab ${selectedPeriod === 'monthly' ? 'active' : ''}`} onClick={() => setSelectedPeriod('monthly')}>Monthly</button>
                <button className={`tab ${selectedPeriod === 'yearly' ? 'active' : ''}`} onClick={() => setSelectedPeriod('yearly')}>Yearly</button>
              </div>
              
              <div className="zodiac-grid">
                {zodiacSigns.map(sign => (
                  <button 
                    key={sign.name}
                    className={`zodiac-card ${selectedZodiac === sign.name ? 'active' : ''}`}
                    onClick={() => setSelectedZodiac(sign.name)}
                  >
                    <div className="zodiac-icon">{sign.symbol}</div>
                    <div className="zodiac-text">{sign.displayName}</div>
                  </button>
                ))}
              </div>

              <div className="horoscope-content-area">
                <h3>{selectedZodiac.charAt(0).toUpperCase() + selectedZodiac.slice(1)} {selectedPeriod.charAt(0).toUpperCase() + selectedPeriod.slice(1)} Horoscope</h3>
                {loading ? (
                  <div className="horoscope-loading">Loading your personalized horoscope...</div>
                ) : (
                  <div className="horoscope-details">
                    <div className="horoscope-main">
                      <p><strong>Overall:</strong> {getCurrentHoroscope().prediction?.overall}</p>
                    </div>
                    <div className="horoscope-categories">
                      <div className="category">
                        <h4>💕 Love</h4>
                        <p>{getCurrentHoroscope().prediction?.love}</p>
                      </div>
                      <div className="category">
                        <h4>💼 Career</h4>
                        <p>{getCurrentHoroscope().prediction?.career}</p>
                      </div>
                      <div className="category">
                        <h4>🏥 Health</h4>
                        <p>{getCurrentHoroscope().prediction?.health}</p>
                      </div>
                      <div className="category">
                        <h4>💰 Finance</h4>
                        <p>{getCurrentHoroscope().prediction?.finance}</p>
                      </div>
                    </div>
                    <div className="horoscope-extras">
                      <div className="lucky-info">
                        <span><strong>Lucky Number:</strong> {getCurrentHoroscope().lucky_number}</span>
                        <span><strong>Lucky Color:</strong> {getCurrentHoroscope().lucky_color}</span>
                        <span><strong>Rating:</strong> {'⭐'.repeat(getCurrentHoroscope().rating || 0)}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="festivals-sidebar">
              <h3>Festivals</h3>
              <div className="festival-tabs">
                <button className="tab active">Festival 2025</button>
                <button className="tab">Holidays 2025</button>
              </div>
              <div className="festival-list">
                <a href="#diwali">Diwali 2025</a>
                <a href="#navratri">Navratri 2025</a>
                <a href="#dussehra">Dussehra 2025</a>
                <a href="#karva">Karva Chauth 2025</a>
              </div>
            </div>
          </div>
        </div>
      </section>



      {/* Live Offers Banner */}
      <section className="live-offers">
        <div className="container">
          <div className="offers-scroll">
            {liveOffers.map((offer, index) => (
              <div key={index} className="offer-banner" style={{borderColor: offer.color}}>
                <div className="offer-content">
                  <h3>{offer.title}</h3>
                  <p>{offer.desc}</p>
                  <div className="timer" style={{color: offer.color}}>
                    ⏰ {offer.timer}
                  </div>
                </div>
                <button className="claim-btn" style={{background: offer.color}}>CLAIM NOW</button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust & Social Proof */}
      <section className="trust-section">
        <div className="container">
          <div className="trust-stats">
            <div className="stat-item">
              <div className="stat-number">50,000+</div>
              <div className="stat-label">Happy Customers</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">15+</div>
              <div className="stat-label">Years Experience</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">98%</div>
              <div className="stat-label">Accuracy Rate</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">24/7</div>
              <div className="stat-label">Support Available</div>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Features */}
      <section className="interactive-section">
        <div className="container">
          <h2>Today's Cosmic Insights</h2>
          <div className="interactive-grid">
            <div className="lucky-widget">
              <h3>🍀 Today's Lucky</h3>
              <div className="lucky-content">
                <div className="lucky-item">
                  <strong>Numbers:</strong> {todaysData.luckyNumbers.join(', ')}
                </div>
                <div className="lucky-item">
                  <strong>Colors:</strong> {todaysData.luckyColors.join(', ')}
                </div>
              </div>
            </div>
            
            <div className="planetary-widget">
              <h3>🪐 Live Planetary Positions</h3>
              <div className="planet-list">
                {todaysData.planetaryPositions.map((planet, index) => (
                  <div key={index} className="planet-item">
                    <span className="planet-name">{planet.planet}</span>
                    <span className="planet-sign">{planet.sign} {planet.degree}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="compatibility-widget">
              <h3>💕 Quick Compatibility</h3>
              <div className="compat-form">
                <select><option>Your Sign</option></select>
                <select><option>Partner's Sign</option></select>
                <button className="check-compat-btn">Check Match</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials-section">
        <div className="container">
          <h2>What Our Customers Say</h2>
          <div className="testimonials-grid">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="testimonial-card">
                <div className="testimonial-header">
                  <img src={testimonial.image} alt={testimonial.name} className="testimonial-avatar" />
                  <div className="testimonial-info">
                    <h4>{testimonial.name}</h4>
                    <p>{testimonial.location}</p>
                    <div className="rating">{'⭐'.repeat(testimonial.rating)}</div>
                  </div>
                </div>
                <p className="testimonial-text">"{testimonial.text}"</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* VIP Membership */}
      <section className="vip-section">
        <div className="container">
          <h2>VIP Membership Plans</h2>
          <div className="vip-grid">
            {vipTiers.map((tier, index) => (
              <div key={index} className="vip-card">
                <div className="vip-icon">{tier.icon}</div>
                <h3>{tier.name}</h3>
                <div className="vip-price">{tier.price}</div>
                <ul className="vip-features">
                  {tier.features.map((feature, i) => (
                    <li key={i}>✓ {feature}</li>
                  ))}
                </ul>
                <button className="vip-btn">Choose Plan</button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Mobile App Promotion */}
      <section className="app-section">
        <div className="container">
          <div className="app-content">
            <div className="app-info">
              <h2>📱 Download Our Mobile App</h2>
              <p>Get instant access to astrology on the go!</p>
              <ul className="app-features">
                <li>✓ Push notifications for important transits</li>
                <li>✓ Offline chart viewing</li>
                <li>✓ Quick consultation booking</li>
                <li>✓ Daily horoscope alerts</li>
              </ul>
              <div className="app-badges">
                <button className="app-badge">📱 App Store</button>
                <button className="app-badge">🤖 Google Play</button>
              </div>
            </div>
            <div className="app-mockup">
              <div className="phone-mockup">📱</div>
            </div>
          </div>
        </div>
      </section>

      {/* Educational Content */}
      <section className="education-section">
        <div className="container">
          <h2>Learn Astrology</h2>
          <div className="education-grid">
            <div className="education-card">
              <h3>🎓 Beginner's Guide</h3>
              <p>Start your astrology journey with basics</p>
              <button className="learn-btn">Start Learning</button>
            </div>
            <div className="education-card">
              <h3>📚 Advanced Courses</h3>
              <p>Master complex astrological techniques</p>
              <button className="learn-btn">Explore Courses</button>
            </div>
            <div className="education-card">
              <h3>🔍 Myth vs Reality</h3>
              <p>Separate facts from misconceptions</p>
              <button className="learn-btn">Read Articles</button>
            </div>
          </div>
        </div>
      </section>

      {/* Live Chat Widget */}
      <div className="live-chat-widget">
        <button className="chat-widget-btn">
          💬 Ask Question Now
          <span className="chat-pulse"></span>
        </button>
      </div>

      {/* Consultation Section */}
      <section className="consultation-section">
        <div className="container">
          <h2>Consult Astrologer on Call & Chat</h2>
          <div className="consultation-grid">
            {aiAstrologers.slice(0, 4).map(astrologer => (
              <div key={astrologer.id} className="consultation-card">
                <div className="astrologer-profile">
                  <div className="profile-image">
                    <div 
                      className="placeholder-img" 
                      style={{
                        backgroundImage: `url(${astrologer.image})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center'
                      }}
                    >
                    </div>
                    <span className={`status-dot ${astrologer.status}`}></span>
                  </div>
                  <div className="profile-info">
                    <h4>{astrologer.name}</h4>
                    <p className="expertise">{astrologer.expertise}</p>
                    <p className="experience">{astrologer.experience}</p>
                    <div className="rating">⭐ {astrologer.rating}</div>
                    <div className="rate">{astrologer.rate}</div>
                  </div>
                </div>
                <div className="consultation-actions">
                  <button className="call-btn">📞 Call</button>
                  <button className="chat-btn">💬 Chat</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="main-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-links">
              <a href="#shop">Shop</a>
              <a href="#astrologers">Astrologers</a>
              <a href="#kundli">Free Kundli</a>
              <a href="#matching">Horoscope Matching</a>
              <a href="#zodiac">Zodiac Signs</a>
              <a href="#about">About Us</a>
              <a href="#contact">Contact Us</a>
              <a href="#privacy">Privacy Policy</a>
            </div>
            <div className="footer-bottom">
              <p>© 2025 AstroRoshni.com. All rights reserved.</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AstroRoshniHomepage;