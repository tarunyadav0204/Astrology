import React from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import './AdvancedCourses.css';

const AdvancedCourses = () => {
  const courses = [
    {
      id: 1,
      title: "Predictive Astrology Mastery",
      level: "Advanced",
      duration: "12 weeks",
      price: "₹15,000",
      description: "Master the art of accurate predictions using Vimshottari Dasha, transits, and classical techniques.",
      topics: ["Dasha Analysis", "Transit Predictions", "Timing Events", "Yogas & Combinations"],
      instructor: "Pandit Rajesh Sharma",
      rating: 4.9
    },
    {
      id: 2,
      title: "Medical Astrology Certification",
      level: "Expert",
      duration: "16 weeks",
      price: "₹25,000",
      description: "Learn to analyze health patterns and potential medical issues through astrological charts.",
      topics: ["Disease Prediction", "Planetary Health", "Remedial Measures", "Case Studies"],
      instructor: "Dr. Priya Agarwal",
      rating: 4.8
    },
    {
      id: 3,
      title: "Relationship & Marriage Analysis",
      level: "Intermediate",
      duration: "8 weeks",
      price: "₹12,000",
      description: "Comprehensive study of compatibility, marriage timing, and relationship dynamics.",
      topics: ["Compatibility Analysis", "Marriage Timing", "Divorce Yoga", "Remedies"],
      instructor: "Acharya Vikram Singh",
      rating: 4.7
    },
    {
      id: 4,
      title: "Financial Astrology & Wealth",
      level: "Advanced",
      duration: "10 weeks",
      price: "₹18,000",
      description: "Analyze wealth potential, business success, and financial timing through charts.",
      topics: ["Wealth Yogas", "Business Astrology", "Stock Market", "Property Analysis"],
      instructor: "CA Suresh Kumar",
      rating: 4.9
    },
    {
      id: 5,
      title: "Remedial Astrology & Gemstones",
      level: "Intermediate",
      duration: "6 weeks",
      price: "₹10,000",
      description: "Learn effective remedial measures, gemstone selection, and spiritual practices.",
      topics: ["Gemstone Selection", "Mantra Therapy", "Yantra Science", "Puja Methods"],
      instructor: "Pandit Mohan Joshi",
      rating: 4.6
    },
    {
      id: 6,
      title: "Mundane & Political Astrology",
      level: "Expert",
      duration: "14 weeks",
      price: "₹22,000",
      description: "Study world events, political changes, and natural disasters through astrology.",
      topics: ["World Events", "Political Analysis", "Natural Disasters", "Economic Trends"],
      instructor: "Prof. Ashok Patel",
      rating: 4.8
    }
  ];

  const navigate = useNavigate();

  return (
    <div className="advanced-courses-page">
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
          <h1>📚 Advanced Astrology Courses</h1>
          <p>Master complex astrological techniques with expert guidance</p>
        </header>

        <div className="courses-grid">
          {courses.map(course => (
            <div key={course.id} className="course-card">
              <div className="course-header">
                <div className="course-level">{course.level}</div>
                <div className="course-rating">⭐ {course.rating}</div>
              </div>
              
              <h3 className="course-title">{course.title}</h3>
              <p className="course-description">{course.description}</p>
              
              <div className="course-details">
                <div className="detail-item">
                  <span className="detail-label">Duration:</span>
                  <span className="detail-value">{course.duration}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Instructor:</span>
                  <span className="detail-value">{course.instructor}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Price:</span>
                  <span className="detail-price">{course.price}</span>
                </div>
              </div>

              <div className="course-topics">
                <h4>What You'll Learn:</h4>
                <ul>
                  {course.topics.map((topic, index) => (
                    <li key={index}>{topic}</li>
                  ))}
                </ul>
              </div>

              <button className="enroll-btn">
                Enroll Now
              </button>
            </div>
          ))}
        </div>

        <section className="course-benefits">
          <h2>🎯 Why Choose Our Courses?</h2>
          <div className="benefits-grid">
            <div className="benefit-card">
              <h3>🎓 Expert Instructors</h3>
              <p>Learn from renowned astrologers with decades of experience</p>
            </div>
            <div className="benefit-card">
              <h3>📖 Classical Texts</h3>
              <p>Study authentic Vedic texts and traditional methodologies</p>
            </div>
            <div className="benefit-card">
              <h3>🔬 Practical Training</h3>
              <p>Hands-on practice with real charts and case studies</p>
            </div>
            <div className="benefit-card">
              <h3>📜 Certification</h3>
              <p>Receive recognized certificates upon course completion</p>
            </div>
          </div>
        </section>

        <section className="enrollment-info">
          <h2>📞 Ready to Begin Your Journey?</h2>
          <p>Contact us for personalized course recommendations and enrollment assistance.</p>
          <div className="contact-buttons">
            <button className="contact-btn primary">
              📞 Call: +91-9876543210
            </button>
            <button className="contact-btn secondary">
              📧 Email: courses@astroroshni.com
            </button>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AdvancedCourses;