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
    const [currentAnswer, setCurrentAnswer] = useState('');
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
        idle: 'Tap the mic to ask Tara',
        listening: 'Listening… speak naturally',
        thinking: 'Tara is reading the chart…',
        speaking: 'Tara is speaking',
    }), []);

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
        const timer = setTimeout(() => {
            scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
        }, 60);
        return () => clearTimeout(timer);
    }, [turns, currentTranscript, currentAnswer, status]);

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
        setCurrentAnswer('');
    };

    const speakAnswer = (answerText) => {
        const trimmed = String(answerText || '').trim();
        if (!trimmed) {
            setStatus('idle');
            return;
        }

        interruptAssistantSpeech();
        setStatus('speaking');
        setCurrentAnswer(trimmed);

        textToSpeech.speak(trimmed, {
            rate: 0.93,
            pitch: 1,
            onEnd: () => {
                if (!mountedRef.current) return;
                setCurrentAnswer('');
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
                setCurrentAnswer('');
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
        setCurrentAnswer('');
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
        setCurrentAnswer('');
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

    return (
        <div className="speech-chat-page">
            <div className="speech-chat-shell">
                <header className="speech-chat-header">
                    <button type="button" className="speech-chat-back" onClick={() => navigate('/chat')}>
                        ← Back to chat
                    </button>
                    <div className="speech-chat-header__text">
                        <p className="speech-chat-kicker">AstroRoshni · Voice</p>
                        <div className="speech-chat-title-row">
                            <h1>Tara</h1>
                            <span className="speech-chat-tara-badge" aria-hidden>✦</span>
                        </div>
                        <p>{headerSubtitle}</p>
                    </div>
                    <label className="speech-chat-toggle">
                        <input
                            type="checkbox"
                            checked={handsFree}
                            onChange={(e) => setHandsFree(e.target.checked)}
                        />
                        <span>Hands-free follow-up</span>
                    </label>
                </header>

                {!birthData ? (
                    <section className="speech-chat-empty">
                        <h2>Select a chart first</h2>
                        <p>Tara needs a birth chart so she knows which chart to read.</p>
                        <button type="button" onClick={() => navigate('/chat')}>
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
                        <button type="button" onClick={() => navigate('/chat')}>
                            Back to chat
                        </button>
                    </section>
                ) : (
                    <>
                        <section className="speech-chat-stage">
                            <div className={`speech-chat-orb speech-chat-orb--${status}`}>
                                <button
                                    type="button"
                                    className="speech-chat-mic"
                                    onClick={handleMicPress}
                                    disabled={
                                        status === 'thinking'
                                        || !isSpeechSupported
                                        || credits < speechChatCost
                                    }
                                >
                                    {status === 'speaking' ? 'Interrupt' : status === 'listening' ? 'Stop' : 'Talk'}
                                </button>
                            </div>
                            <p className="speech-chat-status">{taraStatusLabels[status] || taraStatusLabels.idle}</p>
                            <p className="speech-chat-meta">
                                Credits: {credits} · Speech chat (Tara): {speechChatCost} credit{speechChatCost !== 1 ? 's' : ''} per turn
                            </p>
                            {errorText ? <p className="speech-chat-error">{errorText}</p> : null}
                        </section>

                        <section className="speech-chat-live">
                            <div className="speech-chat-live-card">
                                <span className="speech-chat-live-label">You</span>
                                <p>{currentTranscript || 'Your transcript will appear here while you speak.'}</p>
                            </div>
                            <div className="speech-chat-live-card speech-chat-live-card--answer">
                                <span className="speech-chat-live-label">Tara</span>
                                <p>{currentAnswer || 'Tara will speak her reply here.'}</p>
                            </div>
                        </section>

                        {followUps.length > 0 ? (
                            <section className="speech-chat-followups">
                                {followUps.map((item) => (
                                    <button key={item} type="button" onClick={() => handleFollowUp(item)}>
                                        {item}
                                    </button>
                                ))}
                            </section>
                        ) : null}

                        <section className="speech-chat-turns" ref={scrollRef}>
                            {turns.map((turn) => (
                                <article key={turn.id} className="speech-turn">
                                    <div className="speech-turn__question">
                                        <span>You asked</span>
                                        <p>{turn.question}</p>
                                    </div>
                                    <div className="speech-turn__answer">
                                        <span>Tara said</span>
                                        <p>{turn.pending ? 'Tara is reading the chart…' : turn.answer}</p>
                                    </div>
                                </article>
                            ))}
                        </section>
                    </>
                )}
            </div>
        </div>
    );
};

export default SpeechChatPage;
