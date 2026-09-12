import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { buildQueryContext } from '../../utils/queryContext';
import textToSpeech from '../../utils/textToSpeech';
import {
    buildConversationalClosing,
    speechLocaleForLanguage,
    takeSpeakableChunks,
} from '../../utils/speechStreaming';
import './SpeechChatPage.css';

const POLL_INTERVAL_MS = 1400;
const RECOGNITION_MAX_MS = 30000;
// Allow a natural thinking pause without turning the partial transcript into a
// question. The separate review grace still lets users correct or send now.
const RECOGNITION_SILENCE_MS = 3000;
const RECOGNITION_END_GRACE_MS = 1600;
const BACKEND_RECORDING_MAX_MS = 20000;
const SPEECH_BILLING_MIN_START_MINUTES = 2;
const HANDS_FREE_MAX_NO_SPEECH_RETRIES = 4;
const TRANSCRIPT_SEND_GRACE_MS = 1800;

const WEB_SPEECH_COPY = {
    english: {
        title: 'Talk To Tara', live: 'Live', back: 'Back to chat', language: 'Talk To Tara language',
        idleHandsFree: 'Tap the mic and Tara will keep listening after each answer',
        idle: 'Tap the mic and ask your question', listening: 'Listening… tap again when done',
        thinking: 'Reading the chart…', transcribing: 'Understanding your question…',
        reviewing: 'Check your question — sending shortly', speaking: 'Speaking the answer… tap to stop',
        selectChart: 'Select a chart first', selectChartBody: 'Tara needs a birth chart so she knows which chart to read.',
        chooseChart: 'Choose chart in chat', unavailable: 'Talk To Tara unavailable',
        voiceDisabled: 'Voice features are not enabled for your account right now.',
        liveDisabled: 'Live chat is turned off. You can still use typed chat from the main chat screen.',
        backToChat: 'Back to chat', emptyBody: 'Keep questions short and natural. Tara answers aloud and suggests follow-ups.',
        youAsked: 'You asked', answering: 'Tara is answering', stopped: 'Answer stopped', answered: 'Tara answered',
        reading: 'Tara is reading the chart…', checkQuestion: 'Check your question',
        alternatives: 'Other words the microphone may have heard', cancel: 'Cancel', sendNow: 'Send now',
        heard: 'Heard so far', currentQuestion: 'Current question', handsFree: 'Hands-free follow-up',
        on: 'On', off: 'Off', credits: 'Credits', perMinute: 'credit/min',
        startMic: 'Start microphone', stopListening: 'Stop listening', stopSpeaking: 'Stop speaking',
        stopAnswer: 'Stop answer', transcribingMic: 'Transcribing speech', privacy: 'Voice privacy',
        privacyBody: 'Audio is processed only to transcribe your question and is not kept after successful processing. The question and answer are saved in chat history.',
        clearScreen: 'Clear this screen', deleteHistory: 'Delete saved chat history',
        privacyDetails: 'Privacy and conversation controls',
        deleteConfirm: 'Permanently delete every saved question and answer? Your account, charts and credits will not be deleted.',
        historyDeleted: 'Your saved chat history was deleted.', deleteFailed: 'Could not delete chat history. Please try again.',
        chartFor: 'Live astrology conversation for', genericSubtitle: 'Your live astrology conversation',
        sessionStartFailed: 'Could not start a speech session right now.', sessionIncomplete: 'Speech session response was incomplete.',
        billingStartFailed: 'Could not start Talk To Tara billing.', creditsFinished: 'Talk To Tara paused because your available talk credits finished.',
        chooseChartError: 'Select a birth chart before starting Talk To Tara.', accountUnavailable: 'Talk To Tara is not available for your account right now.',
        browserUnsupported: 'Speech recognition is not supported in this browser.', insufficientCredits: 'You need at least {credits} credits to start a Talk To Tara session.',
        replyFailed: 'The speech reply failed. Please try again.', replyTimeout: 'The speech reply is taking too long.',
        emptyReply: 'I have the answer, but it came back empty.', answerUnavailable: 'I could not answer that right now. Please try again.',
        noSpeech: 'No speech was detected. Please try again.', micBlocked: 'Microphone permission was blocked for this site.',
        speechFailed: 'Speech recognition failed. Please try again.', recordingFailed: 'Microphone recording failed. Please try again.',
        transcriptionFailed: 'Speech transcription failed. Please try again.', inactivity: 'Talk To Tara paused after prolonged silence. Tap the mic when you are ready.',
        endTalk: 'End Talk', sessionPaused: 'Talk To Tara is paused. Tap the mic when you are ready.',
        sessionReceipt: '{time} · {credits} credits used',
    },
    hindi: {
        title: 'तारा से बात करें', live: 'लाइव', back: 'चैट पर वापस जाएँ', language: 'बातचीत की भाषा',
        idleHandsFree: 'माइक दबाएँ। हर उत्तर के बाद तारा फिर से सुनती रहेगी', idle: 'माइक दबाकर अपना सवाल पूछें',
        listening: 'सुन रही हूँ… पूरा होने पर फिर दबाएँ', thinking: 'कुंडली देख रही हूँ…',
        transcribing: 'आपका सवाल समझ रही हूँ…', reviewing: 'अपना सवाल जाँचें — यह कुछ ही क्षण में भेजा जाएगा',
        speaking: 'उत्तर बोल रही हूँ… रोकने के लिए दबाएँ', selectChart: 'पहले कुंडली चुनें',
        selectChartBody: 'उत्तर देने के लिए तारा को एक जन्म कुंडली चाहिए।', chooseChart: 'चैट में कुंडली चुनें',
        unavailable: 'तारा से बात करें अभी उपलब्ध नहीं है', voiceDisabled: 'आपके खाते के लिए आवाज़ की सुविधा अभी चालू नहीं है।',
        liveDisabled: 'लाइव चैट अभी बंद है। मुख्य चैट स्क्रीन पर लिखकर सवाल पूछ सकते हैं।', backToChat: 'चैट पर वापस जाएँ',
        emptyBody: 'सवाल छोटा और स्वाभाविक रखें। तारा बोलकर उत्तर देगी और आगे के सवाल सुझाएगी।',
        youAsked: 'आपने पूछा', answering: 'तारा उत्तर दे रही है', stopped: 'उत्तर रोक दिया गया', answered: 'तारा ने उत्तर दिया',
        reading: 'तारा कुंडली देख रही है…', checkQuestion: 'अपना सवाल जाँचें', alternatives: 'माइक्रोफ़ोन ने शायद ये शब्द भी सुने हों',
        cancel: 'रद्द करें', sendNow: 'अभी भेजें', heard: 'अब तक सुना', currentQuestion: 'मौजूदा सवाल',
        handsFree: 'हैंड्स-फ़्री फॉलो-अप', on: 'चालू', off: 'बंद', credits: 'क्रेडिट', perMinute: 'क्रेडिट/मिनट',
        startMic: 'माइक्रोफ़ोन चालू करें', stopListening: 'सुनना रोकें', stopSpeaking: 'बोलना रोकें', stopAnswer: 'उत्तर रोकें',
        transcribingMic: 'आवाज़ समझी जा रही है', privacy: 'आवाज़ की गोपनीयता',
        privacyBody: 'आपका सवाल लिखने के लिए ऑडियो संसाधित होता है और सफल प्रक्रिया के बाद रखा नहीं जाता। सवाल और उत्तर चैट इतिहास में सहेजे जाते हैं।',
        clearScreen: 'यह स्क्रीन साफ़ करें', deleteHistory: 'सहेजा गया चैट इतिहास मिटाएँ',
        privacyDetails: 'गोपनीयता और बातचीत के विकल्प',
        deleteConfirm: 'क्या सभी सहेजे गए सवाल और जवाब हमेशा के लिए मिटा दें? आपका खाता, कुंडलियाँ और क्रेडिट नहीं मिटेंगे।',
        historyDeleted: 'आपका सहेजा गया चैट इतिहास मिटा दिया गया है।', deleteFailed: 'चैट इतिहास नहीं मिट सका। कृपया फिर कोशिश करें।',
        chartFor: 'लाइव ज्योतिष बातचीत:', genericSubtitle: 'आपकी लाइव ज्योतिष बातचीत',
        sessionStartFailed: 'अभी आवाज़ की बातचीत शुरू नहीं हो सकी।', sessionIncomplete: 'आवाज़ की बातचीत शुरू करने का उत्तर अधूरा था।',
        billingStartFailed: 'तारा से बात करें का बिलिंग सत्र शुरू नहीं हो सका।', creditsFinished: 'उपलब्ध क्रेडिट समाप्त होने के कारण तारा से बातचीत रोक दी गई है।',
        chooseChartError: 'तारा से बात शुरू करने से पहले जन्म कुंडली चुनें।', accountUnavailable: 'तारा से बात करें अभी आपके खाते के लिए उपलब्ध नहीं है।',
        browserUnsupported: 'यह ब्राउज़र आवाज़ पहचानने का समर्थन नहीं करता।', insufficientCredits: 'तारा से बातचीत शुरू करने के लिए कम से कम {credits} क्रेडिट चाहिए।',
        replyFailed: 'आवाज़ में उत्तर देने में समस्या हुई। कृपया फिर कोशिश करें।', replyTimeout: 'आवाज़ का उत्तर आने में बहुत समय लग रहा है।',
        emptyReply: 'उत्तर तैयार हुआ, लेकिन उसका टेक्स्ट नहीं मिला।', answerUnavailable: 'अभी उत्तर नहीं दिया जा सका। कृपया फिर कोशिश करें।',
        noSpeech: 'आवाज़ साफ़ समझ नहीं आई। कृपया फिर कोशिश करें।', micBlocked: 'इस साइट के लिए माइक्रोफ़ोन की अनुमति बंद है।',
        speechFailed: 'आवाज़ पहचानने में समस्या हुई। कृपया फिर कोशिश करें।', recordingFailed: 'माइक्रोफ़ोन रिकॉर्डिंग में समस्या हुई। कृपया फिर कोशिश करें।',
        transcriptionFailed: 'आवाज़ को लिखने में समस्या हुई। कृपया फिर कोशिश करें।', inactivity: 'लंबे समय तक आवाज़ न मिलने के कारण बातचीत रोक दी गई है। तैयार होने पर माइक दबाएँ।',
        endTalk: 'बातचीत समाप्त करें', sessionPaused: 'तारा से बातचीत रोक दी गई है। तैयार होने पर माइक दबाएँ।',
        sessionReceipt: '{time} · {credits} क्रेडिट उपयोग हुए',
    },
};

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

const formatSpeechDuration = (seconds) => {
    const total = Math.max(0, Number(seconds || 0));
    const minutes = Math.floor(total / 60);
    return `${minutes}:${String(total % 60).padStart(2, '0')}`;
};

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
        speechChatPerMinuteCost,
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
    const [billingSession, setBillingSession] = useState(null);
    const [billingReceipt, setBillingReceipt] = useState('');
    const [callElapsedSeconds, setCallElapsedSeconds] = useState(0);
    const [pendingTranscript, setPendingTranscript] = useState('');
    const [transcriptAlternatives, setTranscriptAlternatives] = useState([]);
    const [micLevel, setMicLevel] = useState(0);
    const [processingBridgeCaption, setProcessingBridgeCaption] = useState('');
    const pendingSpokenFollowUpRef = useRef(null);

    const recognitionRef = useRef(null);
    const recognitionSilenceTimerRef = useRef(null);
    const recognitionMaxTimerRef = useRef(null);
    const recognitionEndTimerRef = useRef(null);
    const transcriptSendTimerRef = useRef(null);
    const recognitionAlternativesRef = useRef([]);
    const mediaRecorderRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const mediaChunksRef = useRef([]);
    const mediaRecordingStartedAtRef = useRef(0);
    const mediaRecordingTimerRef = useRef(null);
    const audioMeterContextRef = useRef(null);
    const audioMeterTimerRef = useRef(null);
    const audioMeterStreamRef = useRef(null);
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
    const billingSessionRef = useRef(null);
    const billingStartPromiseRef = useRef(null);
    const billingTimerRef = useRef(null);
    const billingStartMsRef = useRef(0);
    const lastBillingHeartbeatSecondRef = useRef(0);
    const billingHeartbeatInFlightRef = useRef(false);
    const endSpeechBillingSessionRef = useRef(() => Promise.resolve());
    const endBillingAfterCurrentTurnRef = useRef(false);
    const pageHiddenRef = useRef(typeof document !== 'undefined' && document.visibilityState === 'hidden');
    const statusRef = useRef(status);
    const consecutiveNoSpeechRef = useRef(0);
    const micRequestedAtRef = useRef(0);
    const firstPartialReportedRef = useRef(false);
    const questionSubmittedAtRef = useRef(0);
    const firstAnswerTextReportedRef = useRef(false);
    const firstSpokenAudioReportedRef = useRef(false);
    const processingBridgeEpochRef = useRef(0);
    const processingBridgeSpeakingRef = useRef(false);
    const processingBridgeGracefulStopRef = useRef(false);
    const processingBridgeResolveRef = useRef(null);
    const processingBridgeAfterCurrentRef = useRef(null);
    const recentProcessingBridgeLinesRef = useRef([]);
    const spokenAnswerTextRef = useRef(new Map());
    const answerRevealFallbackTimersRef = useRef(new Map());
    const answerFallbackRevealedRef = useRef(new Set());

    handsFreeRef.current = handsFree;
    speechLanguageRef.current = speechLanguage;
    statusRef.current = status;
    const copy = (key) => (
        WEB_SPEECH_COPY[speechLanguage]?.[key]
        || WEB_SPEECH_COPY.english[key]
        || key
    );
    const emitSpeechMetric = (event, options = {}) => {
        const token = localStorage.getItem('token') || '';
        void fetch('/api/speech/telemetry', {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                event,
                platform: 'web',
                session_id: billingSessionRef.current?.session_id || null,
                turn_id: thinkingTurnIdRef.current || null,
                value_ms: options.valueMs == null ? null : Math.max(0, Math.round(options.valueMs)),
                success: options.success == null ? null : Boolean(options.success),
                metadata: {
                    language: speechLanguageRef.current,
                    hands_free: Boolean(handsFreeRef.current),
                    ...(options.metadata || {}),
                },
            }),
        }).catch(() => {});
    };

    useEffect(() => {
        if (!speechTtsProvider) return;
        textToSpeech.setProvider(speechTtsProvider);
        return () => textToSpeech.setProvider('local');
    }, [speechTtsProvider]);

    useEffect(() => {
        const handleVisibilityChange = () => {
            const hidden = document.visibilityState !== 'visible';
            pageHiddenRef.current = hidden;
            if (!hidden && statusRef.current === 'speaking') {
                textToSpeech.resume();
                emitSpeechMetric('playback_resumed', { success: true, metadata: { app_state: 'visible' } });
                return;
            }
            if (!hidden) return;

            setHandsFree(false);
            handsFreeRef.current = false;
            if (autoRestartTimerRef.current) {
                clearTimeout(autoRestartTimerRef.current);
                autoRestartTimerRef.current = null;
            }
            if (['speaking', 'thinking', 'transcribing'].includes(statusRef.current)) {
                endBillingAfterCurrentTurnRef.current = true;
                return;
            }
            shouldAutoSendSpeechRef.current = false;
            if (recognitionRef.current) {
                recognitionRef.current.onresult = null;
                recognitionRef.current.onend = null;
                recognitionRef.current.onerror = null;
                recognitionRef.current.abort?.();
            }
            recognitionRef.current = null;
            if (mediaRecorderRef.current?.state === 'recording') {
                discardedMediaRecordersRef.current.add(mediaRecorderRef.current);
                mediaRecorderRef.current.stop();
            }
            mediaStreamRef.current?.getTracks?.().forEach((track) => track.stop());
            mediaStreamRef.current = null;
            setStatus('idle');
            setErrorText(copy('sessionPaused'));
            void endSpeechBillingSessionRef.current('page_hidden');
        };
        document.addEventListener('visibilitychange', handleVisibilityChange);
        window.addEventListener('pageshow', handleVisibilityChange);
        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            window.removeEventListener('pageshow', handleVisibilityChange);
        };
    }, [speechLanguage]);

    const taraStatusLabels = useMemo(() => ({
        idle: handsFree
            ? copy('idleHandsFree')
            : copy('idle'),
        listening: copy('listening'),
        thinking: copy('thinking'),
        transcribing: copy('transcribing'),
        reviewing: copy('reviewing'),
        speaking: copy('speaking'),
    }), [handsFree, speechLanguage]);

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
            if (transcriptSendTimerRef.current) clearTimeout(transcriptSendTimerRef.current);
            if (mediaRecordingTimerRef.current) clearTimeout(mediaRecordingTimerRef.current);
            if (mediaRecorderRef.current?.state === 'recording') mediaRecorderRef.current.stop();
            mediaRecorderRef.current = null;
            mediaStreamRef.current?.getTracks?.().forEach((track) => track.stop());
            mediaStreamRef.current = null;
            if (audioMeterTimerRef.current) clearInterval(audioMeterTimerRef.current);
            audioMeterStreamRef.current?.getTracks?.().forEach((track) => track.stop());
            audioMeterContextRef.current?.close?.().catch?.(() => {});
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
            answerRevealFallbackTimersRef.current.forEach((timer) => clearTimeout(timer));
            answerRevealFallbackTimersRef.current.clear();
            if (billingTimerRef.current) clearInterval(billingTimerRef.current);
            endSpeechBillingSessionRef.current('screen_unmount', { keepalive: true });
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
        if (!birthData?.name) return copy('genericSubtitle');
        return `${copy('chartFor')} ${birthData.name}`;
    }, [birthData?.name, speechLanguage]);

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
            throw new Error(copy('sessionStartFailed'));
        }

        const data = await response.json();
        if (data?.session_id) {
            setSessionId(data.session_id);
            return data.session_id;
        }
        throw new Error(copy('sessionIncomplete'));
    };

    const endSpeechBillingSession = async (reason = 'ended', { keepalive = false } = {}) => {
        const current = billingSessionRef.current;
        if (!current?.session_id) return null;
        billingSessionRef.current = null;
        setBillingSession(null);
        if (billingTimerRef.current) {
            clearInterval(billingTimerRef.current);
            billingTimerRef.current = null;
        }
        try {
            const token = localStorage.getItem('token') || '';
            const response = await fetch(`/api/credits/speech-session/${encodeURIComponent(current.session_id)}/end`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ reason }),
                keepalive,
            });
            const result = keepalive ? null : await response.json().catch(() => null);
            if (!keepalive) {
                fetchBalance();
                if (result && mountedRef.current) {
                    const time = formatSpeechDuration(result.elapsed_seconds || callElapsedSeconds);
                    setBillingReceipt(copy('sessionReceipt')
                        .replace('{time}', time)
                        .replace('{credits}', String(result.charged_credits ?? 0)));
                }
            }
            return result;
        } catch {
            // The server heartbeat lease reconciles an interrupted close.
            return null;
        }
    };
    endSpeechBillingSessionRef.current = endSpeechBillingSession;

    const ensureSpeechBillingSession = async () => {
        if (billingSessionRef.current?.session_id) return true;
        if (billingStartPromiseRef.current) return billingStartPromiseRef.current;
        billingStartPromiseRef.current = (async () => {
            try {
                const token = localStorage.getItem('token') || '';
                const response = await fetch('/api/credits/speech-session/start', {
                    method: 'POST',
                    headers: { Authorization: `Bearer ${token}` },
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    const detail = data?.detail || {};
                    throw new Error(detail.message || copy('billingStartFailed'));
                }
                const elapsed = Math.max(0, Number(data.elapsed_seconds || 0));
                billingSessionRef.current = data;
                billingStartMsRef.current = Date.now() - elapsed * 1000;
                lastBillingHeartbeatSecondRef.current = elapsed;
                setBillingSession(data);
                setBillingReceipt('');
                setCallElapsedSeconds(elapsed);
                if (billingTimerRef.current) clearInterval(billingTimerRef.current);
                billingTimerRef.current = setInterval(() => {
                    const active = billingSessionRef.current;
                    if (!active?.session_id) return;
                    const currentElapsed = Math.max(0, Math.floor((Date.now() - billingStartMsRef.current) / 1000));
                    setCallElapsedSeconds(currentElapsed);
                    const heartbeatEvery = Math.max(5, Number(active.heartbeat_interval_seconds || 10));
                    if (
                        currentElapsed - lastBillingHeartbeatSecondRef.current >= heartbeatEvery
                        && !billingHeartbeatInFlightRef.current
                    ) {
                        lastBillingHeartbeatSecondRef.current = currentElapsed;
                        billingHeartbeatInFlightRef.current = true;
                        fetch(`/api/credits/speech-session/${encodeURIComponent(active.session_id)}/heartbeat`, {
                            method: 'POST',
                            headers: { Authorization: `Bearer ${token}` },
                        }).then(async (heartbeatResponse) => {
                            const heartbeat = await heartbeatResponse.json().catch(() => ({}));
                            if (!heartbeatResponse.ok || heartbeat.status !== 'active' || heartbeat.remaining_seconds === 0) {
                                await endSpeechBillingSession('credits_finished');
                                setErrorText(copy('creditsFinished'));
                                setStatus('idle');
                            } else if (Number.isFinite(Number(heartbeat.elapsed_seconds))) {
                                const confirmedElapsed = Math.max(0, Number(heartbeat.elapsed_seconds));
                                billingStartMsRef.current = Date.now() - confirmedElapsed * 1000;
                                lastBillingHeartbeatSecondRef.current = confirmedElapsed;
                                setCallElapsedSeconds(confirmedElapsed);
                            }
                        }).catch(() => {}).finally(() => {
                            billingHeartbeatInFlightRef.current = false;
                        });
                    }
                }, 1000);
                return true;
            } catch (error) {
                setErrorText(error?.message || copy('billingStartFailed'));
                return false;
            } finally {
                billingStartPromiseRef.current = null;
            }
        })();
        return billingStartPromiseRef.current;
    };

    const scheduleHandsFreeRestart = ({ noSpeech = false } = {}) => {
        if (!handsFreeRef.current || !mountedRef.current || pageHiddenRef.current || endBillingAfterCurrentTurnRef.current) return;
        consecutiveNoSpeechRef.current = noSpeech ? consecutiveNoSpeechRef.current + 1 : 0;
        if (noSpeech && consecutiveNoSpeechRef.current >= HANDS_FREE_MAX_NO_SPEECH_RETRIES) {
            setHandsFree(false);
            handsFreeRef.current = false;
            setStatus('idle');
            setErrorText(copy('inactivity'));
            void endSpeechBillingSessionRef.current('inactivity_timeout');
            return;
        }
        if (autoRestartTimerRef.current) clearTimeout(autoRestartTimerRef.current);
        autoRestartTimerRef.current = setTimeout(() => {
            if (mountedRef.current && handsFreeRef.current && !pageHiddenRef.current && !endBillingAfterCurrentTurnRef.current) {
                startListeningRef.current();
                emitSpeechMetric('hands_free_restart', {
                    success: true,
                    metadata: { reason: noSpeech ? 'no_speech' : 'after_answer' },
                });
            }
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
        setTurns((prev) => prev.map((turn) => (
            turn.id === turnId
                ? { ...turn, answer: turn.fullAnswer || turn.answer, voiceState: 'done', pending: false }
                : turn
        )));
        setStatus('idle');
        if (endBillingAfterCurrentTurnRef.current || pageHiddenRef.current) {
            endBillingAfterCurrentTurnRef.current = false;
            setHandsFree(false);
            handsFreeRef.current = false;
            setErrorText(copy('sessionPaused'));
            void endSpeechBillingSessionRef.current('background_after_answer');
            return;
        }
        scheduleHandsFreeRestart();
    };

    const revealAnswerText = (turnId, text, { voiceState } = {}) => {
        const visible = String(text || '');
        spokenAnswerTextRef.current.set(turnId, visible);
        setTurns((prev) => prev.map((turn) => (
            turn.id === turnId
                ? { ...turn, answer: visible, ...(voiceState ? { voiceState } : {}) }
                : turn
        )));
    };

    const progressivePrefix = (text, ratio, minimumWords = 1) => {
        const words = String(text || '').trim().split(/\s+/).filter(Boolean);
        if (!words.length) return '';
        const count = Math.min(words.length, Math.max(minimumWords, Math.ceil(words.length * Math.max(0, Math.min(1, ratio)))));
        return words.slice(0, count).join(' ');
    };

    const clearAnswerRevealFallback = (turnId) => {
        const timer = answerRevealFallbackTimersRef.current.get(turnId);
        if (timer) clearTimeout(timer);
        answerRevealFallbackTimersRef.current.delete(turnId);
    };

    const scheduleAnswerRevealFallback = (turnId, fullAnswer) => {
        clearAnswerRevealFallback(turnId);
        const timer = setTimeout(() => {
            answerRevealFallbackTimersRef.current.delete(turnId);
            answerFallbackRevealedRef.current.add(turnId);
            revealAnswerText(turnId, fullAnswer, { voiceState: 'fallback' });
        }, 8000);
        answerRevealFallbackTimersRef.current.set(turnId, timer);
    };

    const pumpStreamSpeech = (turnId) => {
        const state = streamSpeechRef.current;
        if (state.turnId !== turnId || state.playing || processingBridgeSpeakingRef.current) return;
        const next = state.queue.shift();
        if (!next) {
            if (state.completed) finishStreamSpeech(turnId, state.epoch);
            else setStatus('thinking');
            return;
        }
        const epoch = state.epoch;
        const baseText = spokenAnswerTextRef.current.get(turnId) || '';
        const joinVisible = (part) => [baseText.trim(), String(part || '').trim()].filter(Boolean).join(' ');
        state.playing = true;
        state.started = true;
        scheduleAnswerRevealFallback(turnId, joinVisible(next));
        const speechStarted = textToSpeech.speak(next, {
            rate: 0.93,
            pitch: 1,
            lang: speechLocaleForLanguage(state.language),
            onStart: () => {
                setStatus('speaking');
                clearAnswerRevealFallback(turnId);
                if (!answerFallbackRevealedRef.current.has(turnId)) {
                    revealAnswerText(turnId, joinVisible(progressivePrefix(next, 0, 1)), { voiceState: 'speaking' });
                }
                if (!firstSpokenAudioReportedRef.current && questionSubmittedAtRef.current) {
                    firstSpokenAudioReportedRef.current = true;
                    emitSpeechMetric('first_spoken_audio_ms', {
                        valueMs: Date.now() - questionSubmittedAtRef.current,
                        success: true,
                        metadata: { provider: speechTtsProvider || 'unknown' },
                    });
                }
            },
            onProgress: (positionMs, durationMs) => {
                if (durationMs > 0 && !answerFallbackRevealedRef.current.has(turnId)) revealAnswerText(turnId, joinVisible(progressivePrefix(next, positionMs / durationMs)), { voiceState: 'speaking' });
            },
            onBoundary: (charIndex) => {
                if (!answerFallbackRevealedRef.current.has(turnId)) revealAnswerText(turnId, joinVisible(String(next).slice(0, Math.max(1, charIndex))), { voiceState: 'speaking' });
            },
            onEnd: () => {
                const current = streamSpeechRef.current;
                if (current.turnId !== turnId || current.epoch !== epoch) return;
                revealAnswerText(turnId, joinVisible(next), { voiceState: 'speaking' });
                current.playing = false;
                pumpStreamSpeech(turnId);
            },
            onError: () => {
                const current = streamSpeechRef.current;
                if (current.turnId !== turnId || current.epoch !== epoch) return;
                current.playing = false;
                current.queue = [];
                setTurns((prev) => prev.map((turn) => (
                    turn.id === turnId ? { ...turn, answer: turn.fullAnswer || turn.answer, voiceState: 'fallback', pending: false } : turn
                )));
                if (current.completed) finishStreamSpeech(turnId, epoch);
                else setStatus('thinking');
            },
        });
        if (!speechStarted) {
            clearAnswerRevealFallback(turnId);
            revealAnswerText(turnId, joinVisible(next), { voiceState: 'fallback' });
            state.playing = false;
            pumpStreamSpeech(turnId);
        }
    };

    const beginStreamSpeech = (turnId, language) => {
        resetStreamSpeech();
        streamSpeechRef.current.turnId = turnId;
        streamSpeechRef.current.language = language;
        spokenAnswerTextRef.current.set(turnId, '');
        answerFallbackRevealedRef.current.delete(turnId);
    };

    const enqueuePlayableText = (turnId, text, { flush = false } = {}) => {
        const state = streamSpeechRef.current;
        if (state.turnId !== turnId) return;
        const extracted = takeSpeakableChunks(`${state.buffer}${String(text || '')}`, { flush });
        state.buffer = extracted.remainder;
        state.queue.push(...extracted.chunks);
        extracted.chunks.forEach((chunk) => {
            textToSpeech.prefetch(chunk, { lang: speechLocaleForLanguage(state.language) }).catch(() => null);
        });
        if (state.queue.length) {
            cancelProcessingBridge('answer_audio_queued', { interruptCurrent: false });
            pumpStreamSpeech(turnId);
        }
    };

    const replaceStreamSpeech = (turnId, content, event) => {
        const state = streamSpeechRef.current;
        if (state.turnId !== turnId || !(event?.validated || event?.playable)) return;
        const language = state.language;
        const nextEpoch = state.epoch + 1;
        if (state.playing) textToSpeech.stop();
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

    const interruptAssistantSpeech = ({ revealFinal = true } = {}) => {
        speechLeadInEpochRef.current += 1;
        cancelProcessingBridge('user_interrupt', { interruptCurrent: true });
        resetStreamSpeech();
        textToSpeech.stop();
        if (autoRestartTimerRef.current) {
            clearTimeout(autoRestartTimerRef.current);
            autoRestartTimerRef.current = null;
        }
        if (revealFinal) {
            setTurns((prev) => prev.map((turn) => (
                ['waiting', 'speaking'].includes(turn.voiceState) && turn.fullAnswer
                    ? { ...turn, answer: turn.fullAnswer, voiceState: 'stopped', pending: false, stopped: true }
                    : turn
            )));
        }
        setStatus('idle');
    };

    const cancelProcessingBridge = (reason = 'cancelled', { interruptCurrent = true } = {}) => {
        if (!interruptCurrent && processingBridgeGracefulStopRef.current) return;
        processingBridgeEpochRef.current += 1;
        if (!interruptCurrent && processingBridgeSpeakingRef.current) {
            processingBridgeGracefulStopRef.current = true;
            emitSpeechMetric('processing_bridge_cancelled', {
                success: true,
                metadata: { cancel_reason: `${reason}_after_current_line` },
            });
            return;
        }
        setProcessingBridgeCaption('');
        processingBridgeGracefulStopRef.current = false;
        processingBridgeAfterCurrentRef.current = null;
        const resolve = processingBridgeResolveRef.current;
        processingBridgeResolveRef.current = null;
        resolve?.(false);
        if (processingBridgeSpeakingRef.current) {
            processingBridgeSpeakingRef.current = false;
            processingBridgeGracefulStopRef.current = false;
            textToSpeech.stop();
            emitSpeechMetric('processing_bridge_cancelled', {
                success: true,
                metadata: { cancel_reason: reason },
            });
        }
    };

    const speakProcessingBridgeLine = (line, language, epoch) => new Promise((resolve) => {
        if (!mountedRef.current || processingBridgeEpochRef.current !== epoch) {
            resolve(false);
            return;
        }
        processingBridgeResolveRef.current = resolve;
        processingBridgeSpeakingRef.current = true;
        setProcessingBridgeCaption(line);
        const finish = (spoken) => {
            if (processingBridgeResolveRef.current === resolve) processingBridgeResolveRef.current = null;
            processingBridgeSpeakingRef.current = false;
            setProcessingBridgeCaption('');
            resolve(spoken);
            const afterCurrent = processingBridgeAfterCurrentRef.current;
            processingBridgeAfterCurrentRef.current = null;
            if (afterCurrent) afterCurrent();
            else {
                const queuedTurnId = streamSpeechRef.current.turnId;
                if (queuedTurnId) pumpStreamSpeech(queuedTurnId);
            }
        };
        const started = textToSpeech.speak(line, {
            rate: 0.95,
            pitch: 1,
            lang: speechLocaleForLanguage(language),
            onEnd: () => finish(true),
            onError: () => finish(false),
        });
        if (!started) finish(false);
    });

    const startProcessingBridge = async (question, turnId, language, submittedAt) => {
        const epoch = processingBridgeEpochRef.current + 1;
        processingBridgeEpochRef.current = epoch;
        processingBridgeGracefulStopRef.current = false;
        const generatedAt = Date.now();
        try {
            const token = localStorage.getItem('token') || '';
            const response = await fetch('/api/speech/guide-lines', {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scene: 'processing',
                    language,
                    question,
                    hands_free: handsFreeRef.current,
                    recent_lines: recentProcessingBridgeLinesRef.current.slice(-20),
                    answer_style: 'simple',
                }),
            });
            if (!response.ok || processingBridgeEpochRef.current !== epoch || thinkingTurnIdRef.current !== turnId) return;
            const data = await response.json();
            const lines = Array.isArray(data?.lines) ? data.lines.filter(Boolean).slice(0, Number(data.max_lines) || 3) : [];
            emitSpeechMetric('processing_bridge_generated_ms', {
                valueMs: Date.now() - generatedAt,
                success: Boolean(lines.length),
                metadata: { line_count: lines.length },
            });
            if (!lines.length) return;
            const waitMs = Math.max(0, (Number(data.initial_delay_ms) || 0) - (Date.now() - submittedAt));
            if (waitMs) await new Promise((resolve) => setTimeout(resolve, waitMs));
            for (const line of lines) {
                if (!mountedRef.current || processingBridgeEpochRef.current !== epoch || thinkingTurnIdRef.current !== turnId) break;
                const spoken = await speakProcessingBridgeLine(String(line), language, epoch);
                if (spoken) recentProcessingBridgeLinesRef.current = [...recentProcessingBridgeLinesRef.current, String(line)].slice(-20);
                if (!spoken || processingBridgeEpochRef.current !== epoch) break;
                emitSpeechMetric('processing_bridge_spoken', { success: true });
                const gapMs = Math.max(0, Number(data.line_gap_ms) || 0);
                if (gapMs) await new Promise((resolve) => setTimeout(resolve, gapMs));
            }
            if (processingBridgeEpochRef.current === epoch) setProcessingBridgeCaption('');
        } catch (_) {
            if (processingBridgeEpochRef.current === epoch) setProcessingBridgeCaption('');
        }
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
                    if (event.message_id) pending.messageId = event.message_id;
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
                    error.messageId = pending.messageId;
                    error.clientRequestId = pending.clientRequestId;
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
                    error.messageId = pending.messageId;
                    error.clientRequestId = pending.clientRequestId;
                    error.retryableConnectionFailure = true;
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
                clientRequestId: requestBody.client_request_id,
            });
            try {
                socket.send(JSON.stringify({ ...requestBody, type: 'ask', turn_id: turnId }));
            } catch (error) {
                speechSocketTurnsRef.current.delete(turnId);
                reject(error);
            }
        });
    };

    const speakAnswer = (answerText, language = speechLanguage, turnId = thinkingTurnIdRef.current) => {
        const trimmed = String(answerText || '').trim();
        if (!trimmed) {
            setStatus('idle');
            return;
        }

        interruptAssistantSpeech({ revealFinal: false });
        setStatus('thinking');
        const activeTurnId = turnId;
        spokenAnswerTextRef.current.set(activeTurnId, '');
        scheduleAnswerRevealFallback(activeTurnId, trimmed);

        const speechStarted = textToSpeech.speak(trimmed, {
            rate: 0.93,
            pitch: 1,
            lang: speechLocaleForLanguage(language),
            onStart: () => {
                setStatus('speaking');
                clearAnswerRevealFallback(activeTurnId);
                if (!answerFallbackRevealedRef.current.has(activeTurnId)) revealAnswerText(activeTurnId, progressivePrefix(trimmed, 0, 1), { voiceState: 'speaking' });
                if (!firstSpokenAudioReportedRef.current && questionSubmittedAtRef.current) {
                    firstSpokenAudioReportedRef.current = true;
                    emitSpeechMetric('first_spoken_audio_ms', {
                        valueMs: Date.now() - questionSubmittedAtRef.current,
                        success: true,
                        metadata: { provider: speechTtsProvider || 'unknown' },
                    });
                }
            },
            onProgress: (positionMs, durationMs) => {
                if (durationMs > 0 && !answerFallbackRevealedRef.current.has(activeTurnId)) revealAnswerText(activeTurnId, progressivePrefix(trimmed, positionMs / durationMs), { voiceState: 'speaking' });
            },
            onBoundary: (charIndex) => {
                if (!answerFallbackRevealedRef.current.has(activeTurnId)) revealAnswerText(activeTurnId, trimmed.slice(0, Math.max(1, charIndex)), { voiceState: 'speaking' });
            },
            onEnd: () => {
                if (!mountedRef.current) return;
                clearAnswerRevealFallback(activeTurnId);
                revealAnswerText(activeTurnId, trimmed, { voiceState: 'done' });
                setStatus('idle');
                if (endBillingAfterCurrentTurnRef.current || pageHiddenRef.current) {
                    endBillingAfterCurrentTurnRef.current = false;
                    setHandsFree(false);
                    handsFreeRef.current = false;
                    setErrorText(copy('sessionPaused'));
                    void endSpeechBillingSessionRef.current('background_after_answer');
                    return;
                }
                scheduleHandsFreeRestart();
            },
            onError: () => {
                if (!mountedRef.current) return;
                clearAnswerRevealFallback(activeTurnId);
                revealAnswerText(activeTurnId, trimmed, { voiceState: 'fallback' });
                setStatus('idle');
                if (endBillingAfterCurrentTurnRef.current || pageHiddenRef.current) {
                    endBillingAfterCurrentTurnRef.current = false;
                    setHandsFree(false);
                    handsFreeRef.current = false;
                    setErrorText(copy('sessionPaused'));
                    void endSpeechBillingSessionRef.current('background_after_answer');
                    return;
                }
                scheduleHandsFreeRestart();
            },
        });
        if (!speechStarted) {
            clearAnswerRevealFallback(activeTurnId);
            revealAnswerText(activeTurnId, trimmed, { voiceState: 'fallback' });
            setStatus('idle');
            if (endBillingAfterCurrentTurnRef.current || pageHiddenRef.current) {
                endBillingAfterCurrentTurnRef.current = false;
                setHandsFree(false);
                handsFreeRef.current = false;
                setErrorText(copy('sessionPaused'));
                void endSpeechBillingSessionRef.current('background_after_answer');
            }
        }
    };

    const sendRecognizedQuestion = async (transcript) => {
        const question = String(transcript || '').trim();
        if (!question || !mountedRef.current) return;
        consecutiveNoSpeechRef.current = 0;
        const turnLanguage = speechLanguageRef.current;
        setStatus('thinking');
        sendQuestion(question, turnLanguage);
    };

    const clearTranscriptSendTimer = () => {
        if (!transcriptSendTimerRef.current) return;
        clearTimeout(transcriptSendTimerRef.current);
        transcriptSendTimerRef.current = null;
    };

    const sendPendingTranscript = (overrideText = null) => {
        const question = String(overrideText ?? pendingTranscript).trim();
        clearTranscriptSendTimer();
        setPendingTranscript('');
        setTranscriptAlternatives([]);
        if (!question) {
            setCurrentTranscript('');
            setStatus('idle');
            return;
        }
        setCurrentTranscript(question);
        void sendRecognizedQuestion(question);
    };

    const submitRecognizedQuestion = (transcript, alternatives = []) => {
        const question = String(transcript || '').trim();
        if (!question || !mountedRef.current) return;
        clearTranscriptSendTimer();
        const distinctAlternatives = Array.from(new Set(
            (Array.isArray(alternatives) ? alternatives : [])
                .map((item) => String(item?.transcript || item || '').trim())
                .filter((item) => item && item.toLowerCase() !== question.toLowerCase())
        )).slice(0, 2);
        setPendingTranscript(question);
        setTranscriptAlternatives(distinctAlternatives);
        setCurrentTranscript(question);
        setStatus('reviewing');
        transcriptSendTimerRef.current = setTimeout(() => {
            transcriptSendTimerRef.current = null;
            sendPendingTranscript(question);
        }, TRANSCRIPT_SEND_GRACE_MS);
    };

    const cancelPendingTranscript = () => {
        clearTranscriptSendTimer();
        setPendingTranscript('');
        setTranscriptAlternatives([]);
        setCurrentTranscript('');
        setStatus('idle');
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

    const stopAudioMeter = () => {
        if (audioMeterTimerRef.current) clearInterval(audioMeterTimerRef.current);
        audioMeterTimerRef.current = null;
        audioMeterContextRef.current?.close?.().catch?.(() => {});
        audioMeterContextRef.current = null;
        audioMeterStreamRef.current?.getTracks?.().forEach((track) => track.stop());
        audioMeterStreamRef.current = null;
        setMicLevel(0);
    };

    const startAudioMeter = (stream, { ownsStream = false } = {}) => {
        stopAudioMeter();
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextClass) return;
        try {
            const context = new AudioContextClass();
            const analyser = context.createAnalyser();
            analyser.fftSize = 256;
            context.createMediaStreamSource(stream).connect(analyser);
            const samples = new Uint8Array(analyser.fftSize);
            audioMeterContextRef.current = context;
            audioMeterStreamRef.current = ownsStream ? stream : null;
            audioMeterTimerRef.current = setInterval(() => {
                analyser.getByteTimeDomainData(samples);
                const meanSquare = samples.reduce((sum, value) => {
                    const normalized = (value - 128) / 128;
                    return sum + normalized * normalized;
                }, 0) / samples.length;
                setMicLevel(Math.min(1, Math.max(0.08, Math.sqrt(meanSquare) * 4.5)));
            }, 90);
        } catch {
            stopAudioMeter();
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
            startAudioMeter(stream);
            mediaRecorderRef.current = recorder;
            mediaChunksRef.current = [];
            mediaRecordingStartedAtRef.current = Date.now();
            recorder.ondataavailable = (event) => {
                if (event.data?.size) mediaChunksRef.current.push(event.data);
            };
            recorder.onerror = () => {
                if (!mountedRef.current) return;
                setErrorText(copy('recordingFailed'));
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
                stopAudioMeter();
                if (discardRecording) return;
                if (!chunks.length || !mountedRef.current) {
                    if (mountedRef.current) {
                        setErrorText(copy('noSpeech'));
                        setStatus('idle');
                        scheduleHandsFreeRestart({ noSpeech: true });
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
                    if (!transcript) throw new Error(copy('noSpeech'));
                    setCurrentTranscript(transcript);
                    await submitRecognizedQuestion(transcript);
                } catch (error) {
                    if (!mountedRef.current) return;
                    setErrorText(error?.message || copy('transcriptionFailed'));
                    setStatus('idle');
                    if (/no speech|understand|empty/i.test(String(error?.message || ''))) {
                        scheduleHandsFreeRestart({ noSpeech: true });
                    }
                }
            };

            recorder.start(250);
            setStatus('listening');
            navigator.vibrate?.(20);
            emitSpeechMetric('microphone_ready_ms', {
                valueMs: micRequestedAtRef.current ? Date.now() - micRequestedAtRef.current : null,
                success: true,
                metadata: { recognizer: 'backend' },
            });
            mediaRecordingTimerRef.current = setTimeout(stopBackendRecording, BACKEND_RECORDING_MAX_MS);
        } catch (error) {
            if (!mountedRef.current) return;
            const permissionDenied = error?.name === 'NotAllowedError' || error?.name === 'SecurityError';
            setErrorText(
                permissionDenied
                    ? copy('micBlocked')
                    : copy('recordingFailed')
            );
            setStatus('idle');
        }
    };

    const startListening = () => {
        speechLeadInEpochRef.current += 1;
        if (!birthData) {
            setErrorText(copy('chooseChartError'));
            return;
        }
        if (!speechChatEnabled) {
            setErrorText(copy('accountUnavailable'));
            return;
        }
        if (!instantChatEnabled) {
            setErrorText(copy('liveDisabled'));
            return;
        }
        const requiredStartCredits = speechChatPerMinuteCost * SPEECH_BILLING_MIN_START_MINUTES;
        if (!billingSessionRef.current?.session_id && credits < requiredStartCredits) {
            setErrorText(copy('insufficientCredits').replace('{credits}', requiredStartCredits));
            return;
        }

        const SpeechRecognitionClass = getSpeechRecognitionClass();
        if (!SpeechRecognitionClass && !supportsBackendRecording()) {
            setErrorText(copy('browserUnsupported'));
            return;
        }
        if (!billingSessionRef.current?.session_id) {
            if (billingStartPromiseRef.current) return;
            void ensureSpeechBillingSession().then((started) => {
                if (started && mountedRef.current) startListeningRef.current();
            });
            return;
        }

        if (autoRestartTimerRef.current) {
            clearTimeout(autoRestartTimerRef.current);
            autoRestartTimerRef.current = null;
        }

        setErrorText('');
        setCurrentTranscript('');
        micRequestedAtRef.current = Date.now();
        firstPartialReportedRef.current = false;
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
        // Chrome otherwise finalizes a short phrase at its own aggressive
        // endpoint and closes the session before our silence grace can apply.
        recognition.continuous = true;
        recognition.maxAlternatives = 3;
        recognitionAlternativesRef.current = [];

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
            stopAudioMeter();
            recognitionRef.current = null;
            const transcript = String(finalTranscriptRef.current || liveTranscriptRef.current || '').trim();
            const shouldSend = shouldAutoSendSpeechRef.current;
            shouldAutoSendSpeechRef.current = false;
            if (shouldSend && transcript) {
                void submitRecognizedQuestion(transcript, recognitionAlternativesRef.current);
            } else {
                setStatus('idle');
                if (!transcript) setErrorText(copy('noSpeech'));
                if (!transcript) scheduleHandsFreeRestart({ noSpeech: true });
            }
        };

        recognition.onstart = () => {
            if (!mountedRef.current) return;
            setStatus('listening');
            navigator.vibrate?.(20);
            emitSpeechMetric('microphone_ready_ms', {
                valueMs: micRequestedAtRef.current ? Date.now() - micRequestedAtRef.current : null,
                success: true,
                metadata: { recognizer: 'browser' },
            });
            recognitionMaxTimerRef.current = setTimeout(() => {
                try { recognition.stop(); } catch { finishRecognition(); }
                recognitionEndTimerRef.current = setTimeout(finishRecognition, RECOGNITION_END_GRACE_MS);
            }, RECOGNITION_MAX_MS);
        };

        recognition.onresult = (event) => {
            let finalText = '';
            let interimText = '';
            for (let i = 0; i < event.results.length; i += 1) {
                const result = event.results[i];
                const fragment = result?.[0]?.transcript || '';
                if (result.isFinal) {
                    finalText += fragment;
                    recognitionAlternativesRef.current = Array.from(result || [])
                        .map((candidate) => ({
                            transcript: String(candidate?.transcript || '').trim(),
                            confidence: Number(candidate?.confidence || 0),
                        }))
                        .filter((candidate) => candidate.transcript);
                } else {
                    interimText += fragment;
                }
            }
            const combined = `${finalText} ${interimText}`.trim();
            if (combined && !firstPartialReportedRef.current) {
                firstPartialReportedRef.current = true;
                emitSpeechMetric('first_partial_transcript_ms', {
                    valueMs: micRequestedAtRef.current ? Date.now() - micRequestedAtRef.current : null,
                    success: true,
                    metadata: { recognizer: 'browser' },
                });
            }
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
            stopAudioMeter();
            recognitionSettled = true;
            shouldAutoSendSpeechRef.current = false;
            if (event?.error === 'no-speech') {
                setErrorText(copy('noSpeech'));
                scheduleHandsFreeRestart({ noSpeech: true });
            } else if (event?.error === 'not-allowed' || event?.error === 'service-not-allowed') {
                setErrorText(copy('micBlocked'));
            } else {
                setErrorText(copy('speechFailed'));
            }
            setStatus('idle');
        };

        recognition.onend = () => {
            finishRecognition();
        };

        recognitionRef.current = recognition;
        navigator.mediaDevices?.getUserMedia?.({ audio: true }).then((meterStream) => {
            if (!mountedRef.current || recognitionRef.current !== recognition) {
                meterStream.getTracks().forEach((track) => track.stop());
                return;
            }
            startAudioMeter(meterStream, { ownsStream: true });
        }).catch(() => {});
        try {
            recognition.start();
        } catch (error) {
            recognitionRef.current = null;
            clearRecognitionTimers();
            setErrorText(copy('speechFailed'));
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

    const getConversationalClosing = async (answer, nextFollowUps, language) => {
        const localClosing = buildConversationalClosing(answer, nextFollowUps, language);
        if (!nextFollowUps.length || !localClosing) return localClosing;
        try {
            const token = localStorage.getItem('token') || '';
            const response = await fetch('/api/speech/guide-lines', {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scene: 'closing',
                    language,
                    follow_ups: nextFollowUps,
                    hands_free: handsFreeRef.current,
                    answer_style: 'simple',
                }),
            });
            if (response.ok) {
                const data = await response.json();
                const line = String(data?.lines?.[0] || '').trim();
                if (line) return line;
            }
        } catch (_) {
            // Fall through to the local non-impersonating invitation.
        }
        return localClosing;
    };

    const completeTurn = async (turnId, result, language) => {
        if (cancelledTurnIdsRef.current.has(turnId) || !mountedRef.current) return;
        cancelProcessingBridge('answer_complete', { interruptCurrent: false });
        const answer = String(result?.content || '').trim() || copy('emptyReply');
        const nextFollowUps = Array.isArray(result?.follow_up_questions)
            ? result.follow_up_questions.map((item) => String(item || '').trim()).filter(Boolean).slice(0, 3)
            : [];
        const closingQuestion = await getConversationalClosing(answer, nextFollowUps, language);
        if (cancelledTurnIdsRef.current.has(turnId) || !mountedRef.current) return;
        const conversationalAnswer = closingQuestion
            ? `${answer}\n\n${closingQuestion}`
            : answer;
        setTurns((prev) => prev.map((turn) => (
            turn.id === turnId
                ? {
                    ...turn,
                    fullAnswer: conversationalAnswer,
                    answer: turn.answer || '',
                    pending: true,
                    voiceState: turn.voiceState || 'waiting',
                    assistantMessageId: result?.message_id,
                }
                : turn
        )));
        setFollowUps(nextFollowUps);
        pendingSpokenFollowUpRef.current = nextFollowUps[0]
            ? { question: nextFollowUps[0], invitation: closingQuestion }
            : null;
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
        if (endBillingAfterCurrentTurnRef.current && pageHiddenRef.current) {
            endBillingAfterCurrentTurnRef.current = false;
            cancelProcessingBridge('background_answer_complete', { interruptCurrent: true });
            revealAnswerText(turnId, conversationalAnswer, { voiceState: 'done' });
            setTurns((prev) => prev.map((turn) => (
                turn.id === turnId ? { ...turn, pending: false } : turn
            )));
            setHandsFree(false);
            handsFreeRef.current = false;
            setStatus('idle');
            setErrorText(copy('sessionPaused'));
            void endSpeechBillingSessionRef.current('background_after_answer');
            return;
        }
        textToSpeech.prefetch(conversationalAnswer, {
            lang: speechLocaleForLanguage(language),
        }).catch(() => null);
        resetStreamSpeech({ stopAudio: !processingBridgeSpeakingRef.current });
        const startAnswerSpeech = () => {
            if (mountedRef.current && !cancelledTurnIdsRef.current.has(turnId)) {
                speakAnswer(conversationalAnswer, language, turnId);
            }
        };
        if (processingBridgeSpeakingRef.current) processingBridgeAfterCurrentRef.current = startAnswerSpeech;
        else startAnswerSpeech();
    };

    const sendQuestion = async (questionText, requestedLanguage = speechLanguage) => {
        const question = String(questionText || '').trim();
        if (!question) {
            setStatus('idle');
            return;
        }
        if (!speechChatEnabled || !instantChatEnabled) {
            setErrorText(copy('accountUnavailable'));
            setStatus('idle');
            return;
        }
        const requiredStartCredits = speechChatPerMinuteCost * SPEECH_BILLING_MIN_START_MINUTES;
        if (!billingSessionRef.current?.session_id && credits < requiredStartCredits) {
            setErrorText(copy('insufficientCredits').replace('{credits}', requiredStartCredits));
            setStatus('idle');
            return;
        }
        if (!billingSessionRef.current?.session_id) {
            const billingStarted = await ensureSpeechBillingSession();
            if (!billingStarted) {
                setStatus('idle');
                return;
            }
        }

        const token = localStorage.getItem('token');
        let activeSessionId;
        try {
            activeSessionId = await ensureSession();
        } catch (error) {
            setErrorText(error?.message || copy('sessionStartFailed'));
            setStatus('idle');
            return;
        }
        const turnId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const turnLanguage = requestedLanguage === 'hindi' ? 'hindi' : 'english';
        thinkingTurnIdRef.current = turnId;
        questionSubmittedAtRef.current = Date.now();
        firstAnswerTextReportedRef.current = false;
        firstSpokenAudioReportedRef.current = false;
        emitSpeechMetric('question_submitted', { success: true });
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

        const pendingFollowUp = pendingSpokenFollowUpRef.current;
        pendingSpokenFollowUpRef.current = null;
        const requestBody = {
            session_id: activeSessionId,
            question,
            query_context: buildQueryContext(
                pendingFollowUp?.question
                    ? {
                        speech_follow_up_offer: pendingFollowUp.question,
                        speech_follow_up_invitation: pendingFollowUp.invitation || '',
                    }
                    : {}
            ),
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
                const streamedPromise = askOverSpeechSocket(requestBody, turnId, {
                    onChunk: (delta, event) => {
                        if (!firstAnswerTextReportedRef.current && (event?.content || delta)) {
                            firstAnswerTextReportedRef.current = true;
                            emitSpeechMetric('first_answer_text_ms', {
                                valueMs: Date.now() - questionSubmittedAtRef.current,
                                success: true,
                                metadata: { transport: 'websocket' },
                            });
                        }
                        setTurns((prev) => prev.map((turn) => (
                            turn.id === turnId ? { ...turn, preparedAnswer: event?.content || '', pending: true } : turn
                        )));
                        if (event?.validated || event?.playable) enqueuePlayableText(turnId, delta);
                    },
                    onReplace: (content, event) => {
                        if (!firstAnswerTextReportedRef.current && content) {
                            firstAnswerTextReportedRef.current = true;
                            emitSpeechMetric('first_answer_text_ms', {
                                valueMs: Date.now() - questionSubmittedAtRef.current,
                                success: true,
                                metadata: { transport: 'websocket_replace' },
                            });
                        }
                        setTurns((prev) => prev.map((turn) => (
                            turn.id === turnId ? { ...turn, preparedAnswer: content, pending: true } : turn
                        )));
                        replaceStreamSpeech(turnId, content, event);
                    },
                });
                void startProcessingBridge(question, turnId, turnLanguage, questionSubmittedAtRef.current);
                const streamedResult = await streamedPromise;
                await completeTurn(turnId, streamedResult, turnLanguage);
                return;
            } catch (socketError) {
                // Only fall back before a WebSocket turn has been accepted.
                if (socketError?.cancelled) return;
                if (socketError?.turnAccepted && socketError?.messageId) {
                    pollForReply(socketError.messageId, turnId, turnLanguage);
                    return;
                }
                if (socketError?.turnAccepted && !socketError?.retryableConnectionFailure) throw socketError;
                // Re-submit the identical idempotency key over HTTP when the
                // socket closed before it delivered a message id. The backend
                // returns the existing turn if it was already created.
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
                throw new Error(copy('replyFailed'));
            }

            pollForReply(assistantMessageId, turnId, turnLanguage);
        } catch (error) {
            if (error?.cancelled || cancelledTurnIdsRef.current.has(turnId)) return;
            cancelProcessingBridge('answer_error');
            resetStreamSpeech();
            if (thinkingTurnIdRef.current === turnId) thinkingTurnIdRef.current = null;
            setTurns((prev) =>
                prev.map((turn) =>
                    turn.id === turnId
                        ? { ...turn, answer: copy('answerUnavailable'), pending: false }
                        : turn
                )
            );
            setErrorText(error?.message || copy('replyFailed'));
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
                if (!firstAnswerTextReportedRef.current && statusData.content) {
                    firstAnswerTextReportedRef.current = true;
                    emitSpeechMetric('first_answer_text_ms', {
                        valueMs: Date.now() - questionSubmittedAtRef.current,
                        success: true,
                        metadata: { transport: 'poll_completed' },
                    });
                }
                await completeTurn(turnId, { ...statusData, message_id: assistantMessageId }, turnLanguage);
                return;
            }

            if (statusData.status === 'processing' && statusData.partial_content) {
                if (!firstAnswerTextReportedRef.current) {
                    firstAnswerTextReportedRef.current = true;
                    emitSpeechMetric('first_answer_text_ms', {
                        valueMs: Date.now() - questionSubmittedAtRef.current,
                        success: true,
                        metadata: { transport: 'poll_partial' },
                    });
                }
                setTurns((prev) => prev.map((turn) => (
                    turn.id === turnId
                        ? { ...turn, preparedAnswer: String(statusData.partial_content), pending: true }
                        : turn
                )));
            }

            if (statusData.status === 'failed') {
                throw new Error(statusData.error_message || copy('replyFailed'));
            }

            pollCount += 1;
            if (pollCount >= maxPolls) {
                throw new Error(copy('replyTimeout'));
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
                        ? { ...turn, answer: copy('replyFailed'), pending: false }
                        : turn
                )
            );
            setErrorText(error?.message || copy('replyFailed'));
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
        if (status === 'reviewing') {
            cancelPendingTranscript();
            startListening();
            return;
        }
        if (status === 'thinking') {
            if (!cancelActiveTurn()) interruptAssistantSpeech();
            startListening();
            return;
        }
        startListening();
    };

    const handleEndTalk = async () => {
        endBillingAfterCurrentTurnRef.current = false;
        setHandsFree(false);
        handsFreeRef.current = false;
        shouldAutoSendSpeechRef.current = false;
        clearTranscriptSendTimer();
        if (autoRestartTimerRef.current) {
            clearTimeout(autoRestartTimerRef.current);
            autoRestartTimerRef.current = null;
        }
        if (recognitionRef.current) {
            recognitionRef.current.onresult = null;
            recognitionRef.current.onend = null;
            recognitionRef.current.onerror = null;
            recognitionRef.current.abort?.();
            recognitionRef.current = null;
        }
        if (mediaRecorderRef.current?.state === 'recording') {
            discardedMediaRecordersRef.current.add(mediaRecorderRef.current);
            mediaRecorderRef.current.stop();
        }
        mediaStreamRef.current?.getTracks?.().forEach((track) => track.stop());
        mediaStreamRef.current = null;
        stopAudioMeter();
        if (!cancelActiveTurn()) interruptAssistantSpeech();
        setCurrentTranscript('');
        setPendingTranscript('');
        setStatus('idle');
        setErrorText(copy('sessionPaused'));
        await endSpeechBillingSession('user_ended');
    };

    const handleFollowUp = (question) => {
        interruptAssistantSpeech();
        void sendRecognizedQuestion(question);
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
            stopAudioMeter();
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
    const requiredStartCredits = speechChatPerMinuteCost * SPEECH_BILLING_MIN_START_MINUTES;
    const micDisabled = status === 'transcribing'
        || !isSpeechSupported
        || (!billingSession && credits < requiredStartCredits);
    const languageSelectionDisabled = status === 'thinking' || status === 'transcribing';

    const sessionActive = Boolean(birthData && speechChatEnabled && instantChatEnabled);

    const clearCurrentConversation = () => {
        clearTranscriptSendTimer();
        interruptAssistantSpeech();
        setPendingTranscript('');
        setTranscriptAlternatives([]);
        setCurrentTranscript('');
        setFollowUps([]);
        setTurns([]);
        spokenAnswerTextRef.current.clear();
        answerFallbackRevealedRef.current.clear();
        answerRevealFallbackTimersRef.current.forEach((timer) => clearTimeout(timer));
        answerRevealFallbackTimersRef.current.clear();
        setErrorText('');
        setStatus('idle');
    };

    const deleteSavedChatHistory = async () => {
        if (!window.confirm(copy('deleteConfirm'))) return;
        clearTranscriptSendTimer();
        cancelActiveTurn();
        interruptAssistantSpeech();
        await endSpeechBillingSession('history_deleted');
        try {
            const token = localStorage.getItem('token') || '';
            const response = await fetch('/api/chat-v2/history', {
                method: 'DELETE',
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!response.ok) throw new Error(copy('deleteFailed'));
            setSessionId(null);
            clearCurrentConversation();
            setErrorText(copy('historyDeleted'));
        } catch (error) {
            setErrorText(error?.message || copy('deleteFailed'));
        }
    };

    return (
        <div className={`speech-chat-page ${sessionActive ? 'speech-chat-page--session' : ''}`}>
            <div className={`speech-chat-shell ${sessionActive ? 'speech-chat-shell--session' : ''}`}>
                <header className="speech-chat-header">
                    <button type="button" className="speech-chat-back" onClick={() => navigate('/chat?app=1')} aria-label={copy('back')}>
                        <svg className="speech-chat-back-icon" viewBox="0 0 24 24" width="22" height="22" aria-hidden>
                            <path fill="currentColor" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
                        </svg>
                    </button>
                    <div className="speech-chat-header__text">
                        <div className="speech-chat-title-row">
                            <h1>{copy('title')}</h1>
                            <span className="speech-chat-tara-badge" aria-hidden>✦</span>
                        </div>
                        <p className="speech-chat-header__subtitle">{headerSubtitle}</p>
                    </div>
                    <div className="speech-chat-language" role="group" aria-label={copy('language')}>
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
                        <span className="speech-chat-live-badge-text">{copy('live')}</span>
                    </div>
                </header>

                {!birthData ? (
                    <section className="speech-chat-empty">
                        <h2>{copy('selectChart')}</h2>
                        <p>{copy('selectChartBody')}</p>
                        <button type="button" onClick={() => navigate('/chat?app=1')}>
                            {copy('chooseChart')}
                        </button>
                    </section>
                ) : !speechChatEnabled || !instantChatEnabled ? (
                    <section className="speech-chat-empty">
                        <h2>{copy('unavailable')}</h2>
                        <p>
                            {!speechChatEnabled
                                ? copy('voiceDisabled')
                                : copy('liveDisabled')}
                        </p>
                        <button type="button" onClick={() => navigate('/chat?app=1')}>
                            {copy('backToChat')}
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
                                            <h2 className="speech-chat-empty-card-title">{copy('title')}</h2>
                                            <p className="speech-chat-empty-card-body">
                                                {copy('emptyBody')}
                                            </p>
                                        </div>
                                    ) : null}

                                    {turns.map((turn) => (
                                        <article key={turn.id} className="speech-turn">
                                            <div className="speech-turn__question">
                                                <span>{copy('youAsked')}</span>
                                                <p>{turn.question}</p>
                                            </div>
                                            <div
                                                className="speech-turn__answer"
                                                role="status"
                                                aria-live="polite"
                                                aria-atomic="false"
                                            >
                                                <span>{turn.voiceState === 'speaking' ? copy('speaking') : turn.pending ? copy('answering') : turn.stopped ? copy('stopped') : copy('answered')}</span>
                                                <p>{turn.answer || (turn.pending ? (processingBridgeCaption || copy('reading')) : '')}</p>
                                            </div>
                                        </article>
                                    ))}

                                    {status === 'reviewing' ? (
                                        <div className="speech-chat-review-card">
                                            <label htmlFor="speech-review-input">{copy('checkQuestion')}</label>
                                            <textarea
                                                id="speech-review-input"
                                                value={pendingTranscript}
                                                onFocus={clearTranscriptSendTimer}
                                                onChange={(event) => {
                                                    clearTranscriptSendTimer();
                                                    setPendingTranscript(event.target.value);
                                                    setCurrentTranscript(event.target.value);
                                                }}
                                                rows={2}
                                            />
                                            {transcriptAlternatives.length > 0 ? (
                                                <div className="speech-chat-review-alternatives" aria-label={copy('alternatives')}>
                                                    {transcriptAlternatives.map((alternative) => (
                                                        <button
                                                            key={alternative}
                                                            type="button"
                                                            onClick={() => {
                                                                clearTranscriptSendTimer();
                                                                setPendingTranscript(alternative);
                                                                setCurrentTranscript(alternative);
                                                            }}
                                                        >
                                                            {alternative}
                                                        </button>
                                                    ))}
                                                </div>
                                            ) : null}
                                            <div className="speech-chat-review-actions">
                                                <button type="button" className="is-secondary" onClick={cancelPendingTranscript}>{copy('cancel')}</button>
                                                <button type="button" onClick={() => sendPendingTranscript()} disabled={!pendingTranscript.trim()}>{copy('sendNow')}</button>
                                            </div>
                                        </div>
                                    ) : currentTranscript ? (
                                        <div
                                            className={`speech-chat-live-card ${status !== 'idle' ? 'speech-chat-live-card--pulse' : ''}`}
                                        >
                                            <span className="speech-chat-live-card-label">
                                                {status === 'listening' ? copy('heard') : copy('currentQuestion')}
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
                            {billingReceipt ? <p className="speech-chat-receipt">{billingReceipt}</p> : null}
                            <details className="speech-chat-privacy">
                                <summary>{copy('privacyDetails')}</summary>
                                <p>{copy('privacyBody')}</p>
                                <div className="speech-chat-privacy__actions">
                                    <button type="button" onClick={clearCurrentConversation}>{copy('clearScreen')}</button>
                                    <button type="button" className="is-danger" onClick={deleteSavedChatHistory}>{copy('deleteHistory')}</button>
                                </div>
                            </details>
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
                                    <div className={`speech-chat-wave-row ${status === 'listening' && micLevel > 0 ? 'speech-chat-wave-row--metered' : ''}`}>
                                        {[0, 1, 2, 3, 4].map((i) => (
                                            <span
                                                key={i}
                                                className={`speech-chat-wave-bar speech-chat-wave-bar--${i}`}
                                                style={status === 'listening' && micLevel > 0
                                                    ? { transform: `scaleY(${Math.min(1, 0.2 + micLevel * (0.7 + (i % 3) * 0.12))})` }
                                                    : undefined}
                                            />
                                        ))}
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    className={`speech-chat-hands-free ${handsFree ? 'speech-chat-hands-free--on' : ''}`}
                                    onClick={() => setHandsFree((v) => !v)}
                                >
                                    <span className="speech-chat-hands-free-icon" aria-hidden>{handsFree ? '◉' : '○'}</span>
                                    <span className="speech-chat-hands-free-label">{copy('handsFree')}</span>
                                    <span className={`speech-chat-hands-free-state ${handsFree ? 'is-on' : ''}`}>
                                        {handsFree ? copy('on') : copy('off')}
                                    </span>
                                </button>

                                <p className="speech-chat-status" role="status" aria-live="polite">
                                    {taraStatusLabels[status] || taraStatusLabels.idle}
                                </p>
                                <p className="speech-chat-meta">
                                    {billingSession ? `${formatSpeechDuration(callElapsedSeconds)} · ` : ''}
                                    {copy('credits')}: {credits} · {copy('title')}: {speechChatPerMinuteCost} {copy('perMinute')}
                                </p>

                                {billingSession ? (
                                    <button type="button" className="speech-chat-end-talk" onClick={handleEndTalk}>
                                        <span aria-hidden>■</span> {copy('endTalk')}
                                    </button>
                                ) : null}

                                <div className="speech-chat-mic-outer">
                                    <button
                                        type="button"
                                        className={`speech-chat-mic speech-chat-mic--${status}`}
                                        onClick={handleMicPress}
                                        disabled={micDisabled}
                                        aria-label={
                                            status === 'speaking'
                                                ? copy('stopSpeaking')
                                                : status === 'thinking'
                                                    ? copy('stopAnswer')
                                                : status === 'listening'
                                                    ? copy('stopListening')
                                                    : status === 'transcribing'
                                                        ? copy('transcribingMic')
                                                    : copy('startMic')
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
