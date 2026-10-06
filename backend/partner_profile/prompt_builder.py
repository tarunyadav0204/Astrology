"""Translate resolved chart evidence into constrained image prompts.

The generator is not allowed to reinterpret astrology.  It receives only the
attributes that survived the deterministic resolver and a few user-selected
art-direction choices.
"""

from __future__ import annotations

from typing import Any, Mapping


VISUAL_CONTEXTS = {
    "south_asian": "South Asian regional appearance and setting",
    "east_southeast_asian": "East or Southeast Asian regional appearance and setting",
    "middle_eastern_north_african": "Middle Eastern or North African regional appearance and setting",
    "sub_saharan_african": "Sub-Saharan African regional appearance and setting",
    "european": "European regional appearance and setting",
    "latin_american": "Latin American regional appearance and setting",
    "north_american": "North American multicultural appearance and setting",
    "central_asian": "Central Asian regional appearance and setting",
    "oceania": "Oceanian, Australian or Pacific regional appearance and setting",
    "global_mixed": "globally neutral or mixed-heritage appearance and setting",
}

CLOTHING_DIRECTIONS = {
    "contemporary": "contemporary clothing appropriate to the selected regional context",
    "traditional_regional": "tasteful traditional clothing appropriate to the selected regional context",
    "modern_formal": "modern formal clothing appropriate to the selected regional context",
    # Backward-compatible values used by builds released before regional choice.
    "contemporary_indian": "contemporary clothing appropriate to the selected regional context",
    "classic_indian": "tasteful traditional clothing appropriate to the selected regional context",
}

PRESENTATIONS = {"feminine": "adult woman", "masculine": "adult man"}


def _complexion_prompt_ready(primary: Mapping[str, Any]) -> bool:
    """Only send complexion to the image model when evidence is corroborated.

    A single suggestive channel (often spouse karaka before 1.5.0) was enough to
    lock portraits into an overly dark tone. Moderate-or-strong confidence, or
    two independent marriage channels, is the minimum bar for a hard instruction.
    """
    if primary.get("confidence") in {"strong", "moderate"}:
        return True
    evidence = list(primary.get("evidence") or [])
    independent = len({row.get("independence") for row in evidence if row.get("independence")})
    return independent >= 2


def _complexion_trait(result: Mapping[str, Any], primary: Mapping[str, Any]) -> str:
    """Phrase complexion for the image model, softening close classical conflicts."""
    value = str(primary.get("value") or "")
    alternatives = [row for row in (result.get("alternatives") or []) if isinstance(row, Mapping) and row.get("value")]
    if not alternatives:
        return f"complexion: {value}"
    alternative = alternatives[0]
    primary_support = float(primary.get("effective_repetitions") or 0.0)
    alternative_support = float(alternative.get("effective_repetitions") or 0.0)
    if alternative_support >= primary_support * 0.75:
        # When two classical tones are nearly tied, avoid forcing an extreme.
        return (
            f"complexion: balanced between {value} and {alternative['value']}; "
            "render a natural middle tone without pushing toward either extreme"
        )
    return f"complexion: {value}"


def _resolved_traits(profile: Mapping[str, Any]) -> list[str]:
    traits: list[str] = []
    appearance = profile.get("appearance") or {}
    # Complexion needs an explicit instruction before regional context reaches
    # the image model; otherwise it tends to invent one from regional priors.
    ordered_attributes = sorted(appearance, key=lambda value: (value != "complexion", value))
    for attribute in ordered_attributes:
        result = appearance[attribute]
        primary = result.get("primary") if isinstance(result, dict) else None
        if not isinstance(primary, dict):
            continue
        # Complexion and head hair use corroboration gates so a lone Venus
        # spouse-karaka signal cannot lock every male portrait into brown skin
        # or curls. Other attributes still need moderate/strong confidence.
        if attribute == "complexion":
            if not _complexion_prompt_ready(primary):
                continue
        elif attribute in {"hair", "head_hair"}:
            if not _complexion_prompt_ready(primary):
                continue
        elif primary.get("confidence") not in {"strong", "moderate"}:
            continue
        # Body-hair wording in BPHS describes Scorpio's form. It is retained in
        # the textual evidence, but a clothed portrait cannot represent it
        # responsibly and the image model must not turn it into head hair.
        if attribute == "body_hair":
            continue
        value = str(primary.get("value") or "")
        if attribute in {"hair", "head_hair"} and value in {"sparse hair", "less abundant hair"}:
            traits.append(
                "head hair: naturally fine or lower-volume hair with normal scalp coverage; "
                "not bald, balding, shaved, or visibly hairless"
            )
            continue
        if attribute in {"hair", "head_hair"} and value == "coarse hair":
            # BPHS 3.29 describes Saturn's hair texture as coarse; it does not
            # state that the hair is dense or abundant. Image models otherwise
            # tend to turn "coarse" into a thick, luxuriant hairstyle.
            traits.append(
                "head hair: coarse-textured or slightly wiry hair with ordinary natural coverage; "
                "density is unspecified, so do not make it unusually thick, dense, or luxuriant"
            )
            continue
        if attribute in {"hair", "head_hair"} and value in {
            "curly hair",
            "soft wavy or gently curled hair",
        }:
            # BPHS 3.28 vakramūrdhaja supports curl, but "curly" alone makes
            # image models overdo tight ringlets. Prefer soft wave unless
            # stronger classical wording is supplied later.
            traits.append(
                "head hair: soft natural waves or gentle curls; "
                "not tight ringlets, not overly curly, not a defined curly-hair stereotype"
            )
            continue
        if attribute == "complexion":
            traits.append(_complexion_trait(result, primary))
            continue
        traits.append(f"{attribute.replace('_', ' ')}: {value}")
    return traits[:8]


def build_portrait_prompt(
    profile: Mapping[str, Any], *, presentation: str, age_band: str, clothing_style: str,
    visual_context: str = "global_mixed",
) -> str:
    traits = "; ".join(_resolved_traits(profile)) or "balanced, natural adult appearance"
    context = VISUAL_CONTEXTS.get(visual_context, VISUAL_CONTEXTS["global_mixed"])
    clothing = CLOTHING_DIRECTIONS.get(clothing_style, CLOTHING_DIRECTIONS["contemporary"])
    person = PRESENTATIONS[presentation]
    return (
        "Create a respectful photorealistic editorial portrait of one fictional adult. "
        f"The user explicitly selected an {person}. Apparent age: {age_band}. "
        f"Birth-location-derived visual context: {context}. This sets regional visual context, not complexion. "
        f"Resolved visual archetype: {traits}. Clothing: {clothing}. "
        "Treat regional context and complexion as independent instructions. Regional context must never determine, "
        "darken, lighten, or override skin tone. In particular, do not default a South Asian person to wheatish, "
        "medium-brown, or dark skin. Follow the resolved complexion exactly when it is supplied. "
        "Head and shoulders, natural expression, realistic anatomy, elegant neutral studio setting, "
        "premium magazine photography, no text, no symbols on the body. Do not add cultural or religious symbols "
        "unless required by the selected clothing direction. Do not infer caste, religion, disability, identity, "
        "or socioeconomic status. Do not depict baldness, a shaved head, a receding hairline, or severe hair loss; "
        "a lower-volume hair indication still requires natural scalp coverage. "
        "This is a symbolic artistic archetype, not a photograph of a real or future person."
    )


def build_full_body_prompt(
    profile: Mapping[str, Any], *, presentation: str, age_band: str, clothing_style: str,
    visual_context: str = "global_mixed",
) -> str:
    traits = "; ".join(_resolved_traits(profile)) or "balanced, natural adult appearance"
    context = VISUAL_CONTEXTS.get(visual_context, VISUAL_CONTEXTS["global_mixed"])
    clothing = CLOTHING_DIRECTIONS.get(clothing_style, CLOTHING_DIRECTIONS["contemporary"])
    person = PRESENTATIONS[presentation]
    return (
        "Preserve the exact same fictional person's face, hair and identity from the input portrait. "
        f"Show a natural full-body standing view of the user-selected {person}. Apparent age: {age_band}. "
        f"Keep the birth-location-derived visual context: {context}. Resolved visual archetype, including body build: {traits}. "
        "Preserve the reference portrait's complexion exactly. Regional context must never darken, lighten, or "
        "override skin tone, and must not cause a default wheatish South Asian complexion. "
        f"Clothing: {clothing}. Realistic proportions, relaxed posture, premium editorial photography, "
        "a tasteful neutral interior appropriate to the selected regional context, "
        "no text, no astrological labels, no body exaggeration. Preserve natural scalp coverage and do not turn a "
        "lower-volume hair indication into baldness, a shaved head, a receding hairline, or severe hair loss. "
        "Any unspecified visual detail is ordinary artistic "
        "completion and must not be treated as an astrological claim."
    )
