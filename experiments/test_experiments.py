"""Small checks for statistics and patient-selection logic."""
import unittest
import numpy as np
import pandas as pd

from model_experiment import auc, average_precision, cohort_from, fit_predict
from readmission_experiment import stats
from robustness_experiment import split
from standardization_experiment import estimate
from brfss_analysis import standardize_age, weighted_rate
from brfss_access_standardization import standardized
from survey_variance_probe import ratio_linearized
from standardized_contrast_probe import contrast_and_scores, design_variance


class ExperimentsTest(unittest.TestCase):
    def test_auc_and_average_precision_with_ties(self):
        y = np.array([1, 0, 1, 0])
        prediction = np.array([0.9, 0.9, 0.4, 0.1])
        self.assertAlmostEqual(auc(y, prediction), 0.625)
        self.assertAlmostEqual(average_precision(y, prediction), 7/12)

    def test_wilson_interval_contains_proportion(self):
        result = stats([{'readmitted': '<30'}] * 2 + [{'readmitted': 'NO'}] * 8)
        self.assertEqual(result['n'], 10)
        self.assertEqual(result['events'], 2)
        self.assertLess(result['ci_low'], 0.2)
        self.assertGreater(result['ci_high'], 0.2)

    def test_selection_precedes_exclusion(self):
        rows = [
            {'patient_nbr': 'a', 'encounter_id': '1', 'discharge_disposition_id': '11'},
            {'patient_nbr': 'a', 'encounter_id': '2', 'discharge_disposition_id': '1'},
            {'patient_nbr': 'b', 'encounter_id': '4', 'discharge_disposition_id': '1'},
            {'patient_nbr': 'b', 'encounter_id': '3', 'discharge_disposition_id': '1'},
        ]
        self.assertEqual([r['encounter_id'] for r in cohort_from(rows)], ['3'])

    def test_split_has_no_overlap_and_preserves_outcomes(self):
        y = np.array([0] * 80 + [1] * 20)
        train, test = split(y, 11)
        self.assertFalse(set(train) & set(test))
        self.assertEqual(len(train), 80)
        self.assertEqual(int(y[test].sum()), 4)

    def test_intercept_only_data_predict_training_prevalence(self):
        x = np.ones((100, 1))
        y = np.array([0] * 80 + [1] * 20)
        predicted, gradient = fit_predict(x, y, np.ones((2, 1)))
        np.testing.assert_allclose(predicted, [0.2, 0.2], atol=1e-10)
        self.assertLess(gradient, 1e-10)

    def test_standardization_and_overlap(self):
        strata = np.repeat(np.arange(8), 4)
        recorded = np.tile([0, 0, 1, 1], 8)
        outcome = np.tile([0, 1, 1, 1], 8)
        counts, events, standardized = estimate(outcome, recorded, strata)
        np.testing.assert_array_equal(counts, np.full((8, 2), 2))
        np.testing.assert_allclose(standardized, [0.5, 1.0])
        with self.assertRaises(ValueError):
            estimate(outcome[:-1], recorded[:-1] * 0, strata[:-1])

    def test_weighted_age_standardization(self):
        df = pd.DataFrame({'_AGEG5YR': [1, 1, 6, 6], 'DIABETE4': [1, 3, 1, 3],
                           'MEDCOST1': [1, 2, 2, 1], '_LLCPWT': [1., 2., 3., 4.]})
        self.assertAlmostEqual(weighted_rate(df, (df.MEDCOST1 == 1).astype(float)), 0.5)
        bands = [('young', 1, 5), ('older', 6, 9)]
        np.testing.assert_allclose(standardize_age(df, bands)['standard_rates'], [0.3, 0.7])
        np.testing.assert_allclose(standardize_age(df, bands, 'diabetes')['standard_rates'], [0.25, 0.75])

    def test_joint_standardization_checks_overlap(self):
        df = pd.DataFrame({'stratum': ['a', 'a', 'b', 'b'], 'DIABETE4': [1, 3, 1, 3],
                           'MEDCOST1': [1, 2, 2, 1], '_LLCPWT': [1., 2., 3., 4.]})
        np.testing.assert_allclose(standardized(df, ['stratum'])['standardized_rates'], [0.3, 0.7])
        with self.assertRaises(ValueError):
            standardized(df.iloc[:3], ['stratum'])

    def test_ratio_variance_on_simple_strata(self):
        df = pd.DataFrame({'_LLCPWT': [1., 1., 1., 1.], '_STSTR': [1, 1, 2, 2],
                           '_PSU': [1, 2, 3, 4]})
        result = ratio_linearized(df, np.array([1., 0., 0., 0.]), np.ones(4))
        self.assertAlmostEqual(result['estimate'], 0.25)
        self.assertAlmostEqual(result['se'], 0.25)

    def test_standardized_contrast_weight_derivatives(self):
        weight=np.array([1.,2.,3.,4.,5.,6.,7.,8.,2.])
        age=np.array([0,0,0,0,1,1,1,1,0])
        group=np.array([0,0,1,1,0,0,1,1,-1])
        y=np.array([0.,1.,0.,1.,0.,1.,1.,1.,1.])
        delta,scores=contrast_and_scores(weight,age,group,y)
        self.assertAlmostEqual(scores.sum(),0.)
        self.assertEqual(scores[-1],0.)
        for i in range(len(weight)):
            hi=weight.copy();lo=weight.copy();hi[i]*=1.00001;lo[i]*=.99999
            diff=(contrast_and_scores(hi,age,group,y)[0]-contrast_and_scores(lo,age,group,y)[0])/0.00002
            self.assertAlmostEqual(scores[i],diff,places=9)
        self.assertGreaterEqual(design_variance([1]*4+[2]*5,range(9),scores),0)


if __name__ == '__main__':
    unittest.main()
