import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import { API_BASE_URL } from '../../config';
import { generatePageSEO } from '../../config/seo.config';
import './HoroscopePage.css';

const HoroscopePage = () => {
  const location = useLocation();
  
  // Get URL parameters
  const urlParams = new URLSearchParams(location.search);
  const periodParam = urlParams.get('period') || 'daily';
  const signParam = urlParams.get('sign') || 'aries';
  
  const [selectedPeriod, setSelectedPeriod] = useState(periodParam);
  const [selectedZodiac, setSelectedZodiac] = useState(signParam);
  const [horoscopeData, setHoroscopeData] = useState(null);
  const [loading, setLoading] = useState(false);

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

  const periods = [
    { key: 'daily', label: 'Daily', icon: '📅' },
    { key: 'weekly', label: 'Weekly', icon: '📊' },
    { key: 'monthly', label: 'Monthly', icon: '🗓️' },
    { key: 'yearly', label: 'Yearly', icon: '📆' }
  ];

  // Update state when URL parameters change
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const periodParam = urlParams.get('period');
    const signParam = urlParams.get('sign');
    
    if (periodParam && periodParam !== selectedPeriod) {
      setSelectedPeriod(periodParam);
    }
    if (signParam && signParam !== selectedZodiac) {
      setSelectedZodiac(signParam);
    }
  }, [location.search]);

  useEffect(() => {
    fetchHoroscope();
  }, [selectedPeriod, selectedZodiac]);

  const fetchHoroscope = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/horoscope/${selectedPeriod}/${selectedZodiac}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setHoroscopeData(data);
    } catch (error) {
      console.error('Error fetching horoscope:', error);
      setHoroscopeData(null);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentZodiac = () => zodiacSigns.find(z => z.name === selectedZodiac);

  const currentZodiac = getCurrentZodiac();
  const seoData = generatePageSEO('dailyHoroscope', { 
    path: `/horoscope/${selectedPeriod}`,
    title: `${currentZodiac?.displayName} ${selectedPeriod.charAt(0).toUpperCase() + selectedPeriod.slice(1)} Horoscope | AstroRoshni`,
    description: `Read your ${selectedPeriod} ${currentZodiac?.displayName} horoscope predictions for love, career, health and finance. Accurate astrology forecasts updated daily.`
  });

  return (
    <div className="horoscope-page">
      <SEOHead 
        title={seoData.title}
        description={seoData.description}
        keywords={`${currentZodiac?.displayName.toLowerCase()} horoscope, ${selectedPeriod} horoscope, ${currentZodiac?.displayName.toLowerCase()} predictions, astrology forecast`}
        canonical={seoData.canonical}
        structuredData={{
          "@context": "https://schema.org",
          "@type": "Article",
          "headline": seoData.title,
          "description": seoData.description,
          "author": { "@type": "Organization", "name": "AstroRoshni" },
          "publisher": { "@type": "Organization", "name": "AstroRoshni" }
        }}
      />
      <NavigationHeader compact={true} onPeriodChange={setSelectedPeriod} />
      
      <div className="container">
        <div className="horoscope-header">
          <h1>🔮 Detailed Horoscope</h1>
          <p>Comprehensive astrological insights powered by Western tropical astrology</p>
        </div>

        <div className="period-selector">
          {periods.map(period => (
            <button
              key={period.key}
              className={`period-btn ${selectedPeriod === period.key ? 'active' : ''}`}
              onClick={() => setSelectedPeriod(period.key)}
            >
              {period.icon} {period.label}
            </button>
          ))}
        </div>

        <div className="zodiac-selector">
          {zodiacSigns.map(sign => (
            <button
              key={sign.name}
              className={`zodiac-btn ${selectedZodiac === sign.name ? 'active' : ''}`}
              onClick={() => setSelectedZodiac(sign.name)}
              title={sign.displayName}
            >
              <div className="zodiac-symbol">{sign.symbol}</div>
              <div className="zodiac-name">{sign.displayName}</div>
            </button>
          ))}
        </div>

        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading your cosmic insights...</p>
          </div>
        ) : horoscopeData ? (
          <div className="horoscope-content">
            {(horoscopeData.daily_summary || horoscopeData.weekly_summary || horoscopeData.monthly_summary) && (
              <div className="daily-summary-banner">
                <div className="summary-emoji">
                  {horoscopeData.daily_summary?.emoji || horoscopeData.weekly_summary?.emoji || horoscopeData.monthly_summary?.emoji}
                </div>
                <div className="summary-content">
                  <div className="summary-theme">
                    {horoscopeData.daily_summary?.theme || horoscopeData.weekly_summary?.theme || horoscopeData.monthly_summary?.theme}
                  </div>
                  <div className="summary-essence">
                    {horoscopeData.daily_summary?.essence || horoscopeData.weekly_summary?.essence || horoscopeData.monthly_summary?.essence}
                  </div>
                </div>
              </div>
            )}
            
            <div className="horoscope-title">
              <div className="zodiac-info">
                <span className="zodiac-symbol">{getCurrentZodiac()?.symbol}</span>
                <div>
                  <h2>{getCurrentZodiac()?.displayName} {selectedPeriod.charAt(0).toUpperCase() + selectedPeriod.slice(1)} Horoscope</h2>
                  <div className="horoscope-meta">
                    <span>Lucky Number: {horoscopeData.lucky_number}</span>
                    <span>Lucky Color: {horoscopeData.lucky_color}</span>
                    <span>Rating: {'⭐'.repeat(horoscopeData.rating)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="overall-prediction-hero">
              <div className="prediction-header">
                <div className="cosmic-icon">🌟</div>
                <h3>Overall Cosmic Forecast</h3>
                <div className="period-badge">{selectedPeriod.charAt(0).toUpperCase() + selectedPeriod.slice(1)} Outlook</div>
              </div>
              
              <div className="prediction-content">
                <div className="prediction-text">
                  <div className="opening-quote">"</div>
                  <p>{horoscopeData.prediction?.overall}</p>
                  <div className="closing-quote">"</div>
                </div>
                
                <div className="prediction-highlights">
                  {horoscopeData.todays_energy && (
                    <div className="highlight-item">
                      <div className="highlight-icon">🌟</div>
                      <div className="highlight-text">
                        <strong>Today's Energy</strong>
                        <span>{horoscopeData.todays_energy}</span>
                      </div>
                    </div>
                  )}
                  {horoscopeData.best_time && (
                    <div className="highlight-item">
                      <div className="highlight-icon">⏰</div>
                      <div className="highlight-text">
                        <strong>Best Time</strong>
                        <span>{horoscopeData.best_time}</span>
                      </div>
                    </div>
                  )}
                  {horoscopeData.key_focus && (
                    <div className="highlight-item">
                      <div className="highlight-icon">🎯</div>
                      <div className="highlight-text">
                        <strong>Key Focus</strong>
                        <span>{horoscopeData.key_focus}</span>
                      </div>
                    </div>
                  )}
                  {horoscopeData.what_to_avoid && (
                    <div className="highlight-item">
                      <div className="highlight-icon">⚠️</div>
                      <div className="highlight-text">
                        <strong>What to Avoid</strong>
                        <span>{horoscopeData.what_to_avoid}</span>
                      </div>
                    </div>
                  )}
                  {horoscopeData.lucky_element && (
                    <div className="highlight-item">
                      <div className="highlight-icon">🍀</div>
                      <div className="highlight-text">
                        <strong>Lucky Element</strong>
                        <span>{horoscopeData.lucky_element}</span>
                      </div>
                    </div>
                  )}
                  {horoscopeData.moon_timing && (
                    <div className="highlight-item">
                      <div className="highlight-icon">🌙</div>
                      <div className="highlight-text">
                        <strong>Moon Phase</strong>
                        <span>{horoscopeData.moon_timing.phase} - {horoscopeData.moon_timing.phase_meaning}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="cosmic-elements">
                <div className="floating-star star-1">✨</div>
                <div className="floating-star star-2">⭐</div>
                <div className="floating-star star-3">🌟</div>
                <div className="cosmic-wave"></div>
              </div>
            </div>

            {horoscopeData.daily_actions && (
              <div className="daily-actions-section">
                <h3>🎯 Daily Action Plan</h3>
                <div className="actions-grid">
                  <div className="actions-list">
                    <h4>✅ Priority Actions</h4>
                    <ul>
                      {horoscopeData.daily_actions.actions.map((action, index) => (
                        <li key={index}>{action}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="avoid-item">
                    <h4>⚠️ Avoid Today</h4>
                    <p>{horoscopeData.daily_actions.avoid}</p>
                  </div>
                </div>
              </div>
            )}

            {horoscopeData.energy_forecast && (
              <div className="energy-forecast-section">
                <h3>⚡ Energy Forecast</h3>
                <div className="energy-timeline">
                  <div className="energy-period">
                    <div className="period-label">Morning</div>
                    <div className="energy-bar">
                      <div className="energy-fill" style={{width: `${horoscopeData.energy_forecast.morning}%`}}></div>
                    </div>
                    <div className="energy-value">{horoscopeData.energy_forecast.morning}%</div>
                  </div>
                  <div className="energy-period">
                    <div className="period-label">Afternoon</div>
                    <div className="energy-bar">
                      <div className="energy-fill" style={{width: `${horoscopeData.energy_forecast.afternoon}%`}}></div>
                    </div>
                    <div className="energy-value">{horoscopeData.energy_forecast.afternoon}%</div>
                  </div>
                  <div className="energy-period">
                    <div className="period-label">Evening</div>
                    <div className="energy-bar">
                      <div className="energy-fill" style={{width: `${horoscopeData.energy_forecast.evening}%`}}></div>
                    </div>
                    <div className="energy-value">{horoscopeData.energy_forecast.evening}%</div>
                  </div>
                </div>
                <p className="peak-time">Peak Energy: {horoscopeData.energy_forecast.peak_time}</p>
              </div>
            )}

            <div className="predictions-grid">
              <div className="prediction-card">
                <h3>💕 Love & Relationships</h3>
                <p>{horoscopeData.prediction?.love}</p>
              </div>
              <div className="prediction-card">
                <h3>💼 Career & Business</h3>
                <p>{horoscopeData.prediction?.career}</p>
              </div>
              <div className="prediction-card">
                <h3>🏥 Health & Wellness</h3>
                <p>{horoscopeData.prediction?.health}</p>
              </div>
              <div className="prediction-card">
                <h3>💰 Finance & Money</h3>
                <p>{horoscopeData.prediction?.finance}</p>
              </div>
              <div className="prediction-card">
                <h3>📚 Education & Learning</h3>
                <p>{horoscopeData.prediction?.education}</p>
              </div>
              <div className="prediction-card">
                <h3>🕉️ Spirituality & Faith</h3>
                <p>{horoscopeData.prediction?.spirituality}</p>
              </div>
            </div>

            {horoscopeData.intuitive_insights && (
              <div className="intuitive-insights-section">
                <h3>🔮 Intuitive Insights</h3>
                <div className="insights-grid">
                  <div className="insight-card">
                    <h4>🌌 Psychic Sensitivity</h4>
                    <div className="sensitivity-meter">
                      <div className="sensitivity-fill" style={{width: `${horoscopeData.intuitive_insights.psychic_sensitivity}%`}}></div>
                    </div>
                    <span>{horoscopeData.intuitive_insights.psychic_sensitivity}%</span>
                  </div>
                  <div className="insight-card">
                    <h4>✨ Synchronicity Level</h4>
                    <div className="sensitivity-meter">
                      <div className="sensitivity-fill" style={{width: `${horoscopeData.intuitive_insights.synchronicity_level}%`}}></div>
                    </div>
                    <span>{horoscopeData.intuitive_insights.synchronicity_level}%</span>
                  </div>
                  <div className="insight-card">
                    <h4>🌙 Dream Significance</h4>
                    <p>{horoscopeData.intuitive_insights.dream_significance}</p>
                  </div>
                  <div className="insight-card signs-to-watch">
                    <h4>🔍 Signs to Watch</h4>
                    {horoscopeData.intuitive_insights.signs_to_watch && horoscopeData.intuitive_insights.signs_to_watch.signs ? (
                      <div className="signs-guidance">
                        <p className="signs-overview">{horoscopeData.intuitive_insights.signs_to_watch.overview}</p>
                        <div className="signs-list">
                          {horoscopeData.intuitive_insights.signs_to_watch.signs.map((signInfo, index) => (
                            <div key={index} className="sign-watch-item">
                              <div className="sign-header">
                                <strong>{signInfo.sign}</strong>
                                <span className="sign-reason">{signInfo.reason}</span>
                              </div>
                              <div className="sign-details">
                                <div className="what-to-watch">
                                  <strong>Watch for:</strong> {signInfo.what_to_watch}
                                </div>
                                <div className="symbols-info">
                                  <strong>Symbols:</strong> {signInfo.symbols.symbols.join(', ')}
                                </div>
                                <div className="colors-info">
                                  <strong>Colors:</strong> {signInfo.symbols.colors.join(', ')}
                                </div>
                                <div className="how-to-use">
                                  <strong>How to use:</strong> {signInfo.how_to_use}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                        <div className="watch-methods">
                          <h5>How to Watch for These Signs:</h5>
                          <ul>
                            {horoscopeData.intuitive_insights.signs_to_watch.methods.map((method, index) => (
                              <li key={index}>{method}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ) : (
                      <p>{typeof horoscopeData.intuitive_insights.signs_to_watch === 'string' ? horoscopeData.intuitive_insights.signs_to_watch : 'Watch for meaningful synchronicities today'}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {horoscopeData.prediction?.detailed_analysis && (
              <div className="comprehensive-analysis">
                <h3>🔍 Comprehensive 360° Analysis</h3>
                
                {horoscopeData.cosmic_weather && (
                  <div className="cosmic-weather">
                    <h4>🌌 Current Cosmic Weather</h4>
                    <div className="weather-grid">
                      <div className="weather-item">
                        <span className="weather-label">Energy Level</span>
                        <div className="weather-bar">
                          <div className="weather-fill" style={{width: `${horoscopeData.cosmic_weather.energy_level}%`}}></div>
                        </div>
                        <span className="weather-value">{horoscopeData.cosmic_weather.energy_level}%</span>
                      </div>
                      <div className="weather-item">
                        <span className="weather-label">Manifestation Power</span>
                        <div className="weather-bar">
                          <div className="weather-fill" style={{width: `${horoscopeData.cosmic_weather.manifestation_power}%`}}></div>
                        </div>
                        <span className="weather-value">{horoscopeData.cosmic_weather.manifestation_power}%</span>
                      </div>
                      <div className="weather-item">
                        <span className="weather-label">Intuition Strength</span>
                        <div className="weather-bar">
                          <div className="weather-fill" style={{width: `${horoscopeData.cosmic_weather.intuition_strength}%`}}></div>
                        </div>
                        <span className="weather-value">{horoscopeData.cosmic_weather.intuition_strength}%</span>
                      </div>
                      <div className="weather-item">
                        <span className="weather-label">Relationship Harmony</span>
                        <div className="weather-bar">
                          <div className="weather-fill" style={{width: `${horoscopeData.cosmic_weather.relationship_harmony}%`}}></div>
                        </div>
                        <span className="weather-value">{horoscopeData.cosmic_weather.relationship_harmony}%</span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="analysis-section">
                  <h4>🪐 Planetary Influences & Aspects</h4>
                  <div className="planetary-influences">
                    {horoscopeData.prediction.detailed_analysis.planetary_influences?.map((planet, index) => (
                      <div key={index} className="planet-influence-detailed">
                        <div className="planet-header">
                          <strong>{planet.planet}</strong>
                          <span className="strength">{planet.strength}%</span>
                        </div>
                        <p className="influence-desc">{planet.influence}</p>
                        {planetary_signs && planetary_signs[planet.planet] ? <p className="sign-info"><strong>Sign:</strong> {planetary_signs[planet.planet].sign} | <strong>Aspect:</strong> {planet.aspect}</p> : planet.sign && <p className="sign-info"><strong>Sign:</strong> {planet.sign} | <strong>Aspect:</strong> {planet.aspect}</p>}
                        {planet.orb && <p className="orb-info"><strong>Orb:</strong> {planet.orb}</p>}
                        {planet.effect && <p className="effect-info"><strong>Effect:</strong> {planet.effect}</p>}
                        <div className="strength-bar">
                          <div className="strength-fill" style={{width: `${planet.strength}%`}}></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {(horoscopeData.prediction.detailed_analysis.challenges || horoscopeData.prediction.detailed_analysis.opportunities) && (
                  <div className="challenges-opportunities">
                    {horoscopeData.prediction.detailed_analysis.challenges && (
                      <div className="analysis-section">
                        <h4>⚠️ Challenges to Navigate</h4>
                        <ul>
                          {horoscopeData.prediction.detailed_analysis.challenges.map((challenge, index) => (
                            <li key={index}>{challenge}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {horoscopeData.prediction.detailed_analysis.opportunities && (
                      <div className="analysis-section">
                        <h4>🌟 Golden Opportunities</h4>
                        <ul>
                          {horoscopeData.prediction.detailed_analysis.opportunities.map((opportunity, index) => (
                            <li key={index}>{opportunity}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {horoscopeData.action_plan && (
              <div className="action-items">
                <h3>📋 Personalized Action Plan</h3>
                <div className="actions-grid">
                  <div className="action-card priority-high">
                    <h4>🎯 Primary Focus Areas</h4>
                    <p>{horoscopeData.action_plan.primary_focus}</p>
                  </div>
                  <div className="action-card priority-medium">
                    <h4>⏰ Optimal Timing</h4>
                    <p>{horoscopeData.action_plan.optimal_timing}</p>
                  </div>
                  <div className="action-card priority-high">
                    <h4>🔮 Daily Practices</h4>
                    <p>{horoscopeData.action_plan.daily_practices}</p>
                  </div>
                  <div className="action-card priority-medium">
                    <h4>🌱 Growth Opportunities</h4>
                    <p>{horoscopeData.action_plan.growth_opportunities}</p>
                  </div>
                  <div className="action-card priority-low">
                    <h4>⚖️ Balance Strategies</h4>
                    <p>{horoscopeData.action_plan.balance_strategies}</p>
                  </div>
                  <div className="action-card priority-high">
                    <h4>💫 Manifestation Techniques</h4>
                    <p>{horoscopeData.action_plan.manifestation_techniques}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="error-message">
            <h3>Unable to load horoscope data</h3>
            <p>Please check your connection and try again.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default HoroscopePage;