import React, { useState, useRef } from 'react';
import textToSpeech from '../../utils/textToSpeech';
import { showToast } from '../../utils/toast';

const MessageBubble = ({ message, language = 'english', onFollowUpClick, onChartRefClick }) => {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [hasError, setHasError] = useState(false);
    const [selectedVoice, setSelectedVoice] = useState(null);
    const [voices, setVoices] = useState([]);
    const [currentChunk, setCurrentChunk] = useState(0);
    const [totalChunks, setTotalChunks] = useState(0);
    const [showActions, setShowActions] = useState(false);
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
    const formatContent = (content) => {
        // First, normalize line breaks
        let formatted = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        
        // Handle Follow-up Questions section
        formatted = formatted.replace(/<div class="follow-up-questions">([\s\S]*?)<\/div>/g, (match, questions) => {
            const questionList = questions.trim().split('\n')
                .filter(q => q.trim())
                .map(q => `<button class="follow-up-btn">${q.trim()}</button>`)
                .join('');
            return `<div class="follow-up-questions">${questionList}</div>`;
        });
        
        // Handle Final Thoughts section specially
        formatted = formatted.replace(/(### Final Thoughts[\s\S]*?)(?=###|$)/g, (match, finalThoughts) => {
            const cleanContent = finalThoughts
                .replace(/### Final Thoughts\n?/, '')
                .replace(/\*\*(.*?)\*\*/gs, '<strong class="chat-bold">$1</strong>')
                .replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em class="chat-italic">$1</em>')
                .trim();
            return `<div class="final-thoughts-card"><strong>Final Thoughts</strong><br><br>${cleanContent}</div>`;
        });
        
        // Process headers - handle both ### and standalone # symbols
        formatted = formatted.replace(/### (.*?)\n/g, '<h3 class="chat-header">◆ $1 ◆</h3>\n\n');
        
        // Remove standalone # symbols that appear alone on lines
        formatted = formatted.replace(/^\s*#\s*$/gm, '');
        
        // Clean up any remaining # symbols at start of lines
        formatted = formatted.replace(/^\s*#+\s*/gm, '');
        
        // Process bold text
        formatted = formatted.replace(/\*\*(.*?)\*\*/gs, '<strong class="chat-bold">$1</strong>');
        
        // Process italics (single asterisks not part of bold)
        formatted = formatted.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em class="chat-italic">$1</em>');
        
        // Clean up multiple line breaks and split into paragraphs
        formatted = formatted.replace(/\n\s*\n\s*\n+/g, '\n\n');
        const paragraphs = formatted.split(/\n\s*\n/);
        
        return paragraphs.map(paragraph => {
            paragraph = paragraph.trim();
            if (!paragraph) return '';
            
            // Skip if already processed as final-thoughts-card
            if (paragraph.includes('final-thoughts-card')) {
                return paragraph;
            }
            
            // Check if it's a numbered list paragraph
            if (/^\d+\./m.test(paragraph)) {
                const items = paragraph.split(/\n(?=\d+\.)/)
                    .map(item => {
                        const match = item.match(/^(\d+\.)\s*(.*)$/s);
                        if (match) {
                            return `<li class="chat-numbered">▸ ${match[2].replace(/\n/g, ' ').trim()}</li>`;
                        }
                        return '';
                    })
                    .filter(item => item);
                return `<ol class="chat-numbered-list">${items.join('')}</ol>`;
            }
            
            // Check if it's a bullet list paragraph
            if (/^[•*]/m.test(paragraph)) {
                const items = paragraph.split(/\n(?=[•*])/)
                    .map(item => {
                        const match = item.match(/^[•*]\s*(.*)$/s);
                        if (match) {
                            return `<li class="chat-bullet">• ${match[1].replace(/\n/g, ' ').trim()}</li>`;
                        }
                        return '';
                    })
                    .filter(item => item);
                return `<ul class="chat-list">${items.join('')}</ul>`;
            }
            
            // Check for Key Insights section
            if (paragraph.startsWith('Key Insights')) {
                const lines = paragraph.split('\n');
                const title = lines[0];
                const body = lines.slice(1).join(' ').trim();
                return `<div class="chat-insights"><h4>★ ${title}</h4><div class="insights-content">${body}</div></div>`;
            }
            
            // Regular paragraph - replace single line breaks with spaces
            return `<p class="chat-paragraph">${paragraph.replace(/\n/g, ' ')}</p>`;
        }).filter(p => p).join('');
    };

    const handleSpeak = () => {
        console.log('Speak button clicked for message:', message);
        setHasError(false);
        
        // Always cancel any existing speech first
        window.speechSynthesis.cancel();
        
        if (isSpeaking) {
            setIsSpeaking(false);
        } else {
            if (message.content && message.content.trim()) {
                // Clean the text first
                let cleanText = message.content
                    .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold
                    .replace(/\*(.*?)\*/g, '$1')     // Remove italics
                    .replace(/###\s*(.*?)$/gm, '$1') // Remove headers
                    .replace(/•\s*/g, '')            // Remove bullets
                    .replace(/\n+/g, '. ')           // Replace line breaks
                    .replace(/\s+/g, ' ')            // Normalize spaces
                    .trim();
                
                console.log('Full text length for speech:', cleanText.length);
                
                // Break text into chunks for reliable speech synthesis
                const chunkSize = 1000; // Characters per chunk
                const chunks = [];
                for (let i = 0; i < cleanText.length; i += chunkSize) {
                    chunks.push(cleanText.substring(i, i + chunkSize));
                }
                
                setTotalChunks(chunks.length);
                setCurrentChunk(0);
                console.log(`Breaking into ${chunks.length} chunks for speech`);
                
                const speakChunk = (chunkIndex) => {
                    if (chunkIndex >= chunks.length) {
                        console.log('All chunks completed');
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
                        console.log(`Speaking chunk ${chunkIndex + 1}/${chunks.length}`);
                        setIsSpeaking(true);
                        setCurrentChunk(chunkIndex + 1);
                    };
                    
                    utterance.onend = () => {
                        console.log(`Chunk ${chunkIndex + 1} completed`);
                        // Speak next chunk after a brief pause
                        setTimeout(() => speakChunk(chunkIndex + 1), 100);
                    };
                    
                    utterance.onerror = (error) => {
                        if (error.error !== 'interrupted') {
                            console.error('Speech error:', error);
                            setHasError(true);
                        }
                        setIsSpeaking(false);
                    };
                    
                    window.speechSynthesis.speak(utterance);
                };
                
                // Start speaking from first chunk
                speakChunk(0);
            } else {
                console.warn('No content to speak');
            }
        }
    };

    return (
        <div 
            ref={messageRef}
            className={`message-bubble ${message.role} ${message.isTyping ? 'typing' : ''}`}
            onTouchStart={isMobile() ? handleLongPress : undefined}
            onClick={() => isMobile() && showActions && setShowActions(false)}
        >
            {/* Action buttons */}
            {showActions && !message.isTyping && isMobile() && (
                <div className="message-actions">
                    <button 
                        className="action-btn whatsapp-btn"
                        onClick={handleWhatsAppShare}
                        title="Share on WhatsApp"
                    >
                        📱
                    </button>
                </div>
            )}
            
            <div className="message-content">
                {message.role === 'assistant' && !message.isTyping && textToSpeech.isSupported && message.content && (
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
                    dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
                    onClick={(e) => {
                        if (e.target.classList.contains('follow-up-btn')) {
                            const question = e.target.textContent.replace(/^[\u{1F300}-\u{1F9FF}\s]+/u, '').trim();
                            onFollowUpClick && onFollowUpClick(question);
                        } else if (e.target.classList.contains('chart-ref')) {
                            const type = e.target.dataset.planet ? 'planet' : 
                                        e.target.dataset.house ? 'house' : 'sign';
                            const value = e.target.dataset.planet || e.target.dataset.house || e.target.dataset.sign;
                            onChartRefClick && onChartRefClick({ type, value });
                        }
                    }}
                />
                {message.isTyping && (
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
        </div>
    );
};

export default MessageBubble;