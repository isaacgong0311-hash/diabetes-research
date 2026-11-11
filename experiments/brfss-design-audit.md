# 2023 BRFSS survey-design audit

Run date: 2026-11-01. This is a diagnostic, not a variance estimate. Source and codebook checks are documented in [the 2023 findings](brfss2023-findings.md).

## Full survey structure

The entire 433,323-record file contains **2,146** strata defined by `_STSTR` and **433,323** distinct stratum/PSU pairs. **101** full-sample strata have only one PSU. The counts of strata and full-sample singleton strata match the example reported in the [brfssdata survey-design documentation](https://muntasirmasum.github.io/brfssdata/articles/survey-design.html). This agreement is a useful data check, not a validation of our estimates or variance calculations.

## Example domain: reported diabetes and known cost response

For the 48 available states and DC (excluding territories), 58,047 people reported diabetes and answered the cost question yes or no. Viewed within the **full file's** strata:

- 263 strata contain no members of that domain.
- 188 strata contain one domain PSU; 174 of these arise inside full-sample strata with multiple PSUs.
- 1,695 strata contain multiple domain PSUs.

This illustrates why simply filtering records before constructing a survey design can lose information about the sample design. Full-sample singletons and singletons created by a domain are not automatically identical cases for variance estimation. The analyst must explicitly document the software's singleton and domain options.

## Implication

The existing weighted proportions and standardized comparisons are point estimates. A formal analysis should use a validated complex-survey package, retain the design before domain restriction, specify singleton handling, and independently cross-check variance estimates. Standardized differences also require correct covariance propagation across estimated stratum rates and reference weights. This audit does not calculate those intervals, make a statistical significance claim, or establish causality.

## Reproduce

Run `python brfss_design_audit.py` after preparing the 2023 survey extract. The structured counts are in `brfss-design-audit-results.json`. Requires pandas.
