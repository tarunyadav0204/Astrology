import React from 'react';
import { 
  getPlanetDignity, houseLords, getFriendship, getNakshatraLord
} from '../../utils/planetAnalyzer';

const SpousePersonalityAnalysis = ({ chartData, getDarakarka, getConjunctions }) => {
  const personalityTraits = [];
  const behaviorPatterns = [];
  const physicalTraits = [];
  
  // Define personality traits for each planet
  const darakarkaTraits = {
    'Sun': {
      personality: ['Authoritative', 'Confident', 'Leadership qualities', 'Dignified', 'Proud'],
      behavior: ['Takes charge in relationships', 'Expects respect', 'Generous but demanding', 'Strong-willed'],
      physical: ['Strong build', 'Commanding presence', 'Bright eyes', 'Regal appearance']
    },
    'Moon': {
      personality: ['Emotional', 'Caring', 'Intuitive', 'Moody', 'Nurturing'],
      behavior: ['Emotionally expressive', 'Needs security', 'Changeable moods', 'Protective'],
      physical: ['Round face', 'Soft features', 'Fair complexion', 'Gentle appearance']
    },
    'Mars': {
      personality: ['Energetic', 'Aggressive', 'Competitive', 'Courageous', 'Impulsive'],
      behavior: ['Quick to anger', 'Protective of family', 'Athletic interests', 'Direct communication'],
      physical: ['Athletic build', 'Sharp features', 'Reddish complexion', 'Strong physique']
    },
    'Mercury': {
      personality: ['Intelligent', 'Communicative', 'Witty', 'Adaptable', 'Curious'],
      behavior: ['Loves conversation', 'Quick thinking', 'Restless nature', 'Analytical approach'],
      physical: ['Youthful appearance', 'Expressive eyes', 'Medium height', 'Quick movements']
    },
    'Jupiter': {
      personality: ['Wise', 'Spiritual', 'Optimistic', 'Generous', 'Philosophical'],
      behavior: ['Gives good advice', 'Religious inclinations', 'Ethical conduct', 'Teaching nature'],
      physical: ['Well-built', 'Pleasant features', 'Yellowish complexion', 'Dignified posture']
    },
    'Venus': {
      personality: ['Charming', 'Artistic', 'Romantic', 'Luxury-loving', 'Diplomatic'],
      behavior: ['Affectionate nature', 'Appreciates beauty', 'Social butterfly', 'Harmonious approach'],
      physical: ['Beautiful/handsome', 'Attractive features', 'Fair complexion', 'Graceful movements']
    },
    'Saturn': {
      personality: ['Serious', 'Disciplined', 'Hardworking', 'Traditional', 'Patient'],
      behavior: ['Slow but steady', 'Responsible nature', 'Conservative approach', 'Long-term thinking'],
      physical: ['Lean build', 'Dark complexion', 'Prominent bones', 'Mature appearance']
    }
  };
  
  // Darakarka Analysis (Most Important)
  const darakarka = getDarakarka();
  const darakarkaData = chartData?.planets?.[darakarka];
  
  if (darakarka && darakarkaData) {
    const darakarkaDignity = getPlanetDignity(darakarka, darakarkaData.sign);
    
    if (darakarkaTraits[darakarka]) {
      personalityTraits.push({
        source: `Darakarka ${darakarka}`,
        traits: darakarkaTraits[darakarka].personality,
        strength: 'Primary'
      });
      behaviorPatterns.push({
        source: `Darakarka ${darakarka}`,
        patterns: darakarkaTraits[darakarka].behavior,
        strength: 'Primary'
      });
      physicalTraits.push({
        source: `Darakarka ${darakarka}`,
        traits: darakarkaTraits[darakarka].physical,
        strength: 'Primary'
      });
      
      // Modify based on dignity
      if (darakarkaDignity === 'Exalted') {
        personalityTraits[personalityTraits.length - 1].traits.push('Highly refined', 'Noble character');
      } else if (darakarkaDignity === 'Debilitated') {
        personalityTraits[personalityTraits.length - 1].traits.push('Challenges in core nature', 'Needs support');
      }
    }
  }
  
  // 7th House Lord Analysis
  const seventhHouseSign = chartData?.houses?.[6]?.sign || 0;
  const seventhHouseLord = houseLords[seventhHouseSign];
  const seventhLordData = chartData?.planets?.[seventhHouseLord];
  
  if (seventhLordData) {
    const seventhLordHouse = chartData?.houses?.findIndex(house => house.sign === seventhLordData.sign) + 1;
    
    const houseInfluences = {
      1: ['Self-centered', 'Independent', 'Strong personality'],
      2: ['Family-oriented', 'Wealth-conscious', 'Traditional values'],
      3: ['Communicative', 'Sibling-focused', 'Adventurous'],
      4: ['Home-loving', 'Emotional', 'Mother-attached'],
      5: ['Creative', 'Child-loving', 'Romantic'],
      6: ['Service-minded', 'Health-conscious', 'Competitive'],
      8: ['Mysterious', 'Research-oriented', 'Transformative'],
      9: ['Spiritual', 'Philosophical', 'Lucky'],
      10: ['Career-focused', 'Ambitious', 'Status-conscious'],
      11: ['Social', 'Friend-oriented', 'Gain-focused'],
      12: ['Spiritual', 'Foreign connections', 'Sacrificing']
    };
    
    if (houseInfluences[seventhLordHouse]) {
      personalityTraits.push({
        source: `7th Lord in ${seventhLordHouse}th House`,
        traits: houseInfluences[seventhLordHouse],
        strength: 'Strong'
      });
    }
  }
  
  // Planets in 7th House Analysis
  const planetsIn7th = Object.entries(chartData?.planets || {}).filter(
    ([name, data]) => data.sign === seventhHouseSign
  ).map(([name]) => name);
  
  if (planetsIn7th.length > 0) {
    planetsIn7th.forEach(planet => {
      if (darakarkaTraits[planet]) {
        personalityTraits.push({
          source: `${planet} in 7th House`,
          traits: darakarkaTraits[planet].personality.slice(0, 3),
          strength: 'Moderate'
        });
      }
    });
  }
  
  // Venus Analysis for Romance Style
  const venusData = chartData?.planets?.['Venus'];
  if (venusData) {
    const venusHouse = chartData?.houses?.findIndex(house => house.sign === venusData.sign) + 1;
    
    const romanticStyles = {
      1: 'Direct and passionate in love',
      2: 'Traditional and stable in romance',
      3: 'Communicative and playful lover',
      4: 'Emotionally nurturing partner',
      5: 'Highly romantic and creative',
      6: 'Practical approach to love',
      7: 'Balanced and harmonious partner',
      8: 'Intense and transformative love',
      9: 'Philosophical and spiritual romance',
      10: 'Status-conscious in relationships',
      11: 'Social and friendly romantic style',
      12: 'Sacrificing and spiritual love'
    };
    
    behaviorPatterns.push({
      source: `Venus in ${venusHouse}th House`,
      patterns: [romanticStyles[venusHouse] || 'Balanced romantic approach'],
      strength: 'Moderate'
    });
  }
  
  return (
    <div className="analysis-section">
      <h3>👤 Spouse Personality & Behavior</h3>
      <div className="spouse-personality-result">
        <div className="personality-summary">
          <h4>🎯 Core Personality Profile</h4>
          <div className="darakarka-highlight">
            <div className="darakarka-info">
              <span className="darakarka-planet">{darakarka}</span>
              <span className="darakarka-label">Darakarka (Spouse Significator)</span>
            </div>
            <p>Your spouse's core personality will be primarily influenced by {darakarka} energy, making them {darakarkaTraits[darakarka]?.personality.slice(0, 3).join(', ').toLowerCase() || 'balanced and harmonious'}.</p>
          </div>
        </div>
        
        <div className="personality-details">
          <div className="personality-section">
            <h4>🧠 Personality Traits</h4>
            <div className="traits-grid">
              {personalityTraits.map((trait, index) => (
                <div key={index} className={`trait-card ${trait.strength.toLowerCase()}`}>
                  <div className="trait-header">
                    <span className="trait-source">{trait.source}</span>
                    <span className={`trait-strength ${trait.strength.toLowerCase()}`}>{trait.strength}</span>
                  </div>
                  <div className="trait-list">
                    {trait.traits.map((t, i) => (
                      <span key={i} className="trait-tag">{t}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="personality-section">
            <h4>💫 Behavior Patterns</h4>
            <div className="behavior-grid">
              {behaviorPatterns.map((behavior, index) => (
                <div key={index} className={`behavior-card ${behavior.strength.toLowerCase()}`}>
                  <div className="behavior-header">
                    <span className="behavior-source">{behavior.source}</span>
                    <span className={`behavior-strength ${behavior.strength.toLowerCase()}`}>{behavior.strength}</span>
                  </div>
                  <div className="behavior-list">
                    {behavior.patterns.map((pattern, i) => (
                      <div key={i} className="behavior-item">{pattern}</div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="personality-section">
            <h4>👁️ Physical Appearance</h4>
            <div className="physical-grid">
              {physicalTraits.map((physical, index) => (
                <div key={index} className={`physical-card ${physical.strength.toLowerCase()}`}>
                  <div className="physical-header">
                    <span className="physical-source">{physical.source}</span>
                    <span className={`physical-strength ${physical.strength.toLowerCase()}`}>{physical.strength}</span>
                  </div>
                  <div className="physical-list">
                    {physical.traits.map((trait, i) => (
                      <span key={i} className="physical-tag">{trait}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="compatibility-insights">
          <h4>💡 Relationship Insights</h4>
          <div className="insights-grid">
            <div className="insight-item">
              <span className="insight-icon">🤝</span>
              <div className="insight-content">
                <h5>Communication Style</h5>
                <p>{darakarka === 'Mercury' ? 'Your spouse will be highly communicative and intellectual. Expect lots of meaningful conversations.' : 
                   darakarka === 'Mars' ? 'Your spouse will be direct and straightforward. They prefer honest, clear communication.' :
                   darakarka === 'Venus' ? 'Your spouse will be diplomatic and charming. They prefer harmonious, gentle communication.' :
                   'Your spouse will have a balanced communication style adapted to situations.'}</p>
              </div>
            </div>
            <div className="insight-item">
              <span className="insight-icon">❤️</span>
              <div className="insight-content">
                <h5>Love Expression</h5>
                <p>{darakarka === 'Venus' ? 'Highly romantic with grand gestures, gifts, and artistic expressions of love.' :
                   darakarka === 'Moon' ? 'Emotionally expressive, caring through nurturing and creating emotional security.' :
                   darakarka === 'Mars' ? 'Passionate and protective, shows love through actions and physical affection.' :
                   darakarka === 'Jupiter' ? 'Shows love through wisdom, guidance, and spiritual connection.' :
                   'Balanced approach to expressing love and affection.'}</p>
              </div>
            </div>
            <div className="insight-item">
              <span className="insight-icon">⚖️</span>
              <div className="insight-content">
                <h5>Conflict Resolution</h5>
                <p>{darakarka === 'Venus' ? 'Prefers harmony and compromise, avoids confrontation, seeks peaceful solutions.' :
                   darakarka === 'Mars' ? 'Direct confrontation, quick to anger but also quick to forgive and move on.' :
                   darakarka === 'Saturn' ? 'Slow to anger but holds grudges, prefers structured solutions and clear boundaries.' :
                   darakarka === 'Jupiter' ? 'Wise and fair approach, seeks understanding and moral solutions.' :
                   'Balanced approach to resolving conflicts and disagreements.'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpousePersonalityAnalysis;