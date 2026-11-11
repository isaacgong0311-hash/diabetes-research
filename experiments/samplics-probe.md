# Exploratory survey-estimator cross-check

This check compares two implementations on the same checksum-verified 2023 BRFSS source. The full survey sample and its strata/PSU structure are retained, with subgroups expressed as ratios of weighted domain indicators. Three domains are checked: the published 65+ fair/poor-health example, reported diabetes with a definite cost response, and reported no diabetes with a definite cost response.

Both implementations use the **skip-singleton** policy for this comparison. This sets the variance contribution of full-sample singleton strata to zero and may understate uncertainty. It differs from the centered singleton policy in the [published benchmark](https://muntasirmasum.github.io/brfssdata/articles/survey-design.html); see [the separate centered-policy probe](survey-variance-probe.md).

| Domain | Python ratio | Python SE | samplics ratio | samplics SE |
|---|---:|---:|---:|---:|
| age65_fair_poor | 0.25426400 | 0.00271549 | 0.25426400 | 0.00271549 |
| diabetes_cost | 0.11168921 | 0.00330790 | 0.11168921 | 0.00330790 |
| no_diabetes_cost | 0.11448607 | 0.00132860 | 0.11448607 | 0.00132860 |

The Python implementation and `samplics` agree to the displayed precision for these examples. An additional comparison passes the standardized-contrast prototype's already-computed influence scores to `samplics` as a weighted total, checking the score-aggregation standard error under the same skip-singleton rule. The two score standard errors are 0.00667754 and 0.00667754 respectively. That checks aggregation only: it does not independently verify the influence-score formula or its statistical assumptions. The installed `samplics` 0.6.1 identifies itself as archived and no longer maintained. This check does not validate its behavior for all domains, the centered-singleton rule, age-standardized estimates, correlated contrasts, annual changes, or confidence-interval coverage. **The main survey analyses remain descriptive point estimates**, and design-based uncertainty for the primary standardized comparisons remains outstanding.

## Reproduce

Run `python samplics_probe.py` after the 2023 extract is created and a compatible `samplics` installation is available. This exploratory check was run with `samplics` 0.6.1 in a local dependency folder. Machine-readable output is in `samplics-probe-results.json`. For formal work, use a supported, independently validated survey package and document its handling of singleton strata and domains.
