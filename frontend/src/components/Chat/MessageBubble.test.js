import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import MessageBubble from './MessageBubble';

jest.mock('jspdf', () => ({ jsPDF: jest.fn() }));
jest.mock('../../context/CreditContext', () => ({ useCredits: () => ({ credits: 100, chatCost: 1, podcastCost: 1, refreshBalance: jest.fn() }) }));
jest.mock('./SavedAnswers', () => ({ SaveAnswerButton: () => null }));
jest.mock('../Charts/NorthIndianChart', () => () => null);
global.IS_REACT_ACT_ENVIRONMENT = true;

test('Verified pending answers show live calculation activity without a static chart loader', () => {
  const host = document.createElement('div'); document.body.appendChild(host);
  const root = createRoot(host);
  try {
    act(() => root.render(<MessageBubble message={{ role: 'assistant', chatTier: 'verified', isProcessing: true,
      content: '', calculationTrace: [{ id: 'dasha', title: 'Dasha periods checked', detail: 'Comparing the requested three-year period.' }] }} />));
    expect(host.textContent).toContain('Tara is reading');
    expect(host.textContent).toContain('Comparing the requested three-year period.');
    expect(host.textContent).not.toContain('Chart in progress');
    expect(host.textContent).not.toContain('Luna');
    act(() => root.render(<MessageBubble message={{ role: 'assistant', chatTier: 'verified', isProcessing: false,
      content: 'Your completed reading.', calculationTrace: [{ id: 'dasha', title: 'Dasha periods checked' }] }} />));
    expect(host.textContent).toContain('Your completed reading.');
    expect(host.textContent).not.toContain('Tara is reading');
  } finally { act(() => root.unmount()); host.remove(); }
});

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

test('compact remedy label retains the full follow-up request on click', () => {
  const host = document.createElement('div'); document.body.appendChild(host);
  const root = createRoot(host); const followUp = jest.fn();
  const question = 'Please explain the practical supportive routines for this entire period in detail.';
  try {
    act(() => root.render(<MessageBubble onFollowUpClick={followUp} message={{ role: 'assistant', content: 'Your reading.',
      next_action: { type: 'remedy', title: 'Supportive practices', reason: 'A demanding period.', follow_up_questions: [question] } }} />));
    const button = host.querySelector('.remedy-next-action-card__button');
    expect(button.textContent.trim()).toBe('Explore supportive practices');
    expect(button.textContent).not.toContain(question);
    act(() => button.click());
    expect(followUp.mock.calls[0][0]).toContain(question);
  } finally { act(() => root.unmount()); host.remove(); }
});
