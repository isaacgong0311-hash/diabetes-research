# Synthetic cluster-sampling experiment

Run date: 2026-11-01. These are invented data and are not a diabetes or BRFSS finding.

## Design

A fixed synthetic population contains 3 strata, 100 clusters per stratum and 30 people per cluster. Outcome probabilities share a random cluster effect. Age and group prevalence vary, and the target is the difference between groups after standardization to the population's pooled age distribution. The fixed-population target is 0.05388.

We drew 8 clusters with replacement in each stratum, retaining everyone in each selected cluster, for 720 observations per sample. Repeated selections count as distinct sampled PSUs. We repeated this 1,500 times with seed 483027. Intervals use a normal 1.96 multiplier and the same estimated contrast; the only change is whether the variance estimator recognizes clusters or treats individual rows as PSUs. Samples missing a group in any age category are excluded; 0 of 1,500 samples were excluded.

## Results

| Variance calculation | Mean estimated SE | Approximate 95% interval coverage | Monte Carlo SE of coverage |
|---|---:|---:|---:|
| Correct sampled clusters as PSUs | 0.03975 | 91.9% | 0.7 percentage points |
| Incorrectly treating people as PSUs | 0.03832 | 92.4% | 0.7 percentage points |

Across valid samples, the empirical standard deviation of the contrast was 0.04179 and empirical bias was +0.00182. Coverage is conditional on valid samples and subject to simulation noise. A normal interval with only eight sampled clusters per stratum may have poor small-sample behavior; this is not a test of every available interval method.

The two methods address the same sampled data but use different variance assumptions. The direction and size of their difference depend on the estimator and simulated correlation; do not generalize this numerical result to another design. In the actual 2023 extract used in this project every record has a distinct stratum/PSU pair, so this hypothetical clustered design is not a description of that dataset.

## Reproduce

Run `python cluster_simulation.py` with NumPy and pandas installed. The complete numeric results are in `cluster-simulation-results.json`. This experiment uses the prototype's influence scores and is not independent validation of their formula.
