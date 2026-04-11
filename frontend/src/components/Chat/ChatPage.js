import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import MessageList from './MessageList';
import { scrollChatThreadAfterMessagesChange } from './chatScrollUtils';
import ChatChartEssence from './ChatChartEssence';
import ChatInput from './ChatInput';
import BirthFormModal from '../BirthForm/BirthFormModal';
import NavigationHeader from '../Shared/NavigationHeader';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import CreditsModal from '../Credits/CreditsModal';
import ContextModal from './ContextModal';
import PartnerChartModal from './PartnerChartModal';
import { authService } from '../../services/authService';
import { locationService } from '../../services/locationService';
import { apiService } from '../../services/apiService';
import { normalizeBirthDetailsForChat } from '../../utils/normalizeBirthDetailsForChat';
import '../Shared/nativeSelectorChip.css';
import './ChatPage.css';

/** Single-chart wizard: empty `{}` is truthy in JS — require real fields before showing a “profile ready” card. */
function isBirthChartReadyForChat(data) {
    const norm = normalizeBirthDetailsForChat(data);
    if (!norm) return false;
    if (!norm.date || !String(norm.date).trim()) return false;
    if (!norm.time || !String(norm.time).trim()) return false;
    const hasCoords = Number.isFinite(norm.latitude) && Number.isFinite(norm.longitude);
    const hasPlace = norm.place && String(norm.place).trim().length > 0;
    return hasCoords || hasPlace;
}

/**
 * `/api/chat/history` (legacy session store) returns rows like `{ question, response, timestamp }`.
 * MessageBubble expects `{ role, content, timestamp }`; without this, `content` is missing and only the
 * per-row clock (toLocaleTimeString) appears under chart essence.
 */
function normalizeLegacyChatHistoryItems(items) {
    if (!Array.isArray(items)) return [];
    const out = [];
    let seq = 0;
    const nid = () => `hist-${Date.now()}-${seq++}`;

    for (const item of items) {
        if (!item || typeof item !== 'object') continue;

        if (item.role === 'user' || item.role === 'assistant') {
            out.push({
                ...item,
                messageId: item.messageId ?? item.message_id ?? nid(),
                timestamp: item.timestamp || new Date().toISOString(),
            });
            continue;
        }

        const ts = item.timestamp || new Date().toISOString();
        const q = item.question != null ? String(item.question).trim() : '';
        const r = item.response != null ? String(item.response).trim() : '';
        if (q) {
            out.push({ role: 'user', content: q, timestamp: ts, messageId: nid() });
        }
        if (r) {
            out.push({
                role: 'assistant',
                content: r,
                timestamp: ts,
                messageId: nid(),
                message_type: item.message_type || 'answer',
            });
        }
    }
    return out;
}

function singleChartProfileDisplay(b) {
    if (!b) return { name: 'Your chart', initials: '?', metaLine: '' };
    const name = (b.name && String(b.name).trim()) || 'Your chart';
    const parts = name.split(/\s+/).filter(Boolean);
    const initials =
        parts.length >= 2
            ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
            : (parts[0] && parts[0][0] ? parts[0][0].toUpperCase() : '?');

    let dateLabel = b.date || '';
    try {
        const raw = String(dateLabel).split('T')[0];
        const seg = raw.split('-').map((x) => parseInt(x, 10));
        if (seg.length === 3 && seg.every((n) => !Number.isNaN(n))) {
            const [yy, mm, dd] = seg;
            dateLabel = new Date(yy, mm - 1, dd).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
            });
        }
    } catch {
        /* keep raw */
    }
    const rawTime = b.time != null ? String(b.time) : '';
    const timeMatch = rawTime.match(/(\d{1,2}:\d{2})/);
    const timeShort = timeMatch ? timeMatch[1] : rawTime.slice(0, 5);
    const loc = b.place && String(b.place).trim();
    const coordFallback =
        !loc && b.latitude != null && b.longitude != null
            ? `${Number(b.latitude).toFixed(4)}, ${Number(b.longitude).toFixed(4)}`
            : '';
    const metaLine = [dateLabel, timeShort, loc || coordFallback].filter(Boolean).join(' · ');
    return { name, initials, metaLine };
}

// Enable detailed logging for debugging
// console.log('ChatPage component loaded - debugging enabled');

const ChatPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { birthData } = useAstrology();
    const singleChartWizardProfile = useMemo(() => singleChartProfileDisplay(birthData), [birthData]);
    const { credits, chatCost, partnershipCost, fetchBalance, freeQuestionAvailable } = useCredits();
    const { birthData: initialBirthData } = location.state || {};
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showCreditsModal, setShowCreditsModal] = useState(false);
    const [showContextModal, setShowContextModal] = useState(false);
    const [contextData, setContextData] = useState(null);
    const [isAdmin, setIsAdmin] = useState(false);
    const [headerUser, setHeaderUser] = useState(() => {
        try {
            const raw = localStorage.getItem('user');
            return raw ? JSON.parse(raw) : null;
        } catch {
            return null;
        }
    });
    const [isPartnershipMode, setIsPartnershipMode] = useState(false);
    const [selectedPartnerChart, setSelectedPartnerChart] = useState(null);
    const [showPartnerModal, setShowPartnerModal] = useState(false);
    const messagesEndRef = useRef(null);

    // Guided workflow wizard (embedded in this one-screen chat page).
    const [wizardMode, setWizardMode] = useState(null); // 'single' | 'partnership' | 'mundane'
    const [wizardStep, setWizardStep] = useState(0);
    const [wizardCompleted, setWizardCompleted] = useState(false);
    const isWizardLocked = !wizardCompleted;
    const [wizardPartnershipStep, setWizardPartnershipStep] = useState(1); // 1:first chart, 2:second chart, 3:relationship
    const [wizardPrimaryChart, setWizardPrimaryChart] = useState(null);
    const [wizardSecondaryChart, setWizardSecondaryChart] = useState(null);
    const [wizardRelationshipText, setWizardRelationshipText] = useState('');
    const [wizardRelationshipSubStep, setWizardRelationshipSubStep] = useState(0);
    const [wizardRelationshipOtherMode, setWizardRelationshipOtherMode] = useState(false);
    const [wizardRelationshipOtherText, setWizardRelationshipOtherText] = useState('');
    const [partnerModalMode, setPartnerModalMode] = useState(null); // 'wizard-first' | 'wizard-second'
    const [showBirthFormModal, setShowBirthFormModal] = useState(false);
    const [pendingFollowUpQuestion, setPendingFollowUpQuestion] = useState('');
    /** Set when navigating from analysis follow-up chips; consumed when single-chart chat is ready. */
    const analysisChatIntentRef = useRef(null);

    // Mundane wizard state
    const [isMundaneMode, setIsMundaneMode] = useState(false);
    const [mundaneSessionId, setMundaneSessionId] = useState(null);
    const [mundaneForm, setMundaneForm] = useState({
        country: '',
        year: '',
        category: 'general',
        entitiesRaw: '',
        eventDate: '',
        eventTime: '',
        placeQuery: '',
        placeSuggestions: [],
        placeLoading: false,
        latitude: null,
        longitude: null,
    });

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const RELATIONSHIP_PRESETS = [
        {
            label: 'Husband & Wife',
            subSteps: [
                {
                    prompt: 'Who is who?',
                    options: (n, p) => [
                        { label: `${n?.name || 'Person 1'} (H) & ${p?.name || 'Person 2'} (W)`, value: `${n?.name || 'Person 1'} is husband and ${p?.name || 'Person 2'} is wife` },
                        { label: `${n?.name || 'Person 1'} (W) & ${p?.name || 'Person 2'} (H)`, value: `${n?.name || 'Person 1'} is wife and ${p?.name || 'Person 2'} is husband` }
                    ]
                },
                {
                    prompt: 'Marriage details?',
                    options: () => [
                        { label: 'First Marriage', value: '1st Marriage' },
                        { label: 'Second Marriage', value: '2nd Marriage' },
                        { label: 'Third Marriage', value: '3rd Marriage' }
                    ]
                }
            ]
        },
        {
            label: 'Parent & Child',
            subSteps: [
                {
                    prompt: 'Relationship roles?',
                    options: (n, p) => [
                        { label: `${n?.name || 'Person 1'} is Parent`, value: `${n?.name || 'Person 1'} is parent and ${p?.name || 'Person 2'} is child` },
                        { label: `${p?.name || 'Person 2'} is Parent`, value: `${p?.name || 'Person 2'} is parent and ${n?.name || 'Person 1'} is child` }
                    ]
                },
                {
                    prompt: 'Specify child details?',
                    options: () => [
                        { label: '1st Son', value: '1st son' },
                        { label: '2nd Son', value: '2nd son' },
                        { label: '3rd Son', value: '3rd son' },
                        { label: '1st Daughter', value: '1st daughter' },
                        { label: '2nd Daughter', value: '2nd daughter' },
                        { label: '3rd Daughter', value: '3rd daughter' }
                    ]
                }
            ]
        },
        {
            label: 'Siblings',
            subSteps: [
                {
                    prompt: 'Who is elder?',
                    options: (n, p) => [
                        { label: `${n?.name || 'Person 1'} is Elder`, value: `${n?.name || 'Person 1'} is elder sibling and ${p?.name || 'Person 2'} is younger` },
                        { label: `${p?.name || 'Person 2'} is Elder`, value: `${p?.name || 'Person 2'} is elder sibling and ${n?.name || 'Person 1'} is younger` }
                    ]
                }
            ]
        },
        {
            label: 'In-Laws',
            subSteps: [
                {
                    prompt: 'Who is the In-Law?',
                    options: (n, p) => [
                        { label: `${n?.name || 'Person 1'} is In-Law`, value: `${n?.name || 'Person 1'} is in-law of ${p?.name || 'Person 2'}` },
                        { label: `${p?.name || 'Person 2'} is In-Law`, value: `${p?.name || 'Person 2'} is in-law of ${n?.name || 'Person 1'}` }
                    ]
                },
                {
                    prompt: 'Specific relationship?',
                    options: () => [
                        { label: 'Mother-in-law & Daughter-in-law', value: 'Mother-in-law and Daughter-in-law' },
                        { label: 'Mother-in-law & Son-in-law', value: 'Mother-in-law and Son-in-law' },
                        { label: 'Father-in-law & Daughter-in-law', value: 'Father-in-law and Daughter-in-law' },
                        { label: 'Father-in-law & Son-in-law', value: 'Father-in-law and Son-in-law' },
                        { label: 'Brother-in-law', value: 'Brother-in-law relation' },
                        { label: 'Sister-in-law', value: 'Sister-in-law relation' }
                    ]
                }
            ]
        },
        {
            label: 'Grandparent & Grandchild',
            subSteps: [
                {
                    prompt: 'Roles?',
                    options: (n, p) => [
                        { label: `${n?.name || 'Person 1'} is Grandparent`, value: `${n?.name || 'Person 1'} is grandparent and ${p?.name || 'Person 2'} is grandchild` },
                        { label: `${p?.name || 'Person 2'} is Grandparent`, value: `${p?.name || 'Person 2'} is grandparent and ${n?.name || 'Person 1'} is grandchild` }
                    ]
                }
            ]
        },
        {
            label: 'Uncle/Aunt & Nephew/Niece',
            subSteps: [
                {
                    prompt: 'Roles?',
                    options: (n, p) => [
                        { label: `${n?.name || 'Person 1'} is Uncle/Aunt`, value: `${n?.name || 'Person 1'} is uncle/aunt and ${p?.name || 'Person 2'} is nephew/niece` },
                        { label: `${p?.name || 'Person 2'} is Uncle/Aunt`, value: `${p?.name || 'Person 2'} is uncle/aunt and ${n?.name || 'Person 1'} is nephew/niece` }
                    ]
                }
            ]
        },
        { label: 'Cousins' },
        { label: 'Guru & Disciple' },
        { label: 'Business Partners' },
        { label: 'Close Friends' },
        { label: 'Boyfriend & Girlfriend' },
        {
            label: 'Manager & Employee',
            subSteps: [
                {
                    prompt: 'Work roles?',
                    options: (n, p) => [
                        { label: `${n?.name || 'Person 1'} is Manager`, value: `${n?.name || 'Person 1'} is manager and ${p?.name || 'Person 2'} is employee` },
                        { label: `${p?.name || 'Person 2'} is Manager`, value: `${p?.name || 'Person 2'} is manager and ${n?.name || 'Person 1'} is employee` }
                    ]
                }
            ]
        },
        { label: 'Colleague' },
        { label: 'Teacher & Student' },
        { label: 'Other...' }
    ];

    const getActiveRelationshipPreset = () => {
        if (!wizardRelationshipText) return null;
        return RELATIONSHIP_PRESETS.find((p) => (
            wizardRelationshipText === p.label || wizardRelationshipText.startsWith(`${p.label}:`)
        )) || null;
    };

    const isRelationshipReady = () => {
        if (!wizardRelationshipText) return false;
        const currentPreset = getActiveRelationshipPreset();
        if (!currentPreset || !currentPreset.subSteps) return true;
        return wizardRelationshipSubStep >= currentPreset.subSteps.length;
    };

    const getRelationshipSuggestedQuestions = () => {
        const label = wizardRelationshipText || 'this relationship';
        return [
            `What supportive links show up between the charts in ${label}?`,
            `What challenges or growth edges are clearest in ${label}?`,
            `What timing or dasha/transit phases matter most for ${label}?`,
        ];
    };

    const handleRelationshipSelect = (selection) => {
        if (selection === 'Other...') {
            setWizardRelationshipOtherMode(true);
            setWizardRelationshipOtherText('');
            setWizardRelationshipText('');
            setWizardRelationshipSubStep(0);
            return;
        }

        const selectionLabel = typeof selection === 'object' ? selection.label : selection;
        const activePreset = RELATIONSHIP_PRESETS.find((p) => p.label === selectionLabel);

        if (activePreset && activePreset.subSteps && wizardRelationshipText !== activePreset.label) {
            // Start preset flow (mobile parity)
            setWizardRelationshipText(activePreset.label);
            setWizardRelationshipSubStep(0);
            setWizardRelationshipOtherMode(false);
            setWizardRelationshipOtherText('');
            return;
        }

        const currentPreset = getActiveRelationshipPreset();
        if (currentPreset && currentPreset.subSteps && wizardRelationshipSubStep < currentPreset.subSteps.length) {
            // Continue sub-steps (mobile parity)
            const valueToUse = typeof selection === 'object' ? selection.value : selection;
            const newRelation = (wizardRelationshipText === currentPreset.label)
                ? `${currentPreset.label}: ${valueToUse}`
                : `${wizardRelationshipText}, ${valueToUse}`;
            const nextSubStep = wizardRelationshipSubStep + 1;
            setWizardRelationshipText(newRelation);
            setWizardRelationshipSubStep(nextSubStep);
            return;
        }

        // Simple preset / final direct relation
        setWizardRelationshipOtherMode(false);
        setWizardRelationshipOtherText('');
        setWizardRelationshipSubStep(999);
        setWizardRelationshipText(selectionLabel);
    };

    const handleRelationshipBack = () => {
        const currentPreset = getActiveRelationshipPreset();
        if (!currentPreset || !currentPreset.subSteps) return;
        if (wizardRelationshipSubStep <= 0) {
            setWizardRelationshipText('');
            setWizardRelationshipSubStep(0);
            return;
        }

        // If user already has appended values, reset to base label and step 0.
        setWizardRelationshipText(currentPreset.label);
        setWizardRelationshipSubStep(0);
    };

    const handleRelationshipPresetSelect = (label) => {
        if (label === 'Other...') {
            handleRelationshipSelect('Other...');
            return;
        }

        setWizardRelationshipOtherMode(false);
        setWizardRelationshipOtherText('');
        handleRelationshipSelect(label);
    };

    // --- chat-v2 async flow (mobile parity) ---
    const [chatV2SessionId, setChatV2SessionId] = useState(null);
    const [personalChartData, setPersonalChartData] = useState(null);
    const [chatDashaData, setChatDashaData] = useState(null);
    const [chartEssenceLoading, setChartEssenceLoading] = useState(false);

    useEffect(() => {
        let cancelled = false;

        if (!wizardCompleted || isMundaneMode || !isBirthChartReadyForChat(birthData)) {
            setPersonalChartData(null);
            setChatDashaData(null);
            setChartEssenceLoading(false);
            return;
        }

        const run = async () => {
            setChartEssenceLoading(true);
            setPersonalChartData(null);
            setChatDashaData(null);

            try {
                const chartPayload = {
                    ...birthData,
                    latitude: birthData.latitude != null ? parseFloat(birthData.latitude) : undefined,
                    longitude: birthData.longitude != null ? parseFloat(birthData.longitude) : undefined,
                };
                const today = new Date().toISOString().split('T')[0];

                const [chartResult, dashaResult] = await Promise.allSettled([
                    apiService.calculateChartOnly(chartPayload),
                    /* Same normalized birth payload as chart (mobile Safari / form quirks). */
                    apiService.calculateCascadingDashas(chartPayload, today),
                ]);

                if (cancelled) return;

                if (chartResult.status === 'fulfilled') {
                    setPersonalChartData(chartResult.value);
                } else {
                    console.error('[ChatPage] Failed to calculate chart only:', chartResult.reason);
                }

                if (dashaResult.status === 'fulfilled') {
                    const d = dashaResult.value;
                    if (d && !d.error) setChatDashaData(d);
                } else {
                    console.error('[ChatPage] Failed to calculate cascading dashas:', dashaResult.reason);
                }
            } finally {
                if (!cancelled) setChartEssenceLoading(false);
            }
        };

        run();
        return () => {
            cancelled = true;
        };
    }, [wizardCompleted, isMundaneMode, birthData]);

    const createChatV2Session = async () => {
        try {
            const token = localStorage.getItem('token');
            // Web flow may not have a persisted birth_chart_id (birthData.id).
            // Backend supports null birth_chart_id; we still pass full birth_details on /ask.
            const birthChartId = birthData?.id ?? null;
            if (!birthData?.id) {
                console.warn('[ChatPage] chat-v2 session: missing birthData.id (using null birth_chart_id)');
            }

            const response = await fetch('/api/chat-v2/session', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    birth_chart_id: birthChartId,
                }),
            });

            if (!response.ok) {
                const t = await response.text().catch(() => '');
                console.warn('[ChatPage] chat-v2 session create failed:', response.status, t);
                return null;
            }

            const data = await response.json();
            return data.session_id;
        } catch (e) {
            console.error('[ChatPage] Error creating chat-v2 session:', e);
            return null;
        }
    };

    const parsePythonLikeDictString = (input) => {
        if (typeof input !== 'string') return null;
        const s = input.trim();
        if (!s) return null;

        // 1) Try JSON directly first (in case backend ever returns valid JSON).
        try {
            return JSON.parse(s);
        } catch (_) {}

        // 2) Backend currently sends a Python-literal-ish dict as a string.
        //    It's close to a JS object literal, but it may include Python-only tokens
        //    like `datetime.datetime(...)` which will crash evaluation in the browser.
        //    We'll sanitize those to `null` before evaluating.
        try {
            const sanitized = s
                .replace(/\bdatetime\.datetime\([^)]*\)/g, 'null')
                .replace(/\bdatetime\.date\([^)]*\)/g, 'null')
                .replace(/\bdatetime\.timedelta\([^)]*\)/g, 'null');

            const jsLiteral = sanitized
                .replace(/\bTrue\b/g, 'true')
                .replace(/\bFalse\b/g, 'false')
                .replace(/\bNone\b/g, 'null');

            // eslint-disable-next-line no-new-func
            const obj = new Function(`"use strict"; return (${jsLiteral});`)();
            return obj;
        } catch (e) {
            console.warn('[ChatPage] [CONTEXT PARSE] failed to parse context string', {
                message: e?.message,
            });
            return null;
        }
    };

    useEffect(() => {
        return scrollChatThreadAfterMessagesChange(messages, scrollToBottom);
    }, [messages]);

    const addGreetingMessage = (overrideText = null) => {
        const place = birthData?.place && !birthData.place.includes(',') ? birthData.place : `${birthData?.latitude}, ${birthData?.longitude}`;
        const defaultText = `Hello ${birthData?.name || 'there'}! I see you were born on ${birthData?.date ? new Date(birthData.date).toLocaleDateString() : 'your birth date'} at ${place || 'your place'}. I'm here to help you understand your birth chart and provide astrological guidance. What would you like to know?`;
        const greetingMessage = {
            role: 'assistant',
            content: overrideText || defaultText,
            timestamp: new Date().toISOString()
        };
        setMessages([greetingMessage]);
    };
    
    // Check token validity and user role on component mount
    useEffect(() => {
        const checkTokenValidity = async () => {
            const token = localStorage.getItem('token');
            // console.log('🔍 Checking token and admin status...');
            if (token) {
                try {
                    const response = await fetch('/api/me', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (response.status === 401) {
                        // console.log('🔐 Invalid token detected, clearing auth...');
                        localStorage.removeItem('token');
                        localStorage.removeItem('user');
                        setHeaderUser(null);
                        window.location.href = '/login';
                    } else if (response.ok) {
                        const userData = await response.json();
                        // console.log('👤 User data:', userData);
                        // console.log('🔑 User role:', userData.role);
                        // console.log('👑 Is admin?', userData.role === 'admin');
                        setIsAdmin(userData.role === 'admin');
                        setHeaderUser(userData);
                    }
                } catch (error) {
                    console.log('Token validation failed:', error);
                }
            } else {
                console.log('❌ No token found');
            }
        };
        checkTokenValidity();
    }, []);

    // Mundane wizard: live place search suggestions
    useEffect(() => {
        if (wizardMode !== 'mundane' || wizardCompleted) return;

        const q = (mundaneForm.placeQuery || '').trim();
        if (q.length < 3) {
            setMundaneForm((p) => ({ ...p, placeSuggestions: [] }));
            return;
        }

        const timeout = setTimeout(async () => {
            setMundaneForm((p) => ({ ...p, placeLoading: true }));
            try {
                const results = await locationService.searchPlaces(q);
                setMundaneForm((p) => ({
                    ...p,
                    placeSuggestions: (results || []).slice(0, 5),
                    placeLoading: false,
                }));
            } catch (e) {
                setMundaneForm((p) => ({ ...p, placeSuggestions: [], placeLoading: false }));
            }
        }, 450);

        return () => clearTimeout(timeout);
    }, [mundaneForm.placeQuery, wizardMode, wizardCompleted]);
    
    // Initialize message thread after wizard completion.
    const threadInitializedRef = useRef(false);
    useEffect(() => {
        if (!wizardCompleted) return;
        if (!birthData && !isMundaneMode) return;
        if (threadInitializedRef.current) return;

        threadInitializedRef.current = true;
        if (isMundaneMode) {
            addGreetingMessage(
                `🌍 Mundane mode enabled.\n\nYou’ll be able to ask about global trends and event dynamics related to ${mundaneForm.country || 'your selected region'}. Start by asking your main question (e.g. “What are the likely phases for this event category this year?”).`
            );
            return;
        }

        if (wizardMode === 'single') {
            loadChatHistory();
            return;
        }

        if (
            wizardMode === 'partnership' &&
            wizardPrimaryChart &&
            wizardSecondaryChart &&
            (wizardRelationshipText || '').trim()
        ) {
            const rel = wizardRelationshipText.trim();
            addGreetingMessage(
                `Everything set! Analysis for **${wizardPrimaryChart.name}** & **${wizardSecondaryChart.name}** (${rel}) is ready.\n\nAsk any question about your compatibility!`
            );
            return;
        }

        addGreetingMessage();
    }, [
        wizardCompleted,
        wizardMode,
        birthData,
        isMundaneMode,
        mundaneForm.country,
        wizardPrimaryChart,
        wizardSecondaryChart,
        wizardRelationshipText,
    ]);

    const loadChatHistory = async () => {
        try {
            // console.log('Loading chat history for:', birthData);
            const token = localStorage.getItem('token');
            const response = await fetch('/api/chat/history', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify(birthData)
            });
            
            if (!response.ok) {
                // console.error('History response error:', response.status, response.statusText);
            }
            
            const data = await response.json();
            // console.log('Chat history response:', data);
            const existingMessages = normalizeLegacyChatHistoryItems(data.history || data.messages || []);
            setMessages(existingMessages);
            
            // Add greeting if no existing messages
            if (existingMessages.length === 0) {
                addGreetingMessage();
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
            // Add greeting on error too
            addGreetingMessage();
        }
    };

    const resetThreadForWizard = (nextMode) => {
        setMessages([]);
        setWizardCompleted(false);
        threadInitializedRef.current = false;
        setIsPartnershipMode(false);
        setSelectedPartnerChart(null);
        setWizardPartnershipStep(1);
        setWizardPrimaryChart(null);
        setWizardSecondaryChart(null);
        setWizardRelationshipText('');
        setWizardRelationshipSubStep(0);
        setWizardRelationshipOtherMode(false);
        setWizardRelationshipOtherText('');
        setIsMundaneMode(nextMode === 'mundane');
        setMundaneSessionId(null);
        setMundaneForm((prev) => ({
            ...prev,
            country: '',
            year: '',
            category: 'general',
            entitiesRaw: '',
            eventDate: '',
            eventTime: '',
            placeQuery: '',
            placeSuggestions: [],
            placeLoading: false,
            latitude: null,
            longitude: null,
        }));
    };

    // Universal AI analysis follow-up → Single chart mode + prefill composer (see UniversalAIInsights follow-up chips)
    useEffect(() => {
        const st = location.state;
        if (!st?.openSingleChartChat) return;

        const q = typeof st.followUpQuestion === 'string' ? st.followUpQuestion.trim() : '';
        analysisChatIntentRef.current = { question: q };

        navigate(location.pathname, { replace: true, state: {} });

        resetThreadForWizard('single');
        setChatV2SessionId(null);
        setWizardMode('single');
        setWizardStep(1);
    }, [location.state]);

    useEffect(() => {
        const intent = analysisChatIntentRef.current;
        if (!intent) return;
        if (!birthData?.name || !birthData?.date) return;

        setIsPartnershipMode(false);
        setIsMundaneMode(false);
        setWizardCompleted(true);
        if (intent.question) {
            setPendingFollowUpQuestion(intent.question);
        }
        analysisChatIntentRef.current = null;
    }, [birthData]);

    const createMundaneSession = async () => {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/mundane/session', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            }
        });
        if (!res.ok) {
            const t = await res.text().catch(() => '');
            throw new Error(`Failed to create mundane session: ${res.status} ${t}`);
        }
        const data = await res.json();
        return data.session_id;
    };

    const pollMundaneStatus = async (messageId, assistantMessageIdToUpdate) => {
        const token = localStorage.getItem('token');
        const maxPolls = 120; // 6 minutes (120 * 3s)
        let pollCount = 0;

        const poll = async () => {
            const res = await fetch(`/api/chat-v2/status/${messageId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error(`Status polling failed: HTTP ${res.status}`);
            const status = await res.json();

            if (status.status === 'completed') {
                setMessages((prev) =>
                    prev.map((m) =>
                        m.messageId === assistantMessageIdToUpdate
                            ? { ...m, content: status.content || '', isProcessing: false }
                            : m
                    )
                );
                setIsLoading(false);
                return;
            }

            if (status.status === 'failed') {
                setMessages((prev) =>
                    prev.map((m) =>
                        m.messageId === assistantMessageIdToUpdate
                            ? { ...m, content: status.error_message || 'Mundane analysis failed. Please try again.', isProcessing: false }
                            : m
                    )
                );
                setIsLoading(false);
                return;
            }

            // Still processing
            if (status.status === 'processing' && status.message) {
                setMessages((prev) =>
                    prev.map((m) =>
                        m.messageId === assistantMessageIdToUpdate ? { ...m, content: status.message, isProcessing: true } : m
                    )
                );
            }

            pollCount++;
            if (pollCount >= maxPolls) {
                setMessages((prev) =>
                    prev.map((m) =>
                        m.messageId === assistantMessageIdToUpdate
                            ? { ...m, content: 'Mundane analysis is taking longer than expected. You can refresh later from history.', isProcessing: false }
                            : m
                    )
                );
                setIsLoading(false);
                return;
            }

            setTimeout(() => poll().catch(() => {}), 3000);
        };

        return poll();
    };

    const handleSendMundaneMessage = async (message, options = {}) => {
        if (!mundaneForm.country || !mundaneForm.latitude || !mundaneForm.longitude) {
            setIsLoading(false);
            return;
        }

        setIsLoading(true);

        const userMessage = {
            role: 'user',
            content: message,
            timestamp: new Date().toISOString(),
            messageId: Date.now()
        };
        setMessages((prev) => [...prev, userMessage]);

        let currentSessionId = mundaneSessionId;
        if (!currentSessionId) {
            currentSessionId = await createMundaneSession();
            setMundaneSessionId(currentSessionId);
        }

        const entities = mundaneForm.entitiesRaw
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean);

        const payload = {
            session_id: currentSessionId,
            country: mundaneForm.country,
            year: mundaneForm.year ? parseInt(mundaneForm.year, 10) : undefined,
            latitude: mundaneForm.latitude,
            longitude: mundaneForm.longitude,
            question: message,
            category: mundaneForm.category || 'general',
            event_date: mundaneForm.eventDate || undefined,
            event_time: mundaneForm.eventTime || undefined,
            entities: entities.length ? entities : undefined,
        };

        const token = localStorage.getItem('token');
        const res = await fetch('/api/mundane/analyze', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            const t = await res.text().catch(() => '');
            setIsLoading(false);
            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: `Mundane analysis failed to start. ${res.status} ${t}`.trim(),
                    timestamp: new Date().toISOString(),
                    messageId: Date.now() + 1,
                    isProcessing: false,
                }
            ]);
            return;
        }

        const data = await res.json();
        const assistantMessageId = data.message_id;

        const assistantMessage = {
            role: 'assistant',
            content: data.message || 'Analyzing global trends...',
            timestamp: new Date().toISOString(),
            messageId: assistantMessageId,
            isProcessing: true,
            isFromDatabase: true,
            message_type: 'answer',
        };

        setMessages((prev) => [...prev, assistantMessage]);

        // Poll status until completed/failed.
        pollMundaneStatus(assistantMessageId, assistantMessageId).catch(() => {
            setIsLoading(false);
        });
    };

    const pollChatV2Status = async (assistantMessageId, processingClientId) => {
        const token = localStorage.getItem('token');
        const maxPolls = 120; // 6 minutes (120 * 3s), aligned with Ashtakavarga life-predictions jobs
        let pollCount = 0;

        const poll = async () => {
            try {
                const res = await fetch(`/api/chat-v2/status/${assistantMessageId}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (!res.ok) {
                    throw new Error(`chat-v2 status failed: HTTP ${res.status}`);
                }

                const status = await res.json();
                console.log('[ChatPage] chat-v2 poll', {
                    assistantMessageId,
                    pollCount,
                    status: status?.status,
                });

                if (status.status === 'completed') {
                    const raw =
                        status.content != null && String(status.content).trim() !== ''
                            ? status.content
                            : '';
                    const content =
                        raw ||
                        "This answer didn't save any text. Please try your question again, or contact support if it keeps happening.";
                    setMessages(prev =>
                        prev.map(m =>
                            m.processingClientId === processingClientId
                                ? {
                                    ...m,
                                    messageId: assistantMessageId,
                                    content,
                                    isProcessing: false,
                                    isTyping: false,
                                    message_type: status.message_type || 'answer',
                                    terms: status.terms || [],
                                    glossary: status.glossary || {},
                                    summary_image: status.summary_image || null,
                                    follow_up_questions: status.follow_up_questions || [],
                                }
                                : m
                        )
                    );
                    setIsLoading(false);
                    fetchBalance();
                    return;
                }

                if (status.status === 'failed') {
                    setMessages(prev =>
                        prev.map(m =>
                            m.processingClientId === processingClientId
                                ? {
                                    ...m,
                                    content: status.error_message || 'Analysis failed. Please try again.',
                                    isProcessing: false,
                                    isTyping: false,
                                    showRestartButton: true,
                                }
                                : m
                        )
                    );
                    setIsLoading(false);
                    return;
                }

                if (status.status === 'processing') {
                    // If chart_insights wasn't provided, fall back to rotating loading strings.
                    const loadingList = status.loading_messages || [];
                    if (Array.isArray(loadingList) && loadingList.length > 0) {
                        const next = loadingList[Math.floor(Math.random() * loadingList.length)];
                        setMessages(prev =>
                            prev.map(m =>
                                m.processingClientId === processingClientId
                                    ? { ...m, loadingMessage: next, isProcessing: true, isTyping: true }
                                    : m
                            )
                        );
                    }

                    pollCount++;
                    if (pollCount < maxPolls) {
                        setTimeout(() => poll().catch(() => {}), 3000);
                    } else {
                        setMessages(prev =>
                            prev.map(m =>
                                m.processingClientId === processingClientId
                                    ? {
                                        ...m,
                                        content: 'Analysis is taking longer than expected. Please try again later.',
                                        isProcessing: false,
                                        isTyping: false,
                                        showRestartButton: true,
                                    }
                                    : m
                            )
                        );
                        setIsLoading(false);
                    }
                } else {
                    // Unknown intermediate status - keep polling.
                    pollCount++;
                    if (pollCount < maxPolls) {
                        setTimeout(() => poll().catch(() => {}), 3000);
                    } else {
                        setIsLoading(false);
                    }
                }
            } catch (e) {
                console.error('[ChatPage] chat-v2 poll error:', e);
                setMessages(prev =>
                    prev.map(m =>
                        m.processingClientId === processingClientId
                            ? {
                                ...m,
                                content: 'Connection error. Please try again.',
                                isProcessing: false,
                                isTyping: false,
                                showRestartButton: true,
                            }
                            : m
                    )
                );
                setIsLoading(false);
            }
        };

        return poll();
    };

    const handleSendMessageChatV2 = async (message, options = {}) => {
        if (!birthData) return;

        let currentSessionId = chatV2SessionId;
        if (!currentSessionId) {
            currentSessionId = await createChatV2Session();
            if (!currentSessionId) return;
            setChatV2SessionId(currentSessionId);
        }

        const userMessageId = Date.now();
        setMessages(prev => [
            ...prev,
            { role: 'user', content: message, timestamp: new Date().toISOString(), messageId: userMessageId },
        ]);
        setIsLoading(true);

        let chartDataForMessage = personalChartData;
        if (!chartDataForMessage) {
            try {
                const calcNorm = normalizeBirthDetailsForChat(birthData);
                if (calcNorm && Number.isFinite(calcNorm.latitude) && Number.isFinite(calcNorm.longitude)) {
                    chartDataForMessage = await apiService.calculateChartOnly({
                        ...birthData,
                        ...calcNorm,
                    });
                    setPersonalChartData(chartDataForMessage);
                }
            } catch (e) {
                console.warn('[ChatPage] Could not calculate chart for processing bubble:', e);
            }
        }

        const processingClientId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const processingMessage = {
            role: 'assistant',
            content: '',
            timestamp: new Date().toISOString(),
            messageId: processingClientId,
            processingClientId,
            isProcessing: true,
            isTyping: true,
            message_type: 'answer',
            loadingMessage: '🔮 Analyzing your birth chart...',
            chartData: chartDataForMessage,
            chartInsights: [],
        };

        setMessages(prev => [...prev, processingMessage]);

        const token = localStorage.getItem('token');
        const partnershipBirth = isPartnershipMode && wizardPrimaryChart ? wizardPrimaryChart : birthData;
        const partnershipSecond = isPartnershipMode && wizardSecondaryChart ? wizardSecondaryChart : selectedPartnerChart;
        const relationshipLabel = (wizardRelationshipText || '').trim();
        // Backend chat-v2 does not read partnership_relationship; mobile prepends this for model/context (see ChatScreen.js).
        const questionForApi =
            isPartnershipMode && relationshipLabel
                ? `[Relationship: ${relationshipLabel}] ${message}`
                : message;

        const useFreeQuestion = !isPartnershipMode && !isMundaneMode && freeQuestionAvailable;

        const birthForAsk = normalizeBirthDetailsForChat(partnershipBirth);
        if (!birthForAsk || !Number.isFinite(birthForAsk.latitude) || !Number.isFinite(birthForAsk.longitude)) {
            console.error('[ChatPage] Invalid birth_details for chat-v2/ask', { partnershipBirth, birthForAsk });
            setIsLoading(false);
            setMessages((prev) =>
                prev.map((m) =>
                    m.processingClientId === processingClientId
                        ? {
                              ...m,
                              content: 'Birth place coordinates are missing or invalid. Please re-select your chart with a valid location.',
                              isProcessing: false,
                              isTyping: false,
                              showRestartButton: true,
                          }
                        : m
                )
            );
            return;
        }

        const requestData = {
            session_id: currentSessionId,
            question: questionForApi,
            language: 'english',
            response_style: 'detailed',
            premium_analysis: useFreeQuestion ? false : !!options.premium_analysis,
            partnership_mode: isPartnershipMode,
            native_name: partnershipBirth?.name,
            birth_details: birthForAsk,
        };

        if (isPartnershipMode && partnershipSecond) {
            const partnerNorm = normalizeBirthDetailsForChat(partnershipSecond);
            if (!partnerNorm || !Number.isFinite(partnerNorm.latitude) || !Number.isFinite(partnerNorm.longitude)) {
                console.error('[ChatPage] Invalid partner birth_details for chat-v2/ask', { partnershipSecond, partnerNorm });
                setIsLoading(false);
                setMessages((prev) =>
                    prev.map((m) =>
                        m.processingClientId === processingClientId
                            ? {
                                  ...m,
                                  content: 'Partner chart coordinates are missing or invalid. Please re-select the second profile.',
                                  isProcessing: false,
                                  isTyping: false,
                                  showRestartButton: true,
                              }
                            : m
                    )
                );
                return;
            }
            requestData.partner_name = partnerNorm.name;
            requestData.partner_date = partnerNorm.date;
            requestData.partner_time = partnerNorm.time;
            requestData.partner_place = partnerNorm.place || '';
            requestData.partner_latitude = partnerNorm.latitude;
            requestData.partner_longitude = partnerNorm.longitude;
            requestData.partner_timezone = partnershipSecond.timezone;
            requestData.partner_gender = partnerNorm.gender || '';
            requestData.partnership_relationship = relationshipLabel || undefined;
        }

        try {
            const response = await fetch('/api/chat-v2/ask', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData),
            });

            if (!response.ok) {
                const t = await response.text().catch(() => '');
                throw new Error(`chat-v2/ask failed: HTTP ${response.status} ${t}`);
            }

            const result = await response.json();
            console.log('[ChatPage] chat-v2/ask result', {
                message_id: result?.message_id,
                user_message_id: result?.user_message_id,
                chart_insights_count: result?.chart_insights?.length || 0,
            });

            const assistantMessageId = result.message_id;
            const serverUserMessageId = result.user_message_id;
            const chartInsights = Array.isArray(result.chart_insights) ? result.chart_insights : [];
            const loadingMessages = Array.isArray(result.loading_messages) ? result.loading_messages : [];

            setMessages(prev =>
                prev.map(m => (m.messageId === userMessageId ? { ...m, messageId: serverUserMessageId, isFromDatabase: true } : m))
            );

            setMessages(prev =>
                prev.map(m =>
                    m.processingClientId === processingClientId
                        ? {
                            ...m,
                            messageId: assistantMessageId,
                            chartInsights,
                            chartData: chartDataForMessage,
                            loadingMessage: loadingMessages[0] || m.loadingMessage,
                        }
                        : m
                )
            );

            pollChatV2Status(assistantMessageId, processingClientId).catch(() => {
                setIsLoading(false);
            });
        } catch (e) {
            console.error('[ChatPage] chat-v2/ask error:', e);
            setIsLoading(false);
            setMessages(prev =>
                prev.map(m =>
                    m.processingClientId === processingClientId
                        ? {
                            ...m,
                            content: 'I\'m having trouble processing your question right now. Please try again in a moment.',
                            isProcessing: false,
                            isTyping: false,
                            showRestartButton: true,
                        }
                        : m
                )
            );
        }
    };

    const handleSendMessage = async (message, options = {}) => {
        if (isMundaneMode) {
            // Mundane does not require birthData, but ChatInput is still wired to this component.
            await handleSendMundaneMessage(message, options);
            return;
        }
        if (!birthData) return;

        return handleSendMessageChatV2(message, options);

        const userMessage = { role: 'user', content: message, timestamp: new Date().toISOString(), messageId: Date.now() };
        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);
        let loadingTimer = null;
        const loadingMessages = [
            '🔮 Analyzing your birth chart...',
            '⭐ Consulting the cosmic energies...',
            '📊 Calculating planetary positions...',
            '🌟 Interpreting astrological patterns...',
            '✨ Preparing your personalized insights...',
            '🌙 Reading lunar influences...',
            '☀️ Examining solar aspects...',
            '♃ Studying Jupiter blessings...',
            '♀ Analyzing Venus placements...',
            '♂ Checking Mars energy...',
        ];
        // Insert the processing bubble immediately so it always paints (mobile-like UX).
        let assistantMessage = {
            role: 'assistant',
            content: '', // actual streamed response text comes in later
            loadingMessage: loadingMessages[0], // mobile-like rotating loading copy
            timestamp: new Date().toISOString(),
            messageId: Date.now() + 1,
            isProcessing: true,
            isTyping: true,
            message_type: 'answer',
        };
        const assistantMessageId = assistantMessage.messageId;
        setMessages(prev => [...prev, assistantMessage]);
        let hasReceivedContent = false;
        const streamStartAt = Date.now();
        let firstChunkSeen = false;
        console.log('[ChatPage] [STREAM] started', { at: new Date().toISOString() });

        try {
            // console.log('Sending chat request:', { ...birthData, question: message });
            
            const token = localStorage.getItem('token');
            // console.log('Token exists:', !!token);
            // console.log('Token preview:', token ? token.substring(0, 20) + '...' : 'No token');
            
            const requestBody = { ...birthData, question: message };
            if (isAdmin) {
                requestBody.include_context = true;
            }
            if (options.premium_analysis) {
                requestBody.premium_analysis = true;
            }
            if (isPartnershipMode && selectedPartnerChart) {
                requestBody.partnership_mode = true;
                requestBody.partner_data = {
                    name: selectedPartnerChart.name,
                    date: selectedPartnerChart.date,
                    time: selectedPartnerChart.time,
                    latitude: selectedPartnerChart.latitude,
                    longitude: selectedPartnerChart.longitude,
                    timezone: selectedPartnerChart.timezone
                };
            }
            
            const response = await fetch('/api/chat/ask', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify(requestBody)
            });

            // console.log('Response status:', response.status, response.statusText);
            // console.log('Response headers:', Object.fromEntries(response.headers.entries()));
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Response error:', errorText);
                console.error('Full response details:', {
                    status: response.status,
                    statusText: response.statusText,
                    url: response.url,
                    headers: Object.fromEntries(response.headers.entries()),
                    body: errorText
                });
                
                // If 401 Unauthorized, token is invalid - clear auth and redirect to login
                if (response.status === 401) {
                    console.log('🔐 401 error detected - invalid token, clearing auth...');
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    
                    // Show user-friendly message before redirect
                    setMessages(prev => {
                        const filtered = prev.filter(
                            msg =>
                                !(
                                    msg.role === 'assistant' &&
                                    !msg.isProcessing &&
                                    !msg.isTyping &&
                                    (!msg.content || !msg.content.trim())
                                )
                        );
                        return [...filtered, { 
                            role: 'assistant', 
                            content: "Your session has expired. Please log in again to continue.", 
                            timestamp: new Date().toISOString() 
                        }];
                    });
                    
                    // Redirect to login after a short delay
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                    return;
                }
                
                // If 402 Payment Required, refresh credit balance
                if (response.status === 402) {
                    console.log('🔄 402 error detected, refreshing credit balance...');
                    fetchBalance();
                }
                
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let streamTimeout;

            // Mobile-like dynamic "thinking" messages while streaming is in progress.
            loadingTimer = setInterval(() => {
                setMessages(prev => {
                    const idx = prev.findIndex(m => m.messageId === assistantMessage.messageId);
                    if (idx === -1) return prev;
                    const current = prev[idx];
                    if (!current || !current.isProcessing) return prev;
                    const nextContent = loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
                    const next = { ...current, loadingMessage: nextContent };
                    const updated = [...prev];
                    updated[idx] = next;
                    return updated;
                });
            }, 2200);
            
            // Mobile-friendly timeout for streaming
            const resetTimeout = () => {
                if (streamTimeout) clearTimeout(streamTimeout);
                streamTimeout = setTimeout(() => {
                    console.warn('Stream timeout - mobile network issue detected');
                    if (!hasReceivedContent) {
                        throw new Error('Stream timeout - please try again');
                    }
                }, 30000); // 30 second timeout
            };
            
            resetTimeout();

            try {
                let stopStreaming = false;
                // SSE chunks can arrive mid-line; buffer until we have full newline-delimited lines.
                let sseBuffer = '';
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    resetTimeout(); // Reset timeout on each chunk

                    const chunk = decoder.decode(value, { stream: true });
                    // Avoid logging huge payloads; length is enough for debugging streaming boundaries.
                    console.log('Received chunk:', { len: chunk.length });

                    sseBuffer += chunk;
                    const parts = sseBuffer.split('\n');
                    // Keep last partial line for the next read.
                    sseBuffer = parts.pop() || '';

                    for (const rawLine of parts) {
                        const line = rawLine.trim();
                        if (!line) continue;
                        if (line.startsWith('data:')) {
                            const data = line.slice(5).trim(); // supports both "data: " and "data:"
                            console.log('Processing data:', data);
                            
                            if (data === '[DONE]') break;
                            if (data && data.startsWith('{')) {
                                try {
                                    const parsed = JSON.parse(data);
                                    console.log('Parsed data:', parsed);
                                    console.log('[ChatPage] [STREAM EVENT]', {
                                        status: parsed?.status,
                                        at: new Date().toISOString(),
                                        elapsedMs: Date.now() - streamStartAt,
                                        hasResponse: typeof parsed?.response === 'string' && parsed.response.length > 0,
                                        hasMessage: typeof parsed?.message === 'string' && parsed.message.length > 0,
                                        keys: parsed && typeof parsed === 'object' ? Object.keys(parsed) : [],
                                    });

                                    if (parsed.status === 'context' && parsed.context) {
                                        // Backend sends initial chart/context before the actual streamed response.
                                        console.log('[ChatPage] [STREAM EVENT] context received', {
                                            contextStrLen: typeof parsed.context === 'string' ? parsed.context.length : null
                                        });

                                        const parsedContext = parsePythonLikeDictString(parsed.context);
                                        console.log('[ChatPage] [CONTEXT PARSED]', {
                                            ok: !!parsedContext,
                                            keys: parsedContext && typeof parsedContext === 'object' ? Object.keys(parsedContext) : [],
                                            hasD1: !!parsedContext?.d1_chart,
                                            hasD9: !!parsedContext?.d9_chart,
                                            hasBirthDetails: !!parsedContext?.birth_details,
                                        });

                                        if (parsedContext && (parsedContext.d1_chart || parsedContext.birth_details || parsedContext.d9_chart)) {
                                            if (loadingTimer) {
                                                // Keep rotating "thinking" text, but remove the skeleton content so chart summary shows.
                                                // (If you prefer rotating text to continue, we can keep it; this is just to reduce confusion.)
                                                // We do NOT clear the interval here to preserve UX.
                                            }

                                            assistantMessage = {
                                                ...assistantMessage,
                                                // Provide chart data for the skeleton UI.
                                                chartData: parsedContext.d1_chart || parsedContext.d9_chart || null,
                                                chartBirthData: parsedContext.birth_details || null,
                                                loadingMessage: assistantMessage.loadingMessage || loadingMessages[0],
                                                isProcessing: true,
                                                isTyping: true,
                                            };

                                            // Mark as received so we don't trip "empty response" due to chart-only payloads.
                                            hasReceivedContent = true;
                                            console.log('[ChatPage] [CHAT MESSAGE UPDATE] chartData set on processing bubble', {
                                                hasChartData: !!assistantMessage.chartData,
                                                ascHouse0Sign: assistantMessage.chartData?.houses?.[0]?.sign_name || null,
                                            });

                                            setMessages(prev => {
                                                const newMessages = [...prev];
                                                const idx = newMessages.findIndex(m => m.messageId === assistantMessageId);
                                                if (idx === -1) return prev;
                                                newMessages[idx] = { ...assistantMessage };
                                                return newMessages;
                                            });
                                        }

                                        continue;
                                    }

                                            if (parsed.status === 'clarification' && typeof parsed.message === 'string') {
                                                // Backend can short-circuit with a clarification question.
                                                if (loadingTimer) clearInterval(loadingTimer);
                                                assistantMessage = {
                                                    ...assistantMessage,
                                                    content: parsed.message,
                                                    loadingMessage: null,
                                                    isProcessing: false,
                                                    isTyping: false,
                                                    message_type: 'clarification',
                                                };
                                                hasReceivedContent = true;
                                                stopStreaming = true;
                                                setMessages(prev => {
                                                    const newMessages = [...prev];
                                                    const idx = newMessages.findIndex(m => m.messageId === assistantMessageId);
                                                    if (idx === -1) return prev;
                                                    newMessages[idx] = { ...assistantMessage };
                                                    return newMessages;
                                                });
                                                clearTimeout(streamTimeout);
                                                break;
                                            }

                                            if (parsed.status === 'chunk' && (typeof parsed.response === 'string')) {
                                                // Backend chunking sends {status:'chunk', response:<text>}
                                                if (!firstChunkSeen) {
                                                    firstChunkSeen = true;
                                                    // Once real streamed text starts, stop rotating generic placeholder.
                                                    if (loadingTimer) clearInterval(loadingTimer);
                                                    loadingTimer = null;
                                                    console.log('[ChatPage] [STREAM] first chunk received -> hiding loadingMessage');
                                                }
                                                assistantMessage = {
                                                    ...assistantMessage,
                                                    content: (assistantMessage.content || '') + parsed.response,
                                                    isProcessing: true,
                                                    isTyping: true,
                                                    loadingMessage: null,
                                                    terms: parsed.terms || assistantMessage.terms || [],
                                                    glossary: parsed.glossary || assistantMessage.glossary || {},
                                                    summary_image: parsed.summary_image || assistantMessage.summary_image || null,
                                                };
                                                hasReceivedContent = true;
                                                setMessages(prev => {
                                                    const newMessages = [...prev];
                                                    const idx = newMessages.findIndex(m => m.messageId === assistantMessageId);
                                                    if (idx === -1) return prev;
                                                    newMessages[idx] = { ...assistantMessage };
                                                    return newMessages;
                                                });
                                                continue;
                                            }

                                            if (parsed.status === 'complete') {
                                                // Some payloads only send {status:'complete'} without response
                                                if (typeof parsed.response === 'string') {
                                                    assistantMessage = {
                                                        ...assistantMessage,
                                                        content: parsed.response,
                                                        loadingMessage: null,
                                                        terms: parsed.terms || [],
                                                        glossary: parsed.glossary || {},
                                                        summary_image: parsed.summary_image || null,
                                                    };
                                                    hasReceivedContent = true;
                                                }

                                                if (loadingTimer) clearInterval(loadingTimer);
                                                assistantMessage = {
                                                    ...assistantMessage,
                                                    isProcessing: false,
                                                    isTyping: false,
                                                    loadingMessage: null,
                                                    message_type: parsed.message_type || assistantMessage.message_type || 'answer',
                                                };
                                                stopStreaming = true;
                                                setMessages(prev => {
                                                    const newMessages = [...prev];
                                                    const idx = newMessages.findIndex(m => m.messageId === assistantMessageId);
                                                    if (idx === -1) return prev;
                                                    newMessages[idx] = { ...assistantMessage };
                                                    return newMessages;
                                                });
                                                clearTimeout(streamTimeout);
                                                break;
                                            }

                                            if (parsed.status === 'error') {
                                                clearTimeout(streamTimeout);
                                                if (loadingTimer) clearInterval(loadingTimer);
                                                throw new Error(parsed.error || 'AI analysis failed');
                                            }

                                            if (parsed.content) {
                                                // Fallback for older frontend/backend formats.
                                                assistantMessage = {
                                                    ...assistantMessage,
                                                    content: (assistantMessage.content || '') + parsed.content,
                                                };
                                                hasReceivedContent = true;
                                                setMessages(prev => {
                                                    const newMessages = [...prev];
                                                    const idx = newMessages.findIndex(m => m.messageId === assistantMessageId);
                                                    if (idx === -1) return prev;
                                                    newMessages[idx] = { ...assistantMessage };
                                                    return newMessages;
                                                });
                                            }
                                } catch (parseError) {
                                    console.error('Error parsing chunk:', parseError, 'Data:', data);
                                }
                            }
                        }
                                if (stopStreaming) break;
                    }
                }

                // Flush any remaining buffered line content after the stream ends.
                const tail = sseBuffer.trim();
                if (tail.startsWith('data:')) {
                    const data = tail.slice(5).trim();
                    if (data && data.startsWith('{') && data !== '[DONE]') {
                        try {
                            const parsed = JSON.parse(data);
                            console.log('[ChatPage] [STREAM EVENT] tail flush', {
                                status: parsed?.status,
                                keys: parsed && typeof parsed === 'object' ? Object.keys(parsed) : [],
                            });
                            // Minimal handler: context chart setup (used for the "chart in progress" skeleton).
                            if (parsed?.status === 'context' && parsed?.context) {
                                const parsedContext = parsePythonLikeDictString(parsed.context);
                                if (parsedContext && (parsedContext.d1_chart || parsedContext.birth_details || parsedContext.d9_chart)) {
                                    assistantMessage = {
                                        ...assistantMessage,
                                        chartData: parsedContext.d1_chart || parsedContext.d9_chart || null,
                                        chartBirthData: parsedContext.birth_details || null,
                                        loadingMessage: assistantMessage.loadingMessage || loadingMessages[0],
                                        isProcessing: true,
                                        isTyping: true,
                                    };
                                    hasReceivedContent = true;
                                    setMessages(prev => {
                                        const newMessages = [...prev];
                                        const idx = newMessages.findIndex(m => m.messageId === assistantMessageId);
                                        if (idx === -1) return prev;
                                        newMessages[idx] = { ...assistantMessage };
                                        return newMessages;
                                    });
                                }
                            }
                        } catch (e) {
                            console.warn('[ChatPage] [STREAM] tail JSON parse failed', { message: e?.message });
                        }
                    }
                }
            } finally {
                clearTimeout(streamTimeout);
            }
            
            // Final validation
            if (!hasReceivedContent || !assistantMessage.content.trim()) {
                console.error('Empty response detected:', { hasReceivedContent, content: assistantMessage.content });
                throw new Error('Empty response received - please try again');
            }
            
            // Update credit balance after successful response
            fetchBalance();
        } catch (error) {
            if (loadingTimer) clearInterval(loadingTimer);
            loadingTimer = null;
            console.error('Complete error details:', {
                message: error.message,
                stack: error.stack,
                birthData: birthData,
                question: message,
                userAgent: navigator.userAgent,
                isMobile: /Mobi|Android/i.test(navigator.userAgent),
                hasToken: !!localStorage.getItem('token'),
                tokenPreview: localStorage.getItem('token') ? localStorage.getItem('token').substring(0, 20) + '...' : 'No token'
            });
            
            // Show generic user-friendly error messages
            let errorMessage = "I'm having trouble processing your question right now. Please try again in a moment.";
            
            if (error.message.includes('quota') || error.message.includes('rate limit')) {
                errorMessage = "I'm receiving too many requests right now. Please wait a moment and try again.";
            } else if (error.message.includes('network') || error.message.includes('connection')) {
                errorMessage = "Please check your internet connection and try again.";
            } else if (error.message.includes('timeout')) {
                errorMessage = "Your request is taking longer than expected. Please try again.";
            }
            
            // Update the existing processing assistant bubble (avoid inserting a second one).
            setMessages(prev => {
                const assistantIdxFromEnd = [...prev].reverse().findIndex(m => m.role === 'assistant');
                if (assistantIdxFromEnd === -1) {
                    return [...prev, { role: 'assistant', content: errorMessage, loadingMessage: null, timestamp: new Date().toISOString() }];
                }
                const idx = prev.length - 1 - assistantIdxFromEnd;
                const next = [...prev];
                next[idx] = {
                    ...next[idx],
                    content: errorMessage,
                    loadingMessage: null,
                    isProcessing: false,
                    isTyping: false,
                    message_type: 'answer',
                };
                return next;
            });
        } finally {
            setIsLoading(false);
            if (loadingTimer) clearInterval(loadingTimer);
            loadingTimer = null;
            // Ensure no empty bubbles remain (but keep the processing bubble during streaming)
            setTimeout(() => {
                setMessages(prev =>
                    prev.filter(
                        msg =>
                            !(
                                msg.role === 'assistant' &&
                                !msg.isProcessing &&
                                !msg.isTyping &&
                                (!msg.content || !msg.content.trim())
                            )
                    )
                );
            }, 1000);
        }
    };

    const handleSelectPartner = (chart) => {
        if (partnerModalMode === 'wizard-first') {
            setWizardPrimaryChart(chart);
            setWizardSecondaryChart(null);
            setWizardRelationshipText('');
            setWizardRelationshipSubStep(0);
            setWizardRelationshipOtherMode(false);
            setWizardRelationshipOtherText('');
            setWizardPartnershipStep(2);
            return;
        }

        if (partnerModalMode === 'wizard-second') {
            if (wizardPrimaryChart?.id && chart?.id && wizardPrimaryChart.id === chart.id) {
                return;
            }
            setWizardSecondaryChart(chart);
            setSelectedPartnerChart(chart); // keep existing references in header/components
            setWizardRelationshipText('');
            setWizardRelationshipSubStep(0);
            setWizardRelationshipOtherMode(false);
            setWizardRelationshipOtherText('');
            setWizardPartnershipStep(3);
        }
    };

    const handleDeleteMessage = (messageId) => {
        setMessages(prev => prev.filter(msg => msg.messageId !== messageId));
    };

    return (
        <>
            <NavigationHeader
                compact
                variant="chat"
                user={headerUser}
                birthData={birthData}
                onChangeNative={() => setShowBirthFormModal(true)}
                onCreditsClick={() => setShowCreditsModal(true)}
                onLogout={() => {
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    setHeaderUser(null);
                    navigate('/');
                }}
                onLogin={() => navigate('/login')}
                showLoginButton={!headerUser}
            />
            <div className={`chat-page${wizardCompleted ? '' : ' chat-page--wizard'}`}>
            <div className={`chat-header${wizardCompleted ? '' : ' chat-header--wizard'}`}>
                {!wizardCompleted ? (
                    <div className="chat-wizard-flow">
                        <div className="chat-wizard-intro">
                            <h1 className="chat-wizard-intro__title">AstroRoshni Guided Setup</h1>
                            <p className="chat-wizard-intro__text">
                                Choose your analysis type below. The chat unlocks only after you complete the guided steps.
                            </p>
                        </div>
                        <div className="wizard-mode-grid">
                        <button
                            type="button"
                            className={`wizard-mode-card ${wizardMode === 'single' ? 'active' : ''}`}
                            onClick={() => {
                                resetThreadForWizard('single');
                                setWizardMode('single');
                                setWizardStep(1);
                            }}
                        >
                            <div className="wizard-mode-title">✨ Single Chart</div>
                            <div className="wizard-mode-subtitle">Your birth chart + your life guidance</div>
                        </button>
                        <button
                            type="button"
                            className={`wizard-mode-card ${wizardMode === 'partnership' ? 'active' : ''}`}
                            onClick={() => {
                                resetThreadForWizard('partnership');
                                setWizardMode('partnership');
                                setWizardStep(1);
                            }}
                        >
                            <div className="wizard-mode-title">💞 Partnership</div>
                            <div className="wizard-mode-subtitle">Two charts + relationship insights</div>
                        </button>
                        <button
                            type="button"
                            className={`wizard-mode-card ${wizardMode === 'mundane' ? 'active' : ''}`}
                            onClick={() => {
                                resetThreadForWizard('mundane');
                                setWizardMode('mundane');
                                setWizardStep(1);
                            }}
                        >
                            <div className="wizard-mode-title">🌍 Mundane</div>
                            <div className="wizard-mode-subtitle">Global events + trend dynamics</div>
                        </button>
                        </div>
                        <div className="wizard-step">
                        {wizardMode === 'single' && (
                            <>
                                <div className="wizard-step-title">Single Chart — set up this session</div>
                                {isBirthChartReadyForChat(birthData) ? (
                                    <div className="wizard-inline-card wizard-inline-card--single-ready">
                                        <p className="single-chart-intro">
                                            <span className="single-chart-intro__badge" aria-hidden="true">
                                                ✨
                                            </span>
                                            <span>
                                                You’re in <strong>Single Chart</strong> mode — every reply is cast for <strong>one</strong> birth
                                                chart. This is the profile we’ll use for this session.
                                            </span>
                                        </p>
                                        <div className="single-chart-profile-panel" role="group" aria-label="Selected birth chart">
                                            <div className="single-chart-profile-panel__top">
                                                <span className="single-chart-profile-panel__label">Chart for this session</span>
                                            </div>
                                            <div className="single-chart-profile-row">
                                                <div className="single-chart-profile-main">
                                                    <div className="single-chart-avatar" aria-hidden="true">
                                                        {singleChartWizardProfile.initials}
                                                    </div>
                                                    <div className="single-chart-profile-copy">
                                                        <p className="single-chart-profile-name">{singleChartWizardProfile.name}</p>
                                                        <p className="single-chart-profile-meta">{singleChartWizardProfile.metaLine}</p>
                                                    </div>
                                                </div>
                                                <button
                                                    type="button"
                                                    className="single-chart-change-btn"
                                                    onClick={() => setShowBirthFormModal(true)}
                                                >
                                                    Change chart
                                                </button>
                                            </div>
                                        </div>
                                        <button
                                            type="button"
                                            className="wizard-primary-btn single-chart-start-btn"
                                            onClick={() => {
                                                setIsPartnershipMode(false);
                                                setIsMundaneMode(false);
                                                setWizardCompleted(true);
                                            }}
                                        >
                                            Start chat with this chart
                                        </button>
                                    </div>
                                ) : (
                                    <div className="wizard-inline-card wizard-inline-card--single-setup">
                                        <p className="single-chart-setup-title">Personal chart Q&amp;A</p>
                                        <p className="single-chart-setup-lead">
                                            Choose <strong>Single Chart</strong> when you want answers from <strong>your</strong> horoscope — houses,
                                            dasha, and timing — not generic astrology. Add your date, time, and place once (saved chart or new).
                                        </p>
                                        <button
                                            type="button"
                                            className="wizard-primary-btn single-chart-setup-cta"
                                            onClick={() => setShowBirthFormModal(true)}
                                        >
                                            Choose or add birth chart…
                                        </button>
                                        <p className="single-chart-setup-hint">
                                            After your chart is saved, tap <strong>Start chat with this chart</strong> to begin.
                                        </p>
                                    </div>
                                )}
                            </>
                        )}

                        {wizardMode === 'partnership' && (
                            <>
                                <div className="wizard-step-title">Step 1-3: Select first chart, second chart, then relationship type</div>
                                {(wizardPrimaryChart && wizardSecondaryChart && isRelationshipReady()) ? (
                                    <div className="wizard-inline-card">
                                        <div style={{ fontWeight: 700, marginBottom: 6 }}>
                                            {wizardPrimaryChart.name} + {wizardSecondaryChart.name}
                                        </div>
                                        <div style={{ color: '#374151', fontSize: 13, lineHeight: 1.5, marginBottom: 6 }}>
                                            Relationship type: <strong>{wizardRelationshipText}</strong>
                                        </div>
                                        <div style={{ color: '#555', fontSize: 13, lineHeight: 1.5 }}>
                                            Why this matters: partnership analysis needs both natal charts plus relationship context for accurate guidance.
                                        </div>
                                        <div style={{ marginTop: 12 }}>
                                            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8, color: '#111827' }}>
                                                Suggested questions for this relationship:
                                            </div>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                                {getRelationshipSuggestedQuestions().map((q, idx) => (
                                                    <button
                                                        key={idx}
                                                        type="button"
                                                        className="wizard-secondary-btn"
                                                        style={{
                                                            textAlign: 'left',
                                                            justifyContent: 'flex-start',
                                                            fontSize: 12,
                                                            color: '#4b5563',
                                                            background: 'rgba(17,24,39,0.03)',
                                                            border: '1px solid rgba(0,0,0,0.06)',
                                                            borderRadius: 8,
                                                            padding: '6px 8px'
                                                        }}
                                                        onClick={() => setPendingFollowUpQuestion(q)}
                                                    >
                                                        {q}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                        <div style={{ marginTop: 12, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                                            <button
                                                className="wizard-primary-btn"
                                                onClick={() => {
                                                    setIsPartnershipMode(true);
                                                    setIsMundaneMode(false);
                                                    setWizardCompleted(true);
                                                }}
                                            >
                                                Start partnership chat
                                            </button>
                                            <button
                                                className="wizard-secondary-btn"
                                                onClick={() => {
                                                    setWizardPartnershipStep(1);
                                                    setWizardPrimaryChart(null);
                                                    setWizardSecondaryChart(null);
                                                    setWizardRelationshipText('');
                                                    setWizardRelationshipSubStep(0);
                                                    setWizardRelationshipOtherMode(false);
                                                    setWizardRelationshipOtherText('');
                                                    setSelectedPartnerChart(null);
                                                }}
                                            >
                                                Restart setup
                                            </button>
                                        </div>
                                        <div style={{ marginTop: 10 }}>
                                            <button
                                                className="wizard-link-btn"
                                                onClick={() => {
                                                    setWizardPartnershipStep(1);
                                                    setPartnerModalMode('wizard-first');
                                                    setShowPartnerModal(true);
                                                }}
                                            >
                                                Change charts
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="wizard-inline-card">
                                        <div style={{ color: '#555', fontSize: 13, lineHeight: 1.5, marginBottom: 10 }}>
                                            Complete each step to configure partnership analysis.
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                            <div style={{ border: '1px solid rgba(0,0,0,0.08)', borderRadius: 10, padding: 10, background: 'rgba(255,255,255,0.8)' }}>
                                                <div style={{ fontSize: 12, color: '#6b7280', fontWeight: 700 }}>Step 1</div>
                                                <div style={{ fontSize: 13, color: '#111827', fontWeight: 700 }}>
                                                    First chart: {wizardPrimaryChart ? wizardPrimaryChart.name : 'Not selected'}
                                                </div>
                                                <button
                                                    className="wizard-link-btn"
                                                    onClick={() => {
                                                        setPartnerModalMode('wizard-first');
                                                        setShowPartnerModal(true);
                                                    }}
                                                >
                                                    {wizardPrimaryChart ? 'Change first chart' : 'Select first chart'}
                                                </button>
                                            </div>

                                            <div style={{ border: '1px solid rgba(0,0,0,0.08)', borderRadius: 10, padding: 10, background: 'rgba(255,255,255,0.8)', opacity: wizardPrimaryChart ? 1 : 0.6 }}>
                                                <div style={{ fontSize: 12, color: '#6b7280', fontWeight: 700 }}>Step 2</div>
                                                <div style={{ fontSize: 13, color: '#111827', fontWeight: 700 }}>
                                                    Second chart: {wizardSecondaryChart ? wizardSecondaryChart.name : 'Not selected'}
                                                </div>
                                                <button
                                                    className="wizard-link-btn"
                                                    disabled={!wizardPrimaryChart}
                                                    onClick={() => {
                                                        if (!wizardPrimaryChart) return;
                                                        setPartnerModalMode('wizard-second');
                                                        setShowPartnerModal(true);
                                                    }}
                                                >
                                                    {wizardSecondaryChart ? 'Change second chart' : 'Select second chart'}
                                                </button>
                                            </div>

                                            <div style={{ border: '1px solid rgba(0,0,0,0.08)', borderRadius: 10, padding: 10, background: 'rgba(255,255,255,0.8)', opacity: wizardSecondaryChart ? 1 : 0.6 }}>
                                                <div style={{ fontSize: 12, color: '#6b7280', fontWeight: 700 }}>Step 3</div>
                                                <div style={{ fontSize: 13, color: '#111827', fontWeight: 700, marginBottom: 8 }}>
                                                    Relationship type: {wizardRelationshipText || 'Not selected'}
                                                </div>
                                                {!wizardRelationshipOtherMode && (
                                                    <>
                                                        {(() => {
                                                            const activePreset = getActiveRelationshipPreset();
                                                            if (activePreset && activePreset.subSteps && wizardRelationshipSubStep < activePreset.subSteps.length) {
                                                                const subStep = activePreset.subSteps[wizardRelationshipSubStep];
                                                                const options = subStep.options(wizardPrimaryChart, wizardSecondaryChart);
                                                                return (
                                                                    <>
                                                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                                                            <div style={{ fontSize: 12, color: '#ff6b35', fontWeight: 700 }}>
                                                                                {subStep.prompt}
                                                                            </div>
                                                                            <button
                                                                                type="button"
                                                                                className="wizard-link-btn"
                                                                                onClick={handleRelationshipBack}
                                                                            >
                                                                                Back
                                                                            </button>
                                                                        </div>
                                                                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                                                            {options.map((opt, idx) => (
                                                                                <button
                                                                                    key={`${activePreset.label}-${idx}`}
                                                                                    type="button"
                                                                                    className="wizard-secondary-btn"
                                                                                    disabled={!wizardSecondaryChart}
                                                                                    onClick={() => {
                                                                                        if (!wizardSecondaryChart) return;
                                                                                        handleRelationshipSelect(opt);
                                                                                    }}
                                                                                >
                                                                                    {opt.label}
                                                                                </button>
                                                                            ))}
                                                                        </div>
                                                                    </>
                                                                );
                                                            }

                                                            return (
                                                                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                                                    {RELATIONSHIP_PRESETS.map((preset) => (
                                                                        <button
                                                                            key={preset.label}
                                                                            type="button"
                                                                            className={`wizard-secondary-btn ${(wizardRelationshipText === preset.label || wizardRelationshipText.startsWith(`${preset.label}:`)) ? 'active' : ''}`}
                                                                            disabled={!wizardSecondaryChart}
                                                                            onClick={() => {
                                                                                if (!wizardSecondaryChart) return;
                                                                                handleRelationshipPresetSelect(preset.label);
                                                                            }}
                                                                        >
                                                                            {preset.label}
                                                                        </button>
                                                                    ))}
                                                                </div>
                                                            );
                                                        })()}
                                                    </>
                                                )}
                                                {wizardRelationshipOtherMode && (
                                                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                                                        <input
                                                            value={wizardRelationshipOtherText}
                                                            onChange={(e) => setWizardRelationshipOtherText(e.target.value)}
                                                            className="wizard-input"
                                                            placeholder="Type relationship (e.g., Mentor, Distant cousin)"
                                                            style={{ minWidth: 260 }}
                                                        />
                                                        <button
                                                            type="button"
                                                            className="wizard-primary-btn"
                                                            disabled={!wizardRelationshipOtherText.trim()}
                                                            onClick={() => {
                                                                if (!wizardRelationshipOtherText.trim()) return;
                                                                setWizardRelationshipText(wizardRelationshipOtherText.trim());
                                                                setWizardRelationshipSubStep(999);
                                                                setWizardRelationshipOtherMode(false);
                                                            }}
                                                        >
                                                            Done
                                                        </button>
                                                        <button
                                                            type="button"
                                                            className="wizard-link-btn"
                                                            onClick={() => {
                                                                setWizardRelationshipOtherMode(false);
                                                                setWizardRelationshipOtherText('');
                                                            }}
                                                        >
                                                            Back
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}

                        {wizardMode === 'mundane' && (
                            <>
                                <div className="wizard-step-title">Step: Configure the global event context</div>
                                <div className="wizard-inline-card">
                                    <div className="wizard-field">
                                        <label>Country/Region</label>
                                        <input
                                            value={mundaneForm.country}
                                            onChange={(e) => setMundaneForm((p) => ({ ...p, country: e.target.value }))}
                                            className="wizard-input"
                                            placeholder="e.g., India, USA, Europe"
                                        />
                                    </div>
                                    <div className="wizard-field">
                                        <label>Category</label>
                                        <select
                                            value={mundaneForm.category}
                                            onChange={(e) => setMundaneForm((p) => ({ ...p, category: e.target.value }))}
                                            className="wizard-input"
                                        >
                                            <option value="general">general</option>
                                            <option value="sports">sports</option>
                                            <option value="markets">markets</option>
                                            <option value="wars">wars</option>
                                        </select>
                                    </div>
                                    <div className="wizard-field">
                                        <label>Year (optional)</label>
                                        <input
                                            value={mundaneForm.year}
                                            onChange={(e) => setMundaneForm((p) => ({ ...p, year: e.target.value }))}
                                            className="wizard-input"
                                            placeholder="e.g., 2026"
                                        />
                                    </div>
                                    <div className="wizard-field">
                                        <label>Event date (optional)</label>
                                        <input
                                            value={mundaneForm.eventDate}
                                            onChange={(e) => setMundaneForm((p) => ({ ...p, eventDate: e.target.value }))}
                                            className="wizard-input"
                                            type="date"
                                        />
                                    </div>
                                    <div className="wizard-field">
                                        <label>Event time (optional)</label>
                                        <input
                                            value={mundaneForm.eventTime}
                                            onChange={(e) => setMundaneForm((p) => ({ ...p, eventTime: e.target.value }))}
                                            className="wizard-input"
                                            type="time"
                                        />
                                    </div>
                                    <div className="wizard-field">
                                        <label>Entities (optional, comma-separated)</label>
                                        <input
                                            value={mundaneForm.entitiesRaw}
                                            onChange={(e) => setMundaneForm((p) => ({ ...p, entitiesRaw: e.target.value }))}
                                            className="wizard-input"
                                            placeholder="e.g., teams, indices, or countries"
                                        />
                                    </div>
                                    <div className="wizard-field">
                                        <label>Event place (search)</label>
                                        <input
                                            value={mundaneForm.placeQuery}
                                            onChange={(e) => setMundaneForm((p) => ({ ...p, placeQuery: e.target.value }))}
                                            className="wizard-input"
                                            placeholder="Type a place and pick one"
                                        />
                                        {mundaneForm.placeLoading && <div style={{ fontSize: 12, marginTop: 6, color: '#666' }}>Searching...</div>}
                                        {!!mundaneForm.placeSuggestions.length && (
                                            <div className="wizard-suggestions">
                                                {mundaneForm.placeSuggestions.map((s) => (
                                                    <button
                                                        type="button"
                                                        key={s.id}
                                                        className="wizard-suggestion-btn"
                                                        onClick={() => {
                                                            setMundaneForm((p) => ({
                                                                ...p,
                                                                latitude: s.latitude,
                                                                longitude: s.longitude,
                                                                placeQuery: s.name,
                                                                placeSuggestions: [],
                                                            }));
                                                        }}
                                                    >
                                                        {s.name}
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                        {mundaneForm.latitude && mundaneForm.longitude && (
                                            <div style={{ fontSize: 12, marginTop: 6, color: '#666' }}>
                                                Selected coordinates: {mundaneForm.latitude.toFixed(3)}, {mundaneForm.longitude.toFixed(3)}
                                            </div>
                                        )}
                                    </div>
                                    <div style={{ marginTop: 12 }}>
                                        <button
                                            className="wizard-primary-btn"
                                            onClick={() => {
                                                if (!mundaneForm.country || !mundaneForm.latitude || !mundaneForm.longitude) return;
                                                setIsMundaneMode(true);
                                                setIsPartnershipMode(false);
                                                setWizardCompleted(true);
                                            }}
                                        >
                                            Start mundane chat
                                        </button>
                                    </div>
                                    <div style={{ marginTop: 10, fontSize: 12, color: '#666', lineHeight: 1.4 }}>
                                        Why this matters: the event place/time changes the chart framework used for predictions.
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                    </div>
                ) : (
                    <div className="chat-header-toolbar">
                        <div className="chat-header-toolbar__info">
                            {(isMundaneMode || isPartnershipMode) && (
                                <div className="chat-header-toolbar__mode-chip" aria-hidden="true">
                                    {isMundaneMode ? 'Mundane' : 'Partnership'}
                                </div>
                            )}
                            <h1 className="chat-header-toolbar__title">
                                {isPartnershipMode && wizardPrimaryChart && wizardSecondaryChart ? (
                                    <span className="chat-header-toolbar__title-focus">
                                        {`${wizardPrimaryChart.name} & ${wizardSecondaryChart.name}`}
                                    </span>
                                ) : isMundaneMode ? (
                                    <span className="chat-header-toolbar__title-focus">
                                        {birthData?.name || 'Consultation'}
                                    </span>
                                ) : (
                                    <button
                                        type="button"
                                        className="native-selector-chip chat-header-native-chip"
                                        onClick={() => setShowBirthFormModal(true)}
                                        title="Change birth chart / native"
                                        aria-haspopup="dialog"
                                        aria-label={`Selected native ${birthData?.name || 'chart'}. Choose a different chart.`}
                                    >
                                        <span className="native-selector-chip__icon" aria-hidden="true">
                                            👤
                                        </span>
                                        <span className="native-selector-chip__name">
                                            {(birthData?.name && String(birthData.name).trim()) ||
                                                'Select chart'}
                                        </span>
                                        <span className="native-selector-chip__chevron" aria-hidden="true">
                                            ▾
                                        </span>
                                    </button>
                                )}
                            </h1>
                            {(isMundaneMode || isPartnershipMode) && (
                                <p className="chat-header-toolbar__meta chat-header-toolbar__meta--desktop">
                                    {isMundaneMode ? 'Mundane context' : 'Two-chart analysis'}
                                </p>
                            )}
                        </div>
                        <div className="chat-header-toolbar__actions">
                            <button
                                type="button"
                                className="chat-header-btn"
                                title="Change analysis type"
                                onClick={() => {
                                    resetThreadForWizard(null);
                                    setWizardMode(null);
                                    setWizardStep(0);
                                }}
                            >
                                <span className="chat-header-btn__full">Change type</span>
                                <span className="chat-header-btn__icon" aria-hidden="true">↻</span>
                            </button>
                            {isAdmin && (
                                <button
                                    type="button"
                                    className="chat-header-btn"
                                    title="View Gemini context payload (admin)"
                                    onClick={() => setShowContextModal(true)}
                                >
                                    <span className="chat-header-btn__full">Context</span>
                                    <span className="chat-header-btn__icon" aria-hidden="true">☰</span>
                                </button>
                            )}
                            <button
                                type="button"
                                className="credits-display chat-header-credits"
                                title="Credits and per-question cost"
                                aria-label="Open credits"
                                onClick={() => setShowCreditsModal(true)}
                            >
                                <span className="credits-full">{credits} · {isPartnershipMode ? partnershipCost : chatCost}/q</span>
                                <span className="credits-short">{credits}</span>
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <div className="chat-container">
                {wizardCompleted ? (
                    <div className="chat-thread">
                        {!isMundaneMode && isBirthChartReadyForChat(birthData) && (
                            <div className="message-bubble assistant chat-chart-essence-wrap">
                                <div className="message-content chat-chart-essence-wrap__content">
                                    <ChatChartEssence
                                        chartData={personalChartData}
                                        dashaData={chatDashaData}
                                        personName={birthData?.name}
                                        isLoading={chartEssenceLoading}
                                    />
                                </div>
                            </div>
                        )}
                        <MessageList
                            messages={messages}
                            sessionId={isMundaneMode ? mundaneSessionId : chatV2SessionId}
                            onFollowUpClick={(q) => setPendingFollowUpQuestion(q)}
                            onDeleteMessage={handleDeleteMessage}
                        />
                        <div ref={messagesEndRef} />
                    </div>
                ) : (
                    <div className="wizard-placeholder">
                        {/* Wizard UI is rendered inside the header. Keep the thread area empty to avoid confusion. */}
                    </div>
                )}
            </div>

            {/* No mode chosen yet — hide composer (premium row + placeholder) so setup stays the only focus */}
            {(wizardCompleted || wizardMode) && (
                <ChatInput
                    onSendMessage={handleSendMessage}
                    isLoading={isLoading}
                    followUpQuestion={pendingFollowUpQuestion}
                    onFollowUpUsed={() => setPendingFollowUpQuestion('')}
                    onOpenCreditsModal={() => setShowCreditsModal(true)}
                    isPartnershipMode={isPartnershipMode}
                    isMundaneMode={isMundaneMode}
                    isLocked={isWizardLocked}
                />
            )}

            {/* Credits Modal */}
            <CreditsModal 
                isOpen={showCreditsModal} 
                onClose={() => setShowCreditsModal(false)} 
            />
            
            {/* Context Modal for Admin */}
            <ContextModal 
                isOpen={showContextModal}
                onClose={() => setShowContextModal(false)}
                contextData={contextData}
            />
            
            {/* Partner Chart Selection Modal */}
            <PartnerChartModal 
                isOpen={showPartnerModal}
                onClose={() => setShowPartnerModal(false)}
                onSelectPartner={handleSelectPartner}
            />

                <BirthFormModal
                    isOpen={showBirthFormModal}
                    onClose={() => setShowBirthFormModal(false)}
                    onSubmit={() => {
                        setChatV2SessionId(null); // refresh chat-v2 session for newly selected native
                    }}
                    title="Birth chart for chat"
                    description="Select a saved chart or enter details. This sets the chart used for Single Chart answers."
                />
            </div>
        </>
    );
};

export default ChatPage;