"""Describe cost barriers among working-age BRFSS respondents reporting diabetes."""
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent


def summarize(df):
    n=len(df)
    if n==0: raise ValueError('Empty stratum')
    w=df['_LLCPWT'].to_numpy()
    return {'n':n,'unweighted_events':int((df.MEDCOST1==1).sum()),
            'weighted_rate':float(np.average(df.MEDCOST1==1,weights=w))}


def pct(x): return f'{100*x:.1f}%'


def main():
    df=pd.read_csv(HERE/'brfss2023-selected.csv.gz')
    meta=json.loads((HERE/'brfss2023-metadata.json').read_text(encoding='utf-8'))
    base=df[df['_STATE'].between(1,56)&(df['_LLCPWT']>0)&(df.DIABETE4==1)&df['_AGEG5YR'].between(1,9)]
    cost=base[base.MEDCOST1.isin([1,2])]
    insurance=cost[cost['_HLTHPL1'].isin([1,2])]
    income=cost[cost['_INCOMG1'].isin(range(1,8))]
    insurance_groups=[('Any insurance',summarize(insurance[insurance['_HLTHPL1']==1])),
                      ('No insurance',summarize(insurance[insurance['_HLTHPL1']==2]))]
    income_groups=[('Below $25,000',summarize(income[income['_INCOMG1'].isin([1,2])])),
                   ('$25,000 to < $50,000',summarize(income[income['_INCOMG1'].isin([3,4])])),
                   ('$50,000 or more',summarize(income[income['_INCOMG1'].isin([5,6,7])]))]
    data={'source':meta,'domain_n':len(base),'cost_known_n':len(cost),'cost_unknown_n':len(base)-len(cost),
          'insurance_known_n':len(insurance),'insurance_unknown_n':len(cost)-len(insurance),
          'income_known_n':len(income),'income_unknown_n':len(cost)-len(income),
          'insurance_groups':dict(insurance_groups),'income_groups':dict(income_groups)}
    (HERE/'brfss2023-access-results.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    def table(rows):
        out=['| Group | Respondents | Reported cost barrier | Weighted proportion |','|---|---:|---:|---:|']
        for label,r in rows:
            out.append(f"| {label} | {r['n']:,} | {r['unweighted_events']:,} | {pct(r['weighted_rate'])} |")
        return '\n'.join(out)
    report=f'''# Cost barriers and access context in 2023 BRFSS

Run date: {date.today().isoformat()}. This descriptive follow-up uses the same 2023 survey extract and weighting as [brfss2023-findings.md](brfss2023-findings.md), restricted to respondents aged 18–64 in 48 participating states and DC who reported a diabetes diagnosis. Kentucky and Pennsylvania are absent from the 2023 public data. It is a different population and outcome from the historical hospital experiments.

The question asks whether the respondent needed a doctor in the previous 12 months but could not afford to see one. It does not say the visit was for diabetes. Counts are unweighted; percentages use `_LLCPWT`. The analysis has no validated design-based confidence intervals and does not establish statistical significance or causal effects.

## Sample and missing responses

The working-age diabetes domain contains {len(base):,} respondents; {len(cost):,} gave a definite yes/no answer to the cost question, and {len(base)-len(cost):,} did not. Of those with a definite cost answer, {len(cost)-len(insurance):,} had unknown/refused/missing insurance status and {len(cost)-len(income):,} had unknown/refused/missing income category. The two tables therefore use different denominators. Excluding nonresponses may introduce bias.

## Insurance coverage

{table(insurance_groups)}

Coverage is the survey's calculated indicator of any insurance, not a measure of benefit quality, continuity of coverage, deductibles, or affordability. Insurance status and cost barriers are contemporaneous self-reports. The association is not an estimate of what would happen if a person gained or lost coverage.

## Household income

{table(income_groups)}

Income is annual household income in broad survey categories; it is not adjusted for household size, regional costs, or inflation. Income has substantial nonresponse. These rates are descriptive and are not adjusted for age within 18–64, health status, insurance, household composition, or other determinants.

## Provenance and reproducibility

The source is a checksum-verified [third-party conversion of CDC BRFSS data](https://muntasirmasum.github.io/brfssdata/articles/datasets.html), not a row-by-row verified copy of the original XPT. CDC's [2023 codebook](https://topofire.dbs.umt.edu/public_data/federal_public_datasets/CDC%20Behavioral%20Risk%20Factor%20Surveillance%20System%20/2023%20Annual%20Survey%20Data/Survey%20Data%20Information/USCODE23_LLCP_091024.HTML) defines `_HLTHPL1` and `_INCOMG1`; 9/unknown categories are excluded from their respective tables. Archive SHA-256: `{meta['mirror_sha256']}`. Run `python brfss_access_context.py` after preparing the extract; see `brfss2023-access-results.json` for numerical outputs. Before drawing population inferences, obtain design-based uncertainty with validated survey software.
'''
    (HERE/'brfss2023-access-context.md').write_text(report,encoding='utf-8')
    print('Working-age diabetes respondents:',len(base),'cost-known:',len(cost))
    for label,r in insurance_groups+income_groups: print(label,r['n'],pct(r['weighted_rate']))


if __name__=='__main__':main()
