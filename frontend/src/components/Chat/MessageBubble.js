import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import textToSpeech from '../../utils/textToSpeech';
import { showToast } from '../../utils/toast';
import ResponseRenderer from '../TermTooltip/ResponseRenderer';

const MessageBubble = ({ message, language = 'english', onFollowUpClick, onChartRefClick, onRestartPolling, onDeleteMessage }) => {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [hasError, setHasError] = useState(false);
    const [selectedVoice, setSelectedVoice] = useState(null);
    const [voices, setVoices] = useState([]);
    const [currentChunk, setCurrentChunk] = useState(0);
    const [totalChunks, setTotalChunks] = useState(0);
    const [showActions, setShowActions] = useState(false);
    const [tooltipModal, setTooltipModal] = useState({ show: false, term: '', definition: '' });
    const messageRef = useRef(null);
    
    React.useEffect(() => {
        const loadVoices = () => {
            const availableVoices = window.speechSynthesis.getVoices();
            setVoices(availableVoices);
            if (!selectedVoice && availableVoices.length > 0) {
                // Try to find Google US English voice first
                const googleUSVoice = availableVoices.find(voice => 
                    voice.name.includes('Google US English') || 
                    (voice.lang === 'en-US' && voice.name.includes('Google'))
                );
                setSelectedVoice(googleUSVoice || availableVoices[0]);
            }
        };
        
        loadVoices();
        window.speechSynthesis.onvoiceschanged = loadVoices;
    }, [selectedVoice]);
    
    // Auto-select appropriate voice based on language
    React.useEffect(() => {
        if (voices.length > 0) {
            if (language === 'hindi') {
                const hindiVoice = voices.find(voice => 
                    voice.lang.startsWith('hi') || 
                    voice.name.toLowerCase().includes('hindi') ||
                    voice.name.toLowerCase().includes('devanagari')
                );
                if (hindiVoice && selectedVoice !== hindiVoice) {
                    setSelectedVoice(hindiVoice);
                }
            } else if (language === 'telugu') {
                const teluguVoice = voices.find(voice => 
                    voice.lang.startsWith('te') || 
                    voice.name.toLowerCase().includes('telugu')
                );
                if (teluguVoice && selectedVoice !== teluguVoice) {
                    setSelectedVoice(teluguVoice);
                }
            } else if (language === 'gujarati') {
                const gujaratiVoice = voices.find(voice => 
                    voice.lang.startsWith('gu') || 
                    voice.name.toLowerCase().includes('gujarati')
                );
                if (gujaratiVoice && selectedVoice !== gujaratiVoice) {
                    setSelectedVoice(gujaratiVoice);
                }
            } else if (language === 'tamil') {
                const tamilVoice = voices.find(voice => 
                    voice.lang.startsWith('ta') || 
                    voice.name.toLowerCase().includes('tamil')
                );
                if (tamilVoice && selectedVoice !== tamilVoice) {
                    setSelectedVoice(tamilVoice);
                }
            } else {
                const englishVoice = voices.find(voice => 
                    voice.name.includes('Google US English') || 
                    (voice.lang === 'en-US' && voice.name.includes('Google'))
                );
                if (englishVoice && selectedVoice !== englishVoice) {
                    setSelectedVoice(englishVoice);
                }
            }
        }
    }, [language, voices, selectedVoice]);
    
    const cleanTextForCopy = (content) => {
        return content
            .replace(/\*\*(.*?)\*\*/g, '$1')     // Remove bold
            .replace(/\*(.*?)\*/g, '$1')       // Remove italics
            .replace(/###\s*(.*?)$/gm, '$1')   // Remove headers
            .replace(/<div class="quick-answer-card">(.*?)<\/div>/g, '$1') // Remove quick answer wrapper
            .replace(/<div class="final-thoughts-card">(.*?)<\/div>/g, '$1') // Remove final thoughts wrapper
            .replace(/•\s*/g, '• ')            // Normalize bullets
            .replace(/\n\s*\n/g, '\n\n')       // Normalize line breaks
            .trim();
    };
    
    const handleWhatsAppShare = () => {
        const cleanText = cleanTextForCopy(message.content);
        const shareText = `🔮 *AstroRoshni Prediction*\n\n${cleanText}\n\n_Shared from AstroRoshni App_`;
        const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(shareText)}`;
        window.open(whatsappUrl, '_blank');
        showToast('Opening WhatsApp...', 'success');
        setShowActions(false);
    };
    
    const handleDeleteMessage = async () => {
        console.log('🔍 MESSAGE BUBBLE DELETE CLICKED:', {
            messageId: message.messageId,
            timestamp: new Date().toISOString(),
            stackTrace: new Error().stack
        });
        
        if (!message.messageId) {
            showToast('Cannot delete message - no ID found', 'error');
            return;
        }
        
        if (window.confirm('Are you sure you want to delete this message?')) {
            console.log('🔍 USER CONFIRMED DELETE for message:', message.messageId);
            onDeleteMessage && onDeleteMessage(message.messageId);
        } else {
            console.log('🔍 USER CANCELLED DELETE for message:', message.messageId);
        }
        setShowActions(false);
    };
    
    const handleLongPress = () => {
        if ('vibrate' in navigator) {
            navigator.vibrate(50);
        }
        setShowActions(true);
    };
    
    const isMobile = () => {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    };
    
    // Close actions menu when clicking outside on mobile
    React.useEffect(() => {
        const handleClickOutside = (event) => {
            if (showActions && isMobile() && !event.target.closest('.message-actions')) {
                setShowActions(false);
            }
        };
        
        if (showActions && isMobile()) {
            document.addEventListener('touchstart', handleClickOutside);
            return () => document.removeEventListener('touchstart', handleClickOutside);
        }
    }, [showActions]);
    
    // Show actions only on mobile for WhatsApp sharing
    React.useEffect(() => {
        if (!isMobile()) return;
        
        const messageElement = messageRef.current;
        if (!messageElement) return;
        
        const handleMouseEnter = () => setShowActions(true);
        const handleMouseLeave = () => setShowActions(false);
        
        messageElement.addEventListener('mouseenter', handleMouseEnter);
        messageElement.addEventListener('mouseleave', handleMouseLeave);
        
        return () => {
            messageElement.removeEventListener('mouseenter', handleMouseEnter);
            messageElement.removeEventListener('mouseleave', handleMouseLeave);
        };
    }, []);
    const formatContent = (content, message = {}) => {
        if (!content || content.trim() === '') return '';
        
        console.log('🔍 Format Debug:', {
            hasTerms: !!message.terms,
            termsCount: message.terms?.length,
            hasGlossary: !!message.glossary,
            glossaryKeys: Object.keys(message.glossary || {}),
            contentPreview: content.substring(0, 200)
        });
        
        // 1. Decode HTML entities
        let formatted = content
            .replace(/&quot;/g, '"').replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<').replace(/&gt;/g, '>')
            .replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ');
        
        // 2. Add summary image (centered, 500px)
        if (message.summary_image) {
            formatted = `<div class="summary-image-container" style="margin: 0 auto 20px auto; borderRadius: 12px; overflow: hidden; boxShadow: 0 4px 16px rgba(0,0,0,0.15); background: linear-gradient(135deg, rgba(255,107,53,0.1), rgba(138,43,226,0.1)); border: 2px solid rgba(255,107,53,0.3); maxWidth: 500px;"><img src="${message.summary_image}" alt="Analysis Summary" style="width: 100%; height: auto; display: block;" onError="this.style.display='none'; this.parentElement.style.display='none';" /></div>` + formatted;
        }
        
        // 3. Normalize line breaks
        formatted = formatted.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        
        // 4. Handle Follow-up Questions
        formatted = formatted.replace(/<div class="follow-up-questions">([\s\S]*?)<\/div>/g, (match, questions) => {
            const questionList = questions.trim().split('\n').filter(q => q.trim()).map(q => `<button class="follow-up-btn">${q.trim()}</button>`).join('');
            return `<div class="follow-up-questions">${questionList}</div>`;
        });
        
        // 5. Handle Final Thoughts
        formatted = formatted.replace(/(### Final Thoughts[\s\S]*?)(?=###|$)/g, (match, finalThoughts) => {
            const cleanContent = finalThoughts.replace(/### Final Thoughts\n?/, '').replace(/\*\*(.*?)\*\*/gs, '<strong class="chat-bold">$1</strong>').replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em class="chat-italic">$1</em>').trim();
            return `</div></div><div class="final-thoughts-card"><strong class="chat-bold">Final Thoughts</strong>: ${cleanContent}</div>`;
        });
        
        // 6. Process Markdown BEFORE terms
        formatted = formatted.replace(/\*\*(.*?)\*\*/gs, '<strong class="chat-bold">$1</strong>');
        formatted = formatted.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em class="chat-italic">$1</em>');
        
        console.log('🔍 After markdown, before terms:', formatted.substring(0, 300));
        
        // 7. PROCESS TERMS - auto-wrap terms found in glossary
        if (message.terms && message.glossary && Object.keys(message.glossary).length > 0) {
            console.log('🔍 Processing terms:', message.terms);
            
            // First try to find existing <term> tags
            const termRegex = /<term\s+id=["']([^"']+)["']\s*>([^<]+)<\/term>/gi;
            let termCount = 0;
            formatted = formatted.replace(termRegex, (match, termId, termText) => {
                const normalizedId = termId.toLowerCase().trim();
                if (message.glossary[normalizedId]) {
                    termCount++;
                    const definition = message.glossary[normalizedId].replace(/"/g, '&quot;');
                    return `<span class="tooltip-wrapper" data-term="${normalizedId}" data-definition="${definition}" style="color: #e91e63; font-weight: bold; cursor: pointer; border-bottom: 1px dotted #e91e63;"><span class="term-tooltip">${termText}</span></span>`;
                }
                return termText;
            });
            
            // If no tags found, auto-wrap terms from glossary keys
            if (termCount === 0) {
                Object.keys(message.glossary).forEach(termKey => {
                    const definition = message.glossary[termKey].replace(/"/g, '&quot;');
                    // Create case-insensitive regex for the term
                    const termPattern = new RegExp(`\\b(${termKey.replace(/[()]/g, '\\$&')})\\b`, 'gi');
                    formatted = formatted.replace(termPattern, (match) => {
                        termCount++;
                        return `<span class="tooltip-wrapper" data-term="${termKey}" data-definition="${definition}" style="color: #e91e63; font-weight: bold; cursor: pointer; border-bottom: 1px dotted #e91e63;"><span class="term-tooltip">${match}</span></span>`;
                    });
                });
            }
            
            console.log('🔍 Terms replaced:', termCount);
        }
        
        // 8. Convert headers to section cards
        formatted = formatted.replace(/### (.*?)\n/g, (match, header) => {
            return `</div></div><div class="section-card"><div class="section-header">${header.trim()}</div><div class="section-content">`;
        });
        
        // 9. Process paragraphs and lists
        const sections = formatted.split('</div></div>');
        formatted = sections.map(section => {
            if (!section.includes('<div class="section-content">')) return section;
            
            const parts = section.split('<div class="section-content">');
            if (parts.length < 2) return section;
            
            let content = parts[1];
            // Process lists
            content = content.replace(/\n\*\s+(.+)/g, '<li class="chat-bullet">• $1</li>');
            content = content.replace(/(<li class="chat-bullet">.*?<\/li>)/gs, '<ul class="chat-list">$1</ul>');
            
            return parts[0] + '<div class="section-content">' + content;
        }).join('</div></div>');
        
        // 10. Close divs and remove leading closures
        formatted = formatted.trim() + '</div></div>';
        formatted = formatted.replace(/^<\/div><\/div>/, '');
        
        return formatted;
    };

    const handleSpeak = () => {
        setHasError(false);
        
        // Always cancel any existing speech first
        window.speechSynthesis.cancel();
        
        if (isSpeaking) {
            setIsSpeaking(false);
        } else {
            if (message.content && message.content.trim()) {
                // Clean the text first - remove HTML entities and tags
                let cleanText = message.content
                    .replace(/&quot;/g, '"')         // Decode HTML entities
                    .replace(/&amp;/g, '&')
                    .replace(/&lt;/g, '<')
                    .replace(/&gt;/g, '>')
                    .replace(/&#39;/g, "'")
                    .replace(/&nbsp;/g, ' ')
                    .replace(/<[^>]*>/g, '')         // Remove all HTML tags
                    .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
                    .replace(/\*(.*?)\*/g, '$1')     // Remove italics markdown
                    .replace(/###\s*(.*?)$/gm, '$1') // Remove headers
                    .replace(/•\s*/g, '')            // Remove bullets
                    .replace(/\n+/g, '. ')           // Replace line breaks
                    .replace(/\s+/g, ' ')            // Normalize spaces
                    .trim();
                
                // Break text into chunks for reliable speech synthesis
                const chunkSize = 1000; // Characters per chunk
                const chunks = [];
                for (let i = 0; i < cleanText.length; i += chunkSize) {
                    chunks.push(cleanText.substring(i, i + chunkSize));
                }
                
                setTotalChunks(chunks.length);
                setCurrentChunk(0);
                
                const speakChunk = (chunkIndex) => {
                    if (chunkIndex >= chunks.length) {
                        setIsSpeaking(false);
                        setCurrentChunk(0);
                        return;
                    }
                    
                    const utterance = new SpeechSynthesisUtterance(chunks[chunkIndex]);
                    utterance.rate = 0.9;
                    utterance.pitch = 1;
                    utterance.volume = 1;
                    
                    if (selectedVoice) {
                        utterance.voice = selectedVoice;
                    }
                    
                    utterance.onstart = () => {
                        setIsSpeaking(true);
                        setCurrentChunk(chunkIndex + 1);
                    };
                    
                    utterance.onend = () => {
                        // Speak next chunk after a brief pause
                        setTimeout(() => speakChunk(chunkIndex + 1), 100);
                    };
                    
                    utterance.onerror = (error) => {
                        if (error.error !== 'interrupted') {
                            setHasError(true);
                        }
                        setIsSpeaking(false);
                    };
                    
                    window.speechSynthesis.speak(utterance);
                };
                
                // Start speaking from first chunk
                speakChunk(0);
            }
        }
    };

    // Handle tooltip clicks with event delegation
    useEffect(() => {
        // Create global function for tooltip clicks
        window.openTooltip = (termId, term, definition) => {
            setTooltipModal({ show: true, term, definition });
        };
        
        return () => {
            delete window.openTooltip;
        };
    }, []);

    return (
        <div 
            ref={messageRef}
            className={`message-bubble ${message.role} ${message.isTyping ? 'typing' : ''} ${message.isProcessing ? 'processing' : ''} ${message.message_type === 'clarification' ? 'clarification' : ''}`}
            onTouchStart={isMobile() ? handleLongPress : undefined}
            onClick={(e) => {
                if (isMobile() && showActions) {
                    setShowActions(false);
                }
            }}
        >
            {/* Action buttons */}
            {showActions && !message.isTyping && !message.isProcessing && isMobile() && (
                <div className="message-actions">
                    <button 
                        className="action-btn whatsapp-btn"
                        onClick={handleWhatsAppShare}
                        title="Share on WhatsApp"
                    >
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.465 3.488"/>
                        </svg>
                    </button>
                    {message.messageId && message.isFromDatabase && (
                        <button 
                            className="action-btn delete-btn"
                            onClick={handleDeleteMessage}
                            title="Delete Message"
                        >
                            🗑️
                        </button>
                    )}
                </div>
            )}
            

            
            <div className="message-content">
                {message.role === 'assistant' && !message.isTyping && !message.isProcessing && textToSpeech.isSupported && message.content && (
                    <div style={{ clearfix: 'both', marginBottom: '8px', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                        <select 
                            value={selectedVoice?.name || ''}
                            onChange={(e) => {
                                const voice = voices.find(v => v.name === e.target.value);
                                setSelectedVoice(voice);
                            }}
                            style={{
                                fontSize: '11px',
                                padding: '2px 4px',
                                borderRadius: '3px',
                                border: '1px solid #ccc',
                                maxWidth: '120px'
                            }}
                        >
                            {voices.map(voice => (
                                <option key={voice.name} value={voice.name}>
                                    {voice.lang} - {voice.name.split(' ')[0]}
                                </option>
                            ))}
                        </select>
                        <button 
                            onClick={handleSpeak}
                            style={{
                                background: isSpeaking ? '#ff4444' : '#4CAF50',
                                border: 'none',
                                color: 'white',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '12px',
                                cursor: 'pointer'
                            }}
                        >
                            {isSpeaking ? `🔇 Stop (${currentChunk}/${totalChunks})` : hasError ? '⚠️ Retry' : '🔊 Listen'}
                        </button>
                    </div>
                )}
                <div 
                    className="message-text enhanced-formatting"
                    onClick={(e) => {
                        // Check for tooltip wrapper clicks
                        if (e.target.classList.contains('tooltip-wrapper')) {
                            const term = e.target.querySelector('.term-tooltip').textContent;
                            const definition = e.target.getAttribute('data-definition');
                            setTooltipModal({ show: true, term, definition });
                            return;
                        }
                        
                        // Check if clicked inside tooltip wrapper
                        const wrapper = e.target.closest('.tooltip-wrapper');
                        if (wrapper) {
                            const term = wrapper.querySelector('.term-tooltip').textContent;
                            const definition = wrapper.getAttribute('data-definition');
                            setTooltipModal({ show: true, term, definition });
                            return;
                        }
                        
                        console.log('No tooltip found');
                    }}
                >
                    {/* Always use ResponseRenderer for assistant messages */}
                    {message.role === 'assistant' ? (
                        <div dangerouslySetInnerHTML={{ __html: formatContent(message.content, message) }} />
                    ) : (
                        <div dangerouslySetInnerHTML={{ __html: formatContent(message.content) }} />
                    )}
                </div>
                
                {/* Action buttons positioned like mobile */}
                {!message.isTyping && !message.isProcessing && message.messageId && message.isFromDatabase && (
                    <div className="message-action-buttons">
                        <button 
                            className="action-btn copy-btn"
                            style={{
                                width: '20px',
                                height: '20px',
                                minWidth: '20px',
                                padding: '0',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                            onClick={async () => {
                                try {
                                    const cleanText = cleanTextForCopy(message.content);
                                    await navigator.clipboard.writeText(cleanText);
                                    showToast('Message copied!', 'success');
                                } catch (err) {
                                    showToast('Copy failed', 'error');
                                }
                            }}
                            title="Copy Message"
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                            </svg>
                        </button>
                        <button 
                            className="action-btn delete-btn"
                            style={{
                                width: '20px',
                                height: '20px',
                                minWidth: '20px',
                                padding: '0',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                            onClick={handleDeleteMessage}
                            title="Delete Message"
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                            </svg>
                        </button>
                    </div>
                )}
                {message.showRestartButton && (
                    <button 
                        onClick={() => onRestartPolling && onRestartPolling(message.messageId)}
                        style={{
                            background: '#ff6b35',
                            color: 'white',
                            border: 'none',
                            padding: '8px 16px',
                            borderRadius: '6px',
                            fontSize: '14px',
                            cursor: 'pointer',
                            marginTop: '10px',
                            display: 'block'
                        }}
                    >
                        🔄 Check for Response
                    </button>
                )}
                {(message.isTyping || message.isProcessing) && (
                    <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                )}
                <div className="message-timestamp">
                    {new Date(message.timestamp).toLocaleTimeString()}
                </div>
            </div>
            
            {/* Tooltip Modal using Portal */}
            {tooltipModal.show && createPortal(
                <div 
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        backgroundColor: 'rgba(0, 0, 0, 0.5)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 10000
                    }}
                    onClick={() => setTooltipModal({ show: false, term: '', definition: '' })}
                >
                    <div 
                        style={{
                            backgroundColor: 'white',
                            padding: '20px',
                            borderRadius: '10px',
                            maxWidth: '400px',
                            margin: '20px',
                            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 style={{ margin: '0 0 10px 0', color: '#e91e63' }}>{tooltipModal.term}</h3>
                        <p style={{ margin: '0', lineHeight: '1.5', color: '#333' }}>{tooltipModal.definition}</p>
                        <button 
                            onClick={() => setTooltipModal({ show: false, term: '', definition: '' })}
                            style={{
                                marginTop: '15px',
                                padding: '8px 16px',
                                backgroundColor: '#e91e63',
                                color: 'white',
                                border: 'none',
                                borderRadius: '5px',
                                cursor: 'pointer'
                            }}
                        >
                            Close
                        </button>
                    </div>
                </div>,
                document.body
            )}
        </div>
    );
};

export default MessageBubble;