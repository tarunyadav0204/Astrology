import React, { useMemo } from 'react';
import './LoShuGrid.css';

const LoShuGrid = ({ numerologyData }) => {
  // Defensive check for data
  if (!numerologyData || !numerologyData.numerology_chart) return null;

  const { lo_shu_grid, core_numbers } = numerologyData.numerology_chart;
  const { grid_counts, arrows_of_strength, missing_numbers } = lo_shu_grid;

  // The Standard Lo Shu Layout (Don't change this)
  // 4 9 2
  // 3 5 7
  // 8 1 6
  const cells = [
    { num: 4, label: "Wealth" }, { num: 9, label: "Fame" }, { num: 2, label: "Marriage" },
    { num: 3, label: "Health" }, { num: 5, label: "Balance" }, { num: 7, label: "Children" },
    { num: 8, label: "Knowledge" }, { num: 1, label: "Career" }, { num: 6, label: "Help" }
  ];

  // Helper to check if arrow exists - check if all numbers are present in grid
  const hasArrow = (nums) => {
    return nums.every(num => grid_counts[num] > 0);
  };

  // Get meaningful explanations for core numbers
  const getLifePathMeaning = (num) => {
    const meanings = {
      1: "Natural leader, independent, pioneering spirit",
      2: "Cooperative, diplomatic, works well with others", 
      3: "Creative, expressive, artistic talents",
      4: "Practical, organized, builds solid foundations",
      5: "Adventurous, freedom-loving, seeks variety",
      6: "Nurturing, responsible, family-oriented",
      7: "Spiritual seeker, analytical, introspective",
      8: "Ambitious, business-minded, material success",
      9: "Humanitarian, generous, serves others"
    };
    return meanings[num] || "Your unique life journey";
  };

  const getExpressionMeaning = (num) => {
    const meanings = {
      1: "Leadership abilities, innovation, starting new projects",
      2: "Teamwork, mediation, bringing people together",
      3: "Communication, creativity, entertaining others", 
      4: "Organization, hard work, building lasting things",
      5: "Sales, travel, promoting ideas and freedom",
      6: "Teaching, healing, caring for family and community",
      7: "Research, analysis, spiritual or technical expertise",
      8: "Business management, financial success, authority",
      9: "Counseling, charity work, inspiring others"
    };
    return meanings[num] || "Your natural talents";
  };

  const getSoulUrgeMeaning = (num) => {
    const meanings = {
      1: "Desires independence, recognition, to be first",
      2: "Seeks harmony, partnership, peaceful relationships",
      3: "Wants creative expression, joy, social connection",
      4: "Craves security, order, practical achievements", 
      5: "Yearns for freedom, adventure, new experiences",
      6: "Needs to nurture, create beautiful home, help others",
      7: "Seeks truth, wisdom, spiritual understanding",
      8: "Desires material success, power, recognition",
      9: "Wants to serve humanity, make the world better"
    };
    return meanings[num] || "Your inner desires";
  };

  // Get meaningful explanations for arrow patterns
  const getPatternMeaning = (name) => {
    const patterns = {
      "Mental Plane": "Strong thinking & planning abilities",
      "Emotional Plane": "Good emotional balance & relationships", 
      "Physical Plane": "Practical skills & material success",
      "Spiritual Plane": "Intuitive & spiritual awareness",
      "Arrow of Determination": "Strong willpower & persistence",
      "Arrow of Activity": "High energy & action-oriented",
      "Arrow of Intellect": "Sharp mind & analytical thinking",
      "Arrow of Sensitivity": "Empathetic & emotionally aware",
      "Arrow of Skepticism": "Questioning nature & critical thinking"
    };
    return patterns[name] || name;
  };

  return (
    <div className="loshu-container-compact">
      
      {/* Top Section: Core Numbers + Grid */}
      <div className="blueprint-top-section">
        
        {/* Left: Core Numbers */}
        <div className="core-numbers-panel">
          <h3 className="panel-title">🌟 Core Numbers</h3>
          <div className="core-number-item">
            <span className="number-badge life-path">{core_numbers?.life_path?.life_path_number || '?'}</span>
            <div className="number-info">
              <strong>Life Path</strong>
              <small>{getLifePathMeaning(core_numbers?.life_path?.life_path_number)}</small>
              <details className="number-details">
                <summary>💡 What does this mean?</summary>
                <div className="detailed-meaning">
                  <p><strong>Life Path {core_numbers?.life_path?.life_path_number}</strong> - Your life's main journey and lessons</p>
                  
                  <p><strong>What it means:</strong> {core_numbers?.life_path?.life_path_number === 6 ? "You're here to nurture, heal, and create harmony" : "Your unique life purpose"}</p>
                  
                  <p><strong>Career direction:</strong> {core_numbers?.life_path?.life_path_number === 6 ? "Teaching, healthcare, counseling, family business" : "Aligned with your life path energy"}</p>
                  
                  <p><strong>Life theme:</strong> {core_numbers?.life_path?.life_path_number === 6 ? "Service to others, responsibility, creating stable homes/communities" : "Following your natural path"}</p>
                </div>
              </details>
            </div>
          </div>
          <div className="core-number-item">
            <span className="number-badge expression">{core_numbers?.expression?.number || '?'}</span>
            <div className="number-info">
              <strong>Expression</strong>
              <small>{getExpressionMeaning(core_numbers?.expression?.number)}</small>
              <details className="number-details">
                <summary>💡 What does this mean?</summary>
                <div className="detailed-meaning">
                  <p><strong>Expression {core_numbers?.expression?.number}</strong> - Your natural talents and how you approach tasks</p>
                  
                  <p><strong>What it means:</strong> {core_numbers?.expression?.number === 4 ? "You're naturally organized, practical, and hardworking" : "Your natural approach to life"}</p>
                  
                  <p><strong>Strengths:</strong> {core_numbers?.expression?.number === 4 ? "Building systems, managing details, creating lasting results" : "Your key talents"}</p>
                  
                  <p><strong>Work style:</strong> {core_numbers?.expression?.number === 4 ? "Methodical, reliable, prefers structure over chaos" : "Your natural work approach"}</p>
                </div>
              </details>
            </div>
          </div>
          <div className="core-number-item">
            <span className="number-badge soul">{core_numbers?.soul_urge?.number || '?'}</span>
            <div className="number-info">
              <strong>Soul Urge</strong>
              <small>{getSoulUrgeMeaning(core_numbers?.soul_urge?.number)}</small>
              <details className="number-details">
                <summary>💡 What does this mean?</summary>
                <div className="detailed-meaning">
                  <p><strong>Soul Urge {core_numbers?.soul_urge?.number}</strong> - Your inner desires and what motivates you</p>
                  
                  <p><strong>What it means:</strong> {core_numbers?.soul_urge?.number === 9 ? "Deep down, you want to make the world better" : "Your deepest motivations"}</p>
                  
                  <p><strong>Motivation:</strong> {core_numbers?.soul_urge?.number === 9 ? "Helping humanity, leaving a positive legacy" : "What drives you"}</p>
                  
                  <p><strong>Fulfillment:</strong> {core_numbers?.soul_urge?.number === 9 ? "Comes from serving causes bigger than yourself" : "What satisfies your soul"}</p>
                </div>
              </details>
            </div>
          </div>
          
          <details className="combination-analysis">
            <summary className="combination-summary">🎯 How do they work together?</summary>
            <div className="combination-content">
              <p><strong>How they work together:</strong></p>
              
              <p>• Your Life Path {core_numbers?.life_path?.life_path_number} gives you the nurturing nature</p>
              
              <p>• Your Expression {core_numbers?.expression?.number} gives you the practical skills to build lasting help</p>
              
              <p>• Your Soul Urge {core_numbers?.soul_urge?.number} drives you toward humanitarian causes</p>
              
              <p><strong>Practical application:</strong> You'd thrive in careers that combine helping people ({core_numbers?.life_path?.life_path_number}) with systematic approaches ({core_numbers?.expression?.number}) for humanitarian impact ({core_numbers?.soul_urge?.number}) - like running a nonprofit, healthcare administration, or educational program development.</p>
              
              <p>This combination makes you a "practical humanitarian" - someone who doesn't just care, but actually builds systems that help people effectively.</p>
            </div>
          </details>
        </div>

        {/* Right: Lo Shu Grid */}
        <div className="loshu-grid-panel">
          <h3 className="panel-title">🔮 Lo Shu Grid</h3>
          <p className="grid-explanation">Your birth date numbers mapped to life areas. Filled circles show your strengths, empty ones show growth opportunities.</p>
          <div className="loshu-card-compact">
            {/* SVG Layer for Drawing Arrows */}
            <svg className="arrows-overlay" viewBox="0 0 100 100" preserveAspectRatio="none">
              {arrows_of_strength.map((arrow, i) => {
                let path = "";
                const color = "#FFD700";

                if (hasArrow([4, 9, 2])) path = "M 5 16.6 L 85 16.6 M 85 16.6 L 80 12 M 85 16.6 L 80 21";
                if (hasArrow([3, 5, 7])) path = "M 5 50 L 85 50 M 85 50 L 80 45 M 85 50 L 80 55";
                if (hasArrow([8, 1, 6])) path = "M 5 83.3 L 85 83.3 M 85 83.3 L 80 78.3 M 85 83.3 L 80 88.3";
                if (hasArrow([4, 5, 6])) path = "M 16.6 5 L 83.3 85 M 83.3 85 L 78 80 M 83.3 85 L 88 80";
                if (hasArrow([8, 5, 2])) path = "M 16.6 95 L 83.3 15 M 83.3 15 L 78 20 M 83.3 15 L 88 20";
                if (hasArrow([4, 3, 8])) path = "M 16.6 5 L 16.6 85 M 16.6 85 L 12 80 M 16.6 85 L 21 80";
                if (hasArrow([9, 5, 1])) path = "M 50 5 L 50 85 M 50 85 L 45 80 M 50 85 L 55 80";
                if (hasArrow([2, 7, 6])) path = "M 83.3 5 L 83.3 85 M 83.3 85 L 78.3 80 M 83.3 85 L 88.3 80";

                return path ? (
                  <path 
                    key={i} 
                    d={path} 
                    stroke={color} 
                    strokeWidth="3" 
                    strokeLinecap="round"
                    className="arrow-path"
                  />
                ) : null;
              })}
            </svg>

            {/* The Grid Cells */}
            <div className="grid-layout-compact">
              {cells.map((cell) => {
                const count = grid_counts[cell.num] || 0;
                const isActive = count > 0;

                return (
                  <div key={cell.num} className={`grid-cell-compact ${isActive ? 'active' : 'inactive'}`}>
                    <span className={`cell-number ${!isActive ? 'missing' : ''}`}>
                      {cell.num}
                    </span>
                    {count > 1 && (
                      <div className="count-badge">{count}</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          
          <details className="grid-analysis">
            <summary>💡 What does your grid reveal?</summary>
            <div className="grid-analysis-content">
              <p><strong>Your Strengths:</strong></p>
              {Object.entries(grid_counts).filter(([num, count]) => count > 0).map(([num, count]) => {
                const cell = cells.find(c => c.num == num);
                return (
                  <p key={num}>• <strong>{cell?.label} ({num}):</strong> {count > 1 ? `Extra strong - you have ${count} of these numbers. ` : 'Natural strength. '}
                  {num == 1 ? 'Leadership in career, independent thinking' : 
                   num == 2 ? 'Harmonious relationships, diplomatic in marriage' :
                   num == 3 ? 'Good health habits, vitality and energy' :
                   num == 4 ? 'Financial planning skills, wealth building ability' :
                   num == 5 ? 'Balanced approach to life, adaptability' :
                   num == 6 ? 'Helpful nature, people seek your support' :
                   num == 7 ? 'Good with children, creative expression' :
                   num == 8 ? 'Learning ability, knowledge accumulation' :
                   num == 9 ? 'Recognition potential, leadership qualities' : 'Personal strength'}
                  </p>
                );
              })}
              
              {missing_numbers && missing_numbers.length > 0 && (
                <>
                  <p><strong>Growth Areas:</strong></p>
                  {missing_numbers.slice(0, 3).map(missing => {
                    const cell = cells.find(c => c.num == missing.number);
                    return (
                      <p key={missing.number}>⚠️ <strong>{cell?.label} ({missing.number}):</strong> {missing.lesson || 
                        (missing.number == 1 ? 'Develop leadership skills, take more initiative in career' :
                         missing.number == 2 ? 'Work on partnerships, improve relationship harmony' :
                         missing.number == 3 ? 'Focus on health, build vitality and energy' :
                         missing.number == 4 ? 'Develop financial planning, build wealth systematically' :
                         missing.number == 5 ? 'Seek more balance, embrace change and flexibility' :
                         missing.number == 6 ? 'Learn to help others, develop supportive nature' :
                         missing.number == 7 ? 'Connect with children, express creativity' :
                         missing.number == 8 ? 'Pursue learning, accumulate knowledge and skills' :
                         missing.number == 9 ? 'Build reputation, develop recognition and fame' : 'Area for development')}
                      </p>
                    );
                  })}
                </>
              )}
              
              {arrows_of_strength.filter(arrow => arrow.type === 'Strength').length > 0 && (
                <>
                  <p><strong>Your Special Powers:</strong></p>
                  {arrows_of_strength.filter(arrow => arrow.type === 'Strength').slice(0, 2).map((arrow, i) => (
                    <p key={i}>✨ <strong>{arrow.name}:</strong> {arrow.description || getPatternMeaning(arrow.name)}</p>
                  ))}
                </>
              )}
            </div>
          </details>
        </div>
      </div>

      {/* Bottom Section: Strengths & Lessons */}
      <div className="blueprint-bottom-section">
        
        {/* Left: Arrows of Strength */}
        <div className="strengths-panel">
          <h4 className="section-title">✨ Your Patterns</h4>
          <div className="patterns-list">
            {arrows_of_strength.length > 0 ? (
              arrows_of_strength.filter(arrow => arrow.type === 'Strength').slice(0, 2).map((arrow, i) => (
                <div key={i} className="pattern-item">
                  <div className="pattern-name">{arrow.name}</div>
                  <details className="pattern-details">
                    <summary>💡 What does this mean?</summary>
                    <div className="pattern-explanation">
                      <p><strong>{arrow.name}:</strong> {getPatternMeaning(arrow.name)}</p>
                      
                      <p><strong>What it means:</strong> {
                        arrow.name === 'Mental Plane' ? 'You have strong analytical thinking and planning abilities' :
                        arrow.name === 'Emotional Plane' ? 'You have good emotional balance and relationship skills' :
                        arrow.name === 'Physical Plane' ? 'You have practical skills and material success abilities' :
                        arrow.name === 'Arrow of Determination' ? 'You have strong willpower and persistence' :
                        arrow.name === 'Arrow of Activity' ? 'You have high energy and are action-oriented' :
                        arrow.name === 'Arrow of Intellect' ? 'You have sharp mind and analytical thinking' :
                        'You have this special strength pattern'
                      }</p>
                      
                      <p><strong>How to use this:</strong> {
                        arrow.name === 'Mental Plane' ? 'Excel in roles requiring analysis, planning, strategy. Trust your logical thinking in decisions.' :
                        arrow.name === 'Emotional Plane' ? 'Use your emotional intelligence in relationships, counseling, team leadership.' :
                        arrow.name === 'Physical Plane' ? 'Focus on practical achievements, building wealth, material success.' :
                        arrow.name === 'Arrow of Determination' ? 'Take on challenging projects that require persistence and willpower.' :
                        arrow.name === 'Arrow of Activity' ? 'Thrive in dynamic environments, lead action-oriented projects.' :
                        arrow.name === 'Arrow of Intellect' ? 'Pursue intellectual challenges, research, complex problem-solving.' :
                        'Leverage this natural strength in your career and personal life'
                      }</p>
                      
                      <p><strong>Career advantage:</strong> {
                        arrow.name === 'Mental Plane' ? 'Strategy, analysis, planning roles, consulting, research' :
                        arrow.name === 'Emotional Plane' ? 'HR, counseling, teaching, customer relations, team management' :
                        arrow.name === 'Physical Plane' ? 'Business, finance, real estate, construction, material production' :
                        arrow.name === 'Arrow of Determination' ? 'Project management, entrepreneurship, challenging goals' :
                        arrow.name === 'Arrow of Activity' ? 'Sales, marketing, event management, dynamic leadership' :
                        arrow.name === 'Arrow of Intellect' ? 'Research, academia, technical fields, innovation' :
                        'Fields that utilize this strength'
                      }</p>
                    </div>
                  </details>
                </div>
              ))
            ) : (
              <div className="no-patterns">No complete patterns found - focus on developing individual number strengths</div>
            )}
          </div>
        </div>

        {/* Right: Growth Areas */}
        <div className="lessons-panel">
          <h4 className="section-title">🎯 Growth Areas</h4>
          <div className="lessons-grid">
            {arrows_of_strength.filter(arrow => arrow.type === 'Weakness').slice(0, 2).map((arrow, i) => (
              <div key={i} className="lesson-item">
                <span className="missing-arrow">⚠️</span>
                <div className="lesson-details">
                  <span className="lesson-text">{arrow.name}</span>
                  <small style={{display: 'block', color: '#666', fontSize: '0.75rem'}}>
                    {arrow.description}
                  </small>
                </div>
              </div>
            ))}
            {missing_numbers.slice(0, 2).map((item, i) => (
              <div key={`num-${i}`} className="lesson-item">
                <span className="missing-number">{item.number}</span>
                <div className="lesson-details">
                  <span className="lesson-text">{item.missing_energy} ({item.planet})</span>
                  <small style={{display: 'block', color: '#666', fontSize: '0.75rem'}}>
                    {item.lesson}
                  </small>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoShuGrid;