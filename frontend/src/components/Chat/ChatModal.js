import React, { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import BirthForm from '../BirthForm/BirthForm';
import { useAstrology } from '../../context/AstrologyContext';
import { showToast } from '../../utils/toast';

import './ChatModal.css';

const ChatModal = ({ isOpen, onClose, initialBirthData = null, onChartRefClick: parentChartRefClick }) => {
    const { birthData, setBirthData } = useAstrology();
    const [showBirthForm, setShowBirthForm] = useState(!birthData && !initialBirthData);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [language, setLanguage] = useState('english');
    const [responseStyle, setResponseStyle] = useState('detailed');
    const [showMobileMenu, setShowMobileMenu] = useState(false);
    const [hoveredMessage, setHoveredMessage] = useState(null);
    const [buttonPosition, setButtonPosition] = useState({ top: 0, left: 0 });
    const [copySuccess, setCopySuccess] = useState(false);
    
    const getNextLanguage = (current) => {
        const languages = ['english', 'hindi', 'telugu', 'gujarati', 'tamil'];
        const currentIndex = languages.indexOf(current);
        return languages[(currentIndex + 1) % languages.length];
    };
    
    const getLanguageDisplay = (lang) => {
        switch(lang) {
            case 'english': return '🇺🇸 English';
            case 'hindi': return '🇮🇳 हिंदी';
            case 'telugu': return '🇮🇳 తెలుగు';
            case 'gujarati': return '🇮🇳 ગુજરાતી';
            case 'tamil': return '🇮🇳 தமிழ்';
            default: return '🇺🇸 English';
        }
    };
    
    const downloadChatPDF = async () => {
        // Check if chat contains non-English content
        const hasNonEnglish = messages.some(msg => 
            /[\u0900-\u097F]|[\u0C00-\u0C7F]|[\u0A80-\u0AFF]|[\u0B80-\u0BFF]/.test(msg.content)
        );
        
        if (hasNonEnglish) {
            // For non-English content, use text download for better Unicode support
            const chatContent = messages.map(msg => {
                const role = msg.role === 'user' ? 'You' : 'AstroRoshni';
                const content = msg.content.replace(/\*\*(.*?)\*\*/g, '$1').replace(/\*(.*?)\*/g, '$1').replace(/###\s*(.*?)$/gm, '$1');
                return `${role}: ${content}`;
            }).join('\n\n');
            
            const element = document.createElement('a');
            const file = new Blob([chatContent], {type: 'text/plain; charset=utf-8'});
            element.href = URL.createObjectURL(file);
            element.download = `astrology-chat-${new Date().toISOString().split('T')[0]}.txt`;
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
            setShowMobileMenu(false);
            return;
        }
        
        try {
            // Load jsPDF from CDN for English content only
            if (!window.jsPDF) {
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
                document.head.appendChild(script);
                
                await new Promise((resolve, reject) => {
                    script.onload = resolve;
                    script.onerror = reject;
                });
            }
            
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            const pageWidth = doc.internal.pageSize.getWidth();
            const pageHeight = doc.internal.pageSize.getHeight();
            const margin = 20;
            const maxWidth = pageWidth - 2 * margin;
            let yPosition = margin;
            
            // Simple header
            doc.setFontSize(16);
            doc.setFont(undefined, 'bold');
            doc.setTextColor(0, 0, 0);
            doc.text('AstroRoshni - Astrology Chat', margin, yPosition);
            yPosition += 10;
            
            doc.setFontSize(10);
            doc.setFont(undefined, 'normal');
            doc.text(`Generated on: ${new Date().toLocaleDateString()}`, margin, yPosition);
            
            if (birthData?.name) {
                yPosition += 6;
                doc.text(`For: ${birthData.name}`, margin, yPosition);
            }
            
            yPosition += 15;
            
            // Messages - simple like chat modal
            for (const msg of messages) {
                if (yPosition > pageHeight - 30) {
                    doc.addPage();
                    yPosition = margin;
                }
                
                const role = msg.role === 'user' ? 'You' : 'AstroRoshni';
                const content = msg.content
                    .replace(/\*\*(.*?)\*\*/g, '$1')
                    .replace(/\*(.*?)\*/g, '$1')
                    .replace(/###\s*(.*?)$/gm, '$1');
                
                // Message bubble background - like chat modal
                const bubbleHeight = Math.max(20, doc.splitTextToSize(content, maxWidth - 20).length * 5 + 15);
                
                if (msg.role === 'user') {
                    // User message - white background with orange left border
                    doc.setFillColor(255, 255, 255);
                    doc.rect(margin, yPosition - 5, maxWidth, bubbleHeight, 'F');
                    doc.setDrawColor(255, 107, 53);
                    doc.setLineWidth(2);
                    doc.line(margin, yPosition - 5, margin, yPosition - 5 + bubbleHeight);
                } else {
                    // Assistant message - light transparent background
                    doc.setFillColor(245, 245, 245);
                    doc.rect(margin, yPosition - 5, maxWidth, bubbleHeight, 'F');
                }
                
                // Role header
                doc.setFontSize(11);
                doc.setFont(undefined, 'bold');
                doc.setTextColor(msg.role === 'user' ? 51 : 0, msg.role === 'user' ? 51 : 0, msg.role === 'user' ? 51 : 0);
                doc.text(`${role}:`, margin + 5, yPosition + 5);
                yPosition += 12;
                
                // Message content
                doc.setFont(undefined, 'normal');
                doc.setFontSize(10);
                doc.setTextColor(0, 0, 0);
                
                const lines = doc.splitTextToSize(content, maxWidth - 20);
                for (const line of lines) {
                    if (yPosition > pageHeight - 20) {
                        doc.addPage();
                        yPosition = margin;
                    }
                    doc.text(line, margin + 5, yPosition);
                    yPosition += 5;
                }
                
                yPosition += 15;
            }
            
            // Footer
            const totalPages = doc.internal.getNumberOfPages();
            for (let i = 1; i <= totalPages; i++) {
                doc.setPage(i);
                doc.setFontSize(8);
                doc.setTextColor(128, 128, 128);
                doc.text(`Page ${i} of ${totalPages}`, pageWidth - 40, pageHeight - 10);
            }
            
            doc.save(`astrology-chat-${new Date().toISOString().split('T')[0]}.pdf`);
            setShowMobileMenu(false);
        } catch (error) {
            console.error('PDF generation failed:', error);
            // Fallback to text download
            const chatContent = messages.map(msg => {
                const role = msg.role === 'user' ? 'You' : 'AstroRoshni';
                const content = msg.content.replace(/\*\*(.*?)\*\*/g, '$1').replace(/\*(.*?)\*/g, '$1').replace(/###\s*(.*?)$/gm, '$1');
                return `${role}: ${content}`;
            }).join('\n\n');
            
            const element = document.createElement('a');
            const file = new Blob([chatContent], {type: 'text/plain'});
            element.href = URL.createObjectURL(file);
            element.download = `astrology-chat-${new Date().toISOString().split('T')[0]}.txt`;
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
            setShowMobileMenu(false);
        }
    };
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

        // Retry function with exponential backoff
        const retryRequest = async (attempt = 1) => {
            try {
                console.log(`Sending chat request (attempt ${attempt}):`, { ...birthData, question: message, language, response_style: responseStyle });
                
                // Update loading message for retries
                if (attempt > 1) {
                    setMessages(prev => {
                        return prev.map(msg => 
                            msg.id === typingMessageId 
                                ? { ...msg, content: `🔄 Server busy, retrying... (attempt ${attempt} of 3)` }
                                : msg
                        );
                    });
                }
                
                const response = await fetch('/api/chat/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ...birthData, question: message, language, response_style: responseStyle })
                });

                console.log('Chat response status:', response.status);
                
                // Check for server errors that should trigger retry
                if (response.status === 502 || response.status === 503 || response.status === 504) {
                    throw new Error(`Server error: ${response.status}`);
                }
                
                if (!response.ok) {
                    console.error('Chat API error:', response.status, response.statusText);
                    throw new Error(`Chat API error: ${response.status} ${response.statusText}`);
                }
                
                return response;
            } catch (error) {
                const isRetryableError = error.message.includes('502') || 
                                       error.message.includes('503') || 
                                       error.message.includes('504') || 
                                       error.message.includes('upstream') ||
                                       error.message.includes('Network') ||
                                       error.message.includes('fetch');
                
                if (isRetryableError && attempt < 3) {
                    const delay = Math.min(1000 * Math.pow(2, attempt - 1), 4000); // 1s, 2s, 4s
                    console.log(`Retrying in ${delay}ms due to:`, error.message);
                    
                    // Show retry message
                    setMessages(prev => {
                        return prev.map(msg => 
                            msg.id === typingMessageId 
                                ? { ...msg, content: `⏳ Connection issue detected, retrying in ${delay/1000}s...` }
                                : msg
                        );
                    });
                    
                    await new Promise(resolve => setTimeout(resolve, delay));
                    return retryRequest(attempt + 1);
                }
                throw error;
            }
        };
        
        try {
            const response = await retryRequest();

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
            
            let messageAdded = false;

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
                                // Decode HTML entities in the raw data
                                const decodeHtmlEntities = (text) => {
                                    const textarea = document.createElement('textarea');
                                    textarea.innerHTML = text;
                                    return textarea.value;
                                };
                                
                                // First try to parse as-is, then decode if needed
                                let parsed;
                                try {
                                    parsed = JSON.parse(data);
                                } catch (parseError) {
                                    // If direct parsing fails, try decoding first
                                    const decodedData = decodeHtmlEntities(data);
                                    parsed = JSON.parse(decodedData);
                                }
                                
                                if (parsed.status === 'complete' && parsed.response) {
                                    // Decode HTML entities in the response content
                                    let responseText = parsed.response;
                                    
                                    // Check if response contains HTML entities and decode them
                                    if (responseText.includes('&lt;') || responseText.includes('&gt;') || responseText.includes('&quot;') || responseText.includes('&#39;')) {
                                        responseText = decodeHtmlEntities(responseText);
                                    }
                                    
                                    responseText = responseText.trim();
                                    
                                    // Debug for production
                                    if (window.location.hostname === 'astroroshni.com') {
                                        console.log('PROD - Response text length:', responseText.length);
                                        console.log('PROD - messageAdded flag:', messageAdded);
                                        console.log('PROD - assistantMessage ID:', assistantMessage.id);
                                        console.log('PROD - typingMessageId:', typingMessageId);
                                    }
                                    
                                    if (responseText.length > 0) {
                                        assistantMessage.content = responseText;
                                        
                                        if (!messageAdded) {
                                            // Replace typing message with actual response
                                            setMessages(prev => {
                                                const updated = prev.map(msg => 
                                                    msg.id === typingMessageId 
                                                        ? { ...assistantMessage }
                                                        : msg
                                                );
                                                
                                                if (window.location.hostname === 'astroroshni.com') {
                                                    console.log('PROD - Updated messages count:', updated.length);
                                                    console.log('PROD - Assistant message in array:', updated.find(m => m.id === assistantMessage.id));
                                                }
                                                
                                                return updated;
                                            });
                                            messageAdded = true;
                                        } else {
                                            // Update existing message
                                            setMessages(prev => {
                                                return prev.map(msg => 
                                                    msg.id === assistantMessage.id 
                                                        ? { ...assistantMessage }
                                                        : msg
                                                );
                                            });
                                        }
                                        await saveMessage(currentSessionId, 'assistant', responseText);
                                    }
                                } else if (parsed.status === 'error') {
                                    assistantMessage.content = `Sorry, I encountered an error: ${parsed.error || 'Unknown error'}. Please try again.`;
                                    
                                    if (!messageAdded) {
                                        setMessages(prev => {
                                            return prev.map(msg => 
                                                msg.id === typingMessageId 
                                                    ? { ...assistantMessage }
                                                    : msg
                                            );
                                        });
                                        messageAdded = true;
                                    }
                                }
                            } catch (e) {
                                const statusMatch = data.match(/"status"\s*:\s*"([^"]+)"/);
                                const responseMatch = data.match(/"response"\s*:\s*"((?:[^"\\]|\\.)*)"/);
                                
                                if (statusMatch && responseMatch && statusMatch[1] === 'complete') {
                                    let response = responseMatch[1]
                                        .replace(/\\n/g, '\n')
                                        .replace(/\\"/g, '"');
                                    
                                    // Check if response contains HTML entities and decode them
                                    if (response.includes('&lt;') || response.includes('&gt;') || response.includes('&quot;') || response.includes('&#39;')) {
                                        response = decodeHtmlEntities(response);
                                    }
                                    assistantMessage.content = response;
                                    
                                    if (!messageAdded) {
                                        setMessages(prev => {
                                            return prev.map(msg => 
                                                msg.id === typingMessageId 
                                                    ? { ...assistantMessage }
                                                    : msg
                                            );
                                        });
                                        messageAdded = true;
                                    }
                                    await saveMessage(currentSessionId, 'assistant', response);
                                }
                            }
                        }
                    }
                }
            }
            
            // If no message was added, remove the typing indicator
            if (!messageAdded) {
                setMessages(prev => prev.filter(msg => msg.id !== typingMessageId));
            }
        } catch (error) {
            console.error('Error sending message after retries:', error);
            clearInterval(loadingInterval);
            
            let errorMessage = 'Sorry, I encountered an error after multiple attempts. Please try again.';
            
            if (error.message.includes('502') || error.message.includes('503') || error.message.includes('upstream')) {
                errorMessage = 'Server is experiencing high load. Please try again in a few moments.';
            } else if (error.message.includes('404')) {
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

    // Cleanup speech when modal closes
    React.useEffect(() => {
        if (!isOpen) {
            window.speechSynthesis.cancel();
        }
    }, [isOpen]);
    
    // Close mobile menu when clicking outside
    React.useEffect(() => {
        const handleClickOutside = (event) => {
            if (showMobileMenu && !event.target.closest('.mobile-menu')) {
                setShowMobileMenu(false);
            }
        };
        
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showMobileMenu]);
    
    // Clear hovered message when mobile menu is open to prevent action buttons
    React.useEffect(() => {
        if (showMobileMenu) {
            setHoveredMessage(null);
        }
    }, [showMobileMenu]);
    
    const handleCopyMessage = async () => {
        if (!hoveredMessage) return;
        
        try {
            const cleanText = hoveredMessage.content
                .replace(/\*\*(.*?)\*\*/g, '$1')
                .replace(/\*(.*?)\*/g, '$1')
                .replace(/###\s*(.*?)$/gm, '$1')
                .replace(/<div class="quick-answer-card">(.*?)<\/div>/g, '$1')
                .replace(/<div class="final-thoughts-card">(.*?)<\/div>/g, '$1')
                .replace(/•\s*/g, '• ')
                .replace(/\n\s*\n/g, '\n\n')
                .trim();
                
            await navigator.clipboard.writeText(cleanText);
            setCopySuccess(true);
            showToast('Message copied!', 'success');
            setTimeout(() => setCopySuccess(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
            showToast('Copy failed', 'error');
        }
    };
    
    const [followUpQuestion, setFollowUpQuestion] = useState('');
    const [chartRefHighlight, setChartRefHighlight] = useState(null);
    
    const handleFollowUpClick = (question) => {
        setFollowUpQuestion(question);
    };
    
    const handleChartRefClick = (chartRef) => {
        // If parent has chart ref handler, use it (for Dashboard integration)
        if (parentChartRefClick) {
            parentChartRefClick(chartRef);
            return;
        }
        
        // Fallback: local handling with toast only
        setChartRefHighlight(chartRef);
        // Show notification to user about chart reference
        const { type, value } = chartRef;
        let message = '';
        if (type === 'planet') {
            message = `🪐 ${value.charAt(0).toUpperCase() + value.slice(1)} highlighted! Check your birth chart to see this planet's position.`;
        } else if (type === 'house') {
            message = `🏠 House ${value} highlighted! This represents specific life areas in your chart.`;
        } else if (type === 'sign') {
            const signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
            const signName = signs[parseInt(value) - 1] || value;
            message = `♈ ${signName} highlighted! This zodiac sign influences your personality and life path.`;
        }
        
        // Show toast notification
        import('../../utils/toast').then(({ showToast }) => {
            showToast(message, 'info');
        });
        
        // Auto-clear highlight after 5 seconds
        setTimeout(() => setChartRefHighlight(null), 5000);
    };
    
    if (!isOpen) return null;

    return (
        <>
        <div className="chat-modal-overlay" onClick={onClose}>
            <div className="chat-modal" onClick={(e) => e.stopPropagation()}>
                <div className="chat-modal-header">
                    <h2>AstroRoshni - Your Personal Astrologer</h2>
                    
                    {/* Desktop buttons */}
                    <div className="desktop-buttons" style={{ display: 'none' }}>
                        <button 
                            onClick={() => setResponseStyle(responseStyle === 'detailed' ? 'concise' : 'detailed')}
                            style={{
                                background: 'rgba(255,255,255,0.2)',
                                border: '1px solid rgba(255,255,255,0.3)',
                                color: 'white',
                                padding: '6px 12px',
                                borderRadius: '6px',
                                fontSize: '12px',
                                cursor: 'pointer',
                                position: 'absolute',
                                right: '650px',
                                top: '20px'
                            }}
                        >
                            {responseStyle === 'detailed' ? '⚡ Quick' : '📋 Detailed'}
                        </button>
                        <button 
                            onClick={() => setLanguage(getNextLanguage(language))}
                            style={{
                                background: 'rgba(255,255,255,0.2)',
                                border: '1px solid rgba(255,255,255,0.3)',
                                color: 'white',
                                padding: '6px 12px',
                                borderRadius: '6px',
                                fontSize: '12px',
                                cursor: 'pointer',
                                position: 'absolute',
                                right: '520px',
                                top: '20px'
                            }}
                        >
                            {getLanguageDisplay(getNextLanguage(language))}
                        </button>
                        <button 
                            onClick={downloadChatPDF}
                            style={{
                                background: 'rgba(255,255,255,0.2)',
                                border: '1px solid rgba(255,255,255,0.3)',
                                color: 'white',
                                padding: '6px 12px',
                                borderRadius: '6px',
                                fontSize: '12px',
                                cursor: 'pointer',
                                position: 'absolute',
                                right: '390px',
                                top: '20px'
                            }}
                        >
                            📄 Download PDF
                        </button>
                        <button 
                            onClick={() => {
                                const event = new CustomEvent('openChartModal');
                                window.dispatchEvent(event);
                            }}
                            style={{
                                background: 'rgba(255,255,255,0.2)',
                                border: '1px solid rgba(255,255,255,0.3)',
                                color: 'white',
                                padding: '6px 12px',
                                borderRadius: '6px',
                                fontSize: '12px',
                                cursor: 'pointer',
                                position: 'absolute',
                                right: '260px',
                                top: '20px'
                            }}
                        >
                            📊 View Chart
                        </button>
                        <button 
                            onClick={() => setShowBirthForm(true)}
                            style={{
                                background: 'rgba(255,255,255,0.2)',
                                border: '1px solid rgba(255,255,255,0.3)',
                                color: 'white',
                                padding: '6px 12px',
                                borderRadius: '6px',
                                fontSize: '12px',
                                cursor: 'pointer',
                                position: 'absolute',
                                right: '100px',
                                top: '20px'
                            }}
                        >
                            👤 Change Person
                        </button>
                    </div>
                    
                    {/* Mobile menu */}
                    <div className="mobile-menu">
                        <button 
                            onClick={() => setShowMobileMenu(!showMobileMenu)}
                            style={{
                                background: 'rgba(255,255,255,0.2)',
                                border: '1px solid rgba(255,255,255,0.3)',
                                color: 'white',
                                padding: '6px 8px',
                                borderRadius: '6px',
                                fontSize: '16px',
                                cursor: 'pointer',
                                position: 'absolute',
                                right: '70px',
                                top: '20px'
                            }}
                        >
                            ⋮
                        </button>
                    </div>
                    
                    <button className="close-btn" onClick={onClose}>×</button>
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
                                <MessageList 
                                    messages={messages} 
                                    language={language} 
                                    onMessageHover={(message, element) => {
                                        if (!showMobileMenu) {
                                            setHoveredMessage(message);
                                            if (message && element) {
                                                const rect = element.getBoundingClientRect();
                                                setButtonPosition({
                                                    top: rect.top + 5,
                                                    left: rect.left - 10
                                                });
                                            }
                                        }
                                    }}
                                    onFollowUpClick={handleFollowUpClick}
                                    onChartRefClick={handleChartRefClick}
                                />
                                {hoveredMessage && !showMobileMenu && (
                                    <button 
                                        className="floating-copy-btn"
                                        onClick={handleCopyMessage}
                                        onMouseEnter={() => setHoveredMessage(hoveredMessage)}
                                        title="Copy message"
                                        style={{
                                            position: 'fixed',
                                            top: `${buttonPosition.top}px`,
                                            left: `${buttonPosition.left}px`,
                                            zIndex: 10001,
                                            background: '#e91e63',
                                            color: 'white',
                                            border: 'none',
                                            padding: '6px 12px',
                                            borderRadius: '6px',
                                            fontSize: '12px',
                                            fontWeight: '600',
                                            cursor: 'pointer',
                                            width: 'auto',
                                            height: 'auto'
                                        }}
                                    >
                                        {copySuccess ? 'Copied!' : 'Copy'}
                                    </button>
                                )}
                            </div>
                            <ChatInput 
                                onSendMessage={handleSendMessage} 
                                isLoading={isLoading} 
                                followUpQuestion={followUpQuestion}
                                onFollowUpUsed={() => setFollowUpQuestion('')}
                            />
                        </>
                    )}
                </div>
            </div>
        </div>
        
        {/* Mobile dropdown rendered completely outside modal */}
        {showMobileMenu && (
            <div style={{
                position: 'fixed',
                right: '15px',
                top: '60px',
                background: 'rgba(255,255,255,0.95)',
                border: '1px solid rgba(0,0,0,0.1)',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                zIndex: 200000,
                minWidth: '150px',
                pointerEvents: 'auto'
            }}>
                    <button 
                        onClick={(e) => { e.stopPropagation(); setResponseStyle(responseStyle === 'detailed' ? 'concise' : 'detailed'); setShowMobileMenu(false); }}
                        onTouchEnd={(e) => { e.stopPropagation(); setResponseStyle(responseStyle === 'detailed' ? 'concise' : 'detailed'); setShowMobileMenu(false); }}
                        style={{
                            width: '100%',
                            padding: '10px 15px',
                            border: 'none',
                            background: 'transparent',
                            color: '#333',
                            fontSize: '12px',
                            cursor: 'pointer',
                            textAlign: 'left',
                            borderBottom: '1px solid rgba(0,0,0,0.1)',
                            touchAction: 'manipulation',
                            userSelect: 'none'
                        }}
                    >
                        {responseStyle === 'detailed' ? '⚡ Quick Mode' : '📋 Detailed Mode'}
                    </button>
                    <button 
                        onClick={(e) => {
                            e.stopPropagation();
                            const event = new CustomEvent('openChartModal');
                            window.dispatchEvent(event);
                            setShowMobileMenu(false);
                        }}
                        onTouchEnd={(e) => {
                            e.stopPropagation();
                            const event = new CustomEvent('openChartModal');
                            window.dispatchEvent(event);
                            setShowMobileMenu(false);
                        }}
                        style={{
                            width: '100%',
                            padding: '10px 15px',
                            border: 'none',
                            background: 'transparent',
                            color: '#333',
                            fontSize: '12px',
                            cursor: 'pointer',
                            textAlign: 'left',
                            borderBottom: '1px solid rgba(0,0,0,0.1)',
                            touchAction: 'manipulation',
                            userSelect: 'none'
                        }}
                    >
                        📊 View Chart
                    </button>
                    <button 
                        onClick={(e) => { e.stopPropagation(); setShowBirthForm(true); setShowMobileMenu(false); }}
                        onTouchEnd={(e) => { e.stopPropagation(); setShowBirthForm(true); setShowMobileMenu(false); }}
                        style={{
                            width: '100%',
                            padding: '10px 15px',
                            border: 'none',
                            background: 'transparent',
                            color: '#333',
                            fontSize: '12px',
                            cursor: 'pointer',
                            textAlign: 'left',
                            borderBottom: '1px solid rgba(0,0,0,0.1)',
                            touchAction: 'manipulation',
                            userSelect: 'none'
                        }}
                    >
                        👤 Change Person
                    </button>
                    <button 
                        onClick={(e) => { e.stopPropagation(); downloadChatPDF(); setShowMobileMenu(false); }}
                        onTouchEnd={(e) => { e.stopPropagation(); downloadChatPDF(); setShowMobileMenu(false); }}
                        style={{
                            width: '100%',
                            padding: '10px 15px',
                            border: 'none',
                            background: 'transparent',
                            color: '#333',
                            fontSize: '12px',
                            cursor: 'pointer',
                            textAlign: 'left',
                            borderBottom: '1px solid rgba(0,0,0,0.1)',
                            touchAction: 'manipulation',
                            userSelect: 'none'
                        }}
                    >
                        📄 Download Chat
                    </button>
                    <div>
                        <div style={{
                            padding: '10px 15px',
                            fontSize: '12px',
                            fontWeight: 'bold',
                            color: '#666'
                        }}>
                            🌐 Language
                        </div>
                        <button 
                            onClick={(e) => { e.stopPropagation(); setLanguage('english'); setShowMobileMenu(false); }}
                            onTouchEnd={(e) => { e.stopPropagation(); setLanguage('english'); setShowMobileMenu(false); }}
                            style={{
                                width: '100%',
                                padding: '8px 25px',
                                border: 'none',
                                background: language === 'english' ? 'rgba(255,107,53,0.1)' : 'transparent',
                                color: language === 'english' ? '#ff6b35' : '#333',
                                fontSize: '11px',
                                cursor: 'pointer',
                                textAlign: 'left',
                                touchAction: 'manipulation',
                                userSelect: 'none'
                            }}
                        >
                            🇺🇸 English
                        </button>
                        <button 
                            onClick={(e) => { e.stopPropagation(); setLanguage('hindi'); setShowMobileMenu(false); }}
                            onTouchEnd={(e) => { e.stopPropagation(); setLanguage('hindi'); setShowMobileMenu(false); }}
                            style={{
                                width: '100%',
                                padding: '8px 25px',
                                border: 'none',
                                background: language === 'hindi' ? 'rgba(255,107,53,0.1)' : 'transparent',
                                color: language === 'hindi' ? '#ff6b35' : '#333',
                                fontSize: '11px',
                                cursor: 'pointer',
                                textAlign: 'left',
                                touchAction: 'manipulation',
                                userSelect: 'none'
                            }}
                        >
                            🇮🇳 हिंदी
                        </button>
                        <button 
                            onClick={(e) => { e.stopPropagation(); setLanguage('telugu'); setShowMobileMenu(false); }}
                            onTouchEnd={(e) => { e.stopPropagation(); setLanguage('telugu'); setShowMobileMenu(false); }}
                            style={{
                                width: '100%',
                                padding: '8px 25px',
                                border: 'none',
                                background: language === 'telugu' ? 'rgba(255,107,53,0.1)' : 'transparent',
                                color: language === 'telugu' ? '#ff6b35' : '#333',
                                fontSize: '11px',
                                cursor: 'pointer',
                                textAlign: 'left',
                                touchAction: 'manipulation',
                                userSelect: 'none'
                            }}
                        >
                            🇮🇳 తెలుగు
                        </button>
                        <button 
                            onClick={(e) => { e.stopPropagation(); setLanguage('gujarati'); setShowMobileMenu(false); }}
                            onTouchEnd={(e) => { e.stopPropagation(); setLanguage('gujarati'); setShowMobileMenu(false); }}
                            style={{
                                width: '100%',
                                padding: '8px 25px',
                                border: 'none',
                                background: language === 'gujarati' ? 'rgba(255,107,53,0.1)' : 'transparent',
                                color: language === 'gujarati' ? '#ff6b35' : '#333',
                                fontSize: '11px',
                                cursor: 'pointer',
                                textAlign: 'left',
                                touchAction: 'manipulation',
                                userSelect: 'none'
                            }}
                        >
                            🇮🇳 ગુજરાતી
                        </button>
                        <button 
                            onClick={(e) => { e.stopPropagation(); setLanguage('tamil'); setShowMobileMenu(false); }}
                            onTouchEnd={(e) => { e.stopPropagation(); setLanguage('tamil'); setShowMobileMenu(false); }}
                            style={{
                                width: '100%',
                                padding: '8px 25px',
                                border: 'none',
                                background: language === 'tamil' ? 'rgba(255,107,53,0.1)' : 'transparent',
                                color: language === 'tamil' ? '#ff6b35' : '#333',
                                fontSize: '11px',
                                cursor: 'pointer',
                                textAlign: 'left',
                                touchAction: 'manipulation',
                                userSelect: 'none'
                            }}
                        >
                            🇮🇳 தமிழ்
                        </button>
                    </div>
            </div>
        )}
        </>
    );
};

export default ChatModal;