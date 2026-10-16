import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import MessageBubble from './MessageBubble';

jest.mock('jspdf', () => ({ jsPDF: jest.fn() }));
jest.mock('../../context/CreditContext', () => ({ useCredits: () => ({ credits: 100, chatCost: 1, podcastCost: 1, refreshBalance: jest.fn() }) }));
jest.mock('./SavedAnswers', () => ({ SaveAnswerButton: () => null }));
jest.mock('../Charts/NorthIndianChart', () => () => null);
global.IS_REACT_ACT_ENVIRONMENT = true;

test.each([
  ['assistant', {}, null],
  ['user', {}, null],
  ['assistant', { reading_mode: 'PRASHNA' }, 'Prashna · question chart'],
  ['assistant', { workflow_changed: true }, 'Using your birth chart for this question'],
  ['user', { reading_mode: 'PRASHNA' }, null],
])('renders %s messages without crashing and attributes workflow badges correctly', (role, metadata, badge) => {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root = createRoot(host);
  try {
    act(() => root.render(<MessageBubble message={{ role, content: 'Welcome to your chart consultation.', gate_metadata: metadata }} />));
    expect(host.textContent).toContain('Welcome to your chart consultation.');
    const chip = host.querySelector('.message-native-chip');
    if (badge) expect(chip.textContent).toBe(badge);
    else expect(chip).toBeNull();
  } finally {
    act(() => root.unmount());
    host.remove();
  }
});
