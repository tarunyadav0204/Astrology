import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { apiService } from '../services/apiService';

const STORAGE_KEY = 'astroroshni_instant_billing_session';
const CLIENT_KEY = 'astroroshni_instant_billing_client';

const getClientId = () => {
    let id = localStorage.getItem(CLIENT_KEY);
    if (!id) {
        id = `web_${Date.now()}_${Math.random().toString(36).slice(2)}`;
        localStorage.setItem(CLIENT_KEY, id);
    }
    return id;
};

const errorMessage = (error) => {
    const detail = error?.response?.data?.detail;
    return detail?.message || detail || error?.message || 'Instant Chat could not be updated.';
};

export default function useInstantBillingSession({ refreshBalance }) {
    const [serverState, setServerState] = useState(null);
    const [displayState, setDisplayState] = useState(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const receivedAtRef = useRef(0);
    const heartbeatBusyRef = useRef(false);

    const acceptState = useCallback((next) => {
        if (!next) return;
        receivedAtRef.current = Date.now();
        setServerState(next);
        setDisplayState(next);
        if (next.status === 'active') localStorage.setItem(STORAGE_KEY, next.session_id);
        else localStorage.removeItem(STORAGE_KEY);
    }, []);

    const heartbeat = useCallback(async (sessionIdOverride) => {
        const sessionId = sessionIdOverride || serverState?.session_id || localStorage.getItem(STORAGE_KEY);
        if (!sessionId || heartbeatBusyRef.current) return null;
        heartbeatBusyRef.current = true;
        try {
            const next = await apiService.heartbeatInstantChatSession(sessionId);
            acceptState(next);
            setError('');
            refreshBalance?.();
            return next;
        } catch (err) {
            setError(errorMessage(err));
            if ([402, 404, 409].includes(err?.response?.status)) localStorage.removeItem(STORAGE_KEY);
            return null;
        } finally {
            heartbeatBusyRef.current = false;
        }
    }, [acceptState, refreshBalance, serverState?.session_id]);

    const start = useCallback(async (chatSessionId) => {
        if (!chatSessionId) throw new Error('A conversation is required before Instant Chat can start.');
        setBusy(true);
        setError('');
        try {
            const next = await apiService.startInstantChatSession({
                chatSessionId,
                clientInstanceId: getClientId(),
            });
            acceptState(next);
            refreshBalance?.();
            return next;
        } catch (err) {
            const message = errorMessage(err);
            setError(message);
            throw new Error(message);
        } finally {
            setBusy(false);
        }
    }, [acceptState, refreshBalance]);

    const end = useCallback(async (reason = 'user_ended') => {
        const sessionId = serverState?.session_id || localStorage.getItem(STORAGE_KEY);
        if (!sessionId) return null;
        setBusy(true);
        setError('');
        try {
            const next = await apiService.endInstantChatSession(sessionId, reason);
            acceptState(next);
            refreshBalance?.();
            return next;
        } catch (err) {
            const message = errorMessage(err);
            setError(message);
            throw new Error(message);
        } finally {
            setBusy(false);
        }
    }, [acceptState, refreshBalance, serverState?.session_id]);

    useEffect(() => {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) heartbeat(stored);
        // Recovery happens once. Recurring heartbeats are installed below.
    }, []);

    useEffect(() => {
        if (serverState?.status !== 'active') return undefined;
        const intervalSeconds = Math.max(5, Number(serverState.heartbeat_interval_seconds || 10));
        const timer = setInterval(() => heartbeat(), intervalSeconds * 1000);
        const onVisibility = () => {
            if (document.visibilityState === 'visible') heartbeat();
        };
        document.addEventListener('visibilitychange', onVisibility);
        return () => {
            clearInterval(timer);
            document.removeEventListener('visibilitychange', onVisibility);
        };
    }, [heartbeat, serverState?.heartbeat_interval_seconds, serverState?.status]);

    useEffect(() => {
        if (!serverState) return undefined;
        const tick = () => {
            if (serverState.status !== 'active') {
                setDisplayState(serverState);
                return;
            }
            const delta = Math.max(0, Math.floor((Date.now() - receivedAtRef.current) / 1000));
            setDisplayState({
                ...serverState,
                elapsed_seconds: Number(serverState.elapsed_seconds || 0) + delta,
                remaining_seconds: Math.max(0, Number(serverState.remaining_seconds || 0) - delta),
            });
        };
        tick();
        const timer = setInterval(tick, 1000);
        return () => clearInterval(timer);
    }, [serverState]);

    return useMemo(() => ({
        state: displayState,
        active: displayState?.status === 'active',
        busy,
        error,
        clearError: () => setError(''),
        start,
        end,
        heartbeat,
    }), [busy, displayState, end, error, heartbeat, start]);
}
