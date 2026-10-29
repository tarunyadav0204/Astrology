from ai import term_matcher


def test_maintained_english_glossary_fills_an_empty_database(monkeypatch):
    class BrokenConnection:
        def __enter__(self):
            raise RuntimeError("unseeded database")

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(term_matcher, "get_conn", lambda: BrokenConnection())

    terms, glossary = term_matcher.find_terms_in_text(
        "Jupiter begins a Mahadasha while Ashtakavarga and Combust conditions are reviewed.",
        language="english",
    )

    assert {"Jupiter", "Mahadasha", "Ashtakavarga", "Combust"}.issubset(set(terms))
    assert glossary["Jupiter"]
