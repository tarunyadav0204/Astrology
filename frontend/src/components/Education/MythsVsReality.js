import React from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import './MythsVsReality.css';

const MythsVsReality = () => {
  const articles = [
    {
      id: 1,
      title: "Astrology vs Astronomy: Understanding the Difference",
      myth: "Astrology and astronomy are the same thing",
      reality: "Astronomy is the scientific study of celestial objects, while astrology is the study of how celestial movements influence human affairs",
      content: "Many people confuse astrology with astronomy. Astronomy is a branch of science that deals with space, celestial objects, and the physical universe. Astrology, on the other hand, is an ancient practice that studies the correlation between planetary movements and human experiences. While astronomy uses telescopes and mathematical calculations, astrology uses birth charts and planetary positions to provide insights into personality and life events.",
      category: "Basics"
    },
    {
      id: 2,
      title: "The Precession Myth: Why Your Sign Hasn't Changed",
      myth: "Due to precession, all zodiac signs have shifted and your sign is wrong",
      reality: "Vedic astrology uses the sidereal zodiac which accounts for precession, while Western astrology uses the tropical zodiac based on seasons",
      content: "The precession argument often surfaces to 'debunk' astrology. However, this shows a misunderstanding of astrological systems. Vedic (Indian) astrology uses the sidereal zodiac, which is based on the actual star positions and does account for precession. Western astrology uses the tropical zodiac, which is based on the Earth's relationship to the Sun and seasons, not star positions. Both systems are internally consistent and serve different purposes.",
      category: "Technical"
    },
    {
      id: 3,
      title: "Free Will vs Determinism in Astrology",
      myth: "Astrology means everything is predetermined and you have no free will",
      reality: "Astrology shows tendencies and potentials, not fixed destinies. Free will allows you to work with or against these influences",
      content: "One of the biggest misconceptions is that astrology promotes fatalism. Classical texts like Brihat Parashara Hora Shastra emphasize that planets show tendencies, not certainties. Your birth chart is like a weather forecast - it shows the cosmic climate, but you decide how to dress and what activities to pursue. Remedial measures, conscious choices, and spiritual practices can all modify outcomes.",
      category: "Philosophy"
    },
    {
      id: 4,
      title: "The Twin Paradox: Why Twins Have Different Lives",
      myth: "If astrology works, twins born minutes apart should have identical lives",
      reality: "Small time differences create different ascendants, and environmental factors, karma, and choices create unique paths",
      content: "Critics often point to twins as proof against astrology. However, even a few minutes difference can change the rising sign (ascendant), which significantly affects the chart interpretation. Additionally, Vedic astrology recognizes that past karma (samskaras), family environment, personal choices, and spiritual development all play crucial roles in shaping one's destiny alongside planetary influences.",
      category: "Common Questions"
    },
    {
      id: 5,
      title: "Scientific Studies and Astrology",
      myth: "No scientific studies support astrology",
      reality: "While mainstream science doesn't validate predictive astrology, some studies show correlations between celestial cycles and human behavior",
      content: "The relationship between astrology and science is complex. While controlled studies haven't validated predictive astrology, research has found correlations between lunar cycles and human behavior, seasonal birth patterns and personality traits, and solar activity and mood disorders. Astrology may work through mechanisms not yet understood by current scientific paradigms, similar to how acupuncture was dismissed before its mechanisms were partially understood.",
      category: "Science"
    },
    {
      id: 6,
      title: "Astrology and Mental Health",
      myth: "Astrology is harmful to mental health and promotes dependency",
      reality: "When used wisely, astrology can provide self-awareness and coping strategies, but shouldn't replace professional mental health care",
      content: "Responsible astrology practice emphasizes self-empowerment and personal growth. It can help people understand their patterns, timing of challenges, and natural strengths. However, it should complement, not replace, professional therapy or medical treatment. Good astrologers encourage clients to take responsibility for their choices and seek appropriate professional help when needed.",
      category: "Psychology"
    },
    {
      id: 7,
      title: "The Placebo Effect Argument",
      myth: "Astrology only works because of the placebo effect",
      reality: "While psychological factors play a role, astrology's effectiveness in timing and prediction suggests mechanisms beyond placebo",
      content: "Skeptics often attribute astrological results to the placebo effect or confirmation bias. While these psychological factors certainly play a role in how people interpret astrological advice, they don't explain astrology's effectiveness in timing predictions, electional astrology (choosing auspicious times), or accurate personality descriptions based solely on birth data without client interaction.",
      category: "Psychology"
    },
    {
      id: 8,
      title: "Newspaper Horoscopes vs Real Astrology",
      myth: "Newspaper horoscopes represent real astrology",
      reality: "Generic sun-sign horoscopes are entertainment, not serious astrology which requires complete birth data",
      content: "Daily newspaper horoscopes are to astrology what fortune cookies are to Chinese philosophy - a simplified, commercialized version for entertainment. Real astrology requires your exact birth time, date, and location to create a personalized birth chart. Sun-sign astrology (newspaper horoscopes) only considers one factor out of dozens that professional astrologers analyze.",
      category: "Basics"
    }
  ];

  const categories = ["All", "Basics", "Technical", "Philosophy", "Common Questions", "Science", "Psychology"];
  const [selectedCategory, setSelectedCategory] = React.useState("All");

  const filteredArticles = selectedCategory === "All" 
    ? articles 
    : articles.filter(article => article.category === selectedCategory);

  const navigate = useNavigate();

  return (
    <div className="myths-reality-page">
      <SEOHead 
        title="Astrology Myths vs Reality - Facts About Vedic Astrology | AstroRoshni"
        description="Separate astrology facts from fiction. Evidence-based explanations debunking common myths about Vedic astrology, zodiac signs, and horoscopes."
        keywords="astrology myths, astrology facts, vedic astrology truth, astrology science, zodiac myths debunked, astrology misconceptions"
        canonical="https://astroroshni.com/myths-vs-reality"
        structuredData={{
          "@context": "https://schema.org",
          "@type": "Article",
          "headline": "Astrology Myths vs Reality - Facts About Vedic Astrology",
          "description": "Evidence-based explanations debunking common myths about astrology",
          "author": { "@type": "Organization", "name": "AstroRoshni" },
          "publisher": { "@type": "Organization", "name": "AstroRoshni" }
        }}
      />
      <NavigationHeader 
        onPeriodChange={() => {}}
        showZodiacSelector={false}
        zodiacSigns={[]}
        selectedZodiac={''}
        onZodiacChange={() => {}}
        user={null}
        onAdminClick={() => {}}
        onLogout={() => {}}
        onLogin={() => {}}
        showLoginButton={true}
      />
      <div className="container">
        <header className="page-header">
          <h1>🔍 Astrology: Myths vs Reality</h1>
          <p>Separating facts from misconceptions with evidence-based explanations</p>
        </header>

        <div className="category-filters">
          {categories.map(category => (
            <button
              key={category}
              className={`filter-btn ${selectedCategory === category ? 'active' : ''}`}
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>

        <div className="articles-grid">
          {filteredArticles.map(article => (
            <article key={article.id} className="myth-article">
              <div className="article-header">
                <span className="category-tag">{article.category}</span>
                <h2>{article.title}</h2>
              </div>
              
              <div className="myth-reality-boxes">
                <div className="myth-box">
                  <h3>❌ Myth</h3>
                  <p>{article.myth}</p>
                </div>
                <div className="reality-box">
                  <h3>✅ Reality</h3>
                  <p>{article.reality}</p>
                </div>
              </div>
              
              <div className="article-content">
                <h3>📖 Detailed Explanation</h3>
                <p>{article.content}</p>
              </div>
            </article>
          ))}
        </div>

        <section className="additional-resources">
          <h2>📚 Further Reading</h2>
          <div className="resources-grid">
            <div className="resource-card">
              <h3>Classical Texts</h3>
              <ul>
                <li>Brihat Parashara Hora Shastra</li>
                <li>Jaimini Sutras</li>
                <li>Phaladeepika</li>
                <li>Saravali</li>
              </ul>
            </div>
            <div className="resource-card">
              <h3>Modern Research</h3>
              <ul>
                <li>Michel Gauquelin's Studies</li>
                <li>Lunar Biological Rhythms</li>
                <li>Seasonal Birth Effects</li>
                <li>Solar Activity Correlations</li>
              </ul>
            </div>
            <div className="resource-card">
              <h3>Recommended Authors</h3>
              <ul>
                <li>B.V. Raman</li>
                <li>K.N. Rao</li>
                <li>Robert Hand</li>
                <li>Demetra George</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="disclaimer">
          <h3>⚠️ Important Note</h3>
          <p>
            This content is for educational purposes only. Astrology should be used as a tool for 
            self-reflection and guidance, not as a substitute for professional advice in medical, 
            legal, or financial matters. Always consult qualified professionals for serious life decisions.
          </p>
        </section>
      </div>
    </div>
  );
};

export default MythsVsReality;