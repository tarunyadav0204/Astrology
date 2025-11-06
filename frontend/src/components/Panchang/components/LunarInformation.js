import React from 'react';
import { MOON_PHASES, PAKSHA_TYPES, SIGN_NAMES } from '../config/panchangConfig';

const LunarInformation = ({ lunarData, panchangData }) => {
  if (!lunarData || !panchangData) {
    throw new Error('Lunar data and Panchang data are required');
  }

  const getMoonPhaseIcon = (phase) => {
    const phaseIcons = {
      [MOON_PHASES.NEW_MOON]: '🌑',
      [MOON_PHASES.WAXING_CRESCENT]: '🌒',
      [MOON_PHASES.FIRST_QUARTER]: '🌓',
      [MOON_PHASES.WAXING_GIBBOUS]: '🌔',
      [MOON_PHASES.FULL_MOON]: '🌕',
      [MOON_PHASES.WANING_GIBBOUS]: '🌖',
      [MOON_PHASES.LAST_QUARTER]: '🌗',
      [MOON_PHASES.WANING_CRESCENT]: '🌘'
    };
    return phaseIcons[phase];
  };

  const calculateMoonStrength = (illumination, sign, nakshatra) => {
    let strength = 0;
    
    // Base strength from illumination
    strength += illumination * 0.4;
    
    // Strength from sign (Moon is exalted in Taurus, debilitated in Scorpio)
    if (sign === 1) strength += 30; // Taurus
    else if (sign === 7) strength -= 20; // Scorpio
    else if ([3, 6, 9].includes(sign)) strength += 10; // Own signs and friendly
    
    // Strength from nakshatra
    if (['Rohini', 'Hasta', 'Shravana'].includes(nakshatra)) strength += 15;
    
    return Math.max(0, Math.min(100, strength));
  };

  const getPakshaType = (tithiNumber) => {
    return tithiNumber <= 15 ? PAKSHA_TYPES.SHUKLA : PAKSHA_TYPES.KRISHNA;
  };

  const moonStrength = calculateMoonStrength(
    lunarData.illumination_percentage,
    lunarData.moon_sign,
    panchangData.nakshatra.name
  );

  return (
    <div className="lunar-information">

      <div className="timing-section">
        <h4>Moon Phase</h4>
        <div className="timing-list">
          <div className="timing-item">
            <span className="timing-name">{getMoonPhaseIcon(lunarData.phase_name)} {lunarData.phase_name}</span>
            <span className="timing-duration">Illumination: {lunarData.illumination_percentage}%</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Moon Age</span>
            <span className="timing-duration">{lunarData.moon_age} days</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Distance</span>
            <span className="timing-duration">{lunarData.distance_km.toLocaleString()} km</span>
          </div>
        </div>
      </div>

      <div className="timing-section">
        <h4>Moon Sign</h4>
        <div className="timing-list">
          <div className="timing-item">
            <span className="timing-name">{lunarData.sign_symbol} {SIGN_NAMES[lunarData.moon_sign]}</span>
            <span className="timing-duration">Degree: {lunarData.moon_degree.toFixed(2)}°</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Sign Lord</span>
            <span className="timing-duration">{lunarData.sign_lord}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Element</span>
            <span className="timing-duration">{lunarData.element}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Quality</span>
            <span className="timing-duration">{lunarData.quality}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Characteristics</span>
            <span className="timing-description">{lunarData.moon_sign_characteristics}</span>
          </div>
        </div>
      </div>

      <div className="timing-section">
        <h4>Lunar Month</h4>
        <div className="timing-list">
          <div className="timing-item">
            <span className="timing-name">{getPakshaType(panchangData.tithi.number) === PAKSHA_TYPES.SHUKLA ? '🌒' : '🌘'} {getPakshaType(panchangData.tithi.number)}</span>
            <span className="timing-duration">Day {((panchangData.tithi.number - 1) % 15) + 1} of 15</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Month</span>
            <span className="timing-duration">{lunarData.lunar_month_name}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Significance</span>
            <span className="timing-description">{lunarData.paksha_significance}</span>
          </div>
        </div>
      </div>

      <div className="timing-section">
        <h4>Chandra Bala</h4>
        <div className="timing-list">
          <div className="timing-item">
            <span className="timing-name">💪 {moonStrength.toFixed(0)}/100</span>
            <span className="timing-duration">{moonStrength >= 70 ? 'Strong' : moonStrength >= 40 ? 'Medium' : 'Weak'}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Illumination</span>
            <span className="timing-duration">{lunarData.illumination_percentage}%</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Sign Position</span>
            <span className="timing-duration">{lunarData.sign_strength}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Nakshatra</span>
            <span className="timing-duration">{lunarData.nakshatra_strength}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Effects</span>
            <span className="timing-description">{lunarData.strength_effects}</span>
          </div>
        </div>
      </div>

      <div className="timing-section">
        <h4>Moon's Nakshatra</h4>
        <div className="timing-list">
          <div className="timing-item">
            <span className="timing-name">⭐ {panchangData.nakshatra.name}</span>
            <span className="timing-duration">Pada: {panchangData.nakshatra.pada}/4</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Lord</span>
            <span className="timing-duration">{panchangData.nakshatra.lord}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Deity</span>
            <span className="timing-duration">{panchangData.nakshatra.deity}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Symbol</span>
            <span className="timing-duration">{panchangData.nakshatra.symbol}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Guna</span>
            <span className="timing-duration">{panchangData.nakshatra.guna}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Nature</span>
            <span className="timing-duration">{panchangData.nakshatra.nature}</span>
          </div>
          <div className="timing-item">
            <span className="timing-name">Compatible Nakshatras</span>
            <span className="timing-description">{panchangData.nakshatra.compatible_nakshatras ? panchangData.nakshatra.compatible_nakshatras.join(', ') : 'N/A'}</span>
          </div>
        </div>
      </div>

      <div className="timing-section">
        <h4>Lunar Yogas</h4>
        <div className="timing-list">
          {lunarData.lunar_yogas && lunarData.lunar_yogas.map((yoga, index) => (
            <div key={index} className="timing-item">
              <span className="timing-name">🧘 {yoga.name}</span>
              <span className="timing-description">{yoga.description} - {yoga.effect}</span>
            </div>
          ))}
          
          {(!lunarData.lunar_yogas || lunarData.lunar_yogas.length === 0) && (
            <div className="timing-item">
              <span className="timing-name">🧘 No special lunar yogas today</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LunarInformation;