// One persistent socket per session. Accepted turns retain durable recovery IDs.
const conversations = new Map();
const turns = new Map();

export async function askOverConversation(url, token, request, fallback) {
    if (typeof WebSocket === 'undefined') return fallback();
    const key = `${url}:${request.session_id}:${token}`;
    let connection = conversations.get(key);
    if (!connection || connection.socket.readyState > 1) {
        let socket;
        try { socket = new WebSocket(`${url}?token=${encodeURIComponent(token)}`); }
        catch (_) { return fallback(); }
        connection = { socket, pending: new Map(), listeners: new Map(), buffers: new Map() };
        conversations.set(key, connection);
        connection.ready = new Promise((resolve, reject) => {
            const timer = setTimeout(() => { reject(new Error('Conversation unavailable')); socket.close(); }, 5000);
            connection.resolveReady = () => { clearTimeout(timer); resolve(); };
            connection.rejectReady = () => { clearTimeout(timer); reject(new Error('Conversation unavailable')); };
        });
        socket.onmessage = event => {
            let payload;
            try { payload = JSON.parse(event.data); } catch (_) { return; }
            if (payload.type === 'conversation_ready') { connection.resolveReady(); return; }
            const pending = connection.pending.get(payload.request_id);
            if (pending && ['queued', 'error'].includes(payload.type)) {
                connection.pending.delete(payload.request_id);
                clearTimeout(pending.timer);
                const ok = payload.type === 'queued';
                const body = ok ? payload.payload : { detail: payload.detail || payload.error };
                if (ok && body.message_id) turns.set(String(body.message_id), connection);
                pending.resolve({ ok, status: ok ? 200 : (payload.status || 500),
                    json: async () => body, text: async () => JSON.stringify(body) });
                return;
            }
            const mid = String(payload.message_id || '');
            const listener = connection.listeners.get(mid);
            if (listener) listener({ data: JSON.stringify(payload) });
            else if (mid) {
                const buffer = connection.buffers.get(mid) || [];
                // Only the latest cumulative content/progress is needed for recovery.
                const previous = buffer.findIndex(item => item.type === payload.type);
                if (previous >= 0) buffer.splice(previous, 1);
                buffer.push(payload);
                connection.buffers.set(mid, buffer);
            }
        };
        const disconnected = () => {
            connection.rejectReady();
            conversations.delete(key);
            for (const pending of connection.pending.values()) {
                clearTimeout(pending.timer);
                pending.reject(new Error('Connection lost after sending. Retry with the same request ID.'));
            }
            connection.pending.clear();
            for (const listener of connection.listeners.values()) listener({ data: JSON.stringify({ type: 'error', error: 'Conversation disconnected' }) });
            for (const [mid, owner] of turns) if (owner === connection) turns.delete(mid);
        };
        socket.onerror = () => socket.close();
        socket.onclose = disconnected;
    }
    try { await connection.ready; } catch (_) { return fallback(); }
    return new Promise((resolve, reject) => {
        const requestId = request.client_request_id;
        const timer = setTimeout(() => {
            connection.pending.delete(requestId);
            reject(new Error('Turn acknowledgement timed out. Retry with the same request ID.'));
        }, 60000);
        connection.pending.set(requestId, { resolve, reject, timer });
        try { connection.socket.send(JSON.stringify({ type: 'ask', request_id: requestId, request })); }
        catch (error) { clearTimeout(timer); connection.pending.delete(requestId); reject(error); }
    });
}

export function takeConversationStream(messageId) {
    const mid = String(messageId);
    const connection = turns.get(mid);
    if (!connection || connection.socket.readyState !== 1) return null;
    return {
        set onmessage(listener) {
            connection.listeners.set(mid, listener);
            const buffered = connection.buffers.get(mid) || [];
            connection.buffers.delete(mid);
            // Match a native socket: delivery occurs after handlers are installed.
            Promise.resolve().then(() => buffered.forEach(payload => listener({ data: JSON.stringify(payload) })));
        },
        close() {
            connection.listeners.delete(mid); connection.buffers.delete(mid); turns.delete(mid);
            if (this.onclose) this.onclose();
        },
    };
}

export function closeConversations() {
    for (const connection of conversations.values()) connection.socket.close();
    conversations.clear();
    turns.clear();
}
