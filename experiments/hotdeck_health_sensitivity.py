"""Donor sensitivity using general-health-matched pools where possible."""
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

SEED = 725200
DRAWS = 200


def add_health_matching(pools, health, weight):
    """Split by observed health; fall back to the unsplit pool when empty."""
    result = []
    for p in pools:
        for h in (0, 1, 2):
            rec = p['recipients'][health[p['recipients']] == h]
            if len(rec) == 0:
                continue
            donor = p['donors'][health[p['donors']] == h]
            fallback = len(donor) == 0
            if fallback:
                donor = p['donors']
            donor_weights = weight[donor]
            updated = {k: p[k] for k in ('age', 'group', 'event', 'pattern', 'known_value')}
            updated.update({'health': h, 'recipients': rec, 'donors': donor,
                            'cumulative': np.cumsum(donor_weights), 'fallback': fallback,
                            'weight_only_ess': float(donor_weights.sum() ** 2 / np.dot(donor_weights, donor_weights))})
            result.append(updated)
    old = np.sort(np.concatenate([p['recipients'] for p in pools]))
    new = np.sort(np.concatenate([p['recipients'] for p in result]))
    if not np.array_equal(old, new):
        raise ValueError('Health split lost or duplicated recipients')
    return result


def main():
    rng = np.random.default_rng(SEED)
    d = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    domain = (d['_STATE'].between(1, 56) & (d['_LLCPWT'] > 0) & d.DIABETE4.isin([1, 3])
              & d.MEDCOST1.isin([1, 2]) & d['_AGEG5YR'].between(1, 13)).to_numpy()
    d = d.loc[domain]
    age = np.select([d['_AGEG5YR'] <= 5, d['_AGEG5YR'] <= 9], [0, 1], default=2)
    income = np.where(d['_INCOMG1'].between(1, 7),
                      np.select([d['_INCOMG1'] <= 2, d['_INCOMG1'] <= 4], [0, 1], default=2), -1)
    insurance = np.where(d['_HLTHPL1'].isin([1, 2]), np.where(d['_HLTHPL1'] == 1, 0, 1), -1)
    group = (d.DIABETE4 == 1).to_numpy().astype(int)
    outcome = (d.MEDCOST1 == 1).to_numpy().astype(int)
    health = np.select([d.GENHLTH.isin([1, 2, 3]), d.GENHLTH.isin([4, 5])], [0, 1], default=2)
    weight = d['_LLCPWT'].to_numpy(dtype=float)
    complete = (income >= 0) & (insurance >= 0)
    reference = np.bincount(age[complete] * 6 + income[complete] * 2 + insurance[complete],
                            weights=weight[complete], minlength=18)
    reference /= reference.sum()
    baseline = json.loads((HERE / 'hotdeck-sensitivity-results.json').read_text(encoding='utf-8'))
    if len(d) != baseline['domain_n'] or int((~complete).sum()) != baseline['recipient_n']:
        raise ValueError('Domain does not match baseline donor experiment')
    pools = add_health_matching(build_pools(age, group, outcome, income, insurance, weight), health, weight)
    recipient_indices = np.concatenate([p['recipients'] for p in pools])
    fallback_indices = np.concatenate([p['recipients'] for p in pools if p['fallback']]) if any(p['fallback'] for p in pools) else np.array([], dtype=int)
    low_indices = np.concatenate([p['recipients'] for p in pools if len(p['donors']) < 30]) if any(len(p['donors']) < 30 for p in pools) else np.array([], dtype=int)
    print(f"Prepared {len(pools)} health-stratified pools; {len(fallback_indices)} recipients use fallback.", flush=True)
    results = []
    for iteration in range(DRAWS):
        filled_income, filled_insurance = impute_once(income, insurance, pools, rng)
        rates, _ = scenario_estimate(weight, age, filled_income, filled_insurance, group, outcome, 0, 0, reference)
        results.append(float(rates[1] - rates[0]))
        if (iteration + 1) % 50 == 0:
            print(f'Completed {iteration + 1}/{DRAWS} health-matched donor draws', flush=True)
    results = np.asarray(results)
    pool_details = [{k: p[k] for k in ('age', 'group', 'event', 'pattern', 'known_value', 'health', 'fallback', 'weight_only_ess')}
                    | {'recipients': len(p['recipients']), 'donors': len(p['donors'])} for p in pools]
    result = {'seed': SEED, 'draws': DRAWS, 'recipient_n': len(recipient_indices),
              'pool_count': len(pools), 'fallback_recipient_n': len(fallback_indices),
              'fallback_weight_fraction': float(weight[fallback_indices].sum() / weight[recipient_indices].sum()),
              'under_30_donor_recipient_n': len(low_indices),
              'under_30_donor_weight_fraction': float(weight[low_indices].sum() / weight[recipient_indices].sum()),
              'minimum_donor_n': min(x['donors'] for x in pool_details),
              'minimum_weight_only_ess': min(x['weight_only_ess'] for x in pool_details),
              'fixed_reference_mean': float(results.mean()), 'fixed_reference_sd_draws': float(results.std(ddof=1)),
              'fixed_reference_min': float(results.min()), 'fixed_reference_max': float(results.max()),
              'baseline_fixed_mean': baseline['fixed_reference']['mean'], 'pools': pool_details,
              'limitation': 'Illustrative, conditional donor draws; no design variance or missingness-model validation.'}
    (HERE / 'hotdeck-health-sensitivity-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    report = f'''# Sensitivity to adding general health to donor matching

Run date: {date.today().isoformat()}. This is an exploratory alternative donor assumption, not causal evidence or a validated imputation model.

The [balance audit](hotdeck-balance-audit.md) found a difference in observed general health between recipients and their original donor pools. Here we split those pools by general health: excellent/very good/good, fair/poor, or unknown. When a split has recipients but no donors, we fall back to the original unsplit pool; this occurred for {len(fallback_indices):,} recipients, representing {100*result['fallback_weight_fraction']:.2f}% of recipient survey weight. Observed income and insurance responses are retained, and recipient survey weights stay fixed. We draw {DRAWS} completed datasets with seed {SEED}, using the same fixed complete-case standard population as the original [donor experiment](hotdeck-sensitivity.md).

| Matching strategy | Mean standardized gap, percentage points | SD between donor draws, points |
|---|---:|---:|
| Original donor pools | {100*baseline['fixed_reference']['mean']:+.2f} | {100*baseline['fixed_reference']['sd_between_draws']:.2f} |
| Add general-health matching | {100*result['fixed_reference_mean']:+.2f} | {100*result['fixed_reference_sd_draws']:.2f} |

The two sets use different seeds; the difference in their means reflects both changed assumptions and finite-draw variation. The between-draw SD is **not** a confidence interval and excludes survey sampling and donor-model uncertainty. Splitting produces {len(pools)} recipient pools; {len(low_indices):,} recipients ({100*result['under_30_donor_weight_fraction']:.1f}% of recipient weight) have fewer than 30 eligible donors, with a minimum of {result['minimum_donor_n']} donors. The minimum weight-only donor effective size is {result['minimum_weight_only_ess']:.1f}. Small or highly weighted pools can make the result sensitive to a few donors.

Matching on observed health can address that specific imbalance when no fallback is needed, but does not prove similarity on missing income or insurance, correct nonresponse, establish a missing-at-random assumption, or make the results causal. A more elaborate matching rule is not automatically more valid. Income, insurance, health, and cost barriers are self-reported, and people with unknown age are excluded. Pool counts and diagnostics are available in `hotdeck-health-sensitivity-results.json` without individual donor links.

## Reproduce

Run `python hotdeck_sensitivity.py`, then `python hotdeck_health_sensitivity.py`, with pandas and NumPy installed.
'''
    (HERE / 'hotdeck-health-sensitivity.md').write_text(report, encoding='utf-8')
    print(json.dumps({k: result[k] for k in result if k != 'pools'}, indent=2))


if __name__ == '__main__':
    main()
