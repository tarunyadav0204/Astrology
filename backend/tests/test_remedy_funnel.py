from credits.remedy_funnel import VALID_EVENTS, record_funnel_event


def test_remedy_funnel_valid_events():
    assert VALID_EVENTS == frozenset({"card_shown", "card_clicked", "remedy_delivered"})


def test_remedy_funnel_record_invalid_event():
    try:
        record_funnel_event(userid=1, event_name="invalid")
        assert False, "expected ValueError"
    except ValueError:
        pass
