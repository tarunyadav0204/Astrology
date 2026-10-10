const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../src/utils/chatJumpControls.js'), 'utf8');
const modulePromise = import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
async function setup() {
  const { createChatJumpControlScheduler } = await modulePromise;
  const frames = new Map(), published = [];
  let id = 0;
  const scheduler = createChatJumpControlScheduler(value => published.push(value), fn => { frames.set(++id, fn); return id; }, key => frames.delete(key));
  return { scheduler, frames, published, flush() { for (const [key, fn] of frames) { frames.delete(key); fn(); } } };
}
test('repeated native scroll events never dispatch unchanged state', async () => {
  const s = await setup();
  for (let i = 0; i < 100; i++) s.scheduler.update({ showTop: false, showBottom: false });
  assert.equal(s.frames.size, 0);
  for (let i = 0; i < 100; i++) s.scheduler.update({ showTop: true, showBottom: false });
  assert.equal(s.frames.size, 1);
  assert.equal(s.published.length, 0);
  s.flush();
  assert.deepEqual(s.published, [{ showTop: true, showBottom: false }]);
  for (let i = 0; i < 100; i++) s.scheduler.update({ showTop: true, showBottom: false });
  assert.equal(s.frames.size, 0);
});
test('a frame uses the latest scroll position and cancels on unmount', async () => {
  const s = await setup();
  s.scheduler.update({ showTop: true, showBottom: false });
  s.scheduler.update({ showTop: false, showBottom: false });
  s.flush();
  assert.equal(s.published.length, 0);
  s.scheduler.update({ showTop: true, showBottom: true });
  s.scheduler.dispose();
  s.flush();
  assert.equal(s.published.length, 0);
});
