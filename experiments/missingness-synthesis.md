# Missing-data experiments: synthesis

Updated: 2026-11-01. These are exploratory analyses of 2023 BRFSS responses from 48 states and DC, not clinical advice, causal estimates, or nationally complete results. The diabetes question does not identify diabetes type. See the broader [research synthesis](research-synthesis.md) for the data and provenance.

## Question and denominator

Among 402,094 respondents with known age and definite diabetes and cost-barrier responses, 85,827 lack income, insurance, or both. The detailed standardization cannot directly use their unknown categories. In the original analysis, people with unknown age are also excluded.

## What the experiments found

1. **Strong fixed assignments:** Across 36 homogeneous hypothetical assignments, the diabetes-minus-no-diabetes cost-barrier gap ranges from +1.38 to +5.98 percentage points with the complete-case reference population held fixed. These assignments are not exhaustive, statistical bounds, or claims about the missing values. [Scenario details](missing-covariate-scenarios.md).
2. **Weighted donor draws:** Selecting respondents with matching age band, diabetes response, cost response, and any observed covariate produced an average fixed-reference gap of +3.33 percentage points across 200 draws. The draw-to-draw SD was 0.08 points; it is **not** a confidence interval and excludes survey sampling and donor-model uncertainty. [Donor experiment](hotdeck-sensitivity.md).
3. **Observed mismatch:** Among recipients with known general health, 20.7% reported fair or poor health, versus 18.6% in their eligible donor pools after matching the recipient pool mix. The descriptive difference does not determine how missing income or insurance differs. [Balance audit](hotdeck-balance-audit.md).
4. **Alternative matching:** Adding general health to donor matching gave an average gap of +3.28 points in a separate 200-draw run, compared with +3.33 points without health matching. Some pools became very small; the minimum donor count was 1. [Alternative matching](hotdeck-health-sensitivity.md).
5. **Artificial holdouts:** Across 8 random splits of respondents whose answers were known, mean weighted income-band accuracy was 48.5% with the original donor rule and 49.8% with health matching. These are random donor draws, not optimized individual predictions. The respondents' outcomes, age, and diabetes response were known to the matcher. [Repeated masking](hotdeck-repeated-masking.md).

The donor method assumes that observed donors are informative about missing respondents within the chosen matching cells. Randomly hiding answers among complete respondents cannot verify that assumption for people who did not answer; health imbalance and small donor pools make independent scrutiny especially important. None of the experiments estimates a treatment effect, fixes missing-data bias, or supplies valid survey confidence intervals after imputation. Unmeasured factors, self-report, survey nonresponse, and absent states remain relevant.

## Reproduce

Run the main `python run_pipeline.py`, then `python run_missingness_pipeline.py`, then `python summarize_missingness_research.py`. The supplemental pipeline records input, script, and output hashes; this synthesis verifies its source results against that completed run and records its own input hashes in `missingness-synthesis-provenance.json`.
