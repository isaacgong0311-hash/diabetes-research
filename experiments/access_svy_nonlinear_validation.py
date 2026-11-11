"""Full nonlinear svy cross-check of joint complete-case standardizations."""
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


def cell_key(a, income, insurance, group, event):
    return f'c{a}{income}{insurance}g{group}e{event}'


def main():
    d = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    domain = (d['_STATE'].between(1, 56) & (d['_LLCPWT'] > 0) & d.DIABETE4.isin([1, 3])
              & d.MEDCOST1.isin([1, 2]) & d['_AGEG5YR'].between(1, 13)
              & d['_INCOMG1'].between(1, 7) & d['_HLTHPL1'].isin([1, 2])).to_numpy()
    age = np.select([d['_AGEG5YR'] <= 5, d['_AGEG5YR'] <= 9], [0, 1], default=2)
    income = np.select([d['_INCOMG1'] <= 2, d['_INCOMG1'] <= 4], [0, 1], default=2)
    insurance = np.where(d['_HLTHPL1'] == 1, 0, 1)
    group = (d.DIABETE4 == 1).to_numpy().astype(int)
    event = (d.MEDCOST1 == 1).to_numpy().astype(int)
    cell = np.full(len(d), 'outside', dtype='<U8')
    for a in range(3):
        for inc in range(3):
            for ins in (0, 1):
                for g in (0, 1):
                    for e in (0, 1):
                        mask = domain & (age == a) & (income == inc) & (insurance == ins) & (group == g) & (event == e)
                        cell[mask] = cell_key(a, inc, ins, g, e)
    if len(d[['_STSTR', '_PSU']].drop_duplicates()) != len(d):
        raise ValueError('Expected one record per stratum/PSU pair')
    frame = pl.DataFrame({'stratum': d['_STSTR'].to_numpy(), 'weight': d['_LLCPWT'].to_numpy(),
                          'domain': domain.astype(int), 'cell': cell})
    sample = svy.Sample(frame, svy.Design(stratum='stratum', wgt='weight',
                                          singleton=svy.Singleton('center', domains='standard')))
    del d, frame, domain, age, income, insurance, group, event, cell
    gc.collect()
    print('Estimating 72 cell proportions and their joint covariance...', flush=True)
    estimates = sample.estimation.prop('cell', where=(svy.col('domain') == 1))
    expected_keys = {cell_key(a, inc, ins, g, e) for a in range(3) for inc in range(3)
                     for ins in (0, 1) for g in (0, 1) for e in (0, 1)}
    keys = set(estimates.keys())
    if not expected_keys.issubset(keys) or keys - expected_keys not in (set(), {'outside'}):
        raise ValueError(f'Unexpected cells: {keys ^ expected_keys}')
    z = {(a, inc, ins, g, e): svy.estd(cell_key(a, inc, ins, g, e))
         for a in range(3) for inc in range(3) for ins in (0, 1) for g in (0, 1) for e in (0, 1)}
    expressions = {}
    for name, axes in [('age_only', 1), ('age_income', 2), ('age_income_insurance', 3)]:
        terms = []
        for a in range(3):
            for inc_group in (range(3) if axes >= 2 else [None]):
                for ins_group in ((0, 1) if axes >= 3 else [None]):
                    income_values = [inc_group] if inc_group is not None else range(3)
                    insurance_values = [ins_group] if ins_group is not None else (0, 1)
                    totals = {(g, e): sum(z[a, inc, ins, g, e] for inc in income_values for ins in insurance_values)
                              for g in (0, 1) for e in (0, 1)}
                    reference = sum(totals.values())
                    rate_one = totals[1, 1] / (totals[1, 0] + totals[1, 1])
                    rate_zero = totals[0, 1] / (totals[0, 0] + totals[0, 1])
                    terms.append(reference * (rate_one - rate_zero))
        expressions[name] = sum(terms)
    expressions['income_minus_age'] = expressions['age_income'] - expressions['age_only']
    expressions['full_minus_age'] = expressions['age_income_insurance'] - expressions['age_only']
    saved = json.loads((HERE / 'access-uncertainty-probe-results.json').read_text(encoding='utf-8'))
    expected = {name: (saved['results'][name]['contrast'], saved['results'][name]['standard_error_centered'])
                for name in ('age_only', 'age_income', 'age_income_insurance')}
    expected['income_minus_age'] = (saved['comparisons']['age_income']['difference_from_age_only'],
                                    saved['comparisons']['age_income']['se'])
    expected['full_minus_age'] = (saved['comparisons']['age_income_insurance']['difference_from_age_only'],
                                  saved['comparisons']['age_income_insurance']['se'])
    results = {}
    for name, expression in expressions.items():
        print(f'Checking nonlinear expression {name}...', flush=True)
        row = estimates.contrast(expression).to_polars().to_dicts()[0]
        point, se = expected[name]
        if not np.isclose(row['est'], point, atol=1e-10, rtol=0):
            raise ValueError(f'{name}: estimate mismatch')
        if not np.isclose(row['se'], se, atol=1e-10, rtol=0):
            raise ValueError(f'{name}: standard error mismatch')
        results[name] = {'svy_estimate': row['est'], 'svy_se': row['se'],
                         'prototype_estimate': point, 'prototype_se': se,
                         'se_difference': row['se'] - se}
    (HERE / 'access-svy-nonlinear-validation-results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    rows = [f"| {name} | {100*r['svy_estimate']:+.4f} | {100*r['prototype_se']:.6f} | {100*r['svy_se']:.6f} |" for name, r in results.items()]
    report = f'''# Nonlinear survey-package check of complete-case standardization

Run date: {date.today().isoformat()}. This checks the computation under shared survey-design assumptions; it does not establish causal effects or interval coverage.

The [complete-case uncertainty probe](access-uncertainty-probe.md) uses record-level influence scores. This check independently expresses the three standardizations and their two paired differences as nonlinear functions of 72 weighted age-by-income-by-insurance-by-diabetes-by-outcome cell proportions. `svy` {svy.__version__} estimates the full cell covariance and applies its contrast machinery. It keeps the full survey design and centers full-sample singleton strata; the 2023 data have one record per stratum/PSU pair.

| Comparison | Estimate, percentage points | Prototype SE, percentage points | svy SE, percentage points |
|---|---:|---:|---:|
{chr(10).join(rows)}

Both calculations agree within 1e-10 on the proportion scale. This provides an end-to-end check of the numeric standardization and variance calculations, including covariance for paired changes, under the same data and design assumptions. It does not validate the sparse-cell normal approximation, prove the missing data are ignorable, or make these comparisons causal. The [bootstrap diagnostic](access-bootstrap-probe.md) illustrates sparse-event instability without establishing coverage.

Run `python access_uncertainty_probe.py` followed by `python access_svy_nonlinear_validation.py`. NumPy, pandas, Polars and svy are required. Results are saved in `access-svy-nonlinear-validation-results.json`.
'''
    (HERE / 'access-svy-nonlinear-validation.md').write_text(report, encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
