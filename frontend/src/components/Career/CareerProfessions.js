import React, { useState } from 'react';
import './CareerProfessions.css';

const CareerProfessions = ({ careerData }) => {
  const [expandedSections, setExpandedSections] = useState({ nature: true });
  
  if (!careerData?.nature_of_work) return <div>Loading professions...</div>;
  
  const {
    career_summary,
    recommended_roles,
    astrological_reasoning,
    key_strengths,
    work_environment
  } = careerData.nature_of_work;
  
  const toggleSection = (sectionId) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };
  
  const sections = [
    {
      id: 'nature',
      title: 'Nature of Work',
      subtitle: 'Creative / Technical / Administrative / Spiritual / Service / Trade / Leadership',
      icon: '🎯',
      bgColor: 'rgba(76, 175, 80, 0.05)',
      borderColor: 'rgba(76, 175, 80, 0.2)',
      active: true
    },
    {
      id: 'domain',
      title: 'Domain of Work',
      subtitle: 'Technology / Finance / Education / Medicine / Law / Arts / etc.',
      icon: '🏢',
      bgColor: 'rgba(33, 150, 243, 0.05)',
      borderColor: 'rgba(33, 150, 243, 0.2)',
      active: careerData?.domain_of_work ? true : false
    },
    {
      id: 'pattern',
      title: 'Work Pattern',
      subtitle: 'Employed / Self-employed / Government / Entrepreneur',
      icon: '💼',
      bgColor: 'rgba(255, 152, 0, 0.05)',
      borderColor: 'rgba(255, 152, 0, 0.2)',
      active: false
    },
    {
      id: 'trajectory',
      title: 'Career Trajectory',
      subtitle: 'Early/Late Success / Shifts / Foreign Connection / Stability',
      icon: '📈',
      bgColor: 'rgba(156, 39, 176, 0.05)',
      borderColor: 'rgba(156, 39, 176, 0.2)',
      active: false
    }
  ];
  
  return (
    <div className="career-professions">
      <h3>🎯 Your Career Analysis Framework</h3>
      <p>Comprehensive analysis of your professional potential based on Vedic astrology</p>
      
      <div className="professions-sections">
        {sections.map((section) => (
          <div 
            key={section.id}
            className="profession-section-card"
            style={{
              backgroundColor: section.bgColor,
              borderColor: section.borderColor
            }}
          >
            <div 
              className="section-header"
              onClick={() => section.active && toggleSection(section.id)}
              style={{ cursor: section.active ? 'pointer' : 'default' }}
            >
              <div className="section-title">
                <span className="section-icon">{section.icon}</span>
                <div className="title-content">
                  <h4>{section.title}</h4>
                  <p>{section.subtitle}</p>
                </div>
              </div>
              <div className="section-controls">
                {section.active && (
                  <span className={`expand-arrow ${expandedSections[section.id] ? 'expanded' : ''}`}>▼</span>
                )}
                <span className={`status-badge ${section.active ? 'active' : 'placeholder'}`}>
                  {section.active ? 'Active' : 'Coming Soon'}
                </span>
              </div>
            </div>
            
            {section.active && expandedSections[section.id] && (
              <div className="section-content">
                {section.id === 'nature' && (
                  <>
                    <div className="career-summary">
                      <h5>Your Work Nature</h5>
                      <p className="summary-text">{career_summary}</p>
                    </div>
                    
                    <div className="recommended-roles">
                      <h5>Recommended Career Paths</h5>
                      
                      <div className="role-section">
                        <h6>Primary Recommendations</h6>
                        <div className="role-tags">
                          {recommended_roles.primary_recommendations.map((role, index) => (
                            <span key={index} className="role-tag primary">{role}</span>
                          ))}
                        </div>
                      </div>
                      
                      <div className="role-section">
                        <h6>Traditional Options</h6>
                        <div className="role-tags">
                          {recommended_roles.traditional_options.map((role, index) => (
                            <span key={index} className="role-tag traditional">{role}</span>
                          ))}
                        </div>
                      </div>
                      
                      {recommended_roles.specialized_combinations && (
                        <div className="role-section">
                          <h6>Specialized Combinations</h6>
                          <div className="role-tags">
                            {recommended_roles.specialized_combinations.map((role, index) => (
                              <span key={index} className="role-tag specialized">{role}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <div className="approach-style">
                        <strong>Your Approach Style:</strong> {recommended_roles.approach_style}
                      </div>
                    </div>
                    
                    <div className="key-strengths">
                      <h5>Your Key Strengths</h5>
                      <div className="strengths-grid">
                        {key_strengths.map((strength, index) => (
                          <div key={index} className="strength-item">
                            <span className="strength-icon">✓</span>
                            {strength}
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div className="work-environment">
                      <h5>Ideal Work Environment</h5>
                      <p className="environment-text">{work_environment}</p>
                    </div>
                    
                    <div className="astrological-reasoning">
                      <h5>Astrological Reasoning</h5>
                      <div className="reasoning-list">
                        {astrological_reasoning.map((reason, index) => (
                          <div key={index} className="reasoning-item">
                            <span className="reasoning-bullet">•</span>
                            <span className="reasoning-text">{reason}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
                
                {section.id === 'domain' && careerData?.domain_of_work && (
                  <>
                    <div className="domain-summary">
                      <h5>Your Primary Domain</h5>
                      <div className="domain-result">
                        <span className="domain-type">{careerData.domain_of_work.primary_domain}</span>
                      </div>
                      {careerData.domain_of_work.astrological_analysis && (
                        <div className="analysis-why">
                          <strong>Why:</strong> {careerData.domain_of_work.astrological_analysis.primary_domain_why}
                        </div>
                      )}
                    </div>
                    
                    <div className="target-industries">
                      <h5>Target Industries</h5>
                      <div className="industry-tags">
                        {careerData.domain_of_work.industries.map((industry, index) => (
                          <span key={index} className="industry-tag">{industry}</span>
                        ))}
                      </div>
                      {careerData.domain_of_work.astrological_analysis && (
                        <div className="analysis-why">
                          <strong>Why:</strong> {careerData.domain_of_work.astrological_analysis.industries_why}
                        </div>
                      )}
                    </div>
                    
                    <div className="specific-roles">
                      <h5>Recommended Roles</h5>
                      <div className="role-tags">
                        {careerData.domain_of_work.specific_roles.map((role, index) => (
                          <span key={index} className="role-tag">{role}</span>
                        ))}
                      </div>
                      {careerData.domain_of_work.astrological_analysis && (
                        <div className="analysis-why">
                          <strong>Why:</strong> {careerData.domain_of_work.astrological_analysis.roles_why}
                        </div>
                      )}
                    </div>
                    
                    <div className="company-types">
                      <h5>Company Types</h5>
                      <div className="company-tags">
                        {careerData.domain_of_work.company_types.map((company, index) => (
                          <span key={index} className="company-tag">{company}</span>
                        ))}
                      </div>
                      {careerData.domain_of_work.astrological_analysis && (
                        <div className="analysis-why">
                          <strong>Why:</strong> {careerData.domain_of_work.astrological_analysis.companies_why}
                        </div>
                      )}
                    </div>
                    

                    <div className="key-skills">
                      <h5>Skills to Develop</h5>
                      <div className="skills-grid">
                        {careerData.domain_of_work.key_skills.map((skill, index) => (
                          <div key={index} className="skill-item">
                            <span className="skill-icon">🎯</span>
                            {skill}
                          </div>
                        ))}
                      </div>
                      {careerData.domain_of_work.astrological_analysis && (
                        <div className="analysis-why">
                          <strong>Why:</strong> {careerData.domain_of_work.astrological_analysis.skills_why}
                        </div>
                      )}
                    </div>
                    
                    {careerData.domain_of_work.modern_applications?.length > 0 && (
                      <div className="modern-applications">
                        <h5>Modern Applications</h5>
                        <div className="application-tags">
                          {careerData.domain_of_work.modern_applications.map((app, index) => (
                            <span key={index} className="application-tag">{app}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="career-guidance">
                      <h5>Action Plan</h5>
                      <div className="guidance-list">
                        {careerData.domain_of_work.career_guidance.map((guidance, index) => (
                          <div key={index} className="guidance-item">
                            <span className="guidance-icon">💡</span>
                            <span className="guidance-text">{guidance}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
            
            {!section.active && (
              <div className="section-placeholder">
                <p>This analysis will provide insights into {section.title.toLowerCase()} based on your birth chart.</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default CareerProfessions;