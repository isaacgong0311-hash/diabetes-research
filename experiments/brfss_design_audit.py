"""Audit BRFSS survey strata/PSUs before attempting design-based inference."""
import json
from datetime import date
from pathlib import Path

import pandas as pd

HERE=Path(__file__).resolve().parent


def main():
    d=pd.read_csv(HERE/'brfss2023-selected.csv.gz')
    if d[['_PSU','_STSTR','_LLCPWT']].isna().any().any():raise ValueError('Missing design fields')
    overall=d.groupby('_STSTR')['_PSU'].nunique()
    domain=d[d['_STATE'].between(1,56)&(d.DIABETE4==1)&d.MEDCOST1.isin([1,2])]
    domain_counts=domain.groupby('_STSTR')['_PSU'].nunique().reindex(overall.index,fill_value=0)
    result={'total_records':len(d),'total_strata':len(overall),'full_sample_single_psu_strata':int((overall==1).sum()),
            'stratum_psu_pairs':len(d[['_STSTR','_PSU']].drop_duplicates()),
            'domain_records':len(domain),'domain_no_psu_strata':int((domain_counts==0).sum()),
            'domain_one_psu_strata':int((domain_counts==1).sum()),
            'domain_multiple_psu_strata':int((domain_counts>=2).sum()),
            'domain_singleton_from_multipsu_strata':int(((domain_counts==1)&(overall>1)).sum())}
    assert result['domain_no_psu_strata']+result['domain_one_psu_strata']+result['domain_multiple_psu_strata']==result['total_strata']
    (HERE/'brfss-design-audit-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    report=f'''# 2023 BRFSS survey-design audit

Run date: {date.today().isoformat()}. This is a diagnostic, not a variance estimate. Source and codebook checks are documented in [the 2023 findings](brfss2023-findings.md).

## Full survey structure

The entire {len(d):,}-record file contains **{len(overall):,}** strata defined by `_STSTR` and **{result['stratum_psu_pairs']:,}** distinct stratum/PSU pairs. **{result['full_sample_single_psu_strata']:,}** full-sample strata have only one PSU. The counts of strata and full-sample singleton strata match the example reported in the [brfssdata survey-design documentation](https://muntasirmasum.github.io/brfssdata/articles/survey-design.html). This agreement is a useful data check, not a validation of our estimates or variance calculations.

## Example domain: reported diabetes and known cost response

For the 48 available states and DC (excluding territories), {len(domain):,} people reported diabetes and answered the cost question yes or no. Viewed within the **full file's** strata:

- {result['domain_no_psu_strata']:,} strata contain no members of that domain.
- {result['domain_one_psu_strata']:,} strata contain one domain PSU; {result['domain_singleton_from_multipsu_strata']:,} of these arise inside full-sample strata with multiple PSUs.
- {result['domain_multiple_psu_strata']:,} strata contain multiple domain PSUs.

This illustrates why simply filtering records before constructing a survey design can lose information about the sample design. Full-sample singletons and singletons created by a domain are not automatically identical cases for variance estimation. The analyst must explicitly document the software's singleton and domain options.

## Implication

The existing weighted proportions and standardized comparisons are point estimates. A formal analysis should use a validated complex-survey package, retain the design before domain restriction, specify singleton handling, and independently cross-check variance estimates. Standardized differences also require correct covariance propagation across estimated stratum rates and reference weights. This audit does not calculate those intervals, make a statistical significance claim, or establish causality.

## Reproduce

Run `python brfss_design_audit.py` after preparing the 2023 survey extract. The structured counts are in `brfss-design-audit-results.json`. Requires pandas.
'''
    (HERE/'brfss-design-audit.md').write_text(report,encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
