"""Tests for category-based divisional chart merge (canonical bundles)."""

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from ai.intent_router import merge_divisional_charts_with_category_defaults


def test_education_appends_d24_when_missing():
    r = {"category": "education", "divisional_charts": ["D1", "D9", "D10"]}
    merge_divisional_charts_with_category_defaults(r)
    assert r["divisional_charts"] == ["D1", "D9", "D10", "D24"]


def test_learning_dedupes_and_normalizes_case():
    r = {"category": "learning", "divisional_charts": ["d1", "D1", "D9"]}
    merge_divisional_charts_with_category_defaults(r)
    assert r["divisional_charts"] == ["D1", "D9", "D24"]


def test_career_unchanged_when_complete():
    r = {"category": "career", "divisional_charts": ["D1", "D9", "D10", "Karkamsa"]}
    merge_divisional_charts_with_category_defaults(r)
    assert r["divisional_charts"] == ["D1", "D9", "D10", "Karkamsa"]


def test_career_adds_karkamsa_when_omitted():
    r = {"category": "career", "divisional_charts": ["D1", "D9", "D10"]}
    merge_divisional_charts_with_category_defaults(r)
    assert r["divisional_charts"] == ["D1", "D9", "D10", "Karkamsa"]


def test_education_invalid_list_replaced_with_defaults():
    r = {"category": "education", "divisional_charts": "not a list"}
    merge_divisional_charts_with_category_defaults(r)
    assert r["divisional_charts"] == ["D1", "D9", "D24"]


def test_property_adds_d12():
    r = {"category": "property", "divisional_charts": ["D1", "D9"]}
    merge_divisional_charts_with_category_defaults(r)
    assert r["divisional_charts"] == ["D1", "D9", "D4", "D12"]
