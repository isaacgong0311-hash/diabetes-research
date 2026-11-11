# Survey variance probe: external benchmark

Run date: 2026-11-01. This is an implementation experiment, not a validated analysis for publication.

## Benchmark

The [brfssdata survey-design vignette](https://muntasirmasum.github.io/brfssdata/articles/survey-design.html) reports a weighted fair/poor health proportion of approximately 0.254 (95% interval 0.249–0.260) for 2023 respondents aged 65 and older (`_AGE_G` = 6) in all participating reporting areas. It constructs a survey design in R and uses singleton adjustments. The published figures are rounded to three decimals. The age code here deliberately matches that benchmark; `_AGEG5YR` is a different calculated variable and gives a different sample count.

The exploratory Python calculation on the checksum-verified converted source gives a ratio estimate of **0.254264**, standard error **0.002716**, and approximate normal interval **0.248940–0.259588**. It has 2,146 full-sample strata, including 101 singleton strata. Agreement within the selected 0.0015 tolerance for each rounded reference value: **True**.

## Method and limits

The exploratory code represents the domain ratio as weighted numerator and denominator over the full sample, linearizes the ratio, sums scores within PSU, computes with-replacement within-stratum variance, and centers full-sample singleton PSU scores at zero. It uses a normal critical value. The reference uses a survey package's own domain and singleton handling; the reference gives only rounded values, and its exact configuration or interval method may differ. Matching one example within rounding is a **sanity check**, not independent validation for all domains, contrasts, standardization, sparse cells, or annual differences.

Before reporting uncertainty for the diabetes comparisons, compare against an established complex-survey implementation on identical data, explicitly verify domain and singleton behavior, and correctly propagate covariance for standardized contrasts. Continue treating the main diabetes figures as point estimates until that check is complete.

## Reproduce

Run `python survey_variance_probe.py` after preparing the 2023 extract. The result is also stored in `survey-variance-probe-results.json`. Requires NumPy and pandas.
