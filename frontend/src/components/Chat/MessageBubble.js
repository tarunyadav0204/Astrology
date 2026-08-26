import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { jsPDF } from 'jspdf';
import { showToast } from '../../utils/toast';
import textToSpeech from '../../utils/textToSpeech';
import { useCredits } from '../../context/CreditContext';
import { splitFreeAnswerContent } from '../../utils/freeAnswerSplit';
import NorthIndianChart from '../Charts/NorthIndianChart';
import ZoomableImageLightbox, { resolveSummaryImageSrc } from './ZoomableImageLightbox';
import './ZoomableImageLightbox.css';
import {
    stopAndRevokePodcastPlayback,
    registerPodcastPlayback,
    base64ToAudioBlob,
    readStoredPodcastListenLang,
    storePodcastListenLang,
} from './podcastPlayback';
import PodcastLanguageModal from './PodcastLanguageModal';
import { buildInstantTypingLines, INSTANT_LOADER_TAKING_LONGER } from '../../constants/instantChatLoader';
import { buildReadableEvidence, buildRoutingSummary } from '../../utils/instantEvidence';

const premiumPodcastReadyKeys = new Set();
const PODCAST_READY_TOAST = 'Podcast ready — tap to listen';

const WHY_TARA_SAYS_THIS = {
    english: 'Why Tara says this',
    hindi: 'तारा ऐसा क्यों कहती हैं',
    es: 'Por qué Tara dice esto',
    fr: 'Pourquoi Tara dit cela',
    german: 'Warum Tara das sagt',
    russian: 'Почему Тара так говорит',
    chinese: '塔拉为什么这样说',
    tamil: 'தாரா ஏன் இப்படிச் சொல்கிறார்',
    telugu: 'తార ఇలా ఎందుకు చెబుతోంది',
    gujarati: 'તારા આવું કેમ કહે છે',
    marathi: 'तारा असे का म्हणते',
};

const CHAT_LANGUAGE_ALIASES = {
    en: 'english', hi: 'hindi', de: 'german', ru: 'russian', zh: 'chinese',
    ta: 'tamil', te: 'telugu', gu: 'gujarati', mr: 'marathi',
};

const whyTaraSaysThis = (language) => WHY_TARA_SAYS_THIS[
    CHAT_LANGUAGE_ALIASES[String(language || '').toLowerCase()] || String(language || 'english').toLowerCase()
]
    || WHY_TARA_SAYS_THIS.english;

const resolveReadyPodcastLang = (messageId, preferredLang) => {
    const mid = messageId != null ? String(messageId) : '';
    if (!mid) return null;
    const preferred = String(preferredLang || '').toLowerCase().startsWith('hi') ? 'hi' : 'en';
    const alternate = preferred === 'hi' ? 'en' : 'hi';
    if (premiumPodcastReadyKeys.has(`${mid}:${preferred}`)) return preferred;
    if (premiumPodcastReadyKeys.has(`${mid}:${alternate}`)) return alternate;
    return null;
};

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
const IconRadioFilled = (p) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={IC.w} height={IC.h} viewBox={IC.vb} {...IC.s({ ...p, strokeWidth: 2.25 })}>
        <circle cx="12" cy="12" r="2.25" fill="currentColor" stroke="none" />
        <path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14" />
    </svg>
);
const IconVolumeOutline = (p) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={IC.w} height={IC.h} viewBox={IC.vb} {...IC.s(p)}>
        <path d="M11 5 6 9H2v6h4l5 4Z" />
        <path d="M15.5 8.5a5 5 0 0 1 0 7" />
        <path d="M18.5 5.5a9 9 0 0 1 0 13" />
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
    // If the model already emitted buttons, pull their text.
    if (/<button\b/i.test(raw)) {
        const fromButtons = [];
        const buttonRe = /<button\b[^>]*>([\s\S]*?)<\/button>/gi;
        let bm;
        while ((bm = buttonRe.exec(raw)) !== null) {
            const label = String(bm[1] || '')
                .replace(/<[^>]+>/g, ' ')
                .replace(/\s+/g, ' ')
                .replace(/^-\s*/, '')
                .trim();
            if (label) fromButtons.push(label);
        }
        if (fromButtons.length) return fromButtons;
    }
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

/** Match follow-up wrappers even when the model escapes quotes. */
const FOLLOW_UP_BLOCK_RE =
    /<div\s+class\s*=\s*(?:["']|&quot;|\\["'])follow-up-questions(?:["']|&quot;|\\["'])\s*>([\s\S]*?)<\/div>/gi;

const extractFollowUpQuestionsFromContent = (content) => {
    const text = String(content || '');
    if (!text) return [];
    const questions = [];
    const re = new RegExp(FOLLOW_UP_BLOCK_RE.source, 'gi');
    let match;
    while ((match = re.exec(text)) !== null) {
        questions.push(...splitFollowUpQuestionsBlock(match[1]));
    }
    return questions;
};

const stripFollowUpQuestionsBlocks = (content) =>
    String(content || '').replace(new RegExp(FOLLOW_UP_BLOCK_RE.source, 'gi'), '').trim();

/** Hide model/internal markers that otherwise leak as [POS_START] / {json} in bubbles. */
const sanitizeVisibleChatContent = (content, { asHtmlSpans = false } = {}) => {
    let out = String(content || '');
    out = out.replace(
        /\n?\s*(?:NEXT_ACTION_META|FAQ_META|PREDICTION_ANCHOR_META)\s*:\s*\{[\s\S]*?\}\s*/gi,
        '\n',
    );
    const held = [];
    const hold = (kind, inner) => {
        const token = `\u0000SENT${held.length}\u0000`;
        held.push({ kind, inner: String(inner).replace(/\n+/g, ' ').trim() });
        return token;
    };
    out = out.replace(/(?:【|\[)POS_START(?:】|\])([\s\S]*?)(?:【|\[)POS_END(?:】|\])/gi, (_, inner) => hold('pos', inner));
    out = out.replace(/(?:【|\[)NEG_START(?:】|\])([\s\S]*?)(?:【|\[)NEG_END(?:】|\])/gi, (_, inner) => hold('neg', inner));
    out = out.replace(/(?:【|\[)(?:POS|NEG)_(?:START|END)(?:】|\])/gi, '');
    held.forEach((item, i) => {
        const token = `\u0000SENT${i}\u0000`;
        const replacement = asHtmlSpans
            ? `<span class="chat-sentiment-${item.kind === 'pos' ? 'positive' : 'negative'}">${item.inner}</span>`
            : `${item.kind === 'pos' ? '【POS_START】' : '【NEG_START】'}${item.inner}${item.kind === 'pos' ? '【POS_END】' : '【NEG_END】'}`;
        out = out.split(token).join(replacement);
    });
    return out;
};

const followUpChipLayoutStyle = {
    display: 'block',
    width: '100%',
    maxWidth: '100%',
    minWidth: 0,
    boxSizing: 'border-box',
    whiteSpace: 'normal',
    overflowWrap: 'anywhere',
    wordBreak: 'break-word',
    textAlign: 'left',
    appearance: 'none',
    WebkitAppearance: 'none',
};

const writeTextToClipboard = async (text) => {
    const value = String(text || '');

    if (navigator.clipboard?.writeText) {
        try {
            await navigator.clipboard.writeText(value);
            return;
        } catch (error) {
            // Installed PWAs and some mobile browsers can expose the API but
            // reject it because of clipboard permissions. Fall back below.
            console.warn('[MessageBubble] Clipboard API unavailable, using fallback', error);
        }
    }

    const textarea = document.createElement('textarea');
    textarea.value = value;
    textarea.setAttribute('readonly', '');
    textarea.setAttribute('aria-hidden', 'true');
    Object.assign(textarea.style, {
        position: 'fixed',
        top: '0',
        left: '-9999px',
        opacity: '0',
        pointerEvents: 'none',
    });

    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);
    try {
        if (!document.execCommand('copy')) {
            throw new Error('Browser rejected the clipboard copy command');
        }
    } finally {
        textarea.remove();
    }
};

const convertMarkdownTablesToStackedBlocks = (text) => {
    const lines = String(text || '').split('\n');
    const out = [];
    let i = 0;
    const isTableRow = (line) => /^\s*\|.*\|\s*$/.test(line || '');
    const isSeparator = (line) => /^\s*\|[\s:|-]+\|\s*$/.test(line || '');
    const cells = (line) => String(line || '').split('|').map((c) => c.trim()).filter(Boolean);

    while (i < lines.length) {
        if (isTableRow(lines[i]) && isSeparator(lines[i + 1])) {
            const headers = cells(lines[i]);
            i += 2;
            const rows = [];
            while (i < lines.length && isTableRow(lines[i])) {
                rows.push(cells(lines[i]));
                i += 1;
            }
            if (headers.length && rows.length) {
                rows.forEach((row, rowIndex) => {
                    out.push(`#### ${row[0] || `Row ${rowIndex + 1}`}`);
                    headers.slice(1).forEach((header, idx) => {
                        const value = row[idx + 1];
                        if (value) out.push(`- **${header}**: ${value}`);
                    });
                    out.push('');
                });
                continue;
            }
        }
        out.push(lines[i]);
        i += 1;
    }
    return out.join('\n').replace(/\n{3,}/g, '\n\n');
};

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

const remedyScreenImpressionClaims = new Set();

const localCalendarDay = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
};

const recordRemedyScreenImpressionOnce = async ({ sessionId, message }) => {
    const sessionScope = String(
        sessionId
        || message?.session_id
        || message?.sessionId
        || 'current'
    );
    const impressionId = `chat_screen:${sessionScope}:${localCalendarDay()}`;
    if (remedyScreenImpressionClaims.has(impressionId)) return;
    remedyScreenImpressionClaims.add(impressionId);

    const storageKey = `remedy_funnel_card_shown:${impressionId}`;
    try {
        if (localStorage.getItem(storageKey)) return;
        // Claim before networking so React remounts and page reloads cannot fan out.
        localStorage.setItem(storageKey, '1');
    } catch (_) {
        // The in-memory claim still protects this page lifecycle.
    }

    const token = localStorage.getItem('token');
    if (!token) return;
    await fetch('/api/credits/remedy-funnel/event', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
            event: 'card_shown',
            message_id: impressionId,
            platform: 'web',
        }),
    });
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
    onContinueSingleChartGate,
    onRelationshipContextGate,
    onStartPartnershipGate,
    podcastAutoLaunchMessageId = null,
    podcastAutoLaunchKey = 0,
    podcastAutoLaunchLang = 'en',
    onPodcastAutoLaunchConsumed,
    instantLoaderRevealWords = 1,
    onOpenCreditsModal = null,
    forceInstantPresentation = false,
}) => {
    const { podcastCost, refreshBalance, credits, chatCost } = useCredits();
    const standardChatCost = Math.max(1, Number(chatCost) || 1);
    const [detailUnlocked, setDetailUnlocked] = useState(false);
    const blurShownTrackedRef = useRef(false);
    const [showActions, setShowActions] = useState(false);
    const [showInstantEvidence, setShowInstantEvidence] = useState(false);
    const [isReadingAloud, setIsReadingAloud] = useState(false);
    const readingAloudRef = useRef(false);
    const [tooltipModal, setTooltipModal] = useState({ show: false, term: '', definition: '' });
    const messageRef = useRef(null);

    const insightsKey = message?.processingClientId ?? message?.messageId ?? null;
    const chartInsights = Array.isArray(message?.chartInsights) ? message.chartInsights : [];
    const [insightIndex, setInsightIndex] = useState(0);
    const followUpQuestions = useMemo(() => {
        const fromContent = extractFollowUpQuestionsFromContent(message?.content);
        if (fromContent.length) return fromContent;
        if (Array.isArray(message?.follow_up_questions)) {
            return message.follow_up_questions
                .map((item) => String(item || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim())
                .filter(Boolean);
        }
        return [];
    }, [message?.content, message?.follow_up_questions]);
    const messageChatTier = String(message?.chatTier || message?.chat_tier || '').trim().toLowerCase();
    const isPremiumChatMessage = messageChatTier === 'premium' || message?.premium_analysis === true;
    const instantPresentation = forceInstantPresentation || messageChatTier === 'instant';
    const instantEvidence = message?.instant_evidence_debug
        || message?.gate_metadata?.instant_evidence_debug
        || null;
    const nextAction = message?.next_action || message?.nextAction || null;
    const nextActionType = String(nextAction?.type || '').trim().toLowerCase();
    const hasNextAction = Boolean(nextAction && nextActionType && nextActionType !== 'none');
    const isRemedyNextAction = nextActionType === 'remedy';
    const isTimelineSelection = nextActionType === 'timeline_selection';
    const timelineOptions = isTimelineSelection && Array.isArray(nextAction?.options)
        ? nextAction.options.filter((option) => option && option.id && option.label)
        : [];
    const [selectedTimelineOption, setSelectedTimelineOption] = useState(null);
    const nextActionTitle = String(nextAction?.title || '').trim();
    const nextActionReason = String(nextAction?.reason || '').trim();
    const nextActionFollowUps = Array.isArray(nextAction?.follow_up_questions)
        ? nextAction.follow_up_questions.map((item) => String(item || '').trim()).filter(Boolean)
        : [];
    const remedyCardButton = nextActionFollowUps[0] || '';
    const hasRemedyCardCopy = Boolean(
        isRemedyNextAction && nextActionTitle && nextActionReason && remedyCardButton
    );
    const showNextActionCard = hasNextAction && (isRemedyNextAction ? hasRemedyCardCopy : true);
    const remedyClickPrompt = isRemedyNextAction
        ? [
              'Generate a remedy-only reading.',
              nextActionTitle ? `Issue: ${nextActionTitle}` : null,
              nextActionReason ? `Why this matters: ${nextActionReason}` : null,
              nextActionFollowUps.length > 0 ? `Possible remedy layers: ${nextActionFollowUps.join(' | ')}` : null,
              'Do not give a general chart reading. Give practical remedies only.',
          ].filter(Boolean).join('\n')
        : '';

    useEffect(() => {
        setSelectedTimelineOption(null);
    }, [message?.messageId, message?.id, nextAction?.selection_stage]);

    const renderTimelineSelectionCard = () => {
        if (
            message.role !== 'assistant'
            || message.isTyping
            || message.isProcessing
            || !isTimelineSelection
            || timelineOptions.length === 0
        ) return null;

        return (
            <div className="marriage-timeline-card" aria-label={nextActionTitle || 'Marriage period selection'}>
                <div className="marriage-timeline-card__eyebrow">
                    Marriage date finder · {String(nextAction?.selection_stage || 'period')}
                </div>
                <div className="marriage-timeline-card__title">
                    {nextActionTitle || 'Choose the closest period'}
                </div>
                {nextActionReason && (
                    <div className="marriage-timeline-card__reason">{nextActionReason}</div>
                )}
                <div className="marriage-timeline-card__options">
                    {timelineOptions.map((option, index) => {
                        const optionId = String(option.id);
                        const isSelected = selectedTimelineOption === optionId;
                        const isDisabled = Boolean(selectedTimelineOption);
                        return (
                            <button
                                key={optionId}
                                type="button"
                                className={`marriage-timeline-option${isSelected ? ' marriage-timeline-option--selected' : ''}`}
                                disabled={isDisabled}
                                onClick={() => {
                                    if (selectedTimelineOption || !onFollowUpClick) return;
                                    setSelectedTimelineOption(optionId);
                                    const sourceMessageId = message.messageId || message.id;
                                    onFollowUpClick(
                                        String(option.submit_text || option.label).trim(),
                                        {
                                            directSend: true,
                                            instant_chat: true,
                                            chat_tier: 'instant',
                                            instant_timeline_selection: true,
                                            query_context: {
                                                ...(option.query_context || {}),
                                                source_message_id: sourceMessageId ? String(sourceMessageId) : undefined,
                                                marriage_timeline_source_message_id: sourceMessageId ? String(sourceMessageId) : undefined,
                                            },
                                        }
                                    );
                                }}
                            >
                                <span className="marriage-timeline-option__rank">
                                    {option.rank ? `#${option.rank}` : index + 1}
                                </span>
                                <span className="marriage-timeline-option__copy">
                                    <strong>{option.primary_label || option.label}</strong>
                                    {(option.technical_label || option.evidence_hint || option.detail) && (
                                        <small>
                                            {option.technical_label ? `Astrology: ${option.technical_label}` : ''}
                                            {option.technical_label && option.evidence_hint ? ' · ' : ''}
                                            {option.evidence_hint || (!option.technical_label ? option.detail : '')}
                                        </small>
                                    )}
                                </span>
                                <span className="marriage-timeline-option__control" aria-hidden="true">
                                    {isSelected ? '✓' : '›'}
                                </span>
                            </button>
                        );
                    })}
                </div>
                <div className="marriage-timeline-card__trust-note">
                    Your choice narrows the calculation; it is not treated as a date predicted independently.
                </div>
            </div>
        );
    };
    const isInstantTypingBubble =
        (message.isTyping || message.isProcessing) && messageChatTier === 'instant';
    const instantTypingState = useMemo(
        () => (isInstantTypingBubble ? buildInstantTypingLines(Math.max(1, instantLoaderRevealWords)) : null),
        [isInstantTypingBubble, instantLoaderRevealWords]
    );

    useEffect(() => {
        if (!insightsKey) return;
        if (!chartInsights.length) return;

        console.log('[MessageBubble] chart insights init', {
            insightsKey,
            messageId: message?.messageId,
            processingClientId: message?.processingClientId,
            chartInsightsCount: chartInsights.length,
            houses: chartInsights.map((item) => item?.house_number ?? item?.house ?? item?.houseNumber),
        });

        setInsightIndex(0);
        const interval = setInterval(() => {
            setInsightIndex((prev) => {
                const next = (prev + 1) % chartInsights.length;
                console.log('[MessageBubble] chart insight rotate', {
                    insightsKey,
                    prev,
                    next,
                    chartInsightsCount: chartInsights.length,
                    currentHouse: chartInsights[next]?.house_number ?? chartInsights[next]?.house ?? chartInsights[next]?.houseNumber,
                });
                return next;
            });
        }, 2500);

        return () => clearInterval(interval);
    }, [insightsKey, chartInsights.length]);

    useEffect(() => {
        if (!chartInsights.length) return;
        console.log('[MessageBubble] render state', {
            insightsKey,
            insightIndex,
            chartInsightsCount: chartInsights.length,
            currentHouse: chartInsights[insightIndex]?.house_number ?? chartInsights[insightIndex]?.house ?? chartInsights[insightIndex]?.houseNumber,
            messageId: message?.messageId,
            processingClientId: message?.processingClientId,
            isProcessing: message?.isProcessing,
        });
    }, [insightsKey, insightIndex, chartInsights, message?.messageId, message?.processingClientId, message?.isProcessing]);

    const [podcastModalOpen, setPodcastModalOpen] = useState(false);
    const [podcastModalMode, setPodcastModalMode] = useState('loading');
    const [podcastLoading, setPodcastLoading] = useState(false);
    const [podcastReady, setPodcastReady] = useState(() => {
        const mid = message?.messageId != null ? String(message.messageId) : '';
        if (!mid) return false;
        return premiumPodcastReadyKeys.has(`${mid}:en`) || premiumPodcastReadyKeys.has(`${mid}:hi`);
    });
    const [showPodcastLanguageModal, setShowPodcastLanguageModal] = useState(false);
    const [podcastListenLang, setPodcastListenLang] = useState(() => readStoredPodcastListenLang(language));
    const podcastListenLangRef = useRef(podcastListenLang);
    const skipPodcastCreditsRef = useRef(false);
    const podcastCacheCheckRef = useRef(false);
    const [pdfGenerating, setPdfGenerating] = useState(false);
    const [podcastCurrentTime, setPodcastCurrentTime] = useState(0);
    const [podcastDuration, setPodcastDuration] = useState(0);
    const [podcastIsPlaying, setPodcastIsPlaying] = useState(false);
    const [podcastPlaybackRate, setPodcastPlaybackRate] = useState(1);
    const [summaryLightboxSrc, setSummaryLightboxSrc] = useState(null);
    const podcastAudioRef = useRef(null);
    const podcastFetchAbortRef = useRef(null);
    const podcastBlobRef = useRef(null);
    const podcastSourceKeyRef = useRef(null);

    const gateMetadata = message.gate_metadata || {};
    const gateIntent = message.intent_gate || gateMetadata.intent_gate || '';
    const isRelationshipSetupGate = gateIntent === 'relationship_setup';
    const isPartnershipOfferGate = gateIntent === 'partnership_offer';
    const isSubjectChartGate =
        gateIntent === 'create_subject_chart' ||
        gateIntent === 'complete_subject_birth_details' ||
        gateIntent === 'create_native';
    const relationshipGateOptions = Array.isArray(gateMetadata.relationship_setup?.options)
        ? gateMetadata.relationship_setup.options
        : [];
    const showRelationshipOptions = isRelationshipSetupGate || (isPartnershipOfferGate && relationshipGateOptions.length > 0);
    const isNativeGate = useMemo(
        () =>
            message.message_type === 'native_gate' ||
            message.intent_gate === 'create_native' ||
            (message.gate_metadata && message.gate_metadata.intent_gate === 'create_native') ||
            [
                'create_subject_chart',
                'complete_subject_birth_details',
                'relationship_setup',
                'partnership_offer',
            ].includes(gateIntent),
        [message.message_type, message.intent_gate, message.gate_metadata, gateIntent],
    );

    const isFreeQuestionAnswer =
        message.role === 'assistant' &&
        !message.isTyping &&
        !message.isProcessing &&
        message.message_type !== 'clarification' &&
        !isNativeGate &&
        Boolean(gateMetadata.free_question_completed);
    const freeSplit = useMemo(
        () => (isFreeQuestionAnswer ? splitFreeAnswerContent(message.content) : null),
        [isFreeQuestionAnswer, message.content],
    );
    const canBlurFreeDetail = Boolean(freeSplit?.canBlur);
    const shouldBlurDetail = canBlurFreeDetail && !detailUnlocked;

    useEffect(() => {
        const mid = message.messageId || message.id;
        if (!canBlurFreeDetail || !mid) return;
        try {
            if (localStorage.getItem(`free_detail_unlocked:${mid}`) === '1') {
                setDetailUnlocked(true);
            }
        } catch (_) {
            /* ignore */
        }
    }, [canBlurFreeDetail, message.messageId, message.id]);

    useEffect(() => {
        if (!canBlurFreeDetail || detailUnlocked || blurShownTrackedRef.current) return;
        const mid = message.messageId || message.id;
        if (!mid) return;
        blurShownTrackedRef.current = true;
        try {
            const token = localStorage.getItem('token');
            if (!token) return;
            fetch('/api/credits/free-answer-funnel/event', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    event: 'blur_shown',
                    message_id: String(mid),
                    platform: 'web',
                }),
            }).catch(() => {});
        } catch (_) {
            /* ignore */
        }
    }, [canBlurFreeDetail, detailUnlocked, message.messageId, message.id]);

    useEffect(() => {
        if (!canBlurFreeDetail || detailUnlocked || Number(credits) <= 0) return;
        const mid = message.messageId || message.id;
        if (!mid) return;
        try {
            if (localStorage.getItem(`free_detail_reveal_clicked:${mid}`) !== '1') return;
            localStorage.setItem(`free_detail_unlocked:${mid}`, '1');
            setDetailUnlocked(true);
        } catch (_) {
            /* ignore */
        }
    }, [canBlurFreeDetail, detailUnlocked, credits, message.messageId, message.id]);

    useEffect(() => {
        if (messageChatTier === 'instant' || !showNextActionCard || !isRemedyNextAction) return;
        recordRemedyScreenImpressionOnce({ sessionId, message }).catch(() => {});
    }, [messageChatTier, showNextActionCard, isRemedyNextAction, sessionId, message]);

    const handleRevealDetailedAnswer = useCallback(() => {
        const mid = message.messageId || message.id;
        if (mid) {
            try {
                localStorage.setItem(`free_detail_reveal_clicked:${mid}`, '1');
            } catch (_) {
                /* ignore */
            }
            try {
                const token = localStorage.getItem('token');
                if (token) {
                    fetch('/api/credits/free-answer-funnel/event', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${token}`,
                        },
                        body: JSON.stringify({
                            event: 'reveal_clicked',
                            message_id: String(mid),
                            platform: 'web',
                        }),
                    }).catch(() => {});
                }
            } catch (_) {
                /* ignore */
            }
        }
        if (Number(credits) >= standardChatCost) {
            if (mid) {
                try {
                    localStorage.setItem(`free_detail_unlocked:${mid}`, '1');
                } catch (_) {
                    /* ignore */
                }
            }
            setDetailUnlocked(true);
            return;
        }
        if (typeof onOpenCreditsModal === 'function') {
            onOpenCreditsModal();
        }
    }, [message.messageId, message.id, credits, standardChatCost, onOpenCreditsModal]);

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

    const markPremiumPodcastReady = useCallback((key) => {
        if (!key) return;
        premiumPodcastReadyKeys.add(key);
        setPodcastReady(true);
    }, []);

    useEffect(() => {
        if (!isPremiumChatMessage || instantPresentation) return;
        if (message.role !== 'assistant' || message.isTyping || message.isProcessing) return;
        if (message.message_type === 'clarification' || isNativeGate) return;
        const mid = message.messageId != null ? String(message.messageId) : '';
        if (!mid) return;
        if (premiumPodcastReadyKeys.has(`${mid}:en`) || premiumPodcastReadyKeys.has(`${mid}:hi`)) {
            setPodcastReady(true);
            return;
        }
        const token = localStorage.getItem('token');
        if (!token) return;
        let active = true;
        void (async () => {
            try {
                const [enResponse, hiResponse] = await Promise.all([
                    fetch(
                        `/api/tts/podcast/check-cache?message_id=${encodeURIComponent(mid)}&lang=en`,
                        { headers: { Authorization: `Bearer ${token}` } },
                    ),
                    fetch(
                        `/api/tts/podcast/check-cache?message_id=${encodeURIComponent(mid)}&lang=hi`,
                        { headers: { Authorization: `Bearer ${token}` } },
                    ),
                ]);
                const enData = enResponse.ok ? await enResponse.json() : null;
                const hiData = hiResponse.ok ? await hiResponse.json() : null;
                if (!active) return;
                if (enData?.cached === true) {
                    markPremiumPodcastReady(`${mid}:en`);
                }
                if (hiData?.cached === true) {
                    markPremiumPodcastReady(`${mid}:hi`);
                }
            } catch (_) {
                /* ignore hydrate errors */
            }
        })();
        return () => {
            active = false;
        };
    }, [
        instantPresentation,
        isNativeGate,
        isPremiumChatMessage,
        markPremiumPodcastReady,
        message.isProcessing,
        message.isTyping,
        message.messageId,
        message.message_type,
        message.role,
    ]);

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

    const persistPodcastListenLang = useCallback((listenLang) => {
        const lang = storePodcastListenLang(listenLang);
        podcastListenLangRef.current = lang;
        setPodcastListenLang(lang);
        return lang;
    }, []);

    const fetchAndPlayPodcast = useCallback(async (listenLang) => {
        const token = localStorage.getItem('token');
        if (!token) {
            showToast('Please log in to listen to podcasts.', 'error');
            return;
        }
        const cleanText = getCleanMessageText();
        if (!cleanText) return;

        const langCode = persistPodcastListenLang(listenLang || podcastListenLangRef.current || language);
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
            if (mid) {
                markPremiumPodcastReady(`${mid}:${langCode}`);
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
        persistPodcastListenLang,
        refreshBalance,
        sessionId,
        markPremiumPodcastReady,
    ]);

    const continuePodcastAfterLanguage = useCallback(async (listenLang) => {
        const token = localStorage.getItem('token');
        if (!token) {
            showToast('Please log in to listen to podcasts.', 'error');
            return;
        }
        const langCode = persistPodcastListenLang(listenLang);
        const skipCredits = skipPodcastCreditsRef.current;
        skipPodcastCreditsRef.current = false;
        setShowPodcastLanguageModal(false);

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

        if (isPremiumChatMessage || skipCredits) {
            await fetchAndPlayPodcast(langCode);
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

        await fetchAndPlayPodcast(langCode);
    }, [
        fetchAndPlayPodcast,
        isPremiumChatMessage,
        message.messageId,
        persistPodcastListenLang,
        podcastCost,
        podcastLoading,
    ]);

    const handlePodcastButtonClick = useCallback(async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            showToast('Please log in to listen to podcasts.', 'error');
            return;
        }
        const cleanText = getCleanMessageText();
        if (!cleanText) return;
        if (podcastLoading) return;
        if (podcastCacheCheckRef.current) return;

        skipPodcastCreditsRef.current = false;

        const playCachedLang = async (lang) => {
            const mid = message.messageId != null ? String(message.messageId) : '';
            if (mid) markPremiumPodcastReady(`${mid}:${lang}`);
            await fetchAndPlayPodcast(lang);
        };

        const localCachedLang = resolveReadyPodcastLang(
            message.messageId,
            podcastListenLangRef.current,
        );
        if (localCachedLang) {
            await playCachedLang(localCachedLang);
            return;
        }

        const mid = message.messageId != null ? String(message.messageId) : '';
        if (mid) {
            podcastCacheCheckRef.current = true;
            try {
                const preferred = podcastListenLangRef.current === 'hi' ? 'hi' : 'en';
                const alternate = preferred === 'hi' ? 'en' : 'hi';
                const [prefResponse, altResponse] = await Promise.all([
                    fetch(
                        `/api/tts/podcast/check-cache?message_id=${encodeURIComponent(mid)}&lang=${encodeURIComponent(preferred)}`,
                        { headers: { Authorization: `Bearer ${token}` } },
                    ),
                    fetch(
                        `/api/tts/podcast/check-cache?message_id=${encodeURIComponent(mid)}&lang=${encodeURIComponent(alternate)}`,
                        { headers: { Authorization: `Bearer ${token}` } },
                    ),
                ]);
                const prefData = prefResponse.ok ? await prefResponse.json() : null;
                const altData = altResponse.ok ? await altResponse.json() : null;
                if (prefData?.cached === true) {
                    await playCachedLang(preferred);
                    return;
                }
                if (altData?.cached === true) {
                    await playCachedLang(alternate);
                    return;
                }
            } catch (_) {
                // Fall through to language picker if cache lookup fails.
            } finally {
                podcastCacheCheckRef.current = false;
            }
        }

        setShowPodcastLanguageModal(true);
    }, [fetchAndPlayPodcast, getCleanMessageText, markPremiumPodcastReady, message.messageId, podcastLoading]);

    const lastPodcastPromoKeyRef = useRef(0);
    useEffect(() => {
        if (!podcastAutoLaunchKey) {
            lastPodcastPromoKeyRef.current = 0;
            return undefined;
        }
        if (podcastAutoLaunchMessageId == null) return undefined;
        const mid = message.messageId != null ? String(message.messageId) : '';
        if (!mid || mid !== String(podcastAutoLaunchMessageId)) return undefined;
        if (message.role !== 'assistant') return undefined;
        if (message.isTyping || message.isProcessing) return undefined;
        if (message.message_type === 'clarification' || isNativeGate) return undefined;
        if (lastPodcastPromoKeyRef.current === podcastAutoLaunchKey) return undefined;
        const timer = setTimeout(() => {
            lastPodcastPromoKeyRef.current = podcastAutoLaunchKey;
            skipPodcastCreditsRef.current = true;
            onPodcastAutoLaunchConsumed?.();
            const lang = String(podcastAutoLaunchLang || '').toLowerCase().startsWith('hi') ? 'hi' : 'en';
            continuePodcastAfterLanguage(lang);
        }, 350);
        return () => clearTimeout(timer);
    }, [
        podcastAutoLaunchKey,
        podcastAutoLaunchMessageId,
        podcastAutoLaunchLang,
        onPodcastAutoLaunchConsumed,
        continuePodcastAfterLanguage,
        message.role,
        message.messageId,
        message.isTyping,
        message.isProcessing,
        message.message_type,
        isNativeGate,
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
        
        // 2. Summary image is rendered as a React thumbnail (click → fullscreen zoom).
        // Do not inject it into HTML here (would duplicate / block click handlers).
        
        // 3. Normalize line breaks
        formatted = formatted.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        formatted = convertMarkdownTablesToStackedBlocks(formatted);
        
        // 4. Strip Follow-up Questions from HTML — rendered as React chips (PWA-safe wrapping).
        formatted = stripFollowUpQuestionsBlocks(formatted);
        formatted = sanitizeVisibleChatContent(formatted, { asHtmlSpans: true });
        
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
        !message.instantStreaming &&
        message.messageId &&
        message.content &&
        message.content.trim().length > 0;

    const handleCopyClick = async () => {
        try {
            const cleanText = cleanTextForCopy(message.content);
            await writeTextToClipboard(cleanText);
            showToast('Message copied!', 'success');
        } catch (err) {
            console.error('[MessageBubble] Failed to copy message', err);
            showToast('Copy failed', 'error');
        }
    };

    const handleReadAloud = () => {
        if (readingAloudRef.current) {
            textToSpeech.stop();
            readingAloudRef.current = false;
            setIsReadingAloud(false);
            return;
        }

        const cleanText = cleanTextForCopy(message.content);
        if (!cleanText) return;

        textToSpeech.stop();
        const started = textToSpeech.speak(cleanText, {
            onStart: () => {
                readingAloudRef.current = true;
                setIsReadingAloud(true);
            },
            onEnd: () => {
                readingAloudRef.current = false;
                setIsReadingAloud(false);
            },
            onError: () => {
                readingAloudRef.current = false;
                setIsReadingAloud(false);
                showToast('Unable to read this answer aloud', 'error');
            },
        });

        if (!started) showToast('Read aloud is not supported in this browser', 'error');
    };

    useEffect(() => () => {
        if (readingAloudRef.current) textToSpeech.stop();
    }, []);

    if (instantPresentation) {
        // `loadingMessage` is deliberately retained on some locally-created rows so a
        // remount can restore the processing copy. Once the server answer completes,
        // however, it must never shadow `message.content` (read-aloud already reads
        // `message.content`, which previously made the answer audible but invisible).
        const isInstantPending = Boolean(message.isTyping || message.isProcessing);
        const content = String(
            isInstantPending
                ? (message.loadingMessage || message.content || '')
                : (message.content || ''),
        ).trim();
        const paragraphs = content
            .replace(/<[^>]+>/g, ' ')
            .replace(/^#{1,6}\s+/gm, '')
            .replace(/\*\*(.*?)\*\*/g, '$1')
            .replace(/__(.*?)__/g, '$1')
            .replace(/[`*_]+/g, '')
            .replace(/(?:【|\[)(?:POS|NEG)_(?:START|END)(?:】|\])/gi, '')
            .replace(/\n?\s*(?:NEXT_ACTION_META|FAQ_META|PREDICTION_ANCHOR_META)\s*:\s*\{[\s\S]*?\}\s*/gi, '\n')
            .split(/\n\s*\n/)
            .map((part) => part.replace(/\s*\n\s*/g, ' ').trim())
            .filter(Boolean);
        const time = message.timestamp
            ? new Date(message.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
            : '';

        return (
            <div className={`message-bubble message-bubble--instant${isTimelineSelection ? ' message-bubble--timeline' : ''} ${message.role} ${message.isTyping || message.isProcessing ? 'typing' : ''}`}>
                <div className="message-content message-content--instant">
                    <div className="instant-chat-copy">
                        {(message.isTyping || message.isProcessing) && instantTypingState ? (
                            <>
                                <span className="instant-chat-thinking">Tara is thinking</span>
                                <span className="instant-chat-dots" aria-label="Tara is typing"><i /><i /><i /></span>
                            </>
                        ) : (
                            paragraphs.map((paragraph, index) => <p key={`${index}-${paragraph.slice(0, 18)}`}>{paragraph}</p>)
                        )}
                        {message.instantStreaming ? <span className="instant-chat-dots" aria-label="Tara is typing"><i /><i /><i /></span> : null}
                    </div>
                    <div className="instant-chat-meta">
                        {message.role === 'assistant' && instantEvidence && !message.isTyping && !message.isProcessing && !message.instantStreaming ? (
                            <button
                                type="button"
                                className={`instant-evidence-toggle${showInstantEvidence ? ' is-open' : ''}`}
                                onClick={() => setShowInstantEvidence((open) => !open)}
                                aria-expanded={showInstantEvidence}
                            >
                                <span aria-hidden="true">◇</span>
                                {whyTaraSaysThis(language)}
                            </button>
                        ) : null}
                        {message.role === 'assistant' && !message.isTyping && !message.isProcessing && !message.instantStreaming && content ? (
                            <button
                                type="button"
                                className={`instant-chat-listen${isReadingAloud ? ' is-active' : ''}`}
                                onClick={handleReadAloud}
                                aria-label={isReadingAloud ? 'Stop reading' : 'Listen to this message'}
                            >
                                <IconVolumeOutline />
                                <span>{isReadingAloud ? 'Stop' : 'Listen'}</span>
                            </button>
                        ) : null}
                        {time ? <time>{time}</time> : null}
                    </div>
                    {showInstantEvidence && instantEvidence ? (
                        <section className="instant-evidence-inspector" aria-label="Instant answer evidence">
                            {(() => {
                                const routing = buildRoutingSummary(instantEvidence);
                                const sections = buildReadableEvidence(instantEvidence);
                                return (
                                    <>
                                        <header>
                                            <div>
                                                <small>HOW THIS ANSWER WAS DERIVED</small>
                                                <strong>{instantEvidence?.user_derivation?.event?.label || instantEvidence?.query_plan?.user_goal || routing.category}</strong>
                                            </div>
                                            <span className={instantEvidence?.verification?.passed ? 'is-pass' : 'is-review'}>
                                                {instantEvidence?.verification?.passed ? 'Evidence linked' : 'Review needed'}
                                            </span>
                                        </header>
                                        <div className="instant-routing-summary" aria-label="Answer routing debug">
                                            <span><small>Final mode</small><strong>{routing.finalMode}</strong></span>
                                            <span><small>Selected</small><strong>{routing.selectedMode}</strong></span>
                                            <span><small>Source</small><strong>{routing.source}</strong></span>
                                            <span><small>Confidence</small><strong>{routing.confidence}</strong></span>
                                            {routing.changed ? <em>Mode adjusted after routing</em> : null}
                                            {routing.degraded ? <em>Fallback used</em> : null}
                                        </div>
                                        <div className="instant-readable-evidence">
                                            {sections.map((section) => (
                                                <article key={section.key}>
                                                    <header>
                                                        {section.step ? <b>{section.step}</b> : null}
                                                        <h4>{section.title}</h4>
                                                    </header>
                                                    <ul>
                                                        {(Array.isArray(section.lines) ? section.lines : []).map((line, index) => (
                                                            <li key={`${section.key}-${index}`}>{line}</li>
                                                        ))}
                                                    </ul>
                                                    {(Array.isArray(section.groups) ? section.groups : []).map((group) => (
                                                        <section className="instant-evidence-group" key={`${section.key}-${group.key}`}>
                                                            <h5>{group.title}</h5>
                                                            {(Array.isArray(group.lines) ? group.lines : []).map((line, index) => <p key={`${group.key}-line-${index}`}>{line}</p>)}
                                                            {(Array.isArray(group.items) ? group.items : []).map((item, index) => (
                                                                <div className="instant-evidence-factor" key={`${group.key}-item-${index}`}>
                                                                    <strong>{item.title}</strong>
                                                                    <p>{item.text}</p>
                                                                </div>
                                                            ))}
                                                        </section>
                                                    ))}
                                                </article>
                                            ))}
                                        </div>
                                    </>
                                );
                            })()}
                        </section>
                    ) : null}
                </div>
                {renderTimelineSelectionCard()}
            </div>
        );
    }

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
                {isAssistant && messageChatTier === 'instant' && (
                    <button
                        type="button"
                        className={`action-btn action-btn--listen ${isReadingAloud ? 'action-btn--listen-active' : ''}`}
                        onClick={handleReadAloud}
                        title={isReadingAloud ? 'Stop reading' : 'Listen to this answer'}
                        aria-pressed={isReadingAloud}
                    >
                        <IconVolumeOutline />
                        <span>{isReadingAloud ? 'Stop' : 'Listen'}</span>
                    </button>
                )}
                {isAssistant && messageChatTier !== 'instant' && (
                    <button
                        type="button"
                        className={`action-btn action-btn--podcast${podcastReady ? ' action-btn--podcast-ready' : ''}${isPremiumChatMessage && !podcastReady && !podcastLoading ? ' action-btn--podcast-included' : ''}`}
                        disabled={podcastLoading}
                        onClick={handlePodcastButtonClick}
                        title={
                            podcastReady
                                ? PODCAST_READY_TOAST
                                : isPremiumChatMessage
                                    ? 'Free podcast included — tap to listen'
                                    : 'Listen as podcast'
                        }
                        aria-label={
                            podcastReady
                                ? PODCAST_READY_TOAST
                                : isPremiumChatMessage
                                    ? 'Free podcast included — tap to listen'
                                    : 'Listen as podcast'
                        }
                    >
                        {podcastLoading ? (
                            <span className="podcast-prep-spinner" aria-hidden="true" />
                        ) : podcastReady ? (
                            <>
                                <IconRadioFilled />
                                <span className="podcast-ready-label">Ready</span>
                            </>
                        ) : isPremiumChatMessage ? (
                            <>
                                <IconRadioOutline />
                                <span className="podcast-included-label">Free</span>
                            </>
                        ) : (
                            <IconRadioOutline />
                        )}
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
            className={`message-bubble ${message.role} ${message.isTyping ? 'typing' : ''} ${message.isProcessing ? 'processing' : ''} ${isInstantTypingBubble ? 'instant-typing' : ''} ${message.message_type === 'clarification' ? 'clarification' : ''} ${isNativeGate ? 'native-gate' : ''}`}
            onTouchStart={isMobile() ? handleLongPress : undefined}
            onClick={(e) => {
                if (isMobile() && showActions) {
                    setShowActions(false);
                }
            }}
        >
            <div className="message-content">
                {message.role === 'assistant' && message.native_name && !message.isTyping && !message.isProcessing && (
                    <div className="message-native-chip">{message.native_name}</div>
                )}
                {message.role === 'user' && message.native_name && !message.isTyping && !message.isProcessing && (
                    <div className="message-native-chip message-native-chip--user">{message.native_name}</div>
                )}
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
                {message.role === 'assistant' && !message.isTyping && !message.isProcessing && !message.instantStreaming && messageChatTier !== 'instant' && message.message_type !== 'clarification' && !isNativeGate && (
                    <div className="chat-message-notice chat-message-notice--beta">
                        ⚠️ BETA: Timeline predictions are experimental. Use logic and discretion.
                    </div>
                )}
                {message.role === 'assistant' && !message.isTyping && !message.isProcessing && !message.instantStreaming && messageChatTier !== 'instant' && message.message_type !== 'clarification' && !isNativeGate && (
                    <div className="chat-message-notice chat-message-notice--disclaimer">
                        ⚖️ DISCLAIMER: Astrology is a probabilistic tool for guidance. Not a substitute for medical, legal, financial, or mental health advice. Consult qualified professionals for important decisions.
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
                    }}
                >
                    {(message.isTyping || message.isProcessing) ? (
                        isInstantTypingBubble && instantTypingState ? (
                            <div className="instant-typing-bubble" aria-live="polite">
                                <div className="instant-typing-bubble__label">Tara is thinking</div>
                                {instantTypingState.lines.map((line, index) => {
                                    return (
                                        <div
                                            key={line.key}
                                            className={`instant-typing-line${index > 0 ? ' instant-typing-line--spaced' : ''}`}
                                        >
                                            <span className="instant-typing-text">{line.text}</span>
                                        </div>
                                    );
                                })}
                                {instantTypingState.isTakingLonger ? (
                                    <div className="instant-typing-longer">{INSTANT_LOADER_TAKING_LONGER}</div>
                                ) : null}
                            </div>
                        ) : (
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
                                            <button
                                                type="button"
                                                className="chat-summary-image-thumb"
                                                onClick={() => setSummaryLightboxSrc(resolveSummaryImageSrc(message.summary_image))}
                                                aria-label="Open map full screen"
                                            >
                                                <img
                                                    src={resolveSummaryImageSrc(message.summary_image)}
                                                    alt="Location map"
                                                    onError={(e) => {
                                                        e.currentTarget.style.display = 'none';
                                                        if (e.currentTarget?.parentElement) e.currentTarget.parentElement.style.display = 'none';
                                                    }}
                                                />
                                                <span className="chat-summary-image-thumb__hint">Tap to expand</span>
                                            </button>
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
                        )
                    ) : (
                        <>
                            {/* Always use ResponseRenderer for assistant messages */}
                            {message.role === 'assistant' ? (
                                <>
                                    {message.summary_image && (
                                        <button
                                            type="button"
                                            className="chat-summary-image-thumb"
                                            onClick={() => setSummaryLightboxSrc(resolveSummaryImageSrc(message.summary_image))}
                                            aria-label="Open map full screen"
                                        >
                                            <img
                                                src={resolveSummaryImageSrc(message.summary_image)}
                                                alt="Location map"
                                                onError={(e) => {
                                                    e.currentTarget.style.display = 'none';
                                                    if (e.currentTarget?.parentElement) {
                                                        e.currentTarget.parentElement.style.display = 'none';
                                                    }
                                                }}
                                            />
                                            <span className="chat-summary-image-thumb__hint">Tap to expand</span>
                                        </button>
                                    )}
                                    <div
                                        dangerouslySetInnerHTML={{
                                            __html: formatContent(
                                                shouldBlurDetail ? freeSplit.quick : message.content,
                                                message,
                                            ),
                                        }}
                                    />
                                    {message.instantStreaming ? (
                                        <div className="instant-response-typing" aria-label="Tara is typing" aria-live="polite">
                                            <span />
                                            <span />
                                            <span />
                                        </div>
                                    ) : null}
                                </>
                            ) : (
                                <div dangerouslySetInnerHTML={{ __html: formatContent(message.content) }} />
                            )}
                            {shouldBlurDetail && (
                                <div className="free-detail-paywall">
                                    <div className="free-detail-blur-block">
                                        <p className="free-detail-teaser">
                                            {(freeSplit.detail || '')
                                                .replace(/<[^>]+>/g, ' ')
                                                .replace(/\s+/g, ' ')
                                                .trim()
                                                .slice(0, 280) ||
                                                'Key Insights, Astrological Analysis, Timing & more…'}
                                        </p>
                                    </div>
                                    <button
                                        type="button"
                                        className="free-detail-reveal-btn"
                                        onClick={handleRevealDetailedAnswer}
                                    >
                                        Reveal the detailed answer
                                    </button>
                                    <div className="free-detail-hint">
                                        Standard mode · {standardChatCost} credits
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>

                {renderTimelineSelectionCard()}

                {message.role === 'assistant'
                    && !message.isTyping
                    && !message.isProcessing
                    && messageChatTier !== 'instant'
                    && followUpQuestions.length > 0 && (
                    <div
                        className="follow-up-questions"
                        style={{
                            margin: '16px 0 10px',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'stretch',
                            gap: 8,
                            width: '100%',
                            maxWidth: '100%',
                            minWidth: 0,
                            boxSizing: 'border-box',
                        }}
                    >
                        {followUpQuestions.map((question, index) => (
                            <button
                                key={`follow-up-${index}-${question.slice(0, 24)}`}
                                type="button"
                                className="follow-up-btn"
                                style={{
                                    ...followUpChipLayoutStyle,
                                    background: 'rgba(255, 107, 53, 0.08)',
                                    border: '1px solid rgba(255, 107, 53, 0.25)',
                                    color: '#7c2d12',
                                    padding: '10px 12px',
                                    borderRadius: 20,
                                    fontSize: 13,
                                    lineHeight: 1.4,
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    overflow: 'hidden',
                                }}
                                onClick={() => {
                                    if (onFollowUpClick) onFollowUpClick(question);
                                }}
                            >
                                <span
                                    className="follow-up-btn__label"
                                    style={{
                                        display: 'block',
                                        maxWidth: '100%',
                                        minWidth: 0,
                                        whiteSpace: 'normal',
                                        overflowWrap: 'anywhere',
                                        wordBreak: 'break-word',
                                    }}
                                >
                                    {question}
                                </span>
                            </button>
                        ))}
                    </div>
                )}

                {message.role === 'assistant'
                    && !message.isTyping
                    && !message.isProcessing
                    && messageChatTier !== 'instant'
                    && !isTimelineSelection
                    && showNextActionCard && (
                    <div
                        className="remedy-next-action-card"
                        style={{
                            marginTop: 12,
                            padding: '14px 14px 12px',
                            borderRadius: 16,
                            background: isRemedyNextAction
                                ? 'linear-gradient(180deg, rgba(255,111,76,0.14), rgba(255,111,76,0.08))'
                                : 'linear-gradient(180deg, rgba(91, 112, 255, 0.12), rgba(91, 112, 255, 0.06))',
                            border: isRemedyNextAction
                                ? '1px solid rgba(255,111,76,0.24)'
                                : '1px solid rgba(91, 112, 255, 0.22)',
                        }}
                    >
                        <div className="remedy-next-action-card__title">
                            {isRemedyNextAction ? nextActionTitle : (nextActionTitle || 'Next step')}
                        </div>
                        {isRemedyNextAction && nextActionReason && (
                            <div className="remedy-next-action-card__reason remedy-next-action-card__reason--positive">
                                {nextActionReason}
                            </div>
                        )}
                        {!isRemedyNextAction && nextActionReason && (
                            <div className="remedy-next-action-card__reason">
                                {nextActionReason}
                            </div>
                        )}
                        <button
                            type="button"
                            className="follow-up-btn remedy-next-action-card__button"
                            style={followUpChipLayoutStyle}
                            onClick={() => {
                                const nextQuestion = isRemedyNextAction
                                    ? remedyClickPrompt
                                    : (
                                        nextActionFollowUps[0]
                                            ? String(nextActionFollowUps[0]).trim()
                                        : String(nextActionTitle || 'Open follow-up').trim()
                                    );
                                const sourceMessageId = message.messageId || message.id;
                                if (isRemedyNextAction && sourceMessageId) {
                                    try {
                                        const token = localStorage.getItem('token');
                                        if (token) {
                                            fetch('/api/credits/remedy-funnel/event', {
                                                method: 'POST',
                                                headers: {
                                                    'Content-Type': 'application/json',
                                                    Authorization: `Bearer ${token}`,
                                                },
                                                body: JSON.stringify({
                                                    event: 'card_clicked',
                                                    message_id: String(sourceMessageId),
                                                    platform: 'web',
                                                }),
                                            }).catch(() => {});
                                        }
                                    } catch (_) {
                                        /* ignore */
                                    }
                                }
                                console.log('[MessageBubble] remedy card clicked', {
                                    hasNextAction,
                                    isRemedyNextAction,
                                    nextActionType,
                                    nextActionTitle,
                                    nextActionReason,
                                    nextActionFollowUps,
                                    nextQuestion,
                                });
                                if (onFollowUpClick && nextQuestion) {
                                    try {
                                        console.log('[MessageBubble] remedy button click payload', {
                                            question: nextQuestion,
                                            query_context: {
                                                follow_up_type: isRemedyNextAction ? 'remedy_action' : (nextActionType || 'follow_up'),
                                                remedy_followup: isRemedyNextAction,
                                                open_remedy: isRemedyNextAction,
                                                source_next_action: nextAction,
                                                remedy_title: nextActionTitle || undefined,
                                                remedy_reason: nextActionReason || undefined,
                                                remedy_follow_up_questions: nextActionFollowUps,
                                            },
                                        });
                                    } catch (err) {
                                        // ignore logging failures
                                    }
                                    onFollowUpClick(nextQuestion, {
                                        directSend: false,
                                        query_context: {
                                            follow_up_type: isRemedyNextAction ? 'remedy_action' : (nextActionType || 'follow_up'),
                                            remedy_followup: isRemedyNextAction,
                                            open_remedy: isRemedyNextAction,
                                            source_next_action: nextAction,
                                            source_message_id: sourceMessageId ? String(sourceMessageId) : undefined,
                                            remedy_title: nextActionTitle || undefined,
                                            remedy_reason: nextActionReason || undefined,
                                            remedy_follow_up_questions: nextActionFollowUps,
                                        },
                                    });
                                }
                            }}
                            style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: 8,
                                background: isRemedyNextAction ? '#ff6b35' : '#5167e8',
                                color: '#fff',
                                border: 'none',
                                borderRadius: 999,
                                padding: '10px 16px',
                                fontWeight: 800,
                                fontSize: 14,
                                cursor: 'pointer',
                                boxShadow: '0 4px 14px rgba(255,107,53,0.22)',
                            }}
                        >
                            {isRemedyNextAction
                                ? remedyCardButton
                                : (nextActionFollowUps[0] ? String(nextActionFollowUps[0]) : 'Open follow-up')}
                        </button>
                    </div>
                )}

                {isNativeGate && !message.isTyping && !message.isProcessing && (
                    <div className="native-gate-actions">
                        <p className="native-gate-helper">
                            Please choose one of the options below instead of typing a reply.
                        </p>
                        <div className="native-gate-ctas">
                        {showRelationshipOptions && relationshipGateOptions.map((option, index) => {
                            const label = String(option?.label || option?.value || '').trim();
                            const value = String(option?.value || label).trim();
                            if (!label || !value) return null;
                            const originalQuestion = String(gateMetadata.original_question || '').trim();
                            const nextQuestion = originalQuestion
                                ? `${originalQuestion}\n\nRelationship context: ${value}`
                                : `Relationship context: ${value}`;
                            return (
                                <button
                                    key={`relationship-gate-${index}-${label}`}
                                    type="button"
                                    onClick={() => {
                                        if (onRelationshipContextGate) {
                                            onRelationshipContextGate(gateMetadata, value, nextQuestion);
                                        } else if (onFollowUpClick) {
                                            onFollowUpClick(nextQuestion);
                                        }
                                    }}
                                    style={{
                                        border: '1px solid rgba(234, 88, 12, 0.26)',
                                        background: 'rgba(255, 247, 237, 0.95)',
                                        color: '#9a3412',
                                        padding: '7px 12px',
                                        borderRadius: 999,
                                        cursor: 'pointer',
                                        fontWeight: 700,
                                        fontSize: 13,
                                    }}
                                >
                                    {label}
                                </button>
                            );
                        })}
                        {(isSubjectChartGate || isPartnershipOfferGate) && onNativeGateOpenSelectNative && (
                            <button
                                type="button"
                                onClick={() => onNativeGateOpenSelectNative()}
                                style={{
                                    background: '#7c2d12',
                                    border: '1px solid #7c2d12',
                                    borderRadius: 999,
                                    padding: '9px 15px',
                                    cursor: 'pointer',
                                    color: '#ffffff',
                                    fontWeight: 800,
                                    fontSize: 14,
                                    lineHeight: 1.2,
                                    boxShadow: '0 2px 6px rgba(124, 45, 18, 0.24)',
                                }}
                            >
                                Select native
                            </button>
                        )}
                        {(isSubjectChartGate || isPartnershipOfferGate) && onNativeGateOpenAddProfile && (
                            <button
                                type="button"
                                onClick={() => {
                                    const hint = gateMetadata.extracted_birth_hint || {};
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
                                {gateIntent === 'complete_subject_birth_details'
                                    ? 'Complete birth profile'
                                    : 'Add new native'}
                            </button>
                        )}
                        {isPartnershipOfferGate && onStartPartnershipGate && (
                            <button
                                type="button"
                                className="native-gate-cta native-gate-cta--secondary"
                                onClick={() => onStartPartnershipGate(gateMetadata)}
                            >
                                Start Partnership Analysis
                            </button>
                        )}
                        {(isSubjectChartGate || isPartnershipOfferGate) && onContinueSingleChartGate && (
                            <button
                                type="button"
                                className="native-gate-cta native-gate-cta--plain"
                                onClick={() => onContinueSingleChartGate(gateMetadata)}
                            >
                                Continue with my chart only
                            </button>
                        )}
                        </div>
                    </div>
                )}

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
                <div className="message-footer">
                    {renderMessageToolbar('bottom')}
                    <div className="message-timestamp">
                        {new Date(message.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                    </div>
                </div>
            </div>
            
            <PodcastLanguageModal
                open={showPodcastLanguageModal}
                selectedLang={podcastListenLang}
                uiLanguage={language}
                included={isPremiumChatMessage}
                onSelect={continuePodcastAfterLanguage}
                onClose={() => {
                    skipPodcastCreditsRef.current = false;
                    setShowPodcastLanguageModal(false);
                }}
            />

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

            {summaryLightboxSrc && (
                <ZoomableImageLightbox
                    src={summaryLightboxSrc}
                    alt="Location map"
                    onClose={() => setSummaryLightboxSrc(null)}
                />
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
