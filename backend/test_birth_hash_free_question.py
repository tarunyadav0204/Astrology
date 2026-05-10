"""Unit tests for canonical birth hash used in free-question / chart policy."""
from __future__ import annotations

import unittest

from utils.birth_hash import (
    birth_hash_from_birth_details_dict,
    birth_hash_from_parts,
    normalize_birth_fields_for_hash,
)


class TestBirthHashNormalization(unittest.TestCase):
    def test_coords_round_to_six_decimals(self):
        a = birth_hash_from_parts("1990-05-01", "14:30", 28.6139, 77.209)
        b = birth_hash_from_parts("1990-05-01", "14:30", 28.613899999, 77.2090001)
        self.assertEqual(a, b)

    def test_iso_date_time_split(self):
        d = {"date": "1990-05-01T00:00:00", "time": "1970-01-01T14:05:00", "latitude": 12.0, "longitude": 77.0}
        h = birth_hash_from_birth_details_dict(d)
        parts = normalize_birth_fields_for_hash("1990-05-01", "14:05", 12.0, 77.0)
        self.assertIsNotNone(parts)
        self.assertEqual(h, birth_hash_from_parts(*parts))

    def test_time_strips_seconds(self):
        a = birth_hash_from_parts("2000-01-01", "09:30:59", 1.0, 2.0)
        b = birth_hash_from_parts("2000-01-01", "09:30", 1.0, 2.0)
        self.assertEqual(a, b)

    def test_credit_service_static_matches_utils(self):
        from credits.credit_service import CreditService

        d = {"date": "1991-06-15", "time": "10:00", "latitude": 19.076, "longitude": 72.8777}
        self.assertEqual(
            CreditService.create_free_question_birth_hash(d),
            birth_hash_from_birth_details_dict(d),
        )

    def test_invalid_returns_none(self):
        self.assertIsNone(birth_hash_from_parts("", "10:00", 1.0, 2.0))
        self.assertIsNone(birth_hash_from_birth_details_dict({"date": "x"}))


if __name__ == "__main__":
    unittest.main()
