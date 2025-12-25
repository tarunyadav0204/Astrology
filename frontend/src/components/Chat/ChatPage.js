import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import BirthForm from '../BirthForm/BirthForm';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import CreditsModal from '../Credits/CreditsModal';
import ContextModal from './ContextModal';
import PartnerChartModal from './PartnerChartModal';
import { authService } from '../../services/authService';
import './ChatPage.css';

// Enable detailed logging for debugging
// console.log('ChatPage component loaded - debugging enabled');

const ChatPage = () => {
    const location = useLocation();
    const { birthData } = useAstrology();
    const { credits, chatCost, partnershipCost, fetchBalance } = useCredits();
    const { birthData: initialBirthData } = location.state || {};
    const [showBirthForm, setShowBirthForm] = useState(!birthData && !initialBirthData);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showCreditsModal, setShowCreditsModal] = useState(false);
    const [showContextModal, setShowContextModal] = useState(false);
    const [contextData, setContextData] = useState(null);
    const [isAdmin, setIsAdmin] = useState(false);
    const [isPartnershipMode, setIsPartnershipMode] = useState(false);
    const [selectedPartnerChart, setSelectedPartnerChart] = useState(null);
    const [showPartnerModal, setShowPartnerModal] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (birthData) {
            setShowBirthForm(false);
            loadChatHistory();
        }
    }, [birthData]);
    
    // Check token validity and user role on component mount
    useEffect(() => {
        const checkTokenValidity = async () => {
            const token = localStorage.getItem('token');
            // console.log('🔍 Checking token and admin status...');
            if (token) {
                try {
                    const response = await fetch('/api/me', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (response.status === 401) {
                        // console.log('🔐 Invalid token detected, clearing auth...');
                        localStorage.removeItem('token');
                        localStorage.removeItem('user');
                        window.location.href = '/login';
                    } else if (response.ok) {
                        const userData = await response.json();
                        // console.log('👤 User data:', userData);
                        // console.log('🔑 User role:', userData.role);
                        // console.log('👑 Is admin?', userData.role === 'admin');
                        setIsAdmin(userData.role === 'admin');
                    }
                } catch (error) {
                    console.log('Token validation failed:', error);
                }
            } else {
                console.log('❌ No token found');
            }
        };
        checkTokenValidity();
    }, []);
    
    const addGreetingMessage = () => {
        const place = birthData.place && !birthData.place.includes(',') ? birthData.place : `${birthData.latitude}, ${birthData.longitude}`;
        const greetingMessage = {
            role: 'assistant',
            content: `Hello ${birthData.name}! I see you were born on ${new Date(birthData.date).toLocaleDateString()} at ${place}. I'm here to help you understand your birth chart and provide astrological guidance. What would you like to know about your cosmic blueprint?`,
            timestamp: new Date().toISOString()
        };
        setMessages([greetingMessage]);
    };

    const loadChatHistory = async () => {
        try {
            // console.log('Loading chat history for:', birthData);
            const token = localStorage.getItem('token');
            const response = await fetch('/api/chat/history', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify(birthData)
            });
            
            if (!response.ok) {
                // console.error('History response error:', response.status, response.statusText);
            }
            
            const data = await response.json();
            // console.log('Chat history response:', data);
            const existingMessages = data.history || data.messages || [];
            setMessages(existingMessages);
            
            // Add greeting if no existing messages
            if (existingMessages.length === 0) {
                addGreetingMessage();
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
            // Add greeting on error too
            addGreetingMessage();
        }
    };

    const handleSendMessage = async (message, options = {}) => {
        if (!birthData) return;

        const userMessage = { role: 'user', content: message, timestamp: new Date().toISOString(), messageId: Date.now() };
        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);

        try {
            // console.log('Sending chat request:', { ...birthData, question: message });
            
            const token = localStorage.getItem('token');
            // console.log('Token exists:', !!token);
            // console.log('Token preview:', token ? token.substring(0, 20) + '...' : 'No token');
            
            const requestBody = { ...birthData, question: message };
            if (isAdmin) {
                requestBody.include_context = true;
            }
            if (options.premium_analysis) {
                requestBody.premium_analysis = true;
            }
            if (isPartnershipMode && selectedPartnerChart) {
                requestBody.partnership_mode = true;
                requestBody.partner_data = {
                    name: selectedPartnerChart.name,
                    date: selectedPartnerChart.date,
                    time: selectedPartnerChart.time,
                    latitude: selectedPartnerChart.latitude,
                    longitude: selectedPartnerChart.longitude,
                    timezone: selectedPartnerChart.timezone
                };
            }
            
            const response = await fetch('/api/chat/ask', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify(requestBody)
            });

            // console.log('Response status:', response.status, response.statusText);
            // console.log('Response headers:', Object.fromEntries(response.headers.entries()));
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Response error:', errorText);
                console.error('Full response details:', {
                    status: response.status,
                    statusText: response.statusText,
                    url: response.url,
                    headers: Object.fromEntries(response.headers.entries()),
                    body: errorText
                });
                
                // If 401 Unauthorized, token is invalid - clear auth and redirect to login
                if (response.status === 401) {
                    console.log('🔐 401 error detected - invalid token, clearing auth...');
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    
                    // Show user-friendly message before redirect
                    setMessages(prev => {
                        const filtered = prev.filter(msg => !(msg.role === 'assistant' && !msg.content.trim()));
                        return [...filtered, { 
                            role: 'assistant', 
                            content: "Your session has expired. Please log in again to continue.", 
                            timestamp: new Date().toISOString() 
                        }];
                    });
                    
                    // Redirect to login after a short delay
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                    return;
                }
                
                // If 402 Payment Required, refresh credit balance
                if (response.status === 402) {
                    console.log('🔄 402 error detected, refreshing credit balance...');
                    fetchBalance();
                }
                
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = { role: 'assistant', content: '', timestamp: new Date().toISOString(), messageId: Date.now() + 1 };
            
            setMessages(prev => [...prev, assistantMessage]);
            let hasReceivedContent = false;
            let streamTimeout;
            
            // Mobile-friendly timeout for streaming
            const resetTimeout = () => {
                if (streamTimeout) clearTimeout(streamTimeout);
                streamTimeout = setTimeout(() => {
                    console.warn('Stream timeout - mobile network issue detected');
                    if (!hasReceivedContent) {
                        throw new Error('Stream timeout - please try again');
                    }
                }, 30000); // 30 second timeout
            };
            
            resetTimeout();

            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    resetTimeout(); // Reset timeout on each chunk

                    const chunk = decoder.decode(value, { stream: true });
                    console.log('Received chunk:', chunk);
                    const lines = chunk.split('\n').filter(line => line.trim());

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6).trim();
                            console.log('Processing data:', data);
                            
                            if (data === '[DONE]') break;
                            if (data && data.startsWith('{')) {
                                try {
                                    const parsed = JSON.parse(data);
                                    console.log('Parsed data:', parsed);
                                    
                                    if (parsed.status === 'complete' && parsed.response) {
                                        assistantMessage.content = parsed.response;
                                        hasReceivedContent = true;
                                        if (isAdmin && parsed.context) {
                                            setContextData(parsed.context);
                                        }
                                        setMessages(prev => {
                                            const newMessages = [...prev];
                                            newMessages[newMessages.length - 1] = { ...assistantMessage };
                                            return newMessages;
                                        });
                                        clearTimeout(streamTimeout);
                                        break;
                                    } else if (parsed.status === 'error') {
                                        clearTimeout(streamTimeout);
                                        throw new Error(parsed.error || 'AI analysis failed');
                                    } else if (parsed.content) {
                                        assistantMessage.content += parsed.content;
                                        hasReceivedContent = true;
                                        setMessages(prev => {
                                            const newMessages = [...prev];
                                            newMessages[newMessages.length - 1] = { ...assistantMessage };
                                            return newMessages;
                                        });
                                    }
                                } catch (parseError) {
                                    console.error('Error parsing chunk:', parseError, 'Data:', data);
                                }
                            }
                        }
                    }
                }
            } finally {
                clearTimeout(streamTimeout);
            }
            
            // Final validation
            if (!hasReceivedContent || !assistantMessage.content.trim()) {
                console.error('Empty response detected:', { hasReceivedContent, content: assistantMessage.content });
                throw new Error('Empty response received - please try again');
            }
            
            // Update credit balance after successful response
            fetchBalance();
        } catch (error) {
            console.error('Complete error details:', {
                message: error.message,
                stack: error.stack,
                birthData: birthData,
                question: message,
                userAgent: navigator.userAgent,
                isMobile: /Mobi|Android/i.test(navigator.userAgent),
                hasToken: !!localStorage.getItem('token'),
                tokenPreview: localStorage.getItem('token') ? localStorage.getItem('token').substring(0, 20) + '...' : 'No token'
            });
            
            // Show generic user-friendly error messages
            let errorMessage = "I'm having trouble processing your question right now. Please try again in a moment.";
            
            if (error.message.includes('quota') || error.message.includes('rate limit')) {
                errorMessage = "I'm receiving too many requests right now. Please wait a moment and try again.";
            } else if (error.message.includes('network') || error.message.includes('connection')) {
                errorMessage = "Please check your internet connection and try again.";
            } else if (error.message.includes('timeout')) {
                errorMessage = "Your request is taking longer than expected. Please try again.";
            }
            
            // Remove empty assistant message if it exists
            setMessages(prev => {
                const filtered = prev.filter(msg => !(msg.role === 'assistant' && !msg.content.trim()));
                return [...filtered, { 
                    role: 'assistant', 
                    content: errorMessage, 
                    timestamp: new Date().toISOString() 
                }];
            });
        } finally {
            setIsLoading(false);
            // Ensure no empty bubbles remain
            setTimeout(() => {
                setMessages(prev => prev.filter(msg => !(msg.role === 'assistant' && !msg.content.trim())));
            }, 1000);
        }
    };

    const handlePartnershipToggle = () => {
        if (!isPartnershipMode) {
            setShowPartnerModal(true);
        } else {
            setIsPartnershipMode(false);
            setSelectedPartnerChart(null);
        }
    };

    const handleSelectPartner = (chart) => {
        setSelectedPartnerChart(chart);
        setIsPartnershipMode(true);
    };

    const handleDeleteMessage = (messageId) => {
        setMessages(prev => prev.filter(msg => msg.messageId !== messageId));
    };

    const handleBirthFormSubmit = () => {
        setShowBirthForm(false);
    };

    if (showBirthForm) {
        return (
            <div className="chat-page">
                <BirthForm 
                    onSubmit={handleBirthFormSubmit}
                    onLogout={() => {}}
                />
            </div>
        );
    }

    return (
        <div className="chat-page">
            <div className="chat-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '10px' }}>
                    <div style={{ flex: '1 1 auto', minWidth: '200px' }}>
                        <h1 style={{ margin: 0 }}>
                            AstroRoshni {isPartnershipMode && selectedPartnerChart 
                                ? `${birthData?.name} & ${selectedPartnerChart.name}` 
                                : birthData?.name ? `with ${birthData.name}` : 'Consultation'
                            }
                        </h1>
                        <div style={{ fontSize: '10px', color: '#999' }}>
                            {isPartnershipMode ? '💕 Partnership Mode' : 'Individual Mode'} | Admin: {isAdmin ? 'Yes' : 'No'}
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <button 
                            onClick={() => {
                                console.log('Partnership button clicked!');
                                handlePartnershipToggle();
                            }}
                            style={{
                                background: isPartnershipMode ? 'linear-gradient(45deg, #ff6b35, #f7931e)' : 'red',
                                padding: '8px 12px',
                                borderRadius: '20px',
                                fontSize: '11px',
                                fontWeight: 'bold',
                                color: 'white',
                                border: `2px solid ${isPartnershipMode ? '#ff6b35' : 'black'}`,
                                cursor: 'pointer',
                                whiteSpace: 'nowrap',
                                zIndex: 9999,
                                position: 'relative'
                            }}
                        >
                            💕 {isPartnershipMode ? 'Exit Partnership' : 'Partnership Mode'}
                        </button>
                        <button 
                            onClick={() => setShowContextModal(true)}
                            style={{
                                background: 'white',
                                padding: '8px 12px',
                                borderRadius: '20px',
                                fontSize: '11px',
                                fontWeight: 'bold',
                                color: 'black',
                                border: '2px solid black',
                                cursor: 'pointer',
                                whiteSpace: 'nowrap'
                            }}
                        >
                            📄 MENU
                        </button>
                        <div className="credits-display" style={{
                            background: 'rgba(255,107,53,0.1)',
                            padding: '6px 10px',
                            borderRadius: '15px',
                            fontSize: '11px',
                            fontWeight: 'bold',
                            color: '#ff6b35',
                            border: '1px solid rgba(255,107,53,0.3)',
                            whiteSpace: 'nowrap'
                        }}>
                            <span className="credits-full">💳 {credits} | {isPartnershipMode ? partnershipCost : chatCost} per question</span>
                            <span className="credits-short">💳 {credits} Credits</span>
                        </div>
                    </div>
                </div>
                <p>{isPartnershipMode ? 'Ask about your compatibility and relationship guidance' : 'Ask me anything about your birth chart and life guidance'}</p>
            </div>
            <div className="chat-container">
                <MessageList 
                    messages={messages} 
                    onDeleteMessage={handleDeleteMessage}
                />
                <div ref={messagesEndRef} />
            </div>
            <ChatInput 
                onSendMessage={handleSendMessage} 
                isLoading={isLoading} 
                onOpenCreditsModal={() => setShowCreditsModal(true)}
                isPartnershipMode={isPartnershipMode}
            />
            
            {/* Credits Modal */}
            <CreditsModal 
                isOpen={showCreditsModal} 
                onClose={() => setShowCreditsModal(false)} 
            />
            
            {/* Context Modal for Admin */}
            <ContextModal 
                isOpen={showContextModal}
                onClose={() => setShowContextModal(false)}
                contextData={contextData}
            />
            
            {/* Partner Chart Selection Modal */}
            <PartnerChartModal 
                isOpen={showPartnerModal}
                onClose={() => setShowPartnerModal(false)}
                onSelectPartner={handleSelectPartner}
            />
        </div>
    );
};

export default ChatPage;