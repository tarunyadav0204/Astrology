/**
 * Scroll the chat thread after `messages` updates.
 * Completed assistant answers align to the top of the scroll area so reading starts at the beginning.
 * User sends and in-progress assistant rows still pin to the bottom.
 */
export function scrollChatThreadAfterMessagesChange(messages, scrollToBottom) {
    const last = messages[messages.length - 1];
    if (!last) {
        return;
    }

    const isAssistantDone =
        last.role === 'assistant' &&
        !last.isProcessing &&
        !last.isTyping &&
        String(last.content || '').trim().length > 0;

    const scrollId =
        last.messageId != null
            ? String(last.messageId)
            : last.id != null
              ? String(last.id)
              : null;

    const raf = requestAnimationFrame(() => {
        if (isAssistantDone) {
            let el = null;
            if (scrollId) {
                try {
                    const esc =
                        typeof CSS !== 'undefined' && CSS.escape
                            ? CSS.escape(scrollId)
                            : String(scrollId).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
                    el = document.querySelector(`[data-chat-scroll-id="${esc}"]`);
                } catch (_) {
                    /* ignore */
                }
            }
            if (!el && messages.length > 0) {
                const i = messages.length - 1;
                el = document.querySelector(`[data-chat-message-index="${i}"]`);
            }
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                return;
            }
        }
        scrollToBottom();
    });

    return () => cancelAnimationFrame(raf);
}
