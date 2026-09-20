import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// Load the service with a bounded localStorage-like adapter, without RN setup.
const source = readFileSync(new URL('../src/services/storage.js', import.meta.url), 'utf8')
  .replace(/^import .*;\n/gm, '')
  .replace('export const storage =', 'globalThis.storage =');

function setup(initial = {}, limit = 1024, failure = null) {
  const items = new Map(Object.entries(initial));
  const context = vm.createContext({
    AsyncStorage: {
      async setItem(key, value) {
        if (failure) throw failure;
        const next = new Map(items).set(key, value);
        const size = [...next].reduce((sum, [k, v]) => sum + k.length + v.length, 0);
        if (size > limit) {
          const error = new Error(`Setting '${key}' exceeded the quota`);
          error.name = 'QuotaExceededError';
          throw error;
        }
        items.set(key, value);
      },
      async getItem(key) { return items.get(key) ?? null; },
      async getAllKeys() { return [...items.keys()]; },
      async removeItem(key) { items.delete(key); },
      async multiRemove(keys) { keys.forEach((key) => items.delete(key)); },
    },
  });
  vm.runInContext(source, context);
  return { storage: context.storage, items };
}

test('editing a profile recovers from a large legacy chart without losing pending messages', async () => {
  const preserved = {
    authToken: 'token',
    pendingChatMessages_1: 'unsent message',
    pendingFeedback_1: 'unsent feedback',
    chatMessages_1: 'conversation',
    language: 'hi',
  };
  const { storage, items } = setup({ ...preserved, chartData: 'x'.repeat(800) });
  const profile = { id: 1, name: 'Updated native', place: 'Delhi', date: '1990-01-01' };
  await storage.setBirthDetails(profile);
  await storage.addBirthProfile(profile);
  assert.deepEqual(JSON.parse(items.get('birthDetails')), profile);
  assert.deepEqual(JSON.parse(items.get('birthProfiles')), [profile]);
  for (const [key, value] of Object.entries(preserved)) assert.equal(items.get(key), value);
  assert.equal(items.has('chartData'), false);
});

test('profile writes reclaim disposable caches when there is no legacy chart', async () => {
  const { storage, items } = setup({ 'chart_only_cache:old': 'x'.repeat(980) });
  await storage.setBirthProfiles([{ id: 2, name: 'Native' }]);
  assert.equal(items.has('chart_only_cache:old'), false);
  assert.equal(JSON.parse(items.get('birthProfiles'))[0].id, 2);
});

test('chart persistence strips large response metadata and divisional charts', async () => {
  const { storage, items } = setup();
  const chart = { planets: { Sun: { longitude: 15 } }, houses: [], ascendant: 12 };
  await storage.setChartData({
    birthData: { name: 'Native' },
    chartData: { data: { ...chart, d9: 'x'.repeat(3000) }, request: 'x'.repeat(3000) },
  });
  assert.deepEqual(JSON.parse(items.get('chartData')), { birthData: { name: 'Native' }, chartData: chart });
});

test('an uncacheable chart does not reject completion or retain the old chart', async () => {
  const { storage, items } = setup({ chartData: '{"old":true}', pendingChatMessages_1: 'keep' });
  await storage.setChartData({ planets: { oversized: 'x'.repeat(2000) } });
  assert.equal(await storage.getChartData(), null);
  assert.equal(items.get('pendingChatMessages_1'), 'keep');
});

test('essential profile writes still report failures when no disposable space remains', async () => {
  const { storage, items } = setup({ pendingChatMessages_1: 'x'.repeat(950) });
  await assert.rejects(storage.setBirthDetails({ name: 'x'.repeat(100) }), { name: 'QuotaExceededError' });
  assert.equal(items.get('pendingChatMessages_1'), 'x'.repeat(950));
});

test('non-quota failures do not evict data and remain visible for essential writes', async () => {
  const failure = new Error('Storage unavailable');
  const { storage, items } = setup({ chartData: 'old' }, 1024, failure);
  await assert.rejects(storage.setBirthDetails({ id: 1 }), failure);
  assert.equal(items.get('chartData'), 'old');
});
