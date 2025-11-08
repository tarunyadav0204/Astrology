import React, { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import BirthForm from '../BirthForm/BirthForm';
import { useAstrology } from '../../context/AstrologyContext';

import './ChatModal.css';

const ChatModal = ({ isOpen, onClose, initialBirthData = null }) => {
    const { birthData, setBirthData } = useAstrology();
    const [showBirthForm, setShowBirthForm] = useState(!birthData && !initialBirthData);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const messagesEndRef = useRef(null);
    
    // Use initial birth data if provided
    useEffect(() => {
        if (initialBirthData) {
            setBirthData(initialBirthData);
            setShowBirthForm(false);
        }
    }, [initialBirthData, setBirthData]);

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
            // Add greeting message if no existing messages
            if (messages.length === 0) {
                addGreetingMessage();
            }
        }
    }, [birthData]);
    
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
            const response = await fetch('/api/chat/history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(birthData)
            });
            const data = await response.json();
            const existingMessages = data.messages || [];
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

    const createSession = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/chat/session', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                setSessionId(data.session_id);
                return data.session_id;
            }
        } catch (error) {
            console.error('Error creating session:', error);
        }
        return null;
    };

    const saveMessage = async (sessionId, sender, content) => {
        try {
            const token = localStorage.getItem('token');
            await fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    sender: sender,
                    content: content
                })
            });
        } catch (error) {
            console.error('Error saving message:', error);
        }
    };

    const handleSendMessage = async (message) => {
        if (!birthData) return;

        // Create session if first message
        let currentSessionId = sessionId;
        if (!currentSessionId) {
            currentSessionId = await createSession();
            if (!currentSessionId) return;
        }

        const userMessage = { role: 'user', content: message, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMessage]);
        
        // Save user message
        await saveMessage(currentSessionId, 'user', message);
        
        setTimeout(scrollToBottom, 100);
        setIsLoading(true);

        // Add typing indicator with engaging messages
        const loadingMessages = [
            '🔮 Analyzing your birth chart...',
            '⭐ Consulting the cosmic energies...',
            '📊 Calculating planetary positions...',
            '🌟 Interpreting astrological patterns...',
            '✨ Preparing your personalized insights...',
            '🌙 Reading lunar influences...',
            '☀️ Examining solar aspects...',
            '♃ Studying Jupiter blessings...',
            '♀ Analyzing Venus placements...',
            '♂ Checking Mars energy...',
            '☿ Decoding Mercury messages...',
            '♄ Understanding Saturn lessons...',
            '🐉 Exploring Rahu-Ketu axis...',
            '🏠 Examining house strengths...',
            '🔄 Calculating dasha periods...',
            '🎯 Identifying key yogas...',
            '🌊 Flowing through nakshatras...',
            '⚖️ Balancing planetary forces...',
            '🎭 Unveiling karmic patterns...',
            '🗝️ Unlocking hidden potentials...'
        ];
        
        // Add initial typing message
        const typingMessageId = Date.now();
        const typingMessage = { 
            id: typingMessageId,
            role: 'assistant', 
            content: loadingMessages[0], 
            timestamp: new Date().toISOString(),
            isTyping: true
        };
        
        setMessages(prev => [...prev, typingMessage]);
        
        // Cycle through loading messages
        let currentIndex = 0;
        const loadingInterval = setInterval(() => {
            currentIndex = (currentIndex + 1) % loadingMessages.length;
            
            setMessages(prev => {
                return prev.map(msg => 
                    msg.id === typingMessageId 
                        ? { ...msg, content: loadingMessages[currentIndex] }
                        : msg
                );
            });
        }, 3000);

        try {
            console.log('Sending chat request:', { ...birthData, question: message });
            const response = await fetch('/api/chat/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...birthData, question: message })
            });

            console.log('Chat response status:', response.status);
            if (!response.ok) {
                console.error('Chat API error:', response.status, response.statusText);
                throw new Error(`Chat API error: ${response.status} ${response.statusText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            // Clear loading interval
            clearInterval(loadingInterval);
            
            let assistantMessage = { 
                id: Date.now(),
                role: 'assistant', 
                content: '', 
                timestamp: new Date().toISOString() 
            };
            
            // Replace typing message with actual response
            setMessages(prev => {
                return prev.map(msg => 
                    msg.id === typingMessageId 
                        ? assistantMessage
                        : msg
                );
            });

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6).trim();
                        if (data === '[DONE]') break;
                        if (data && data.length > 0) {
                            try {
                                const cleanData = data.replace(/&quot;/g, '"').replace(/&amp;/g, '&');
                                const parsed = JSON.parse(cleanData);
                                
                                if (parsed.status === 'complete' && parsed.response) {
                                    const responseText = parsed.response.trim();
                                    if (responseText.length > 0) {
                                        assistantMessage.content = responseText;
                                        setMessages(prev => {
                                            return prev.map(msg => 
                                                msg.id === assistantMessage.id 
                                                    ? { ...assistantMessage }
                                                    : msg
                                            );
                                        });
                                        await saveMessage(currentSessionId, 'assistant', responseText);
                                    }
                                } else if (parsed.status === 'error') {
                                    assistantMessage.content = `Sorry, I encountered an error: ${parsed.error || 'Unknown error'}. Please try again.`;
                                    setMessages(prev => {
                                        return prev.map(msg => 
                                            msg.id === assistantMessage.id 
                                                ? { ...assistantMessage }
                                                : msg
                                        );
                                    });
                                }
                            } catch (e) {
                                const statusMatch = data.match(/"status"\s*:\s*"([^"]+)"/);
                                const responseMatch = data.match(/"response"\s*:\s*"((?:[^"\\]|\\.)*)"/);
                                
                                if (statusMatch && responseMatch && statusMatch[1] === 'complete') {
                                    const response = responseMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"');
                                    assistantMessage.content = response;
                                    setMessages(prev => {
                                        return prev.map(msg => 
                                            msg.id === assistantMessage.id 
                                                ? { ...assistantMessage }
                                                : msg
                                        );
                                    });
                                    await saveMessage(currentSessionId, 'assistant', response);
                                }
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            clearInterval(loadingInterval);
            
            let errorMessage = 'Sorry, I encountered an error. Please try again.';
            
            if (error.message.includes('404')) {
                errorMessage = 'Chat service is temporarily unavailable. Please try again later.';
            } else if (error.message.includes('500')) {
                errorMessage = 'Server error occurred. Please try again in a few moments.';
            } else if (error.message.includes('Network')) {
                errorMessage = 'Network connection issue. Please check your internet and try again.';
            }
            
            setMessages(prev => {
                return prev.map(msg => 
                    msg.id === typingMessageId 
                        ? { 
                            id: Date.now(),
                            role: 'assistant', 
                            content: errorMessage, 
                            timestamp: new Date().toISOString() 
                        }
                        : msg
                );
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleBirthFormSubmit = () => {
        setShowBirthForm(false);
    };

    if (!isOpen) return null;

    return (
        <div className="chat-modal-overlay" onClick={onClose}>
            <div className="chat-modal" onClick={(e) => e.stopPropagation()}>
                <div className="chat-modal-header">
                    <h2>AstroRoshni - Your Personal Astrologer</h2>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: 'auto' }}>
                        <button 
                            onClick={() => setShowBirthForm(true)}
                            style={{
                                background: 'rgba(255,255,255,0.2)',
                                border: '1px solid rgba(255,255,255,0.3)',
                                color: 'white',
                                padding: '6px 12px',
                                borderRadius: '6px',
                                fontSize: '12px',
                                cursor: 'pointer'
                            }}
                        >
                            👤 Change Person
                        </button>

                        <button className="close-btn" onClick={onClose}>×</button>
                    </div>
                </div>
                
                <div className="chat-modal-content">
                    {showBirthForm ? (
                        <div className="birth-form-container">
                            <BirthForm 
                                onSubmit={handleBirthFormSubmit}
                                onLogout={() => {}}
                            />
                        </div>
                    ) : (
                        <>
                            <div className="chat-messages">
                                <MessageList messages={messages} />
                            </div>
                            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ChatModal;