import React from 'react';
import './SoulBlueprint.css';

const getCoreNumberExplanation = (type, number) => {
  const explanations = {
    life_path: {
      1: "Your life's main journey: Leadership & Independence\n\nWhat it means: You're here to lead, innovate, and pioneer new paths\nCareer direction: Entrepreneurship, management, creative leadership\nLife theme: Self-reliance, breaking new ground, inspiring others to follow",
      
      2: "Your life's main journey: Cooperation & Partnership\n\nWhat it means: You're here to bring people together and create harmony\nCareer direction: Counseling, diplomacy, teamwork-based roles\nLife theme: Building bridges, supporting others, creating peace",
      
      3: "Your life's main journey: Communication & Creativity\n\nWhat it means: You're here to express, inspire, and bring joy to others\nCareer direction: Arts, entertainment, communications, teaching\nLife theme: Self-expression, creativity, uplifting others through your talents",
      
      4: "Your life's main journey: Building & Organization\n\nWhat it means: You're here to create lasting structures and systems\nCareer direction: Engineering, management, construction, systematic work\nLife theme: Hard work, reliability, building foundations for others",
      
      5: "Your life's main journey: Freedom & Adventure\n\nWhat it means: You're here to explore, experience, and promote freedom\nCareer direction: Travel, sales, variety-based work, promoting change\nLife theme: Breaking limitations, experiencing diversity, inspiring others to embrace change",
      
      6: "Your life's main journey: Service & Nurturing\n\nWhat it means: You're here to nurture, heal, and create harmony\nCareer direction: Teaching, healthcare, counseling, family business\nLife theme: Service to others, responsibility, creating stable homes/communities",
      
      7: "Your life's main journey: Wisdom & Analysis\n\nWhat it means: You're here to seek truth, develop wisdom, and share insights\nCareer direction: Research, spirituality, analysis, specialized expertise\nLife theme: Inner development, seeking deeper meaning, becoming a wise guide",
      
      8: "Your life's main journey: Achievement & Authority\n\nWhat it means: You're here to achieve material success and use power wisely\nCareer direction: Business, finance, executive roles, material accomplishment\nLife theme: Material mastery, leadership through achievement, building lasting enterprises",
      
      9: "Your life's main journey: Service & Completion\n\nWhat it means: You're here to serve humanity and complete important cycles\nCareer direction: Humanitarian work, teaching, healing, serving the greater good\nLife theme: Universal service, wisdom sharing, helping humanity evolve"
    },
    
    expression: {
      1: "Your natural talents: Leadership & Initiative\n\nWhat it means: You're naturally independent, pioneering, and leadership-oriented\nStrengths: Starting projects, making decisions, inspiring confidence\nWork style: Self-directed, innovative, prefers to lead rather than follow",
      
      2: "Your natural talents: Cooperation & Diplomacy\n\nWhat it means: You're naturally cooperative, diplomatic, and partnership-oriented\nStrengths: Bringing people together, mediating conflicts, supporting others\nWork style: Collaborative, patient, prefers harmony over competition",
      
      3: "Your natural talents: Communication & Creativity\n\nWhat it means: You're naturally expressive, creative, and socially gifted\nStrengths: Self-expression, inspiring others, bringing joy and creativity\nWork style: Enthusiastic, social, prefers variety and creative freedom",
      
      4: "Your natural talents: Organization & Building\n\nWhat it means: You're naturally organized, practical, and hardworking\nStrengths: Building systems, managing details, creating lasting results\nWork style: Methodical, reliable, prefers structure over chaos",
      
      5: "Your natural talents: Adaptability & Freedom\n\nWhat it means: You're naturally versatile, curious, and freedom-loving\nStrengths: Adapting to change, promoting progress, inspiring adventure\nWork style: Flexible, energetic, prefers variety over routine",
      
      6: "Your natural talents: Nurturing & Responsibility\n\nWhat it means: You're naturally caring, responsible, and service-oriented\nStrengths: Helping others, creating harmony, taking care of family/community\nWork style: Supportive, reliable, prefers meaningful work that helps others",
      
      7: "Your natural talents: Analysis & Intuition\n\nWhat it means: You're naturally analytical, intuitive, and wisdom-seeking\nStrengths: Deep thinking, research, uncovering hidden truths\nWork style: Thoughtful, independent, prefers quality over quantity",
      
      8: "Your natural talents: Business & Achievement\n\nWhat it means: You're naturally business-minded, ambitious, and results-oriented\nStrengths: Managing resources, achieving goals, building material success\nWork style: Ambitious, organized, prefers measurable results and recognition",
      
      9: "Your natural talents: Wisdom & Service\n\nWhat it means: You're naturally wise, compassionate, and humanitarian\nStrengths: Seeing the big picture, inspiring others, serving humanity\nWork style: Idealistic, generous, prefers work that serves a higher purpose"
    },
    
    soul_urge: {
      1: "Your inner desires: Independence & Leadership\n\nWhat it means: Deep down, you want to be your own boss and lead others\nMotivation: Achieving personal independence, being recognized as a leader\nFulfillment: Comes from pioneering new paths and inspiring others to follow",
      
      2: "Your inner desires: Harmony & Partnership\n\nWhat it means: Deep down, you want peace, love, and meaningful relationships\nMotivation: Creating harmony, building lasting partnerships\nFulfillment: Comes from bringing people together and creating cooperation",
      
      3: "Your inner desires: Self-Expression & Joy\n\nWhat it means: Deep down, you want to express yourself and bring joy to others\nMotivation: Creative self-expression, inspiring and entertaining others\nFulfillment: Comes from sharing your talents and making others happy",
      
      4: "Your inner desires: Security & Order\n\nWhat it means: Deep down, you want stability, security, and organized systems\nMotivation: Building lasting security, creating order from chaos\nFulfillment: Comes from building something solid and dependable",
      
      5: "Your inner desires: Freedom & Adventure\n\nWhat it means: Deep down, you want freedom, variety, and new experiences\nMotivation: Experiencing life fully, promoting freedom for all\nFulfillment: Comes from adventure, travel, and breaking free from limitations",
      
      6: "Your inner desires: Love & Service\n\nWhat it means: Deep down, you want to love, nurture, and help others\nMotivation: Creating harmony, helping family and community\nFulfillment: Comes from taking care of others and creating beautiful environments",
      
      7: "Your inner desires: Truth & Understanding\n\nWhat it means: Deep down, you want to understand life's mysteries and find truth\nMotivation: Seeking wisdom, understanding deeper meanings\nFulfillment: Comes from spiritual growth and sharing insights with others",
      
      8: "Your inner desires: Success & Recognition\n\nWhat it means: Deep down, you want material success and recognition for achievements\nMotivation: Building wealth, gaining authority and respect\nFulfillment: Comes from material accomplishment and being recognized as successful",
      
      9: "Your inner desires: Service & Universal Love\n\nWhat it means: Deep down, you want to make the world better\nMotivation: Helping humanity, leaving a positive legacy\nFulfillment: Comes from serving causes bigger than yourself"
    }
  };
  
  return explanations[type]?.[number] || "Personal growth and development";
};

const SoulBlueprint = ({ blueprintData }) => {
  if (!blueprintData) return null;

  const { life_path_number, expression_number, soul_urge_number } = blueprintData;

  const getCombinationAnalysis = (lifePath, expression, soulUrge) => {
    return `How they work together:

• Your Life Path ${lifePath} gives you the ${lifePath === 6 ? 'nurturing nature' : lifePath === 1 ? 'leadership drive' : lifePath === 9 ? 'humanitarian vision' : 'core life direction'}

• Your Expression ${expression} gives you the ${expression === 4 ? 'practical skills to build lasting help' : expression === 1 ? 'leadership abilities' : expression === 9 ? 'wisdom to guide others' : 'natural talents to succeed'}

• Your Soul Urge ${soulUrge} drives you toward ${soulUrge === 9 ? 'humanitarian causes' : soulUrge === 1 ? 'independence and leadership' : soulUrge === 6 ? 'service and nurturing' : 'your deepest motivations'}

Practical application: You'd thrive in careers that combine ${lifePath === 6 ? 'helping people' : 'your life path energy'} (${lifePath}) with ${expression === 4 ? 'systematic approaches' : 'your natural talents'} (${expression}) for ${soulUrge === 9 ? 'humanitarian impact' : 'fulfilling your deepest desires'} (${soulUrge}) - like ${lifePath === 6 && expression === 4 && soulUrge === 9 ? 'running a nonprofit, healthcare administration, or educational program development' : 'roles that align all three numbers'}.

This combination makes you a "${lifePath === 6 && expression === 4 && soulUrge === 9 ? 'practical humanitarian' : 'unique blend'}" - someone who ${lifePath === 6 && expression === 4 && soulUrge === 9 ? "doesn't just care, but actually builds systems that help people effectively" : 'combines these energies in a powerful way'}.`;
  };

  return (
    <div className="soul-blueprint-container">
      <div className="core-numbers-section">
        <h3 className="section-header">🌟 Core Numbers</h3>
        <p className="section-intro">Your three most important numbers that define your personality and life purpose:</p>
        
        <div className="core-numbers-grid">
          {/* Life Path */}
          <div className="core-number-card">
            <div className="number-display">
              <span className="number">{life_path_number}</span>
              <span className="label">Life Path</span>
            </div>
            <div className="number-meaning">
              <p className="brief-meaning">Nurturing, responsible, family-oriented</p>
              <details className="detailed-explanation">
                <summary>💡 What does Life Path {life_path_number} mean for you?</summary>
                <div className="explanation-content">
                  {getCoreNumberExplanation('life_path', life_path_number)}
                </div>
              </details>
            </div>
          </div>

          {/* Expression */}
          <div className="core-number-card">
            <div className="number-display">
              <span className="number">{expression_number}</span>
              <span className="label">Expression</span>
            </div>
            <div className="number-meaning">
              <p className="brief-meaning">Organization, hard work, building lasting things</p>
              <details className="detailed-explanation">
                <summary>💡 What does Expression {expression_number} mean for you?</summary>
                <div className="explanation-content">
                  {getCoreNumberExplanation('expression', expression_number)}
                </div>
              </details>
            </div>
          </div>

          {/* Soul Urge */}
          <div className="core-number-card">
            <div className="number-display">
              <span className="number">{soul_urge_number}</span>
              <span className="label">Soul Urge</span>
            </div>
            <div className="number-meaning">
              <p className="brief-meaning">Wants to serve humanity, make the world better</p>
              <details className="detailed-explanation">
                <summary>💡 What does Soul Urge {soul_urge_number} mean for you?</summary>
                <div className="explanation-content">
                  {getCoreNumberExplanation('soul_urge', soul_urge_number)}
                </div>
              </details>
            </div>
          </div>
        </div>

        {/* Combination Analysis */}
        <div className="combination-analysis">
          <details>
            <summary className="combination-summary">🎯 How do your numbers work together?</summary>
            <div className="combination-content">
              {getCombinationAnalysis(life_path_number, expression_number, soul_urge_number)}
            </div>
          </details>
        </div>
      </div>
    </div>
  );
};

export default SoulBlueprint;