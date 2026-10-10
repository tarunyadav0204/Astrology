const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../src/utils/pdfPreparation.js'), 'utf8');
const helpers = import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

test('loader stops before sharing even when the native share promise stays pending', async () => {
  const { prepareAndSharePdf } = await helpers;
  const events = [];
  let closeShare;
  const operation = prepareAndSharePdf({
    prepare: async () => 'file:///report.pdf',
    setPreparing: value => events.push(value),
    share: uri => {
      assert.equal(uri, 'file:///report.pdf');
      assert.deepEqual(events, [true, false]);
      return new Promise(resolve => { closeShare = resolve; });
    },
  });
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(events, [true, false]);
  closeShare();
  await operation;
});

test('hung preparation times out, clears loader, and never opens sharing', async () => {
  const { prepareAndSharePdf } = await helpers;
  const events = [];
  await assert.rejects(prepareAndSharePdf({
    prepare: () => new Promise(() => {}),
    setPreparing: value => events.push(value),
    share: () => assert.fail('must not share after timeout'),
    timeoutMs: 10,
  }), /PDF generation timeout/);
  assert.deepEqual(events, [true, false]);
});

test('preparation failure clears loader and skips sharing', async () => {
  const { prepareAndSharePdf } = await helpers;
  const events = [];
  await assert.rejects(prepareAndSharePdf({
    prepare: () => { throw new Error('PDF file was not created'); },
    setPreparing: value => events.push(value),
    share: () => assert.fail('must not share a failed export'),
  }), /not created/);
  assert.deepEqual(events, [true, false]);
});

test('share failure propagates after loader has stopped', async () => {
  const { prepareAndSharePdf } = await helpers;
  const events = [];
  await assert.rejects(prepareAndSharePdf({
    prepare: async () => 'file:///report.pdf',
    setPreparing: value => events.push(value),
    share: async () => { throw new Error('Sharing is not available'); },
  }), /Sharing is not available/);
  assert.deepEqual(events, [true, false]);
});
