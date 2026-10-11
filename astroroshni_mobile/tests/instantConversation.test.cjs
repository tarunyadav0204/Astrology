const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

async function load() {
  const source = fs.readFileSync(path.join(__dirname, '../src/utils/instantConversation.js'), 'utf8');
  return import(`data:text/javascript;base64,${Buffer.from(source + `\n// ${Math.random()}`).toString('base64')}`);
}
class Socket {
  static instances = [];
  constructor(url) { this.url = url; this.readyState = 0; Socket.instances.push(this); }
  event(payload) { this.onmessage?.({ data: JSON.stringify(payload) }); }
  ready() { this.readyState = 1; this.event({ type: 'conversation_ready' }); }
  send(data) { this.lastRequest = JSON.parse(data); }
  close() { this.readyState = 3; this.onclose?.(); }
}
const flush = () => new Promise(resolve => setImmediate(resolve));

test('two turns reuse one socket; buffered progress arrives after acknowledgement', async () => {
  const original = global.WebSocket;
  global.WebSocket = Socket; Socket.instances = [];
  const module = await load();
  try {
    let fallbacks = 0;
    const submit = id => module.askOverConversation('ws://example/conversation', 'token',
      { session_id: 'session', client_request_id: id, question: id }, () => { fallbacks++; });
    const first = submit('one');
    const socket = Socket.instances[0]; socket.ready(); await flush();
    assert.equal(socket.lastRequest.type, 'ask');
    socket.event({ type: 'queued', request_id: 'one', payload: { message_id: 11 } });
    socket.event({ type: 'progress', message_id: 11, engagement_updates: [{ type:'calculation', text:'Checked' }] });
    assert.equal((await (await first).json()).message_id, 11);
    const received = [];
    const relay = module.takeConversationStream(11);
    relay.onmessage = event => received.push(JSON.parse(event.data)); await flush();
    assert.equal(received[0].type, 'progress');
    relay.close(); assert.equal(socket.readyState, 1);
    const second = submit('two'); await flush();
    assert.equal(socket.lastRequest.request.question, 'two');
    socket.event({ type:'queued', request_id:'two', payload:{message_id:12} }); await second;
    assert.equal(Socket.instances.length, 1);
    assert.equal(fallbacks, 0);
  } finally { module.closeConversations(); global.WebSocket = original; }
});

test('HTTP fallback occurs before send; disconnect after send does not duplicate work', async () => {
  const original = global.WebSocket;
  const module = await load();
  let fallbacks = 0;
  const fallback = () => { fallbacks++; return 'HTTP'; };
  try {
    global.WebSocket = undefined;
    assert.equal(await module.askOverConversation('ws://example', 'token', {session_id:'s'}, fallback), 'HTTP');
    global.WebSocket = Socket; Socket.instances = [];
    const pending = module.askOverConversation('ws://example', 'token', {session_id:'s',client_request_id:'id'}, fallback);
    const socket = Socket.instances[0]; socket.ready(); await flush(); socket.close();
    await assert.rejects(pending, /same request ID/);
    assert.equal(fallbacks, 1);
  } finally { module.closeConversations(); global.WebSocket = original; }
});

test('server ownership errors retain HTTP status and detail for existing session recovery', async () => {
  const original = global.WebSocket; global.WebSocket = Socket; Socket.instances = [];
  const module = await load();
  try {
    const pending = module.askOverConversation('ws://example', 'token', {session_id:'s',client_request_id:'id'}, () => {});
    const socket = Socket.instances[0]; socket.ready(); await flush();
    socket.event({type:'error',request_id:'id',status:409,detail:{code:'chart_mismatch'}});
    const response = await pending;
    assert.equal(response.ok, false); assert.equal(response.status, 409);
    assert.match(await response.text(), /chart_mismatch/);
  } finally { module.closeConversations(); global.WebSocket = original; }
});

test('web and mobile share the same conversation protocol implementation', () => {
  assert.equal(fs.readFileSync(path.join(__dirname,'../src/utils/instantConversation.js'),'utf8'),
    fs.readFileSync(path.join(__dirname,'../../frontend/src/utils/instantConversation.js'),'utf8'));
});
