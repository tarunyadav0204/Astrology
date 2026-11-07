const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;

const source = fs.readFileSync(path.join(__dirname, '../src/components/ReelPlayerModal.js'), 'utf8');
const ast = parser.parse(source, { sourceType: 'module', plugins: ['jsx'] });
let config;
let touchSurface;
traverse(ast, {
  CallExpression(p) {
    if (p.node.callee.object?.name === 'PanResponder' &&
        p.findParent((parent) => parent.isVariableDeclarator())?.node.id.name === 'feedSwipe') {
      config = source.slice(p.node.arguments[0].start, p.node.arguments[0].end);
    }
  },
  JSXElement(p) {
    if (p.node.openingElement.attributes.some((a) => a.name?.name === 'testID' && a.value?.value === 'reel-swipe-surface')) {
      touchSurface = p;
    }
  },
});

function harness(jobId = 'newest') {
  const calls = [];
  const changing = { current: false };
  let revealed = 0;
  const reelFeedRef = { current: {
    jobId, height: 900, reelIds: ['newest', 'middle', 'oldest'], onSwipeToReel: (id) => { calls.push(id); changing.current = false; },
  } };
  const handlers = vm.runInNewContext(`(${config})`, {
    reelFeedRef, revealControls: () => revealed++,
    busyRef: { current: false }, menuRef: { current: null }, changing,
    slide: { setValue() {} }, setPeekId() {}, savePosition() {}, pausePlayback: async () => {},
    Platform: { OS: 'android' }, Vibration: { vibrate() {} },
    Animated: { timing: () => ({ start: (cb) => cb?.({ finished: true }) }), spring: () => ({ start() {} }) },
  });
  const swipe = (dx, dy) => {
    assert.equal(handlers.onStartShouldSetPanResponder(), true,
      'the surface must own touch-down instead of relying on the native video to bubble movement');
    handlers.onPanResponderGrant();
    handlers.onPanResponderRelease({}, { dx, dy });
  };
  return { calls, handlers, swipe, reelFeedRef, revealed: () => revealed };
}

test('up advances one saved reel, down returns, and the handler reads the current selection', () => {
  const h = harness();
  h.swipe(8, -250);
  assert.deepEqual(h.calls, ['middle']);
  h.reelFeedRef.current.jobId = 'middle';
  h.swipe(4, -240);
  h.reelFeedRef.current.jobId = 'oldest';
  h.swipe(0, 200);
  assert.deepEqual(h.calls, ['middle', 'oldest', 'middle']);
});

test('taps reveal controls; short, horizontal and diagonal gestures do not change reels', () => {
  const h = harness('middle');
  for (const [dx, dy] of [[0, 0], [2, 30], [300, 20], [200, -200]]) h.swipe(dx, dy);
  assert.deepEqual(h.calls, []);
  assert.equal(h.revealed(), 4);
});

test('feed edges and a standalone reel cannot navigate to a missing reel', () => {
  const h = harness();
  h.swipe(0, 250);
  h.reelFeedRef.current.jobId = 'oldest';
  h.swipe(0, -250);
  h.reelFeedRef.current = { jobId: 'only', reelIds: ['only'] };
  h.swipe(0, -250);
  assert.deepEqual(h.calls, []);
});

test('the gesture surface is above video but below buttons and the timeline', () => {
  assert.ok(touchSurface, 'native video needs an independent touch target');
  const children = touchSurface.parentPath.node.children;
  const index = children.indexOf(touchSurface.node);
  const before = source.slice(children[0].start, touchSurface.node.start);
  const after = source.slice(touchSurface.node.end, children.at(-1).end);
  assert.match(before, /<Video\b/);
  assert.match(after, /scrubber\.panHandlers/);
  assert.match(after, /<Animated\.View/);
  assert.ok(index > 0);
  assert.match(source.slice(touchSurface.node.start, touchSurface.node.end), /feedSwipe\.panHandlers/);
});
