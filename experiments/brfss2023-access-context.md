# Cost barriers and access context in 2023 BRFSS

Run date: 2026-11-01. This descriptive follow-up uses the same 2023 survey extract and weighting as [brfss2023-findings.md](brfss2023-findings.md), restricted to respondents aged 18–64 in 48 participating states and DC who reported a diabetes diagnosis. Kentucky and Pennsylvania are absent from the 2023 public data. It is a different population and outcome from the historical hospital experiments.

The question asks whether the respondent needed a doctor in the previous 12 months but could not afford to see one. It does not say the visit was for diabetes. Counts are unweighted; percentages use `_LLCPWT`. The analysis has no validated design-based confidence intervals and does not establish statistical significance or causal effects.

## Sample and missing responses

The working-age diabetes domain contains 23,857 respondents; 23,778 gave a definite yes/no answer to the cost question, and 79 did not. Of those with a definite cost answer, 843 had unknown/refused/missing insurance status and 3,651 had unknown/refused/missing income category. The two tables therefore use different denominators. Excluding nonresponses may introduce bias.

## Insurance coverage

| Group | Respondents | Reported cost barrier | Weighted proportion |
|---|---:|---:|---:|
| Any insurance | 21,555 | 2,448 | 13.1% |
| No insurance | 1,380 | 728 | 56.3% |

Coverage is the survey's calculated indicator of any insurance, not a measure of benefit quality, continuity of coverage, deductibles, or affordability. Insurance status and cost barriers are contemporaneous self-reports. The association is not an estimate of what would happen if a person gained or lost coverage.

## Household income

| Group | Respondents | Reported cost barrier | Weighted proportion |
|---|---:|---:|---:|
| Below $25,000 | 4,872 | 1,046 | 27.1% |
| $25,000 to < $50,000 | 5,047 | 985 | 21.8% |
| $50,000 or more | 10,208 | 757 | 8.8% |

Income is annual household income in broad survey categories; it is not adjusted for household size, regional costs, or inflation. Income has substantial nonresponse. These rates are descriptive and are not adjusted for age within 18–64, health status, insurance, household composition, or other determinants.

## Provenance and reproducibility

The source is a checksum-verified [third-party conversion of CDC BRFSS data](https://muntasirmasum.github.io/brfssdata/articles/datasets.html), not a row-by-row verified copy of the original XPT. CDC's [2023 codebook](https://topofire.dbs.umt.edu/public_data/federal_public_datasets/CDC%20Behavioral%20Risk%20Factor%20Surveillance%20System%20/2023%20Annual%20Survey%20Data/Survey%20Data%20Information/USCODE23_LLCP_091024.HTML) defines `_HLTHPL1` and `_INCOMG1`; 9/unknown categories are excluded from their respective tables. Archive SHA-256: `128ef26a1c0a84e271e1e35e6584f3c7bfd7690c8cd7ba602313c0d738021ffe`. Run `python brfss_access_context.py` after preparing the extract; see `brfss2023-access-results.json` for numerical outputs. Before drawing population inferences, obtain design-based uncertainty with validated survey software.
