import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import ChartChatThread from './ChartChatThread';
let mockStream;
const mockAsk = jest.fn();
const mockClose = jest.fn();
jest.mock('../../context/CreditContext', () => ({ useCredits: () => ({ chartChatCost: 0, credits: 0, fetchBalance: jest.fn() }) }));
jest.mock('../../utils/instantConversation', () => ({ askOverConversation: (...args) => mockAsk(...args), takeConversationStream: () => mockStream, closeConversationSession: (...args) => mockClose(...args) }));
jest.mock('./MessageBubble', () => ({ __esModule: true, default: ({ message }) => <p>{message.content}</p> }));
global.IS_REACT_ACT_ENVIRONMENT = true;
test.each([['chart_id', 7], ['birth_chart_id', 7], ['id', 7], [null, null]])('Chart Chat handles web profile ID %s and streams answers', async (idField, idValue) => {
  jest.useFakeTimers();
  mockAsk.mockClear(); mockClose.mockClear();
  localStorage.setItem('token', 'test-token');
  const originalFetch = global.fetch;
  global.fetch = jest.fn(async url => ({ ok: true, json: async () => url.includes('/status/') ? { status: 'processing', partial_content: 'First', engagement_updates: [{ text: 'Reviewing calculated strengths' }] } : { session_id: 'chart-session' } }));
  mockStream = { close: jest.fn() };
  mockAsk.mockResolvedValue({ ok: true, json: async () => ({ message_id: 19 }) });
  const host = document.createElement('div'); document.body.appendChild(host); const root = createRoot(host);
  const type = async text => act(async () => {
    const input = host.querySelector('textarea');
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(input, text);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
  try {
    await act(async () => root.render(<ChartChatThread birthData={{ ...(idField ? { [idField]: idValue } : {}), name: 'Test Native', date: '1990-01-01', time: '12:00', latitude: 28, longitude: 77 }} chartType="lagna" />));
    await type('मेरी शादी कब होगी?');
    expect(host.querySelector('button[type="submit"]').disabled).toBe(false);
    await act(async () => host.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
    expect(host.querySelector('[role="status"]').textContent).toContain('Reading your question');
    await act(async () => mockStream.onmessage({ data: JSON.stringify({ type: 'progress', engagement_updates: [{ text: 'Checking natal health factors' }] }) }));
    expect(host.querySelector('[role="status"]').textContent).toContain('Checking natal health factors');
    expect(host.querySelector('.chart-chat-thread__messages').contains(host.querySelector('[role="status"]'))).toBe(false);
    const body = mockAsk.mock.calls[0][2];
    expect(body).toMatchObject({ chat_tier: 'instant', instant_path: 'calculator_first', response_style: 'simple', query_context: { source: 'chart_sheet', viewed_chart: 'lagna' } });
    expect(JSON.parse(global.fetch.mock.calls[0][1].body).birth_chart_id).toBe(idValue);
    expect(body.birth_details.id).toBe(idValue);
    expect(body.instant_billing_session_id).toBeUndefined();
    expect(body.question).toBe('मेरी शादी कब होगी?');
    await act(async () => mockStream.onmessage({ data: JSON.stringify({ type: 'content_delta', delta: 'First ' }) }));
    expect(host.textContent).toContain('First ');
    expect(host.querySelector('[aria-label="Tara is typing"]')).not.toBeNull();
    await act(async () => mockStream.onmessage({ data: JSON.stringify({ type: 'content_delta', delta: 'part' }) }));
    expect(host.textContent).toContain('First part');
    await act(async () => jest.advanceTimersByTime(1500));
    expect(host.querySelector('[role="status"]').textContent).toContain('Reviewing calculated strengths');
    expect(host.textContent).toContain('First part'); // an older status snapshot cannot roll back live text
    await act(async () => mockStream.onmessage({ data: JSON.stringify({ type: 'completed', payload: { content: 'Complete answer' } }) }));
    expect(host.textContent).toContain('Complete answer');
    expect(host.querySelector('[role="status"]')).toBeNull();
    await type('And next year?');
    await act(async () => host.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
    expect(global.fetch).toHaveBeenCalledTimes(2);
    expect(mockAsk.mock.calls[1][2].session_id).toBe('chart-session');
  } finally { act(() => root.unmount()); host.remove(); global.fetch = originalFetch; localStorage.removeItem('token'); jest.useRealTimers(); }
  expect(mockClose).toHaveBeenCalledWith('chart-session');
});
