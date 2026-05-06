import AsyncStorage from '@react-native-async-storage/async-storage';

const LAST_RUNTIME_ISSUE_KEY = '@runtime_guard:last_issue';

let installed = false;
let currentFatalIssue = null;
let previousGlobalHandler = null;
const fatalListeners = new Set();

function notifyFatalListeners() {
  for (const listener of fatalListeners) {
    try {
      listener(currentFatalIssue);
    } catch (listenerError) {
      console.warn('[RuntimeGuard] Failed to notify listener:', listenerError);
    }
  }
}

function stringifyError(input) {
  if (input instanceof Error) {
    return input.stack || `${input.name}: ${input.message}`;
  }

  if (typeof input === 'string') {
    return input;
  }

  try {
    return JSON.stringify(input);
  } catch (error) {
    return String(input);
  }
}

function normalizeIssue(error, options = {}) {
  const { fatal = false, source = 'unknown', metadata = null } = options;

  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    source,
    fatal,
    timestamp: new Date().toISOString(),
    name: error?.name || 'Error',
    message: error?.message || stringifyError(error),
    stack: error?.stack || stringifyError(error),
    metadata,
  };
}

async function persistIssue(issue) {
  try {
    await AsyncStorage.setItem(LAST_RUNTIME_ISSUE_KEY, JSON.stringify(issue));
  } catch (storageError) {
    if (__DEV__) {
      console.warn('[RuntimeGuard] Failed to persist runtime issue:', storageError);
    }
  }
}

export async function recordRuntimeIssue(error, options = {}) {
  const issue = normalizeIssue(error, options);
  await persistIssue(issue);

  if (issue.fatal) {
    currentFatalIssue = issue;
    notifyFatalListeners();
  }

  if (__DEV__) {
    const level = issue.fatal ? 'error' : 'warn';
    console[level](`[RuntimeGuard] ${issue.source}: ${issue.message}`, error);
  }

  return issue;
}

export function subscribeToFatalRuntimeError(listener) {
  fatalListeners.add(listener);
  listener(currentFatalIssue);

  return () => {
    fatalListeners.delete(listener);
  };
}

export async function getLastRuntimeIssue() {
  try {
    const raw = await AsyncStorage.getItem(LAST_RUNTIME_ISSUE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

export async function clearFatalRuntimeError() {
  currentFatalIssue = null;
  notifyFatalListeners();
}

export function installRuntimeGuard() {
  if (installed) {
    return;
  }
  installed = true;

  if (global.ErrorUtils?.getGlobalHandler && global.ErrorUtils?.setGlobalHandler) {
    previousGlobalHandler = global.ErrorUtils.getGlobalHandler();

    global.ErrorUtils.setGlobalHandler((error, isFatal) => {
      recordRuntimeIssue(error, {
        fatal: Boolean(isFatal),
        source: 'global_js',
      }).catch(() => {});

      if (__DEV__ && typeof previousGlobalHandler === 'function') {
        previousGlobalHandler(error, isFatal);
      }
    });
  }

  try {
    const rejectionTracking = require('promise/setimmediate/rejection-tracking');
    rejectionTracking.enable({
      allRejections: true,
      onUnhandled: (id, rejection = {}) => {
        recordRuntimeIssue(rejection, {
          fatal: false,
          source: 'unhandled_promise',
          metadata: { id },
        }).catch(() => {});
      },
      onHandled: () => {},
    });
  } catch (error) {
    if (__DEV__) {
      console.warn('[RuntimeGuard] Promise rejection tracking unavailable:', error);
    }
  }
}
