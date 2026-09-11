import re

from tts.routes import _apply_pronunciation_plain, _plain_tts_chunks


def test_hindi_planets_are_disambiguated_without_changing_weekdays():
    spoken = _apply_pronunciation_plain(
        "मंगल दूसरे भाव में है, बुध मजबूत है, मंगलवार और बुधवार।"
    )
    assert spoken == "मंगल ग्रह दूसरे भाव में है, बुध ग्रह मजबूत है, मंगलवार और बुधवार।"


def test_existing_planet_context_and_mangal_dosh_are_preserved():
    spoken = _apply_pronunciation_plain("मंगल ग्रह, बुध ग्रह, मंगल दोष, Mangal and Budh graha")
    assert spoken == "मंगल ग्रह, बुध ग्रह, मंगल दोष, Mangal graha and Budh graha"


def test_long_unpunctuated_hindi_is_split_into_bounded_sentences():
    text = " ".join(["आपके दसवें घर का विस्तृत विश्लेषण करियर और सार्वजनिक जीवन बताता है"] * 45)
    chunks = _plain_tts_chunks(text)

    assert len(chunks) > 1
    assert all(len(chunk.encode("utf-8")) <= 1800 for chunk in chunks)
    for chunk in chunks:
        sentences = [part.strip() for part in re.split(r"[.!?।]", chunk) if part.strip()]
        assert all(len(sentence.encode("utf-8")) <= 700 for sentence in sentences)
