import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { showToast } from '../../utils/toast';
import { useCredits } from '../../context/CreditContext';
import NorthIndianChart from '../Charts/NorthIndianChart';
import {
    stopAndRevokePodcastPlayback,
    registerPodcastPlayback,
    base64ToAudioBlob,
    podcastLangFromUiLanguage,
} from './podcastPlayback';

const MessageBubble = ({ message, language = 'english', sessionId = null, onFollowUpClick, onChartRefClick, onRestartPolling, onDeleteMessage }) => {
    const { podcastCost, refreshBalance } = useCredits();
    const [showActions, setShowActions] = useState(false);
    const [tooltipModal, setTooltipModal] = useState({ show: false, term: '', definition: '' });
    const messageRef = useRef(null);

    const insightsKey = message?.processingClientId ?? message?.messageId ?? null;
    const chartInsights = Array.isArray(message?.chartInsights) ? message.chartInsights : [];
    const [insightIndex, setInsightIndex] = useState(0);

    useEffect(() => {
        if (!insightsKey) return;
        if (!chartInsights.length) return;

        setInsightIndex(0);
        const interval = setInterval(() => {
            setInsightIndex((prev) => (prev + 1) % chartInsights.length);
        }, 10000);

        return () => clearInterval(interval);
    }, [insightsKey, chartInsights.length]);

    const [podcastModalOpen, setPodcastModalOpen] = useState(false);
    const [podcastModalMode, setPodcastModalMode] = useState('loading');
    const [podcastLoading, setPodcastLoading] = useState(false);
    const [podcastCurrentTime, setPodcastCurrentTime] = useState(0);
    const [podcastDuration, setPodcastDuration] = useState(0);
    const [podcastIsPlaying, setPodcastIsPlaying] = useState(false);
    const [podcastPlaybackRate, setPodcastPlaybackRate] = useState(1);
    const podcastAudioRef = useRef(null);
    const podcastFetchAbortRef = useRef(null);
    const podcastBlobRef = useRef(null);
    const podcastSourceKeyRef = useRef(null);

    const getCleanMessageText = useCallback(() => {
        if (!message?.content) return '';
        return message.content
            .replace(/<[^>]*>/g, '')
            .replace(/\*\*(.*?)\*\*/g, '$1')
            .replace(/\*(.*?)\*/g, '$1')
            .replace(/&quot;/g, '"')
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&#39;/g, "'")
            .replace(/&nbsp;/g, ' ')
            .trim();
    }, [message?.content]);

    useEffect(() => {
        return () => {
            podcastFetchAbortRef.current?.abort();
            if (podcastAudioRef.current) {
                podcastAudioRef.current.pause();
                podcastAudioRef.current.src = '';
            }
            if (podcastBlobRef.current) {
                URL.revokeObjectURL(podcastBlobRef.current);
                podcastBlobRef.current = null;
            }
        };
    }, []);

    const attachPodcastAudioListeners = useCallback((audio) => {
        audio.ontimeupdate = () => setPodcastCurrentTime(audio.currentTime || 0);
        audio.onloadedmetadata = () => setPodcastDuration(audio.duration && Number.isFinite(audio.duration) ? audio.duration : 0);
        audio.onplay = () => setPodcastIsPlaying(true);
        audio.onpause = () => setPodcastIsPlaying(false);
        audio.onended = () => {
            setPodcastIsPlaying(false);
            setPodcastCurrentTime(0);
        };
    }, []);

    const closePodcastModal = useCallback(() => {
        podcastFetchAbortRef.current?.abort();
        podcastFetchAbortRef.current = null;
        stopAndRevokePodcastPlayback();
        if (podcastAudioRef.current) {
            podcastAudioRef.current.pause();
            podcastAudioRef.current.src = '';
        }
        podcastBlobRef.current = null;
        podcastSourceKeyRef.current = null;
        setPodcastModalOpen(false);
        setPodcastModalMode('loading');
        setPodcastLoading(false);
        setPodcastIsPlaying(false);
        setPodcastCurrentTime(0);
        setPodcastDuration(0);
    }, []);

    const fetchAndPlayPodcast = useCallback(async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            showToast('Please log in to listen to podcasts.', 'error');
            return;
        }
        const cleanText = getCleanMessageText();
        if (!cleanText) return;

        const langCode = podcastLangFromUiLanguage(language);
        const mid = message.messageId != null ? String(message.messageId) : null;

        podcastFetchAbortRef.current?.abort();
        const ac = new AbortController();
        podcastFetchAbortRef.current = ac;

        setPodcastModalOpen(true);
        setPodcastModalMode('loading');
        setPodcastLoading(true);
        setPodcastCurrentTime(0);
        setPodcastDuration(0);

        try {
            const res = await fetch('/api/tts/podcast', {
                method: 'POST',
                signal: ac.signal,
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message_content: cleanText,
                    language: langCode,
                    ...(mid ? { message_id: mid } : {}),
                    ...(sessionId ? { session_id: sessionId } : {}),
                    preview: (cleanText || message.content || '').slice(0, 150),
                    ...(message.native_name ? { native_name: message.native_name } : {}),
                }),
            });

            if (res.status === 402) {
                const cost = podcastCost ?? 2;
                showToast(`Insufficient credits. You need ${cost} credits to generate this podcast.`, 'error');
                refreshBalance();
                closePodcastModal();
                return;
            }

            if (!res.ok) {
                const t = await res.text().catch(() => '');
                throw new Error(t || `Podcast request failed (${res.status})`);
            }

            const data = await res.json();
            const b64 = data?.audio;
            if (!b64 || typeof b64 !== 'string') {
                throw new Error('No audio in response');
            }

            const blob = base64ToAudioBlob(b64);
            const url = URL.createObjectURL(blob);

            if (!podcastAudioRef.current) {
                podcastAudioRef.current = new Audio();
                attachPodcastAudioListeners(podcastAudioRef.current);
            }
            const audio = podcastAudioRef.current;
            registerPodcastPlayback(audio, url);
            podcastBlobRef.current = url;
            podcastSourceKeyRef.current = `${mid || 'noid'}_${langCode}`;

            audio.playbackRate = podcastPlaybackRate;
            audio.src = url;
            await audio.play();

            setPodcastModalMode('playing');
            setPodcastLoading(false);
            if (data.cached !== true) {
                refreshBalance();
            }
        } catch (e) {
            if (e?.name === 'AbortError') {
                return;
            }
            console.error('[Podcast]', e);
            showToast('Could not play podcast. Please try again.', 'error');
            closePodcastModal();
        }
    }, [
        attachPodcastAudioListeners,
        closePodcastModal,
        getCleanMessageText,
        language,
        message.content,
        message.messageId,
        message.native_name,
        podcastCost,
        podcastPlaybackRate,
        refreshBalance,
        sessionId,
    ]);

    const handlePodcastButtonClick = useCallback(async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            showToast('Please log in to listen to podcasts.', 'error');
            return;
        }
        const cleanText = getCleanMessageText();
        if (!cleanText) return;

        const langCode = podcastLangFromUiLanguage(language);
        const mid = message.messageId != null ? String(message.messageId) : null;
        const sourceKey = `${mid || 'noid'}_${langCode}`;

        if (podcastSourceKeyRef.current === sourceKey && podcastAudioRef.current?.src && !podcastLoading) {
            setPodcastModalOpen(true);
            setPodcastModalMode('playing');
            const a = podcastAudioRef.current;
            if (a.paused) {
                await a.play().catch(() => {});
            }
            return;
        }

        let cached = false;
        if (mid) {
            try {
                const cr = await fetch(
                    `/api/tts/podcast/check-cache?message_id=${encodeURIComponent(mid)}&lang=${encodeURIComponent(langCode)}`,
                    { headers: { Authorization: `Bearer ${token}` } }
                );
                if (cr.ok) {
                    const cd = await cr.json();
                    cached = cd.cached === true;
                }
            } catch (_) {
                /* fall through to confirm */
            }
        }

        if (!cached) {
            const cost = podcastCost ?? 2;
            const ok = window.confirm(
                `Listen as podcast?\n\n${cost} credits will be used when the audio is first generated. Replays are free when already saved.`
            );
            if (!ok) return;
        }

        await fetchAndPlayPodcast();
    }, [fetchAndPlayPodcast, getCleanMessageText, language, message.messageId, podcastCost, podcastLoading]);

    const handlePodcastTogglePause = () => {
        const audio = podcastAudioRef.current;
        if (!audio || !audio.src) return;
        if (audio.paused) {
            audio.play().catch(() => {});
        } else {
            audio.pause();
        }
    };

    const handlePodcastSeek = (value) => {
        const audio = podcastAudioRef.current;
        if (!audio || !Number.isFinite(+value)) return;
        audio.currentTime = +value;
        setPodcastCurrentTime(audio.currentTime);
    };

    const handlePodcastRateChange = (rate) => {
        const r = parseFloat(rate, 10) || 1;
        setPodcastPlaybackRate(r);
        if (podcastAudioRef.current) {
            podcastAudioRef.current.playbackRate = r;
        }
    };

    const handlePodcastShare = async () => {
        const blobUrl = podcastBlobRef.current;
        if (!blobUrl) {
            showToast('Nothing to share yet.', 'error');
            return;
        }
        try {
            const res = await fetch(blobUrl);
            const blob = await res.blob();
            const file = new File([blob], `AstroRoshni-Podcast-${Date.now()}.mp3`, { type: 'audio/mpeg' });
            if (navigator.share && typeof navigator.canShare === 'function' && navigator.canShare({ files: [file] })) {
                await navigator.share({ files: [file], title: 'AstroRoshni podcast' });
            } else {
                const a = document.createElement('a');
                a.href = blobUrl;
                a.download = `AstroRoshni-Podcast-${Date.now()}.mp3`;
                a.click();
                showToast('Download started.', 'success');
            }
        } catch (e) {
            console.error('[Podcast share]', e);
            showToast('Could not share or download.', 'error');
        }
    };

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
        
        // console.log('🔍 Format Debug:', {
        //     hasTerms: !!message.terms,
        //     termsCount: message.terms?.length,
        //     hasGlossary: !!message.glossary,
        //     glossaryKeys: Object.keys(message.glossary || {}),
        //     contentPreview: content.substring(0, 200)
        // });
        
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
        
        // console.log('🔍 After markdown, before terms:', formatted.substring(0, 300));
        
        // 7. PROCESS TERMS - auto-wrap terms found in glossary
        if (message.terms && message.glossary && Object.keys(message.glossary).length > 0) {
            // console.log('🔍 Processing terms:', message.terms);
            
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
        
        // 8. Headings (lighter, non-overwhelming)
        formatted = formatted.replace(/#### (.*?)\n/g, (match, header) => {
            return `<h4 class="chat-subheader">${header.trim()}</h4>\n`;
        });
        formatted = formatted.replace(/### (.*?)\n/g, (match, header) => {
            return `<h3 class="chat-section-title">${header.trim()}</h3>\n`;
        });

        // 9. Lists (keep them readable without heavy card chrome)
        // Some responses return dash bullets inline on one line:
        // "... sentence. - Bullet one - Bullet two"
        // Normalize those into line-start bullets before list conversion.
        formatted = formatted.replace(/([.:!?])\s-\s(?=(?:\*\*)?[A-Z0-9])/g, '$1\n- ');
        formatted = formatted.replace(/(\d+\.\s+[^\n]+)/g, '<p class="numbered-item">$1</p>');
        formatted = formatted.replace(/(^|\n)-\s+(.+)/g, '$1<li class="chat-bullet">• $2</li>');
        formatted = formatted.replace(/\n\*\s+(.+)/g, '<li class="chat-bullet">• $1</li>');
        formatted = formatted.replace(/(<li class="chat-bullet">.*?<\/li>)/gs, '<ul class="chat-list">$1</ul>');

        // 10. Wrap into a single response container to avoid many "cards"
        formatted = `<div class="chat-response">${formatted.trim()}</div>`;
        return formatted;
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
                    {message.messageId && (
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
                {/* Beta Notice for Timeline Predictions */}
                {message.role === 'assistant' && !message.isTyping && !message.isProcessing && message.message_type !== 'clarification' && (
                    <div style={{
                        backgroundColor: 'rgba(255, 152, 0, 0.1)',
                        borderLeft: '3px solid #FF9800',
                        borderRadius: '8px',
                        padding: '10px',
                        marginBottom: '12px',
                        fontSize: '12px',
                        color: '#E65100',
                        fontWeight: '600',
                        lineHeight: '16px'
                    }}>
                        ⚠️ BETA NOTICE: Timeline predictions are experimental. Please use logic and discretion.
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
                    {(message.isTyping || message.isProcessing) ? (
                        <>
                            <div className="processing-chart-skeleton">
                                <div style={{ fontWeight: 900, marginBottom: 6 }}>Chart in progress...</div>
                                {chartInsights.length > 0 && message.chartData ? (
                                    (() => {
                                        const currentInsight = chartInsights[insightIndex] || chartInsights[0];
                                        const houseNumberRaw = currentInsight?.house_number ?? currentInsight?.house ?? currentInsight?.houseNumber;
                                        const houseNumber = parseInt(houseNumberRaw, 10);
                                        return (
                                            <>
                                                <div style={{
                                                    width: '100%',
                                                    maxWidth: 420,
                                                    margin: '0 auto 10px auto',
                                                    borderRadius: 14,
                                                    border: '1px solid rgba(255,107,53,0.25)',
                                                    background: 'rgba(255,107,53,0.05)',
                                                    padding: 10,
                                                    overflow: 'hidden'
                                                }}>
                                                    <NorthIndianChart
                                                        chartData={message.chartData}
                                                        showDegreeNakshatra={false}
                                                        chartRefHighlight={
                                                            Number.isFinite(houseNumber)
                                                                ? { type: 'house', value: houseNumber }
                                                                : null
                                                        }
                                                    />
                                                </div>
                                                <div style={{ color: '#7c2d12', opacity: 0.95, lineHeight: 1.35, whiteSpace: 'pre-wrap', fontSize: 14 }}>
                                                    {currentInsight?.message || message.loadingMessage || message.content}
                                                </div>
                                            </>
                                        );
                                    })()
                                ) : (
                                    <>
                                        {message.summary_image && (
                                            <div
                                                style={{
                                                    margin: '0 auto 12px auto',
                                                    borderRadius: 12,
                                                    overflow: 'hidden',
                                                    boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
                                                    background: 'linear-gradient(135deg, rgba(255,107,53,0.1), rgba(138,43,226,0.1))',
                                                    border: '2px solid rgba(255,107,53,0.3)',
                                                    maxWidth: 500
                                                }}
                                            >
                                                <img
                                                    src={
                                                        message.summary_image.startsWith('data:')
                                                            ? message.summary_image
                                                            : `data:image/png;base64,${message.summary_image}`
                                                    }
                                                    alt="Analysis Summary"
                                                    style={{ width: '100%', height: 'auto', display: 'block' }}
                                                    onError={(e) => {
                                                        e.currentTarget.style.display = 'none';
                                                        if (e.currentTarget?.parentElement) e.currentTarget.parentElement.style.display = 'none';
                                                    }}
                                                />
                                            </div>
                                        )}
                                        {message.chartData && (
                                            <div style={{
                                                width: '100%',
                                                margin: '0 auto 12px auto',
                                                padding: '10px 12px',
                                                borderRadius: 12,
                                                border: '1px solid rgba(255,107,53,0.25)',
                                                background: 'rgba(255,107,53,0.06)'
                                            }}>
                                                <div style={{ fontWeight: 800, marginBottom: 6, color: '#7c2d12' }}>
                                                    Chart essence
                                                </div>
                                                <div style={{
                                                    display: 'grid',
                                                    gridTemplateColumns: '1fr 1fr 1fr',
                                                    gap: 8,
                                                    alignItems: 'start'
                                                }}>
                                                    <div>
                                                        <div style={{ fontSize: 11, color: '#7c2d12', opacity: 0.8 }}>☀️ Sun</div>
                                                        <div style={{ fontSize: 12, fontWeight: 700 }}>
                                                            {message.chartData?.planets?.Sun?.sign_name || '...'}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <div style={{ fontSize: 11, color: '#7c2d12', opacity: 0.8 }}>🌙 Moon</div>
                                                        <div style={{ fontSize: 12, fontWeight: 700 }}>
                                                            {message.chartData?.planets?.Moon?.sign_name || '...'}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <div style={{ fontSize: 11, color: '#7c2d12', opacity: 0.8 }}>⬆️ Asc</div>
                                                        <div style={{ fontSize: 12, fontWeight: 700 }}>
                                                            {message.chartData?.houses?.[0]?.sign_name || '...'}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div style={{ marginTop: 10, fontSize: 11, color: '#7c2d12', opacity: 0.9 }}>
                                                    Graha Drishti facets: {
                                                        (message.chartData?.houses || []).reduce((acc, h) => acc + (h?.graha_drishti?.length || 0), 0)
                                                    }
                                                </div>
                                            </div>
                                        )}
                                        <div style={{ color: '#7c2d12', opacity: 0.9, lineHeight: 1.35, whiteSpace: 'pre-wrap' }}>
                                            {message.loadingMessage || message.content}
                                        </div>
                                    </>
                                )}
                            </div>
                        </>
                    ) : (
                        <>
                            {/* Always use ResponseRenderer for assistant messages */}
                            {message.role === 'assistant' ? (
                                <div dangerouslySetInnerHTML={{ __html: formatContent(message.content, message) }} />
                            ) : (
                                <div dangerouslySetInnerHTML={{ __html: formatContent(message.content) }} />
                            )}
                        </>
                    )}
                </div>
                
                {/* Action buttons positioned like mobile */}
                {!message.isTyping &&
                    !message.isProcessing &&
                    message.messageId &&
                    message.content &&
                    message.content.trim().length > 0 && (
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
                        {message.role === 'assistant' && (
                            <button
                                type="button"
                                className="action-btn podcast-btn"
                                style={{
                                    width: '20px',
                                    height: '20px',
                                    minWidth: '20px',
                                    padding: '0',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    opacity: podcastLoading ? 0.5 : 1,
                                }}
                                disabled={podcastLoading}
                                onClick={handlePodcastButtonClick}
                                title="Listen as podcast"
                            >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                                    <path d="M12 3v9.28c-.47-.17-.97-.28-1.5-.28C8.01 12 6 14.01 6 16.5S8.01 21 10.5 21c2.31 0 4.2-1.75 4.45-4H15V6h4V3h-7zm-1.5 16.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
                                </svg>
                            </button>
                        )}
                        <button
                            className="action-btn whatsapp-btn"
                            style={{
                                width: '20px',
                                height: '20px',
                                minWidth: '20px',
                                padding: '0',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                            onClick={handleWhatsAppShare}
                            title="Share on WhatsApp"
                        >
                            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.465 3.488"/>
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
            
            {podcastModalOpen &&
                createPortal(
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
                            zIndex: 10001,
                        }}
                        onClick={closePodcastModal}
                        role="presentation"
                    >
                        <div
                            style={{
                                backgroundColor: 'white',
                                padding: '22px',
                                borderRadius: '12px',
                                maxWidth: '400px',
                                width: '90%',
                                margin: '20px',
                                boxShadow: '0 4px 24px rgba(0, 0, 0, 0.25)',
                            }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <h3 style={{ margin: '0 0 12px 0', color: '#c2410c', fontSize: '18px' }}>
                                Podcast
                            </h3>
                            {podcastModalMode === 'loading' || podcastLoading ? (
                                <p style={{ margin: 0, lineHeight: 1.5, color: '#444' }}>
                                    Generating your podcast… this can take up to a couple of minutes.
                                </p>
                            ) : (
                                <>
                                    <div style={{ marginBottom: '12px', fontSize: '12px', color: '#666' }}>
                                        {(() => {
                                            const fmt = (t) => {
                                                if (!Number.isFinite(t) || t < 0) return '0:00';
                                                const m = Math.floor(t / 60);
                                                const sec = Math.floor(t % 60);
                                                return `${m}:${sec.toString().padStart(2, '0')}`;
                                            };
                                            return (
                                                <>
                                                    {fmt(podcastCurrentTime)} / {fmt(podcastDuration)}
                                                </>
                                            );
                                        })()}
                                    </div>
                                    <input
                                        type="range"
                                        min={0}
                                        max={podcastDuration > 0 ? podcastDuration : 1}
                                        step={0.1}
                                        value={Math.min(podcastCurrentTime, podcastDuration > 0 ? podcastDuration : 0)}
                                        onChange={(e) => handlePodcastSeek(parseFloat(e.target.value))}
                                        style={{ width: '100%', marginBottom: '14px' }}
                                    />
                                    <div
                                        style={{
                                            display: 'flex',
                                            flexWrap: 'wrap',
                                            gap: '8px',
                                            alignItems: 'center',
                                            marginBottom: '12px',
                                        }}
                                    >
                                        <button
                                            type="button"
                                            onClick={handlePodcastTogglePause}
                                            style={{
                                                padding: '8px 14px',
                                                borderRadius: '8px',
                                                border: 'none',
                                                background: '#ea580c',
                                                color: 'white',
                                                cursor: 'pointer',
                                                fontSize: '14px',
                                            }}
                                        >
                                            {podcastIsPlaying ? 'Pause' : 'Play'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={closePodcastModal}
                                            style={{
                                                padding: '8px 14px',
                                                borderRadius: '8px',
                                                border: '1px solid #ccc',
                                                background: '#f3f4f6',
                                                cursor: 'pointer',
                                                fontSize: '14px',
                                            }}
                                        >
                                            Stop & close
                                        </button>
                                        <label style={{ fontSize: '13px', color: '#374151' }}>
                                            Speed{' '}
                                            <select
                                                value={String(podcastPlaybackRate)}
                                                onChange={(e) => handlePodcastRateChange(e.target.value)}
                                                style={{ marginLeft: 4 }}
                                            >
                                                <option value="0.75">0.75×</option>
                                                <option value="1">1×</option>
                                                <option value="1.25">1.25×</option>
                                                <option value="1.5">1.5×</option>
                                                <option value="2">2×</option>
                                            </select>
                                        </label>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={handlePodcastShare}
                                        style={{
                                            padding: '8px 14px',
                                            borderRadius: '8px',
                                            border: '1px solid #ea580c',
                                            background: 'white',
                                            color: '#c2410c',
                                            cursor: 'pointer',
                                            fontSize: '14px',
                                            width: '100%',
                                        }}
                                    >
                                        Share or download MP3
                                    </button>
                                </>
                            )}
                        </div>
                    </div>,
                    document.body
                )}

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