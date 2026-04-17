import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { jsPDF } from 'jspdf';
import { showToast } from '../../utils/toast';
import { useCredits } from '../../context/CreditContext';
import NorthIndianChart from '../Charts/NorthIndianChart';
import {
    stopAndRevokePodcastPlayback,
    registerPodcastPlayback,
    base64ToAudioBlob,
    podcastLangFromUiLanguage,
} from './podcastPlayback';

/** Lucide-style 24×24 outline icons to match mobile Ionicons outline look */
const IC = {
    w: 18,
    h: 18,
    vb: '0 0 24 24',
    s: (props) => ({ fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round', ...props }),
};

const IconCopyOutline = (p) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={IC.w} height={IC.h} viewBox={IC.vb} {...IC.s(p)}>
        <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
        <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
    </svg>
);
const IconShareSocialOutline = (p) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={IC.w} height={IC.h} viewBox={IC.vb} {...IC.s(p)}>
        <circle cx="18" cy="5" r="3" />
        <circle cx="6" cy="12" r="3" />
        <circle cx="18" cy="19" r="3" />
        <line x1="8.59" x2="15.42" y1="13.51" y2="17.49" />
        <line x1="15.41" x2="8.59" y1="6.51" y2="10.49" />
    </svg>
);
const IconRadioOutline = (p) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={IC.w} height={IC.h} viewBox={IC.vb} {...IC.s(p)}>
        <path d="M12 12h.01" />
        <path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14" />
    </svg>
);
const IconDocumentOutline = (p) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={IC.w} height={IC.h} viewBox={IC.vb} {...IC.s(p)}>
        <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
        <path d="M14 2v4a2 2 0 0 0 2 2h4" />
        <path d="M10 9H8" />
        <path d="M16 13H8" />
        <path d="M16 17H8" />
    </svg>
);
const IconTrashOutline = (p) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={IC.w} height={IC.h} viewBox={IC.vb} {...IC.s(p)}>
        <path d="M3 6h18" />
        <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
        <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
        <line x1="10" x2="10" y1="11" y2="17" />
        <line x1="14" x2="14" y1="11" y2="17" />
    </svg>
);
const IconRefreshOutline = (p) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={IC.w} height={IC.h} viewBox={IC.vb} {...IC.s(p)}>
        <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
        <path d="M21 3v5h-5" />
        <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
        <path d="M8 16H3v5" />
    </svg>
);

/** Split follow-up block into separate chip labels (newline list or single-line emoji-led segments). */
const splitFollowUpQuestionsBlock = (inner) => {
    const raw = (inner || '').trim();
    if (!raw) return [];
    const byLines = raw.split(/\n/).map((l) => l.trim()).filter(Boolean);
    let items;
    if (byLines.length > 1) {
        items = byLines;
    } else {
        const one = byLines[0] || raw;
        const splitMulti = one
            .split(/(?=[📅🔮💼🌟❓💡🎯⭐🔆📆💎🤔✨📌🔔])/u)
            .map((s) => s.trim())
            .filter(Boolean);
        items = splitMulti.length > 1 ? splitMulti : [one];
    }
    return items.map((q) => q.replace(/^-\s*/, '').trim()).filter(Boolean);
};

const escapeHtmlTextContent = (s) =>
    String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');

/** Block-level starts we must not wrap in <p> (invalid / breaks layout). */
const CHAT_BLOCK_START_RE = /^<(h[34]|ul\b|ol\b|div\b|p\b|blockquote|table|hr\b)/i;

/**
 * HTML ignores raw newlines; split on blank lines into paragraphs and single newlines into <br>.
 */
const applyChatProseParagraphs = (html) => {
    if (!html || !html.trim()) return html;
    const normalized = String(html).replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    const segments = normalized.split(/\n{2,}/);
    const parts = [];
    for (let seg of segments) {
        seg = seg.trim();
        if (!seg) {
            parts.push('<div class="chat-prose-spacer" aria-hidden="true"></div>');
            continue;
        }
        if (CHAT_BLOCK_START_RE.test(seg)) {
            parts.push(seg.replace(/\n/g, '<br />'));
        } else {
            parts.push(`<p class="chat-prose-block">${seg.replace(/\n/g, '<br />')}</p>`);
        }
    }
    return parts.join('');
};

/** Ensure glossary is a non-array object; API/history may omit or stringify oddly. */
const normalizeGlossaryObject = (g) => {
    if (g == null) return {};
    if (typeof g === 'string') {
        try {
            const p = JSON.parse(g);
            return typeof p === 'object' && p !== null && !Array.isArray(p) ? p : {};
        } catch {
            return {};
        }
    }
    if (typeof g !== 'object' || Array.isArray(g)) return {};
    return g;
};

const getGlossaryDefinition = (glossary, termId) => {
    if (!termId || !glossary) return undefined;
    const raw = String(termId).trim();
    if (glossary[raw] !== undefined) return { key: raw, definition: glossary[raw] };
    const low = raw.toLowerCase();
    const found = Object.keys(glossary).find((k) => k.toLowerCase() === low);
    if (found !== undefined) return { key: found, definition: glossary[found] };
    return undefined;
};

const MessageBubble = ({
    message,
    language = 'english',
    sessionId = null,
    onFollowUpClick,
    onChartRefClick,
    onRestartPolling,
    onDeleteMessage,
    onNativeGateOpenSelectNative,
    onNativeGateOpenAddProfile,
    podcastAutoLaunchMessageId = null,
    podcastAutoLaunchKey = 0,
}) => {
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
    const [pdfGenerating, setPdfGenerating] = useState(false);
    const [podcastCurrentTime, setPodcastCurrentTime] = useState(0);
    const [podcastDuration, setPodcastDuration] = useState(0);
    const [podcastIsPlaying, setPodcastIsPlaying] = useState(false);
    const [podcastPlaybackRate, setPodcastPlaybackRate] = useState(1);
    const podcastAudioRef = useRef(null);
    const podcastFetchAbortRef = useRef(null);
    const podcastBlobRef = useRef(null);
    const podcastSourceKeyRef = useRef(null);

    const isNativeGate = useMemo(
        () =>
            message.message_type === 'native_gate' ||
            message.intent_gate === 'create_native' ||
            (message.gate_metadata && message.gate_metadata.intent_gate === 'create_native'),
        [message.message_type, message.intent_gate, message.gate_metadata],
    );

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

    const lastPodcastPromoKeyRef = useRef(0);
    useEffect(() => {
        if (!podcastAutoLaunchKey || podcastAutoLaunchMessageId == null) return;
        const mid = message.messageId != null ? String(message.messageId) : '';
        if (!mid || mid !== String(podcastAutoLaunchMessageId)) return;
        if (message.role !== 'assistant') return;
        if (message.isTyping || message.isProcessing) return;
        if (message.message_type === 'clarification' || isNativeGate) return;
        if (lastPodcastPromoKeyRef.current === podcastAutoLaunchKey) return;
        lastPodcastPromoKeyRef.current = podcastAutoLaunchKey;
        const timer = setTimeout(() => {
            fetchAndPlayPodcast();
        }, 350);
        return () => clearTimeout(timer);
    }, [
        podcastAutoLaunchKey,
        podcastAutoLaunchMessageId,
        message.role,
        message.messageId,
        message.isTyping,
        message.isProcessing,
        message.message_type,
        isNativeGate,
        fetchAndPlayPodcast,
    ]);

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
    
    const handleShareMessage = async () => {
        const cleanText = cleanTextForCopy(message.content);
        const shareText = `☀️ AstroRoshni Prediction\n\n${cleanText}\n\nShared from AstroRoshni App`;
        const waText = `🔮 *AstroRoshni Prediction*\n\n${cleanText}\n\n_Shared from AstroRoshni App_`;
        const openWhatsApp = () => {
            window.open(`https://wa.me/?text=${encodeURIComponent(waText)}`, '_blank');
            showToast('Opening WhatsApp...', 'success');
        };
        try {
            if (navigator.share) {
                await navigator.share({ text: shareText, title: 'AstroRoshni' });
                showToast('Shared', 'success');
            } else {
                openWhatsApp();
            }
        } catch (e) {
            if (e && e.name === 'AbortError') return;
            openWhatsApp();
        }
        setShowActions(false);
    };

    const handleMessagePdf = useCallback(async () => {
        const cleanText = getCleanMessageText();
        if (!cleanText) return;
        setPdfGenerating(true);
        try {
            const doc = new jsPDF({ unit: 'pt', format: 'a4' });
            const margin = 40;
            const pageW = doc.internal.pageSize.getWidth();
            const pageH = doc.internal.pageSize.getHeight();
            const maxWidth = pageW - margin * 2;
            const lines = doc.splitTextToSize(cleanText, maxWidth);
            let y = margin;
            const lineHeight = 16;
            const title = 'AstroRoshni';
            doc.setFontSize(12);
            doc.setFont('helvetica', 'bold');
            doc.text(title, margin, y);
            y += lineHeight * 1.25;
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(10);
            lines.forEach((line) => {
                if (y > pageH - margin) {
                    doc.addPage();
                    y = margin;
                }
                doc.text(line, margin, y);
                y += lineHeight;
            });
            doc.save(`astroroshni-message-${Date.now()}.pdf`);
            showToast('PDF downloaded', 'success');
        } catch (e) {
            console.error('[Message PDF]', e);
            showToast('Could not create PDF', 'error');
        } finally {
            setPdfGenerating(false);
        }
    }, [getCleanMessageText]);
    
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
            if (showActions && isMobile() && !event.target.closest('.message-bubble-mobile-actions')) {
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
        
        // 4. Handle Follow-up Questions (chips; click handled in message-text onClick)
        formatted = formatted.replace(/<div class="follow-up-questions">([\s\S]*?)<\/div>/g, (match, questions) => {
            const parts = splitFollowUpQuestionsBlock(questions);
            const questionList = parts
                .map((q) => `<button type="button" class="follow-up-btn">${escapeHtmlTextContent(q)}</button>`)
                .join('');
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
        // Dense answers often chain "**Point:** … **Next point:**" on one line — add vertical space between labels
        formatted = formatted.replace(
            /(<strong class="chat-bold">[^<]{1,120}:<\/strong>)(\s{0,3})(<strong class="chat-bold">)/g,
            '$1<br class="chat-bold-cluster-gap" /><br class="chat-bold-cluster-gap" />$3'
        );

        // console.log('🔍 After markdown, before terms:', formatted.substring(0, 300));
        
        // 7. PROCESS TERMS — glossary alone is enough (do not require message.terms; history often omits it)
        const glossary = normalizeGlossaryObject(message.glossary);
        if (Object.keys(glossary).length > 0) {
            // First try to find existing <term> tags
            const termRegex = /<term\s+id=["']([^"']+)["']\s*>([^<]+)<\/term>/gi;
            let termCount = 0;
            formatted = formatted.replace(termRegex, (match, termId, termText) => {
                const resolved = getGlossaryDefinition(glossary, termId);
                if (resolved && resolved.definition != null && String(resolved.definition).trim() !== '') {
                    termCount++;
                    const defEsc = String(resolved.definition).replace(/"/g, '&quot;');
                    const dataKey = resolved.key.replace(/"/g, '&quot;');
                    return `<span class="tooltip-wrapper" data-term="${dataKey}" data-definition="${defEsc}" style="color: #e91e63; font-weight: bold; cursor: pointer; border-bottom: 1px dotted #e91e63;"><span class="term-tooltip">${termText}</span></span>`;
                }
                return termText;
            });

            // Auto-wrap plain-text mentions when the model did not emit <term> tags (longer phrases first)
            if (termCount === 0) {
                const sortedKeys = Object.keys(glossary).sort((a, b) => b.length - a.length);
                sortedKeys.forEach((termKey) => {
                    const defRaw = glossary[termKey];
                    if (defRaw == null || String(defRaw).trim() === '') return;
                    const definition = String(defRaw).replace(/"/g, '&quot;');
                    const dataKey = termKey.replace(/"/g, '&quot;');
                    const escaped = termKey.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    const termPattern = new RegExp(`\\b(${escaped})\\b`, 'gi');
                    formatted = formatted.replace(termPattern, (match) => {
                        termCount++;
                        return `<span class="tooltip-wrapper" data-term="${dataKey}" data-definition="${definition}" style="color: #e91e63; font-weight: bold; cursor: pointer; border-bottom: 1px dotted #e91e63;"><span class="term-tooltip">${match}</span></span>`;
                    });
                });
            }
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

        // 9b. Turn blank lines / single newlines into visible spacing (HTML collapses raw \n)
        formatted = applyChatProseParagraphs(formatted.trim());

        // 10. Wrap into a single response container to avoid many "cards"
        formatted = `<div class="chat-response">${formatted}</div>`;
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

    const showMessageToolbar =
        !message.isTyping &&
        !message.isProcessing &&
        message.messageId &&
        message.content &&
        message.content.trim().length > 0;

    const handleCopyClick = async () => {
        try {
            const cleanText = cleanTextForCopy(message.content);
            await navigator.clipboard.writeText(cleanText);
            showToast('Message copied!', 'success');
        } catch (err) {
            showToast('Copy failed', 'error');
        }
    };

    const renderMessageToolbar = (placement) => {
        if (!showMessageToolbar) return null;
        if (isNativeGate && placement === 'top') return null;
        const isAssistant = message.role === 'assistant';
        const placementClass = placement === 'top' ? 'message-action-buttons--top' : 'message-action-buttons--bottom';
        return (
            <div
                className={`message-action-buttons ${placementClass}`}
                role="toolbar"
                aria-label="Message actions"
            >
                {message.showRestartButton && message.messageId && (
                    <button
                        type="button"
                        className="action-btn action-btn--restart"
                        onClick={() => onRestartPolling && onRestartPolling(message.messageId)}
                        title="Check for response"
                    >
                        <IconRefreshOutline />
                    </button>
                )}
                {isAssistant && (
                    <button
                        type="button"
                        className="action-btn action-btn--podcast"
                        disabled={podcastLoading}
                        onClick={handlePodcastButtonClick}
                        title="Listen as podcast"
                    >
                        <IconRadioOutline />
                    </button>
                )}
                <button type="button" className="action-btn action-btn--toolbar" onClick={handleCopyClick} title="Copy message">
                    <IconCopyOutline />
                </button>
                <button type="button" className="action-btn action-btn--toolbar" onClick={handleShareMessage} title="Share">
                    <IconShareSocialOutline />
                </button>
                {isAssistant && (
                    <button
                        type="button"
                        className="action-btn action-btn--pdf"
                        disabled={pdfGenerating}
                        onClick={handleMessagePdf}
                        title="Download as PDF"
                    >
                        <IconDocumentOutline />
                    </button>
                )}
                <button type="button" className="action-btn action-btn--delete" onClick={handleDeleteMessage} title="Delete message">
                    <IconTrashOutline />
                </button>
            </div>
        );
    };

    return (
        <div 
            ref={messageRef}
            className={`message-bubble ${message.role} ${message.isTyping ? 'typing' : ''} ${message.isProcessing ? 'processing' : ''} ${message.message_type === 'clarification' ? 'clarification' : ''} ${isNativeGate ? 'native-gate' : ''}`}
            onTouchStart={isMobile() ? handleLongPress : undefined}
            onClick={(e) => {
                if (isMobile() && showActions) {
                    setShowActions(false);
                }
            }}
        >
            <div className="message-content">
                {/* Mobile share/delete overlay (positioned inside card so layout does not shift) */}
                {showActions && !message.isTyping && !message.isProcessing && isMobile() && (
                    <div className="message-bubble-mobile-actions" role="toolbar" aria-label="Message quick actions">
                        <button
                            type="button"
                            className="action-btn action-btn--toolbar"
                            onClick={handleShareMessage}
                            title="Share"
                        >
                            <IconShareSocialOutline />
                        </button>
                        {message.messageId && (
                            <button
                                type="button"
                                className="action-btn action-btn--delete"
                                onClick={handleDeleteMessage}
                                title="Delete message"
                            >
                                <IconTrashOutline />
                            </button>
                        )}
                    </div>
                )}
                {/* Beta Notice for Timeline Predictions */}
                {message.role === 'assistant' && !message.isTyping && !message.isProcessing && message.message_type !== 'clarification' && !isNativeGate && (
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
                        ⚠️ BETA: Timeline predictions are experimental. Use logic and discretion.
                    </div>
                )}
                {message.role === 'assistant' && !message.isTyping && !message.isProcessing && message.message_type !== 'clarification' && !isNativeGate && (
                    <div style={{
                        backgroundColor: 'rgba(156, 39, 176, 0.08)',
                        borderLeft: '3px solid #9C27B0',
                        borderRadius: '8px',
                        padding: '12px',
                        marginBottom: '12px',
                        fontSize: '11px',
                        color: '#6A1B9A',
                        fontWeight: '600',
                        lineHeight: '16px'
                    }}>
                        ⚖️ DISCLAIMER: Astrology is a probabilistic tool for guidance. Not a substitute for medical, legal, financial, or mental health advice. Consult qualified professionals for important decisions.
                    </div>
                )}
                {renderMessageToolbar('top')}
                <div 
                    className="message-text enhanced-formatting"
                    onClick={(e) => {
                        const followBtn = e.target.closest('.follow-up-btn');
                        if (followBtn && onFollowUpClick) {
                            e.preventDefault();
                            e.stopPropagation();
                            const text = (followBtn.textContent || '').trim();
                            if (text) onFollowUpClick(text);
                            return;
                        }
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

                {isNativeGate && !message.isTyping && !message.isProcessing && (onNativeGateOpenSelectNative || onNativeGateOpenAddProfile) && (
                    <div
                        className="native-gate-ctas"
                        style={{
                            display: 'flex',
                            flexDirection: 'row',
                            flexWrap: 'wrap',
                            alignItems: 'center',
                            gap: '10px 14px',
                            marginTop: 10,
                            marginBottom: 2,
                        }}
                    >
                        {onNativeGateOpenSelectNative && (
                            <button
                                type="button"
                                onClick={() => onNativeGateOpenSelectNative()}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    padding: '4px 0',
                                    cursor: 'pointer',
                                    color: '#ea580c',
                                    fontWeight: 700,
                                    fontSize: 14,
                                    textDecoration: 'underline',
                                }}
                            >
                                Select native
                            </button>
                        )}
                        {onNativeGateOpenAddProfile && (
                            <button
                                type="button"
                                onClick={() => {
                                    const hint = message.gate_metadata?.extracted_birth_hint || {};
                                    onNativeGateOpenAddProfile(hint);
                                }}
                                style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: 6,
                                    padding: '8px 14px',
                                    borderRadius: 999,
                                    border: 'none',
                                    cursor: 'pointer',
                                    background: 'linear-gradient(90deg, #ff6b35, #f97316)',
                                    color: '#fff',
                                    fontWeight: 600,
                                    fontSize: 14,
                                    lineHeight: 1.2,
                                    boxShadow: '0 1px 4px rgba(234, 88, 12, 0.35)',
                                }}
                            >
                                <span aria-hidden style={{ fontSize: 15, fontWeight: 700 }}>
                                    +
                                </span>
                                Add new birth profile
                            </button>
                        )}
                    </div>
                )}

                {renderMessageToolbar('bottom')}
                {message.showRestartButton && !showMessageToolbar && (
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