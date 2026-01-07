import React, { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import BirthForm from '../BirthForm/BirthForm';
import BirthFormModal from '../BirthForm/BirthFormModal';
import ChatGreeting from './ChatGreeting';
import EventPeriods from './EventPeriods';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { showToast } from '../../utils/toast';
import CreditsModal from '../Credits/CreditsModal';
import ContextModal from './ContextModal';
import PartnerChartModal from './PartnerChartModal';
import ChatPartnerSelector from './ChatPartnerSelector';
import { apiService } from '../../services/apiService';

import './ChatModal.css';

const ChatModal = ({ isOpen, onClose, initialBirthData = null, onChartRefClick: parentChartRefClick }) => {
    const { birthData, setBirthData } = useAstrology();
    const { credits, chatCost, partnershipCost, fetchBalance } = useCredits();
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
    const [chatMode, setChatMode] = useState('greeting'); // 'greeting', 'question', 'periods'
    const [eventPeriods, setEventPeriods] = useState([]);
    const [isPremiumMode, setIsPremiumMode] = useState(false);
    const [pendingMessages, setPendingMessages] = useState(new Set());
    const [currentPersonId, setCurrentPersonId] = useState(null);
    const [isPartnershipMode, setIsPartnershipMode] = useState(false);
    const [selectedPartnerChart, setSelectedPartnerChart] = useState(null);
    const [showPartnerModal, setShowPartnerModal] = useState(false);
    const [isAdmin, setIsAdmin] = useState(false);
    const [showChatPartnerSelector, setShowChatPartnerSelector] = useState(false);
    
    // Check admin status
    useEffect(() => {
        const checkAdminStatus = async () => {
            const token = localStorage.getItem('token');
            if (token) {
                try {
                    const response = await fetch('/api/me', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (response.ok) {
                        const userData = await response.json();
                        // console.log('👤 Admin check - User data:', userData);
                        setIsAdmin(userData.role === 'admin');
                    }
                } catch (error) {
                    // console.log('Admin check failed:', error);
                }
            }
        };
        checkAdminStatus();
    }, []);
    
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
                
                // Calculate bubble height including image if present
                let imageHeight = 0;
                if (msg.summary_image) {
                    imageHeight = 60; // Reserve space for image
                }
                const bubbleHeight = Math.max(20, doc.splitTextToSize(content, maxWidth - 20).length * 5 + 15 + imageHeight);
                
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
                
                // Add image if present
                if (msg.summary_image) {
                    try {
                        const imgData = msg.summary_image.startsWith('data:') ? msg.summary_image : `data:image/png;base64,${msg.summary_image}`;
                        doc.addImage(imgData, 'PNG', margin + 5, yPosition, maxWidth - 10, 50);
                        yPosition += 55;
                    } catch (error) {
                        console.error('Failed to add image to PDF:', error);
                    }
                }
                
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
            // Create unique person ID from birth data
            const personId = `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}`;
            
            // Check if person changed
            if (currentPersonId && currentPersonId !== personId) {
                // Different person selected - clear current state immediately
                setMessages([]);
                setSessionId(null);
                setIsLoading(false);
                setChatMode('greeting');
            }
            
            setCurrentPersonId(personId);
            setShowBirthForm(false);
            loadChatHistory(personId);
            // Check for pending responses when component loads
            checkPendingResponses(personId);
        }
    }, [birthData]);
    
    // Check for pending responses on component mount and when returning to page
    const checkPendingResponses = (personId = currentPersonId) => {
        const stored = localStorage.getItem(`pendingChatMessages_${personId}`);
        if (stored) {
            const pendingIds = JSON.parse(stored);
            pendingIds.forEach(messageId => {
                // Resume polling for each pending message
                pollForResponse(messageId, true); // true = resume mode
            });
        }
    };
    
    // Save pending message to localStorage per person
    const addPendingMessage = (messageId) => {
        const key = `pendingChatMessages_${currentPersonId}`;
        const stored = localStorage.getItem(key);
        const pendingIds = stored ? JSON.parse(stored) : [];
        if (!pendingIds.includes(messageId)) {
            pendingIds.push(messageId);
            localStorage.setItem(key, JSON.stringify(pendingIds));
        }
        setPendingMessages(prev => new Set([...prev, messageId]));
    };
    
    // Remove completed message from localStorage per person
    const removePendingMessage = (messageId) => {
        const key = `pendingChatMessages_${currentPersonId}`;
        const stored = localStorage.getItem(key);
        if (stored) {
            const pendingIds = JSON.parse(stored).filter(id => id !== messageId);
            localStorage.setItem(key, JSON.stringify(pendingIds));
        }
        setPendingMessages(prev => {
            const newSet = new Set(prev);
            newSet.delete(messageId);
            return newSet;
        });
    };
    

    
    const addGreetingMessage = () => {
        // Set greeting mode instead of adding message
        setChatMode('greeting');
        setMessages([]);
    };
    
    const handleOptionSelect = async (option) => {
        if (option === 'periods') {
            setChatMode('periods');
        } else {
            setChatMode('question');
            // Add opening message for question mode
            const openingMessage = {
                role: 'assistant',
                content: `Hello ${birthData?.name || 'there'}! I'm here to help you understand your birth chart and provide astrological guidance. Feel free to ask me anything about your personality, relationships, career, health, or future predictions. What would you like to know?`,
                timestamp: new Date().toISOString()
            };
            setMessages([openingMessage]);
        }
    };
    
    const handlePeriodSelect = (period) => {
        setChatMode('question');
        const question = `Predict specific events for this period: ${period.label}`;
        // Scroll to bottom when switching to question mode from period selection
        setTimeout(scrollToBottom, 100);
        handleSendMessage(question, { selected_period: period.period_data });
    };
    
    const handleBackToGreeting = () => {
        setChatMode('greeting');
    };

    const loadChatHistory = async (personId = currentPersonId) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/chat-v2/history', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                const sessions = data.sessions || [];
                
                if (sessions.length > 0) {
                    // Load the most recent session
                    const latestSession = sessions[0];
                    const sessionResponse = await fetch(`/api/chat-v2/session/${latestSession.session_id}`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    
                    if (sessionResponse.ok) {
                        const sessionData = await sessionResponse.json();
                        const messages = sessionData.messages || [];
                        
                        // Filter messages for current person and convert format
                        const currentBirthHash = `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}`;
                        
                        // For now, since backend doesn't filter by birth data, we'll use localStorage to track per-person sessions
                        const personSessions = JSON.parse(localStorage.getItem(`chatSessions_${currentBirthHash}`) || '[]');
                        
                        // Only load if this session belongs to current person
                        if (!personSessions.includes(latestSession.session_id)) {
                            // This session doesn't belong to current person - start fresh
                            addGreetingMessage();
                            return;
                        }
                        
                        const formattedMessages = messages.map(msg => {
                            const formatted = {
                                role: msg.sender === 'user' ? 'user' : 'assistant',
                                content: msg.content || '🔮 Analyzing your birth chart...',
                                timestamp: msg.timestamp,
                                messageId: msg.message_id, // Add messageId from database
                                isFromDatabase: true, // Mark as from database
                                terms: msg.terms || [],
                                glossary: msg.glossary || {},
                                message_type: msg.message_type || 'answer',
                                summary_image: msg.summary_image || null // Add summary_image from database
                            };
                            
                            console.log('📜 Loaded message:', { id: msg.message_id, sender: msg.sender, hasContent: !!msg.content });
                            
                            // Check if this is a pending message for this person
                            const pendingIds = JSON.parse(localStorage.getItem(`pendingChatMessages_${personId}`) || '[]');
                            if (msg.sender === 'assistant' && !msg.content && pendingIds.length > 0) {
                                // This might be a pending message - add processing state
                                formatted.isProcessing = true;
                                formatted.messageId = pendingIds[pendingIds.length - 1]; // Assume latest pending
                                formatted.showRestartButton = true;
                            }
                            
                            return formatted;
                        });
                        
                        if (formattedMessages.length > 0) {
                            setMessages(formattedMessages);
                            setSessionId(latestSession.session_id);
                            setChatMode('question');
                        } else {
                            addGreetingMessage();
                        }
                        return;
                    }
                }
            }
            
            // No history found - show greeting
            addGreetingMessage();
        } catch (error) {
            console.error('Error loading chat history:', error);
            addGreetingMessage();
        }
    };

    const createSession = async () => {
        try {
            const token = localStorage.getItem('token');
            const birth_chart_id = birthData?.id; // Get from birthData
            
            console.log('Creating session with birth_chart_id:', birth_chart_id);
            
            const response = await fetch('/api/chat-v2/session', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    birth_chart_id: birth_chart_id || null
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                const newSessionId = data.session_id;
                setSessionId(newSessionId);
                
                // Track this session for current person
                const currentBirthHash = `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}`;
                const personSessions = JSON.parse(localStorage.getItem(`chatSessions_${currentBirthHash}`) || '[]');
                if (!personSessions.includes(newSessionId)) {
                    personSessions.push(newSessionId);
                    localStorage.setItem(`chatSessions_${currentBirthHash}`, JSON.stringify(personSessions));
                }
                
                return newSessionId;
            }
        } catch (error) {
            console.error('Error creating session:', error);
        }
        return null;
    };



    const handleSendMessage = async (message, options = {}) => {
        if (!birthData) return;

        // Create session if first message
        let currentSessionId = sessionId;
        if (!currentSessionId) {
            currentSessionId = await createSession();
            if (!currentSessionId) return;
        }

        const userMessage = { role: 'user', content: message, timestamp: new Date().toISOString(), messageId: null };
        setMessages(prev => [...prev, userMessage]);
        
        // Add processing message
        const processingMessage = { 
            role: 'assistant', 
            content: '🔮 Analyzing your birth chart...', 
            timestamp: new Date().toISOString(),
            isProcessing: true,
            messageId: null
        };
        setMessages(prev => [...prev, processingMessage]);
        setIsLoading(true);
        
        // Scroll to bottom after messages are added
        setTimeout(scrollToBottom, 100);

        try {
            const requestData = {
                session_id: currentSessionId,
                question: message,
                language,
                response_style: responseStyle,
                premium_analysis: options.premium_analysis || false,
                partnership_mode: isPartnershipMode,
                birth_details: {
                    name: birthData.name,
                    date: birthData.date,
                    time: birthData.time,
                    latitude: parseFloat(birthData.latitude),
                    longitude: parseFloat(birthData.longitude),
                    place: birthData.place || '',
                    gender: birthData.gender || ''
                }
            };
            
            if (isPartnershipMode && selectedPartnerChart) {
                requestData.partner_name = selectedPartnerChart.name;
                requestData.partner_date = typeof selectedPartnerChart.date === 'string' ? selectedPartnerChart.date.split('T')[0] : selectedPartnerChart.date;
                requestData.partner_time = typeof selectedPartnerChart.time === 'string' ? selectedPartnerChart.time.split('T')[1]?.slice(0, 5) || selectedPartnerChart.time : selectedPartnerChart.time;
                requestData.partner_place = selectedPartnerChart.place || '';
                requestData.partner_latitude = parseFloat(selectedPartnerChart.latitude);
                requestData.partner_longitude = parseFloat(selectedPartnerChart.longitude);
                requestData.partner_gender = selectedPartnerChart.gender || '';
            }
            
            // console.log('Chat request data:', requestData);
            // console.log('Token:', localStorage.getItem('token') ? 'Present' : 'Missing');
            
            // Start async processing
            const response = await fetch('/api/chat-v2/ask', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            // console.log('Chat response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                // console.error('Chat error response:', errorText);
                
                if (response.status === 402) {
                    fetchBalance();
                }
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const result = await response.json();
            const assistantMessageId = result.message_id;
            const userMessageId = result.user_message_id;
            
            console.log('💬 Backend response IDs:', { assistantMessageId, userMessageId });

            // Update user message with messageId from backend
            setMessages(prev => prev.map((msg, index) => {
                // Find the user message (second to last message)
                if (index === prev.length - 2 && msg.role === 'user' && !msg.messageId) {
                    console.log('👤 Updating user message with ID:', userMessageId);
                    return { ...msg, messageId: userMessageId, isFromDatabase: true };
                }
                return msg;
            }));

            // Update processing message with messageId
            setMessages(prev => prev.map(msg => {
                if (msg.isProcessing) {
                    console.log('🤖 Updating assistant message with ID:', assistantMessageId);
                    return { ...msg, messageId: assistantMessageId, isFromDatabase: true };
                }
                return msg;
            }));

            // Start polling
            pollForResponse(assistantMessageId);

        } catch (error) {
            console.error('Error starting chat:', error);
            setMessages(prev => prev.map(msg => 
                msg.isProcessing 
                    ? { ...msg, content: 'Error starting analysis. Please try again.', isProcessing: false }
                    : msg
            ));
            setIsLoading(false);
        }
    };

    // Polling function
    const pollForResponse = async (messageId, isResume = false) => {
        const maxPolls = 80; // 4 minutes max (80 * 3s = 240s)
        let pollCount = 0;
        
        // Add to pending messages if not resuming
        if (!isResume) {
            addPendingMessage(messageId);
        }
        
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
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/chat-v2/status/${messageId}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                });
                
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const status = await response.json();
                
                if (status.status === 'completed') {
                    // Check if person changed during processing
                    const currentPersonIdNow = birthData ? `${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}` : null;
                    if (currentPersonIdNow !== currentPersonId) {
                        // Person changed - don't show response, just clean up
                        removePendingMessage(messageId);
                        return;
                    }
                    
                    // Replace processing message with actual response including terms, glossary, message_type, and summary_image
                    setMessages(prev => prev.map(msg => 
                        msg.messageId === messageId 
                            ? { 
                                ...msg, 
                                content: status.content, 
                                isProcessing: false,
                                terms: status.terms || [],
                                glossary: status.glossary || {},
                                message_type: status.message_type || 'answer',
                                summary_image: status.summary_image || null // Add summary_image from backend response
                            }
                            : msg
                    ));
                    setIsLoading(false);
                    removePendingMessage(messageId);
                    return;
                }
                
                if (status.status === 'failed') {
                    setMessages(prev => prev.map(msg => 
                        msg.messageId === messageId 
                            ? { ...msg, content: status.error_message || 'Analysis failed. Please try again.', isProcessing: false }
                            : msg
                    ));
                    setIsLoading(false);
                    removePendingMessage(messageId);
                    return;
                }
                
                // Still processing - update message and continue polling
                if (status.status === 'processing') {
                    const randomMessage = loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
                    
                    setMessages(prev => prev.map(msg => 
                        msg.messageId === messageId 
                            ? { ...msg, content: randomMessage }
                            : msg
                    ));
                    
                    // Continue polling
                    pollCount++;
                    if (pollCount < maxPolls) {
                        setTimeout(poll, 3000); // Poll every 3 seconds
                    } else {
                        // Timeout - show restart option
                        setMessages(prev => prev.map(msg => 
                            msg.messageId === messageId 
                                ? { 
                                    ...msg, 
                                    content: 'Analysis is taking longer than expected. The system is still working on your request.', 
                                    isProcessing: false,
                                    showRestartButton: true
                                }
                                : msg
                        ));
                        setIsLoading(false);
                        // Keep in pending messages for later resume
                    }
                }
                
            } catch (error) {
                console.error('Polling error:', error);
                setMessages(prev => prev.map(msg => 
                    msg.messageId === messageId 
                        ? { ...msg, content: 'Connection error. Please try again.', isProcessing: false }
                        : msg
                ));
                setIsLoading(false);
                removePendingMessage(messageId);
            }
        };
        
        // Start first poll after 1 second
        setTimeout(poll, 1000);
    };

    const restartPolling = (messageId) => {
        // Update message to show restarting
        setMessages(prev => prev.map(msg => 
            msg.messageId === messageId 
                ? { ...msg, content: '🔄 Checking for response...', isProcessing: true, showRestartButton: false }
                : msg
        ));
        setIsLoading(true);
        
        // Restart polling (resume mode)
        pollForResponse(messageId, true);
    };

    const [deletingMessages, setDeletingMessages] = useState(new Set());
    
    const handleDeleteMessage = async (messageId) => {
        console.log('🔍 DELETE HANDLER CALLED:', {
            messageId,
            timestamp: new Date().toISOString(),
            stackTrace: new Error().stack
        });
        
        // Prevent duplicate delete requests
        if (deletingMessages.has(messageId)) {
            console.log('❌ Delete already in progress for message:', messageId);
            return;
        }
        
        try {
            setDeletingMessages(prev => new Set([...prev, messageId]));
            console.log('🗑️ Attempting to delete message ID:', messageId);
            
            const token = localStorage.getItem('token');
            const response = await fetch(`/api/chat-v2/message/${messageId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                showToast('Message deleted successfully', 'success');
                setMessages(prev => prev.filter(msg => msg.messageId !== messageId));
            } else {
                const errorText = await response.text();
                console.error('Delete failed:', response.status, errorText);
                showToast('Failed to delete message', 'error');
            }
        } catch (error) {
            console.error('Delete error:', error);
            showToast('Error deleting message', 'error');
        } finally {
            setDeletingMessages(prev => {
                const newSet = new Set(prev);
                newSet.delete(messageId);
                return newSet;
            });
        }
    };

    const handleBirthFormSubmit = () => {
        setShowBirthForm(false);
    };

    const handlePartnershipToggle = () => {
        if (!isPartnershipMode) {
            setShowChatPartnerSelector(true);
        } else {
            setIsPartnershipMode(false);
            setSelectedPartnerChart(null);
        }
    };

    const handlePartnerSelect = (chart) => {
        setSelectedPartnerChart(chart);
        setIsPartnershipMode(true);
    };

    const handleSelectPartner = (chart) => {
        setSelectedPartnerChart(chart);
        setIsPartnershipMode(true);
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
    
    // Handle page visibility changes - resume polling when user returns
    React.useEffect(() => {
        const handleVisibilityChange = () => {
            if (!document.hidden && birthData && currentPersonId) {
                // User returned to page - check for pending responses for current person
                setTimeout(() => checkPendingResponses(currentPersonId), 1000);
            }
        };
        
        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [birthData, currentPersonId]);
    
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
    const [showCreditsModal, setShowCreditsModal] = useState(false);
    const [showContextModal, setShowContextModal] = useState(false);
    const [contextData, setContextData] = useState(null);
    const [showEnhancedPopup, setShowEnhancedPopup] = useState(false);
    
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
            <div className={`chat-modal ${isPremiumMode ? 'premium-theme' : ''}`} onClick={(e) => e.stopPropagation()}>
                <div className="chat-modal-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', marginRight: '100px' }}>
                        <h2 style={{ margin: 0, flex: 1 }}>
                            AstroRoshni {isPartnershipMode && selectedPartnerChart 
                                ? `${birthData?.name} & ${selectedPartnerChart.name}` 
                                : birthData?.name ? `with ${birthData.name}` : '- Your Personal Astrologer'
                            }
                        </h2>
                        <button 
                            onClick={handlePartnershipToggle}
                            style={{
                                background: isPartnershipMode ? 'linear-gradient(45deg, #ff6b35, #f7931e)' : 'rgba(255,255,255,0.2)',
                                padding: '6px 10px',
                                borderRadius: '15px',
                                fontSize: '11px',
                                fontWeight: 'bold',
                                color: 'white',
                                border: `1px solid ${isPartnershipMode ? '#ff6b35' : 'rgba(255,255,255,0.3)'}`,
                                cursor: 'pointer',
                                whiteSpace: 'nowrap',
                                marginRight: '8px'
                            }}
                        >
                            💕 {isPartnershipMode ? 'Exit Partnership' : 'Partnership'}
                        </button>
                        <div style={{
                            background: 'rgba(255,255,255,0.2)',
                            padding: '4px 12px',
                            borderRadius: '15px',
                            fontSize: '12px',
                            color: 'white',
                            fontWeight: 'bold',
                            whiteSpace: 'nowrap'
                        }}>
                            💳 {credits} | {isPartnershipMode ? partnershipCost : chatCost}/q
                        </div>
                    </div>
                    

                    
                    {/* Desktop buttons */}
                    <div className="desktop-buttons">
                        {(chatMode === 'question' || chatMode === 'periods') && (
                            <button onClick={handleBackToGreeting}>
                                ← Back
                            </button>
                        )}
                        <button onClick={() => setResponseStyle(responseStyle === 'detailed' ? 'concise' : 'detailed')}>
                            {responseStyle === 'detailed' ? '⚡ Quick' : '📋 Detailed'}
                        </button>
                        <button onClick={() => setLanguage(getNextLanguage(language))}>
                            {getLanguageDisplay(getNextLanguage(language))}
                        </button>
                        <button onClick={downloadChatPDF}>
                            📄 Download PDF
                        </button>
                        <button onClick={() => {
                            const event = new CustomEvent('openChartModal');
                            window.dispatchEvent(event);
                        }}>
                            📊 View Chart
                        </button>
                        <button onClick={() => setShowBirthForm(true)}>
                            👤 {birthData?.name || 'Change Person'}
                        </button>
                        {isPartnershipMode && (
                            <button onClick={() => setShowChatPartnerSelector(true)}>
                                💕 {selectedPartnerChart ? selectedPartnerChart.name : 'Select Partner'}
                            </button>
                        )}
                        {isAdmin && (
                            <button 
                                onClick={() => {
                                    // console.log('Context button clicked, contextData:', contextData);
                                    setShowContextModal(true);
                                }}
                                style={{
                                    background: contextData ? 'red' : 'orange',
                                    color: 'white',
                                    border: '2px solid black'
                                }}
                            >
                                📄 Context {contextData ? '(Has Data)' : '(No Data)'}
                            </button>
                        )}
                    </div>
                    

                    
                    {/* Mobile menu */}
                    <div className="mobile-menu">
                        <button 
                            onClick={() => setShowMobileMenu(!showMobileMenu)}
                            className="mobile-menu-btn"
                        >
                            ⋮
                        </button>
                    </div>
                    
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>
                
                <div className="chat-modal-content">
                    {showBirthForm ? (
                        <div className="birth-form-container" style={{ position: 'relative' }}>
                            <button 
                                onClick={() => setShowBirthForm(false)}
                                style={{
                                    position: 'absolute',
                                    top: '10px',
                                    right: '10px',
                                    background: 'rgba(255,255,255,0.9)',
                                    border: 'none',
                                    color: '#333',
                                    width: '30px',
                                    height: '30px',
                                    borderRadius: '50%',
                                    cursor: 'pointer',
                                    fontSize: '18px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    zIndex: 1000,
                                    boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
                                }}
                            >
                                ×
                            </button>
                            <BirthForm 
                                onSubmit={handleBirthFormSubmit}
                                onLogout={() => {}}
                            />
                        </div>
                    ) : (
                        <>
                            {chatMode === 'greeting' && (
                                <div className="chat-messages">
                                    <ChatGreeting 
                                        birthData={birthData}
                                        onOptionSelect={handleOptionSelect}
                                    />
                                </div>
                            )}
                            
                            {chatMode === 'periods' && (
                                <div className="chat-messages">
                                    <EventPeriods 
                                        birthData={birthData}
                                        onPeriodSelect={handlePeriodSelect}
                                        onBack={handleBackToGreeting}
                                    />
                                </div>
                            )}
                            
                            {chatMode === 'question' && (
                                <>
                                    <div className="chat-messages">
                                        <div style={{
                                            padding: '10px 0',
                                            borderBottom: '1px solid rgba(255,255,255,0.2)',
                                            marginBottom: '15px'
                                        }}>
                                            <button 
                                                onClick={handleBackToGreeting}
                                                style={{
                                                    background: 'rgba(255,255,255,0.2)',
                                                    border: '1px solid rgba(255,255,255,0.3)',
                                                    color: 'white',
                                                    padding: '6px 12px',
                                                    borderRadius: '6px',
                                                    fontSize: '12px',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.3s ease'
                                                }}
                                            >
                                                ← Back to Options
                                            </button>
                                        </div>
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
                                            onRestartPolling={restartPolling}
                                            onDeleteMessage={handleDeleteMessage}
                                        />
                                    </div>
                                    <ChatInput 
                                        onSendMessage={handleSendMessage} 
                                        isLoading={isLoading} 
                                        followUpQuestion={followUpQuestion}
                                        onFollowUpUsed={() => setFollowUpQuestion('')}
                                        onOpenCreditsModal={() => setShowCreditsModal(true)}
                                        onPremiumModeChange={setIsPremiumMode}
                                        onShowEnhancedPopup={() => setShowEnhancedPopup(true)}
                                        isPartnershipMode={isPartnershipMode}
                                    />
                                </>
                            )}
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
                    {(chatMode === 'question' || chatMode === 'periods') && (
                        <button 
                            onClick={(e) => { e.stopPropagation(); handleBackToGreeting(); setShowMobileMenu(false); }}
                            onTouchEnd={(e) => { e.stopPropagation(); handleBackToGreeting(); setShowMobileMenu(false); }}
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
                            ← Back to Options
                        </button>
                    )}
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
        
        {/* Birth Form Modal */}
        <BirthFormModal
            isOpen={showBirthForm}
            onClose={() => setShowBirthForm(false)}
            onSubmit={handleBirthFormSubmit}
            title="Chat - Enter Birth Details"
            description="Please provide your birth information to start chatting with AstroRoshni"
        />
        
        {/* Credits Modal */}
        <CreditsModal 
            isOpen={showCreditsModal} 
            onClose={() => setShowCreditsModal(false)} 
        />
        
        {/* Context Modal */}
        <ContextModal 
            isOpen={showContextModal}
            onClose={() => setShowContextModal(false)}
            contextData={contextData}
        />
        
        {/* Enhanced Analysis Popup */}
        {showEnhancedPopup && (
            <div className="enhanced-popup-overlay" onClick={() => setShowEnhancedPopup(false)}>
                <div className="enhanced-popup" onClick={(e) => e.stopPropagation()}>
                    <button className="popup-close" onClick={() => setShowEnhancedPopup(false)}>×</button>
                    <div className="popup-header">
                        <span className="popup-icon">✨</span>
                        <h3>Enhanced Deep Analysis</h3>
                    </div>
                    <div className="popup-content">
                        <p className="popup-intro">This advanced analysis uses more sophisticated astrological calculations and deeper interpretation techniques to provide you with comprehensive insights.</p>
                        
                        <div className="benefit-list">
                            <div className="benefit-item">
                                <span className="benefit-icon">🔮</span>
                                <div>
                                    <strong>Multi-Layered Chart Analysis</strong>
                                    <p>Examines Lagna, Navamsa, and divisional charts with intricate planetary relationships and house lordships</p>
                                </div>
                            </div>
                            
                            <div className="benefit-item">
                                <span className="benefit-icon">🌟</span>
                                <div>
                                    <strong>Advanced Dasha Interpretation</strong>
                                    <p>Analyzes Mahadasha, Antardasha, and Pratyantardasha periods with precise event timing predictions</p>
                                </div>
                            </div>
                            
                            <div className="benefit-item">
                                <span className="benefit-icon">🎯</span>
                                <div>
                                    <strong>Yoga & Dosha Detection</strong>
                                    <p>Identifies powerful yogas like Raja, Dhana, Gaja Kesari and doshas affecting your life trajectory</p>
                                </div>
                            </div>
                            
                            <div className="benefit-item">
                                <span className="benefit-icon">🌙</span>
                                <div>
                                    <strong>Nakshatra Deep Dive</strong>
                                    <p>Reveals hidden personality traits, karmic patterns, and life purpose through nakshatra analysis</p>
                                </div>
                            </div>
                            
                            <div className="benefit-item">
                                <span className="benefit-icon">⚡</span>
                                <div>
                                    <strong>Transit Correlation</strong>
                                    <p>Maps current planetary transits against your birth chart for accurate timing of events</p>
                                </div>
                            </div>
                            
                            <div className="benefit-item">
                                <span className="benefit-icon">🏆</span>
                                <div>
                                    <strong>Remedial Recommendations</strong>
                                    <p>Provides personalized gemstone, mantra, and ritual suggestions based on planetary strengths</p>
                                </div>
                            </div>
                        </div>
                        
                        <div className="popup-footer">
                            <button className="popup-btn" onClick={() => setShowEnhancedPopup(false)}>
                                Got it!
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )}
        
        {/* Partner Chart Selection Modal */}
        <PartnerChartModal 
            isOpen={showPartnerModal}
            onClose={() => setShowPartnerModal(false)}
            onSelectPartner={handleSelectPartner}
        />
        
        {/* Chat Partner Selector */}
        <ChatPartnerSelector 
            isOpen={showChatPartnerSelector}
            onClose={() => setShowChatPartnerSelector(false)}
            onSelectPartner={handlePartnerSelect}
        />
        </>
    );
};

export default ChatModal;