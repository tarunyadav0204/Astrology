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
            </div>
          </div>
          <div className="core-number-item">
            <span className="number-badge expression">{core_numbers?.expression?.number || '?'}</span>
            <div className="number-info">
              <strong>Expression</strong>
              <small>{getExpressionMeaning(core_numbers?.expression?.number)}</small>
            </div>
          </div>
          <div className="core-number-item">
            <span className="number-badge soul">{core_numbers?.soul_urge?.number || '?'}</span>
            <div className="number-info">
              <strong>Soul Urge</strong>
              <small>{getSoulUrgeMeaning(core_numbers?.soul_urge?.number)}</small>
            </div>
          </div>
        </div>

        {/* Right: Lo Shu Grid */}
        <div className="loshu-grid-panel">
          <h3 className="panel-title">🔮 Lo Shu Grid</h3>
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
        </div>
      </div>

      {/* Bottom Section: Strengths & Lessons */}
      <div className="blueprint-bottom-section">
        
        {/* Left: Arrows of Strength */}
        <div className="strengths-panel">
          <h4 className="section-title">✨ Your Patterns</h4>
          <div className="strengths-grid">
            {arrows_of_strength.length > 0 ? (
              arrows_of_strength.filter(arrow => arrow.type === 'Strength').slice(0, 3).map((arrow, i) => (
                <div key={i} className="arrow-badge strength" title={getPatternMeaning(arrow.name)}>
                  {getPatternMeaning(arrow.name)}
                </div>
              ))
            ) : (
              <div className="no-strengths">No complete patterns found</div>
            )}
          </div>
        </div>

        {/* Right: Growth Areas */}
        <div className="lessons-panel">
          <h4 className="section-title">🎯 Growth Areas</h4>
          <div className="lessons-grid">
            {/* Show missing arrows first */}
            {arrows_of_strength.filter(arrow => arrow.type === 'Weakness').slice(0, 2).map((arrow, i) => (
              <div key={i} className="lesson-item">
                <span className="missing-arrow">⚠️</span>
                <span className="lesson-text">{getPatternMeaning(arrow.name.replace('Missing ', ''))}</span>
              </div>
            ))}
            {/* Then show missing numbers */}
            {missing_numbers.slice(0, 1).map((item, i) => (
              <div key={`num-${i}`} className="lesson-item">
                <span className="missing-number">{item.number}</span>
                <span className="lesson-text">{item.lesson.split('.')[0]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoShuGrid;