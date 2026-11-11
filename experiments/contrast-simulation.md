# Synthetic simulation: standardized contrast prototype

Run date: 2026-11-01. This synthetic simulation checks a calculation when the population answer is known. It is **not** evidence about people with diabetes and does not validate an analysis of BRFSS.

## Setup

We generated a fixed synthetic finite population of 11,000 individuals in three sampling strata with different age distributions. Each individual has a simulated binary group, three-level age, and a binary outcome. The simulated group and outcome probabilities vary by age. The true target is the group difference in outcome rates directly standardized to the full synthetic population's pooled age distribution.

For each of three sample sizes, we drew 1,000 independent samples with replacement, with unequal sampling fractions across design strata and inverse-probability weights. Each draw was treated as a separate PSU. For each sample with both groups represented in every age category, we calculated the contrast and a linearized with-replacement standard error, then formed an approximate normal 95% interval. Seed: 7321.

## Results

The true synthetic-population contrast is **0.0202** on the proportion scale.

| Sample size | Valid / attempted | Mean contrast | Empirical SD | Mean prototype SE | 95% interval coverage |
|---:|---:|---:|---:|---:|---:|
| 720 | 1,000 / 1,000 | 0.0213 | 0.0436 | 0.0415 | 92.9% |
| 1,440 | 1,000 / 1,000 | 0.0207 | 0.0293 | 0.0296 | 95.0% |
| 2,880 | 1,000 / 1,000 | 0.0202 | 0.0214 | 0.0209 | 93.8% |

Coverage is the proportion of simulations whose intervals contained the fixed synthetic truth. At coverage near 95%, the Monte Carlo standard error is roughly 0.7 percentage points for 1,000 independent simulations. Samples lacking a group in any age cell are excluded and counted in the JSON results. The target standard population in each sample is estimated from the pooled sample, so the prototype includes variation in both age-specific rates and the reference distribution. A shortfall relative to nominal 95% in any scenario is a reason for further investigation, not proof of a particular cause.

## Interpretation

This tests one favorable, fully observed, with-replacement design at three sample sizes and one set of event rates. It does not establish coverage for BRFSS, which has different sampling, weights, nonresponse, missingness, singleton strata, and data distributions. The uncertainty analysis in the main survey reports remains unvalidated for use in population inference. See the [supported-package calculation check](svy-contrast-validation.md) and a separate [hypothetical cluster-sampling simulation](cluster-simulation.md).

## Reproduce

Run `python contrast_simulation.py` with NumPy and pandas available. Results are in `contrast-simulation-results.json`. The simulation calls functions from `standardized_contrast_probe.py` and uses no patient records.
