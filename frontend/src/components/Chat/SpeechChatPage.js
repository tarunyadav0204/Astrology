import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { buildQueryContext } from '../../utils/queryContext';
import textToSpeech from '../../utils/textToSpeech';
import { speakThinkingHandoff } from '../../utils/speechThinkingHandoff';
import './SpeechChatPage.css';

const POLL_INTERVAL_MS = 1400;

function readStoredWebUserName() {
    try {
        const raw = localStorage.getItem('user');
        const u = raw ? JSON.parse(raw) : null;
        return String(u?.name || u?.full_name || '').trim();
    } catch {
        return '';
    }
}

function buildTaraGreeting(displayName, chartFirstName) {
    const chart = String(chartFirstName || 'this').trim();
    const user = String(displayName || '').trim();
    if (user) {
        return `Hello ${user}, I'm Tara, your voice guide on AstroRoshni. Thanks for sharing ${chart}'s chart. How can I help you? Do you have a question for me?`;
    }
    return `Hello, I'm Tara, your voice guide on AstroRoshni. Thanks for sharing ${chart}'s chart. How can I help you? Do you have a question for me?`;
}

const getSpeechRecognitionClass = () => {
    if (typeof window === 'undefined') return null;
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
};

const getSpeechRecognitionLang = () => 'en-US';

const toChatBirthDetails = (birthData) => ({
    name: birthData?.name,
    date: typeof birthData?.date === 'string' ? birthData.date.split('T')[0] : birthData?.date,
    time: typeof birthData?.time === 'string'
        ? birthData.time.split('T')[1]?.slice(0, 5) || birthData.time
        : birthData?.time,
    latitude: parseFloat(birthData?.latitude),
    longitude: parseFloat(birthData?.longitude),
    place: birthData?.place || '',
    gender: birthData?.gender || '',
});

const SpeechChatPage = () => {
    const navigate = useNavigate();
    const { birthData } = useAstrology();
    const {
        credits,
        fetchBalance,
        instantChatCost,
        speechChatCost,
        instantChatEnabled,
        speechChatEnabled,
    } = useCredits();

    const [sessionId, setSessionId] = useState(null);
    const [turns, setTurns] = useState([]);
    const [status, setStatus] = useState('idle');
    const [currentTranscript, setCurrentTranscript] = useState('');
    const [errorText, setErrorText] = useState('');
    const [handsFree, setHandsFree] = useState(true);
    const [followUps, setFollowUps] = useState([]);
    const [isSpeechSupported, setIsSpeechSupported] = useState(() => Boolean(getSpeechRecognitionClass()));
    const [displayUserName] = useState(() => readStoredWebUserName());

    const recognitionRef = useRef(null);
    const finalTranscriptRef = useRef('');
    const liveTranscriptRef = useRef('');
    const shouldAutoSendSpeechRef = useRef(false);
    const mountedRef = useRef(true);
    const thinkingTurnIdRef = useRef(null);
    const autoRestartTimerRef = useRef(null);
    const scrollRef = useRef(null);
    const greetedRef = useRef(false);
    const startListeningRef = useRef(() => {});
    const handsFreeRef = useRef(handsFree);

    handsFreeRef.current = handsFree;

    const taraStatusLabels = useMemo(() => ({
        idle: handsFree
            ? 'Tap the mic and AstroRoshni will keep listening after each answer'
            : 'Tap the mic and ask your question',
        listening: 'Listening… tap again when done',
        thinking: 'Reading the chart…',
        speaking: 'Speaking the answer… tap to stop',
    }), [handsFree]);

    useEffect(() => {
        mountedRef.current = true;
        setIsSpeechSupported(Boolean(getSpeechRecognitionClass()));
        return () => {
            mountedRef.current = false;
            if (recognitionRef.current) {
                recognitionRef.current.onstart = null;
                recognitionRef.current.onresult = null;
                recognitionRef.current.onerror = null;
                recognitionRef.current.onend = null;
                recognitionRef.current.abort();
                recognitionRef.current = null;
            }
            if (autoRestartTimerRef.current) {
                clearTimeout(autoRestartTimerRef.current);
                autoRestartTimerRef.current = null;
            }
            textToSpeech.stop();
        };
    }, []);

    useEffect(() => {
        if (!currentTranscript) return undefined;
        const el = scrollRef.current;
        if (!el) return undefined;
        const timer = setTimeout(() => {
            el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
        }, 60);
        return () => clearTimeout(timer);
    }, [currentTranscript]);

    const chartLabel = useMemo(() => {
        if (!birthData?.name) return 'your selected chart';
        return `${birthData.name}'s chart`;
    }, [birthData]);

    const headerSubtitle = useMemo(() => {
        if (!birthData?.name) return 'Voice guide on AstroRoshni · Instant spoken answers';
        return `Voice guide on AstroRoshni · Instant answers for ${birthData.name}`;
    }, [birthData?.name]);

    useEffect(() => {
        greetedRef.current = false;
    }, [birthData?.id]);

    const ensureSession = async () => {
        if (sessionId) return sessionId;
        const token = localStorage.getItem('token');
        const birthChartId = birthData?.id ?? null;
        const response = await fetch('/api/chat-v2/session', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                birth_chart_id: birthChartId,
                query_context: buildQueryContext(),
            }),
        });

        if (!response.ok) {
            throw new Error('Could not start a speech session right now.');
        }

        const data = await response.json();
        if (data?.session_id) {
            setSessionId(data.session_id);
            return data.session_id;
        }
        throw new Error('Speech session response was incomplete.');
    };

    const interruptAssistantSpeech = () => {
        textToSpeech.stop();
        if (autoRestartTimerRef.current) {
            clearTimeout(autoRestartTimerRef.current);
            autoRestartTimerRef.current = null;
        }
        setStatus('idle');
    };

    const speakAnswer = (answerText) => {
        const trimmed = String(answerText || '').trim();
        if (!trimmed) {
            setStatus('idle');
            return;
        }

        interruptAssistantSpeech();
        setStatus('speaking');

        textToSpeech.speak(trimmed, {
            rate: 0.93,
            pitch: 1,
            onEnd: () => {
                if (!mountedRef.current) return;
                setStatus('idle');
                if (handsFree) {
                    autoRestartTimerRef.current = setTimeout(() => {
                        if (mountedRef.current) {
                            startListening();
                        }
                    }, 450);
                }
            },
            onError: () => {
                if (!mountedRef.current) return;
                setStatus('idle');
            },
        });
    };

    const startListening = () => {
        if (!birthData) {
            setErrorText('Select a birth chart before starting speech chat.');
            return;
        }
        if (!speechChatEnabled) {
            setErrorText('Voice chat is not available for your account right now.');
            return;
        }
        if (!instantChatEnabled) {
            setErrorText('Instant chat is turned off right now. Use typed chat instead.');
            return;
        }
        if (credits < speechChatCost) {
            setErrorText(`You need at least ${speechChatCost} credit${speechChatCost !== 1 ? 's' : ''} for speech chat.`);
            return;
        }

        const SpeechRecognitionClass = getSpeechRecognitionClass();
        if (!SpeechRecognitionClass) {
            setErrorText('Speech recognition is not supported in this browser.');
            return;
        }

        if (autoRestartTimerRef.current) {
            clearTimeout(autoRestartTimerRef.current);
            autoRestartTimerRef.current = null;
        }

        setErrorText('');
        setCurrentTranscript('');
        finalTranscriptRef.current = '';
        liveTranscriptRef.current = '';
        shouldAutoSendSpeechRef.current = true;

        const recognition = new SpeechRecognitionClass();
        recognition.lang = getSpeechRecognitionLang();
        recognition.interimResults = true;
        recognition.continuous = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            if (!mountedRef.current) return;
            setStatus('listening');
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
            finalTranscriptRef.current = finalText.trim() || combined;
            liveTranscriptRef.current = combined;
            setCurrentTranscript(combined);
        };

        recognition.onerror = (event) => {
            recognitionRef.current = null;
            shouldAutoSendSpeechRef.current = false;
            if (!mountedRef.current) return;
            if (event?.error === 'aborted') return;
            if (event?.error === 'no-speech') {
                setErrorText('No speech was detected. Please try again.');
            } else if (event?.error === 'not-allowed' || event?.error === 'service-not-allowed') {
                setErrorText('Microphone permission was blocked for this site.');
            } else {
                setErrorText('Speech recognition failed. Please try again.');
            }
            setStatus('idle');
        };

        recognition.onend = () => {
            recognitionRef.current = null;
            if (!mountedRef.current) return;
            const transcript = String(finalTranscriptRef.current || liveTranscriptRef.current || '').trim();
            const shouldSend = shouldAutoSendSpeechRef.current;
            shouldAutoSendSpeechRef.current = false;
            if (shouldSend && transcript) {
                void (async () => {
                    await speakThinkingHandoff();
                    if (!mountedRef.current) return;
                    sendQuestion(transcript);
                })();
            } else {
                setStatus('idle');
            }
        };

        recognitionRef.current = recognition;
        recognition.start();
    };

    const stopListening = () => {
        shouldAutoSendSpeechRef.current = true;
        recognitionRef.current?.stop();
        setStatus('thinking');
    };

    const sendQuestion = async (questionText) => {
        const question = String(questionText || '').trim();
        if (!question) {
            setStatus('idle');
            return;
        }
        if (!speechChatEnabled || !instantChatEnabled) {
            setErrorText('Speech chat is not available right now.');
            setStatus('idle');
            return;
        }
        if (credits < speechChatCost) {
            setErrorText(`You need at least ${speechChatCost} credit${speechChatCost !== 1 ? 's' : ''} for speech chat.`);
            setStatus('idle');
            return;
        }

        const token = localStorage.getItem('token');
        const activeSessionId = await ensureSession();
        const turnId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        thinkingTurnIdRef.current = turnId;

        setTurns((prev) => [
            ...prev,
            {
                id: turnId,
                question,
                answer: '',
                pending: true,
            },
        ]);
        setFollowUps([]);
        setCurrentTranscript(question);
        setStatus('thinking');

        const requestBody = {
            session_id: activeSessionId,
            question,
            query_context: buildQueryContext(),
            language: 'english',
            response_style: 'concise',
            premium_analysis: false,
            chat_tier: 'instant',
            speech_chat: true,
            native_name: birthData?.name,
            birth_details: toChatBirthDetails(birthData),
            client_request_id: `speech_web_${Date.now()}_${Math.random().toString(36).slice(2)}`,
        };

        try {
            const response = await fetch('/api/chat-v2/ask', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            if (!response.ok) {
                const text = await response.text().catch(() => '');
                throw new Error(`Speech chat failed: ${response.status} ${text}`);
            }

            const result = await response.json();
            const assistantMessageId = result?.message_id;
            if (!assistantMessageId) {
                throw new Error('Speech reply did not start correctly.');
            }

            pollForReply(assistantMessageId, turnId);
        } catch (error) {
            setTurns((prev) =>
                prev.map((turn) =>
                    turn.id === turnId
                        ? { ...turn, answer: 'I could not answer that right now. Please try again.', pending: false }
                        : turn
                )
            );
            setErrorText(error?.message || 'Speech chat failed. Please try again.');
            setStatus('idle');
        }
    };

    const pollForReply = async (assistantMessageId, turnId) => {
        const token = localStorage.getItem('token');
        let pollCount = 0;
        const maxPolls = 120;

        const poll = async () => {
            const res = await fetch(`/api/chat-v2/status/${assistantMessageId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) {
                throw new Error(`Status check failed: ${res.status}`);
            }
            const statusData = await res.json();

            if (statusData.status === 'completed') {
                const answer = String(statusData.content || '').trim() || 'I have the answer, but it came back empty.';
                const nextFollowUps = Array.isArray(statusData.follow_up_questions)
                    ? statusData.follow_up_questions.map((item) => String(item || '').trim()).filter(Boolean).slice(0, 3)
                    : [];

                setTurns((prev) =>
                    prev.map((turn) =>
                        turn.id === turnId
                            ? { ...turn, answer, pending: false, assistantMessageId }
                            : turn
                    )
                );
                setFollowUps(nextFollowUps);
                setCurrentTranscript('');
                fetchBalance();
                speakAnswer(answer);
                return;
            }

            if (statusData.status === 'failed') {
                throw new Error(statusData.error_message || 'Instant speech reply failed.');
            }

            pollCount += 1;
            if (pollCount >= maxPolls) {
                throw new Error('Speech reply is taking too long.');
            }
            setTimeout(() => poll().catch(handlePollError), POLL_INTERVAL_MS);
        };

        const handlePollError = (error) => {
            setTurns((prev) =>
                prev.map((turn) =>
                    turn.id === turnId
                        ? { ...turn, answer: 'The speech reply failed. Please try again.', pending: false }
                        : turn
                )
            );
            setErrorText(error?.message || 'The speech reply failed.');
            setStatus('idle');
        };

        poll().catch(handlePollError);
    };

    const handleMicPress = () => {
        if (status === 'speaking') {
            interruptAssistantSpeech();
            startListening();
            return;
        }
        if (status === 'listening') {
            stopListening();
            return;
        }
        if (status === 'thinking') {
            return;
        }
        startListening();
    };

    const handleFollowUp = (question) => {
        interruptAssistantSpeech();
        setStatus('thinking');
        void (async () => {
            await speakThinkingHandoff();
            if (!mountedRef.current) return;
            sendQuestion(question);
        })();
    };

    startListeningRef.current = startListening;

    useEffect(() => {
        if (greetedRef.current || !birthData?.name || status !== 'idle') return;
        if (!speechChatEnabled || !instantChatEnabled) return;

        const greeting = buildTaraGreeting(displayUserName, birthData.name);
        if (!greeting) return;

        greetedRef.current = true;
        setErrorText('');
        setStatus('speaking');

        textToSpeech.speak(greeting, {
            rate: 0.95,
            pitch: 1,
            onEnd: () => {
                if (!mountedRef.current) return;
                if (handsFreeRef.current) {
                    autoRestartTimerRef.current = setTimeout(() => {
                        if (mountedRef.current) startListeningRef.current();
                    }, 260);
                    return;
                }
                setStatus('idle');
            },
            onError: () => {
                if (mountedRef.current) setStatus('idle');
            },
        });
    }, [birthData?.name, displayUserName, status, speechChatEnabled, instantChatEnabled]);

    const micBusy = status === 'thinking';

    const sessionActive = Boolean(birthData && speechChatEnabled && instantChatEnabled);

    return (
        <div className={`speech-chat-page ${sessionActive ? 'speech-chat-page--session' : ''}`}>
            <div className={`speech-chat-shell ${sessionActive ? 'speech-chat-shell--session' : ''}`}>
                <header className="speech-chat-header">
                    <button type="button" className="speech-chat-back" onClick={() => navigate('/chat?app=1')} aria-label="Back to chat">
                        <svg className="speech-chat-back-icon" viewBox="0 0 24 24" width="22" height="22" aria-hidden>
                            <path fill="currentColor" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
                        </svg>
                    </button>
                    <div className="speech-chat-header__text">
                        <div className="speech-chat-title-row">
                            <h1>Tara</h1>
                            <span className="speech-chat-tara-badge" aria-hidden>✦</span>
                        </div>
                        <p className="speech-chat-header__subtitle">{headerSubtitle}</p>
                    </div>
                    <div className="speech-chat-live-badge" role="status">
                        <span className="speech-chat-live-dot" aria-hidden />
                        <span className="speech-chat-live-badge-text">Live</span>
                    </div>
                </header>

                {!birthData ? (
                    <section className="speech-chat-empty">
                        <h2>Select a chart first</h2>
                        <p>Tara needs a birth chart so she knows which chart to read.</p>
                        <button type="button" onClick={() => navigate('/chat?app=1')}>
                            Choose chart in chat
                        </button>
                    </section>
                ) : !speechChatEnabled || !instantChatEnabled ? (
                    <section className="speech-chat-empty">
                        <h2>Speech chat unavailable</h2>
                        <p>
                            {!speechChatEnabled
                                ? 'Voice features are not enabled for your account right now.'
                                : 'Instant chat is turned off. You can still use typed chat from the main chat screen.'}
                        </p>
                        <button type="button" onClick={() => navigate('/chat?app=1')}>
                            Back to chat
                        </button>
                    </section>
                ) : (
                    <>
                        <div className="speech-chat-body">
                            <div className="speech-chat-scroll" ref={scrollRef}>
                                <div className="speech-chat-conversation">
                                    {turns.length === 0 && !currentTranscript ? (
                                        <div className="speech-chat-empty-card">
                                            <span className="speech-chat-empty-card-icon" aria-hidden>🎙</span>
                                            <h2 className="speech-chat-empty-card-title">Ask by speaking</h2>
                                            <p className="speech-chat-empty-card-body">
                                                Keep questions short and natural. Tara answers aloud and suggests follow-ups.
                                            </p>
                                        </div>
                                    ) : null}

                                    {turns.map((turn) => (
                                        <article key={turn.id} className="speech-turn">
                                            <div className="speech-turn__question">
                                                <span>You asked</span>
                                                <p>{turn.question}</p>
                                            </div>
                                            <div className="speech-turn__answer">
                                                <span>Tara answered</span>
                                                <p>{turn.pending ? 'Tara is reading the chart…' : turn.answer}</p>
                                            </div>
                                        </article>
                                    ))}

                                    {currentTranscript ? (
                                        <div
                                            className={`speech-chat-live-card ${status !== 'idle' ? 'speech-chat-live-card--pulse' : ''}`}
                                        >
                                            <span className="speech-chat-live-card-label">
                                                {status === 'listening' ? 'Heard so far' : 'Current question'}
                                            </span>
                                            <p>{currentTranscript}</p>
                                        </div>
                                    ) : null}
                                </div>
                            </div>

                            {followUps.length > 0 && status === 'idle' ? (
                                <div className="speech-chat-followups">
                                    {followUps.map((item) => (
                                        <button key={item} type="button" className="speech-chat-followup-chip" onClick={() => handleFollowUp(item)}>
                                            {item}
                                        </button>
                                    ))}
                                </div>
                            ) : null}

                            {errorText ? <p className="speech-chat-error speech-chat-error--inline">{errorText}</p> : null}
                        </div>

                        <div className="speech-chat-controls-shell">
                            <div className="speech-chat-wave-backdrop" aria-hidden>
                                <div className="speech-chat-wave-blob speech-chat-wave-blob--1" />
                                <div className="speech-chat-wave-blob speech-chat-wave-blob--2" />
                                <div className="speech-chat-wave-blob speech-chat-wave-blob--3" />
                            </div>
                            <div className="speech-chat-controls">
                                <div className={`speech-chat-voice-stage speech-chat-voice-stage--${status}`}>
                                    <div className="speech-chat-voice-glow" />
                                    <div className="speech-chat-wave-row">
                                        {[0, 1, 2, 3, 4].map((i) => (
                                            <span key={i} className={`speech-chat-wave-bar speech-chat-wave-bar--${i}`} />
                                        ))}
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    className={`speech-chat-hands-free ${handsFree ? 'speech-chat-hands-free--on' : ''}`}
                                    onClick={() => setHandsFree((v) => !v)}
                                >
                                    <span className="speech-chat-hands-free-icon" aria-hidden>{handsFree ? '◉' : '○'}</span>
                                    <span className="speech-chat-hands-free-label">Hands-free follow-up</span>
                                    <span className={`speech-chat-hands-free-state ${handsFree ? 'is-on' : ''}`}>
                                        {handsFree ? 'On' : 'Off'}
                                    </span>
                                </button>

                                <p className="speech-chat-status">{taraStatusLabels[status] || taraStatusLabels.idle}</p>
                                <p className="speech-chat-meta">
                                    Credits: {credits} · Speech chat (Tara): {speechChatCost} credit{speechChatCost !== 1 ? 's' : ''} per turn
                                </p>

                                <div className="speech-chat-mic-outer">
                                    <button
                                        type="button"
                                        className={`speech-chat-mic speech-chat-mic--${status}`}
                                        onClick={handleMicPress}
                                        disabled={micBusy || !isSpeechSupported || credits < speechChatCost}
                                        aria-label={
                                            status === 'speaking'
                                                ? 'Stop speaking'
                                                : status === 'listening'
                                                    ? 'Stop listening'
                                                    : 'Start microphone'
                                        }
                                    >
                                        {micBusy ? (
                                            <span className="speech-chat-mic-spinner" aria-hidden />
                                        ) : (
                                            <>
                                                {status === 'speaking' ? (
                                                    <svg className="speech-chat-mic-icon" viewBox="0 0 24 24" width="36" height="36" aria-hidden>
                                                        <path fill="currentColor" d="M6 6h12v12H6z" />
                                                    </svg>
                                                ) : status === 'listening' ? (
                                                    <svg className="speech-chat-mic-icon" viewBox="0 0 24 24" width="36" height="36" aria-hidden>
                                                        <path fill="currentColor" d="M6 6h12v12H6z" />
                                                    </svg>
                                                ) : (
                                                    <svg className="speech-chat-mic-icon" viewBox="0 0 24 24" width="36" height="36" aria-hidden>
                                                        <path
                                                            fill="currentColor"
                                                            d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"
                                                        />
                                                    </svg>
                                                )}
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default SpeechChatPage;
