"""Checks for complete-case bootstrap aggregation and rescaling."""
import itertools
import unittest

import numpy as np

from access_bootstrap_probe import estimates_from_cells
from missingness_standardized_probe import four_group_contrast
from standardized_contrast_probe import contrast_and_scores


class AccessBootstrapTests(unittest.TestCase):
    def test_cell_aggregation_matches_record_level_estimator(self):
        rng = np.random.default_rng(904)
        counts = rng.uniform(.2, 4, size=(3, 3, 2, 2, 2))
        observed = estimates_from_cells(counts)
        age, income, insurance, group, outcome = np.indices(counts.shape)
        weight = counts.ravel()
        age, income, insurance, group, outcome = [x.ravel() for x in (age, income, insurance, group, outcome)]
        categories = [age, age * 3 + income, age * 6 + income * 2 + insurance]
        expected = [contrast_and_scores(weight, c, group, outcome)[0] for c in categories]
        np.testing.assert_allclose(observed, expected, rtol=0, atol=1e-14)

    def test_rescaled_with_replacement_stratum_has_expected_variance(self):
        # Exhaust all draws when n=3 and m=n-1=2, avoiding Monte Carlo noise.
        scores = np.array([.2, -.1, .6])
        draws = np.array([1.5 * scores[list(pair)].sum() for pair in itertools.product(range(3), repeat=2)])
        expected = 3 / 2 * np.sum((scores - scores.mean()) ** 2)
        self.assertAlmostEqual(draws.mean(), scores.sum())
        self.assertAlmostEqual(draws.var(), expected)

    def test_empty_group_is_rejected(self):
        cells = np.ones((3, 3, 2, 2, 2))
        cells[0, 0, 0, 1, :] = 0
        with self.assertRaises(ValueError):
            estimates_from_cells(cells)

    def test_four_group_standardization_scores_and_linearity(self):
        age = np.repeat(np.arange(3), 8)
        group = np.tile(np.repeat(np.arange(4), 2), 3)
        outcome = np.tile([0., 1.], 12)
        weights = np.random.default_rng(82).uniform(.5, 2, len(age))
        complete, s_complete, ref = four_group_contrast(weights, age, group, outcome, [-1, 1, 0, 0])
        incomplete, s_incomplete, _ = four_group_contrast(weights, age, group, outcome, [0, 0, -1, 1])
        delta, score, _ = four_group_contrast(weights, age, group, outcome, [-1, 1, 1, -1])
        self.assertAlmostEqual(delta, complete - incomplete)
        self.assertAlmostEqual(ref.sum(), 1)
        self.assertAlmostEqual(score.sum(), 0)
        np.testing.assert_allclose(score, s_complete - s_incomplete, atol=1e-14)
        for i in (0, 7, 13, 22):
            up, down = weights.copy(), weights.copy()
            up[i] *= 1.000001
            down[i] *= .999999
            hi = four_group_contrast(up, age, group, outcome, [-1, 1, 1, -1])[0]
            lo = four_group_contrast(down, age, group, outcome, [-1, 1, 1, -1])[0]
            self.assertAlmostEqual(score[i], (hi - lo) / .000002, places=8)


if __name__ == '__main__':
    unittest.main()
