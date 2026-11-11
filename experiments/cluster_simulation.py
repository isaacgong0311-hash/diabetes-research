"""Evaluate the standardized-contrast variance under synthetic cluster sampling.

This simulation uses no human records and does not model BRFSS specifically.
"""
import json
from datetime import date
from pathlib import Path

import numpy as np

from standardized_contrast_probe import contrast_and_scores, design_variance

HERE = Path(__file__).resolve().parent
SEED = 483027
REPEATS = 1500
STRATA = 3
CLUSTERS_PER_STRATUM = 100
CLUSTERS_DRAWN = 8
PEOPLE_PER_CLUSTER = 30
NORMAL_QUANTILE = 1.959963984540054


def main():
    rng = np.random.default_rng(SEED)
    age_distributions = [[.60, .30, .10], [.30, .45, .25], [.15, .35, .50]]
    population = []
    for stratum in range(STRATA):
        for cluster in range(CLUSTERS_PER_STRATUM):
            age = rng.choice(3, PEOPLE_PER_CLUSTER, p=age_distributions[stratum])
            diabetes = rng.binomial(1, np.array([.15, .24, .36])[age])
            shared_effect = rng.normal(0, 1.1)
            logit = np.array([-1.4, -1.9, -2.3])[age] + .35 * diabetes + shared_effect
            outcome = rng.binomial(1, 1 / (1 + np.exp(-logit)))
            population.append((age, diabetes, outcome))

    true_age, true_group, true_outcome = [np.concatenate([p[i] for p in population]) for i in range(3)]
    truth, _ = contrast_and_scores(np.ones(len(true_age)), true_age, true_group, true_outcome)
    estimates, cluster_ses, row_ses = [], [], []
    excluded = 0
    for _ in range(REPEATS):
        selected = []
        strata = []
        psus = []
        for s in range(STRATA):
            for draw, c in enumerate(rng.integers(CLUSTERS_PER_STRATUM, size=CLUSTERS_DRAWN)):
                selected.append(population[s * CLUSTERS_PER_STRATUM + c])
                strata.extend([s] * PEOPLE_PER_CLUSTER)
                # A repeated draw of the same population cluster is a new sampled PSU.
                psus.extend([s * CLUSTERS_DRAWN + draw] * PEOPLE_PER_CLUSTER)
        age, group, outcome = [np.concatenate([p[i] for p in selected]) for i in range(3)]
        if any(not np.any((age == a) & (group == g)) for a in range(3) for g in (0, 1)):
            excluded += 1
            continue
        weight = np.full(len(age), CLUSTERS_PER_STRATUM / CLUSTERS_DRAWN)
        estimate, scores = contrast_and_scores(weight, age, group, outcome)
        estimates.append(estimate)
        cluster_ses.append(design_variance(strata, psus, scores) ** .5)
        row_ses.append(design_variance(strata, np.arange(len(age)), scores) ** .5)

    estimates = np.asarray(estimates)
    cluster_ses, row_ses = np.asarray(cluster_ses), np.asarray(row_ses)
    if len(estimates) == 0:
        raise RuntimeError('No usable samples')

    def summarize(ses):
        coverage = np.mean(np.abs(estimates - truth) <= NORMAL_QUANTILE * ses)
        return {'mean_standard_error': float(ses.mean()), 'coverage': float(coverage),
                'coverage_monte_carlo_se': float(np.sqrt(coverage * (1 - coverage) / len(estimates)))}

    result = {'seed': SEED, 'attempted_samples': REPEATS, 'valid_samples': len(estimates),
              'excluded_missing_age_group': excluded, 'population_size': len(true_age),
              'sample_size': STRATA * CLUSTERS_DRAWN * PEOPLE_PER_CLUSTER,
              'true_contrast': truth, 'mean_estimate': float(estimates.mean()),
              'empirical_bias': float(estimates.mean() - truth),
              'empirical_sd': float(estimates.std(ddof=1)),
              'cluster_psu': summarize(cluster_ses), 'row_psu': summarize(row_ses)}
    (HERE / 'cluster-simulation-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    c, r = result['cluster_psu'], result['row_psu']
    report = f'''# Synthetic cluster-sampling experiment

Run date: {date.today().isoformat()}. These are invented data and are not a diabetes or BRFSS finding.

## Design

A fixed synthetic population contains {STRATA} strata, {CLUSTERS_PER_STRATUM} clusters per stratum and {PEOPLE_PER_CLUSTER} people per cluster. Outcome probabilities share a random cluster effect. Age and group prevalence vary, and the target is the difference between groups after standardization to the population's pooled age distribution. The fixed-population target is {truth:.5f}.

We drew {CLUSTERS_DRAWN} clusters with replacement in each stratum, retaining everyone in each selected cluster, for {result['sample_size']:,} observations per sample. Repeated selections count as distinct sampled PSUs. We repeated this {REPEATS:,} times with seed {SEED}. Intervals use a normal 1.96 multiplier and the same estimated contrast; the only change is whether the variance estimator recognizes clusters or treats individual rows as PSUs. Samples missing a group in any age category are excluded; {excluded:,} of {REPEATS:,} samples were excluded.

## Results

| Variance calculation | Mean estimated SE | Approximate 95% interval coverage | Monte Carlo SE of coverage |
|---|---:|---:|---:|
| Correct sampled clusters as PSUs | {c['mean_standard_error']:.5f} | {100*c['coverage']:.1f}% | {100*c['coverage_monte_carlo_se']:.1f} percentage points |
| Incorrectly treating people as PSUs | {r['mean_standard_error']:.5f} | {100*r['coverage']:.1f}% | {100*r['coverage_monte_carlo_se']:.1f} percentage points |

Across valid samples, the empirical standard deviation of the contrast was {result['empirical_sd']:.5f} and empirical bias was {result['empirical_bias']:+.5f}. Coverage is conditional on valid samples and subject to simulation noise. A normal interval with only eight sampled clusters per stratum may have poor small-sample behavior; this is not a test of every available interval method.

The two methods address the same sampled data but use different variance assumptions. The direction and size of their difference depend on the estimator and simulated correlation; do not generalize this numerical result to another design. In the actual 2023 extract used in this project every record has a distinct stratum/PSU pair, so this hypothetical clustered design is not a description of that dataset.

## Reproduce

Run `python cluster_simulation.py` with NumPy and pandas installed. The complete numeric results are in `cluster-simulation-results.json`. This experiment uses the prototype's influence scores and is not independent validation of their formula.
'''
    (HERE / 'cluster-simulation.md').write_text(report, encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
