import React, { useState } from 'react';

const AIQuestionsTab = ({ analysisData, user }) => {
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [customQuestion, setCustomQuestion] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const commonQuestions = [
    "What subjects should I focus on for better career prospects?",
    "When is the best time for me to pursue higher education?",
    "Should I consider studying abroad?",
    "What are my chances of success in competitive exams?",
    "How can I improve my concentration and memory?",
    "What type of learning environment suits me best?",
    "Should I pursue technical or non-technical education?",
    "What are the best periods for starting new courses?",
    "How can I overcome educational obstacles?",
    "What remedies can help improve my academic performance?"
  ];

  const handleQuestionSelect = (question) => {
    setSelectedQuestion(question);
    setCustomQuestion(question);
  };

  const handleAskQuestion = async () => {
    if (!customQuestion.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/ai/education-question', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          question: customQuestion,
          analysisData: analysisData,
          userContext: {
            name: user?.name,
            birthData: JSON.parse(localStorage.getItem('currentBirthData') || '{}')
          }
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get AI response');
      }

      const data = await response.json();
      setAiResponse(data.response);
    } catch (error) {
      console.error('Error getting AI response:', error);
      setAiResponse('Sorry, I encountered an error while processing your question. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-questions-tab">
      <div className="ai-intro">
        <h2>🤖 Ask AI About Your Education</h2>
        <p>Get personalized answers to your education-related questions based on your astrological analysis.</p>
      </div>

      <div className="questions-section">
        <h3>💡 Common Questions</h3>
        <div className="questions-grid">
          {commonQuestions.map((question, index) => (
            <button
              key={index}
              className={`question-btn ${selectedQuestion === question ? 'selected' : ''}`}
              onClick={() => handleQuestionSelect(question)}
            >
              {question}
            </button>
          ))}
        </div>
      </div>

      <div className="custom-question-section">
        <h3>✍️ Ask Your Own Question</h3>
        <div className="question-input-container">
          <textarea
            value={customQuestion}
            onChange={(e) => setCustomQuestion(e.target.value)}
            placeholder="Type your education-related question here..."
            className="question-input"
            rows={3}
          />
          <button
            onClick={handleAskQuestion}
            disabled={!customQuestion.trim() || loading}
            className="ask-btn"
          >
            {loading ? '🤔 Thinking...' : '🚀 Ask AI'}
          </button>
        </div>
      </div>

      {aiResponse && (
        <div className="ai-response-section">
          <h3>🎯 AI Response</h3>
          <div className="ai-response">
            <div className="response-header">
              <span className="question-label">Question:</span>
              <p className="asked-question">{customQuestion}</p>
            </div>
            <div className="response-content">
              <span className="answer-label">Answer:</span>
              <div className="ai-answer">
                {aiResponse.split('\n').map((paragraph, index) => (
                  <p key={index}>{paragraph}</p>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {!analysisData && (
        <div className="no-analysis-warning">
          <p>⚠️ Complete your technical analysis first to get more accurate AI responses.</p>
        </div>
      )}
    </div>
  );
};

export default AIQuestionsTab;