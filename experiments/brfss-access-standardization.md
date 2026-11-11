# Cost-barrier standardization sensitivity: 2023 BRFSS

Run date: 2026-11-01. This is an exploratory, cross-sectional description using survey weights, not causal analysis. A separate [uncertainty probe](access-uncertainty-probe.md) examines design-based standard errors and sparse cells. The source, 48-state-plus-DC footprint, coding, and limitations are documented in [brfss2023-findings.md](brfss2023-findings.md).

## Question and cohort

How do cost-barrier comparisons change when we standardize to common distributions of age, reported household income, and insurance status? The cost question concerns any needed doctor visit during the preceding year, not necessarily diabetes care. Both diabetes and access are self-reported; diabetes type is not determined.

Among 409,306 respondents with definite diabetes and cost answers, 316,267 had known age, income, and insurance and were retained for **all** rows below; 93,039 were excluded because at least one was unknown. Income nonresponse is substantial and may be nonrandom, so this complete-case population may differ from the broader comparison sample. Group counts are 44,808 reporting diabetes and 271,459 reporting no diabetes. The results cannot be interpreted as applying automatically to people with missing income or insurance data.

## Comparison using the same complete-case sample

| Comparison | Diabetes | No diabetes reported | Difference | Smallest group/cell n |
|---|---:|---:|---:|---:|
| Unstandardized complete cases | 11.4% | 11.6% | -0.1 pp | — |
| Standardized: Age | 16.0% | 11.1% | +4.9 pp | 3,361 |
| Standardized: Age + income | 14.1% | 11.4% | +2.7 pp | 736 |
| Standardized: Age + income + insurance | 14.8% | 11.3% | +3.5 pp | 23 |

The standard population for each row is the pooled weighted distribution of complete cases in the specified strata. Age is grouped 18–44, 45–64, and 65+; income is household income below $25,000, $25,000–<$50,000, or $50,000 and above; insurance is any versus none. The final specification has 18 joint strata. The smallest unweighted diabetes-status group in a cell is shown to help assess overlap; cell-level rates and weights are in the JSON file.

Changing the factors or the standard population changes the descriptive question. Income and insurance are not necessarily independent confounders: they can be connected to illness, employment, age, and healthcare needs. Standardization here does not identify whether diabetes itself causes the difference and must not be interpreted as the effect of changing coverage or income. Residual confounding, missingness, self-report, survey selection, and broad categories remain.

## Interpretation and next work

These are point estimates without fully validated confidence intervals. The [uncertainty and sparse-cell probe](access-uncertainty-probe.md) retains the full design and documents exploratory intervals; a [nonlinear package check](access-svy-nonlinear-validation.md) reproduces their computation, and a [resampling diagnostic](access-bootstrap-probe.md) examines stability. These checks do not resolve nonresponse or validate interval coverage. Further work should investigate sparse cells and missingness and replicate with a separately developed survey implementation.

## Reproduce

Run `python brfss_access_standardization.py` after preparing the 2023 extract. The code writes `brfss-access-standardization-results.json` including all strata. Requires pandas and NumPy. The source is a checksum-verified third-party conversion; see the main survey report for provenance and codebook cross-checks.
