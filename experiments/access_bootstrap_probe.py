"""Exploratory stratified PSU bootstrap of complete-case standardizations.

This does not establish coverage for BRFSS or correct nonresponse/missingness.
"""
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

SEED = 60241
REPEATS = 500
SPECS = ('age_only', 'age_income', 'age_income_insurance')


def estimates_from_cells(counts):
    """Counts are weighted age x income x insurance x group x outcome cells."""
    output = []
    for totals in (counts.sum(axis=(1, 2)), counts.sum(axis=2), counts):
        group_total = totals.sum(axis=-1)
        if np.any(group_total <= 0):
            raise ValueError('Missing a standardization group in at least one cell')
        mean = totals[..., 1] / group_total
        reference = group_total.sum(axis=-1)
        output.append(float(np.sum(reference * (mean[..., 1] - mean[..., 0])) / reference.sum()))
    return np.asarray(output)


def main():
    rng = np.random.default_rng(SEED)
    d = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    if d[['_STSTR', '_PSU']].isna().any().any() or len(d[['_STSTR', '_PSU']].drop_duplicates()) != len(d):
        raise ValueError('Resampling requires a distinct PSU for each record within stratum')
    domain = (d['_STATE'].between(1, 56) & (d['_LLCPWT'] > 0) & d.DIABETE4.isin([1, 3])
              & d.MEDCOST1.isin([1, 2]) & d['_AGEG5YR'].between(1, 13)
              & d['_INCOMG1'].between(1, 7) & d['_HLTHPL1'].isin([1, 2])).to_numpy()
    age = np.select([d['_AGEG5YR'] <= 5, d['_AGEG5YR'] <= 9], [0, 1], default=2)
    income = np.select([d['_INCOMG1'] <= 2, d['_INCOMG1'] <= 4], [0, 1], default=2)
    insurance = np.where(d['_HLTHPL1'] == 1, 0, 1)
    group = (d.DIABETE4 == 1).to_numpy().astype(int)
    event = (d.MEDCOST1 == 1).to_numpy().astype(int)
    leaf = ((((age * 3 + income) * 2 + insurance) * 2 + group) * 2 + event)
    order = np.argsort(d['_STSTR'].to_numpy(), kind='stable')
    sorted_strata = d['_STSTR'].to_numpy()[order]
    domain, leaf = domain[order], leaf[order]
    weights = d['_LLCPWT'].to_numpy(dtype=float)[order]
    n = len(order)
    starts = np.r_[0, np.flatnonzero(sorted_strata[1:] != sorted_strata[:-1]) + 1]
    sizes = np.diff(np.r_[starts, n])
    scales = np.repeat(np.where(sizes > 1, sizes / np.maximum(sizes - 1, 1), 1), sizes)
    singleton_starts = starts[sizes == 1]
    multi_starts, multi_sizes = starts[sizes > 1], sizes[sizes > 1]
    def aggregate(multiplicity):
        return np.bincount(leaf[domain], weights=weights[domain] * multiplicity[domain],
                           minlength=72).reshape(3, 3, 2, 2, 2)
    original = estimates_from_cells(aggregate(np.ones(n)))
    expected = json.loads((HERE / 'access-uncertainty-probe-results.json').read_text(encoding='utf-8'))
    for i, spec in enumerate(SPECS):
        if not np.isclose(original[i], expected['results'][spec]['contrast'], atol=1e-10, rtol=0):
            raise ValueError(f'{spec}: original estimate mismatch')
    repetitions, zero_event_count, invalid = [], 0, 0
    for repeat in range(REPEATS):
        # Draw n_h-1 PSUs from each non-singleton stratum, rescaling weights by
        # n_h/(n_h-1); singleton PSUs are fixed (zero bootstrap variance).
        draws = [rng.integers(start, start + size, size=size - 1)
                 for start, size in zip(multi_starts, multi_sizes)]
        selected = np.concatenate([singleton_starts, *draws])
        multiplicity = np.bincount(selected, minlength=n) * scales
        cells = aggregate(multiplicity)
        if np.any(cells[..., 1] == 0):
            zero_event_count += 1
        try:
            values = estimates_from_cells(cells)
        except ValueError:
            invalid += 1
            continue
        repetitions.append(values)
        if (repeat + 1) % 100 == 0:
            print(f'Completed {repeat + 1}/{REPEATS} bootstrap draws', flush=True)
    reps = np.asarray(repetitions)
    if len(reps) < REPEATS * .95:
        raise ValueError('Too many bootstrap replicates lack a group in at least one cell')
    summary = {}
    for i, spec in enumerate(SPECS):
        low, high = np.quantile(reps[:, i], [.025, .975])
        summary[spec] = {'point': float(original[i]), 'bootstrap_sd': float(reps[:, i].std(ddof=1)),
                         'bootstrap_percentile_low': float(low), 'bootstrap_percentile_high': float(high),
                         'linearized_skip_se': expected['results'][spec]['standard_error_skip']}
    result = {'seed': SEED, 'attempted': REPEATS, 'valid': len(reps), 'invalid_missing_group': invalid,
              'replicates_with_any_zero_event_joint_group_cell': zero_event_count,
              'full_design_strata': len(sizes), 'full_design_singletons_fixed': len(singleton_starts),
              'estimates': summary}
    (HERE / 'access-bootstrap-probe-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    rows = [f"| {name} | {100*z['point']:+.2f} | {100*z['linearized_skip_se']:.2f} | {100*z['bootstrap_sd']:.2f} | {100*z['bootstrap_percentile_low']:+.2f} to {100*z['bootstrap_percentile_high']:+.2f} |" for name, z in summary.items()]
    report = f'''# Stratified PSU bootstrap diagnostic for complete-case contrasts

Run date: {date.today().isoformat()}. This is exploratory resampling of the observed survey, not a validation of coverage or a causal analysis.

## Method

Using the full 2023 sample design, including records outside the complete-case comparison domain, this program independently resamples PSUs within each design stratum. Each stratum with n > 1 sampled PSUs contributes n−1 draws with replacement and a weight multiplier n/(n−1). The {len(singleton_starts)} full-sample singleton PSUs stay fixed, so this bootstrap gives them zero variance contribution; the comparison is the **skip-singleton** linearized SE. All records have a unique stratum/PSU pair in this extract. The bootstrap recomputes the estimated pooled reference distribution and the within-cell rates in every replicate. It holds the released analysis weights fixed apart from the resampling multipliers; it does not rerun survey weight calibration or model nonresponse.

Seed {SEED}; {REPEATS:,} attempted replicates, {len(reps):,} valid, and {invalid:,} missing a group in at least one standardization cell. {zero_event_count:,} attempted replicates had at least one of the 36 joint group/cells with zero observed events. A zero event cell can still yield a finite estimate, but it is a warning about stability.

| Standardization | Point contrast, percentage points | Linearized SE (skip singleton), points | Bootstrap SD, points | Bootstrap percentile interval, points |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

These are descriptive diagnostics. With only {REPEATS:,} replicates, tail quantiles have substantial Monte Carlo uncertainty. This resampling scheme is a simplified with-replacement approximation and has not been independently validated as CDC replicate weights for this survey. It cannot repair missing income or insurance, guarantee coverage for sparse cells, account for residual confounding, or determine the cause of a difference. The normal intervals in the [linearization probe](access-uncertainty-probe.md) use centered singleton handling, unlike the skip rule here.

## Reproduce

Run `python access_uncertainty_probe.py` followed by `python access_bootstrap_probe.py` with NumPy and pandas. All results are in `access-bootstrap-probe-results.json`.
'''
    (HERE / 'access-bootstrap-probe.md').write_text(report, encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
