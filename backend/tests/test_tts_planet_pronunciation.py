from tts.routes import _apply_pronunciation_plain


def test_hindi_planets_are_disambiguated_without_changing_weekdays():
    spoken = _apply_pronunciation_plain(
        "मंगल दूसरे भाव में है, बुध मजबूत है, मंगलवार और बुधवार।"
    )
    assert spoken == "मंगल ग्रह दूसरे भाव में है, बुध ग्रह मजबूत है, मंगलवार और बुधवार।"


def test_existing_planet_context_and_mangal_dosh_are_preserved():
    spoken = _apply_pronunciation_plain("मंगल ग्रह, बुध ग्रह, मंगल दोष, Mangal and Budh graha")
    assert spoken == "मंगल ग्रह, बुध ग्रह, मंगल दोष, Mangal graha and Budh graha"
