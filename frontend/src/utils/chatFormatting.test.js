import { formatChatHeadings, formatChatLists } from './chatFormatting';

test('renders Verified Simple sections with the Standard section styling', () => {
    const content = 'Direct answer.\n\n## Best-fit fields\n\n1. Analytics\nExplanation.\n\n## Final verdict';
    const result = formatChatHeadings(content);
    expect(result).toContain('<h3 class="chat-section-title">Best-fit fields</h3>');
    expect(result).toContain('<h3 class="chat-section-title">Final verdict</h3>');
    expect(result).toContain('1. Analytics\nExplanation.');
    expect(result).not.toContain('##');
});

test('adjacent bullets form one list, separate sections remain separate', () => {
    const result = formatChatLists('- First point\n- Second point\n\nParagraph.\n\n- Last point');
    const host = document.createElement('div'); host.innerHTML = result;
    expect(host.querySelectorAll('ul')).toHaveLength(2);
    expect(host.querySelector('ul').querySelectorAll('li')).toHaveLength(2);
    expect(host.textContent).toContain('Paragraph.');
});

test('inline numbers and decimals are not converted into list blocks', () => {
    expect(formatChatLists('Mercury has 8.81 rupas in house 4. A strong result.')).toBe('Mercury has 8.81 rupas in house 4. A strong result.');
});

test('preserves technical heading styles and inline hashes', () => {
    expect(formatChatHeadings('### Analysis\n\n#### Evidence\n\nText ## inline')).toBe(
        '<h3 class="chat-section-title">Analysis</h3>\n\n\n<h4 class="chat-subheader">Evidence</h4>\n\n\nText ## inline',
    );
});

test('standalone bold labels become subheadings without promoting inline emphasis', () => {
    expect(formatChatHeadings('<strong class="chat-bold">Dasha breakdown:</strong>\n\nParagraph.')).toContain('<h4 class="chat-subheader">Dasha breakdown</h4>');
    expect(formatChatHeadings('A <strong class="chat-bold">strong planet</strong> supports this.')).not.toContain('<h4');
});
