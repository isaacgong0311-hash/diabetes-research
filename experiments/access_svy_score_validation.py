"""Check aggregation of complete-case contrast scores using supported svy."""
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
import polars as pl
import svy

from standardized_contrast_probe import contrast_and_scores


def main():
    data = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    domain = (data['_STATE'].between(1, 56) & (data['_LLCPWT'] > 0)
              & data.DIABETE4.isin([1, 3]) & data.MEDCOST1.isin([1, 2])
              & data['_AGEG5YR'].between(1, 13) & data['_INCOMG1'].between(1, 7)
              & data['_HLTHPL1'].isin([1, 2])).to_numpy()
    if len(data[['_STSTR', '_PSU']].drop_duplicates()) != len(data):
        raise ValueError('Expected one PSU per record within each stratum')
    weight = data['_LLCPWT'].to_numpy(dtype=float)
    if np.any(~np.isfinite(weight)) or np.any(weight <= 0):
        raise ValueError('Expected finite, positive survey weights throughout the full design')
    group = np.where(domain, np.where(data.DIABETE4 == 1, 1, 0), -1)
    outcome = (data.MEDCOST1 == 1).to_numpy(dtype=float)
    age = np.select([data['_AGEG5YR'] <= 5, data['_AGEG5YR'] <= 9], [0, 1], default=2)
    income = np.select([data['_INCOMG1'] <= 2, data['_INCOMG1'] <= 4], [0, 1], default=2)
    insurance = np.where(data['_HLTHPL1'] == 1, 0, 1)
    categories = {'age_only': age, 'age_income': age * 3 + income,
                  'age_income_insurance': age * 6 + income * 2 + insurance}
    score = {name: contrast_and_scores(weight, category, group, outcome)[1]
             for name, category in categories.items()}
    score['income_minus_age'] = score['age_income'] - score['age_only']
    score['full_minus_age'] = score['age_income_insurance'] - score['age_only']
    saved = json.loads((HERE / 'access-uncertainty-probe-results.json').read_text(encoding='utf-8'))
    expected = {name: saved['results'][name]['standard_error_centered'] for name in categories}
    expected['income_minus_age'] = saved['comparisons']['age_income']['se']
    expected['full_minus_age'] = saved['comparisons']['age_income_insurance']['se']
    frame = {'stratum': data['_STSTR'].to_numpy(), 'weight': weight}
    frame.update({name: values / weight for name, values in score.items()})
    design = svy.Design(stratum='stratum', wgt='weight', singleton=svy.Singleton('center', domains='standard'))
    sample = svy.Sample(pl.DataFrame(frame), design)
    results = {}
    for name in score:
        print(f'Checking score aggregation for {name}...', flush=True)
        estimate = sample.estimation.total(name).to_polars().to_dicts()[0]
        if not np.isclose(estimate['se'], expected[name], atol=1e-10, rtol=0):
            raise ValueError(f'{name}: svy score SE differs from prototype')
        if abs(estimate['est']) > 1e-9:
            raise ValueError(f'{name}: influence-score total is not near zero')
        results[name] = {'prototype_se': expected[name], 'svy_se': estimate['se'],
                         'difference': estimate['se'] - expected[name], 'score_total': estimate['est']}
    (HERE / 'access-svy-score-validation-results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    rows = [f"| {name} | {100*r['prototype_se']:.6f} | {100*r['svy_se']:.6f} |" for name, r in results.items()]
    report = f'''# Supported-package check of complete-case score aggregation

Run date: {date.today().isoformat()}. This is a computational check, not validation of the underlying comparison or its interval coverage.

The [complete-case uncertainty probe](access-uncertainty-probe.md) computes influence scores for three standardizations and two paired differences. This script passes those **already computed scores** to `svy` {svy.__version__} as weighted totals and asks the package to compute their standard errors, keeping the full survey design and centering full-sample singleton strata. Every 2023 record has a unique stratum/PSU pair, so the package uses each record as a PSU. The two paths agree within 1e-10 on the proportion scale.

| Score | Prototype SE, percentage points | svy SE, percentage points |
|---|---:|---:|
{chr(10).join(rows)}

This tests aggregation of the supplied scores and covariance for the paired differences. It does **not** independently derive the nonlinear joint-stratum contrast, verify the score formula, validate normal-interval coverage with sparse cells, or resolve missingness and confounding. The corresponding age-only calculation in the broader 2023 domain was separately checked as a [nonlinear svy contrast](svy-contrast-validation.md).

Run `python access_uncertainty_probe.py` followed by `python access_svy_score_validation.py`. Install NumPy, pandas, Polars, and svy; details are in `access-svy-score-validation-results.json`.
'''
    (HERE / 'access-svy-score-validation.md').write_text(report, encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
