"""Tests for exact-match, weighted donor imputation."""
import itertools
import unittest

import numpy as np

from hotdeck_sensitivity import build_pools, impute_once
from hotdeck_masking_validation import majority_prediction, weighted_accuracy
from hotdeck_health_sensitivity import add_health_matching


class HotdeckTests(unittest.TestCase):
    def setUp(self):
        rows = []
        for a, group, event in itertools.product(range(3), range(2), range(2)):
            rows.extend((a, group, event, income, insurance, 1 + income + insurance)
                        for income, insurance in itertools.product(range(3), range(2)))
            rows.extend((a, group, event, -1, insurance, 1) for insurance in range(2))
            rows.extend((a, group, event, income, -1, 1) for income in range(3))
            rows.append((a, group, event, -1, -1, 1))
        values = np.asarray(rows)
        self.age, self.group, self.outcome, self.income, self.insurance, self.weight = values.T

    def test_exact_matching_and_preservation(self):
        pools = build_pools(self.age, self.group, self.outcome, self.income, self.insurance, self.weight)
        for p in pools:
            for indices in (p['donors'], p['recipients']):
                self.assertTrue(np.all(self.age[indices] == p['age']))
                self.assertTrue(np.all(self.group[indices] == p['group']))
                self.assertTrue(np.all(self.outcome[indices] == p['event']))
            if p['pattern'] == 'income_only':
                self.assertTrue(np.all(self.insurance[p['donors']] == self.insurance[p['recipients'][0]]))
            if p['pattern'] == 'insurance_only':
                self.assertTrue(np.all(self.income[p['donors']] == self.income[p['recipients'][0]]))
        filled_income, filled_insurance = impute_once(self.income, self.insurance, pools, np.random.default_rng(7))
        np.testing.assert_array_equal(filled_income[self.income >= 0], self.income[self.income >= 0])
        np.testing.assert_array_equal(filled_insurance[self.insurance >= 0], self.insurance[self.insurance >= 0])
        self.assertTrue(np.all((filled_income >= 0) & (filled_income <= 2)))
        self.assertTrue(np.all((filled_insurance >= 0) & (filled_insurance <= 1)))
        again = impute_once(self.income, self.insurance, pools, np.random.default_rng(7))
        np.testing.assert_array_equal(filled_income, again[0])
        np.testing.assert_array_equal(filled_insurance, again[1])

    def test_missing_donor_pool_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'No donor'):
            build_pools(np.array([0, 0]), np.array([0, 0]), np.array([0, 0]),
                        np.array([0, -1]), np.array([0, 1]), np.ones(2))

    def test_donor_sampling_respects_weight_proportions(self):
        n = 10000
        age = np.zeros(n + 2, dtype=int)
        group = np.zeros(n + 2, dtype=int)
        outcome = np.zeros(n + 2, dtype=int)
        income = np.r_[0, 2, np.full(n, -1)]
        insurance = np.zeros(n + 2, dtype=int)
        weight = np.r_[1., 3., np.ones(n)]
        pools = build_pools(age, group, outcome, income, insurance, weight)
        filled, _ = impute_once(income, insurance, pools, np.random.default_rng(11))
        self.assertLess(abs(np.mean(filled[2:] == 2) - .75), .02)

    def test_holdout_cannot_donate_and_majority_uses_weights(self):
        age = np.array([0, 0, 0])
        group = np.array([0, 0, 0])
        outcome = np.array([0, 0, 0])
        original_income = np.array([0, 2, 0])
        insurance = np.array([1, 1, 1])
        weight = np.array([1., 4., 1.])
        masked_income = np.array([0, 2, -1])
        pools = build_pools(age, group, outcome, masked_income, insurance, weight)
        self.assertNotIn(2, pools[0]['donors'])
        prediction = majority_prediction(original_income, insurance, weight, pools, 'income')
        self.assertEqual(prediction[2], 2)
        self.assertEqual(weighted_accuracy(np.array([0, 1]), np.array([0, 0]), np.array([3., 1.])), .75)

    def test_health_matching_and_documented_empty_pool_fallback(self):
        age = np.zeros(5, dtype=int)
        group = np.zeros(5, dtype=int)
        outcome = np.zeros(5, dtype=int)
        income = np.array([0, 2, -1, -1, -1])
        insurance = np.zeros(5, dtype=int)
        weight = np.array([1., 3., 1., 1., 1.])
        health = np.array([0, 1, 0, 1, 2])
        original = build_pools(age, group, outcome, income, insurance, weight)
        pools = add_health_matching(original, health, weight)
        self.assertEqual(len(pools), 3)
        for pool in pools:
            if pool['health'] == 2:
                self.assertTrue(pool['fallback'])
                np.testing.assert_array_equal(pool['donors'], [0, 1])
            else:
                self.assertFalse(pool['fallback'])
                self.assertTrue(np.all(health[pool['donors']] == pool['health']))
        filled, _ = impute_once(income, insurance, pools, np.random.default_rng(17))
        self.assertEqual(filled[2], 0)
        self.assertEqual(filled[3], 2)


if __name__ == '__main__':
    unittest.main()
