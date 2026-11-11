# 2023–2025 BRFSS: three-year common-footprint check

Run date: 2026-11-01. This is a descriptive sensitivity check using annual cross-sectional samples and survey-weighted point estimates. It is not a longitudinal study, and design-based confidence intervals and trend tests have not been calculated.

## Harmonized geography and sample

The [CDC 2023 release](https://www.cdc.gov/brfss/annual_data/annual_2023.html) excludes Kentucky and Pennsylvania, the [2024 release](https://www.cdc.gov/brfss/annual_data/annual_2024.html) excludes Tennessee, and the [2025 release](https://www.cdc.gov/brfss/annual_data/annual_2025.html) excludes California, Mississippi and Nevada. All three analyses therefore exclude these six states and territories. The resulting **44 states plus DC do not represent the entire United States**, especially because California is absent.

For each year, we keep definite yes/no responses to the diabetes and doctor-visit affordability questions and known age, using the same definitions as [the 2023–2024 check](brfss-year-comparison.md). The question asks whether respondents needed a doctor in the preceding 12 months but could not afford to see one; the reason for the visit is unknown. Counts are unweighted and percentages use `_LLCPWT`.

Both comparison groups in each year are standardized to the same weighted age distribution from the 2023 common-footprint sample: 18–44 45.8%, 45–64 30.4%, and 65+ 23.9%.

| Year | Respondents | Reports diabetes | Reports no diabetes | Difference |
|---|---:|---:|---:|---:|
| 2023 | 379,334 | 15.8% | 11.0% | +4.8 pp |
| 2024 | 402,275 | 18.0% | 11.8% | +6.1 pp |
| 2025 | 314,576 | 18.2% | 12.2% | +6.0 pp |

The difference is within-year diabetes minus no-diabetes in percentage points. Changes across years are descriptive; the samples differ, six states are excluded, and uncertainty has not been quantified. The results cannot establish a causal effect of diabetes, age, insurance, income, or an intervention.

## Source and validation

The 2025 file has 356,158 rows, consistent with the CDC's listed file size. Its [third-party conversion](https://muntasirmasum.github.io/brfssdata/articles/datasets.html) was checked against published SHA-256 `6cd8bd7137b69d15f3d08d8739a14f820df0af71d7d2b0eddeefa1eb50d754d7`. Across all 2025 records, 51,827 reported diabetes (12.51% weighted) and 34,602 reported a cost barrier (12.69% weighted), matching the [CDC 2025 codebook](https://www.cdc.gov/brfss/annual_data/2025/zip/codebook25_llcp-v2-508.zip) at its displayed precision. These benchmark percentages include territories and all response categories; they differ from the comparison denominators above. The 2023 and 2024 conversions and checks are documented in the prior reports. We have not compared every row to the original CDC files; annual questionnaire and coding changes, nonresponse and selection still require review before formal time-trend analysis.

## Reproduce

Run `python brfss_3year_check.py` after creating the 2023 extract with `brfss_prepare_mirror.py`. The script uses the cached 2024 mirror and downloads the 2025 mirror if absent; it validates the 2025 checksum and writes `brfss-3year-results.json`. Requires NumPy, pandas, and DuckDB.
