import React, { useState } from 'react';
import { KP_CONFIG } from '../../../config/kpConfig';
import kpService from '../../../services/kpService';
import RulingPlanets from '../RulingPlanets/RulingPlanets';
import './KPHorary.css';

const KPHorary = ({ birthData }) => {
  const [question, setQuestion] = useState('');
  const [horaryNumber, setHoraryNumber] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [questionTime, setQuestionTime] = useState(null);
  const [showPopup, setShowPopup] = useState(false);

  const handleAnalyze = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    const number = parseInt(horaryNumber);
    if (!kpService.isValidHoraryNumber(number)) {
      setError(`Horary number must be between ${KP_CONFIG.HORARY.MIN_NUMBER} and ${KP_CONFIG.HORARY.MAX_NUMBER}`);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const currentTime = new Date().toISOString();
      setQuestionTime(currentTime);
      
      const result = await kpService.analyzeHorary(birthData, question, number, currentTime);
      setAnalysis(result);
      setShowPopup(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateRandomNumber = () => {
    const randomNum = Math.floor(Math.random() * KP_CONFIG.HORARY.MAX_NUMBER) + 1;
    setHoraryNumber(randomNum.toString());
  };

  return (
    <div className="kp-horary-container">
      <div className="horary-header">
        <h3>KP Horary</h3>
        <div className="horary-info">
          Ask a specific question and get precise answers
        </div>
      </div>
      
      <div className="horary-form">
        <div className="form-group">
          <label>Your Question</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a specific question (e.g., Will I get this job?)"
            rows={3}
            className="question-input"
          />
        </div>
        
        <div className="form-group">
          <label>Horary Number (1-249)</label>
          <div className="number-input-group">
            <input
              type="number"
              value={horaryNumber}
              onChange={(e) => setHoraryNumber(e.target.value)}
              min={KP_CONFIG.HORARY.MIN_NUMBER}
              max={KP_CONFIG.HORARY.MAX_NUMBER}
              placeholder="Enter or generate number"
              className="horary-number-input"
            />
            <button 
              onClick={generateRandomNumber}
              className="generate-btn"
              type="button"
            >
              Generate
            </button>
          </div>
        </div>
        
        <button 
          onClick={handleAnalyze}
          disabled={loading}
          className="analyze-btn"
        >
          {loading ? 'Analyzing...' : 'Analyze Question'}
        </button>
        
        {error && (
          <div className="horary-error">{error}</div>
        )}
      </div>
      
      {questionTime && (
        <div className="question-ruling">
          <RulingPlanets 
            birthData={birthData} 
            questionTime={questionTime}
          />
        </div>
      )}
      
      {showPopup && analysis && (
        <div className="horary-popup-overlay" onClick={() => setShowPopup(false)}>
          <div className="horary-popup" onClick={(e) => e.stopPropagation()}>
            <div className="popup-header">
              <h4>Analysis Result</h4>
              <button className="close-btn" onClick={() => setShowPopup(false)}>×</button>
            </div>
            
            <div className="popup-content">
              <div className="question-details">
                <span><strong>Question:</strong> {question}</span>
                <span><strong>Number:</strong> {horaryNumber}</span>
              </div>
              
              <div className="analysis-result">
                <div className={`answer ${analysis.answer ? analysis.answer.toLowerCase() : 'unknown'}`}>
                  <span className="answer-label">Answer:</span>
                  <span className="answer-value">{analysis.answer || 'No answer'}</span>
                </div>
                
                {analysis.confidence && (
                  <div className="confidence">
                    <span>Confidence: {analysis.confidence}%</span>
                  </div>
                )}
              </div>
              
              {analysis.explanation && (
                <div className="analysis-explanation">
                  <h5>Explanation</h5>
                  <p>{analysis.explanation}</p>
                </div>
              )}
              
              {analysis.timing && (
                <div className="analysis-timing">
                  <h5>Timing</h5>
                  <p>{analysis.timing}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KPHorary;