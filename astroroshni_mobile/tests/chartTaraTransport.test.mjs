import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const source = await readFile(new URL('../src/utils/instantConversation.js', import.meta.url), 'utf8');
const transport = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
class Socket {
  static all = [];
  constructor() { this.readyState = 1; Socket.all.push(this); queueMicrotask(() => this.emit({ type: 'conversation_ready' })); }
  emit(payload) { this.onmessage?.({ data: JSON.stringify(payload) }); }
  send(raw) { const command = JSON.parse(raw); this.command = command; this.emit({ type: 'queued', request_id: command.request_id, payload: { message_id: command.request.session_id } }); }
  close() { this.readyState = 3; this.onclose?.(); }
}
test('chart calculator-first requests stream over the same conversation socket; cleanup leaves main chat open', async () => {
  const original = globalThis.WebSocket;
  globalThis.WebSocket = Socket;
  try {
    const ask = session_id => transport.askOverConversation('ws://test/conversation', 'test-token', { session_id, client_request_id: `${session_id}-1`, instant_path: session_id === 'chart' ? 'calculator_first' : 'baseline' }, () => assert.fail('Unexpected HTTP fallback'));
    await ask('main');
    await ask('chart');
    assert.equal(Socket.all[1].command.request.instant_path, 'calculator_first');
    const stream = transport.takeConversationStream('chart');
    const events = [];
    stream.onmessage = event => events.push(JSON.parse(event.data));
    Socket.all[1].emit({ type: 'content_delta', message_id: 'chart', content: 'Your ' });
    Socket.all[1].emit({ type: 'content_delta', message_id: 'chart', content: 'Your reading.' });
    assert.deepEqual(events.map(event => event.content), ['Your ', 'Your reading.']);
    // Releasing a completed turn does not close the persistent conversation.
    stream.close();
    assert.equal(Socket.all[1].readyState, 1);
    await ask('chart');
    assert.equal(Socket.all.length, 2);
    transport.closeConversationSession('chart');
    assert.equal(Socket.all[1].readyState, 3);
    assert.equal(Socket.all[0].readyState, 1);
  } finally { transport.closeConversations(); globalThis.WebSocket = original; }
});
