const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;

// Exercise the production comparator, launch effect and handler without loading
// native media modules or calling a paid provider.
const source = fs.readFileSync(path.join(__dirname, '../src/components/Chat/MessageBubble.js'), 'utf8');
const ast = parser.parse(source, { sourceType: 'module', plugins: ['jsx'] });
const functions = {};
let launchEffect;
traverse(ast, {
  VariableDeclarator(p) {
    if (['areMessageBubblePropsEqual', 'openReelStudio', 'confirmReelSetup'].includes(p.node.id.name)) {
      functions[p.node.id.name] = source.slice(p.node.init.start, p.node.init.end);
    }
  },
  CallExpression(p) {
    const [callback, deps] = p.node.arguments;
    if (p.node.callee.name === 'useEffect' && deps?.elements?.some((x) => x?.name === 'reelAutoLaunchKey')) {
      launchEffect = source.slice(callback.start, callback.end);
    }
  },
});
const equal = vm.runInNewContext(`(${functions.areMessageBubblePropsEqual})`);

function harness(savedJob = null) {
  const state = {};
  const calls = { saved: 0, draft: 0, queue: 0, consumed: 0 };
  const timers = [];
  const context = {
    message: { messageId: 123, role: 'assistant', content: 'A complete answer. '.repeat(10) },
    reelAutoLaunchKey: 1, reelAutoLaunchMessageId: 123, reelAutoLaunchLang: 'hi',
    isInstantChatMessage: false, isClarification: false, isNativeGate: false,
    lastReelPromoKeyRef: { current: 0 }, reelPrepareLock: { current: false },
    isPreparingReel: false, reelJobId: null, reelJobStatus: '',
    getCleanMessageText: () => 'A complete answer. '.repeat(10),
    setTimeout: (fn) => { timers.push(fn); return timers.length; }, clearTimeout() {},
    requestAnimationFrame: (fn) => fn(),
    onReelAutoLaunchConsumed: () => { calls.consumed++; },
    podcastLangFromUiLanguage: (lang) => lang === 'hi' ? 'hi' : 'en',
    REEL_FORMATS: { short: { duration: 90 } },
    requireAuthForPaid: async () => true, refreshCredits() {},
    t: (_key, text) => text, apiErrorMessage: (err) => err.message,
    showReelError: (err) => { state.error = err; },
    navigation: { navigate: () => assert.fail('unexpected navigation') },
    chatAPI: {
      getSavedReel: async () => { calls.saved++; return { data: { job: savedJob } }; },
      getReelPricing: async () => ({ data: { credits: 100, credit_cost: 15 } }),
      createReelDraft: async (args) => { calls.draft++; state.draftArgs = args; return { data: { draft_id: 'draft_test', claims: [{ id: 'claim_1' }] } }; },
      queueReel: async (args) => { calls.queue++; state.queueArgs = args; return { data: { job_id: 'job_test', status: 'queued' } }; },
    },
  };
  for (const name of ['ShowReelStudio', 'ShowReelPlayer', 'ReelDraft', 'IsPreparingReel', 'ReelJobId', 'ReelJobStatus', 'ReelJobError', 'ReelFormat', 'ReelLanguage', 'ReelCreditQuote', 'IsRecreatingReel', 'ShowReelFormatModal', 'ReelFormatQuotes', 'IsQueueingReel']) {
    context[`set${name}`] = (value) => { state[name] = value; };
  }
  vm.createContext(context);
  context.openReelStudio = vm.runInContext(`(${functions.openReelStudio})`, context);
  return { state, calls, context, timers };
}

test('promo reaches the memoized answer and opens one setup without paid calls', async () => {
  const h = harness();
  const before = { message: h.context.message, podcastAutoLaunchMessageId: 123, reelAutoLaunchMessageId: 123, reelAutoLaunchKey: 0, reelAutoLaunchLang: 'en' };
  const after = { ...before, reelAutoLaunchKey: 1, reelAutoLaunchLang: 'hi' };
  assert.equal(equal(before, after), false, 'the reel launch must not be skipped by React.memo');
  vm.runInContext(`(${launchEffect})()`, h.context);
  h.timers.forEach((fn) => fn());
  assert.equal(h.state.ShowReelStudio, true, 'progress opens before generation completes');
  await new Promise(setImmediate);
  assert.equal(h.calls.draft, 0);
  assert.equal(h.calls.queue, 0);
  assert.equal(h.state.ReelLanguage, 'hi');
  assert.equal(h.state.ShowReelFormatModal, true);
  assert.equal(h.calls.consumed, 1);
});

test('each reel launch prop invalidates memoization', () => {
  const before = { message: {} };
  for (const [key, value] of Object.entries({ reelAutoLaunchKey: 1, reelAutoLaunchMessageId: 123, reelAutoLaunchLang: 'hi' })) {
    assert.equal(equal(before, { ...before, [key]: value }), false, key);
  }
  assert.equal(equal(before, { ...before }), true);
});

test('reel icon reopens preparation without a second request', async () => {
  const h = harness();
  h.context.isPreparingReel = true;
  await h.context.openReelStudio();
  assert.equal(h.state.ShowReelStudio, true);
  assert.equal(h.calls.saved, 0);
  assert.equal(h.calls.draft, 0);
  assert.equal(h.state.ShowReelFormatModal, undefined);
});

test('reel icon reconnects to the queued render after the answer remounts', async () => {
  const h = harness({ job_id: 'existing', status: 'queued', settings: { duration_seconds: 90 } });
  await h.context.openReelStudio();
  assert.equal(h.state.ShowReelStudio, true);
  assert.equal(h.state.ReelJobId, 'existing');
  assert.equal(h.state.ReelJobStatus, 'queued');
  assert.equal(h.calls.draft, 0);
  assert.equal(h.calls.queue, 0);
  assert.equal(h.state.ShowReelFormatModal, undefined);
});

test('icon tap during the promo request cannot open a second chooser', async () => {
  const h = harness();
  const started = h.context.openReelStudio(false, 'hi');
  // State has not committed yet, as with two taps in the same React frame.
  await h.context.openReelStudio();
  await started;
  assert.equal(h.calls.saved, 1);
  assert.equal(h.calls.draft, 0);
  assert.equal(h.calls.queue, 0);
  assert.equal(h.state.ShowReelFormatModal, true);
});

test('icon opens the known running job even before saved-job lookup catches up', async () => {
  const h = harness();
  h.context.reelJobId = 'running';
  h.context.reelJobStatus = 'creating_planned_shots';
  await h.context.openReelStudio();
  assert.equal(h.state.ShowReelStudio, true);
  assert.equal(h.calls.saved, 0);
  assert.equal(h.calls.draft, 0);
  assert.equal(h.state.ShowReelFormatModal, undefined);
});

 test('one create action passes the same settings and total to draft and job, and opens progress', async () => {
  const h = harness();
  const create = vm.runInContext(`(${functions.confirmReelSetup})`, h.context);
  const selection = { language: 'hi', durationSeconds: 180, presenterEnabled: true, confirmedCreditCost: 35 };
  const pending = create(selection);
  await create(selection);
  assert.equal(h.state.ShowReelStudio, true);
  assert.equal(h.state.IsPreparingReel, true);
  assert.equal(h.state.ShowReelFormatModal, false);
  await pending;
  assert.equal(h.calls.draft, 1);
  assert.equal(h.calls.queue, 1);
  for (const key of Object.keys(selection)) {
    assert.equal(h.state.draftArgs[key], selection[key]);
    assert.equal(h.state.queueArgs[key], selection[key]);
  }
  assert.equal(h.state.ReelJobStatus, 'queued');
  assert.equal(h.context.reelPrepareLock.current, false);
});
