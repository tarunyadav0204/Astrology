import json
from pathlib import Path

import pytest
from ai import term_matcher
from scripts.sync_chat_glossary import load_terms, sync_terms

DATA = Path(__file__).resolve().parents[1] / 'data'


def maintained_terms():
    return load_terms([DATA / 'chat_glossary_terms_v2.json', DATA / 'chat_glossary_terms_v3.json'])


def test_all_spellings_present_in_answer_are_returned(monkeypatch):
    monkeypatch.setattr(term_matcher, 'load_glossary_terms', lambda _: maintained_terms())
    _, glossary = term_matcher.find_terms_in_text('Fourth house, 4th House and House 4. Atmakaraka. Cusp Sub-Lord. KP. D24. Lagna and ascendant lord.')
    for label in ['fourth house', '4th house', 'house 4', 'atmakaraka', 'cusp sub-lord', 'kp', 'd24', 'lagna', 'ascendant lord']:
        assert glossary.get(label), label


@pytest.mark.parametrize('text', [
    'D24 Kashta own sign moolatrikona functionally benefic Yogi point Avayogi reversal house Tithi Dagdha Rashis',
    'Parashari Jaimini Nadi Sudarshana natal chart ascendant Lagna fourth lord fifth lord ninth lord',
    'cusp Star Lord sub-lord sub-sub-lord four-step theory signifies opposition aspects',
    'Pushya Uttara Ashadha fixed nakshatra nakshatra lord Vishve Devas',
    'Mercury Mars Jupiter Venus Saturn Rahu Ketu Sun Moon Taurus Scorpio Gemini Cancer Aries Pisces Virgo Sagittarius Leo Capricorn',
])
def test_audited_missing_terms_are_now_covered(text, monkeypatch):
    monkeypatch.setattr(term_matcher, 'load_glossary_terms', lambda _: maintained_terms())
    _, glossary = term_matcher.find_terms_in_text(text)
    labels = sorted(glossary, key=len, reverse=True)
    import re
    leftovers = re.sub(r'\b(?:' + '|'.join(map(re.escape, labels)) + r')\b', '', text, flags=re.I)
    assert not leftovers.strip(), leftovers


def test_sync_preserves_admin_definition_aliases_and_stable_id(monkeypatch):
    from scripts import sync_chat_glossary as sync
    written = []
    class Cursor:
        def fetchone(self):
            return ('Atmakarka', 'Admin-reviewed definition', 'english', '["Custom spelling"]')
    def execute(_conn, sql, params):
        if sql.lstrip().startswith('INSERT'):
            written.append(params)
        return Cursor()
    monkeypatch.setattr(sync, 'execute', execute)
    row = next(t for t in maintained_terms() if t['term_id'] == 'Atmakarka')
    sync_terms(object(), [row], preserve_existing=True)
    tid, display, definition, language, aliases = written[0]
    assert tid == 'Atmakarka'
    assert display == 'Atmakaraka'
    assert definition == 'Admin-reviewed definition'
    assert {'Custom spelling', 'Atmakarka', 'Atmakaraka'} <= set(json.loads(aliases))


def test_indic_aliases_are_returned_without_requiring_ascii_word_boundaries(monkeypatch):
    monkeypatch.setattr(term_matcher, 'load_glossary_terms', lambda _: [{'term_id':'महादशा', 'display_text':'महादशा', 'definition':'Main period', 'aliases':['महादशा काल']}])
    _, glossary = term_matcher.find_terms_in_text('महादशा काल और महादशा', 'hindi')
    assert glossary['महादशा काल'] == glossary['महादशा'] == 'Main period'
