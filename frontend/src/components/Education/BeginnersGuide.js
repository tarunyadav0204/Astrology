import React from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import './BeginnersGuide.css';

const BeginnersGuide = () => {
  const lessons = [
    {
      id: 1,
      title: "What is Astrology?",
      duration: "5 min read",
      level: "Beginner",
      content: "Astrology is the study of celestial movements and their influence on human affairs. Learn the fundamental concepts and history of this ancient practice.",
      topics: ["Definition of Astrology", "Historical Background", "Vedic vs Western Systems", "Basic Principles"],
      completed: false
    },
    {
      id: 2,
      title: "The Zodiac Signs",
      duration: "8 min read",
      level: "Beginner",
      content: "Discover the 12 zodiac signs, their characteristics, elements, and ruling planets. Understanding signs is fundamental to astrology.",
      topics: ["12 Zodiac Signs", "Elements (Fire, Earth, Air, Water)", "Ruling Planets", "Sign Characteristics"],
      completed: false
    },
    {
      id: 3,
      title: "Understanding Your Birth Chart",
      duration: "10 min read",
      level: "Beginner",
      content: "Learn how to read a birth chart, including houses, planets, and aspects. Your birth chart is your cosmic blueprint.",
      topics: ["Birth Chart Basics", "12 Houses", "Planet Positions", "Ascendant/Rising Sign"],
      completed: false
    },
    {
      id: 4,
      title: "The Planets and Their Meanings",
      duration: "12 min read",
      level: "Beginner",
      content: "Explore the nine planets in Vedic astrology and their significance in your life and personality.",
      topics: ["Sun, Moon, Mars", "Mercury, Jupiter, Venus", "Saturn, Rahu, Ketu", "Planetary Influences"],
      completed: false
    },
    {
      id: 5,
      title: "The 12 Houses Explained",
      duration: "15 min read",
      level: "Intermediate",
      content: "Deep dive into the 12 houses of astrology and what each represents in different areas of your life.",
      topics: ["House Meanings", "Life Areas", "House Lords", "Planetary Placements"],
      completed: false
    },
    {
      id: 6,
      title: "Aspects and Conjunctions",
      duration: "10 min read",
      level: "Intermediate",
      content: "Learn about planetary aspects, conjunctions, and how planets influence each other in your chart.",
      topics: ["Planetary Aspects", "Conjunctions", "Trines & Squares", "Aspect Meanings"],
      completed: false
    },
    {
      id: 7,
      title: "Nakshatras (Lunar Mansions)",
      duration: "12 min read",
      level: "Intermediate",
      content: "Understand the 27 Nakshatras and their role in Vedic astrology for deeper personality insights.",
      topics: ["27 Nakshatras", "Nakshatra Lords", "Pada System", "Characteristics"],
      completed: false
    },
    {
      id: 8,
      title: "Dasha Systems",
      duration: "15 min read",
      level: "Advanced",
      content: "Introduction to planetary periods (Dashas) and how they influence timing of events in your life.",
      topics: ["Vimshottari Dasha", "Planetary Periods", "Sub-periods", "Timing Events"],
      completed: false
    }
  ];

  const [completedLessons, setCompletedLessons] = React.useState(new Set());
  const navigate = useNavigate();

  const toggleLessonComplete = (lessonId) => {
    const newCompleted = new Set(completedLessons);
    if (newCompleted.has(lessonId)) {
      newCompleted.delete(lessonId);
    } else {
      newCompleted.add(lessonId);
    }
    setCompletedLessons(newCompleted);
  };

  const progressPercentage = (completedLessons.size / lessons.length) * 100;

  return (
    <div className="beginners-guide-page">
      <SEOHead 
        title="Beginner's Guide to Astrology - Learn Vedic Astrology Basics | AstroRoshni"
        description="Complete beginner's guide to astrology with step-by-step lessons. Learn zodiac signs, birth charts, planets, houses and Vedic astrology fundamentals."
        keywords="astrology for beginners, learn astrology, vedic astrology basics, zodiac signs guide, birth chart tutorial, astrology lessons"
        canonical="https://astroroshni.com/beginners-guide"
        structuredData={{
          "@context": "https://schema.org",
          "@type": "Course",
          "name": "Beginner's Guide to Astrology",
          "description": "Complete astrology course for beginners covering zodiac signs, birth charts, planets and Vedic astrology",
          "provider": { "@type": "Organization", "name": "AstroRoshni" },
          "courseMode": "online",
          "educationalLevel": "Beginner"
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
          <h1>🎓 Beginner's Guide to Astrology</h1>
          <p>Start your astrology journey with step-by-step lessons</p>
        </header>

        <div className="progress-section">
          <div className="progress-header">
            <h3>Your Learning Progress</h3>
            <span className="progress-text">{completedLessons.size} of {lessons.length} lessons completed</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{width: `${progressPercentage}%`}}></div>
          </div>
          <div className="progress-percentage">{Math.round(progressPercentage)}%</div>
        </div>

        <div className="lessons-grid">
          {lessons.map(lesson => (
            <div key={lesson.id} className={`lesson-card ${completedLessons.has(lesson.id) ? 'completed' : ''}`}>
              <div className="lesson-header">
                <div className="lesson-number">Lesson {lesson.id}</div>
                <div className="lesson-level">{lesson.level}</div>
                <div className="lesson-duration">{lesson.duration}</div>
              </div>
              
              <h3 className="lesson-title">{lesson.title}</h3>
              <p className="lesson-description">{lesson.content}</p>
              
              <div className="lesson-topics">
                <h4>What You'll Learn:</h4>
                <ul>
                  {lesson.topics.map((topic, index) => (
                    <li key={index}>{topic}</li>
                  ))}
                </ul>
              </div>

              <div className="lesson-actions">
                <button 
                  className="start-lesson-btn"
                  onClick={() => navigate(`/lesson/${lesson.id}`)}
                >
                  {completedLessons.has(lesson.id) ? 'Review Lesson' : 'Start Lesson'}
                </button>
                <button 
                  className={`complete-btn ${completedLessons.has(lesson.id) ? 'completed' : ''}`}
                  onClick={() => toggleLessonComplete(lesson.id)}
                >
                  {completedLessons.has(lesson.id) ? '✓ Completed' : 'Mark Complete'}
                </button>
              </div>
            </div>
          ))}
        </div>

        <section className="learning-resources">
          <h2>📖 Additional Learning Resources</h2>
          <div className="resources-grid">
            <div className="resource-card">
              <h3>🔤 Astrology Glossary</h3>
              <p>Essential terms and definitions for beginners</p>
              <ul>
                <li>Ascendant - Your rising sign</li>
                <li>Conjunction - Planets close together</li>
                <li>Transit - Current planetary movements</li>
                <li>Retrograde - Apparent backward motion</li>
              </ul>
            </div>
            <div className="resource-card">
              <h3>🎯 Practice Exercises</h3>
              <p>Hands-on activities to reinforce learning</p>
              <ul>
                <li>Identify your Sun, Moon, Rising signs</li>
                <li>Locate planets in your birth chart</li>
                <li>Practice reading house meanings</li>
                <li>Calculate your current Dasha period</li>
              </ul>
            </div>
            <div className="resource-card">
              <h3>📚 Recommended Books</h3>
              <p>Essential reading for astrology students</p>
              <ul>
                <li>Light on Life by Hart de Fouw</li>
                <li>Astrology for the Soul by Jan Spiller</li>
                <li>The Only Astrology Book You'll Ever Need</li>
                <li>Vedic Astrology by David Frawley</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="next-steps">
          <h2>🚀 Ready for More?</h2>
          <div className="next-steps-grid">
            <div className="next-step-card">
              <h3>📊 Practice with Your Chart</h3>
              <p>Apply what you've learned to your own birth chart</p>
              <button className="next-step-btn" onClick={() => navigate('/birth-details')}>
                Get My Chart
              </button>
            </div>
            <div className="next-step-card">
              <h3>📚 Advanced Courses</h3>
              <p>Take your knowledge to the next level</p>
              <button className="next-step-btn" onClick={() => navigate('/advanced-courses')}>
                View Courses
              </button>
            </div>
            <div className="next-step-card">
              <h3>💬 Ask Questions</h3>
              <p>Get personalized guidance from experts</p>
              <button className="next-step-btn" onClick={() => navigate('/chat')}>
                Start Chat
              </button>
            </div>
          </div>
        </section>

        <section className="study-tips">
          <h2>💡 Study Tips for Success</h2>
          <div className="tips-grid">
            <div className="tip-card">
              <div className="tip-icon">📅</div>
              <h4>Study Regularly</h4>
              <p>Dedicate 15-20 minutes daily to astrology study for best results</p>
            </div>
            <div className="tip-card">
              <div className="tip-icon">📝</div>
              <h4>Take Notes</h4>
              <p>Keep a journal of your observations and chart interpretations</p>
            </div>
            <div className="tip-card">
              <div className="tip-icon">🤝</div>
              <h4>Practice with Others</h4>
              <p>Study friends' and family charts to gain experience</p>
            </div>
            <div className="tip-card">
              <div className="tip-icon">🔍</div>
              <h4>Start Simple</h4>
              <p>Master the basics before moving to advanced techniques</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default BeginnersGuide;