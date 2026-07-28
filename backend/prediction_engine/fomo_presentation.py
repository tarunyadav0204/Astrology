from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Mapping, Sequence, Tuple

from .contracts import (
    ChartManifestation,
    FomoPresentation,
    Polarity,
)
from .errors import PredictionConfigurationError


FOMO_PRESENTATION_VERSION = "1.4.0"

_LOCALE_ALIASES = {
    "en": "en",
    "en-in": "en",
    "english": "en",
    "hi": "hi",
    "hi-in": "hi",
    "hindi": "hi",
}

_SUBJECT_FOCUS: Mapping[str, Mapping[str, Mapping[str, str]]] = {
    "en": {
        "self": {"display": "your {area}", "question": "my {area}"},
        "mother": {
            "display": "your mother’s {area}",
            "question": "my mother’s {area}",
        },
        "father": {
            "display": "your father’s {area}",
            "question": "my father’s {area}",
        },
        "spouse": {
            "display": "your partner’s {area}",
            "question": "my partner’s {area}",
        },
    },
    "hi": {
        "self": {
            "display": "आपके जीवन में {area} को लेकर",
            "question": "मेरे जीवन में {area} को लेकर",
        },
        "mother": {
            "display": "आपकी माता के जीवन में {area} को लेकर",
            "question": "मेरी माता के जीवन में {area} को लेकर",
        },
        "father": {
            "display": "आपके पिता के जीवन में {area} को लेकर",
            "question": "मेरे पिता के जीवन में {area} को लेकर",
        },
        "spouse": {
            "display": "आपके जीवनसाथी के जीवन में {area} को लेकर",
            "question": "मेरे जीवनसाथी के जीवन में {area} को लेकर",
        },
    },
}

# These are intentionally broad life areas. They must not contain the resolved
# manifestation label, summary, or bounded possibilities.
_DOMAIN_AREA: Mapping[str, Mapping[str, str]] = {
    "en": {
        "career": "career direction",
        "finance": "financial priorities",
        "relationship": "relationship direction",
        "property": "home and living situation",
        "education": "learning or family responsibilities",
        "travel": "movement and future plans",
        "health": "work and wellbeing",
        "family": "family priorities",
        "decisions": "important decisions",
    },
    "hi": {
        "career": "करियर",
        "finance": "आर्थिक प्राथमिकताओं",
        "relationship": "रिश्तों",
        "property": "घर और रहने की स्थिति",
        "education": "शिक्षा या पारिवारिक जिम्मेदारियों",
        "travel": "यात्रा और आगे की योजनाओं",
        "health": "काम और सेहत",
        "family": "पारिवारिक प्राथमिकताओं",
        "decisions": "महत्वपूर्ण फैसलों",
    },
}

_RELATIVE_HOUSE_AREA: Mapping[str, Mapping[int, str]] = {
    "en": {
        1: "personal direction and wellbeing",
        2: "family finances and speech",
        3: "communication and movement",
        4: "home and property",
        5: "learning, children, and creativity",
        6: "health, work, and obligations",
        7: "relationships and agreements",
        8: "shared finances and major adjustments",
        9: "guidance, higher learning, and travel",
        10: "career and authority",
        11: "income, goals, and networks",
        12: "expenses, distance, and release",
    },
    "hi": {
        1: "व्यक्तिगत दिशा और सेहत",
        2: "पारिवारिक धन और वाणी",
        3: "संवाद और आवागमन",
        4: "घर और संपत्ति",
        5: "शिक्षा, संतान और रचनात्मकता",
        6: "सेहत, काम और दायित्व",
        7: "रिश्ते और समझौते",
        8: "साझा धन और बड़े समायोजन",
        9: "मार्गदर्शन, उच्च शिक्षा और यात्रा",
        10: "करियर और अधिकार",
        11: "आय, लक्ष्य और संपर्क",
        12: "खर्च, दूरी और मुक्ति",
    },
}

_COMBINED_AREA: Mapping[str, Mapping[str, str]] = {
    "en": {
        "pair": "{first} and {second}",
        "list": "{leading}, and {last}",
        "overflow": "{leading}, and other connected matters",
    },
    "hi": {
        "pair": "{first} और {second}",
        "list": "{leading} और {last}",
        "overflow": "{leading} और अन्य जुड़े विषयों",
    },
}

_TEMPLATES: Mapping[str, Mapping[Polarity, Mapping[str, str]]] = {
    "en": {
        Polarity.SUPPORTIVE: {
            "title": "Is something beginning to open around {focus}?",
            "teaser": (
                "Several independent chart indications are aligning around this "
                "part of life. The important detail appears only when those "
                "connections are read together."
            ),
            "question": (
                "What may manifest over the next few months around "
                "{question_focus}, when is it most likely, and how should I prepare?"
            ),
        },
        Polarity.MIXED: {
            "title": "A turning point may be forming around {focus}",
            "teaser": (
                "The chart shows movement here, but the indications do not all "
                "pull in one direction. Understanding what is progressing and "
                "what needs adjustment can change how you handle it."
            ),
            "question": (
                "What may manifest over the next few months around "
                "{question_focus}, when is it most likely, and how should I prepare?"
            ),
        },
        Polarity.CHALLENGING: {
            "title": "Something around {focus} may need closer attention",
            "teaser": (
                "A repeated chart pattern suggests that preparation and timing "
                "matter in this area. Reading the connected indications together "
                "can show what deserves attention before you act."
            ),
            "question": (
                "What may manifest over the next few months around "
                "{question_focus}, when is it most likely, and how should I prepare?"
            ),
        },
        Polarity.NEUTRAL: {
            "title": "Why is your chart highlighting {focus}?",
            "teaser": (
                "This area is active, although the direction is not settled "
                "enough to call positive or difficult. The connected chart "
                "factors explain what is coming into focus."
            ),
            "question": (
                "What may manifest over the next few months around "
                "{question_focus}, when is it most likely, and how should I prepare?"
            ),
        },
    },
    "hi": {
        Polarity.SUPPORTIVE: {
            "title": "क्या {focus} कोई नया रास्ता खुल रहा है?",
            "teaser": (
                "कुंडली के कई स्वतंत्र संकेत जीवन के इसी हिस्से की ओर इशारा कर "
                "रहे हैं। महत्वपूर्ण बात तभी स्पष्ट होती है जब इन जुड़े संकेतों "
                "को एक साथ पढ़ा जाए।"
            ),
            "question": (
                "अगले कुछ महीनों में {question_focus} क्या घटित हो सकता है, "
                "इसका सबसे संभावित समय क्या है, और मुझे कैसे तैयारी करनी चाहिए?"
            ),
        },
        Polarity.MIXED: {
            "title": "{focus} एक महत्वपूर्ण मोड़ बन रहा है",
            "teaser": (
                "यहां हलचल दिखाई देती है, लेकिन सभी संकेत एक ही दिशा में नहीं "
                "हैं। क्या आगे बढ़ रहा है और कहां समायोजन चाहिए—यह समझना आपके "
                "फैसले को बदल सकता है।"
            ),
            "question": (
                "अगले कुछ महीनों में {question_focus} क्या घटित हो सकता है, "
                "इसका सबसे संभावित समय क्या है, और मुझे कैसे तैयारी करनी चाहिए?"
            ),
        },
        Polarity.CHALLENGING: {
            "title": "{focus} से जुड़ा एक संकेत ध्यान मांग रहा है",
            "teaser": (
                "बार-बार बनता हुआ एक ज्योतिषीय संकेत बताता है कि इस विषय में "
                "तैयारी और सही समय महत्वपूर्ण हैं। पूरी बात जुड़े संकेतों को "
                "देखने पर ही सामने आती है।"
            ),
            "question": (
                "अगले कुछ महीनों में {question_focus} क्या घटित हो सकता है, "
                "इसका सबसे संभावित समय क्या है, और मुझे कैसे तैयारी करनी चाहिए?"
            ),
        },
        Polarity.NEUTRAL: {
            "title": "आपकी कुंडली {focus} पर ध्यान क्यों दिला रही है?",
            "teaser": (
                "यह विषय सक्रिय है, लेकिन दिशा अभी इतनी स्पष्ट नहीं कि इसे "
                "सकारात्मक या कठिन कहा जाए। जुड़े हुए संकेत बताते हैं कि किस "
                "बात पर ध्यान देना चाहिए।"
            ),
            "question": (
                "अगले कुछ महीनों में {question_focus} क्या घटित हो सकता है, "
                "इसका सबसे संभावित समय क्या है, और मुझे कैसे तैयारी करनी चाहिए?"
            ),
        },
    },
}


def normalize_fomo_locale(locale: str) -> str:
    normalized = str(locale or "").strip().lower().replace("_", "-")
    resolved = _LOCALE_ALIASES.get(normalized)
    if resolved is None:
        raise PredictionConfigurationError(
            f"Unsupported FOMO presentation locale: {locale!r}"
        )
    return resolved


def _manifestation_domains(manifestation: ChartManifestation) -> Tuple[str, ...]:
    if manifestation.domain != "combined":
        return (manifestation.domain,)
    domains = tuple(dict.fromkeys(
        str(row.get("domain") or "").strip()
        for row in manifestation.constituent_themes
        if str(row.get("domain") or "").strip()
    ))
    if len(domains) < 2:
        raise PredictionConfigurationError(
            "Combined chart manifestation does not declare at least two "
            f"constituent domains: {manifestation.manifestation_id}"
        )
    return domains


def _area(locale: str, manifestation: ChartManifestation) -> str:
    required_native_houses = {
        int(house)
        for theme in manifestation.constituent_themes
        if isinstance(theme, Mapping)
        for house in (theme.get("required_native_houses") or ())
    }
    relative_houses = tuple(dict.fromkeys(
        int(role.relative_house)
        for role in manifestation.house_roles
        if (
            not required_native_houses
            or int(role.native_house) in required_native_houses
        )
    ))
    try:
        translated = (
            tuple(_RELATIVE_HOUSE_AREA[locale][house] for house in relative_houses)
            if relative_houses
            else tuple(
                _DOMAIN_AREA[locale][domain]
                for domain in _manifestation_domains(manifestation)
            )
        )
        if len(translated) == 1:
            return translated[0]
        if len(translated) == 2:
            return _COMBINED_AREA[locale]["pair"].format(
                first=translated[0],
                second=translated[1],
            )
        if len(translated) <= 4:
            return _COMBINED_AREA[locale]["list"].format(
                leading=", ".join(translated[:-1]),
                last=translated[-1],
            )
        return _COMBINED_AREA[locale]["overflow"].format(
            leading=", ".join(translated[:4]),
        )
    except KeyError as exc:
        raise PredictionConfigurationError(
            "Missing deterministic FOMO wording for "
            f"locale={locale}, subject={manifestation.subject}, "
            f"domain={manifestation.domain}, relative_houses={relative_houses}"
        ) from exc


def _focus(
    locale: str,
    manifestation: ChartManifestation,
) -> Tuple[str, str]:
    try:
        area = _area(locale, manifestation)
        patterns = _SUBJECT_FOCUS[locale][manifestation.subject]
        return (
            patterns["display"].format(area=area),
            patterns["question"].format(area=area),
        )
    except KeyError as exc:
        raise PredictionConfigurationError(
            "Missing deterministic FOMO wording for "
            f"locale={locale}, subject={manifestation.subject}, "
            f"domain={manifestation.domain}"
        ) from exc


@dataclass(frozen=True)
class FomoPresentationAdapter:
    version: str = FOMO_PRESENTATION_VERSION

    def present(
        self,
        manifestations: Sequence[ChartManifestation],
        *,
        locale: str,
    ) -> Tuple[FomoPresentation, ...]:
        resolved_locale = normalize_fomo_locale(locale)
        output = []
        for manifestation in manifestations:
            area = _area(resolved_locale, manifestation)
            focus, question_focus = _focus(resolved_locale, manifestation)
            try:
                template = _TEMPLATES[resolved_locale][manifestation.outcome_tone]
            except KeyError as exc:
                raise PredictionConfigurationError(
                    "Missing deterministic FOMO tone template for "
                    f"locale={resolved_locale}, "
                    f"tone={manifestation.outcome_tone.value}"
                ) from exc
            values = {
                "focus": focus,
                "question_focus": question_focus,
            }
            presentation_id = hashlib.sha256(
                (
                    f"{manifestation.manifestation_id}|{resolved_locale}|"
                    f"{self.version}"
                ).encode("utf-8")
            ).hexdigest()[:32]
            output.append(FomoPresentation(
                presentation_id=presentation_id,
                manifestation_id=manifestation.manifestation_id,
                locale=resolved_locale,
                subject=manifestation.subject,
                domain=manifestation.domain,
                area_label=area,
                tone=manifestation.outcome_tone,
                title=template["title"].format(**values),
                teaser=template["teaser"].format(**values),
                suggested_question=template["question"].format(**values),
                rule_id="deterministic_subject_domain_tone_template",
                template_version=self.version,
            ))
        return tuple(output)
