import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import BirthForm from '../BirthForm/BirthForm';
import { useAstrology } from '../../context/AstrologyContext';
import './ChatPage.css';

const ChatPage = () => {
    const location = useLocation();
    const { birthData } = useAstrology();
    const { birthData: initialBirthData } = location.state || {};
    const [showBirthForm, setShowBirthForm] = useState(!birthData && !initialBirthData);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
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

    const handleSendMessage = async (message) => {
        if (!birthData) return;

        const userMessage = { role: 'user', content: message, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);

        try {
            const response = await fetch('/api/chat/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...birthData, question: message })
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = { role: 'assistant', content: '', timestamp: new Date().toISOString() };
            
            setMessages(prev => [...prev, assistantMessage]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') break;
                        if (data.startsWith('{')) {
                            try {
                                const parsed = JSON.parse(data);
                                if (parsed.content) {
                                    assistantMessage.content += parsed.content;
                                    setMessages(prev => {
                                        const newMessages = [...prev];
                                        newMessages[newMessages.length - 1] = { ...assistantMessage };
                                        return newMessages;
                                    });
                                }
                            } catch (e) {
                                console.error('Error parsing chunk:', e);
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: 'Sorry, I encountered an error. Please try again.', 
                timestamp: new Date().toISOString() 
            }]);
        } finally {
            setIsLoading(false);
        }
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
                <h1>Astrological Consultation</h1>
                <p>Ask me anything about your birth chart and life guidance</p>
            </div>
            <div className="chat-container">
                <MessageList messages={messages} />
                <div ref={messagesEndRef} />
            </div>
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
    );
};

export default ChatPage;