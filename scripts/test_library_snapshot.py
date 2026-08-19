"""Tests for library_snapshot.py's normalize().

Run with: python3 scripts/test_library_snapshot.py
"""

from __future__ import annotations

import unittest

from library_snapshot import normalize


class NormalizeTests(unittest.TestCase):
    def test_splits_multi_value_field(self):
        records = [{"genres": "Rock; Indie Rock; Shoegaze"}]
        self.assertEqual(
            normalize(records)[0]["genres"],
            ["Rock", "Indie Rock", "Shoegaze"],
        )

    def test_leaves_single_value_field_untouched(self):
        records = [{"album": "Loveless"}]
        self.assertEqual(normalize(records)[0]["album"], "Loveless")

    def test_empty_string_multi_value_field_becomes_empty_list(self):
        records = [{"genres": ""}]
        self.assertEqual(normalize(records)[0]["genres"], [])

    def test_missing_multi_value_field_is_not_added(self):
        records = [{"album": "Loveless"}]
        normalized = normalize(records)[0]
        self.assertNotIn("genres", normalized)

    def test_does_not_mutate_input_records(self):
        records = [{"genres": "Rock; Indie Rock"}]
        normalize(records)
        self.assertEqual(records[0]["genres"], "Rock; Indie Rock")


if __name__ == "__main__":
    unittest.main()
