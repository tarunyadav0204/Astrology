import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import ChatMemory from './ChatMemory';

test('opens the selected chart memory and removes through the fact API', async () => {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root = createRoot(host);
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ facts: [{ id: 9, category: 'career', fact: 'Offer received' }] }) });
  const confirm = jest.spyOn(window, 'confirm').mockReturnValue(true);
  const flush = () => new Promise(resolve => setTimeout(resolve, 0));
  try {
    await act(async () => { root.render(<ChatMemory chartId={17} name="Amber" />); await flush(); });
    expect(host.querySelector('button').getAttribute('aria-label')).toContain('Memory for Amber, 1 saved details');
    await act(async () => { host.querySelector('button').click(); await flush(); });
    expect(document.querySelector('[role="dialog"]').textContent).toContain('Remembered about Amber');
    act(() => document.querySelector('[aria-label^="Edit:"]').click());
    expect(document.querySelector('textarea').value).toBe('Offer received');
    act(() => [...document.querySelectorAll('button')].find(button => button.textContent === 'Cancel').click());
    await act(async () => { document.querySelector('[aria-label^="Remove:"]').click(); await flush(); });
    expect(global.fetch.mock.calls.some(([url, options]) => url === '/api/facts/9' && options.method === 'DELETE')).toBe(true);
    expect(global.fetch.mock.calls.every(([url]) => url.startsWith('/api/facts'))).toBe(true);
  } finally { act(() => root.unmount()); host.remove(); confirm.mockRestore(); }
});
