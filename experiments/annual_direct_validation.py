"""Direct record-level check of the annual cell-covariance calculation."""
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / '.surveydeps'), str(HERE / '.deps')]
import numpy as np

from annual_contrast_probe import load_year
from brfss_3year_check import EXCLUDED
from standardized_contrast_probe import design_variance


def read_data(year):
    d = load_year(year)
    domain = (d['_STATE'].between(1, 56) & ~d['_STATE'].isin(EXCLUDED)
              & (d['_LLCPWT'] > 0) & d.DIABETE4.isin([1, 3])
              & d.MEDCOST1.isin([1, 2]) & d['_AGEG5YR'].between(1, 13)).to_numpy()
    ages = np.select([d['_AGEG5YR'] <= 5, d['_AGEG5YR'] <= 9], [0, 1], default=2)
    groups = (d.DIABETE4 == 1).to_numpy().astype(int)
    outcomes = (d.MEDCOST1 == 1).to_numpy().astype(int)
    weights = d['_LLCPWT'].to_numpy(dtype=float)
    totals, means = np.zeros((3, 2)), np.zeros((3, 2))
    for age in range(3):
        for group in (0, 1):
            mask = domain & (ages == age) & (groups == group)
            totals[age, group] = weights[mask].sum()
            means[age, group] = np.dot(weights[mask], outcomes[mask]) / totals[age, group]
    return {'domain': domain, 'age': ages, 'group': groups, 'outcome': outcomes,
            'weight': weights, 'stratum': d['_STSTR'].to_numpy(), 'psu': d['_PSU'].to_numpy(),
            'totals': totals, 'means': means}


def contributions(base, later):
    """Compute record influences directly from age shares and within-group means."""
    age_share = base['totals'].sum(axis=1) / base['totals'].sum()
    base_diff = base['means'][:, 1] - base['means'][:, 0]
    later_diff = later['means'][:, 1] - later['means'][:, 0]
    age_change = later_diff - base_diff
    delta = float(age_share @ age_change)
    variances = []
    for is_base, d in ((True, base), (False, later)):
        influence = np.zeros(len(d['weight']))
        for age in range(3):
            for group in (0, 1):
                mask = d['domain'] & (d['age'] == age) & (d['group'] == group)
                sign = 1 if group == 1 else -1
                rate_influence = (age_share[age] * sign * d['weight'][mask]
                                  * (d['outcome'][mask] - d['means'][age, group])
                                  / d['totals'][age, group])
                if is_base:
                    reference_influence = (d['weight'][mask] / d['totals'].sum()
                                           * (age_change[age] - delta))
                    influence[mask] = reference_influence - rate_influence
                else:
                    influence[mask] = rate_influence
        variances.append(design_variance(d['stratum'], d['psu'], influence, singleton='center'))
    return delta, variances


def main():
    saved = json.loads((HERE / 'annual-contrast-probe-results.json').read_text(encoding='utf-8'))
    print('Preparing full-design direct influence-score check...', flush=True)
    base = read_data(2023)
    results = {}
    for year in (2024, 2025):
        later = read_data(year)
        delta, variances = contributions(base, later)
        expected = saved['comparisons'][str(year)]
        direct_se = float(np.sqrt(sum(variances)))
        if not np.isclose(delta, expected['difference_in_contrasts'], rtol=0, atol=1e-10):
            raise ValueError(f'{year}: direct contrast does not agree')
        if not np.allclose(variances, [expected['variance_from_2023'], expected['variance_from_later_year']],
                           rtol=1e-7, atol=1e-12):
            raise ValueError(f'{year}: direct variance contributions do not agree')
        results[year] = {'direct_difference': delta, 'direct_se': direct_se,
                         'variance_contributions': variances,
                         'difference_from_svy_covariance_se': direct_se - expected['standard_error']}
        print(f'{year} direct SE {direct_se:.10f}; covariance SE {expected["standard_error"]:.10f}', flush=True)
        del later
    (HERE / 'annual-direct-validation-results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    rows = [f"| {year} | {100*r['direct_difference']:+.4f} | {100*r['direct_se']:.6f} | {r['difference_from_svy_covariance_se']:.3g} |" for year, r in results.items()]
    report = f'''# Direct check of the annual uncertainty calculation

Run date: {date.today().isoformat()}. This checks arithmetic under shared assumptions; it does not validate the statistical interpretation or assumptions for real surveys.

The [annual contrast probe](annual-contrast-probe.md) combines `svy` cell-proportion covariance matrices with derivatives. This program instead computes the contrast directly from weighted age-by-group means and the baseline age distribution. It derives per-record influence contributions from those quantities and aggregates them by the full-sample strata and PSUs, including records outside the comparison domain with zero contribution. The 2023 contribution includes both the reference-age distribution and baseline group rates; annual sampling is assumed independent, and full-sample singleton strata are centered.

| Comparison | Change in contrast, percentage points | Direct standard error, percentage points | Direct minus svy-covariance SE, proportion scale |
|---|---:|---:|---:|
{chr(10).join(rows)}

For each comparison, both the point estimate and the two year-specific variance contributions match the `svy` covariance approach within numerical tolerances. The checks use different computational pathways but the same linearization, data, singleton rule, and independence assumptions; this is not an independent study, a guarantee of coverage, or confirmation that annual samples have zero covariance.

Run `python annual_contrast_probe.py` followed by `python annual_direct_validation.py` after preparing the datasets. The results are also available in `annual-direct-validation-results.json`.
'''
    (HERE / 'annual-direct-validation.md').write_text(report, encoding='utf-8')


if __name__ == '__main__':
    main()
