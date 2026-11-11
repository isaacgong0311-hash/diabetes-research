"""Compare complete/incomplete covariate groups using a shared age reference."""
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

from standardized_contrast_probe import design_variance


def four_group_contrast(weight, age, group, outcome, coefficients):
    """Linearized age-standardized weighted sum of four group outcome means.

    group -1 is outside the domain; the reference age distribution comes from
    the pooled domain sample. Coefficients are indexed by group 0..3.
    """
    domain = group >= 0
    total = weight[domain].sum()
    means = np.empty((3, 4))
    totals = np.empty((3, 4))
    age_weight = np.empty(3)
    for a in range(3):
        age_mask = domain & (age == a)
        age_weight[a] = weight[age_mask].sum()
        for g in range(4):
            mask = age_mask & (group == g)
            totals[a, g] = weight[mask].sum()
            if totals[a, g] <= 0:
                raise ValueError('An age/completeness/diabetes group is empty')
            means[a, g] = np.dot(weight[mask], outcome[mask]) / totals[a, g]
    if total <= 0 or not np.isclose(age_weight.sum(), total):
        raise ValueError('Invalid reference domain')
    age_values = means @ np.asarray(coefficients)
    value = float(age_weight @ age_values / total)
    score = np.zeros(len(weight))
    for a in range(3):
        mask = domain & (age == a)
        score[mask] += weight[mask] / total * (age_values[a] - value)
        for g in range(4):
            selected = mask & (group == g)
            score[selected] += (age_weight[a] / total * coefficients[g] * weight[selected]
                                * (outcome[selected] - means[a, g]) / totals[a, g])
    return value, score, age_weight / total


def main():
    d = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    domain = (d['_STATE'].between(1, 56) & (d['_LLCPWT'] > 0) & d.DIABETE4.isin([1, 3])
              & d.MEDCOST1.isin([1, 2]) & d['_AGEG5YR'].between(1, 13)).to_numpy()
    complete = (d['_INCOMG1'].between(1, 7) & d['_HLTHPL1'].isin([1, 2])).to_numpy()
    # g0 complete/no diabetes, g1 complete/diabetes,
    # g2 incomplete/no diabetes, g3 incomplete/diabetes.
    group = np.where(domain, (~complete).astype(int) * 2 + (d.DIABETE4 == 1).to_numpy().astype(int), -1)
    age = np.select([d['_AGEG5YR'] <= 5, d['_AGEG5YR'] <= 9], [0, 1], default=2)
    weight = d['_LLCPWT'].to_numpy(dtype=float)
    outcome = (d.MEDCOST1 == 1).to_numpy(dtype=float)
    specs = {'complete': [-1, 1, 0, 0], 'incomplete': [0, 0, -1, 1],
             'complete_minus_incomplete': [-1, 1, 1, -1]}
    result = {'known_age_domain_n': int(domain.sum()), 'complete_n': int((domain & complete).sum()),
              'incomplete_n': int((domain & ~complete).sum()), 'estimates': {}}
    scores = {}
    for name, coefficients in specs.items():
        point, score, reference = four_group_contrast(weight, age, group, outcome, coefficients)
        se = design_variance(d['_STSTR'], d['_PSU'], score, singleton='center') ** .5
        result['estimates'][name] = {'contrast': point, 'se': se,
                                     'normal_95_low': point - 1.95996398454 * se,
                                     'normal_95_high': point + 1.95996398454 * se}
        scores[name] = score
    if not np.isclose(result['estimates']['complete']['contrast'] - result['estimates']['incomplete']['contrast'],
                      result['estimates']['complete_minus_incomplete']['contrast'], atol=1e-12):
        raise ValueError('Difference-in-contrasts failed')
    if not np.allclose(scores['complete'] - scores['incomplete'], scores['complete_minus_incomplete'], atol=1e-14):
        raise ValueError('Difference-in-contrast scores failed')
    errors = []
    for a in range(3):
        for g in range(4):
            for e in (0, 1):
                candidates = np.flatnonzero(domain & (age == a) & (group == g) & (outcome == e))
                if not len(candidates):
                    raise ValueError('Derivative check group is empty')
                i = candidates[len(candidates) // 2]
                up, down = weight.copy(), weight.copy()
                up[i] *= 1.0001
                down[i] *= .9999
                hi = four_group_contrast(up, age, group, outcome, specs['complete_minus_incomplete'])[0]
                lo = four_group_contrast(down, age, group, outcome, specs['complete_minus_incomplete'])[0]
                errors.append(abs((hi - lo) / .0002 - scores['complete_minus_incomplete'][i]))
    if max(errors) > 1e-8:
        raise ValueError('Selected numerical derivatives disagree')
    result['reference_age_weights'] = reference.tolist()
    result['derivatives_checked'] = len(errors)
    result['max_derivative_error'] = max(errors)
    (HERE / 'missingness-standardized-probe-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    labels = [('complete', 'Complete income and insurance'), ('incomplete', 'Missing income and/or insurance'),
              ('complete_minus_incomplete', 'Complete gap minus incomplete gap')]
    rows = [f"| {label} | {100*result['estimates'][key]['contrast']:+.2f} | {100*result['estimates'][key]['se']:.2f} | {100*result['estimates'][key]['normal_95_low']:+.2f} to {100*result['estimates'][key]['normal_95_high']:+.2f} |" for key, label in labels]
    report = f'''# Missingness sensitivity with a shared age distribution

Run date: {date.today().isoformat()}. This is an exploratory observational comparison, not a missing-data correction or causal analysis.

Among {domain.sum():,} 2023 respondents with known age and definite diabetes and cost responses in 48 states plus DC, {result['complete_n']:,} had known income and insurance and {result['incomplete_n']:,} lacked at least one. Respondents with unknown age are excluded from this particular comparison. The [missingness audit](access-missingness-audit.md) includes them in its overall counts.

For each completeness group, the gap is the cost-barrier rate for respondents reporting diabetes minus that for respondents reporting no diabetes. Both gaps are standardized to the **same pooled age distribution of all known-age respondents**, including complete and incomplete cases. Thus these complete-case figures differ from [earlier estimates](brfss-access-standardization.md) that use the complete-case age distribution as their reference. The contrast between gaps reflects differences in observed outcomes, not the effect of missingness and not the outcome that would have occurred had missing covariates been observed.

| Comparison | Gap or difference, percentage points | SE, points | Approximate 95% interval, points |
|---|---:|---:|---:|
{chr(10).join(rows)}

The prototype uses the full strata and PSUs, accounts for uncertainty in the shared estimated age reference and covariance between the two gaps, and centers full-sample singleton strata. A [survey-package cross-check](missingness-svy-validation.md) reproduces the whole nonlinear calculation under the same design choices; coverage of the normal-approximation intervals is not established. The common reference shares are {100*reference[0]:.1f}%, {100*reference[1]:.1f}%, and {100*reference[2]:.1f}% for ages 18–44, 45–64, and 65+. Numerical checks of {len(errors)} selected derivatives had maximum error {max(errors):.2g} on the proportion scale.

Differences may reflect other respondent characteristics, nonresponse, self-report, selection, sampling error, or residual age differences within bands. This does not identify the missing income or insurance values, establish whether data are missing at random, or extend the complete-case income-and-insurance-standardized results to all respondents. Diabetes type is not identified and the missing Kentucky and Pennsylvania data prevent all-state coverage.

## Reproduce

Run `python missingness_standardized_probe.py` after the 2023 extract is prepared; NumPy and pandas are required. Numerical results are in `missingness-standardized-probe-results.json`.
'''
    (HERE / 'missingness-standardized-probe.md').write_text(report, encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
