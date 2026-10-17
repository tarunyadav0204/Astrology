import { askOverConversation, takeConversationStream, closeConversations } from './instantConversation';

let sockets;
let originalSocket;
beforeEach(() => {
  sockets = [];
  originalSocket = global.WebSocket;
  global.WebSocket = class {
    constructor(url) { this.url = url; this.readyState = 0; this.sent = []; sockets.push(this); }
    send(data) { this.sent.push(JSON.parse(data)); }
    emit(payload) { this.onmessage({ data: JSON.stringify(payload) }); }
    close() { this.readyState = 3; this.onclose?.(); }
  };
});
afterEach(() => { closeConversations(); global.WebSocket = originalSocket; });

test('Verified questions and clarification replies share a bidirectional conversation socket', async () => {
  const fallback = jest.fn();
  const body = { session_id: 'verified-session', client_request_id: 'turn-1', chat_tier: 'verified', question: 'Explain my dashas' };
  const pending = askOverConversation('ws://localhost/api/chat-v2/conversation', 'test-token', body, fallback);
  const socket = sockets[0]; socket.readyState = 1;
  socket.emit({ type: 'conversation_ready' });
  await Promise.resolve();
  expect(socket.sent[0]).toEqual({ type: 'ask', request_id: 'turn-1', request: body });
  socket.emit({ type: 'queued', request_id: 'turn-1', payload: { message_id: 1, chat_tier: 'verified' } });
  expect((await (await pending).json()).chat_tier).toBe('verified');
  socket.emit({ type: 'progress', message_id: 1, engagement_updates: [{ type: 'calculation', text: 'Dasha periods checked' }] });
  const stream = takeConversationStream(1);
  const events = [];
  stream.onmessage = event => events.push(JSON.parse(event.data));
  await Promise.resolve();
  socket.emit({ type: 'content_delta', message_id: 1, content: 'Your reading' });
  socket.emit({ type: 'completed', message_id: 1 });
  expect(events.map(event => event.type)).toEqual(['progress', 'content_delta', 'completed']);
  stream.close();
  const reply = { ...body, client_request_id: 'turn-2', question: 'Use the selected chart' };
  const next = askOverConversation('ws://localhost/api/chat-v2/conversation', 'test-token', reply, fallback);
  await Promise.resolve();
  socket.emit({ type: 'queued', request_id: 'turn-2', payload: { message_id: 2 } });
  expect((await (await next).json()).message_id).toBe(2);
  expect(sockets).toHaveLength(1);
  expect(socket.sent[1].request.question).toBe('Use the selected chart');
  expect(fallback).not.toHaveBeenCalled();
});

test('unavailable WebSocket falls back to the same durable HTTP request', async () => {
  global.WebSocket = undefined;
  const response = { ok: true };
  const fallback = jest.fn().mockResolvedValue(response);
  expect(await askOverConversation('ws://localhost/conversation', 'test-token', {}, fallback)).toBe(response);
  expect(fallback).toHaveBeenCalledTimes(1);
});
