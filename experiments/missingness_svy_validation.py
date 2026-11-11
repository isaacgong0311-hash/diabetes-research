"""Independent nonlinear survey-package check of the missingness comparison."""
import gc
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


def main():
    d = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    domain = (d['_STATE'].between(1, 56) & (d['_LLCPWT'] > 0) & d.DIABETE4.isin([1, 3])
              & d.MEDCOST1.isin([1, 2]) & d['_AGEG5YR'].between(1, 13)).to_numpy()
    complete = (d['_INCOMG1'].between(1, 7) & d['_HLTHPL1'].isin([1, 2])).to_numpy()
    group = (~complete).astype(int) * 2 + (d.DIABETE4 == 1).to_numpy().astype(int)
    age = np.select([d['_AGEG5YR'] <= 5, d['_AGEG5YR'] <= 9], [0, 1], default=2)
    event = (d.MEDCOST1 == 1).to_numpy().astype(int)
    cell = np.full(len(d), 'outside', dtype='<U8')
    for a in range(3):
        for g in range(4):
            for e in (0, 1):
                cell[domain & (age == a) & (group == g) & (event == e)] = f'a{a}g{g}e{e}'
    if len(d[['_STSTR', '_PSU']].drop_duplicates()) != len(d):
        raise ValueError('Expected one record per stratum/PSU pair')
    frame = pl.DataFrame({'stratum': d['_STSTR'].to_numpy(), 'weight': d['_LLCPWT'].to_numpy(),
                          'domain': domain.astype(int), 'cell': cell})
    design = svy.Design(stratum='stratum', wgt='weight', singleton=svy.Singleton('center', domains='standard'))
    sample = svy.Sample(frame, design)
    del d, frame, domain, complete, group, age, event, cell
    gc.collect()
    print('Estimating 24 cell proportions and covariance...', flush=True)
    estimates = sample.estimation.prop('cell', where=(svy.col('domain') == 1))
    expected = {f'a{a}g{g}e{e}' for a in range(3) for g in range(4) for e in (0, 1)}
    keys = set(estimates.keys())
    if not expected.issubset(keys) or keys - expected not in (set(), {'outside'}):
        raise ValueError(f'Unexpected cell keys: {keys}')
    labels = {'complete': [-1, 1, 0, 0], 'incomplete': [0, 0, -1, 1],
              'complete_minus_incomplete': [-1, 1, 1, -1]}
    expressions = {}
    for name, coefficients in labels.items():
        terms = []
        for a in range(3):
            z = {(g, e): svy.estd(f'a{a}g{g}e{e}') for g in range(4) for e in (0, 1)}
            age_share = sum(z.values())
            rates = [z[g, 1] / (z[g, 0] + z[g, 1]) for g in range(4)]
            age_contrast = sum(coefficient * rate for coefficient, rate in zip(coefficients, rates) if coefficient)
            terms.append(age_share * age_contrast)
        expressions[name] = sum(terms)
    # Nonlinear contrasts derive directly from the package covariance, not the prototype scores.
    saved = json.loads((HERE / 'missingness-standardized-probe-results.json').read_text(encoding='utf-8'))
    results = {}
    for name, expression in expressions.items():
        row = estimates.contrast(expression).to_polars().to_dicts()[0]
        reference = saved['estimates'][name]
        if not np.isclose(row['est'], reference['contrast'], atol=1e-10, rtol=0):
            raise ValueError(f'{name}: point estimate mismatch')
        if not np.isclose(row['se'], reference['se'], atol=1e-10, rtol=0):
            raise ValueError(f'{name}: SE mismatch')
        results[name] = {'svy_estimate': row['est'], 'svy_se': row['se'],
                         'prototype_estimate': reference['contrast'], 'prototype_se': reference['se'],
                         'se_difference': row['se'] - reference['se']}
    (HERE / 'missingness-svy-validation-results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    rows = [f"| {name} | {100*r['svy_estimate']:+.4f} | {100*r['prototype_se']:.6f} | {100*r['svy_se']:.6f} |" for name, r in results.items()]
    report = f'''# Nonlinear survey-package check of the missingness comparison

Run date: {date.today().isoformat()}. This is a numerical cross-check under specified assumptions, not validation of the missing-data mechanism or survey coverage.

The [shared-age comparison](missingness-standardized-probe.md) derives record-level influence scores. This check uses `svy` {svy.__version__} to estimate 24 weighted age-by-completeness-by-diabetes-by-outcome cell proportions and their joint covariance. It constructs each gap and their difference directly as nonlinear expressions of those proportions, independently of the prototype's influence scores. The full survey design is retained, with one record per stratum/PSU pair and centered full-sample singleton strata.

| Comparison | Estimate, percentage points | Prototype SE, percentage points | svy SE, percentage points |
|---|---:|---:|---:|
{chr(10).join(rows)}

Both computations agree to better than 1e-10 on the proportion scale. This supports the numerical calculation under the same input data and design choices. It does not prove that missingness is ignorable, that income or insurance has no effect, or that the normal intervals have nominal coverage. It does not replace a separately developed replication or address confounding and nonresponse.

Run `python missingness_standardized_probe.py` followed by `python missingness_svy_validation.py` with NumPy, pandas, Polars and svy installed. Machine-readable results are in `missingness-svy-validation-results.json`.
'''
    (HERE / 'missingness-svy-validation.md').write_text(report, encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
