import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import ChatSummary from './ChatSummary';
global.IS_REACT_ACT_ENVIRONMENT = true;
test('caps selection at three and submits only selected IDs', async () => {
  const host = document.createElement('div'); document.body.appendChild(host); const root = createRoot(host);
  const originalFetch = global.fetch;
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ summary: '**A focused summary**', count: 3 }) });
  const messages = Array.from({ length: 4 }, (_, index) => ({ role: 'assistant', content: `Answer ${index + 1}`, messageId: index + 1 }));
  try {
    act(() => root.render(<ChatSummary messages={messages} />));
    act(() => host.querySelector('button').click());
    const boxes = [...document.querySelectorAll('input[type="checkbox"]')];
    for (const box of boxes.slice(0,3)) act(() => box.click());
    expect(boxes[3].disabled).toBe(true);
    const generate = [...document.querySelectorAll('button')].find(button => button.textContent === 'Summarize selected (3)');
    await act(async () => generate.click());
    expect(JSON.parse(global.fetch.mock.calls[0][1].body).message_ids).toEqual([1,2,3]);
    expect(document.querySelector('strong').textContent).toBe('A focused summary');
  } finally { act(() => root.unmount()); host.remove(); global.fetch = originalFetch; }
});

test('Prashna setup selects a searched current city and closes tools', async () => {
  const { locationService } = require('../../services/locationService');
  const place = { id: 12, name: 'Gurugram', latitude: 28.4595, longitude: 77.0266 };
  const search = jest.spyOn(locationService, 'searchPlaces').mockResolvedValue([place]);
  const onPrashna = jest.fn();
  const host = document.createElement('div'); document.body.appendChild(host); const root = createRoot(host);
  try {
    act(() => root.render(<ChatSummary onPrashna={onPrashna} />));
    act(() => host.querySelector('button').click());
    act(() => [...document.querySelectorAll('button')].find(button => button.textContent === 'Ask with Prashna').click());
    const input = document.querySelector('input[placeholder="Search your current city"]');
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, 'Gurugram');
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await act(async () => [...document.querySelectorAll('button')].find(button => button.textContent === 'Find city').click());
    act(() => [...document.querySelectorAll('button')].find(button => button.textContent === 'Gurugram').click());
    expect(onPrashna).toHaveBeenCalledWith(place);
    expect(document.querySelector('[role="dialog"]')).toBeNull();
  } finally { act(() => root.unmount()); host.remove(); search.mockRestore(); }
});
