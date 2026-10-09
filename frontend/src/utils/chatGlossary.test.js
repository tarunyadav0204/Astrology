import { autoWrapGlossaryTermsInHtml, buildGlossaryTooltipHtml } from './chatGlossary';

test('one glossary term cannot corrupt another tooltip definition', () => {
    const result = autoWrapGlossaryTermsInHtml(
        'Your Lagna lord supports the journey.',
        {
            journey: 'It turns your other planets into reality. It is the Prime Mover of your life\'s journey.',
            'Lagna lord': 'The ruler of the ascendant.',
        },
    );

    expect(result.count).toBe(2);
    expect(result.html).toContain('data-definition="The ruler of the ascendant."');
    expect(result.html).toContain('life&#39;s journey.');
    expect((result.html.match(/class="tooltip-wrapper"/g) || [])).toHaveLength(2);
    const rendered = document.createElement('div');
    rendered.innerHTML = result.html;
    expect(rendered.textContent).toBe('Your Lagna lord supports the journey.');
    expect(rendered.querySelectorAll('.tooltip-wrapper')).toHaveLength(2);
    expect(rendered.querySelector('[data-term="journey"]').dataset.definition)
        .toBe('It turns your other planets into reality. It is the Prime Mover of your life\'s journey.');
});

test('tooltip attributes escape quotes and markup', () => {
    const html = buildGlossaryTooltipHtml(
        'Lagna lord',
        'Lagna "lord"',
        'A "quoted" definition with <b>markup</b> & an apostrophe\'s edge.',
    );
    expect(html).toContain('data-term="Lagna &quot;lord&quot;"');
    expect(html).toContain('data-definition="A &quot;quoted&quot; definition with &lt;b&gt;markup&lt;/b&gt; &amp; an apostrophe&#39;s edge."');
});

test('existing HTML attributes are never modified', () => {
    const result = autoWrapGlossaryTermsInHtml(
        '<strong data-note="Lagna lord">Lagna lord</strong>',
        { 'Lagna lord': 'Ascendant ruler' },
    );
    expect(result.html).toContain('data-note="Lagna lord"');
    expect(result.html).toContain('<strong data-note="Lagna lord"><span class="tooltip-wrapper"');
    expect(result.count).toBe(1);
});

test('overlapping aliases and partial model tagging do not nest tooltips', () => {
    const tagged = buildGlossaryTooltipHtml('Lagna lord', 'Lagna lord', 'Ruler');
    const result = autoWrapGlossaryTermsInHtml(`${tagged} and Lagna. Fourth house and House 4.`, {
        Lagna: 'Ascendant', 'Lagna lord': 'Ruler',
        'fourth house': 'Home', 'House 4': 'Home',
    });
    const rendered = document.createElement('div');
    rendered.innerHTML = result.html;
    expect(rendered.textContent).toBe('Lagna lord and Lagna. Fourth house and House 4.');
    expect(rendered.querySelectorAll('.tooltip-wrapper')).toHaveLength(4);
    expect(rendered.querySelector('.tooltip-wrapper .tooltip-wrapper')).toBeNull();
});
