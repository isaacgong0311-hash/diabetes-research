# Weighted donor-draw sensitivity experiment

Run date: 2026-11-01. This is exploratory research under a strong donor-exchangeability assumption. It is not a validated multiple-imputation analysis, a confidence interval, or a causal result.

## Setup

The known-age 2023 comparison domain contains 402,094 respondents in 48 states and DC, of whom 85,827 have unknown income and/or insurance. To give those missing fields hypothetical values, we select donors with both fields observed who match the recipient's broad age band, diabetes response, and known cost-barrier outcome. If just one covariate is missing, the donor also matches the other, observed covariate. If both are missing, the pair comes from the same donor. Donors are sampled with replacement with probability proportional to their survey weight within each pool; recipient survey weights remain unchanged. Recorded answers are never overwritten.

These matching variables are a very limited model. Drawing from observed respondents assumes the donor distribution is informative for missing respondents within each pool. That assumption cannot be verified from these data and may fail even when observed cost rates are similar. This is a simple sensitivity experiment inspired by [Census hot-deck methods](https://www.census.gov/programs-surveys/cps/technical-documentation/methodology/imputation-of-unreported-data-items.html), not the Census procedure or a CDC method. A [survey methods review](https://pmc.ncbi.nlm.nih.gov/articles/3130338/) discusses the separate problem of valid variance estimation after hot-deck imputation.

## Results across 200 donor draws

The table shows the diabetes-minus-no-diabetes cost-barrier gap, standardized by age, income, and insurance. The fixed standard is the pooled complete-case distribution; the varying standard is recalculated after every donor draw. The displayed spread is **between these donor draws only** and does not include sampling variance or uncertainty about how the donor distributions were estimated. It is not a 95% confidence interval.

| Reference distribution | Mean gap, percentage points | SD across draws, points | Minimum to maximum across draws, points |
|---|---:|---:|---:|
| Fixed complete-case distribution | +3.33 | 0.08 | +3.13 to +3.60 |
| Recomputed in each draw | +3.38 | 0.09 | +3.17 to +3.66 |

There are 72 nonempty donor pools, of which 0 have fewer than 30 donors. The smallest pool has 44 donors and the lowest weight-only effective size is 15.3; these minima may occur in different pools. Weight-only effective size is a weight-concentration diagnostic, not survey degrees of freedom. The smallest unweighted group/cell size over all completed datasets was 25. Pool-level counts and draw summaries are saved in the JSON; no imputed individual records are exported.

The earlier [fixed-assignment stress scenarios](missing-covariate-scenarios.md) explore much stronger, homogeneous assumptions and are neither bounds nor a model. This donor experiment uses different assumptions; agreement or disagreement does not identify the true missing answers. Income and insurance may depend on unmeasured factors or on missingness itself, donor pools can be sparse, and outcome, age and insurance are self-reported. Unknown age cases remain excluded. Valid inference would require an appropriate imputation model, assessment of its assumptions, survey-design variance, and an approach that accounts for imputation-model uncertainty.

Further checks include [masking known answers](hotdeck-masking-validation.md), an observed [general-health balance audit](hotdeck-balance-audit.md), an alternative [health-matched donor rule](hotdeck-health-sensitivity.md), and [repeated holdout splits](hotdeck-repeated-masking.md). None establish how the method performs on the truly missing answers.

## Reproduce

Run `python missingness_standardized_probe.py`, then `python hotdeck_sensitivity.py` with NumPy and pandas installed. The seed is 725199; output summaries are in `hotdeck-sensitivity-results.json`.
