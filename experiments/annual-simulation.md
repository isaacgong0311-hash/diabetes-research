# Synthetic shared-reference annual comparison

Run date: 2026-11-01. This experiment uses invented observations and does not validate inference for BRFSS.

We created two independent, fixed synthetic populations of 10,000 people each in three sampling strata. Each has a three-level age, binary group, and binary outcome; their age-specific group differences need not match. The true target is the later-minus-earlier change in the group outcome contrast, with *both* contrasts standardized to the earlier population's pooled age distribution. The true value is +0.00168.

For each of 1,000 repetitions (seed 194062), we independently sampled 540 people per population with replacement within strata, using inverse selection weights. The standard population and both sets of group rates were estimated from the samples. The linearized variance retains the dependency between the baseline contrast and the estimated reference; annual samples are independent by construction. Normal intervals use the 1.96 multiplier. 0 samples missing an age/group cell were excluded, leaving 1,000 valid repetitions.

| Diagnostic | Result |
|---|---:|
| Empirical bias | -0.00275 |
| Empirical standard deviation | 0.06520 |
| Mean estimated standard error | 0.06156 |
| Approximate 95% interval coverage | 94.1% |
| Monte Carlo SE of coverage | 0.7 percentage points |

This is a check in one favorable design with complete responses and independently sampled years. The simulation uses the same analytic derivatives as the annual prototype and therefore does not independently establish their correctness. It does not address actual cross-year dependence, nonresponse, missingness, small domain singletons, third-party conversion provenance, or the coverage of intervals for the real survey.

Run `python annual_simulation.py` with the same dependencies as the [annual contrast probe](annual-contrast-probe.md); results are in `annual-simulation-results.json`.
