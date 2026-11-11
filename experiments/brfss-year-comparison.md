# BRFSS 2023–2024: common-footprint sensitivity check

Run date: 2026-11-01. This is an exploratory comparison of two independent annual telephone survey samples, not a longitudinal study of the same respondents. It uses weighted point estimates only; survey-design confidence intervals and significance tests have not been validated.

## Coverage and measurement

The [CDC 2023 documentation](https://www.cdc.gov/brfss/annual_data/annual_2023.html) says Kentucky and Pennsylvania were absent; the [2024 documentation](https://www.cdc.gov/brfss/annual_data/annual_2024.html) says Tennessee was absent. We exclude all three states in both years, yielding 47 states and DC. Territory records are excluded. This footprint does not represent all U.S. states. The analyses use the `_LLCPWT` weight, diabetes responses of 1 (yes) or 3 (no), definite yes/no answers to `MEDCOST1`, and known age. Borderline and pregnancy-only diabetes responses, missing/unknown responses, and unknown ages are excluded. Counts are unweighted.

The 2023 and 2024 files are checksum-verified [third-party conversions](https://muntasirmasum.github.io/brfssdata/articles/datasets.html), not independently checked row-by-row against CDC's source files. The 2024 file contains 457,670 records and SHA-256 `00c40d2c741bc5594b5a146b433249dd02b30c4963c85a9133f35d91fc70829b`. As an additional check against an independent official source, the 2024 Wisconsin records contain 2,098 diabetes-yes responses among 13,096 respondents; the weighted yes percentage is 11.90%, matching the [Wisconsin 2024 codebook](https://www.dhs.wisconsin.gov/stats/2024-wisconsin-brfss-codebook.pdf). Questions are self-reported, and the diabetes question does not identify type 2 specifically. A cost barrier refers to any needed doctor visit, not necessarily diabetes care.

## Same age reference for both years

We standardize both diabetes groups and both years to the same weighted three-band age distribution of the pooled 2023 common-footprint comparison sample: 18–44 (46.1%), 45–64 (30.3%), and 65+ (23.6%). This reference differs from the 48-state-and-DC reference in the 2023 report, so estimates can differ slightly.

| Year | Respondents | Diabetes group | No diabetes reported | Difference |
|---|---:|---:|---:|---:|
| 2023 | 396,781 | 15.9% | 11.0% | +4.9 percentage points |
| 2024 | 415,350 | 17.2% | 11.8% | +5.4 percentage points |

The difference column is within-year diabetes minus no-diabetes, not an estimated causal effect. Differences across years can reflect sampling, changing population composition within age groups, coverage, nonresponse, and other factors. Without complex-design uncertainty estimates, do not infer a trend or a significant year-to-year change.

## Within-age-group estimates

| Year | Age | Diabetes: n; rate | No diabetes: n; rate |
|---|---|---:|---:|
| 2023 | 18–44 | 4,035; 22.2% | 115,437; 15.6% |
| 2023 | 45–64 | 19,310; 14.9% | 105,143; 10.0% |
| 2023 | 65+ | 32,887; 4.8% | 119,969; 3.1% |
| 2024 | 18–44 | 4,698; 23.9% | 124,728; 16.7% |
| 2024 | 45–64 | 20,976; 16.0% | 106,122; 11.1% |
| 2024 | 65+ | 35,583; 5.7% | 123,243; 3.1% |

The counts are the numbers of eligible survey respondents in each cell; rates are weighted. Common geography and age standardization do not make these samples identical or eliminate confounding.

## Reproduce

Install NumPy, pandas, and DuckDB. Run `python brfss_prepare_mirror.py` then `python brfss_year_comparison.py`. The latter downloads the 2024 Parquet mirror if absent, verifies its pinned hash, and writes `brfss-year-comparison-results.json` and this report. Before publication, verify both years against the original CDC files and codebooks and compute design-based uncertainty with validated survey software.
