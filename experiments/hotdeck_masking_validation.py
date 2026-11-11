"""Holdout masking experiment for the exploratory weighted donor procedure."""
import json
import os
import sys
from datetime import date
from pathlib import Path

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / '.surveydeps'))
import numpy as np
import pandas as pd

from hotdeck_sensitivity import build_pools, impute_once
from missing_covariate_scenarios import scenario_estimate

SEED = 67032
DRAWS = 50
HOLDOUT_FRACTION = .20


def weighted_accuracy(actual, predicted, weights):
    return float(np.dot(weights, actual == predicted) / weights.sum())


def majority_prediction(income, insurance, weight, pools, mode):
    """Most heavily weighted donor category in each independently fitted pool."""
    predicted = np.full(len(income), -1, dtype=int)
    for p in pools:
        donor = p['donors']
        if mode == 'income':
            labels = income[donor]
        elif mode == 'insurance':
            labels = insurance[donor]
        else:
            labels = income[donor] * 2 + insurance[donor]
        prediction = int(np.argmax(np.bincount(labels, weights=weight[donor])))
        predicted[p['recipients']] = prediction
    return predicted


def main():
    rng = np.random.default_rng(SEED)
    d = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    domain = (d['_STATE'].between(1, 56) & (d['_LLCPWT'] > 0) & d.DIABETE4.isin([1, 3])
              & d.MEDCOST1.isin([1, 2]) & d['_AGEG5YR'].between(1, 13)
              & d['_INCOMG1'].between(1, 7) & d['_HLTHPL1'].isin([1, 2])).to_numpy()
    d = d.loc[domain]
    age = np.select([d['_AGEG5YR'] <= 5, d['_AGEG5YR'] <= 9], [0, 1], default=2)
    income = np.select([d['_INCOMG1'] <= 2, d['_INCOMG1'] <= 4], [0, 1], default=2)
    insurance = np.where(d['_HLTHPL1'] == 1, 0, 1)
    group = (d.DIABETE4 == 1).to_numpy().astype(int)
    outcome = (d.MEDCOST1 == 1).to_numpy().astype(int)
    weight = d['_LLCPWT'].to_numpy(dtype=float)
    known = json.loads((HERE / 'brfss-access-standardization-results.json').read_text(encoding='utf-8'))
    if len(d) != known['complete_n']:
        raise ValueError('Complete-case domain does not match previous analysis')
    holdout = rng.random(len(d)) < HOLDOUT_FRACTION
    ref = np.bincount(age * 6 + income * 2 + insurance, weights=weight, minlength=18)
    ref /= ref.sum()
    truth_rates, _ = scenario_estimate(weight, age, income, insurance, group, outcome, 0, 0, ref)
    truth = truth_rates[1] - truth_rates[0]
    reference_rates = known['estimates']['age_income_insurance']['standardized_rates']
    if not np.isclose(truth, reference_rates[0] - reference_rates[1], atol=1e-10, rtol=0):
        raise ValueError('Complete-case contrast does not match prior result')
    results = {}
    for mode in ('income', 'insurance', 'both'):
        masked_income, masked_insurance = income.copy(), insurance.copy()
        if mode in ('income', 'both'):
            masked_income[holdout] = -1
        if mode in ('insurance', 'both'):
            masked_insurance[holdout] = -1
        pools = build_pools(age, group, outcome, masked_income, masked_insurance, weight)
        if sum(len(p['recipients']) for p in pools) != holdout.sum():
            raise ValueError('Holdout cases did not map one-to-one to donor pools')
        actual = income if mode == 'income' else insurance if mode == 'insurance' else income * 2 + insurance
        majority = majority_prediction(income, insurance, weight, pools, mode)
        if np.any(majority[holdout] < 0):
            raise ValueError('No majority prediction for a holdout case')
        majority_accuracy = weighted_accuracy(actual[holdout], majority[holdout], weight[holdout])
        accuracy, contrasts = [], []
        for _ in range(DRAWS):
            imputed_income, imputed_insurance = impute_once(masked_income, masked_insurance, pools, rng)
            predicted = (imputed_income if mode == 'income' else imputed_insurance if mode == 'insurance'
                         else imputed_income * 2 + imputed_insurance)
            accuracy.append(weighted_accuracy(actual[holdout], predicted[holdout], weight[holdout]))
            rates, _ = scenario_estimate(weight, age, imputed_income, imputed_insurance, group, outcome, 0, 0, ref)
            contrasts.append(rates[1] - rates[0])
        accuracy, contrasts = np.asarray(accuracy), np.asarray(contrasts)
        results[mode] = {'holdout_n': int(holdout.sum()), 'donor_n': int((~holdout).sum()),
                         'pool_count': len(pools), 'minimum_donor_n': min(len(p['donors']) for p in pools),
                         'weighted_accuracy_mean': float(accuracy.mean()),
                         'weighted_majority_accuracy': majority_accuracy,
                         'contrast_truth': float(truth), 'contrast_mean': float(contrasts.mean()),
                         'contrast_bias_from_masking': float(contrasts.mean() - truth),
                         'contrast_sd_between_draws': float(contrasts.std(ddof=1))}
        print(f"{mode}: donor accuracy {100*accuracy.mean():.1f}%, held-out majority {100*majority_accuracy:.1f}%", flush=True)
    result = {'seed': SEED, 'draws_per_pattern': DRAWS, 'holdout_fraction': HOLDOUT_FRACTION,
              'complete_n': len(d), 'results': results,
              'limitation': 'Random masking among observed respondents cannot validate truly missing responses.'}
    (HERE / 'hotdeck-masking-validation-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    labels = {'income': 'Income only', 'insurance': 'Insurance only', 'both': 'Income and insurance together'}
    rows = [f"| {labels[name]} | {100*r['weighted_accuracy_mean']:.1f}% | {100*r['weighted_majority_accuracy']:.1f}% | {100*r['contrast_bias_from_masking']:+.3f} | {100*r['contrast_sd_between_draws']:.3f} |" for name, r in results.items()]
    report = f'''# Donor-method masking check on observed respondents

Run date: {date.today().isoformat()}. This is an artificial holdout check, not validation of a missing-data model for respondents who did not answer.

## Design

Starting with {len(d):,} respondents whose age, income, insurance, diabetes response, and cost response are known, we randomly selected {int(holdout.sum()):,} ({HOLDOUT_FRACTION:.0%} target) as holdouts, seed {SEED}. Holdouts are excluded as donors. In turn, we hide income only, insurance only, or both fields on the same holdouts. For each pattern, we generate {DRAWS} weighted donor draws using the [same matching rules](hotdeck-sensitivity.md), and compare imputed categories to their known values. For the two-field pattern, accuracy requires both answers to match. Percentages are survey-weighted descriptive accuracy on held-out observed respondents; they are not design-based uncertainty estimates.

As a simple predictive benchmark, the majority column always selects the donor pool's highest-weight category. A donor draw is intended to represent variation rather than optimize individual accuracy, so the two serve different purposes. We also recompute the overall age-income-insurance-standardized group gap after masking and drawing; the reference distribution is held fixed at the original complete-case distribution. The fully observed reference gap is {100*truth:+.3f} percentage points. Its use here is for evaluation against known answers and would not be available for truly missing covariates.

| Hidden fields | Mean donor-draw accuracy | Weighted majority accuracy | Mean reconstructed gap minus known gap, points | SD across draws, points |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

The smallest donor pool in this exercise had {min(r['minimum_donor_n'] for r in results.values())} members. The contrast errors and accuracy scores are affected by the particular random holdout split and donor draws. Small mean contrast error can coexist with many wrong individual assignments; neither result implies that donor draws recover the true missing answers.

The holdouts were randomly masked among **observed complete cases**, unlike the original unknown responses. If real nonresponse depends on income, insurance, or unmeasured characteristics, this check can substantially overstate real-world validity. It does not estimate complex-survey sampling uncertainty, correct nonresponse, prove a missing-at-random assumption, or establish causality. Outcome and diabetes status were included in donor matching and remain observed in the targeted domain.

## Reproduce

Run `python hotdeck_masking_validation.py` after generating `brfss-access-standardization-results.json`; NumPy and pandas are required. Results are saved in `hotdeck-masking-validation-results.json`. No record-level imputations are exported.
'''
    (HERE / 'hotdeck-masking-validation.md').write_text(report, encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
