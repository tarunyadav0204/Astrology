import { formatChatHeadings } from './chatFormatting';

test('renders Verified Simple sections with the Standard section styling', () => {
    const content = 'Direct answer.\n\n## Best-fit fields\n\n1. Analytics\nExplanation.\n\n## Final verdict';
    const result = formatChatHeadings(content);
    expect(result).toContain('<h3 class="chat-section-title">Best-fit fields</h3>');
    expect(result).toContain('<h3 class="chat-section-title">Final verdict</h3>');
    expect(result).toContain('1. Analytics\nExplanation.');
    expect(result).not.toContain('##');
});

test('preserves technical heading styles and inline hashes', () => {
    expect(formatChatHeadings('### Analysis\n\n#### Evidence\n\nText ## inline')).toBe(
        '<h3 class="chat-section-title">Analysis</h3>\n\n\n<h4 class="chat-subheader">Evidence</h4>\n\n\nText ## inline',
    );
});
