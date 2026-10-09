import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import ChatInput from './ChatInput';
let mockCredits = 5;
jest.mock('../../context/CreditContext', () => ({ useCredits: () => ({ credits: mockCredits, chatCost: 1, verifiedChatCost: 10, premiumChatCost: 15, partnershipCost: 2, loading: false, freeQuestionAvailable: true, instantChatEnabled: false, speechChatEnabled: false }) }));
global.IS_REACT_ACT_ENVIRONMENT = true;
const noop = () => {};
test('after Prashna selection ends, Verified keeps its correct paid tier until the user switches', () => {
  window.matchMedia = () => ({ matches:false, addEventListener:noop, removeEventListener:noop });
  const host=document.createElement('div'); document.body.appendChild(host); const root=createRoot(host); const send=jest.fn(); const change=jest.fn();
  try {
    act(() => root.render(<ChatInput onSendMessage={send} verifiedMode prashnaMode={false} followUpQuestion="Explain my D9" onFollowUpUsed={noop} onInstantModeChange={noop} onModeChange={change} />));
    expect(host.textContent).toContain('Verified: 10');
    expect(host.querySelector('button[type="submit"]').disabled).toBe(true);
    mockCredits=20;
    act(() => root.render(<ChatInput onSendMessage={send} verifiedMode prashnaMode={false} followUpQuestion="Explain my D9" onFollowUpUsed={noop} onInstantModeChange={noop} onModeChange={change} />));
    act(() => host.querySelector('form').dispatchEvent(new Event('submit', { bubbles:true, cancelable:true })));
    expect(send).toHaveBeenCalledWith('Explain my D9', expect.objectContaining({ chat_tier:'verified', premium_analysis:false }));
    const standard=host.querySelector('.chat-mode-option:not(.chat-mode-option--active)');
    act(() => standard.click());
    expect(change).toHaveBeenCalledWith('standard');
  } finally { act(() => root.unmount()); host.remove(); mockCredits=5; }
});
