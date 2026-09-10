import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { buildQueryContext } from '../../utils/queryContext';
import textToSpeech from '../../utils/textToSpeech';
import { speakThinkingHandoff } from '../../utils/speechThinkingHandoff';
import {
    buildConversationalClosing,
    speechLocaleForLanguage,
    takeSpeakableChunks,
} from '../../utils/speechStreaming';
import './SpeechChatPage.css';

const POLL_INTERVAL_MS = 1400;
const RECOGNITION_MAX_MS = 20000;
const RECOGNITION_SILENCE_MS = 1400;
const RECOGNITION_END_GRACE_MS = 1600;
const BACKEND_RECORDING_MAX_MS = 20000;

function readStoredWebUserName() {
    try {
        const raw = localStorage.getItem('user');
        const u = raw ? JSON.parse(raw) : null;
        return String(u?.name || u?.full_name || '').trim();
    } catch {
        return '';
    }
}

function buildTaraGreeting(displayName, chartFirstName, language = 'english') {
    const chart = String(chartFirstName || 'this').trim();
    const user = String(displayName || '').trim();
    if (String(language).toLowerCase().startsWith('hi')) {
        return user
            ? `नमस्ते ${user}, मैं तारा हूँ। ${chart} की कुंडली मेरे सामने है। आप क्या जानना चाहते हैं?`
            : `नमस्ते, मैं तारा हूँ। ${chart} की कुंडली मेरे सामने है। आप क्या जानना चाहते हैं?`;
    }
    if (user) {
        return `Hello ${user}, I'm Tara, your voice guide on AstroRoshni. Thanks for sharing ${chart}'s chart. How can I help you? Do you have a question for me?`;
    }
    return `Hello, I'm Tara, your voice guide on AstroRoshni. Thanks for sharing ${chart}'s chart. How can I help you? Do you have a question for me?`;
}

const getSpeechRecognitionClass = () => {
    if (typeof window === 'undefined') return null;
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
};

const getSpeechRecognitionLang = () => {
    const stored = String(localStorage.getItem('language') || '').toLowerCase();
    if (stored.startsWith('hi') || stored === 'hindi') return 'hi-IN';
    return navigator.language || 'en-US';
};

const getChatLanguage = () => (
    getSpeechRecognitionLang().toLowerCase().startsWith('hi') ? 'hindi' : 'english'
);

const supportsBackendRecording = () => Boolean(
    typeof window !== 'undefined'
    && window.MediaRecorder
    && window.navigator?.mediaDevices?.getUserMedia
);

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
        speechTtsProvider,
    } = useCredits();

    const [sessionId, setSessionId] = useState(null);
    const [turns, setTurns] = useState([]);
    const [status, setStatus] = useState('idle');
    const [currentTranscript, setCurrentTranscript] = useState('');
    const [errorText, setErrorText] = useState('');
    const [handsFree, setHandsFree] = useState(true);
    const [followUps, setFollowUps] = useState([]);
    const [isSpeechSupported, setIsSpeechSupported] = useState(() => (
        Boolean(getSpeechRecognitionClass()) || supportsBackendRecording()
    ));
    const [speechLanguage, setSpeechLanguage] = useState(() => getChatLanguage());
    const [displayUserName] = useState(() => readStoredWebUserName());

    const recognitionRef = useRef(null);
    const recognitionSilenceTimerRef = useRef(null);
    const recognitionMaxTimerRef = useRef(null);
    const recognitionEndTimerRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const mediaChunksRef = useRef([]);
    const mediaRecordingStartedAtRef = useRef(0);
    const mediaRecordingTimerRef = useRef(null);
    const discardedMediaRecordersRef = useRef(new WeakSet());
    const speechSocketRef = useRef(null);
    const speechSocketConnectRef = useRef(null);
    const speechSocketTurnsRef = useRef(new Map());
    const finalTranscriptRef = useRef('');
    const liveTranscriptRef = useRef('');
    const shouldAutoSendSpeechRef = useRef(false);
    const speechLeadInEpochRef = useRef(0);
    const mountedRef = useRef(true);
    const thinkingTurnIdRef = useRef(null);
    const cancelledTurnIdsRef = useRef(new Set());
    const streamSpeechRef = useRef({
        epoch: 0,
        turnId: null,
        queue: [],
        buffer: '',
        playing: false,
        started: false,
        completed: false,
        language: 'english',
    });
    const autoRestartTimerRef = useRef(null);
    const scrollRef = useRef(null);
    const greetedRef = useRef(false);
    const greetingEpochRef = useRef(0);
    const startListeningRef = useRef(() => {});
    const handsFreeRef = useRef(handsFree);
    const speechLanguageRef = useRef(speechLanguage);

    handsFreeRef.current = handsFree;
    speechLanguageRef.current = speechLanguage;

    useEffect(() => {
        if (!speechTtsProvider) return;
        textToSpeech.setProvider(speechTtsProvider);
        return () => textToSpeech.setProvider('local');
    }, [speechTtsProvider]);

    const taraStatusLabels = useMemo(() => ({
        idle: handsFree
            ? 'Tap the mic and AstroRoshni will keep listening after each answer'
            : 'Tap the mic and ask your question',
        listening: 'Listening… tap again when done',
        thinking: 'Reading the chart…',
        transcribing: 'Understanding your question…',
        speaking: 'Speaking the answer… tap to stop',
    }), [handsFree]);

    useEffect(() => {
        mountedRef.current = true;
        setIsSpeechSupported(Boolean(getSpeechRecognitionClass()) || supportsBackendRecording());
        return () => {
            mountedRef.current = false;
            speechLeadInEpochRef.current += 1;
            if (recognitionRef.current) {
                recognitionRef.current.onstart = null;
                recognitionRef.current.onresult = null;
                recognitionRef.current.onerror = null;
                recognitionRef.current.onend = null;
                recognitionRef.current.abort();
                recognitionRef.current = null;
            }
            [recognitionSilenceTimerRef, recognitionMaxTimerRef, recognitionEndTimerRef].forEach((timerRef) => {
                if (timerRef.current) clearTimeout(timerRef.current);
                timerRef.current = null;
            });
            if (mediaRecordingTimerRef.current) clearTimeout(mediaRecordingTimerRef.current);
            if (mediaRecorderRef.current?.state === 'recording') mediaRecorderRef.current.stop();
            mediaRecorderRef.current = null;
            mediaStreamRef.current?.getTracks?.().forEach((track) => track.stop());
            mediaStreamRef.current = null;
            speechSocketTurnsRef.current.forEach((pending) => pending.reject?.(new Error('Speech socket closed')));
            speechSocketTurnsRef.current.clear();
            speechSocketRef.current?.close();
            speechSocketRef.current = null;
            speechSocketConnectRef.current = null;
            if (autoRestartTimerRef.current) {
                clearTimeout(autoRestartTimerRef.current);
                autoRestartTimerRef.current = null;
            }
            textToSpeech.stop();
        };
    }, []);

    const latestAnswer = turns.length ? turns[turns.length - 1]?.answer : '';

    useEffect(() => {
        if (!currentTranscript && !latestAnswer) return undefined;
        const el = scrollRef.current;
        if (!el) return undefined;
        const timer = setTimeout(() => {
            el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
        }, 60);
        return () => clearTimeout(timer);
    }, [currentTranscript, latestAnswer]);

    const chartLabel = useMemo(() => {
        if (!birthData?.name) return 'your selected chart';
        return `${birthData.name}'s chart`;
    }, [birthData]);

    const headerSubtitle = useMemo(() => {
        if (!birthData?.name) return 'Your live astrology conversation';
        return `Live astrology conversation for ${birthData.name}`;
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

    const scheduleHandsFreeRestart = () => {
        if (!handsFreeRef.current || !mountedRef.current) return;
        if (autoRestartTimerRef.current) clearTimeout(autoRestartTimerRef.current);
        autoRestartTimerRef.current = setTimeout(() => {
            if (mountedRef.current && handsFreeRef.current) startListeningRef.current();
        }, 450);
    };

    const resetStreamSpeech = ({ stopAudio = true } = {}) => {
        const previous = streamSpeechRef.current;
        streamSpeechRef.current = {
            epoch: Number(previous?.epoch || 0) + 1,
            turnId: null,
            queue: [],
            buffer: '',
            playing: false,
            started: false,
            completed: false,
            language: 'english',
        };
        if (stopAudio) textToSpeech.stop();
    };

    const finishStreamSpeech = (turnId, epoch) => {
        const state = streamSpeechRef.current;
        if (state.turnId !== turnId || state.epoch !== epoch || !state.completed) return;
        state.playing = false;
        setStatus('idle');
        scheduleHandsFreeRestart();
    };

    const pumpStreamSpeech = (turnId) => {
        const state = streamSpeechRef.current;
        if (state.turnId !== turnId || state.playing) return;
        const next = state.queue.shift();
        if (!next) {
            if (state.completed) finishStreamSpeech(turnId, state.epoch);
            else setStatus('thinking');
            return;
        }
        const epoch = state.epoch;
        state.playing = true;
        state.started = true;
        setStatus('speaking');
        textToSpeech.speak(next, {
            rate: 0.93,
            pitch: 1,
            lang: speechLocaleForLanguage(state.language),
            onEnd: () => {
                const current = streamSpeechRef.current;
                if (current.turnId !== turnId || current.epoch !== epoch) return;
                current.playing = false;
                pumpStreamSpeech(turnId);
            },
            onError: () => {
                const current = streamSpeechRef.current;
                if (current.turnId !== turnId || current.epoch !== epoch) return;
                current.playing = false;
                current.queue = [];
                if (current.completed) finishStreamSpeech(turnId, epoch);
                else setStatus('thinking');
            },
        });
    };

    const beginStreamSpeech = (turnId, language) => {
        resetStreamSpeech();
        streamSpeechRef.current.turnId = turnId;
        streamSpeechRef.current.language = language;
    };

    const enqueuePlayableText = (turnId, text, { flush = false } = {}) => {
        const state = streamSpeechRef.current;
        if (state.turnId !== turnId) return;
        const extracted = takeSpeakableChunks(`${state.buffer}${String(text || '')}`, { flush });
        state.buffer = extracted.remainder;
        state.queue.push(...extracted.chunks);
        if (state.queue.length) pumpStreamSpeech(turnId);
    };

    const replaceStreamSpeech = (turnId, content, event) => {
        const state = streamSpeechRef.current;
        if (state.turnId !== turnId || !(event?.validated || event?.playable)) return;
        const language = state.language;
        const nextEpoch = state.epoch + 1;
        textToSpeech.stop();
        streamSpeechRef.current = {
            epoch: nextEpoch,
            turnId,
            queue: [],
            buffer: '',
            playing: false,
            started: false,
            completed: false,
            language,
        };
        enqueuePlayableText(turnId, content, { flush: Boolean(event?.validated) });
    };

    const interruptAssistantSpeech = () => {
        speechLeadInEpochRef.current += 1;
        resetStreamSpeech();
        textToSpeech.stop();
        if (autoRestartTimerRef.current) {
            clearTimeout(autoRestartTimerRef.current);
            autoRestartTimerRef.current = null;
        }
        setStatus('idle');
    };

    const ensureSpeechSocket = async () => {
        if (speechSocketRef.current?.readyState === WebSocket.OPEN) return speechSocketRef.current;
        if (speechSocketConnectRef.current) return speechSocketConnectRef.current;

        speechSocketConnectRef.current = new Promise((resolve, reject) => {
            const token = localStorage.getItem('token') || '';
            const wsOrigin = window.location.origin.replace(/^https:/i, 'wss:').replace(/^http:/i, 'ws:');
            const socket = new WebSocket(`${wsOrigin}/api/speech/ws?token=${encodeURIComponent(token)}`);
            let ready = false;
            const timeout = setTimeout(() => {
                if (ready) return;
                speechSocketConnectRef.current = null;
                socket.close();
                reject(new Error('Speech connection timed out.'));
            }, 8000);

            socket.onmessage = (message) => {
                let event;
                try {
                    event = JSON.parse(message.data || '{}');
                } catch {
                    return;
                }
                if (event.type === 'ready') {
                    ready = true;
                    clearTimeout(timeout);
                    speechSocketRef.current = socket;
                    speechSocketConnectRef.current = null;
                    resolve(socket);
                    return;
                }
                if (event.type === 'ping') {
                    socket.send(JSON.stringify({ type: 'pong' }));
                    return;
                }
                const pending = speechSocketTurnsRef.current.get(event.turn_id);
                if (!pending) return;
                if (event.type === 'turn_started' || event.type === 'turn_queued') {
                    pending.accepted = true;
                    return;
                }
                if (event.type === 'answer_chunk') {
                    const delta = String(event.text || '');
                    pending.content = String(event.content || `${pending.content || ''}${delta}`);
                    pending.onChunk?.(delta, { ...event, content: pending.content });
                    return;
                }
                if (event.type === 'answer_replace') {
                    pending.content = String(event.content || '');
                    pending.onReplace?.(pending.content, event);
                    return;
                }
                if (event.type === 'turn_completed') {
                    speechSocketTurnsRef.current.delete(event.turn_id);
                    pending.resolve(event);
                    return;
                }
                if (event.type === 'turn_error') {
                    speechSocketTurnsRef.current.delete(event.turn_id);
                    const error = new Error(event.message || 'Speech turn failed.');
                    error.turnAccepted = true;
                    pending.reject(error);
                    return;
                }
                if (event.type === 'cancelled' || event.type === 'turn_cancelled') {
                    speechSocketTurnsRef.current.delete(event.turn_id);
                    const error = new Error('Speech turn cancelled.');
                    error.turnAccepted = true;
                    error.cancelled = true;
                    pending.reject(error);
                }
            };
            socket.onerror = () => {
                if (!ready) {
                    clearTimeout(timeout);
                    speechSocketConnectRef.current = null;
                    reject(new Error('Speech connection failed.'));
                }
            };
            socket.onclose = () => {
                clearTimeout(timeout);
                speechSocketRef.current = null;
                speechSocketConnectRef.current = null;
                speechSocketTurnsRef.current.forEach((pending) => {
                    const error = new Error('Speech connection closed.');
                    error.turnAccepted = Boolean(pending.accepted);
                    pending.reject?.(error);
                });
                speechSocketTurnsRef.current.clear();
            };
        });
        return speechSocketConnectRef.current;
    };

    const askOverSpeechSocket = async (requestBody, turnId, handlers = {}) => {
        const socket = await ensureSpeechSocket();
        if (cancelledTurnIdsRef.current.has(turnId)) {
            const error = new Error('Speech turn cancelled.');
            error.cancelled = true;
            throw error;
        }
        return new Promise((resolve, reject) => {
            speechSocketTurnsRef.current.set(turnId, {
                resolve,
                reject,
                onChunk: handlers.onChunk,
                onReplace: handlers.onReplace,
                content: '',
                accepted: false,
            });
            try {
                socket.send(JSON.stringify({ ...requestBody, type: 'ask', turn_id: turnId }));
            } catch (error) {
                speechSocketTurnsRef.current.delete(turnId);
                reject(error);
            }
        });
    };

    const speakAnswer = (answerText, language = speechLanguage) => {
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
            lang: speechLocaleForLanguage(language),
            onEnd: () => {
                if (!mountedRef.current) return;
                setStatus('idle');
                scheduleHandsFreeRestart();
            },
            onError: () => {
                if (!mountedRef.current) return;
                setStatus('idle');
                scheduleHandsFreeRestart();
            },
        });
    };

    const submitRecognizedQuestion = async (transcript) => {
        const question = String(transcript || '').trim();
        if (!question || !mountedRef.current) return;
        const turnLanguage = speechLanguageRef.current;
        const leadInEpoch = speechLeadInEpochRef.current + 1;
        speechLeadInEpochRef.current = leadInEpoch;
        setStatus('thinking');
        await speakThinkingHandoff(turnLanguage);
        if (mountedRef.current && speechLeadInEpochRef.current === leadInEpoch) {
            sendQuestion(question, turnLanguage);
        }
    };

    const stopBackendRecording = () => {
        if (mediaRecordingTimerRef.current) {
            clearTimeout(mediaRecordingTimerRef.current);
            mediaRecordingTimerRef.current = null;
        }
        const recorder = mediaRecorderRef.current;
        if (recorder?.state === 'recording') {
            setStatus('transcribing');
            recorder.stop();
        }
    };

    const startBackendRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            if (!mountedRef.current) {
                stream.getTracks().forEach((track) => track.stop());
                return;
            }
            const preferredMime = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/mp4',
            ].find((mime) => window.MediaRecorder.isTypeSupported?.(mime));
            const recorder = preferredMime
                ? new window.MediaRecorder(stream, { mimeType: preferredMime })
                : new window.MediaRecorder(stream);
            mediaStreamRef.current = stream;
            mediaRecorderRef.current = recorder;
            mediaChunksRef.current = [];
            mediaRecordingStartedAtRef.current = Date.now();
            recorder.ondataavailable = (event) => {
                if (event.data?.size) mediaChunksRef.current.push(event.data);
            };
            recorder.onerror = () => {
                if (!mountedRef.current) return;
                setErrorText('Microphone recording failed. Please try again.');
                setStatus('idle');
            };
            recorder.onstop = async () => {
                const chunks = mediaChunksRef.current;
                const discardRecording = discardedMediaRecordersRef.current.has(recorder);
                discardedMediaRecordersRef.current.delete(recorder);
                const durationMs = Math.max(0, Date.now() - mediaRecordingStartedAtRef.current);
                const mimeType = recorder.mimeType || preferredMime || 'audio/webm';
                mediaChunksRef.current = [];
                mediaRecorderRef.current = null;
                mediaRecordingStartedAtRef.current = 0;
                mediaStreamRef.current?.getTracks?.().forEach((track) => track.stop());
                mediaStreamRef.current = null;
                if (discardRecording) return;
                if (!chunks.length || !mountedRef.current) {
                    if (mountedRef.current) {
                        setErrorText('No speech was recorded. Please try again.');
                        setStatus('idle');
                        scheduleHandsFreeRestart();
                    }
                    return;
                }
                try {
                    const extension = mimeType.includes('mp4') ? 'm4a' : 'webm';
                    const form = new FormData();
                    form.append('audio', new Blob(chunks, { type: mimeType }), `speech-question.${extension}`);
                    form.append('language', speechLanguageRef.current);
                    form.append('duration_ms', String(durationMs));
                    const response = await fetch('/api/speech/transcribe', {
                        method: 'POST',
                        headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
                        body: form,
                    });
                    const data = await response.json().catch(() => ({}));
                    if (!response.ok) throw new Error(data.detail || 'Could not understand the recording.');
                    const transcript = String(data.transcript || '').trim();
                    if (!transcript) throw new Error('No speech was detected. Please try again.');
                    setCurrentTranscript(transcript);
                    await submitRecognizedQuestion(transcript);
                } catch (error) {
                    if (!mountedRef.current) return;
                    setErrorText(error?.message || 'Speech transcription failed. Please try again.');
                    setStatus('idle');
                    if (/no speech|understand|empty/i.test(String(error?.message || ''))) {
                        scheduleHandsFreeRestart();
                    }
                }
            };

            recorder.start(250);
            setStatus('listening');
            mediaRecordingTimerRef.current = setTimeout(stopBackendRecording, BACKEND_RECORDING_MAX_MS);
        } catch (error) {
            if (!mountedRef.current) return;
            const permissionDenied = error?.name === 'NotAllowedError' || error?.name === 'SecurityError';
            setErrorText(
                permissionDenied
                    ? 'Microphone permission was blocked for this site.'
                    : 'Could not start microphone recording. Please try again.'
            );
            setStatus('idle');
        }
    };

    const startListening = () => {
        speechLeadInEpochRef.current += 1;
        if (!birthData) {
            setErrorText('Select a birth chart before starting Talk To Tara.');
            return;
        }
        if (!speechChatEnabled) {
            setErrorText('Talk To Tara is not available for your account right now.');
            return;
        }
        if (!instantChatEnabled) {
            setErrorText('Live chat is turned off right now. Use typed chat instead.');
            return;
        }
        if (credits < speechChatCost) {
            setErrorText(`You need at least ${speechChatCost} credit${speechChatCost !== 1 ? 's' : ''} for Talk To Tara.`);
            return;
        }

        const SpeechRecognitionClass = getSpeechRecognitionClass();
        if (!SpeechRecognitionClass && !supportsBackendRecording()) {
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

        if (!SpeechRecognitionClass) {
            startBackendRecording();
            return;
        }

        const recognition = new SpeechRecognitionClass();
        recognition.lang = speechLocaleForLanguage(speechLanguageRef.current);
        recognition.interimResults = true;
        recognition.continuous = false;
        recognition.maxAlternatives = 1;

        let recognitionSettled = false;
        const clearRecognitionTimers = () => {
            [recognitionSilenceTimerRef, recognitionMaxTimerRef, recognitionEndTimerRef].forEach((timerRef) => {
                if (timerRef.current) clearTimeout(timerRef.current);
                timerRef.current = null;
            });
        };
        const finishRecognition = () => {
            if (recognitionSettled || !mountedRef.current) return;
            recognitionSettled = true;
            clearRecognitionTimers();
            recognitionRef.current = null;
            const transcript = String(finalTranscriptRef.current || liveTranscriptRef.current || '').trim();
            const shouldSend = shouldAutoSendSpeechRef.current;
            shouldAutoSendSpeechRef.current = false;
            if (shouldSend && transcript) {
                void submitRecognizedQuestion(transcript);
            } else {
                setStatus('idle');
                if (!transcript) setErrorText('No speech was detected. Please try again.');
                if (!transcript) scheduleHandsFreeRestart();
            }
        };

        recognition.onstart = () => {
            if (!mountedRef.current) return;
            setStatus('listening');
            recognitionMaxTimerRef.current = setTimeout(() => {
                try { recognition.stop(); } catch { finishRecognition(); }
                recognitionEndTimerRef.current = setTimeout(finishRecognition, RECOGNITION_END_GRACE_MS);
            }, RECOGNITION_MAX_MS);
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
            if (recognitionSilenceTimerRef.current) clearTimeout(recognitionSilenceTimerRef.current);
            recognitionSilenceTimerRef.current = setTimeout(() => {
                try { recognition.stop(); } catch { finishRecognition(); }
                recognitionEndTimerRef.current = setTimeout(finishRecognition, RECOGNITION_END_GRACE_MS);
            }, RECOGNITION_SILENCE_MS);
        };

        recognition.onerror = (event) => {
            recognitionRef.current = null;
            if (!mountedRef.current) return;
            if (event?.error === 'aborted' && (finalTranscriptRef.current || liveTranscriptRef.current)) {
                finishRecognition();
                return;
            }
            clearRecognitionTimers();
            recognitionSettled = true;
            shouldAutoSendSpeechRef.current = false;
            if (event?.error === 'no-speech') {
                setErrorText('No speech was detected. Please try again.');
                scheduleHandsFreeRestart();
            } else if (event?.error === 'not-allowed' || event?.error === 'service-not-allowed') {
                setErrorText('Microphone permission was blocked for this site.');
            } else {
                setErrorText('Speech recognition failed. Please try again.');
            }
            setStatus('idle');
        };

        recognition.onend = () => {
            finishRecognition();
        };

        recognitionRef.current = recognition;
        try {
            recognition.start();
        } catch (error) {
            recognitionRef.current = null;
            clearRecognitionTimers();
            setErrorText('Could not start speech recognition. Please try again.');
            setStatus('idle');
        }
    };

    const stopListening = () => {
        if (mediaRecorderRef.current?.state === 'recording') {
            stopBackendRecording();
            return;
        }
        shouldAutoSendSpeechRef.current = true;
        const recognition = recognitionRef.current;
        recognition?.stop();
        if (recognitionEndTimerRef.current) clearTimeout(recognitionEndTimerRef.current);
        recognitionEndTimerRef.current = setTimeout(() => {
            recognition?.onend?.();
        }, RECOGNITION_END_GRACE_MS);
        setStatus('thinking');
    };

    const completeTurn = (turnId, result, language) => {
        if (cancelledTurnIdsRef.current.has(turnId) || !mountedRef.current) return;
        const answer = String(result?.content || '').trim() || 'I have the answer, but it came back empty.';
        const nextFollowUps = Array.isArray(result?.follow_up_questions)
            ? result.follow_up_questions.map((item) => String(item || '').trim()).filter(Boolean).slice(0, 3)
            : [];
        const closingQuestion = buildConversationalClosing(answer, nextFollowUps, language);
        const conversationalAnswer = closingQuestion
            ? `${answer}\n\n${closingQuestion}`
            : answer;
        setTurns((prev) => prev.map((turn) => (
            turn.id === turnId
                ? { ...turn, answer: conversationalAnswer, pending: false, assistantMessageId: result?.message_id }
                : turn
        )));
        setFollowUps(nextFollowUps);
        setCurrentTranscript('');
        fetchBalance();
        if (thinkingTurnIdRef.current === turnId) thinkingTurnIdRef.current = null;

        const streamState = streamSpeechRef.current;
        const hasStreamedSpeech = streamState.turnId === turnId && Boolean(
            streamState.started || streamState.queue.length || streamState.buffer.trim()
        );
        if (hasStreamedSpeech) {
            streamState.completed = true;
            enqueuePlayableText(
                turnId,
                closingQuestion ? `\n\n${closingQuestion}` : '',
                { flush: true }
            );
            if (!streamState.playing && !streamState.queue.length) {
                finishStreamSpeech(turnId, streamState.epoch);
            }
            return;
        }
        resetStreamSpeech();
        speakAnswer(conversationalAnswer, language);
    };

    const sendQuestion = async (questionText, requestedLanguage = speechLanguage) => {
        const question = String(questionText || '').trim();
        if (!question) {
            setStatus('idle');
            return;
        }
        if (!speechChatEnabled || !instantChatEnabled) {
            setErrorText('Talk To Tara is not available right now.');
            setStatus('idle');
            return;
        }
        if (credits < speechChatCost) {
            setErrorText(`You need at least ${speechChatCost} credit${speechChatCost !== 1 ? 's' : ''} for Talk To Tara.`);
            setStatus('idle');
            return;
        }

        const token = localStorage.getItem('token');
        let activeSessionId;
        try {
            activeSessionId = await ensureSession();
        } catch (error) {
            setErrorText(error?.message || 'Could not start a speech session right now.');
            setStatus('idle');
            return;
        }
        const turnId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const turnLanguage = requestedLanguage === 'hindi' ? 'hindi' : 'english';
        thinkingTurnIdRef.current = turnId;
        beginStreamSpeech(turnId, turnLanguage);

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
        setCurrentTranscript('');
        setStatus('thinking');

        const requestBody = {
            session_id: activeSessionId,
            question,
            query_context: buildQueryContext(),
            language: turnLanguage,
            response_style: 'simple',
            premium_analysis: false,
            chat_tier: 'instant',
            speech_chat: true,
            native_name: birthData?.name,
            birth_details: toChatBirthDetails(birthData),
            client_request_id: `speech_web_${Date.now()}_${Math.random().toString(36).slice(2)}`,
        };

        try {
            try {
                const streamedResult = await askOverSpeechSocket(requestBody, turnId, {
                    onChunk: (delta, event) => {
                        setTurns((prev) => prev.map((turn) => (
                            turn.id === turnId ? { ...turn, answer: event?.content || '', pending: true } : turn
                        )));
                        if (event?.validated || event?.playable) enqueuePlayableText(turnId, delta);
                    },
                    onReplace: (content, event) => {
                        setTurns((prev) => prev.map((turn) => (
                            turn.id === turnId ? { ...turn, answer: content, pending: true } : turn
                        )));
                        replaceStreamSpeech(turnId, content, event);
                    },
                });
                completeTurn(turnId, streamedResult, turnLanguage);
                return;
            } catch (socketError) {
                // Only fall back before a WebSocket turn has been accepted.
                if (socketError?.cancelled) return;
                if (socketError?.turnAccepted) throw socketError;
            }
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
                throw new Error(`Talk To Tara failed: ${response.status} ${text}`);
            }

            const result = await response.json();
            const assistantMessageId = result?.message_id;
            if (!assistantMessageId) {
                throw new Error('Speech reply did not start correctly.');
            }

            pollForReply(assistantMessageId, turnId, turnLanguage);
        } catch (error) {
            if (error?.cancelled || cancelledTurnIdsRef.current.has(turnId)) return;
            resetStreamSpeech();
            if (thinkingTurnIdRef.current === turnId) thinkingTurnIdRef.current = null;
            setTurns((prev) =>
                prev.map((turn) =>
                    turn.id === turnId
                        ? { ...turn, answer: 'I could not answer that right now. Please try again.', pending: false }
                        : turn
                )
            );
            setErrorText(error?.message || 'Talk To Tara failed. Please try again.');
            setStatus('idle');
        }
    };

    const pollForReply = async (assistantMessageId, turnId, turnLanguage) => {
        const token = localStorage.getItem('token');
        let pollCount = 0;
        const maxPolls = 120;

        const poll = async () => {
            if (cancelledTurnIdsRef.current.has(turnId) || !mountedRef.current) return;
            const res = await fetch(`/api/chat-v2/status/${assistantMessageId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) {
                throw new Error(`Status check failed: ${res.status}`);
            }
            const statusData = await res.json();

            if (statusData.status === 'completed') {
                completeTurn(turnId, { ...statusData, message_id: assistantMessageId }, turnLanguage);
                return;
            }

            if (statusData.status === 'processing' && statusData.partial_content) {
                setTurns((prev) => prev.map((turn) => (
                    turn.id === turnId
                        ? { ...turn, answer: String(statusData.partial_content), pending: true }
                        : turn
                )));
            }

            if (statusData.status === 'failed') {
                throw new Error(statusData.error_message || 'Live speech reply failed.');
            }

            pollCount += 1;
            if (pollCount >= maxPolls) {
                throw new Error('Speech reply is taking too long.');
            }
            setTimeout(() => poll().catch(handlePollError), POLL_INTERVAL_MS);
        };

        const handlePollError = (error) => {
            if (cancelledTurnIdsRef.current.has(turnId) || !mountedRef.current) return;
            resetStreamSpeech();
            if (thinkingTurnIdRef.current === turnId) thinkingTurnIdRef.current = null;
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

    const cancelActiveTurn = () => {
        const turnId = thinkingTurnIdRef.current;
        if (!turnId) return false;
        cancelledTurnIdsRef.current.add(turnId);
        thinkingTurnIdRef.current = null;
        const pending = speechSocketTurnsRef.current.get(turnId);
        if (pending) {
            speechSocketTurnsRef.current.delete(turnId);
            const error = new Error('Speech turn cancelled.');
            error.turnAccepted = true;
            error.cancelled = true;
            pending.reject?.(error);
        }
        const socket = speechSocketRef.current;
        if (socket?.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'cancel', turn_id: turnId }));
        }
        resetStreamSpeech();
        setTurns((prev) => prev.map((turn) => (
            turn.id === turnId
                ? { ...turn, answer: turn.answer || 'Answer stopped.', pending: false, stopped: true }
                : turn
        )));
        setCurrentTranscript('');
        setStatus('idle');
        return true;
    };

    const handleMicPress = () => {
        if (status === 'speaking') {
            if (!cancelActiveTurn()) interruptAssistantSpeech();
            startListening();
            return;
        }
        if (status === 'listening') {
            stopListening();
            return;
        }
        if (status === 'thinking') {
            if (!cancelActiveTurn()) interruptAssistantSpeech();
            startListening();
            return;
        }
        startListening();
    };

    const handleFollowUp = (question) => {
        interruptAssistantSpeech();
        void submitRecognizedQuestion(question);
    };

    const handleSpeechLanguageChange = (language) => {
        const nextLanguage = language === 'hindi' ? 'hindi' : 'english';
        if (
            nextLanguage === speechLanguageRef.current
            || status === 'thinking'
            || status === 'transcribing'
        ) return;
        const switchingInitialGreeting = status === 'speaking' && turns.length === 0 && !thinkingTurnIdRef.current;
        const switchingActiveMicrophone = status === 'listening';
        speechLanguageRef.current = nextLanguage;
        if (switchingInitialGreeting) {
            greetingEpochRef.current += 1;
            interruptAssistantSpeech();
            greetedRef.current = false;
        }
        setSpeechLanguage(nextLanguage);
        setErrorText('');
        if (switchingActiveMicrophone) {
            shouldAutoSendSpeechRef.current = false;
            finalTranscriptRef.current = '';
            liveTranscriptRef.current = '';
            setCurrentTranscript('');
            [recognitionSilenceTimerRef, recognitionMaxTimerRef, recognitionEndTimerRef].forEach((timerRef) => {
                if (timerRef.current) clearTimeout(timerRef.current);
                timerRef.current = null;
            });
            const recognition = recognitionRef.current;
            recognitionRef.current = null;
            if (recognition) {
                recognition.onresult = null;
                recognition.onerror = null;
                recognition.onend = null;
                try { recognition.abort(); } catch { /* already stopped */ }
            }
            if (mediaRecordingTimerRef.current) {
                clearTimeout(mediaRecordingTimerRef.current);
                mediaRecordingTimerRef.current = null;
            }
            const recorder = mediaRecorderRef.current;
            if (recorder?.state === 'recording') {
                discardedMediaRecordersRef.current.add(recorder);
                try { recorder.stop(); } catch { /* already stopped */ }
            }
            mediaStreamRef.current?.getTracks?.().forEach((track) => track.stop());
            setStatus('idle');
            setTimeout(() => {
                if (mountedRef.current) startListeningRef.current();
            }, 120);
        }
    };

    startListeningRef.current = startListening;

    useEffect(() => {
        if (greetedRef.current || !birthData?.name || status !== 'idle' || !speechTtsProvider) return;
        if (!speechChatEnabled || !instantChatEnabled) return;

        const greetingLanguage = speechLanguage;
        const greeting = buildTaraGreeting(displayUserName, birthData.name, greetingLanguage);
        if (!greeting) return;

        greetedRef.current = true;
        const greetingEpoch = greetingEpochRef.current + 1;
        greetingEpochRef.current = greetingEpoch;
        setErrorText('');
        setStatus('speaking');

        textToSpeech.speak(greeting, {
            rate: 0.95,
            pitch: 1,
            lang: speechLocaleForLanguage(greetingLanguage),
            onEnd: () => {
                if (!mountedRef.current || greetingEpochRef.current !== greetingEpoch) return;
                if (handsFreeRef.current) {
                    autoRestartTimerRef.current = setTimeout(() => {
                        if (mountedRef.current) startListeningRef.current();
                    }, 260);
                    return;
                }
                setStatus('idle');
            },
            onError: () => {
                if (!mountedRef.current || greetingEpochRef.current !== greetingEpoch) return;
                setStatus('idle');
                scheduleHandsFreeRestart();
            },
        });
    }, [birthData?.name, displayUserName, status, speechChatEnabled, instantChatEnabled, speechLanguage, speechTtsProvider]);

    const micWaiting = status === 'thinking' || status === 'transcribing';
    const micDisabled = status === 'transcribing' || !isSpeechSupported || credits < speechChatCost;
    const languageSelectionDisabled = status === 'thinking' || status === 'transcribing';

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
                            <h1>Talk To Tara</h1>
                            <span className="speech-chat-tara-badge" aria-hidden>✦</span>
                        </div>
                        <p className="speech-chat-header__subtitle">{headerSubtitle}</p>
                    </div>
                    <div className="speech-chat-language" role="group" aria-label="Talk To Tara language">
                        <button
                            type="button"
                            className={speechLanguage === 'english' ? 'is-selected' : ''}
                            aria-pressed={speechLanguage === 'english'}
                            disabled={languageSelectionDisabled}
                            onClick={() => handleSpeechLanguageChange('english')}
                        >
                            English
                        </button>
                        <button
                            type="button"
                            className={speechLanguage === 'hindi' ? 'is-selected' : ''}
                            aria-pressed={speechLanguage === 'hindi'}
                            disabled={languageSelectionDisabled}
                            onClick={() => handleSpeechLanguageChange('hindi')}
                        >
                            हिंदी
                        </button>
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
                        <h2>Talk To Tara unavailable</h2>
                        <p>
                            {!speechChatEnabled
                                ? 'Voice features are not enabled for your account right now.'
                                : 'Live chat is turned off. You can still use typed chat from the main chat screen.'}
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
                                            <h2 className="speech-chat-empty-card-title">Talk To Tara</h2>
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
                                            <div
                                                className="speech-turn__answer"
                                                role="status"
                                                aria-live="polite"
                                                aria-atomic="false"
                                            >
                                                <span>{turn.pending ? 'Tara is answering' : turn.stopped ? 'Answer stopped' : 'Tara answered'}</span>
                                                <p>{turn.pending ? (turn.answer || 'Tara is reading the chart…') : turn.answer}</p>
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

                                <p className="speech-chat-status" role="status" aria-live="polite">
                                    {taraStatusLabels[status] || taraStatusLabels.idle}
                                </p>
                                <p className="speech-chat-meta">
                                    Credits: {credits} · Talk To Tara: {speechChatCost} credit{speechChatCost !== 1 ? 's' : ''} per turn
                                </p>

                                <div className="speech-chat-mic-outer">
                                    <button
                                        type="button"
                                        className={`speech-chat-mic speech-chat-mic--${status}`}
                                        onClick={handleMicPress}
                                        disabled={micDisabled}
                                        aria-label={
                                            status === 'speaking'
                                                ? 'Stop speaking'
                                                : status === 'thinking'
                                                    ? 'Stop answer'
                                                : status === 'listening'
                                                    ? 'Stop listening'
                                                    : status === 'transcribing'
                                                        ? 'Transcribing speech'
                                                    : 'Start microphone'
                                        }
                                    >
                                        {micWaiting ? (
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
