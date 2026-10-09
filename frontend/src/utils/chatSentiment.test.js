import { labelChatSentiment } from './chatSentiment';

test('labels both sentiments while preserving glossary content', () => {
  const html = '<span class="chat-sentiment-positive"><span class="tooltip-wrapper">Mercury</span> supports learning</span> <span class="chat-sentiment-negative">pressure</span>';
  const result = labelChatSentiment(html);
  expect(result).toContain('✓ Support');
  expect(result).toContain('! Caution');
  expect(result).toContain('<span class="tooltip-wrapper">Mercury</span>');
  expect((result.match(/chat-sentiment-label/g) || []).length).toBe(2);
});

test('leaves unmarked prose untouched', () => {
  expect(labelChatSentiment('<p>Ordinary text</p>')).toBe('<p>Ordinary text</p>');
});
