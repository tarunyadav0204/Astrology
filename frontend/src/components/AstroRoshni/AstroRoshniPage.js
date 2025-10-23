import React, { useState } from 'react';
import './AstroRoshniPage.css';

const AstroRoshniPage = () => {
  const [selectedPlan, setSelectedPlan] = useState('professional');

  const features = [
    { icon: '🎯', title: 'Swiss Ephemeris Precision', desc: 'Most accurate planetary calculations globally' },
    { icon: '🤖', title: 'Highest Automation Level', desc: 'Advanced machine learning for precise forecasts' },
    { icon: '⚡', title: 'Automatic Event Detection', desc: 'Detects when events might have happened without scrolling through dashas and transits', featured: true },
    { icon: '📊', title: 'Feature Rich Charts', desc: 'Complete Vedic & Western astrology charts' },
    { icon: '🔮', title: 'Advanced Dasha Systems', desc: 'Vimshottari, Ashtottari, Yogini & more' },
    { icon: '🌟', title: 'Nakshatra Analysis', desc: 'Deep insights into lunar mansions' },
    { icon: '💎', title: 'Yoga Detection', desc: 'Automatic identification of 300+ yogas' },
    { icon: '🏠', title: 'House Strength Analysis', desc: 'Comprehensive bhava bala calculations' },
    { icon: '🔄', title: 'Transit Predictions', desc: 'Real-time planetary transit effects' },
    { icon: '💕', title: 'Compatibility Matching', desc: 'Advanced Ashtakoot & KP matching' },
    { icon: '📱', title: 'Multi-Platform Support', desc: 'Windows, Mac, Web & Mobile apps' },
    { icon: '☁️', title: 'Cloud Synchronization', desc: 'Access your data anywhere, anytime' }
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
        '50 Chart Limit'
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
      title: 'Professional Astrologer',
      image: 'https://images.unsplash.com/photo-1566753323558-f4e0952af115?w=80&h=80&fit=crop&crop=face',
      text: 'AstroRoshni has revolutionized my practice. The accuracy is unmatched!',
      rating: 5
    },
    {
      name: 'Dr. Priya Gupta',
      title: 'Vedic Scholar',
      image: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=80&h=80&fit=crop&crop=face',
      text: 'Best astrology software I have used in 20 years of practice.',
      rating: 5
    },
    {
      name: 'Pandit Suresh Kumar',
      title: 'KP System Expert',
      image: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=80&h=80&fit=crop&crop=face',
      text: 'The KP calculations are perfect. Highly recommended for professionals.',
      rating: 5
    }
  ];

  const screenshots = [
    { title: 'Birth Chart Analysis', image: '/images/software/birth-chart.png', desc: 'Comprehensive Vedic chart with planetary positions' },
    { title: 'Automatic Event Detection', image: '/images/software/event-detection.png', desc: 'AI-powered timeline showing potential event periods', featured: true },
    { title: 'Dasha Timeline', image: '/images/software/dasha-timeline.png', desc: 'Interactive dasha periods with predictions' },
    { title: 'Transit Analysis', image: '/images/software/transit-analysis.png', desc: 'Real-time planetary transits and effects' },
    { title: 'Shadbala Calculations', image: '/images/software/shadbala.png', desc: 'Comprehensive planetary strength analysis' },
    { title: 'Predictive Reports', image: '/images/software/predictions.png', desc: 'Detailed predictions and remedial measures' }
  ];

  return (
    <div className="astroroshni-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-background">
          <div className="cosmic-animation">
            <div className="planet planet-1"></div>
            <div className="planet planet-2"></div>
            <div className="planet planet-3"></div>
          </div>
        </div>
        <div className="container">
          <div className="hero-content">
            <div className="hero-badge">🌟 WORLD'S #1 ASTROLOGY SOFTWARE</div>
            <h1>AstroRoshni Professional</h1>
            <p className="hero-subtitle">The Most Advanced Vedic Astrology Software Trusted by 50,000+ Astrologers Globally</p>
            <div className="hero-stats">
              <div className="stat">
                <div className="stat-number">50,000+</div>
                <div className="stat-label">Active Users</div>
              </div>
              <div className="stat">
                <div className="stat-number">99.9%</div>
                <div className="stat-label">Accuracy</div>
              </div>
              <div className="stat">
                <div className="stat-number">200+</div>
                <div className="stat-label">Chart Types</div>
              </div>
            </div>
            <div className="hero-actions">
              <button className="cta-primary">🚀 Start Free Trial</button>
              <button className="cta-secondary">📹 Watch Demo</button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="container">
          <h2>Powerful Features for Professional Astrologers</h2>
          <div className="features-grid">
            {features.map((feature, index) => (
              <div key={index} className={`feature-card ${feature.featured ? 'featured' : ''}`}>
                <div className="feature-icon">{feature.icon}</div>
                <h3>{feature.title}</h3>
                <p>{feature.desc}</p>
                {feature.featured && <div className="featured-badge">UNIQUE FEATURE</div>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Screenshots Section */}
      <section className="screenshots-section">
        <div className="container">
          <h2>See AstroRoshni in Action</h2>
          <div className="screenshots-grid">
            {screenshots.map((screenshot, index) => (
              <div key={index} className={`screenshot-card ${screenshot.featured ? 'featured' : ''}`}>
                <div className="screenshot-image">
                  <img src={screenshot.image} alt={screenshot.title} />
                </div>
                <h4>{screenshot.title}</h4>
                <p>{screenshot.desc}</p>
                {screenshot.featured && <div className="featured-badge">AI POWERED</div>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Wide Dasha/Transit Table Section */}
      <section className="wide-table-section">
        <div className="container">
          <h2>Complete Dasha & Transit Analysis</h2>
          <div className="wide-image-container">
            <img src="/images/software/dasha-transit-table.png" alt="Comprehensive Dasha and Transit Analysis Table" />
            <div className="wide-image-overlay">
              <div className="overlay-content">
                <h3>🔮 Advanced Timeline Analysis</h3>
                <p>Complete dasha periods with precise transit timings for accurate predictions</p>
              </div>
            </div>
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
                  onClick={() => setSelectedPlan(plan.id)}
                >
                  Choose {plan.name}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="testimonials-section">
        <div className="container">
          <h2>Trusted by Leading Astrologers</h2>
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

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Transform Your Astrology Practice?</h2>
            <p>Join thousands of professional astrologers who trust AstroRoshni</p>
            <div className="cta-actions">
              <button className="cta-primary large">🚀 Get AstroRoshni Now</button>
              <div className="guarantee">
                <span>💯 30-Day Money Back Guarantee</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="astroroshni-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-section">
              <h3>AstroRoshni</h3>
              <p>The world's most advanced astrology software</p>
            </div>
            <div className="footer-section">
              <h4>Product</h4>
              <ul>
                <li><a href="#features">Features</a></li>
                <li><a href="#pricing">Pricing</a></li>
                <li><a href="#demo">Demo</a></li>
              </ul>
            </div>
            <div className="footer-section">
              <h4>Support</h4>
              <ul>
                <li><a href="#help">Help Center</a></li>
                <li><a href="#contact">Contact Us</a></li>
                <li><a href="#training">Training</a></li>
              </ul>
            </div>
            <div className="footer-section">
              <h4>Company</h4>
              <ul>
                <li><a href="#about">About Us</a></li>
                <li><a href="#careers">Careers</a></li>
                <li><a href="#privacy">Privacy Policy</a></li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <p>© 2025 AstroRoshni. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AstroRoshniPage;