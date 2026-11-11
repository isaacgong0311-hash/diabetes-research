"""Deterministic stress scenarios for missing income and insurance categories.

These are not statistical imputations, causal estimates, or rigorous bounds.
"""
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / '.surveydeps'))
import numpy as np
import pandas as pd


def scenario_estimate(weight, age, income, insurance, group, outcome, setting_no, setting_yes, reference=None):
    """Return standardized group rates after fixed group-specific assignments.

    An assignment 0..5 maps to income (0..2) and insurance (0..1).
    Only negative (missing) covariate codes are replaced.
    """
    chosen = np.where(group == 1, setting_yes, setting_no)
    filled_income = np.where(income >= 0, income, chosen // 2)
    filled_insurance = np.where(insurance >= 0, insurance, chosen % 2)
    cell = age * 6 + filled_income * 2 + filled_insurance
    index = cell * 2 + group
    totals = np.bincount(index, weights=weight, minlength=36).reshape(18, 2)
    events = np.bincount(index, weights=weight * outcome, minlength=36).reshape(18, 2)
    if np.any(totals <= 0):
        raise ValueError('At least one stratum lacks a diabetes-response group')
    standard = totals.sum(axis=1) if reference is None else np.asarray(reference, dtype=float)
    if standard.shape != (18,) or np.any(standard < 0) or standard.sum() <= 0:
        raise ValueError('Invalid standard population')
    rates = (standard[:, None] * events / totals).sum(axis=0) / standard.sum()
    return rates, int(np.min(np.bincount(index, minlength=36)))


def main():
    d = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    domain = (d['_STATE'].between(1, 56) & (d['_LLCPWT'] > 0) & d.DIABETE4.isin([1, 3])
              & d.MEDCOST1.isin([1, 2]) & d['_AGEG5YR'].between(1, 13)).to_numpy()
    d = d.loc[domain]
    age = np.select([d['_AGEG5YR'] <= 5, d['_AGEG5YR'] <= 9], [0, 1], default=2)
    income = np.where(d['_INCOMG1'].between(1, 7),
                      np.select([d['_INCOMG1'] <= 2, d['_INCOMG1'] <= 4], [0, 1], default=2), -1)
    insurance = np.where(d['_HLTHPL1'].isin([1, 2]), np.where(d['_HLTHPL1'] == 1, 0, 1), -1)
    group = (d.DIABETE4 == 1).to_numpy().astype(int)
    outcome = (d.MEDCOST1 == 1).to_numpy(dtype=float)
    weight = d['_LLCPWT'].to_numpy(dtype=float)
    missing_n = int(((income < 0) | (insurance < 0)).sum())
    saved = json.loads((HERE / 'missingness-standardized-probe-results.json').read_text(encoding='utf-8'))
    if len(d) != saved['known_age_domain_n'] or missing_n != saved['incomplete_n']:
        raise ValueError('Known-age denominator does not match previous audit')
    complete = (income >= 0) & (insurance >= 0)
    complete_cell = age[complete] * 6 + income[complete] * 2 + insurance[complete]
    fixed_reference = np.bincount(complete_cell, weights=weight[complete], minlength=18)
    if np.any(fixed_reference <= 0):
        raise ValueError('The complete-case standard has an empty cell')
    fixed_reference /= fixed_reference.sum()
    labels = ['<25k insured', '<25k uninsured', '25–<50k insured', '25–<50k uninsured',
              '50k+ insured', '50k+ uninsured']
    scenarios = []
    matrix, fixed_matrix = np.empty((6, 6)), np.empty((6, 6))
    for no in range(6):
        for yes in range(6):
            rates, min_n = scenario_estimate(weight, age, income, insurance, group, outcome, no, yes)
            fixed_rates, _ = scenario_estimate(weight, age, income, insurance, group, outcome, no, yes, fixed_reference)
            difference = float(rates[1] - rates[0])
            matrix[no, yes] = difference
            fixed_matrix[no, yes] = fixed_rates[1] - fixed_rates[0]
            scenarios.append({'no_diabetes_setting': no, 'diabetes_setting': yes,
                              'no_diabetes_rate': float(rates[0]), 'diabetes_rate': float(rates[1]),
                              'difference': difference, 'fixed_reference_difference': float(fixed_rates[1] - fixed_rates[0]),
                              'smallest_group_cell_n': min_n})
    lo, hi = min(scenarios, key=lambda x: x['difference']), max(scenarios, key=lambda x: x['difference'])
    fixed_lo = min(scenarios, key=lambda x: x['fixed_reference_difference'])
    fixed_hi = max(scenarios, key=lambda x: x['fixed_reference_difference'])
    result = {'known_age_n': len(d), 'missing_income_or_insurance_n': missing_n,
              'settings': labels, 'scenarios': scenarios, 'minimum': lo, 'maximum': hi,
              'fixed_reference_minimum': fixed_lo, 'fixed_reference_maximum': fixed_hi,
              'fixed_reference_weights': fixed_reference.tolist(),
              'limitations': 'Fixed, homogeneous within-group assignments; not a missing-data model or exhaustive bounds.'}
    (HERE / 'missing-covariate-scenarios-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    table = ['| No-diabetes assignment ↓ / Diabetes assignment → | ' + ' | '.join(labels) + ' |',
             '|---|' + '---:|' * 6]
    for i, label in enumerate(labels):
        table.append('| ' + label + ' | ' + ' | '.join(f'{100*x:+.2f}' for x in matrix[i]) + ' |')
    fixed_table = ['| No-diabetes assignment ↓ / Diabetes assignment → | ' + ' | '.join(labels) + ' |',
                   '|---|' + '---:|' * 6]
    for i, label in enumerate(labels):
        fixed_table.append('| ' + label + ' | ' + ' | '.join(f'{100*x:+.2f}' for x in fixed_matrix[i]) + ' |')
    report = f'''# Fixed-assignment stress test for missing covariates

Run date: {date.today().isoformat()}. This is a set of deliberately strong hypothetical assignments, not a missing-data model, causal analysis, or set of mathematical bounds.

## Setup

Of {len(d):,} respondents with definite diabetes and cost responses and known age in 48 states plus DC, {missing_n:,} lack income and/or insurance. We retain observed values and fill only the missing fields. Within each diabetes-response group, a scenario assigns **every** missing income to one chosen income band and **every** missing insurance response to one chosen coverage category. Existing observed values are never replaced. The row chooses the assignment for respondents reporting no diabetes; the column chooses it for respondents reporting diabetes. Each cell recomputes both group rates standardized to that scenario's pooled age-income-insurance distribution.

Income bands are below $25,000, $25,000–<$50,000, and $50,000 or above; insured means any reported coverage. Each table entry is the diabetes-minus-no-diabetes difference in percentage points.

{chr(10).join(table)}

Across these 36 specific, deterministic scenarios, the difference ranges from {100*lo['difference']:+.2f} to {100*hi['difference']:+.2f} percentage points. This is **not** the range of all possible missing-value patterns: people within each response group can have different missing values, and assignments could depend on outcomes or other characteristics. It is also not an interval for sampling uncertainty. The standard population changes with each scenario, so the scenarios pose different descriptive questions. The smallest unweighted group/cell across the scenarios is {min(x['smallest_group_cell_n'] for x in scenarios)}.

## Holding the reference population fixed

To separate changes in the estimated group rates from changes in the standard population, this table repeats the same assignments but always standardizes to the pooled age-income-insurance distribution of the original complete cases. Across these 36 settings, the fixed-reference difference ranges from {100*fixed_lo['fixed_reference_difference']:+.2f} to {100*fixed_hi['fixed_reference_difference']:+.2f} percentage points. This comparison still depends on the artificial assignments and is not a bound or uncertainty interval.

{chr(10).join(fixed_table)}

The values provide a stress test of assumptions, not evidence that any assignment is plausible. They do not account for the uncertainty of missing values, residual confounding, nonresponse, omitted states, or changing the missing-age population. They cannot establish why the diabetes and no-diabetes groups differ. The separately [cross-checked complete-case analysis](access-svy-nonlinear-validation.md) uses a narrower population; its results are not directly comparable as causal estimates.

The figures display both the [varying-reference matrix](figure_missing_covariate_scenarios.png) and the [fixed-reference matrix](figure_missing_covariate_fixed.png); SVG versions are also available.

## Reproduce

Run `python missingness_standardized_probe.py` and then `python missing_covariate_scenarios.py`, with pandas and NumPy. Run `python plot_missing_covariate_scenarios.py` with matplotlib installed to regenerate the figure. All 36 rates, assignments, and cell-size diagnostics are in `missing-covariate-scenarios-results.json`.
'''
    (HERE / 'missing-covariate-scenarios.md').write_text(report, encoding='utf-8')
    print(f"36 scenarios, varying standard: {100*lo['difference']:+.2f} to {100*hi['difference']:+.2f} percentage points")
    print(f"36 scenarios, fixed standard: {100*fixed_lo['fixed_reference_difference']:+.2f} to {100*fixed_hi['fixed_reference_difference']:+.2f} percentage points")


if __name__ == '__main__':
    main()
