import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import ChatInput from './ChatInput';
let mockCredits = 5;
jest.mock('../../context/CreditContext', () => ({ useCredits: () => ({ credits: mockCredits, chatCost: 1, verifiedChatCost: 10, premiumChatCost: 15, partnershipCost: 2, loading: false, freeQuestionAvailable: true, features: { verified_chat_enabled: true }, instantChatEnabled: false, speechChatEnabled: false }) }));
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


test('partnership offers Verified and sends the paid tier while a free question is available', () => {
  window.matchMedia = () => ({ matches:false, addEventListener:noop, removeEventListener:noop });
  const host=document.createElement('div'); document.body.appendChild(host); const root=createRoot(host); const send=jest.fn(); const change=jest.fn();
  mockCredits=20;
  try {
    act(() => root.render(<ChatInput onSendMessage={send} isPartnershipMode verifiedMode followUpQuestion="Can our business succeed?" onFollowUpUsed={noop} onInstantModeChange={noop} onModeChange={change} />));
    const modes=host.querySelector('[aria-label="Partnership answer mode"]');
    expect(modes.textContent).toContain('Verified');
    expect(modes.textContent).toContain('10 credits');
    act(() => host.querySelector('form').dispatchEvent(new Event('submit', { bubbles:true, cancelable:true })));
    expect(send).toHaveBeenCalledWith('Can our business succeed?', expect.objectContaining({ chat_tier:'verified', premium_analysis:false }));
    act(() => modes.querySelector('button').click());
    expect(change).toHaveBeenCalledWith('standard');
  } finally { act(() => root.unmount()); host.remove(); mockCredits=5; }
});

test.each(['standard', 'verified', 'premium'])('entering and exiting partnership preserves %s', tier => {
  window.matchMedia = () => ({ matches:false, addEventListener:noop, removeEventListener:noop });
  const host=document.createElement('div'); document.body.appendChild(host); const root=createRoot(host); const send=jest.fn();
  mockCredits=20;
  const render = partnership => root.render(<ChatInput onSendMessage={send} initialMode={tier} verifiedMode={tier === 'verified'} isPartnershipMode={partnership} followUpQuestion={partnership ? "Compare our charts" : "Read my chart"} onFollowUpUsed={noop} onInstantModeChange={noop} />);
  try {
    act(() => render(false));
    act(() => render(true));
    const active=host.querySelector('[aria-label="Partnership answer mode"] .chat-mode-option--active');
    expect(active.textContent.toLowerCase()).toContain(tier);
    act(() => host.querySelector('form').dispatchEvent(new Event('submit', { bubbles:true, cancelable:true })));
    expect(send).toHaveBeenCalledTimes(1);
    expect(send).toHaveBeenLastCalledWith('Compare our charts', expect.objectContaining({premium_analysis:tier === 'premium', ...(tier === 'verified' ? {chat_tier:'verified'} : {})}));
    act(() => render(false));
    act(() => host.querySelector('form').dispatchEvent(new Event('submit', { bubbles:true, cancelable:true })));
    expect(send).toHaveBeenCalledTimes(2);
    expect(send).toHaveBeenLastCalledWith('Read my chart', expect.objectContaining({premium_analysis:tier === 'premium', ...(tier === 'verified' ? {chat_tier:'verified'} : {})}));
  } finally { act(() => root.unmount()); host.remove(); mockCredits=5; }
});
