import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const source = await readFile(new URL('../src/utils/copyChatMessage.js', import.meta.url), 'utf8');
const { copyChatMessage, copyableChatText } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

test('questions retain literal punctuation, markup and Unicode', async () => {
  const question = 'मेरी कुंडली: **my words**, 2 * 3, <5 and #1?';
  let copied;
  await copyChatMessage(question, 'user', text => { copied = text; return true; }, () => assert.fail('Unnecessary fallback'));
  assert.equal(copied, question);
});
test('native fallback copies the same question when Expo rejects', async () => {
  let copied;
  await copyChatMessage('My question?', 'user', () => Promise.reject(new Error('Native write failed')), text => { copied = text; });
  assert.equal(copied, 'My question?');
});
test('false results also trigger fallback', async () => {
  let count = 0;
  await copyChatMessage('Question', 'user', () => false, () => { count++; return true; });
  assert.equal(count, 1);
});
test('both writers failing propagates failure, never success', async () => {
  await assert.rejects(copyChatMessage('Question', 'user', () => Promise.reject(new Error('Primary')), () => Promise.reject(new Error('Fallback'))));
  await assert.rejects(copyChatMessage('Question', 'user', () => false, () => false));
});
test('no fallback and empty messages fail honestly', async () => {
  await assert.rejects(copyChatMessage('Question', 'user', () => false));
  await assert.rejects(copyChatMessage('', 'user', () => assert.fail('Empty write')));
});
test('answers remove presentation markup and preserve paragraph breaks', () => {
  assert.equal(copyableChatText('## Heading\n<p>**Mercury** supports this.</p><p>Next line.</p>', 'assistant'), 'Heading\nMercury supports this.\nNext line.');
});
