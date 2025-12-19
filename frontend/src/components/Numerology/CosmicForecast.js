import React from 'react';
import './CosmicForecast.css';

// Helper functions for actionable advice
const getActionableAdvice = (dayNumber) => {
  const advice = {
    1: "Start new projects, take leadership, make important decisions",
    2: "Collaborate, negotiate, focus on partnerships and teamwork", 
    3: "Communicate, create, network, express your ideas publicly",
    4: "Organize, plan, handle details, build systems and processes",
    5: "Explore opportunities, travel, try new approaches, be flexible",
    6: "Focus on family, home, help others, make improvements",
    7: "Research, analyze, study, reflect, work alone on important projects",
    8: "Handle business matters, make financial decisions, focus on career",
    9: "Complete projects, help others, focus on bigger picture goals"
  };
  return advice[dayNumber] || "Focus on balance and intuition";
};

const getMonthFocus = (monthNumber) => {
  const focus = {
    1: "New beginnings", 2: "Building relationships", 3: "Creative expression",
    4: "Hard work pays off", 5: "Change & freedom", 6: "Family & responsibility", 
    7: "Inner development", 8: "Material success", 9: "Completion & service"
  };
  return focus[monthNumber] || "Personal growth";
};

const getYearTheme = (yearNumber) => {
  const themes = {
    1: "Fresh starts & independence", 2: "Cooperation & patience", 3: "Creativity & social expansion",
    4: "Building foundations", 5: "Freedom & adventure", 6: "Love & responsibility",
    7: "Spiritual growth", 8: "Achievement & recognition", 9: "Humanitarian service"
  };
  return themes[yearNumber] || "Personal transformation";
};

const getPinnacleExplanation = (number, ageRange) => {
  const explanations = {
    1: `The number 1 is your Pinnacle Number for ages ${ageRange}. It represents the dominant energy theme that will shape your experiences during this life phase.\n\nNumber 1 = The Leader/Pioneer\n\nWhat it means practically:\n• Career Success: You'll thrive in leadership roles, entrepreneurship, or pioneering new fields\n• Relationship Pattern: You attract followers and admirers; you're the decision-maker\n• Money Flow: Income comes through your own initiatives and independent ventures\n• Life Lessons: Learning to lead without being domineering, balancing independence with cooperation\n• Natural Talents: Starting projects, making decisions, inspiring confidence in others\n\nWhy this matters: Instead of waiting for others to lead, you'll find more success by taking initiative and trusting your instincts during this phase.`,
    
    2: `The number 2 is your Pinnacle Number for ages ${ageRange}. It represents the dominant energy theme that will shape your experiences during this life phase.\n\nNumber 2 = The Diplomat/Partner\n\nWhat it means practically:\n• Career Success: You'll thrive in collaborative roles, mediation, counseling, or support positions\n• Relationship Pattern: You attract partnerships; you're the peacemaker and supporter\n• Money Flow: Income comes through teamwork, partnerships, and serving others' needs\n• Life Lessons: Learning to assert yourself while maintaining harmony, avoiding over-dependence\n• Natural Talents: Bringing people together, seeing both sides, creating cooperation\n\nWhy this matters: Success comes through collaboration rather than competition during this phase.`,
    
    3: `The number 3 is your Pinnacle Number for ages ${ageRange}. It represents the dominant energy theme that will shape your experiences during this life phase.\n\nNumber 3 = The Communicator/Creative\n\nWhat it means practically:\n• Career Success: You'll thrive in creative fields, communications, entertainment, or social roles\n• Relationship Pattern: You attract social circles; you're the entertainer and communicator\n• Money Flow: Income comes through self-expression, creativity, and social connections\n• Life Lessons: Learning to focus your scattered energies, developing discipline in creative pursuits\n• Natural Talents: Self-expression, inspiring others, bringing joy and creativity to situations\n\nWhy this matters: Your natural charisma and creativity are your greatest assets during this phase.`,
    
    4: `The number 4 is your Pinnacle Number for ages ${ageRange}. It represents the dominant energy theme that will shape your experiences during this life phase.\n\nNumber 4 = The Builder/Organizer\n\nWhat it means practically:\n• Career Success: You'll thrive in structured environments, management, construction, or systematic work\n• Relationship Pattern: You attract people who need stability; you're the reliable foundation\n• Money Flow: Income comes through steady work, building systems, and long-term planning\n• Life Lessons: Learning patience with slow progress, balancing work with rest\n• Natural Talents: Organization, persistence, creating lasting structures and systems\n\nWhy this matters: Success comes through consistent effort and building solid foundations during this phase.`,
    
    5: `The number 5 is your Pinnacle Number for ages ${ageRange}. It represents the dominant energy theme that will shape your experiences during this life phase.\n\nNumber 5 = The Explorer/Freedom Seeker\n\nWhat it means practically:\n• Career Success: You'll thrive in varied roles, travel, sales, or fields requiring adaptability\n• Relationship Pattern: You attract adventurous people; you're the catalyst for change\n• Money Flow: Income comes through variety, travel, and embracing new opportunities\n• Life Lessons: Learning to commit without feeling trapped, channeling restless energy productively\n• Natural Talents: Adaptability, promoting freedom, inspiring others to embrace change\n\nWhy this matters: Embrace variety and change rather than seeking security during this phase.`,
    
    6: `The number 6 is your Pinnacle Number for ages ${ageRange}. It represents the dominant energy theme that will shape your experiences during this life phase.\n\nNumber 6 = The Caregiver/Nurturer\n\nWhat it means practically:\n• Career Success: You'll thrive in jobs where you help, heal, or serve others (teaching, healthcare, counseling, hospitality)\n• Relationship Pattern: You naturally attract people who need support; you're the "go-to" person for advice\n• Money Flow: Income comes through service to others, not aggressive competition\n• Life Lessons: Learning to balance giving with receiving, setting healthy boundaries\n• Natural Talents: Creating harmony, solving problems through compassion, making others feel valued\n\nWhy this matters: Instead of fighting against your nature by choosing purely competitive careers, you'll find more success by embracing roles where you can nurture and support others during this phase.`,
    
    7: `The number 7 is your Pinnacle Number for ages ${ageRange}. It represents the dominant energy theme that will shape your experiences during this life phase.\n\nNumber 7 = The Analyst/Seeker\n\nWhat it means practically:\n• Career Success: You'll thrive in research, analysis, spirituality, or specialized expertise fields\n• Relationship Pattern: You attract deep, meaningful connections; you're the wise advisor\n• Money Flow: Income comes through specialized knowledge and expertise\n• Life Lessons: Learning to share your insights, balancing solitude with social connection\n• Natural Talents: Deep analysis, intuitive insights, uncovering hidden truths\n\nWhy this matters: Trust your need for solitude and deep thinking - it leads to valuable insights during this phase.`,
    
    8: `The number 8 is your Pinnacle Number for ages ${ageRange}. It represents the dominant energy theme that will shape your experiences during this life phase.\n\nNumber 8 = The Achiever/Executive\n\nWhat it means practically:\n• Career Success: You'll thrive in business, finance, management, or authority positions\n• Relationship Pattern: You attract ambitious people; you're the provider and authority figure\n• Money Flow: Income comes through business acumen, investments, and material achievements\n• Life Lessons: Learning to balance material success with spiritual values, using power responsibly\n• Natural Talents: Business sense, organizing resources, achieving material goals\n\nWhy this matters: This is your time for material achievement and recognition - embrace ambitious goals during this phase.`,
    
    9: `The number 9 is your Pinnacle Number for ages ${ageRange}. It represents the dominant energy theme that will shape your experiences during this life phase.\n\nNumber 9 = The Humanitarian/Wise One\n\nWhat it means practically:\n• Career Success: You'll thrive in humanitarian work, teaching, healing, or serving the greater good\n• Relationship Pattern: You attract people seeking wisdom; you're the compassionate guide\n• Money Flow: Income comes through serving humanity and completing meaningful projects\n• Life Lessons: Learning to let go of what no longer serves, embracing your role as a wise guide\n• Natural Talents: Seeing the big picture, inspiring others toward higher purposes, healing and teaching\n\nWhy this matters: Focus on serving the greater good rather than personal gain during this phase.`,
    
    11: `The number 11 is your Pinnacle Number for ages ${ageRange}. It represents the dominant energy theme that will shape your experiences during this life phase.\n\nNumber 11 = The Inspirational Leader/Intuitive\n\nWhat it means practically:\n• Career Success: You'll thrive in inspirational roles, spiritual leadership, or innovative fields\n• Relationship Pattern: You attract people seeking inspiration; you're the visionary and guide\n• Money Flow: Income comes through inspiring others and innovative ideas\n• Life Lessons: Learning to ground your high ideals in practical reality, managing sensitivity\n• Natural Talents: Intuitive insights, inspiring others, bridging spiritual and material worlds\n\nWhy this matters: Trust your intuition and inspirational abilities - they're your greatest gifts during this phase.`,
    
    22: `The number 22 is your Pinnacle Number for ages ${ageRange}. It represents the dominant energy theme that will shape your experiences during this life phase.\n\nNumber 22 = The Master Builder/Visionary\n\nWhat it means practically:\n• Career Success: You'll thrive in large-scale projects, architecture, or turning visions into reality\n• Relationship Pattern: You attract people who share your vision; you're the master planner\n• Money Flow: Income comes through building something lasting and significant\n• Life Lessons: Learning to balance grand visions with practical steps, managing enormous potential\n• Natural Talents: Seeing the big picture, organizing massive projects, building lasting legacies\n\nWhy this matters: You have the potential to build something truly significant during this phase - think big and act systematically.`
  };
  return explanations[number] || "Personal growth and development phase";
};

const CosmicForecast = ({ forecastData }) => {
  if (!forecastData) return null;
  
  console.log('CosmicForecast received data:', forecastData);
  
  const { current_energy, life_timeline } = forecastData;
  const { personal_year, personal_month, personal_day } = current_energy;
  
  console.log('life_timeline:', life_timeline);
  console.log('pinnacles:', life_timeline?.pinnacles);

  return (
    <div className="forecast-container">
      
      {/* 1. Today's Action Plan */}
      <div className="weather-card">
        <div className="weather-header">
          <h4>📅 Today's Energy Focus</h4>
          <span style={{fontSize: '0.8rem', color: '#666'}}>{current_energy.analysis_date}</span>
        </div>

        <div className="energy-summary">
          <div className="energy-number">{personal_day.number}</div>
          <div className="energy-action">
            <h5>Best Actions Today:</h5>
            <p>{getActionableAdvice(personal_day.number)}</p>
          </div>
        </div>

        <div className="energy-context">
          <div className="context-item">
            <span className="context-label">This Month:</span>
            <span className="context-value">{getMonthFocus(personal_month.number)}</span>
          </div>
          <div className="context-item">
            <span className="context-label">This Year:</span>
            <span className="context-value">{getYearTheme(personal_year.number)}</span>
          </div>
        </div>
        
        {current_energy.daily_guidance && (
          <div className="daily-insight">
            <h6>💡 Why This Matters:</h6>
            <p dangerouslySetInnerHTML={{
              __html: current_energy.daily_guidance.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            }} />
          </div>
        )}
      </div>

      {/* 2. Life Strategy Map */}
      <div className="timeline-card">
        <h3 className="timeline-header">🎯 Your Life Strategy Phases</h3>
        <p style={{fontSize: '0.9rem', color: '#666', marginBottom: '20px'}}>
          Your life has 4 strategic phases. Each phase has specific goals and opportunities:
        </p>
        
        {life_timeline?.timeline && life_timeline.timeline.map((phase, i) => {
          const phaseIcons = ["🌱", "🚀", "🎯", "🌟"];
          const phaseGoals = [
            "Develop skills, establish identity, create stability",
            "Explore opportunities, build network, gain experience", 
            "Maximize achievements, lead others, reach peak performance",
            "Mentor others, leave legacy, focus on meaning"
          ];
          
          return (
            <div className="phase-row" key={i}>
              <div style={{flex: 1}}>
                <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px'}}>
                  <span className="phase-age">
                    Age {phase.age_range}
                  </span>
                  <strong style={{color: '#333'}}>{phaseIcons[i]} {phase.phase}</strong>
                </div>
                <div className="phase-info">
                  <p style={{margin: '5px 0', color: '#444', fontSize: '0.9rem'}}>
                    <strong>Goals:</strong> {phaseGoals[i]}
                  </p>
                  <p style={{margin: '0', color: '#666', fontSize: '0.85rem'}}>
                    <strong>Pinnacle #{phase.pinnacle.number}:</strong> {phase.pinnacle.meaning}
                  </p>
                  <details style={{marginTop: '10px'}}>
                    <summary style={{cursor: 'pointer', color: '#e91e63', fontSize: '0.85rem', fontWeight: '500'}}>
                      💡 What does #{phase.pinnacle.number} mean for you?
                    </summary>
                    <div style={{marginTop: '10px', padding: '10px', background: 'rgba(233, 30, 99, 0.05)', borderRadius: '8px', fontSize: '0.8rem', lineHeight: '1.4', whiteSpace: 'pre-line'}}>
                      {getPinnacleExplanation(phase.pinnacle.number, phase.age_range)}
                    </div>
                  </details>
                </div>
              </div>
              <div className="phase-number">
                {phase.pinnacle.number}
              </div>
            </div>
          );
        })}
        
        <div className="strategy-tip">
          <h6>🚀 Action Strategy:</h6>
          <p>Identify your current phase and align your goals with that phase's energy. This creates less resistance and more success in your endeavors.</p>
        </div>
      </div>

    </div>
  );
};

export default CosmicForecast;