import React, { useState, useEffect, useRef } from 'react';
import { useCredits } from '../../context/CreditContext';
import { speakThinkingHandoff } from '../../utils/speechThinkingHandoff';

const MOBILE_PREMIUM_MQ = '(max-width: 768px)';

const getSpeechRecognitionClass = () => {
    if (typeof window === 'undefined') return null;
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
};

const getSpeechRecognitionLang = (isMundaneMode = false, isPartnershipMode = false) => {
    if (isMundaneMode) return 'en-US';
    if (isPartnershipMode) return 'en-US';
    return 'en-US';
};

const ChatInput = ({
    onSendMessage,
    isLoading,
    followUpQuestion = '',
    onFollowUpUsed = () => {},
    onOpenCreditsModal,
    onShowEnhancedPopup,
    isPartnershipMode = false,
    isMundaneMode = false,
    isLocked = false, // when true, composer is disabled until guided steps are completed
    isAssistantSpeaking = false,
    onInterruptAssistantSpeech = () => {},
    instantMode = false,
    onInstantModeChange = () => {},
}) => {
    const {
        credits,
        chatCost,
        premiumChatCost,
        partnershipCost,
        loading: creditsLoading,
        freeQuestionAvailable,
        freeQuestionRequiresNotifications,
        fetchBalance,
        instantChatCost,
        instantChatEnabled,
        speechChatEnabled,
    } = useCredits();
    const [message, setMessage] = useState('');
    const [isPremiumAnalysis, setIsPremiumAnalysis] = useState(false);
    const [showModeSelector, setShowModeSelector] = useState(false);
    const [isSpeechSupported, setIsSpeechSupported] = useState(() => Boolean(getSpeechRecognitionClass()));
    const [isSpeechListening, setIsSpeechListening] = useState(false);
    const [speechError, setSpeechError] = useState('');
    const [isMobileLayout, setIsMobileLayout] = useState(
        typeof window !== 'undefined' && window.matchMedia(MOBILE_PREMIUM_MQ).matches
    );
    const suggestionsScrollRef = useRef(null);
    const recognitionRef = useRef(null);
    const finalTranscriptRef = useRef('');
    const shouldAutoSendSpeechRef = useRef(false);
    const messageRef = useRef('');

    useEffect(() => {
        if (typeof window === 'undefined') return;
        const mq = window.matchMedia(MOBILE_PREMIUM_MQ);
        const onChange = () => setIsMobileLayout(mq.matches);
        onChange();
        mq.addEventListener('change', onChange);
        return () => mq.removeEventListener('change', onChange);
    }, []);

    useEffect(() => {
        setIsSpeechSupported(Boolean(getSpeechRecognitionClass()));
    }, []);

    useEffect(() => {
        messageRef.current = message;
    }, [message]);

    useEffect(() => {
        if (isPartnershipMode || isMundaneMode) {
            setIsPremiumAnalysis(false);
            setShowModeSelector(false);
            onInstantModeChange(false);
        }
    }, [isPartnershipMode, isMundaneMode, onInstantModeChange]);

    const showPremiumControls = !isPartnershipMode && !isMundaneMode;
    const useCompactPremium = showPremiumControls && isMobileLayout;
    const useFreeQuestionEligible = showPremiumControls && freeQuestionAvailable;

    useEffect(() => {
        if (useFreeQuestionEligible && isPremiumAnalysis) {
            setIsPremiumAnalysis(false);
        }
    }, [useFreeQuestionEligible, isPremiumAnalysis]);

    useEffect(() => {
        if (!instantChatEnabled && instantMode) {
            onInstantModeChange(false);
        }
    }, [instantChatEnabled, instantMode, onInstantModeChange]);

    useEffect(() => {
        if (useFreeQuestionEligible && instantMode) {
            onInstantModeChange(false);
        }
    }, [useFreeQuestionEligible, instantMode, onInstantModeChange]);

    const scrollSuggestions = (direction) => {
        const el = suggestionsScrollRef.current;
        if (!el) return;
        el.scrollBy({ left: direction * 280, behavior: 'smooth' });
    };
    
    useEffect(() => {
        if (followUpQuestion) {
            setMessage(followUpQuestion);
            onFollowUpUsed();
        }
    }, [followUpQuestion, onFollowUpUsed]);

    useEffect(() => () => {
        if (recognitionRef.current) {
            recognitionRef.current.onstart = null;
            recognitionRef.current.onresult = null;
            recognitionRef.current.onerror = null;
            recognitionRef.current.onend = null;
            recognitionRef.current.abort();
            recognitionRef.current = null;
        }
    }, []);

    const isInstantSendMode =
        showPremiumControls
        && instantMode
        && instantChatEnabled
        && !useFreeQuestionEligible
        && !isPremiumAnalysis
        && !isPartnershipMode
        && !isMundaneMode;

    const effectiveCost =
        useFreeQuestionEligible && !isPremiumAnalysis && !instantMode
            ? 0
            : isPremiumAnalysis
                ? premiumChatCost
                : isPartnershipMode
                    ? partnershipCost
                    : isInstantSendMode
                        ? instantChatCost
                        : chatCost;

    const canSendMessage = !isLoading && credits >= effectiveCost && !isLocked;
    const useInstantVoiceSend =
        showPremiumControls
        && instantMode
        && !isPremiumAnalysis
        && !isPartnershipMode
        && !isMundaneMode
        && !useFreeQuestionEligible
        && instantChatEnabled
        && speechChatEnabled;
    const canSendInstantMessage = !isLoading && !isLocked && credits >= instantChatCost;

    const commitSend = (text, premiumOverride = null, sendOptions = {}) => {
        const trimmed = String(text || '').trim();
        const isInstantSend = Boolean(sendOptions.instant_chat || sendOptions.chat_tier === 'instant');
        if (!trimmed) return false;
        if (isInstantSend && !canSendInstantMessage) return false;
        if (!isInstantSend && !canSendMessage) return false;
        const premiumForSend = useFreeQuestionEligible ? false : (premiumOverride ?? isPremiumAnalysis);
        console.log('[ChatInput] commitSend unconditional', {
            trimmed,
            premiumForSend,
            sendOptions,
            isInstantSend,
            isPartnershipMode,
            isMundaneMode,
        });
        try {
            console.log('[ChatInput] send button submit payload', {
                text: trimmed,
                premium_analysis: premiumForSend,
                sendOptions,
            });
        } catch (err) {
            // ignore logging failures
        }
        onSendMessage(trimmed, {
            premium_analysis: premiumForSend,
            ...sendOptions,
        });
        setMessage('');
        setSpeechError('');
        finalTranscriptRef.current = '';
        messageRef.current = '';
        return true;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (isLocked) return;
        if (isInstantSendMode) {
            commitSend(message, false, { chat_tier: 'instant', instant_chat: true });
            return;
        }
        commitSend(message);
    };

    const stopSpeechRecognition = () => {
        shouldAutoSendSpeechRef.current = true;
        recognitionRef.current?.stop();
        setIsSpeechListening(false);
    };

    const canStartSpeechSession =
        speechChatEnabled
        && (useInstantVoiceSend ? canSendInstantMessage : canSendMessage);

    const startSpeechRecognition = () => {
        if (!canStartSpeechSession) return;

        const SpeechRecognitionClass = getSpeechRecognitionClass();
        if (!SpeechRecognitionClass) {
            setSpeechError('Speech recognition is not supported in this browser.');
            return;
        }

        setSpeechError('');
        finalTranscriptRef.current = '';
        shouldAutoSendSpeechRef.current = true;

        const recognition = new SpeechRecognitionClass();
        recognition.lang = getSpeechRecognitionLang(isMundaneMode, isPartnershipMode);
        recognition.interimResults = true;
        recognition.continuous = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            setIsSpeechListening(true);
            setSpeechError('');
            setMessage('');
        };

        recognition.onresult = (event) => {
            let finalText = '';
            let interimText = '';

            for (let i = 0; i < event.results.length; i += 1) {
                const fragment = event.results[i]?.[0]?.transcript || '';
                if (event.results[i].isFinal) {
                    finalText += fragment;
                } else {
                    interimText += fragment;
                }
            }

            const combined = `${finalText} ${interimText}`.trim();
            finalTranscriptRef.current = finalText.trim();
            setMessage(combined);
        };

        recognition.onerror = (event) => {
            setIsSpeechListening(false);
            recognitionRef.current = null;
            if (event?.error === 'aborted') return;
            shouldAutoSendSpeechRef.current = false;
            if (event?.error === 'no-speech') {
                setSpeechError('No speech was detected. Please try again.');
                return;
            }
            if (event?.error === 'not-allowed' || event?.error === 'service-not-allowed') {
                setSpeechError('Microphone permission was blocked for this site.');
                return;
            }
            setSpeechError('Speech recognition failed. Please try again.');
        };

        recognition.onend = () => {
            setIsSpeechListening(false);
            recognitionRef.current = null;
            const transcriptToSend = String(finalTranscriptRef.current || messageRef.current || '').trim();
            const shouldSend = shouldAutoSendSpeechRef.current;
            shouldAutoSendSpeechRef.current = false;

            if (!shouldSend || !transcriptToSend) return;

            void (async () => {
                if (useInstantVoiceSend && canSendInstantMessage) {
                    await speakThinkingHandoff();
                    commitSend(transcriptToSend, false, {
                        premium_analysis: false,
                        chat_tier: 'instant',
                        instant_chat: true,
                    });
                    return;
                }
                if (canSendMessage) {
                    commitSend(transcriptToSend, false, {});
                }
            })();
        };

        recognitionRef.current = recognition;
        recognition.start();
    };

    const handleSpeechButton = () => {
        if (isAssistantSpeaking) {
            onInterruptAssistantSpeech();
            setTimeout(() => {
                startSpeechRecognition();
            }, 120);
            return;
        }
        if (isSpeechListening) {
            stopSpeechRecognition();
            return;
        }
        startSpeechRecognition();
    };

    const suggestions = isMundaneMode
        ? [
            "What are the likely phases for this event category this year?",
            "What risks might show up, and how can we prepare?",
            "Which outcomes look more probable, and when?",
            "What broader macro themes are active right now?",
            "Are there signs of stability or volatility ahead?",
            "What should we watch in the next few months?",
        ]
        : isPartnershipMode
            ? [
                "What supportive themes show up between these two charts?",
                "What frictions or blind spots are worth awareness?",
                "How do communication or emotional needs differ here?",
                "What timing or planetary periods matter for this connection?",
                "What karmic or growth patterns appear in this pairing?",
                "What practical steps would improve mutual understanding?",
            ]
            : [
                "What does my birth chart say about my career?",
                "When is a good time for marriage?",
                "What are my health vulnerabilities?",
                "Tell me about my current dasha period",
                "What do the current transits mean for me?",
                "What are my strengths and weaknesses?",
            ];

    return (
        <div className="chat-input-container chat-composer">
            {!creditsLoading && useFreeQuestionEligible && (
                <div className="credit-warning" style={{ background: 'rgba(34, 197, 94, 0.12)', borderColor: 'rgba(34, 197, 94, 0.35)' }}>
                    <span style={{ color: '#166534' }}>Your first standard chart question is free. Premium uses credits.</span>
                </div>
            )}
            {!creditsLoading && showPremiumControls && freeQuestionRequiresNotifications && credits < effectiveCost && (
                <div
                    className="credit-warning"
                    style={{
                        background: 'rgba(59, 130, 246, 0.1)',
                        borderColor: 'rgba(59, 130, 246, 0.35)',
                        display: 'flex',
                        flexWrap: 'wrap',
                        alignItems: 'center',
                        gap: '10px',
                        justifyContent: 'space-between',
                    }}
                >
                    <span style={{ color: '#1e3a8a' }}>
                        Allow browser notifications to unlock your free first standard question (one-time).
                    </span>
                    <button
                        type="button"
                        className="get-credits-btn"
                        onClick={async () => {
                            if (typeof window === 'undefined' || !('Notification' in window)) {
                                window.alert('This browser does not support notifications. Use the mobile app or add credits to continue.');
                                return;
                            }
                            const perm = await Notification.requestPermission();
                            if (perm !== 'granted') {
                                window.alert('Notifications were blocked. Allow them for this site in your browser settings, then try again.');
                                return;
                            }
                            try {
                                const token = localStorage.getItem('token');
                                await fetch('/api/credits/web-notification-opt-in', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        ...(token && { Authorization: `Bearer ${token}` }),
                                    },
                                    body: JSON.stringify({ granted: true }),
                                });
                            } catch (_) {
                                /* ignore */
                            }
                            await fetchBalance();
                        }}
                    >
                        Allow notifications
                    </button>
                </div>
            )}
            {!creditsLoading && credits < effectiveCost && !freeQuestionRequiresNotifications && (
                <div className="credit-warning">
                    <span>
                        Insufficient credits ({credits}/{effectiveCost} required for{' '}
                        {isPremiumAnalysis
                            ? 'Premium Deep Analysis'
                            : isPartnershipMode
                                ? 'Partnership Analysis'
                                : isInstantSendMode
                                    ? 'Instant Analysis'
                                    : 'Standard Analysis'}
                        )
                    </span>
                    <button onClick={onOpenCreditsModal} className="get-credits-btn">
                        Get Credits
                    </button>
                </div>
            )}
            <div
                className="premium-toggle-container chat-composer-premium"
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'stretch',
                    gap: useCompactPremium ? '8px' : '10px',
                    marginBottom: '10px',
                    padding: useCompactPremium ? '6px 8px' : '8px 12px',
                    background: 'rgba(255,107,53,0.06)',
                    border: '1px solid rgba(0,0,0,0.06)',
                    borderRadius: '8px',
                    fontSize: useCompactPremium ? '12px' : '14px',
                }}
            >
                {useCompactPremium && showModeSelector && (
                    <div className="chat-premium-mode-expanded" role="group" aria-label="Question mode">
                        <button
                            type="button"
                            className={`chat-premium-mode-pill ${!isPremiumAnalysis && !instantMode ? 'chat-premium-mode-pill--active' : ''}`}
                            disabled={isLocked}
                            onClick={() => {
                                setIsPremiumAnalysis(false);
                                onInstantModeChange(false);
                                setShowModeSelector(false);
                            }}
                        >
                            <span className="chat-premium-mode-pill__label">Standard</span>
                            <span className="chat-premium-mode-pill__cost">
                                {useFreeQuestionEligible ? 'Free' : `${chatCost} credit${chatCost !== 1 ? 's' : ''}`}
                            </span>
                        </button>
                        {instantChatEnabled && (
                            <button
                                type="button"
                                className={`chat-premium-mode-pill ${instantMode && !isPremiumAnalysis ? 'chat-premium-mode-pill--active-instant' : ''}`}
                                disabled={isLocked || useFreeQuestionEligible}
                                title={useFreeQuestionEligible ? 'Use your free standard question first; instant uses credits.' : undefined}
                                onClick={() => {
                                    if (useFreeQuestionEligible) return;
                                    setIsPremiumAnalysis(false);
                                    onInstantModeChange(true);
                                    setShowModeSelector(false);
                                }}
                            >
                                <span className="chat-premium-mode-pill__label">Instant</span>
                                <span className="chat-premium-mode-pill__cost">
                                    {instantChatCost} credit{instantChatCost !== 1 ? 's' : ''}
                                </span>
                            </button>
                        )}
                        <button
                            type="button"
                            className={`chat-premium-mode-pill ${isPremiumAnalysis ? 'chat-premium-mode-pill--active-premium' : ''}`}
                            disabled={isLocked || useFreeQuestionEligible}
                            title={useFreeQuestionEligible ? 'Use your free standard question first; premium uses credits.' : undefined}
                            onClick={() => {
                                if (useFreeQuestionEligible) return;
                                onInstantModeChange(false);
                                setIsPremiumAnalysis(true);
                                setShowModeSelector(false);
                            }}
                        >
                            <span className="chat-premium-mode-pill__label">Premium</span>
                            <span className="chat-premium-mode-pill__cost">
                                {premiumChatCost} credit{premiumChatCost !== 1 ? 's' : ''}
                            </span>
                        </button>
                    </div>
                )}

                {!useCompactPremium && (
                    <div className="chat-composer-premium-row" style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                        {instantChatEnabled && (
                            <label
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    cursor: isLocked || useFreeQuestionEligible ? 'not-allowed' : 'pointer',
                                    color: '#111827',
                                    opacity: useFreeQuestionEligible ? 0.65 : 1,
                                }}
                                title={useFreeQuestionEligible ? 'First question is free for standard analysis only.' : undefined}
                            >
                                <input
                                    type="checkbox"
                                    checked={instantMode && !isPremiumAnalysis}
                                    onChange={(e) => {
                                        if (useFreeQuestionEligible || isLocked) return;
                                        const on = e.target.checked;
                                        onInstantModeChange(on);
                                        if (on) setIsPremiumAnalysis(false);
                                    }}
                                    style={{ transform: 'scale(1.2)' }}
                                    disabled={isLocked || useFreeQuestionEligible}
                                />
                                <span className="chat-premium-label">⚡ Instant answer</span>
                            </label>
                        )}
                        <label
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                cursor: isLocked || useFreeQuestionEligible ? 'not-allowed' : 'pointer',
                                color: '#111827',
                                opacity: useFreeQuestionEligible ? 0.65 : 1,
                            }}
                            title={useFreeQuestionEligible ? 'First question is free for standard analysis only.' : undefined}
                        >
                            <input
                                type="checkbox"
                                checked={isPremiumAnalysis}
                                onChange={(e) => {
                                    if (useFreeQuestionEligible) return;
                                    const v = e.target.checked;
                                    setIsPremiumAnalysis(v);
                                    if (v) onInstantModeChange(false);
                                }}
                                style={{ transform: 'scale(1.2)' }}
                                disabled={isLocked || useFreeQuestionEligible}
                            />
                            <span className="chat-premium-label">🚀 Premium Deep Analysis</span>
                        </label>
                        <span style={{
                            background: isPremiumAnalysis
                                ? 'linear-gradient(45deg, #ff6b35, #ffd700)'
                                : instantMode && instantChatEnabled && !useFreeQuestionEligible
                                    ? 'linear-gradient(45deg, #fb923c, #f97316)'
                                    : '#666',
                            color: '#ffffff',
                            padding: '4px 8px',
                            borderRadius: '12px',
                            fontSize: '11px',
                            fontWeight: 'bold',
                            boxShadow: isPremiumAnalysis || (instantMode && instantChatEnabled)
                                ? '0 2px 8px rgba(255, 107, 53, 0.3)'
                                : 'none'
                        }}>
                            {isPremiumAnalysis
                                ? `${premiumChatCost} credits`
                                : instantMode && instantChatEnabled && !useFreeQuestionEligible
                                    ? `${instantChatCost} credits`
                                    : useFreeQuestionEligible && !isPartnershipMode
                                        ? 'Free'
                                        : `${isPartnershipMode ? partnershipCost : chatCost} credits`}
                        </span>
                        {isPremiumAnalysis && (
                            <span
                                className="enhanced-analysis-badge"
                                onClick={() => onShowEnhancedPopup && onShowEnhancedPopup()}
                                style={{ cursor: 'pointer' }}
                            >
                                ✨ Enhanced Analysis
                            </span>
                        )}
                    </div>
                )}

                {!isLoading && !isLocked && (
                    <div className="suggestions-scroll-wrapper">
                        <button
                            type="button"
                            className="suggestions-arrow-btn"
                            onClick={() => scrollSuggestions(-1)}
                            aria-label="Scroll suggestions left"
                        >
                            ←
                        </button>
                        <div
                            ref={suggestionsScrollRef}
                            className="suggestions-scroll-row"
                        >
                            {suggestions.map((suggestion, index) => (
                                <button
                                    key={index}
                                    className="suggestion-button suggestion-chip"
                                    onClick={() => setMessage(suggestion)}
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                        <button
                            type="button"
                            className="suggestions-arrow-btn"
                            onClick={() => scrollSuggestions(1)}
                            aria-label="Scroll suggestions right"
                        >
                            →
                        </button>
                    </div>
                )}
            </div>
            <form onSubmit={handleSubmit} className="chat-input-form">
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder={
                        isLocked
                            ? 'Complete the guided steps above to unlock chat...'
                            : isLoading
                                ? "Analyzing your chart..."
                                : credits < effectiveCost
                                    ? "Insufficient credits"
                                    : useCompactPremium && showModeSelector
                                        ? 'Type here...'
                                        : isPartnershipMode
                                            ? "Ask about your compatibility..."
                                            : isMundaneMode
                                                ? "Ask about global events..."
                                                : isInstantSendMode
                                                    ? 'Ask a quick question…'
                                                    : "Ask me about your birth chart..."
                    }
                    disabled={isLoading || credits < effectiveCost || isLocked}
                    className={`chat-input${useCompactPremium && showModeSelector ? ' chat-input--mode-select-open' : ''}`}
                />
                <button
                    type="button"
                    className={`speech-button ${isSpeechListening ? 'speech-button--listening' : ''}`}
                    onClick={handleSpeechButton}
                    disabled={!isSpeechSupported || !speechChatEnabled || isLoading || isLocked || (useInstantVoiceSend ? credits < instantChatCost : credits < effectiveCost)}
                    aria-label={
                        isAssistantSpeaking
                            ? 'Interrupt and ask a follow-up'
                            : isSpeechListening
                                ? 'Stop listening'
                                : 'Speak your question'
                    }
                    title={
                        !isSpeechSupported
                            ? 'Speech recognition is not supported in this browser'
                            : !speechChatEnabled
                                ? 'Voice features are not available right now'
                                : useInstantVoiceSend && credits < instantChatCost
                                    ? `Instant speech uses ${instantChatCost} credit${instantChatCost !== 1 ? 's' : ''}`
                                    : isAssistantSpeaking
                                        ? 'Interrupt and ask the next question'
                                        : isSpeechListening
                                            ? 'Stop listening'
                                            : 'Speak your question'
                    }
                >
                    <span className="speech-button__icon" aria-hidden="true">
                        {isAssistantSpeaking ? '⏭' : isSpeechListening ? '■' : '🎤'}
                    </span>
                    <span className="speech-button__label">
                        {isAssistantSpeaking ? 'Interrupt' : isSpeechListening ? 'Stop' : 'Speak'}
                    </span>
                </button>
                {useCompactPremium && (
                    <>
                        <button
                            type="button"
                            className={`chat-premium-sp-toggle ${isPremiumAnalysis ? 'chat-premium-sp-toggle--premium' : ''} ${instantMode && !isPremiumAnalysis ? 'chat-premium-sp-toggle--instant' : ''} ${showModeSelector ? 'chat-premium-sp-toggle--open' : ''}`}
                            onClick={() => !isLocked && !useFreeQuestionEligible && setShowModeSelector((v) => !v)}
                            disabled={isLocked || useFreeQuestionEligible}
                            title={
                                useFreeQuestionEligible
                                    ? 'First question: standard (free)'
                                    : isPremiumAnalysis
                                        ? 'Premium mode — tap to change'
                                        : instantMode
                                            ? 'Instant mode — tap to change'
                                            : 'Standard mode — tap to change'
                            }
                            aria-expanded={showModeSelector}
                            aria-label={
                                isPremiumAnalysis
                                    ? 'Premium analysis selected. Open mode picker'
                                    : instantMode
                                        ? 'Instant analysis selected. Open mode picker'
                                        : 'Standard analysis. Open mode picker'
                            }
                        >
                            {isPremiumAnalysis ? (
                                <span className="chat-premium-sp-toggle__inner chat-premium-sp-toggle__inner--p">P</span>
                            ) : instantMode ? (
                                <span className="chat-premium-sp-toggle__inner chat-premium-sp-toggle__inner--i">I</span>
                            ) : (
                                <span className="chat-premium-sp-toggle__inner chat-premium-sp-toggle__inner--s">S</span>
                            )}
                        </button>
                        {isPremiumAnalysis && onShowEnhancedPopup && (
                            <button
                                type="button"
                                className="chat-premium-enhanced-icon"
                                onClick={() => onShowEnhancedPopup()}
                                title="What is enhanced premium analysis?"
                                aria-label="Premium analysis details"
                            >
                                ✨
                            </button>
                        )}
                    </>
                )}
                <button 
                    type="submit" 
                    disabled={!message.trim() || isLoading || credits < effectiveCost || isLocked}
                    className="send-button"
                    aria-label={
                        isLoading
                            ? 'Sending'
                            : credits < effectiveCost
                                ? 'Insufficient credits'
                                : isPremiumAnalysis
                                    ? 'Send premium question'
                                    : isInstantSendMode
                                        ? 'Send instant question'
                                        : isPartnershipMode
                                            ? 'Send partnership question'
                                            : 'Send message'
                    }
                    style={{
                        background: isPremiumAnalysis
                            ? 'linear-gradient(45deg, #ff6b35, #ffd700)'
                            : isInstantSendMode
                                ? 'linear-gradient(45deg, #fb923c, #ea580c)'
                                : undefined,
                        boxShadow: isPremiumAnalysis || isInstantSendMode
                            ? '0 2px 12px rgba(255, 107, 53, 0.4)'
                            : undefined
                    }}
                >
                    <span className="send-button__label-desktop">
                        {isLoading
                            ? '...'
                            : credits < effectiveCost
                                ? 'No Credits'
                                : isPremiumAnalysis
                                    ? '🚀 Send Premium'
                                    : isInstantSendMode
                                        ? '⚡ Send Instant'
                                        : isPartnershipMode
                                            ? '💕 Send Partnership'
                                            : 'Send'}
                    </span>
                    <span className="send-button__label-mobile" aria-hidden="true">
                        {isLoading
                            ? '…'
                            : credits < effectiveCost
                                ? '—'
                                : isPremiumAnalysis
                                    ? '🚀'
                                    : isInstantSendMode
                                        ? '⚡'
                                        : isPartnershipMode
                                            ? '💕'
                                            : '➤'}
                    </span>
                </button>
            </form>
            {(speechError || isSpeechListening) && (
                <div className={`speech-status ${speechError ? 'speech-status--error' : 'speech-status--listening'}`}>
                    {speechError || 'Listening… speak naturally and pause when done.'}
                </div>
            )}
            {!speechError && !isSpeechListening && isAssistantSpeaking && (
                <div className="speech-status speech-status--listening">
                    AstroRoshni is speaking. Tap the mic to interrupt and ask the next question.
                </div>
            )}
            {!creditsLoading && (
                <div className="credit-info chat-composer-footnote">
                    Credits: {credits} |{' '}
                    {isPremiumAnalysis
                        ? `Premium: ${premiumChatCost}`
                        : isPartnershipMode
                            ? `Partnership: ${partnershipCost}`
                            : useFreeQuestionEligible
                                ? 'Standard: free (first question)'
                                : isInstantSendMode
                                    ? `Instant: ${instantChatCost}`
                                    : `Standard: ${chatCost}`}{' '}
                    {!useFreeQuestionEligible || isPremiumAnalysis || isPartnershipMode || isInstantSendMode ? 'credits per question' : ''}
                </div>
            )}
        </div>
    );
};

export default ChatInput;
