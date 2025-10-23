import React from 'react';
import './FeatureCard.css';

const FeatureCard = ({ 
  icon, 
  title, 
  description, 
  popular = false, 
  onClick,
  features = [],
  price = null,
  buttonText = "Try Now"
}) => {
  return (
    <div className={`feature-card ${popular ? 'popular' : ''}`} onClick={onClick}>
      {popular && <div className="popular-badge">Most Popular</div>}
      
      <div className="feature-icon">{icon}</div>
      
      <h3 className="feature-title">{title}</h3>
      
      <p className="feature-description">{description}</p>
      
      {features.length > 0 && (
        <ul className="feature-list">
          {features.map((feature, index) => (
            <li key={index} className="feature-item">
              <span className="check-icon">✓</span>
              {feature}
            </li>
          ))}
        </ul>
      )}
      
      {price && (
        <div className="feature-price">
          <span className="price-currency">₹</span>
          <span className="price-amount">{price}</span>
          <span className="price-period">/month</span>
        </div>
      )}
      
      <button className="feature-btn">
        {buttonText}
      </button>
    </div>
  );
};

export default FeatureCard;