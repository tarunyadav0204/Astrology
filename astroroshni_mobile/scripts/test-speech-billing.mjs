import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import test from 'node:test';
import vm from 'node:vm';

const require = createRequire(import.meta.url);
const { parse } = require('@babel/parser');
const source = readFileSync(new URL('../src/components/Chat/SpeechChatScreen.js', import.meta.url), 'utf8');
const ast = parse(source, { sourceType: 'module', plugins: ['jsx'] });
const functions = new Map();
function visit(node) {
  if (!node || typeof node !== 'object') return;
  if (node.type === 'VariableDeclarator' && node.init?.type === 'ArrowFunctionExpression') {
    functions.set(node.id.name, source.slice(node.init.start, node.init.end));
  }
  for (const value of Object.values(node)) {
    if (Array.isArray(value)) value.forEach(visit);
    else if (value?.type) visit(value);
  }
}
visit(ast);

function setup({ allowed = true, active = false } = {}) {
  const events = [];
  const ref = (current) => ({ current });
  const context = vm.createContext({
    mountedRef: ref(true), handsFreeEnabledRef: ref(true), appStateRef: ref('active'),
    billingSessionRef: ref(active ? { session_id: 'existing' } : null),
    activeTurnSerialRef: ref(0), activeTurnLanguageRef: ref('en'),
    speechLanguageLockedRef: ref(true), questionSubmittedAtRef: ref(0),
    listeningModeRef: ref(null), recordingRef: ref(null),
    language: 'en', status: 'idle', IS_IOS_WEB: false, POST_TTS_LISTEN_DELAY_MS: 0,
    setErrorText() {}, setCurrentTranscript() {}, setFollowUps() {}, setStreamingAnswer() {},
    setStatus(value) { events.push(`status:${value}`); },
    normalizeLanguageCode: (value) => value,
    logSpeechDebug: async () => {}, wait: async () => {},
    releaseSpeechRecognizer: async () => {}, stopSpeechUiImmediately() {},
    startListening: async () => { events.push('listen'); },
    startSpeechBillingSession: async () => {
      events.push('bill');
      if (allowed) context.billingSessionRef.current = { session_id: 'new' };
      return allowed;
    },
    askInstant: async () => { events.push('answer'); return null; },
    startProcessingBridge: async () => {},
  });
  const run = (name, ...args) => vm.runInContext(`(${functions.get(name)})`, context)(...args);
  return { run, events };
}

test('automatic listening after the greeting does not start billing', async () => {
  const { run, events } = setup();
  await run('maybeStartAfterGreeting');
  assert.deepEqual(events, ['listen']);
});

test('tapping or retrying the microphone does not start billing', async () => {
  const { run, events } = setup();
  await run('forceStartListening');
  assert.deepEqual(events, ['listen']);
});

test('empty questions do not start billing or generate answers', async () => {
  const { run, events } = setup();
  await run('runQuestionTurn', '  ');
  assert.deepEqual(events, []);
});

test('first submitted question starts billing before its answer; later questions reuse it', async () => {
  const { run, events } = setup();
  await run('runQuestionTurn', 'First question');
  await run('runQuestionTurn', 'Second question');
  assert.deepEqual(events, ['bill', 'answer', 'answer']);
});

test('existing sessions continue without starting another billing session', async () => {
  const { run, events } = setup({ active: true });
  await run('runQuestionTurn', 'Follow-up question');
  assert.deepEqual(events, ['answer']);
});

test('denied billing prevents generation and leaves the thinking state', async () => {
  const { run, events } = setup({ allowed: false });
  await run('runQuestionTurn', 'Question');
  assert.deepEqual(events, ['bill', 'status:idle']);
});
