"""Synthetic coverage check for a contrast using a shared estimated age reference."""
import json
from datetime import date
from pathlib import Path

import numpy as np

from annual_contrast_probe import analytic_gradients, standardized_difference
from standardized_contrast_probe import design_variance

HERE = Path(__file__).resolve().parent
SEED = 194062
REPEATS = 1000
POPULATION_SIZES = [4500, 3000, 2500]
SAMPLE_SIZES = [240, 180, 120]


def cell_proportions(weight, age, group, outcome):
    index = age * 4 + group * 2 + outcome
    p = np.bincount(index, weights=weight, minlength=12).astype(float)
    return p / p.sum(), index


def scores(weight, index, p, gradient):
    # Chain rule from normalized cell proportions to multiplicative weight changes.
    return weight / weight.sum() * (gradient[index] - gradient @ p)


def make_populations(rng, later):
    populations = []
    for s, n in enumerate(POPULATION_SIZES):
        age = rng.choice(3, n, p=[[.65, .25, .10], [.30, .45, .25], [.15, .35, .50]][s])
        group = rng.binomial(1, np.array([.12, .20, .32])[age])
        probability = np.array([.17, .10, .06])[age] + group * np.array([.07, .04, .03])[age]
        if later:
            probability = probability + group * np.array([.025, -.005, .015])[age]
        outcome = rng.binomial(1, probability)
        populations.append((age, group, outcome))
    return populations


def draw(rng, populations):
    chosen = []
    weights, strata = [], []
    for s, (population, size, sample_size) in enumerate(zip(populations, POPULATION_SIZES, SAMPLE_SIZES)):
        pick = rng.integers(size, size=sample_size)
        chosen.append(tuple(column[pick] for column in population))
        weights.append(np.full(sample_size, size / sample_size))
        strata.append(np.full(sample_size, s))
    age, group, outcome = [np.concatenate([x[i] for x in chosen]) for i in range(3)]
    weight, stratum = np.concatenate(weights), np.concatenate(strata)
    return weight, age, group, outcome, stratum


def main():
    rng = np.random.default_rng(SEED)
    populations = [make_populations(rng, False), make_populations(rng, True)]
    population_ps = []
    for pop in populations:
        age, group, outcome = [np.concatenate([x[i] for x in pop]) for i in range(3)]
        population_ps.append(cell_proportions(np.ones(len(age)), age, group, outcome)[0])
    truth = (standardized_difference(population_ps[0], population_ps[1])
             - standardized_difference(population_ps[0], population_ps[0]))
    estimates, ses = [], []
    excluded = 0
    for _ in range(REPEATS):
        samples = [draw(rng, p) for p in populations]
        ps, indices = [], []
        for weight, age, group, outcome, stratum in samples:
            p, index = cell_proportions(weight, age, group, outcome)
            ps.append(p)
            indices.append(index)
        if any(np.any(p.reshape(3, 2, 2).sum(axis=2) <= 0) for p in ps):
            excluded += 1
            continue
        delta = standardized_difference(ps[0], ps[1]) - standardized_difference(ps[0], ps[0])
        gradients = analytic_gradients(ps[0], ps[1])
        variances = []
        for sample, p, index, grad in zip(samples, ps, indices, gradients):
            weight, _, _, _, stratum = sample
            influence = scores(weight, index, p, grad)
            variances.append(design_variance(stratum, np.arange(len(weight)), influence))
        estimates.append(delta)
        ses.append(np.sqrt(sum(variances)))
    estimates, ses = np.asarray(estimates), np.asarray(ses)
    coverage = np.mean(np.abs(estimates - truth) <= 1.95996398454 * ses)
    result = {'seed': SEED, 'attempted': REPEATS, 'valid': len(estimates), 'excluded_empty_age_group': excluded,
              'sample_size_each_year': sum(SAMPLE_SIZES), 'finite_population_size_each_year': sum(POPULATION_SIZES),
              'truth': truth, 'mean_estimate': float(estimates.mean()),
              'bias': float(estimates.mean() - truth), 'empirical_sd': float(estimates.std(ddof=1)),
              'mean_estimated_se': float(ses.mean()), 'coverage': float(coverage),
              'coverage_monte_carlo_se': float(np.sqrt(coverage * (1 - coverage) / len(estimates)))}
    (HERE / 'annual-simulation-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    report = f'''# Synthetic shared-reference annual comparison

Run date: {date.today().isoformat()}. This experiment uses invented observations and does not validate inference for BRFSS.

We created two independent, fixed synthetic populations of {sum(POPULATION_SIZES):,} people each in three sampling strata. Each has a three-level age, binary group, and binary outcome; their age-specific group differences need not match. The true target is the later-minus-earlier change in the group outcome contrast, with *both* contrasts standardized to the earlier population's pooled age distribution. The true value is {truth:+.5f}.

For each of {REPEATS:,} repetitions (seed {SEED}), we independently sampled {sum(SAMPLE_SIZES):,} people per population with replacement within strata, using inverse selection weights. The standard population and both sets of group rates were estimated from the samples. The linearized variance retains the dependency between the baseline contrast and the estimated reference; annual samples are independent by construction. Normal intervals use the 1.96 multiplier. {excluded:,} samples missing an age/group cell were excluded, leaving {len(estimates):,} valid repetitions.

| Diagnostic | Result |
|---|---:|
| Empirical bias | {result['bias']:+.5f} |
| Empirical standard deviation | {result['empirical_sd']:.5f} |
| Mean estimated standard error | {result['mean_estimated_se']:.5f} |
| Approximate 95% interval coverage | {100*coverage:.1f}% |
| Monte Carlo SE of coverage | {100*result['coverage_monte_carlo_se']:.1f} percentage points |

This is a check in one favorable design with complete responses and independently sampled years. The simulation uses the same analytic derivatives as the annual prototype and therefore does not independently establish their correctness. It does not address actual cross-year dependence, nonresponse, missingness, small domain singletons, third-party conversion provenance, or the coverage of intervals for the real survey.

Run `python annual_simulation.py` with the same dependencies as the [annual contrast probe](annual-contrast-probe.md); results are in `annual-simulation-results.json`.
'''
    (HERE / 'annual-simulation.md').write_text(report, encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
