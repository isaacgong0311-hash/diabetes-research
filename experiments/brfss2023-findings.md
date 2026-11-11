# 2023 BRFSS: diabetes and access to care

Run date: 2026-11-01. This is a descriptive, survey-weighted analysis of an independently collected population survey, not a continuation of the historical hospital readmission cohort.

## Data and verification

The [CDC 2023 BRFSS documentation](https://www.cdc.gov/brfss/annual_data/annual_2023.html) describes a telephone survey of noninstitutionalized adults. The CDC download returned HTTP 403 in this environment, so we used a [documented third-party Parquet conversion](https://muntasirmasum.github.io/brfssdata/articles/datasets.html) of the CDC data. Its published SHA-256 was checked: `128ef26a1c0a84e271e1e35e6584f3c7bfd7690c8cd7ba602313c0d738021ffe`. The file has 433,323 rows. We did not independently compare every record with the original CDC file.

As a basic source and coding check, the full file contains 59,786 responses coded “yes” to having been told of diabetes, and those responses account for 12.0% of the full weighted denominator. Both agree with the [2023 codebook](https://topofire.dbs.umt.edu/public_data/federal_public_datasets/CDC%20Behavioral%20Risk%20Factor%20Surveillance%20System%20/2023%20Annual%20Survey%20Data/Survey%20Data%20Information/USCODE23_LLCP_091024.HTML) at displayed precision. This benchmark includes territories and all response categories in the denominator; the analyses below exclude territories and unknown responses as described. The 2023 public file excludes Kentucky and Pennsylvania; these point estimates cover 48 states and DC, not the entire United States.

The following figures use `_LLCPWT` survey weights; respondent counts are unweighted. They are exploratory point estimates only. Although PSU and strata variables were retained, complex-design standard errors have **not** been validated or calculated here, so comparisons have no confidence intervals and should not be presented as statistically established differences.

## Self-reported diagnosis

Among 424,140 respondents in the 48 available states and DC with a definite diabetes response (yes, no, pregnancy only, or borderline), the weighted proportion reporting a diabetes diagnosis other than pregnancy-only was **12.0%**; the unweighted proportion was 13.7%. This is self-reported diagnosed diabetes of any type, not laboratory-defined total diabetes and not type 2 alone. People unaware of diabetes are not identified as having it by this question.

## Affordability of a doctor visit

Among people answering the cost question, 11.2% of those reporting diabetes (unweighted n=58,047) and 11.4% of those answering “no diabetes” (n=351,259) reported a time in the past 12 months when they needed to see a doctor but could not afford it. These groups are not age-matched. The comparison excludes pregnancy-only and borderline responses; 1,379 records in the two comparison groups lacked a definite yes/no cost response and were excluded from this outcome.

| Age group | Diabetes: respondents; weighted cost barrier | No diabetes reported: respondents; weighted cost barrier |
|---|---:|---:|
| 18–44 | 4,115; 22.2% | 117,100; 15.7% |
| 45–64 | 19,663; 15.1% | 106,584; 10.1% |
| 65+ | 33,383; 4.8% | 121,249; 3.1% |

After standardizing each group's age-specific cost-barrier percentages to the weighted age distribution of the pooled comparison respondents with known age, the values were **15.9%** and **11.0%**, respectively. This direct age standardization includes 402,094 respondents. It is an exploratory descriptive comparison, not causal adjustment: income, coverage, health status, and many other factors remain unaccounted for.

As sensitivity checks, using all 13 available age categories and the pooled age distribution gives 16.4% versus 11.0%; using the age distribution of respondents reporting diabetes as the common standard, with the three broad age groups, gives 11.2% versus 7.6%. The reference population changes the question being summarized, so these estimates need not match. They remain unadjusted for other factors and lack validated design-based intervals.

## Other self-reported measures among people reporting diabetes

- **43.4%** rated their general health fair or poor (n=58,032 with a definite answer).
- **93.8%** reported a routine checkup within the past year (n=57,742 with a definite answer, including “never” in the denominator).

These answers are self-reported and are not measures of whether diabetes care met clinical guidelines.

## Limitations and next work

- This is a telephone survey of noninstitutionalized adults and excludes people who cannot be reached or do not respond. Weighting reduces, but cannot eliminate, nonresponse and coverage bias.
- Self-report can misclassify diagnosis, cost barriers, and healthcare utilization. A cost barrier concerns any doctor visit, not necessarily diabetes care.
- All analyses are cross-sectional and cannot determine whether diabetes causes cost barriers or poor health, nor whether barriers precede outcomes.
- Age standardization uses three broad groups, and unknown age is excluded. Missingness and remaining confounding can alter comparisons.
- Survey-weighted point estimates alone do not characterize uncertainty. Before publication or policy use, recompute with validated complex-survey software using `_STSTR`, `_PSU`, and `_LLCPWT`, and cross-check definitions and domains against current CDC guidance.
- The 2023 data are a different population, era, and outcome from the 1999–2008 hospital readmission data. The two analyses do not independently replicate each other.

## Reproduce

Install pandas, NumPy, and DuckDB. Run `python brfss_prepare_mirror.py` then `python brfss_analysis.py` in this folder. The preparation script verifies the mirror checksum and writes a reduced CSV and provenance metadata. `brfss2023-results.json` contains counts and values. A separate `brfss_prepare.py` attempts to download the original CDC archive and failed with HTTP 403 in this environment; it is retained for another environment where access succeeds.
