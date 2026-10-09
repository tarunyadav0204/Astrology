const { test } = require('node:test');
const assert = require('node:assert/strict');
const { openSavedConversation } = require('../src/utils/savedConversation.cjs');
test('loads messages before opening existing conversation viewer', async () => {
  let target;
  await openSavedConversation({ session_id: 's1', name: 'Amber' }, { fetchSession: async id => { assert.equal(id, 's1'); return { messages: [{ message_id: 8, sender: 'assistant', content: 'Answer', chat_tier: 'verified' }] }; }, navigate: (...args) => { target = args; } });
  assert.equal(target[0], 'ChatView');
  assert.equal(target[1].session.messages[0].role, 'assistant');
  assert.equal(target[1].session.messages[0].messageId, 8);
  assert.equal(target[1].session.messages[0].chat_tier, 'verified');
});
test('failed or empty loads do not navigate to an empty screen', async () => {
  for (const fetchSession of [async () => { throw new Error('404'); }, async () => ({ messages: [] })]) {
    await assert.rejects(openSavedConversation({ session_id: 's1' }, { fetchSession, navigate: () => assert.fail('Must not navigate') }));
  }
});
