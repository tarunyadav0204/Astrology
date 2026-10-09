import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { SaveAnswerButton } from './SavedAnswers';

global.IS_REACT_ACT_ENVIRONMENT = true;
test('save button restores state, saves, and removes the answer', async () => {
  const host = document.createElement('div'); document.body.appendChild(host);
  const root = createRoot(host);
  const originalFetch = global.fetch;
  global.fetch = jest.fn().mockResolvedValueOnce({ ok: true, json: async () => ({ saved: false }) }).mockResolvedValueOnce({ ok: true, json: async () => ({ saved: true }) }).mockResolvedValueOnce({ ok: true, json: async () => ({ saved: false }) });
  try {
    await act(async () => { root.render(<SaveAnswerButton message={{ messageId: 8, role: 'assistant', content: 'Career answer' }} />); });
    expect(host.querySelector('button').getAttribute('aria-label')).toBe('Save answer');
    await act(async () => host.querySelector('button').click());
    expect(global.fetch.mock.calls[1][1].method).toBe('PUT');
    expect(host.querySelector('button').getAttribute('aria-pressed')).toBe('true');
    await act(async () => host.querySelector('button').click());
    expect(global.fetch.mock.calls[2][1].method).toBe('DELETE');
    expect(host.querySelector('button').getAttribute('aria-pressed')).toBe('false');
  } finally { act(() => root.unmount()); host.remove(); global.fetch = originalFetch; }
});

test('processing answers cannot be bookmarked', () => {
  const host = document.createElement('div'); const root = createRoot(host);
  act(() => root.render(<SaveAnswerButton message={{ messageId: 8, role: 'assistant', content: 'Processing', isProcessing: true }} />));
  expect(host.querySelector('button')).toBeNull();
  act(() => root.unmount());
});
