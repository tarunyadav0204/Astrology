async function openSavedConversation(answer, { fetchSession, navigate }) {
  if (!answer.session_id) throw new Error('The saved conversation is unavailable.');
  const data = await fetchSession(answer.session_id);
  if (!Array.isArray(data.messages) || !data.messages.length) throw new Error('The conversation could not be loaded. Please try again.');
  const messages = data.messages.map((message, index) => ({
    ...message,
    messageId: message.message_id ?? message.messageId,
    role: ['assistant', 'ai'].includes(message.sender) ? 'assistant' : message.sender || message.role,
    timestamp: message.completed_at || message.timestamp,
    id: `${message.message_id ?? message.messageId ?? index}_${message.completed_at || message.timestamp}`,
    native_name: message.native_name || data.native_name || answer.name,
  }));
  navigate('ChatView', { session: { ...data, session_id: answer.session_id, messages, native_name: data.native_name || answer.name, created_at: messages[0].timestamp || answer.saved_at } });
}
module.exports = { openSavedConversation };
