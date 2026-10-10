const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../src/utils/pdfWebShare.js'), 'utf8');
const helpers = import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
for (const mode of ['supported', 'unsupported', 'cancelled', 'denied', 'failed']) {
  test(`browser PDF share: ${mode}`, async () => {
    const { sharePdfBlobOnWeb } = await helpers;
    let shared = 0, downloaded = 0;
    const originals = Object.getOwnPropertyDescriptors(globalThis);
    Object.defineProperty(globalThis, 'navigator', { configurable: true, value: {
      canShare: () => mode !== 'unsupported',
      share: async ({ files }) => {
        shared++;
        assert.equal(files[0].type, 'application/pdf');
        if (mode === 'cancelled') throw Object.assign(new Error('cancel'), { name: 'AbortError' });
        if (mode === 'denied') throw Object.assign(new Error('activation'), { name: 'NotAllowedError' });
        if (mode === 'failed') throw new Error('share failure');
      },
    }});
    globalThis.document = { body: { appendChild() {} }, createElement: () => ({ click() { downloaded++; }, remove() {} }) };
    globalThis.setTimeout = callback => { callback(); };
    try {
      const operation = sharePdfBlobOnWeb(new Blob(['pdf'], { type: 'application/pdf' }));
      if (mode === 'failed') await assert.rejects(operation, /share failure/);
      else await operation;
      assert.equal(shared, mode === 'unsupported' ? 0 : 1);
      assert.equal(downloaded, ['unsupported', 'denied'].includes(mode) ? 1 : 0);
    } finally {
      for (const name of ['navigator', 'document', 'setTimeout']) {
        if (originals[name]) Object.defineProperty(globalThis, name, originals[name]);
        else delete globalThis[name];
      }
    }
  });
}
