"""Exploratory full-design variance for complete-case standardizations."""
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
from standardized_contrast_probe import contrast_and_scores, design_variance

NORMAL = 1.959963984540054
SPECS = [('age_only', 'Age'), ('age_income', 'Age + income'),
         ('age_income_insurance', 'Age + income + insurance')]


def main():
    d = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    eligible = (d['_STATE'].between(1, 56) & (d['_LLCPWT'] > 0) & d.DIABETE4.isin([1, 3])
                & d.MEDCOST1.isin([1, 2]) & d['_AGEG5YR'].between(1, 13)
                & d['_INCOMG1'].between(1, 7) & d['_HLTHPL1'].isin([1, 2])).to_numpy()
    weight = d['_LLCPWT'].to_numpy(dtype=float)
    group = np.where(eligible, np.where(d.DIABETE4 == 1, 1, 0), -1)
    outcome = (d.MEDCOST1 == 1).to_numpy(dtype=float)
    age = np.select([d['_AGEG5YR'] <= 5, d['_AGEG5YR'] <= 9], [0, 1], default=2)
    income = np.select([d['_INCOMG1'] <= 2, d['_INCOMG1'] <= 4], [0, 1], default=2)
    insurance = np.where(d['_HLTHPL1'] == 1, 0, 1)
    categories = {'age_only': age, 'age_income': age * 3 + income,
                  'age_income_insurance': age * 6 + income * 2 + insurance}
    saved = json.loads((HERE / 'brfss-access-standardization-results.json').read_text(encoding='utf-8'))
    if int(eligible.sum()) != saved['complete_n']:
        raise ValueError('Complete-case denominator does not match original analysis')
    strata, psus = d['_STSTR'], d['_PSU']
    results, scores = {}, {}
    for key, label in SPECS:
        print(f'Linearizing {label}...', flush=True)
        point, score = contrast_and_scores(weight, categories[key], group, outcome)
        expected = saved['estimates'][key]['standardized_rates']
        if not np.isclose(point, expected[0] - expected[1], rtol=0, atol=1e-10):
            raise ValueError(f'{key}: point estimate does not match source report')
        centered = design_variance(strata, psus, score, singleton='center')
        skipped = design_variance(strata, psus, score, singleton='skip')
        if min(centered, skipped) < 0:
            raise ValueError('Negative variance')
        se = np.sqrt(centered)
        scores[key] = score
        results[key] = {'contrast': point, 'standard_error_centered': float(se),
                        'standard_error_skip': float(np.sqrt(skipped)),
                        'normal_95_low': float(point - NORMAL * se),
                        'normal_95_high': float(point + NORMAL * se),
                        'smallest_group_n': saved['estimates'][key]['smallest_group_n']}

    # Contrasts share a sample, so use covariance of their linearized scores.
    comparisons = {}
    for key in ('age_income', 'age_income_insurance'):
        change_score = scores[key] - scores['age_only']
        change = results[key]['contrast'] - results['age_only']['contrast']
        se = np.sqrt(design_variance(strata, psus, change_score, singleton='center'))
        comparisons[key] = {'difference_from_age_only': change, 'se': float(se),
                            'normal_95_low': float(change - NORMAL * se),
                            'normal_95_high': float(change + NORMAL * se)}

    cells = []
    category = categories['age_income_insurance']
    for cell in range(18):
        for status in (0, 1):
            mask = eligible & (category == cell) & (group == status)
            w = weight[mask]
            cells.append({'age': int(cell // 6), 'income': int((cell % 6) // 2),
                          'insurance': int(cell % 2), 'diabetes': status, 'n': int(mask.sum()),
                          'events': int(outcome[mask].sum()),
                          'weight_only_effective_n': float(w.sum() ** 2 / np.dot(w, w))})
    if len(cells) != 36 or any(c['n'] == 0 for c in cells):
        raise ValueError('Unexpected empty complete-case group/cell')
    min_n = min(c['n'] for c in cells)
    min_events = min(c['events'] for c in cells)
    min_ess = min(c['weight_only_effective_n'] for c in cells)
    if min_n != saved['estimates']['age_income_insurance']['smallest_group_n']:
        raise ValueError('Sparse cell count inconsistent with previous analysis')

    # Check the joint-stratum score for 12 distinct groups plus out-of-domain records.
    candidate_rows = []
    for a in range(3):
        for g in (0, 1):
            for e in (0, 1):
                candidates = np.flatnonzero(eligible & (age == a) & (group == g) & (outcome == e))
                if len(candidates) == 0:
                    raise ValueError('No derivative candidate in an age/group/outcome combination')
                candidate_rows.append(int(candidates[len(candidates) // 2]))
    candidate_rows.extend(np.flatnonzero(~eligible)[:2].tolist())
    derivative_errors = []
    for i in candidate_rows:
        up, down = weight.copy(), weight.copy()
        up[i] *= 1.0001
        down[i] *= .9999
        hi, _ = contrast_and_scores(up, category, group, outcome)
        lo, _ = contrast_and_scores(down, category, group, outcome)
        derivative_errors.append(abs((hi - lo) / .0002 - scores['age_income_insurance'][i]))
    if max(derivative_errors) > 1e-8:
        raise ValueError('Joint-stratum derivatives failed numerical check')

    result = {'complete_n': int(eligible.sum()), 'results': results, 'comparisons': comparisons,
              'joint_cells': cells, 'minimum_group_n': min_n, 'minimum_group_event_n': min_events,
              'minimum_weight_only_effective_n': min_ess, 'derivatives_checked': len(derivative_errors),
              'max_derivative_error': max(derivative_errors),
              'limitation': 'Exploratory linearized uncertainty; complete-case selection and sparse-cell inference not validated.'}
    (HERE / 'access-uncertainty-probe-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    rows = [f"| {label} | {100*results[key]['contrast']:+.2f} | {100*results[key]['standard_error_centered']:.2f} | {100*results[key]['normal_95_low']:+.2f} to {100*results[key]['normal_95_high']:+.2f} |" for key, label in SPECS]
    comp_rows = [f"| {label} minus age only | {100*comparisons[key]['difference_from_age_only']:+.2f} | {100*comparisons[key]['se']:.2f} | {100*comparisons[key]['normal_95_low']:+.2f} to {100*comparisons[key]['normal_95_high']:+.2f} |" for key, label in SPECS[1:]]
    report = f'''# Complete-case standardization: exploratory uncertainty and sparse cells

Run date: {date.today().isoformat()}. This is a methods diagnostic, not clinical or causal evidence. The [original comparison](brfss-access-standardization.md) describes the 48-state-plus-DC domain, source, definitions, and complete-case exclusions.

## Full-design calculation

The common complete-case sample contains {eligible.sum():,} respondents. For each specification, the standard population is its corresponding pooled, weighted age or joint-factor distribution in those respondents. The program computes the full influence score for the standardized diabetes-minus-no-diabetes rate, including estimation of the standard-population weights, and aggregates it using full-sample strata and PSUs; records outside the domain contribute zero. Full-sample singleton strata use centering. These are normal-approximation intervals under a with-replacement linearization, presented for research diagnostics only.

| Standardization | Contrast, percentage points | SE, percentage points | Approximate 95% interval, percentage points |
|---|---:|---:|---:|
{chr(10).join(rows)}

The estimates match the earlier point estimates. A [nonlinear survey-package cross-check](access-svy-nonlinear-validation.md) independently reproduces the three complete-case calculations and paired differences under the same data and design assumptions. That checks their computation, not whether the sparse-cell intervals achieve their stated coverage. Center-versus-skip singleton results are retained in the JSON. Point estimates and intervals can be affected by missingness, nonresponse, self-report, residual confounding, and design assumptions.

## How specifications differ

The same sample contributes to every row. The following differences in contrasts therefore use the covariance between their influence scores; they are not calculated as if the rows were independent. Each standardization targets a different weighted population, so these are descriptive changes in a statistical estimand, not effects of changing income or insurance.

| Comparison | Change, percentage points | SE, percentage points | Approximate 95% interval, percentage points |
|---|---:|---:|---:|
{chr(10).join(comp_rows)}

## Sparse cells and verification

The 18 age-income-insurance strata create 36 group/cell combinations. The smallest has {min_n} respondents; the smallest event count is {min_events}, and the smallest weight-only effective sample size is {min_ess:.1f}. These minima may occur in different cells. Weight-only effective size is `(sum of weights)^2 / sum of squared weights`; it is a descriptive weight-concentration diagnostic, not a survey-design degrees of freedom or a guarantee of precision. Small groups and few events can make normal approximations unstable. Cell-by-cell diagnostics are in the JSON.

The program checked {len(derivative_errors)} selected weight derivatives, with maximum absolute error {max(derivative_errors):.2g}; this is an implementation check, not an external validation or coverage study. In this analysis {saved['excluded_n']:,} otherwise eligible respondents had unknown age, income, or insurance and were excluded. Results apply to complete cases and should not be generalized to those with missing values without further investigation.

## Reproduce

Run `python brfss_access_standardization.py`, then `python access_uncertainty_probe.py`, with NumPy and pandas installed. Results and cell diagnostics are saved in `access-uncertainty-probe-results.json`.
'''
    (HERE / 'access-uncertainty-probe.md').write_text(report, encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('complete_n', 'results', 'comparisons', 'minimum_group_n', 'minimum_group_event_n', 'minimum_weight_only_effective_n', 'max_derivative_error')}, indent=2))


if __name__ == '__main__':
    main()
