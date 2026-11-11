"""Exploratory year-to-year contrast with an estimated shared 2023 reference.

Treats annual samples as independent, an assumption requiring further review.
"""
import gc
import json
import os
import sys
from datetime import date
from pathlib import Path

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / '.surveydeps'), str(HERE / '.deps')]

import duckdb
import numpy as np
import pandas as pd
import polars as pl
import svy

from brfss_3year_check import EXCLUDED

YEARS = (2023, 2024, 2025)
FIELDS = ['_STATE', '_LLCPWT', '_STSTR', '_PSU', '_AGEG5YR', 'DIABETE4', 'MEDCOST1']
KEYS = [f'a{a}g{g}e{e}' for a in range(3) for g in (0, 1) for e in (0, 1)]


def load_year(year):
    if year == 2023:
        return pd.read_csv(HERE / 'brfss2023-selected.csv.gz', usecols=FIELDS)
    file = HERE / f'brfss-{year}-mirror.parquet'
    db = duckdb.connect()
    available = {row[0].upper(): row[0] for row in db.execute('DESCRIBE SELECT * FROM read_parquet(?)', [str(file)]).fetchall()}
    if set(FIELDS) - available.keys():
        raise ValueError(f'Missing columns in {year}')
    select = ', '.join('"' + available[c] + '" AS "' + c + '"' for c in FIELDS)
    result = db.execute(f'SELECT {select} FROM read_parquet(?)', [str(file)]).df()
    db.close()
    return result


def estimate_cells(year):
    data = load_year(year)
    if data[['_STSTR', '_PSU']].isna().any().any() or len(data[['_STSTR', '_PSU']].drop_duplicates()) != len(data):
        raise ValueError(f'{year}: one-record PSU assumption fails')
    domain = (data['_STATE'].between(1, 56) & ~data['_STATE'].isin(EXCLUDED)
              & (data['_LLCPWT'] > 0) & data.DIABETE4.isin([1, 3])
              & data.MEDCOST1.isin([1, 2]) & data['_AGEG5YR'].between(1, 13))
    ages = np.select([data['_AGEG5YR'] <= 5, data['_AGEG5YR'] <= 9], [0, 1], default=2)
    group = (data.DIABETE4 == 1).to_numpy().astype(int)
    outcome = (data.MEDCOST1 == 1).to_numpy().astype(int)
    cells = np.full(len(data), 'outside', dtype='<U8')
    for a in range(3):
        for g in (0, 1):
            for e in (0, 1):
                cells[domain & (ages == a) & (group == g) & (outcome == e)] = f'a{a}g{g}e{e}'
    frame = pl.DataFrame({'stratum': data['_STSTR'].to_numpy(), 'weight': data['_LLCPWT'].to_numpy(),
                          'domain': domain.to_numpy().astype(int), 'cell': cells})
    sample = svy.Sample(frame, svy.Design(stratum='stratum', wgt='weight',
                                         singleton=svy.Singleton('center', domains='standard')))
    estimates = sample.estimation.prop('cell', where=(svy.col('domain') == 1))
    keys = estimates.keys()
    if not set(KEYS).issubset(keys) or set(keys) - set(KEYS) not in (set(), {'outside'}):
        raise ValueError(f'{year}: unexpected cells {keys}')
    table = estimates.to_polars().to_dicts()
    values = {r['cell']: r['est'] for r in table}
    indices = [keys.index(k) for k in KEYS]
    proportions = np.array([values[k] for k in KEYS])
    covariance = estimates.covariance[np.ix_(indices, indices)]
    if not np.isclose(proportions.sum(), 1) or not np.isfinite(covariance).all():
        raise ValueError(f'{year}: malformed estimates')
    n = int(domain.sum())
    del sample, estimates, frame, data, cells
    gc.collect()
    return proportions, covariance, n


def standardized_difference(reference, year):
    ref = reference.reshape(3, 2, 2)
    p = year.reshape(3, 2, 2)
    age_weights = ref.sum(axis=(1, 2)) / ref.sum()
    denominators = p.sum(axis=2)
    if np.any(denominators <= 0):
        raise ValueError('Empty age/group cell')
    rates = p[:, :, 1] / denominators
    return float(age_weights @ (rates[:, 1] - rates[:, 0]))


def derivative(function, x, step=1e-6):
    result = np.empty_like(x)
    for i in range(len(x)):
        up, down = x.copy(), x.copy()
        up[i] += step
        down[i] -= step
        result[i] = (function(up) - function(down)) / (2 * step)
    return result


def analytic_gradients(reference, year):
    """Analytic derivatives of D(reference, year) - D(reference, reference)."""
    ref = reference.reshape(3, 2, 2)
    curr = year.reshape(3, 2, 2)
    total = ref.sum()
    age_weights = ref.sum(axis=(1, 2)) / total
    ref_w, curr_w = ref.sum(axis=2), curr.sum(axis=2)
    if np.any(ref_w <= 0) or np.any(curr_w <= 0) or total <= 0:
        raise ValueError('Empty age/group cell')
    ref_rate, curr_rate = ref[:, :, 1] / ref_w, curr[:, :, 1] / curr_w
    age_change = (curr_rate[:, 1] - curr_rate[:, 0]) - (ref_rate[:, 1] - ref_rate[:, 0])
    overall = age_weights @ age_change
    ref_grad, curr_grad = np.empty_like(ref), np.empty_like(curr)
    for a in range(3):
        for g in (0, 1):
            sign = 1 if g == 1 else -1
            for e in (0, 1):
                ref_grad[a, g, e] = ((age_change[a] - overall) / total
                                      - age_weights[a] * sign * (e - ref_rate[a, g]) / ref_w[a, g])
                curr_grad[a, g, e] = age_weights[a] * sign * (e - curr_rate[a, g]) / curr_w[a, g]
    return ref_grad.ravel(), curr_grad.ravel()


def main():
    data = {}
    for year in YEARS:
        print(f'Estimating {year} cell proportions and covariance...', flush=True)
        p, cov, n = estimate_cells(year)
        data[year] = {'p': p, 'cov': cov, 'n': n}
    ref = data[2023]['p']
    saved = json.loads((HERE / 'brfss-3year-results.json').read_text(encoding='utf-8'))
    differences = {}
    for year in YEARS:
        p = data[year]['p']
        observed = standardized_difference(ref, p)
        old = saved['years'][str(year)]['standardized_rates']
        if not np.isclose(observed, old['diabetes'] - old['no_diabetes'], atol=1e-10, rtol=0):
            raise ValueError(f'{year}: contrast differs from prior point estimate')
        differences[year] = observed
    comparisons = {}
    for year in (2024, 2025):
        current = data[year]['p']
        # Both the 2023 reference and the 2023 group rates come from the same
        # sample. Perturbing them together retains their covariance.
        reference_gradient = derivative(lambda x: standardized_difference(x, current) - standardized_difference(x, x), ref)
        year_gradient = derivative(lambda x: standardized_difference(ref, x) - standardized_difference(ref, ref), current)
        analytic_ref, analytic_year = analytic_gradients(ref, current)
        if not np.allclose(reference_gradient, analytic_ref, rtol=1e-7, atol=1e-8):
            raise ValueError('2023 numerical and analytic gradients differ')
        if not np.allclose(year_gradient, analytic_year, rtol=1e-7, atol=1e-8):
            raise ValueError(f'{year} numerical and analytic gradients differ')
        variance_ref = float(reference_gradient @ data[2023]['cov'] @ reference_gradient)
        variance_year = float(year_gradient @ data[year]['cov'] @ year_gradient)
        if min(variance_ref, variance_year) < -1e-12:
            raise ValueError('Unexpected negative variance')
        se = np.sqrt(max(0, variance_ref) + max(0, variance_year))
        delta = differences[year] - differences[2023]
        comparisons[year] = {'difference_in_contrasts': delta, 'standard_error': float(se),
                             'normal_95_low': float(delta - 1.95996398454 * se),
                             'normal_95_high': float(delta + 1.95996398454 * se),
                             'variance_from_2023': variance_ref, 'variance_from_later_year': variance_year}
    result = {'svy_version': svy.__version__, 'year_sample_n': {y: data[y]['n'] for y in YEARS},
              'within_year_contrasts': differences, 'comparisons': comparisons,
              'assumption': 'Independent annual samples; cross-year covariance assumed zero.',
              'limitation': 'Exploratory delta-method calculation; not independently validated or a trend test.'}
    (HERE / 'annual-contrast-probe-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    rows = []
    for year, value in comparisons.items():
        rows.append(f"| {year} versus 2023 | {100*value['difference_in_contrasts']:+.2f} | {100*value['standard_error']:.2f} | {100*value['normal_95_low']:+.2f} to {100*value['normal_95_high']:+.2f} |")
    report = f'''# Exploratory annual contrast uncertainty probe

Run date: {date.today().isoformat()}. This is an experimental computational analysis, not a validated trend test or causal comparison.

## Target and method

For 2023, 2024, and 2025, the target is the cost-barrier rate among respondents reporting diabetes minus that among respondents reporting no diabetes, standardized to the *same estimated 2023 pooled age distribution*. The comparison is the later-year contrast minus the 2023 contrast, in the common footprint of 44 states and DC. It excludes California, Kentucky, Mississippi, Nevada, Pennsylvania, and Tennessee; it is not a U.S.-wide estimate.

The supported `svy` package version {svy.__version__} estimates each year's 12 weighted age-by-group-by-outcome cell proportions and their design covariance, preserving the full design outside the domain and centering full-sample singleton strata. The script verifies one record per stratum/PSU pair in each year before omitting explicit PSU identifiers. It numerically differentiates the difference-in-contrasts with respect to the cell proportions and checks the derivatives against a separate analytic expression. The 2023 reference distribution and 2023 group rates are perturbed together to preserve their covariance. The calculation assumes independent annual samples and zero cross-year covariance; repeated respondents or other cross-year dependence could violate that assumption. It uses normal approximate intervals and does not address the joint uncertainty in both comparisons or multiple testing.

## Preliminary numerical checks

The annual contrasts reproduce the previously calculated three-year point estimates. Under the stated assumptions:

| Comparison | Change in contrast, percentage points | SE, percentage points | Approximate 95% interval, percentage points |
|---|---:|---:|---:|
{chr(10).join(rows)}

These numbers are exploratory. A separate [direct record-level calculation](annual-direct-validation.md) checks the two variance contributions against the covariance-matrix route under the same assumptions; neither calculation establishes interval coverage or cross-year independence. They do not establish a trend or causal change. The comparison can reflect changes in composition, nonresponse, survey coverage, and measurement. Diabetes is self-reported and does not distinguish type 2. The third-party conversions were checked by hashes and selected official benchmarks, not record by record against CDC source files.

## Reproduce

Run `python brfss_3year_check.py` and then `python annual_contrast_probe.py` with NumPy, pandas, DuckDB, Polars and svy installed. Raw estimates, variance contributions, and assumptions are in `annual-contrast-probe-results.json`.
'''
    (HERE / 'annual-contrast-probe.md').write_text(report, encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
