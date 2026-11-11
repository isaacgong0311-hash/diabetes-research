"""Mathematical checks for the annual shared-reference contrast."""
import unittest

import numpy as np

from annual_contrast_probe import analytic_gradients, derivative, standardized_difference
from annual_simulation import cell_proportions, scores


class AnnualContrastTests(unittest.TestCase):
    def test_analytic_gradients_match_numerical_perturbations(self):
        rng = np.random.default_rng(498)
        for _ in range(20):
            ref = rng.dirichlet(np.full(12, 3.0))
            year = rng.dirichlet(np.full(12, 3.0))
            ref_gradient, year_gradient = analytic_gradients(ref, year)
            numeric_ref = derivative(lambda x: standardized_difference(x, year) - standardized_difference(x, x), ref)
            numeric_year = derivative(lambda x: standardized_difference(ref, x) - standardized_difference(ref, ref), year)
            np.testing.assert_allclose(ref_gradient, numeric_ref, atol=1e-8, rtol=1e-7)
            np.testing.assert_allclose(year_gradient, numeric_year, atol=1e-8, rtol=1e-7)

    def test_equal_samples_cancel_and_scaling_does_not_change_result(self):
        ref = np.arange(1, 13, dtype=float)
        ref /= ref.sum()
        g_ref, g_year = analytic_gradients(ref, ref)
        np.testing.assert_allclose(g_ref + g_year, 0, atol=1e-12)
        self.assertAlmostEqual(standardized_difference(ref, ref), standardized_difference(ref * 4, ref * 7))

    def test_equal_group_rates_give_zero(self):
        ref = np.array([.1, .2, .1, .2, .1, .2, .1, .2, .1, .2, .1, .2])
        self.assertAlmostEqual(standardized_difference(ref, ref), 0.0)

    def test_case_weight_scores_match_perturbations(self):
        rng = np.random.default_rng(502)
        age = np.repeat(np.arange(3), 4)
        group = np.tile(np.repeat([0, 1], 2), 3)
        outcome = np.tile([0, 1], 6)
        weights = [rng.uniform(.2, 3, 12), rng.uniform(.2, 3, 12)]
        p0, i0 = cell_proportions(weights[0], age, group, outcome)
        p1, i1 = cell_proportions(weights[1], age, group, outcome)
        gradients = analytic_gradients(p0, p1)
        actual = [scores(weights[0], i0, p0, gradients[0]), scores(weights[1], i1, p1, gradients[1])]
        def comparison(a, b):
            x = cell_proportions(a, age, group, outcome)[0]
            y = cell_proportions(b, age, group, outcome)[0]
            return standardized_difference(x, y) - standardized_difference(x, x)
        for year in (0, 1):
            for index in range(12):
                up = [w.copy() for w in weights]
                down = [w.copy() for w in weights]
                up[year][index] *= 1.000001
                down[year][index] *= .999999
                numeric = (comparison(*up) - comparison(*down)) / .000002
                self.assertAlmostEqual(actual[year][index], numeric, places=8)


if __name__ == '__main__':
    unittest.main()
