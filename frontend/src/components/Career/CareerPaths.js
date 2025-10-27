import React, { useState, useEffect } from 'react';
import { careerService } from '../../services/careerService';

const CareerPaths = ({ birthDetails }) => {
  const [expandedQuestions, setExpandedQuestions] = useState({});
  const [analysisData, setAnalysisData] = useState({});
  const [loading, setLoading] = useState({});
  
  const toggleQuestion = (questionId) => {
    setExpandedQuestions(prev => ({
      ...prev,
      [questionId]: !prev[questionId]
    }));
    
    // Load analysis when question is expanded
    if (!expandedQuestions[questionId] && !analysisData[questionId]) {
      loadAnalysis(questionId);
    }
  };

  const loadAnalysis = async (questionId) => {
    if (!birthDetails) return;
    
    setLoading(prev => ({ ...prev, [questionId]: true }));
    
    try {
      let result;
      switch (questionId) {
        case 'career-fields':
          result = await careerService.getCareerFieldsAnalysis(birthDetails);
          break;
        case 'job-roles':
          result = await careerService.getJobRolesAnalysis(birthDetails);
          break;
        case 'work-mode':
          result = await careerService.getWorkModeAnalysis(birthDetails);
          break;
        case 'industries':
          result = await careerService.getIndustriesAnalysis(birthDetails);
          break;
        case 'work-type':
          result = await careerService.getWorkTypeAnalysis(birthDetails);
          break;
        default:
          return;
      }
      
      setAnalysisData(prev => ({
        ...prev,
        [questionId]: result
      }));
    } catch (error) {
      console.error(`Error loading ${questionId} analysis:`, error);
      setAnalysisData(prev => ({
        ...prev,
        [questionId]: { error: 'Failed to load analysis' }
      }));
    } finally {
      setLoading(prev => ({ ...prev, [questionId]: false }));
    }
  };

  const renderCareerFields = (data) => {
    if (!data?.career_fields) return <p>No career fields data available</p>;
    
    return (
      <div className="career-analysis">
        <h5>🎯 Top Career Fields for You:</h5>
        {data.career_fields.map((field, index) => (
          <div key={index} className="career-field-item">
            <h6>{field.field}</h6>
            <p className="field-reason">{field.reason}</p>
          </div>
        ))}
      </div>
    );
  };

  const renderJobRoles = (data) => {
    if (!data?.job_roles) return <p>No job roles data available</p>;
    
    return (
      <div className="career-analysis">
        <h5>💼 Specific Job Roles for You:</h5>
        <div className="job-roles-list">
          {data.job_roles.map((role, index) => (
            <span key={index} className="job-role-tag">{role}</span>
          ))}
        </div>
      </div>
    );
  };

  const renderWorkMode = (data) => {
    if (!data?.work_mode) return <p>No work mode data available</p>;
    
    const { mode, confidence, reason } = data.work_mode;
    
    return (
      <div className="career-analysis">
        <div className="work-mode-result">
          <h5>🏢 Recommended Work Mode:</h5>
          <div className="mode-recommendation">
            <span className="mode-type">{mode}</span>
            <span className="confidence-score">{confidence}% confidence</span>
          </div>
          <p className="mode-reason">{reason}</p>
        </div>
      </div>
    );
  };

  const renderIndustries = (data) => {
    if (!data?.industries) return <p>No industries data available</p>;
    
    return (
      <div className="career-analysis">
        <h5>🏭 Suitable Industries:</h5>
        {data.industries.map((industry, index) => (
          <div key={index} className="industry-item">
            <h6>{industry.industry}</h6>
            <p className="industry-reason">{industry.reason}</p>
          </div>
        ))}
      </div>
    );
  };

  const renderWorkType = (data) => {
    if (!data?.work_type) return <p>No work type data available</p>;
    
    const { primary_type, scores, reason } = data.work_type;
    
    return (
      <div className="career-analysis">
        <h5>⚙️ Your Work Type:</h5>
        <div className="work-type-result">
          <div className="primary-type">
            <span className="type-label">Primary Type:</span>
            <span className="type-value">{primary_type}</span>
          </div>
          <div className="type-scores">
            {Object.entries(scores).map(([type, score]) => (
              <div key={type} className="score-item">
                <span className="score-type">{type}:</span>
                <span className="score-value">{score.toFixed(0)}%</span>
              </div>
            ))}
          </div>
          <p className="type-reason">{reason}</p>
        </div>
      </div>
    );
  };

  const questions = [
    {
      id: 'career-fields',
      icon: '🎯',
      question: 'What Career Fields Suit Me Best?',
      bgColor: 'rgba(76, 175, 80, 0.05)',
      borderColor: 'rgba(76, 175, 80, 0.2)',
      renderContent: renderCareerFields
    },
    {
      id: 'job-roles',
      icon: '💼',
      question: 'What Specific Job Roles Should I Consider?',
      bgColor: 'rgba(33, 150, 243, 0.05)',
      borderColor: 'rgba(33, 150, 243, 0.2)',
      renderContent: renderJobRoles
    },
    {
      id: 'work-mode',
      icon: '🏢',
      question: 'Should I Be an Employee or Entrepreneur?',
      bgColor: 'rgba(255, 152, 0, 0.05)',
      borderColor: 'rgba(255, 152, 0, 0.2)',
      renderContent: renderWorkMode
    },
    {
      id: 'industries',
      icon: '🏭',
      question: 'What Industries Align with My Nature?',
      bgColor: 'rgba(156, 39, 176, 0.05)',
      borderColor: 'rgba(156, 39, 176, 0.2)',
      renderContent: renderIndustries
    },
    {
      id: 'work-type',
      icon: '⚙️',
      question: 'Am I Meant for Creative, Technical, or Service Work?',
      bgColor: 'rgba(233, 30, 99, 0.05)',
      borderColor: 'rgba(233, 30, 99, 0.2)',
      renderContent: renderWorkType
    }
  ];

  return (
    <div className="career-paths">
      <h3>🛤️ What Career Path Should You Take?</h3>
      <p>Discover your ideal career direction based on your birth chart's professional indicators</p>
      
      <div className="career-path-questions">
        {questions.map((q) => (
          <div 
            key={q.id} 
            className="career-path-question-card"
            style={{ 
              backgroundColor: q.bgColor,
              borderColor: q.borderColor
            }}
          >
            <div 
              className="question-header"
              onClick={() => toggleQuestion(q.id)}
            >
              <div className="question-title">
                <span className="question-icon">{q.icon}</span>
                <h4>{q.question}</h4>
              </div>
              <span className={`expand-arrow ${expandedQuestions[q.id] ? 'expanded' : ''}`}>▼</span>
            </div>
            
            {expandedQuestions[q.id] && (
              <div className="question-content">
                {loading[q.id] ? (
                  <div className="loading-spinner">
                    <div className="spinner"></div>
                    <p>Analyzing your career path...</p>
                  </div>
                ) : analysisData[q.id]?.error ? (
                  <div className="error-message">
                    <p>{analysisData[q.id].error}</p>
                  </div>
                ) : analysisData[q.id] ? (
                  q.renderContent(analysisData[q.id])
                ) : (
                  <div className="no-data">
                    <p>Click to load analysis...</p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default CareerPaths;