const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const babel = require('@babel/core');
const source = babel.transformSync(fs.readFileSync(require.resolve('../src/services/reelMediaCache.js'), 'utf8'), {
  configFile: false, babelrc: false, plugins: ['@babel/plugin-transform-modules-commonjs'],
}).code;
const tick = () => new Promise((resolve) => setImmediate(resolve));

function harness() {
  const downloads = [], deleted = [], moved = [];
  const modules = {
    'react-native': { Platform: { OS: 'android' } },
    'expo-file-system/legacy': {
      cacheDirectory: 'file:///cache/',
      downloadAsync: (url, uri, options) => new Promise((resolve) => downloads.push({ url, uri, options, resolve })),
      deleteAsync: async (uri) => deleted.push(uri),
      moveAsync: async (args) => moved.push(args),
    },
    '@react-native-async-storage/async-storage': { getItem: async () => 'private-token' },
    '../utils/constants': { API_BASE_URL: 'https://api.test', getEndpoint: (path) => '/api' + path },
  };
  const exports = {};
  vm.runInNewContext(source, { exports, require: (name) => modules[name] });
  return { cache: exports.createReelMediaCache(), downloads, deleted, moved };
}

test('prefetch and playback share one authenticated download; keep evicts only other reels', async () => {
  const h = harness(), first = h.cache.prepare('one');
  assert.equal(first, h.cache.prepare('one'));
  await tick();
  assert.equal(h.downloads.length, 1);
  assert.equal(h.downloads[0].options.headers.Authorization, 'Bearer private-token');
  h.downloads[0].resolve({ status: 200 });
  const media = await first;
  h.cache.keep(['one']); await tick();
  assert.ok(!h.deleted.includes(media.uri));
  h.cache.keep([]); await tick();
  assert.ok(h.deleted.includes(media.uri));
});

test('closing during prefetch cleans the completed file and prevents new requests', async () => {
  const h = harness(), promise = h.cache.prepare('one');
  await tick(); h.cache.dispose();
  h.downloads[0].resolve({ status: 200 });
  const media = await promise; await tick();
  assert.ok(h.deleted.includes(media.uri));
  await assert.rejects(h.cache.prepare('two'), /closed/);
});

test('failed downloads are not cached and partial files are removed', async () => {
  const h = harness(), failed = h.cache.prepare('one');
  await tick(); h.downloads[0].resolve({ status: 403 });
  await assert.rejects(failed, /403/);
  assert.ok(h.deleted.includes(h.downloads[0].uri));
  const retry = h.cache.prepare('one'); await tick();
  h.downloads[1].resolve({ status: 200 });
  await retry; assert.equal(h.moved.length, 1);
  h.cache.dispose();
});

test('returning to an evicted in-flight reel cannot delete the new download', async () => {
  const h = harness(), old = h.cache.prepare('one');
  await tick(); h.cache.keep([]);
  const fresh = h.cache.prepare('one'); await tick();
  assert.notEqual(h.downloads[0].uri, h.downloads[1].uri);
  h.downloads[1].resolve({ status: 200 }); const current = await fresh;
  h.downloads[0].resolve({ status: 200 }); await old; await tick();
  assert.ok(!h.deleted.includes(current.uri));
  h.cache.dispose();
});
