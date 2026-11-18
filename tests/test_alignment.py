"""Boundary regressions for retrospective and prior-only matching."""

import hashlib
import unittest

from rosetta import coverage, milliseconds, momentum_match, verify_content


class AlignmentTests(unittest.TestCase):
    def test_exact_match_needs_no_future_sample(self):
        result = momentum_match([10_000, 74_000], [-0.1, 0.2], 10_000)
        self.assertEqual(result["previous_Nms"], -0.1)
        self.assertEqual(result["interpolated_Nms"], -0.1)
        self.assertEqual(result["next_delay_s"], 0.0)

    def test_future_nearest_does_not_count_as_prior(self):
        result = coverage([(52_000, 0.01), (200_000, 0.01)], [(0, -0.1), (64_000, 0.2)], "C", "fixture")
        self.assertEqual(result["symmetric_within_20s"], 1)
        self.assertEqual(result["prior_within_20s"], 0)
        self.assertEqual(result["nearest_is_future_within_20s"], 1)

    def test_tolerance_boundary_is_inclusive(self):
        result = coverage([(20_000, 0.01), (200_000, 0.01)], [(0, 1.0), (64_000, 2.0)], "A", "fixture")
        self.assertEqual(result["prior_within_20s"], 1)
        result = coverage([(20_001, 0.01), (200_000, 0.01)], [(0, 1.0), (64_000, 2.0)], "A", "fixture")
        self.assertEqual(result["prior_within_20s"], 0)

    def test_nearest_tie_chooses_previous(self):
        result = momentum_match([0, 64_000], [-0.1, 0.2], 32_000)
        self.assertEqual(result["nearest_Nms"], -0.1)
        self.assertTrue(result["sign_change_across_bracket"])

    def test_interpolation_stops_at_large_gaps(self):
        self.assertIsNotNone(momentum_match([0, 128_000], [0.0, 1.0], 64_000)["interpolated_Nms"])
        self.assertIsNone(momentum_match([0, 128_001], [0.0, 1.0], 64_000)["interpolated_Nms"])

    def test_missing_side_is_explicit(self):
        before = momentum_match([10_000, 74_000], [0.0, 1.0], 0)
        after = momentum_match([10_000, 74_000], [0.0, 1.0], 90_000)
        self.assertIsNone(before["previous_Nms"])
        self.assertIsNone(after["next_Nms"])
        self.assertIsNone(before["interpolated_Nms"])
        self.assertIsNone(after["interpolated_Nms"])

    def test_timestamp_preserves_integer_milliseconds(self):
        self.assertEqual(milliseconds("2000-01-02T00:00:00.123"), 86_400_123)

    def test_same_length_corruption_fails_checksum(self):
        entry = {"size": 3, "path": "fixture.tab", "sha256": hashlib.sha256(b"abc").hexdigest()}
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_content(b"abd", entry)


if __name__ == "__main__":
    unittest.main()
