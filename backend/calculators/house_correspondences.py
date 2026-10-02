"""Shared classical correspondences that belong to the twelve bhavas.

Keep house-based anatomy here so chart insight, health analysis, and future
clients do not maintain different Kalapurusha mappings.
"""

from typing import Any, Dict


HOUSE_BODY: Dict[int, Dict[str, Any]] = {
    1: {"zones": ["head", "brain", "vitality", "overall body"], "role": "constitution / vitality"},
    2: {"zones": ["face", "mouth", "teeth", "throat", "sinuses"], "role": "intake / face-throat"},
    3: {"zones": ["shoulders", "arms", "hands", "lungs"], "role": "arms / breath effort"},
    4: {"zones": ["chest", "heart", "lungs", "digestive comfort"], "role": "chest / emotional gut"},
    5: {"zones": ["stomach", "spine", "heart region"], "role": "stomach / spine"},
    6: {"zones": ["abdomen", "immunity", "acute illness sites"], "role": "disease / immunity / accidents"},
    7: {"zones": ["kidneys", "lower back", "reproductive balance"], "role": "balance / lumbar"},
    8: {
        "zones": ["anus", "rectum", "pelvis", "excretory organs", "reproductive organs"],
        "role": "chronic / surgery / sudden events",
    },
    9: {"zones": ["hips", "thighs", "liver", "sciatic nerve"], "role": "thighs / mobility"},
    10: {"zones": ["knees", "bones", "joints"], "role": "knees / structure"},
    11: {"zones": ["calves", "ankles", "circulation"], "role": "circulation / lower legs"},
    12: {"zones": ["feet", "sleep", "recovery"], "role": "feet / rest / recovery"},
}


# The concise limb sequence stated for the Kālapuruṣa in BPHS and Saravali.
# It is read twice: naturally from Aries and individually from the natal Lagna.
# Keep this narrow. Expanded medical correspondences belong to HOUSE_BODY and
# the health engine, not to this classical header-level correspondence.
CLASSICAL_KALAPURUSHA_LIMBS = {
    1: ["head"],
    2: ["face"],
    3: ["arms"],
    4: ["chest", "heart"],
    5: ["stomach", "belly"],
    6: ["waist", "hips"],
    7: ["lower abdomen", "groin"],
    8: ["private organs"],
    9: ["thighs"],
    10: ["knees"],
    11: ["shanks", "ankles"],
    12: ["feet"],
}


def classical_house_body_parts(house_number: int):
    """Individual Kālapuruṣa limb counted from the natal Lagna."""
    return list(CLASSICAL_KALAPURUSHA_LIMBS.get(int(house_number), []))


def classical_sign_body_parts(sign_index: int):
    """Natural Kālapuruṣa limb counted from Aries (zero-based sign index)."""
    return list(CLASSICAL_KALAPURUSHA_LIMBS.get(int(sign_index) + 1, []))
