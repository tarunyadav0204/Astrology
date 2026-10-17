import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import ChartTaraPanel, { clampPanelPosition } from './ChartTaraPanel';

jest.mock('../../context/CreditContext', () => ({ useCredits: () => ({ verifiedChatCost: 10, features: { verified_chat_enabled: true } }) }));
jest.mock('./ChatPage', () => ({ __esModule: true, default: ({ embeddedVerified }) => {
  const [draft, setDraft] = require('react').useState('');
  return <input aria-label={embeddedVerified ? 'Verified question' : 'Unlocked mode'} value={draft} onChange={e => setDraft(e.target.value)} />;
} }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test('moving the panel remains within the viewport', () => {
  expect(clampPanelPosition({ x: -100, y: 9999 }, { width: 1000, height: 800 }, { width: 440, height: 740 })).toEqual({ x: 8, y: 52 });
});

test('panel keeps the Verified conversation mounted when minimized and resets for another chart', async () => {
  const host = document.createElement('div'); document.body.appendChild(host);
  const root = createRoot(host);
  try {
    await act(async () => root.render(<ChartTaraPanel birthData={{ id: 1, name: 'First chart' }} />));
    await act(async () => document.querySelector('.chart-tara-launcher').click());
    expect(document.querySelector('[aria-label="Verified question"]')).not.toBeNull();
    const firstInput = document.querySelector('input');
    act(() => document.querySelector('[aria-label="Minimize chat"]').click());
    expect(document.querySelector('.chart-tara-panel').hidden).toBe(true);
    act(() => document.querySelector('.chart-tara-launcher').click());
    expect(document.querySelector('input')).toBe(firstInput);
    await act(async () => root.render(<ChartTaraPanel birthData={{ id: 2, name: 'Second chart' }} />));
    expect(document.querySelector('input')).not.toBe(firstInput);
    expect(document.querySelector('.chart-tara-panel__header').textContent).toContain('Second chart');
  } finally { act(() => root.unmount()); host.remove(); }
});
