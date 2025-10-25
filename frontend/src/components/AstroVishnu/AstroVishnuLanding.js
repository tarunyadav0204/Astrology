import React, { useState, useEffect } from 'react';
import './AstroVishnuLanding.css';

const AstroVishnuLanding = ({ onLogin, onRegister }) => {
  const [selectedPlan, setSelectedPlan] = useState('professional');
  const [currentScreenshot, setCurrentScreenshot] = useState(0);
  const [showDemo, setShowDemo] = useState(false);

  const features = [
    { icon: '🎯', title: 'Swiss Ephemeris Precision', desc: '99.99% accurate planetary calculations', featured: true },
    { icon: '🤖', title: 'AI Event Detection', desc: 'Automatically detects life events without manual analysis', featured: true },
    { icon: '📊', title: '200+ Chart Types', desc: 'Complete Vedic & Western astrology charts' },
    { icon: '🔮', title: 'Advanced Dasha Systems', desc: 'Vimshottari, Ashtottari, Yogini & 15+ more' },
    { icon: '🌟', title: 'Yoga Detection Engine', desc: 'Identifies 500+ classical yogas automatically' },
    { icon: '💎', title: 'Shadbala Calculations', desc: 'Complete planetary strength analysis' },
    { icon: '🔄', title: 'Real-time Transits', desc: 'Live planetary positions and effects' },
    { icon: '💕', title: 'Advanced Matching', desc: 'Ashtakoot, KP & custom compatibility' },
    { icon: '📱', title: 'Multi-Platform', desc: 'Windows, Mac, Web & Mobile apps' },
    { icon: '☁️', title: 'Cloud Sync', desc: 'Access your data anywhere, anytime' }
  ];

  const pricingPlans = [
    {
      id: 'basic',
      name: 'Basic',
      price: '₹1,999',
      originalPrice: '₹2,999',
      duration: '1 Year License',
      features: [
        'Basic Chart Generation',
        'Dasha Calculations',
        'Transit Predictions',
        'Email Support',
        '100 Chart Limit'
      ],
      popular: false
    },
    {
      id: 'professional',
      name: 'Professional',
      price: '₹2,999',
      originalPrice: '₹4,999',
      duration: '1 Year License',
      features: [
        'All Basic Features',
        'AI Event Detection',
        'Advanced Predictions',
        'Yoga Detection',
        'Compatibility Analysis',
        'Priority Support',
        'Unlimited Charts',
        'Custom Reports'
      ],
      popular: true
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: '₹4,999',
      originalPrice: '₹7,999',
      duration: '1 Year License',
      features: [
        'All Professional Features',
        'Multi-User Access',
        'API Integration',
        'White Label Options',
        'Dedicated Support',
        'Custom Development',
        'Training Sessions'
      ],
      popular: false
    }
  ];

  const testimonials = [
    {
      name: 'Acharya Rajesh Sharma',
      title: 'Professional Astrologer, Mumbai',
      image: 'https://images.unsplash.com/photo-1566753323558-f4e0952af115?w=80&h=80&fit=crop&crop=face',
      text: 'AstroVishnu has revolutionized my practice. The AI event detection saves me hours of analysis!',
      rating: 5
    },
    {
      name: 'Dr. Priya Gupta',
      title: 'Vedic Scholar, Delhi',
      image: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=80&h=80&fit=crop&crop=face',
      text: 'Most accurate astrology software I have used in 20 years. Swiss Ephemeris precision is unmatched.',
      rating: 5
    },
    {
      name: 'Pandit Suresh Kumar',
      title: 'KP System Expert, Bangalore',
      image: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=80&h=80&fit=crop&crop=face',
      text: 'The KP calculations are perfect. My consultation efficiency increased by 300%.',
      rating: 5
    }
  ];

  const screenshots = [
    { title: 'AI Event Detection', image: '/images/software/event-detection.png', desc: 'Revolutionary AI-powered timeline showing potential life events' },
    { title: 'Birth Chart Analysis', image: '/images/software/birth-chart.png', desc: 'Comprehensive Vedic chart with planetary positions' },
    { title: 'Dasha Timeline', image: '/images/software/dasha-timeline.png', desc: 'Interactive dasha periods with predictions' },
    { title: 'Transit Analysis', image: '/images/software/transit-analysis.png', desc: 'Real-time planetary transits and effects' },
    { title: 'Shadbala Calculations', image: '/images/software/shadbala.png', desc: 'Complete planetary strength analysis' },
    { title: 'Predictive Reports', image: '/images/software/predictions.png', desc: 'Detailed predictions and remedial measures' }
  ];

  const stats = [
    { number: '50,000+', label: 'Professional Users' },
    { number: '99.99%', label: 'Calculation Accuracy' },
    { number: '200+', label: 'Chart Types' },
    { number: '15+', label: 'Years Trusted' }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentScreenshot((prev) => (prev + 1) % screenshots.length);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="astrovishnu-landing">
      <div style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 10000
      }}>
        <button 
          onClick={onLogin}
          style={{
            background: '#ff6b35',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '25px',
            fontWeight: '600',
            cursor: 'pointer',
            fontSize: '14px',
            boxShadow: '0 4px 15px rgba(255, 107, 53, 0.3)'
          }}
        >
          Sign In
        </button>
      </div>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-background">
          <div className="cosmic-animation">
            <div className="planet planet-1"></div>
            <div className="planet planet-2"></div>
            <div className="planet planet-3"></div>
            <div className="stars"></div>
          </div>
        </div>
        <div className="container">
          <div className="hero-content">
            <div className="hero-badge">🌟 WORLD'S MOST ADVANCED ASTROLOGY SOFTWARE</div>
            <h1>AstroVishnu Professional</h1>
            <p className="hero-subtitle">
              Revolutionary AI-Powered Vedic Astrology Software with Swiss Ephemeris Precision
            </p>
            <div className="hero-stats">
              {stats.map((stat, index) => (
                <div key={index} className="stat">
                  <div className="stat-number">{stat.number}</div>
                  <div className="stat-label">{stat.label}</div>
                </div>
              ))}
            </div>
            <div className="hero-actions">
              <button className="cta-primary" onClick={onLogin}>
                🚀 Start Free Trial
              </button>
              <button className="cta-secondary" onClick={onLogin}>
                🔑 Sign In
              </button>
            </div>
            <div className="trust-indicators">
              <span>✓ 30-Day Money Back Guarantee</span>
              <span>✓ No Credit Card Required</span>
              <span>✓ Instant Access</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="container">
          <h2>Powerful Features for Professional Astrologers</h2>
          <p className="section-subtitle">Everything you need to provide accurate predictions and grow your practice</p>
          <div className="features-grid">
            {features.map((feature, index) => (
              <div key={index} className={`feature-card ${feature.featured ? 'featured' : ''}`}>
                <div className="feature-icon">{feature.icon}</div>
                <h3>{feature.title}</h3>
                <p>{feature.desc}</p>
                {feature.featured && <div className="featured-badge">UNIQUE</div>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Event Detection Highlight */}
      <section className="ai-highlight-section">
        <div className="container">
          <div className="ai-highlight-content">
            <div className="ai-highlight-text">
              <div className="highlight-badge">🤖 REVOLUTIONARY AI TECHNOLOGY</div>
              <h2>Automatic Event Detection</h2>
              <p>
                Our proprietary AI analyzes birth charts and automatically detects potential life events 
                without manual dasha or transit analysis. Save hours of work and never miss important predictions.
              </p>
              <ul className="ai-benefits">
                <li>✓ Detects marriage, career, health events automatically</li>
                <li>✓ Saves 5+ hours per consultation</li>
                <li>✓ 95% accuracy in event timing</li>
                <li>✓ Works with any birth chart instantly</li>
              </ul>
              <button className="cta-primary" onClick={onLogin}>Try AI Detection Free</button>
            </div>
            <div className="ai-highlight-visual">
              <div className="ai-demo-mockup">
                <div className="mockup-screen">
                  <div className="timeline-preview">
                    <div className="event-marker marriage">💒 Marriage: 2024-2026</div>
                    <div className="event-marker career">💼 Career Change: 2025</div>
                    <div className="event-marker health">🏥 Health Focus: 2026</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* App Screenshots Section */}
      <section className="screenshots-section">
        <div className="container">
          <h2>See AstroVishnu in Action</h2>
          <p className="section-subtitle">Explore our intuitive interface and powerful features</p>
          <div className="screenshots-showcase">
            <div className="screenshot-navigation">
              {screenshots.map((screenshot, index) => (
                <button
                  key={index}
                  className={`nav-btn ${index === currentScreenshot ? 'active' : ''}`}
                  onClick={() => setCurrentScreenshot(index)}
                >
                  {screenshot.title}
                </button>
              ))}
            </div>
            <div className="screenshot-display">
              <div className="screenshot-container">
                <div className="astro-app-mockup">
                  <div className="app-header">
                    <div className="app-logo">🔮 AstroVishnu</div>
                    <div className="app-nav">
                      <span className="nav-item active">Dashboard</span>
                      <span className="nav-item">Charts</span>
                      <span className="nav-item">Predictions</span>
                    </div>
                  </div>
                  <div className="app-content">
                    {screenshots[currentScreenshot].title === 'AI Event Detection' && (
                      <div className="ai-detection-view">
                        <div className="timeline-header">
                          <h3>🤖 AI Event Detection Timeline</h3>
                          <div className="chart-info">Birth Chart: John Doe (15/08/1990, 14:30, Mumbai)</div>
                        </div>
                        <div className="timeline-events">
                          <div className="event-item marriage">
                            <div className="event-icon">💒</div>
                            <div className="event-details">
                              <div className="event-title">Marriage Period</div>
                              <div className="event-period">2024 - 2026</div>
                              <div className="event-confidence">Confidence: 87%</div>
                            </div>
                          </div>
                          <div className="event-item career">
                            <div className="event-icon">💼</div>
                            <div className="event-details">
                              <div className="event-title">Career Advancement</div>
                              <div className="event-period">2025 - 2027</div>
                              <div className="event-confidence">Confidence: 92%</div>
                            </div>
                          </div>
                          <div className="event-item health">
                            <div className="event-icon">🏥</div>
                            <div className="event-details">
                              <div className="event-title">Health Focus Required</div>
                              <div className="event-period">2026 - 2028</div>
                              <div className="event-confidence">Confidence: 78%</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    {screenshots[currentScreenshot].title === 'Birth Chart Analysis' && (
                      <div className="chart-view">
                        <div className="chart-container">
                          <div className="vedic-chart">
                            <div className="chart-center">Lagna Chart</div>
                            <div className="house house-1">As<br/>12°</div>
                            <div className="house house-2">Ve<br/>Ma</div>
                            <div className="house house-3"></div>
                            <div className="house house-4">Mo</div>
                            <div className="house house-5">Su<br/>Me</div>
                            <div className="house house-6"></div>
                            <div className="house house-7">Ju</div>
                            <div className="house house-8"></div>
                            <div className="house house-9">Sa</div>
                            <div className="house house-10">Ra</div>
                            <div className="house house-11"></div>
                            <div className="house house-12">Ke</div>
                          </div>
                        </div>
                        <div className="chart-details">
                          <h4>Planetary Positions</h4>
                          <div className="planet-list">
                            <div className="planet-item">Sun: Leo 22°15'</div>
                            <div className="planet-item">Moon: Cancer 08°42'</div>
                            <div className="planet-item">Mars: Taurus 15°33'</div>
                            <div className="planet-item">Mercury: Leo 18°27'</div>
                          </div>
                        </div>
                      </div>
                    )}
                    {screenshots[currentScreenshot].title === 'Dasha Timeline' && (
                      <div className="dasha-view">
                        <div className="dasha-header">
                          <h3>Vimshottari Dasha Timeline</h3>
                          <div className="current-dasha">Current: Venus Mahadasha → Mercury Antardasha</div>
                        </div>
                        <div className="dasha-timeline">
                          <div className="dasha-period active">
                            <div className="period-bar venus"></div>
                            <div className="period-info">
                              <div className="period-name">Venus Mahadasha</div>
                              <div className="period-dates">2020 - 2040 (20 years)</div>
                            </div>
                          </div>
                          <div className="dasha-period">
                            <div className="period-bar sun"></div>
                            <div className="period-info">
                              <div className="period-name">Sun Mahadasha</div>
                              <div className="period-dates">2040 - 2046 (6 years)</div>
                            </div>
                          </div>
                          <div className="dasha-period">
                            <div className="period-bar moon"></div>
                            <div className="period-info">
                              <div className="period-name">Moon Mahadasha</div>
                              <div className="period-dates">2046 - 2056 (10 years)</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    {screenshots[currentScreenshot].title === 'Transit Analysis' && (
                      <div className="transit-view">
                        <div className="transit-header">
                          <h3>🔄 Current Transits & Effects</h3>
                          <div className="date-info">Analysis for: December 2024</div>
                        </div>
                        <div className="transit-list">
                          <div className="transit-item important">
                            <div className="transit-planet">Jupiter</div>
                            <div className="transit-details">
                              <div className="transit-position">Transiting 7th House (Taurus)</div>
                              <div className="transit-effect">Favorable for relationships & partnerships</div>
                              <div className="transit-duration">Duration: 6 months</div>
                            </div>
                          </div>
                          <div className="transit-item">
                            <div className="transit-planet">Saturn</div>
                            <div className="transit-details">
                              <div className="transit-position">Transiting 10th House (Aquarius)</div>
                              <div className="transit-effect">Career challenges, hard work required</div>
                              <div className="transit-duration">Duration: 2.5 years</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    {screenshots[currentScreenshot].title === 'Shadbala Calculations' && (
                      <div className="shadbala-view">
                        <div className="shadbala-header">
                          <h3>💎 Shadbala - Planetary Strength Analysis</h3>
                        </div>
                        <div className="strength-table">
                          <div className="table-header">
                            <div>Planet</div>
                            <div>Total Strength</div>
                            <div>Rank</div>
                            <div>Status</div>
                          </div>
                          <div className="table-row strong">
                            <div>Jupiter</div>
                            <div>425.8</div>
                            <div>1st</div>
                            <div className="status-strong">Very Strong</div>
                          </div>
                          <div className="table-row">
                            <div>Venus</div>
                            <div>387.2</div>
                            <div>2nd</div>
                            <div className="status-good">Strong</div>
                          </div>
                          <div className="table-row">
                            <div>Moon</div>
                            <div>298.5</div>
                            <div>3rd</div>
                            <div className="status-average">Average</div>
                          </div>
                          <div className="table-row weak">
                            <div>Mars</div>
                            <div>156.3</div>
                            <div>7th</div>
                            <div className="status-weak">Weak</div>
                          </div>
                        </div>
                      </div>
                    )}
                    {screenshots[currentScreenshot].title === 'Predictive Reports' && (
                      <div className="reports-view">
                        <div className="report-header">
                          <h3>📈 Predictive Analysis Report</h3>
                          <div className="report-period">Period: 2024-2025</div>
                        </div>
                        <div className="prediction-sections">
                          <div className="prediction-card career">
                            <div className="card-header">
                              <span className="card-icon">💼</span>
                              <span className="card-title">Career & Finance</span>
                              <span className="card-score positive">85%</span>
                            </div>
                            <div className="card-content">
                              Excellent period for career growth. Jupiter's transit supports new opportunities.
                            </div>
                          </div>
                          <div className="prediction-card health">
                            <div className="card-header">
                              <span className="card-icon">🏥</span>
                              <span className="card-title">Health & Wellness</span>
                              <span className="card-score neutral">72%</span>
                            </div>
                            <div className="card-content">
                              Generally stable health. Pay attention to stress levels during Saturn transit.
                            </div>
                          </div>
                          <div className="prediction-card relationships">
                            <div className="card-header">
                              <span className="card-icon">💕</span>
                              <span className="card-title">Relationships</span>
                              <span className="card-score positive">91%</span>
                            </div>
                            <div className="card-content">
                              Highly favorable for marriage and partnerships. Venus strongly placed.
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="screenshot-overlay">
                  <h3>{screenshots[currentScreenshot].title}</h3>
                  <p>{screenshots[currentScreenshot].desc}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials-section">
        <div className="container">
          <h2>Trusted by Professional Astrologers Worldwide</h2>
          <div className="testimonials-grid">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="testimonial-card">
                <div className="testimonial-header">
                  <img src={testimonial.image} alt={testimonial.name} />
                  <div className="testimonial-info">
                    <h4>{testimonial.name}</h4>
                    <p>{testimonial.title}</p>
                    <div className="rating">{'⭐'.repeat(testimonial.rating)}</div>
                  </div>
                </div>
                <p className="testimonial-text">"{testimonial.text}"</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="pricing-section">
        <div className="container">
          <h2>Choose Your Perfect Plan</h2>
          <p className="pricing-subtitle">Special Launch Offer - Save up to 40%</p>
          <div className="pricing-grid">
            {pricingPlans.map((plan) => (
              <div key={plan.id} className={`pricing-card ${plan.popular ? 'popular' : ''}`}>
                {plan.popular && <div className="popular-badge">MOST POPULAR</div>}
                <h3>{plan.name}</h3>
                <div className="price-display">
                  <span className="original-price">{plan.originalPrice}</span>
                  <span className="current-price">{plan.price}</span>
                </div>
                <div className="duration">{plan.duration}</div>
                <ul className="features-list">
                  {plan.features.map((feature, index) => (
                    <li key={index}>✓ {feature}</li>
                  ))}
                </ul>
                <button 
                  className={`plan-btn ${plan.popular ? 'popular-btn' : ''}`}
                  onClick={onLogin}
                >
                  Start Free Trial
                </button>
              </div>
            ))}
          </div>
          <div className="pricing-guarantee">
            <p>💰 30-Day Money Back Guarantee | 🔒 Secure Payment | 📞 24/7 Support</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="final-cta-section">
        <div className="container">
          <div className="final-cta-content">
            <h2>Ready to Transform Your Astrology Practice?</h2>
            <p>Join 50,000+ professional astrologers who trust AstroVishnu for accurate predictions</p>
            <div className="final-cta-actions">
              <button className="cta-primary large" onClick={onLogin}>
                🚀 Start Your Free Trial Now
              </button>
              <button className="cta-secondary" onClick={onRegister}>
                📝 Create Account
              </button>
            </div>
            <div className="final-trust-indicators">
              <span>✓ No Setup Fees</span>
              <span>✓ Cancel Anytime</span>
              <span>✓ Instant Access</span>
            </div>
          </div>
        </div>
      </section>

      {/* Demo Modal */}
      {showDemo && (
        <div className="demo-modal" onClick={() => setShowDemo(false)}>
          <div className="demo-content" onClick={(e) => e.stopPropagation()}>
            <button className="close-btn" onClick={() => setShowDemo(false)}>×</button>
            <h3>AstroVishnu Demo Video</h3>
            <div className="demo-video-placeholder">
              <div className="play-icon">▶️</div>
              <p>Demo video would be embedded here</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AstroVishnuLanding;