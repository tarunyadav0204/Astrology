import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AppState, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { creditAPI } from '../services/api';

const SESSION_KEY = 'instant_billing_session_v1';
const CLIENT_KEY = 'instant_billing_client_v1';

const responseData = (response) => response?.data || response || null;

const readError = (error) => {
  const detail = error?.response?.data?.detail;
  return String(detail?.message || detail || error?.message || 'Live chat could not be updated.')
    .replace(/Instant Chat/gi, 'Live chat')
    .replace(/Instant consultation/gi, 'Live consultation');
};

const getClientId = async () => {
  let id = await AsyncStorage.getItem(CLIENT_KEY);
  if (!id) {
    id = `${Platform.OS}_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    await AsyncStorage.setItem(CLIENT_KEY, id);
  }
  return id;
};

export default function useInstantBillingSession({ refreshBalance }) {
  const [serverState, setServerState] = useState(null);
  const [displayState, setDisplayState] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const receivedAtRef = useRef(0);
  const heartbeatBusyRef = useRef(false);
  const endBusyRef = useRef(null);
  const serverStateRef = useRef(null);

  const acceptState = useCallback(async (next) => {
    if (!next) return;
    receivedAtRef.current = Date.now();
    serverStateRef.current = next;
    setServerState(next);
    setDisplayState(next);
    if (next.status === 'active') {
      await AsyncStorage.setItem(SESSION_KEY, String(next.session_id));
    } else {
      await AsyncStorage.removeItem(SESSION_KEY);
    }
  }, []);

  const heartbeat = useCallback(async (sessionIdOverride = null) => {
    if (heartbeatBusyRef.current) return null;
    const stored = sessionIdOverride || serverStateRef.current?.session_id || await AsyncStorage.getItem(SESSION_KEY);
    if (!stored) return null;
    heartbeatBusyRef.current = true;
    try {
      const response = await creditAPI.heartbeatInstantSession(stored);
      const next = responseData(response);
      await acceptState(next);
      setError('');
      refreshBalance?.();
      return next;
    } catch (err) {
      setError(readError(err));
      if ([402, 404, 409].includes(err?.response?.status)) {
        await AsyncStorage.removeItem(SESSION_KEY);
        serverStateRef.current = null;
        setServerState(null);
        setDisplayState(null);
      }
      return null;
    } finally {
      heartbeatBusyRef.current = false;
    }
  }, [acceptState, refreshBalance]);

  const start = useCallback(async (chatSessionId) => {
    if (!chatSessionId) throw new Error('A conversation is required before Live chat can start.');
    setBusy(true);
    setError('');
    try {
      const response = await creditAPI.startInstantSession(chatSessionId, await getClientId());
      const next = responseData(response);
      await acceptState(next);
      refreshBalance?.();
      return next;
    } catch (err) {
      const message = readError(err);
      setError(message);
      throw new Error(message);
    } finally {
      setBusy(false);
    }
  }, [acceptState, refreshBalance]);

  const end = useCallback(async (reason = 'user_ended') => {
    if (endBusyRef.current) return endBusyRef.current;
    const operation = (async () => {
      const stored = serverStateRef.current?.session_id || await AsyncStorage.getItem(SESSION_KEY);
      if (!stored) return null;
      setBusy(true);
      setError('');
      try {
        const response = await creditAPI.endInstantSession(stored, reason);
        const next = responseData(response);
        await acceptState(next);
        refreshBalance?.();
        return next;
      } catch (err) {
        const message = readError(err);
        setError(message);
        throw new Error(message);
      } finally {
        setBusy(false);
      }
    })();
    endBusyRef.current = operation;
    try {
      return await operation;
    } finally {
      endBusyRef.current = null;
    }
  }, [acceptState, refreshBalance]);

  useEffect(() => {
    AsyncStorage.getItem(SESSION_KEY).then((stored) => stored && heartbeat(stored));
  }, [heartbeat]);

  useEffect(() => {
    if (serverState?.status !== 'active') return undefined;
    const intervalSeconds = Math.max(5, Number(serverState.heartbeat_interval_seconds || 10));
    const timer = setInterval(() => heartbeat(), intervalSeconds * 1000);
    const subscription = AppState.addEventListener('change', (nextState) => {
      if (nextState === 'active') {
        heartbeat();
      } else {
        // Live is foreground-only. Locking or minimizing the app ends billing
        // immediately instead of silently consuming credits in the background.
        end('app_backgrounded').catch(() => {});
      }
    });
    return () => {
      clearInterval(timer);
      subscription?.remove?.();
    };
  }, [end, heartbeat, serverState?.heartbeat_interval_seconds, serverState?.status]);

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
