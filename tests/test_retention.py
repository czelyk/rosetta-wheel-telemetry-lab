"""Byte accounting and evidence bounds for conventional telemetry products."""

import itertools
import unittest

from retention import BUDGETS, POLICIES, Sample, count_bounds, decode, decoded_peak, encode, extrema_bounds, quantize, reference_queries, region, score


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.samples = [Sample(2, 1000, 3971, -4), Sample(2, 2000, -3300, 11),
                        Sample(2, 3000, 1500, -2), Sample(0, 4000, 1200, -400)]
        self.counts = [1, 0, 3, 0]

    def test_all_products_fit_exact_application_allowance(self):
        for policy, budget in itertools.product(POLICIES, BUDGETS):
            packet = encode(self.samples, self.counts, 0, "nearest20", policy, budget)
            self.assertEqual(len(packet), budget)
            self.assertEqual(decode(packet)["admitted"], self.counts)

    def test_summary_answer_and_count_uncertainty(self):
        fixed = decode(encode(self.samples, self.counts, 0, "nearest20", "fixed_count20", 256))
        extrema = decode(encode(self.samples, self.counts, 0, "nearest20", "bin_extrema", 256))
        self.assertEqual(decoded_peak(fixed), (3971, {(2, 3)}))
        self.assertEqual(count_bounds(fixed, 2000)[2, 3], (2, 2))
        self.assertEqual(count_bounds(fixed, 3000)[2, 3], (1, 2))
        self.assertEqual(count_bounds(extrema, 2000)[2, 3], (2, 3))

    def test_extrema_bounds_cover_exhaustive_small_histories(self):
        values = (-3500, -2000, -1000, 0, 1000, 2000, 3500)
        for length in range(1, 5):
            for history in itertools.product(values, repeat=length):
                for level in (2000, 3000):
                    low, high = extrema_bounds(length, min(history), max(history), level)
                    count = sum(abs(value) >= level for value in history)
                    self.assertLessEqual(low, count)
                    self.assertGreaterEqual(high, count)

    def test_strongest_retention_counts_all_events_below_cutoff(self):
        samples = [Sample(2, tick, 100, 0) for tick in range(50)] + [Sample(2, 60, 4000, 0)]
        decoded = decode(encode(samples, [0, 0, 51, 0], 0, "prior20", "strongest", 256))
        self.assertEqual(len(decoded["records"]), 24)
        self.assertEqual(count_bounds(decoded, 2000)[2, 3], (1, 1))
        self.assertEqual(score(decoded, reference_queries(samples))["peak_exact"], 1)

    def test_sparse_periodic_retention_keeps_unknown_counts(self):
        samples = [Sample(0, tick, 100, 0) for tick in range(100)]
        decoded = decode(encode(samples, [100, 0, 0, 0], 0, "nearest20", "equispaced", 256))
        low, high = count_bounds(decoded, 2000)[0, 3]
        self.assertEqual(low, 0)
        self.assertGreater(high, 0)

    def test_quantization_and_bin_edges(self):
        sample = quantize(0, 0, -0.02, 0.5)
        self.assertEqual((sample.torque, sample.momentum), (-2000, 50))
        self.assertEqual(region(49), 3)
        self.assertEqual(region(50), 4)
        with self.assertRaises(ValueError):
            quantize(0, 0, 1.0, 0.0)

    def test_crc_rejects_accidental_single_bit_corruption(self):
        packet = bytearray(encode(self.samples, self.counts, 0, "nearest20", "bin_extrema", 256))
        packet[35] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC"):
            decode(packet)

    def test_empty_admission_and_missing_samples_are_retained(self):
        for policy in POLICIES:
            decoded = decode(encode([], [2, 3, 4, 5], 0, "prior20", policy, 256))
            self.assertEqual(decoded["unpaired"], [2, 3, 4, 5])
            self.assertEqual(decoded_peak(decoded), (None, set()))
            self.assertEqual(score(decoded, reference_queries([]))["nonempty"], 0)


if __name__ == "__main__":
    unittest.main()
