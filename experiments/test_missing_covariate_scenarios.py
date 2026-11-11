"""Checks for deterministic missing-covariate stress scenarios."""
import unittest

import numpy as np

from missing_covariate_scenarios import scenario_estimate
from standardized_contrast_probe import contrast_and_scores


class MissingCovariateScenarioTests(unittest.TestCase):
    def setUp(self):
        self.age, self.income, self.insurance, self.group = [x.ravel() for x in np.indices((3, 3, 2, 2))]
        self.weight = np.random.default_rng(14).uniform(.5, 4, len(self.age))
        self.outcome = ((self.age + self.income + self.insurance + self.group) % 3 == 0).astype(float)

    def test_assignments_do_not_change_fully_observed_data(self):
        baseline, _ = scenario_estimate(self.weight, self.age, self.income, self.insurance,
                                        self.group, self.outcome, 0, 0)
        for no, yes in ((0, 5), (5, 0), (3, 4)):
            rates, _ = scenario_estimate(self.weight, self.age, self.income, self.insurance,
                                         self.group, self.outcome, no, yes)
            np.testing.assert_allclose(rates, baseline, rtol=0, atol=1e-14)

    def test_missing_fields_are_filled_and_match_direct_standardization(self):
        # Repeat all cells so replacing a missing value never leaves a cell empty.
        age, income, insurance, group, outcome, weight = [np.tile(x, 2) for x in
            (self.age, self.income, self.insurance, self.group, self.outcome, self.weight)]
        income[0], insurance[1], income[-1] = -1, -1, -1
        no, yes = 2, 5
        rates, min_n = scenario_estimate(weight, age, income, insurance, group, outcome, no, yes)
        chosen = np.where(group == 1, yes, no)
        category = age * 6 + np.where(income < 0, chosen // 2, income) * 2 + np.where(insurance < 0, chosen % 2, insurance)
        direct, _ = contrast_and_scores(weight, category, group, outcome)
        self.assertAlmostEqual(rates[1] - rates[0], direct, places=13)
        self.assertGreater(min_n, 0)

    def test_fixed_standard_is_used_for_both_groups(self):
        reference = np.arange(1, 19, dtype=float)
        rates, _ = scenario_estimate(self.weight, self.age, self.income, self.insurance,
                                     self.group, self.outcome, 0, 5, reference)
        expected = []
        cells = self.age * 6 + self.income * 2 + self.insurance
        for group in (0, 1):
            group_rates = [self.outcome[(cells == cell) & (self.group == group)][0] for cell in range(18)]
            expected.append(np.dot(reference, group_rates) / reference.sum())
        np.testing.assert_allclose(rates, expected, rtol=0, atol=1e-14)


if __name__ == '__main__':
    unittest.main()
