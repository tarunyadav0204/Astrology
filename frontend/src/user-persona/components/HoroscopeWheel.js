import React, { useState, useEffect } from 'react';
import './HoroscopeWheel.css';

const HoroscopeWheel = ({ onSignSelect, selectedSign }) => {
  const [animatedSigns, setAnimatedSigns] = useState(new Set());

  const zodiacSigns = [
    { symbol: '♈', name: 'Aries', element: 'Fire', dates: 'Mar 21 - Apr 19', color: '#FF6B6B' },
    { symbol: '♉', name: 'Taurus', element: 'Earth', dates: 'Apr 20 - May 20', color: '#4ECDC4' },
    { symbol: '♊', name: 'Gemini', element: 'Air', dates: 'May 21 - Jun 20', color: '#45B7D1' },
    { symbol: '♋', name: 'Cancer', element: 'Water', dates: 'Jun 21 - Jul 22', color: '#96CEB4' },
    { symbol: '♌', name: 'Leo', element: 'Fire', dates: 'Jul 23 - Aug 22', color: '#FFEAA7' },
    { symbol: '♍', name: 'Virgo', element: 'Earth', dates: 'Aug 23 - Sep 22', color: '#DDA0DD' },
    { symbol: '♎', name: 'Libra', element: 'Air', dates: 'Sep 23 - Oct 22', color: '#98D8C8' },
    { symbol: '♏', name: 'Scorpio', element: 'Water', dates: 'Oct 23 - Nov 21', color: '#F7DC6F' },
    { symbol: '♐', name: 'Sagittarius', element: 'Fire', dates: 'Nov 22 - Dec 21', color: '#BB8FCE' },
    { symbol: '♑', name: 'Capricorn', element: 'Earth', dates: 'Dec 22 - Jan 19', color: '#85C1E9' },
    { symbol: '♒', name: 'Aquarius', element: 'Air', dates: 'Jan 20 - Feb 18', color: '#F8C471' },
    { symbol: '♓', name: 'Pisces', element: 'Water', dates: 'Feb 19 - Mar 20', color: '#82E0AA' }
  ];

  useEffect(() => {
    // Animate signs one by one on mount
    zodiacSigns.forEach((_, index) => {
      setTimeout(() => {
        setAnimatedSigns(prev => new Set([...prev, index]));
      }, index * 100);
    });
  }, []);

  const handleSignClick = (index) => {
    onSignSelect(index);
    
    // Add click animation
    const signElement = document.querySelector(`.zodiac-sign[data-index="${index}"]`);
    if (signElement) {
      signElement.classList.add('clicked');
      setTimeout(() => {
        signElement.classList.remove('clicked');
      }, 300);
    }
  };

  return (
    <div className="horoscope-wheel-container">
      <div className="wheel-center">
        <div className="center-icon">🌟</div>
        <div className="center-text">Select Your Sign</div>
      </div>
      
      <div className="zodiac-wheel">
        {zodiacSigns.map((sign, index) => (
          <div
            key={index}
            data-index={index}
            className={`zodiac-sign ${selectedSign === index ? 'active' : ''} ${
              animatedSigns.has(index) ? 'animated' : ''
            }`}
            style={{
              '--sign-color': sign.color,
              '--delay': `${index * 0.1}s`
            }}
            onClick={() => handleSignClick(index)}
          >
            <div className="sign-symbol">{sign.symbol}</div>
            <div className="sign-info">
              <div className="sign-name">{sign.name}</div>
              <div className="sign-element">{sign.element}</div>
              <div className="sign-dates">{sign.dates}</div>
            </div>
            <div className="sign-glow"></div>
          </div>
        ))}
      </div>
      
      <div className="wheel-decorations">
        <div className="decoration decoration-1">✨</div>
        <div className="decoration decoration-2">🌙</div>
        <div className="decoration decoration-3">⭐</div>
        <div className="decoration decoration-4">🌟</div>
      </div>
    </div>
  );
};

export default HoroscopeWheel;