"""Exploratory weighted donor draws for missing income and insurance.

Not a validated multiple-imputation procedure, clinical tool, or causal analysis.
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

from missing_covariate_scenarios import scenario_estimate

SEED = 725199
REPEATS = 200


def build_pools(age, group, outcome, income, insurance, weight):
    """Construct exact-match donor pools while retaining observed covariates.

    All arrays describe known-age domain records. A donor has both covariates
    known and matches age, group, outcome, and any observed covariate.
    """
    age = np.asarray(age); group = np.asarray(group); outcome = np.asarray(outcome)
    income = np.asarray(income); insurance = np.asarray(insurance); weight = np.asarray(weight)
    complete = (income >= 0) & (insurance >= 0)
    if not np.isfinite(weight).all() or np.any(weight <= 0):
        raise ValueError('Weights must be finite and positive')
    pools = []
    for a in range(3):
        for g in (0, 1):
            for event in (0, 1):
                matching = (age == a) & (group == g) & (outcome == event)
                patterns = [('income_only', (income < 0) & (insurance >= 0), insurance, (0, 1)),
                            ('insurance_only', (insurance < 0) & (income >= 0), income, (0, 1, 2)),
                            ('both', (income < 0) & (insurance < 0), None, (None,))]
                for pattern, missing, known, known_values in patterns:
                    for value in known_values:
                        recipients = matching & missing
                        donors = matching & complete
                        if known is not None:
                            recipients &= known == value
                            donors &= known == value
                        recipient_indices = np.flatnonzero(recipients)
                        if not len(recipient_indices):
                            continue
                        donor_indices = np.flatnonzero(donors)
                        if not len(donor_indices):
                            raise ValueError(f'No donor: age={a}, group={g}, event={event}, {pattern}, known={value}')
                        donor_weights = weight[donor_indices]
                        cumulative = np.cumsum(donor_weights)
                        ess = donor_weights.sum() ** 2 / np.dot(donor_weights, donor_weights)
                        pools.append({'age': a, 'group': g, 'event': event, 'pattern': pattern,
                                      'known_value': value, 'recipients': recipient_indices,
                                      'donors': donor_indices, 'cumulative': cumulative,
                                      'weight_only_ess': float(ess)})
    intended = np.flatnonzero(~complete)
    assigned = np.concatenate([x['recipients'] for x in pools]) if pools else np.array([], dtype=int)
    if len(assigned) != len(intended) or not np.array_equal(np.sort(assigned), intended):
        raise ValueError('Missing cases were not assigned to exactly one donor pool')
    return pools


def impute_once(income, insurance, pools, rng):
    """Draw donor records with replacement; never replace known answers."""
    new_income = np.asarray(income).copy()
    new_insurance = np.asarray(insurance).copy()
    for p in pools:
        selection = rng.random(len(p['recipients'])) * p['cumulative'][-1]
        chosen = p['donors'][np.searchsorted(p['cumulative'], selection, side='right')]
        recipient = p['recipients']
        if p['pattern'] in ('income_only', 'both'):
            new_income[recipient] = income[chosen]
        if p['pattern'] in ('insurance_only', 'both'):
            new_insurance[recipient] = insurance[chosen]
    if np.any(new_income < 0) or np.any(new_insurance < 0):
        raise ValueError('Some missing values remain')
    if np.any(new_income[np.asarray(income) >= 0] != np.asarray(income)[np.asarray(income) >= 0]):
        raise ValueError('An observed income was overwritten')
    if np.any(new_insurance[np.asarray(insurance) >= 0] != np.asarray(insurance)[np.asarray(insurance) >= 0]):
        raise ValueError('An observed insurance response was overwritten')
    return new_income, new_insurance


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
    weight = d['_LLCPWT'].to_numpy(dtype=float)
    audit = json.loads((HERE / 'missingness-standardized-probe-results.json').read_text(encoding='utf-8'))
    if len(d) != audit['known_age_domain_n'] or np.sum((income < 0) | (insurance < 0)) != audit['incomplete_n']:
        raise ValueError('Known-age domain does not match prior audit')
    complete = (income >= 0) & (insurance >= 0)
    ref = np.bincount(age[complete] * 6 + income[complete] * 2 + insurance[complete],
                      weights=weight[complete], minlength=18)
    ref /= ref.sum()
    pools = build_pools(age, group, outcome, income, insurance, weight)
    print(f"Prepared {len(pools)} donor pools for {sum(len(x['recipients']) for x in pools):,} recipients.", flush=True)
    draws = []
    for iteration in range(REPEATS):
        filled_income, filled_insurance = impute_once(income, insurance, pools, rng)
        varying, nmin = scenario_estimate(weight, age, filled_income, filled_insurance, group, outcome, 0, 0)
        fixed, _ = scenario_estimate(weight, age, filled_income, filled_insurance, group, outcome, 0, 0, ref)
        draws.append((varying[1] - varying[0], fixed[1] - fixed[0], nmin))
        if (iteration + 1) % 50 == 0:
            print(f'Completed {iteration + 1}/{REPEATS} donor draws', flush=True)
    draws = np.asarray(draws)
    def distribution(x):
        return {'mean': float(x.mean()), 'sd_between_draws': float(x.std(ddof=1)),
                'minimum': float(x.min()), 'maximum': float(x.max()),
                'draw_percentile_2_5': float(np.quantile(x, .025)),
                'draw_percentile_97_5': float(np.quantile(x, .975))}
    pool_summary = [{k: p[k] for k in ('age', 'group', 'event', 'pattern', 'known_value', 'weight_only_ess')}
                    | {'donors': len(p['donors']), 'recipients': len(p['recipients'])} for p in pools]
    result = {'seed': SEED, 'draws': REPEATS, 'domain_n': len(d), 'complete_n': int(complete.sum()),
              'recipient_n': int((~complete).sum()), 'varying_reference': distribution(draws[:, 0]),
              'fixed_reference': distribution(draws[:, 1]), 'min_group_cell_n_over_draws': int(draws[:, 2].min()),
              'donor_pools': pool_summary, 'minimum_donor_n': min(x['donors'] for x in pool_summary),
              'minimum_donor_weight_only_ess': min(x['weight_only_ess'] for x in pool_summary),
              'not_included': 'Sampling variance, donor-distribution estimation uncertainty, missing-age cases, and nonignorable missingness.'}
    (HERE / 'hotdeck-sensitivity-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    variable, fixed = result['varying_reference'], result['fixed_reference']
    small_pools = sum(p['donors'] < 30 for p in pool_summary)
    report = f'''# Weighted donor-draw sensitivity experiment

Run date: {date.today().isoformat()}. This is exploratory research under a strong donor-exchangeability assumption. It is not a validated multiple-imputation analysis, a confidence interval, or a causal result.

## Setup

The known-age 2023 comparison domain contains {len(d):,} respondents in 48 states and DC, of whom {int((~complete).sum()):,} have unknown income and/or insurance. To give those missing fields hypothetical values, we select donors with both fields observed who match the recipient's broad age band, diabetes response, and known cost-barrier outcome. If just one covariate is missing, the donor also matches the other, observed covariate. If both are missing, the pair comes from the same donor. Donors are sampled with replacement with probability proportional to their survey weight within each pool; recipient survey weights remain unchanged. Recorded answers are never overwritten.

These matching variables are a very limited model. Drawing from observed respondents assumes the donor distribution is informative for missing respondents within each pool. That assumption cannot be verified from these data and may fail even when observed cost rates are similar. This is a simple sensitivity experiment inspired by [Census hot-deck methods](https://www.census.gov/programs-surveys/cps/technical-documentation/methodology/imputation-of-unreported-data-items.html), not the Census procedure or a CDC method. A [survey methods review](https://pmc.ncbi.nlm.nih.gov/articles/3130338/) discusses the separate problem of valid variance estimation after hot-deck imputation.

## Results across {REPEATS} donor draws

The table shows the diabetes-minus-no-diabetes cost-barrier gap, standardized by age, income, and insurance. The fixed standard is the pooled complete-case distribution; the varying standard is recalculated after every donor draw. The displayed spread is **between these donor draws only** and does not include sampling variance or uncertainty about how the donor distributions were estimated. It is not a 95% confidence interval.

| Reference distribution | Mean gap, percentage points | SD across draws, points | Minimum to maximum across draws, points |
|---|---:|---:|---:|
| Fixed complete-case distribution | {100*fixed['mean']:+.2f} | {100*fixed['sd_between_draws']:.2f} | {100*fixed['minimum']:+.2f} to {100*fixed['maximum']:+.2f} |
| Recomputed in each draw | {100*variable['mean']:+.2f} | {100*variable['sd_between_draws']:.2f} | {100*variable['minimum']:+.2f} to {100*variable['maximum']:+.2f} |

There are {len(pools)} nonempty donor pools, of which {small_pools} have fewer than 30 donors. The smallest pool has {result['minimum_donor_n']} donors and the lowest weight-only effective size is {result['minimum_donor_weight_only_ess']:.1f}; these minima may occur in different pools. Weight-only effective size is a weight-concentration diagnostic, not survey degrees of freedom. The smallest unweighted group/cell size over all completed datasets was {result['min_group_cell_n_over_draws']}. Pool-level counts and draw summaries are saved in the JSON; no imputed individual records are exported.

The earlier [fixed-assignment stress scenarios](missing-covariate-scenarios.md) explore much stronger, homogeneous assumptions and are neither bounds nor a model. This donor experiment uses different assumptions; agreement or disagreement does not identify the true missing answers. Income and insurance may depend on unmeasured factors or on missingness itself, donor pools can be sparse, and outcome, age and insurance are self-reported. Unknown age cases remain excluded. Valid inference would require an appropriate imputation model, assessment of its assumptions, survey-design variance, and an approach that accounts for imputation-model uncertainty.

Further checks include [masking known answers](hotdeck-masking-validation.md), an observed [general-health balance audit](hotdeck-balance-audit.md), an alternative [health-matched donor rule](hotdeck-health-sensitivity.md), and [repeated holdout splits](hotdeck-repeated-masking.md). None establish how the method performs on the truly missing answers.

## Reproduce

Run `python missingness_standardized_probe.py`, then `python hotdeck_sensitivity.py` with NumPy and pandas installed. The seed is {SEED}; output summaries are in `hotdeck-sensitivity-results.json`.
'''
    (HERE / 'hotdeck-sensitivity.md').write_text(report, encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('domain_n', 'complete_n', 'recipient_n', 'varying_reference',
                                             'fixed_reference', 'minimum_donor_n', 'minimum_donor_weight_only_ess')}, indent=2))


if __name__ == '__main__':
    main()
