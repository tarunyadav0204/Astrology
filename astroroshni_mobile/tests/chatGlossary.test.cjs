const { test } = require('node:test');
const assert = require('node:assert/strict');
const { wrapGlossaryTerms } = require('../src/utils/chatGlossary');

test('longest matching phrase wins without nested or damaged tooltips', () => {
 const output = wrapGlossaryTerms('Lagna lord and Lagna. Fourth house and House 4.', {
  Lagna: 'Ascendant', 'Lagna lord': 'Ascendant ruler',
  'fourth house': 'Home and education', 'House 4': 'Home and education',
 });
 assert.equal(output, '<tooltip data-term="Lagna lord">Lagna lord</tooltip> and <tooltip data-term="Lagna">Lagna</tooltip>. <tooltip data-term="fourth house">Fourth house</tooltip> and <tooltip data-term="House 4">House 4</tooltip>.');
});
test('existing tooltip contents and HTML attributes stay intact', () => {
 const input = '<tooltip data-term="Lagna lord">Lagna lord</tooltip><span data-note="Lagna">Lagna</span>';
 assert.equal(wrapGlossaryTerms(input, { Lagna: 'Ascendant' }), '<tooltip data-term="Lagna lord">Lagna lord</tooltip><span data-note="Lagna"><tooltip data-term="Lagna">Lagna</tooltip></span>');
});
test('Indic labels match and repeated occurrences retain first-occurrence behavior', () => {
 assert.equal(wrapGlossaryTerms('महादशा काल महादशा महादशा', {'महादशा': 'Main period', 'महादशा काल': 'Main period'}), '<tooltip data-term="महादशा काल">महादशा काल</tooltip> <tooltip data-term="महादशा">महादशा</tooltip> महादशा');
});
