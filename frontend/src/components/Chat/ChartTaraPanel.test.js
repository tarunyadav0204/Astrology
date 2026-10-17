import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import ChartTaraPanel, { sheetSnapHeight } from './ChartTaraPanel';
let mockCost = 2;
jest.mock('../../context/CreditContext', () => ({ useCredits: () => ({ chartChatCost: mockCost, features: { instant_chat_enabled: true, verified_chat_enabled: false }, fetchCosts: jest.fn() }) }));
jest.mock('./ChartChatThread', () => ({ __esModule: true, default: ({ birthData, chartType }) => {
  const [draft, setDraft] = require('react').useState('');
  return <input aria-label={`Chart question for ${birthData.name}`} data-chart={chartType} value={draft} onChange={e => setDraft(e.target.value)} />;
} }));
global.IS_REACT_ACT_ENVIRONMENT = true;
test('sheet snaps to collapsed, half and expanded positions', () => {
  expect(sheetSnapHeight(80, 1000)).toBe(72);
  expect(sheetSnapHeight(500, 1000)).toBe(520);
  expect(sheetSnapHeight(950, 1000)).toBe(910);
});
test('Chart Chat works without Verified, preserves conversation on collapse and chart changes, resets for another native', async () => {
  const host = document.createElement('div'); document.body.appendChild(host);
  const root = createRoot(host);
  try {
    await act(async () => root.render(<ChartTaraPanel birthData={{ id: 1, name: 'First chart' }} chartType="lagna" />));
    expect(document.querySelector('.chart-tara-launcher').disabled).toBe(false);
    await act(async () => document.querySelector('.chart-tara-launcher').click());
    const firstInput = document.querySelector('input');
    expect(firstInput.getAttribute('aria-label')).toBe('Chart question for First chart');
    expect(document.querySelector('.chart-tara-panel__header').textContent).toContain('2 credits/question');
    act(() => document.querySelector('[aria-label="Minimize chat"]').click());
    expect(document.querySelector('.chart-tara-panel__body').hidden).toBe(true);
    act(() => document.querySelector('[aria-label="Close Chart Chat"]').click());
    expect(document.querySelector('.chart-tara-panel').hidden).toBe(true);
    act(() => document.querySelector('.chart-tara-launcher').click());
    expect(document.querySelector('.chart-tara-panel').hidden).toBe(false);
    expect(document.querySelector('input')).toBe(firstInput);
    mockCost = 0;
    await act(async () => root.render(<ChartTaraPanel birthData={{ id: 1, name: 'First chart' }} chartType="navamsa" />));
    expect(document.querySelector('input')).toBe(firstInput);
    expect(firstInput.dataset.chart).toBe('navamsa');
    expect(document.querySelector('.chart-tara-panel__header').textContent).toContain('Free');
    await act(async () => root.render(<ChartTaraPanel birthData={{ id: 2, name: 'Second chart' }} />));
    expect(document.querySelector('input')).not.toBe(firstInput);
  } finally { act(() => root.unmount()); host.remove(); mockCost = 2; }
});
