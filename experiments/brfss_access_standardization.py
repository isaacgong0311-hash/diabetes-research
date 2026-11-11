"""Compare cost-barrier estimates under different descriptive standardizations."""
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent


def standardized(df, columns):
    rates=[]; weights=[]; cells=[]
    for key,sub in df.groupby(columns,observed=True,sort=True):
        if not isinstance(key,tuple):key=(key,)
        rec={'cell':list(key),'population_weight':float(sub['_LLCPWT'].sum()),'groups':{}}
        for code,name in [(1,'diabetes'),(3,'no_diabetes')]:
            group=sub[sub.DIABETE4==code]
            if group.empty:raise ValueError(f'No {name} observations in stratum {key}')
            rate=float(np.average(group.MEDCOST1==1,weights=group['_LLCPWT']))
            rec['groups'][name]={'n':len(group),'weighted_rate':rate}
        cells.append(rec);weights.append(rec['population_weight'])
        rates.append([rec['groups']['diabetes']['weighted_rate'],rec['groups']['no_diabetes']['weighted_rate']])
    weights=np.asarray(weights); weights/=weights.sum()
    return {'standardized_rates':(weights@np.asarray(rates)).tolist(), 'cells':cells,
            'smallest_group_n':min(g['n'] for c in cells for g in c['groups'].values())}


def main():
    d=pd.read_csv(HERE/'brfss2023-selected.csv.gz')
    base=d[d['_STATE'].between(1,56)&(d['_LLCPWT']>0)&d.DIABETE4.isin([1,3])&d.MEDCOST1.isin([1,2])].copy()
    complete=base[base['_AGEG5YR'].between(1,13)&base['_INCOMG1'].between(1,7)&base['_HLTHPL1'].isin([1,2])].copy()
    complete['age_band']=np.select([complete['_AGEG5YR']<=5,complete['_AGEG5YR']<=9],['18–44','45–64'],default='65+')
    complete['income_band']=np.select([complete['_INCOMG1']<=2,complete['_INCOMG1']<=4],['below 25k','25k–<50k'],default='50k+')
    raw={}
    for code,name in [(1,'diabetes'),(3,'no_diabetes')]:
        g=complete[complete.DIABETE4==code]
        raw[name]={'n':len(g),'rate':float(np.average(g.MEDCOST1==1,weights=g['_LLCPWT']))}
    estimates={'age_only':standardized(complete,['age_band']),
               'age_income':standardized(complete,['age_band','income_band']),
               'age_income_insurance':standardized(complete,['age_band','income_band','_HLTHPL1'])}
    result={'base_n':len(base),'complete_n':len(complete),'excluded_n':len(base)-len(complete),'raw':raw,'estimates':estimates}
    (HERE/'brfss-access-standardization-results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    fmt=lambda n:f'{100*n:.1f}%'
    rows=['| Comparison | Diabetes | No diabetes reported | Difference | Smallest group/cell n |','|---|---:|---:|---:|---:|']
    rows.append(f"| Unstandardized complete cases | {fmt(raw['diabetes']['rate'])} | {fmt(raw['no_diabetes']['rate'])} | {100*(raw['diabetes']['rate']-raw['no_diabetes']['rate']):+.1f} pp | — |")
    for key,label in [('age_only','Age'),('age_income','Age + income'),('age_income_insurance','Age + income + insurance')]:
        r=estimates[key];a,b=r['standardized_rates']
        rows.append(f"| Standardized: {label} | {fmt(a)} | {fmt(b)} | {100*(a-b):+.1f} pp | {r['smallest_group_n']:,} |")
    report=f'''# Cost-barrier standardization sensitivity: 2023 BRFSS

Run date: {date.today().isoformat()}. This is an exploratory, cross-sectional description using survey weights, not causal analysis. A separate [uncertainty probe](access-uncertainty-probe.md) examines design-based standard errors and sparse cells. The source, 48-state-plus-DC footprint, coding, and limitations are documented in [brfss2023-findings.md](brfss2023-findings.md).

## Question and cohort

How do cost-barrier comparisons change when we standardize to common distributions of age, reported household income, and insurance status? The cost question concerns any needed doctor visit during the preceding year, not necessarily diabetes care. Both diabetes and access are self-reported; diabetes type is not determined.

Among {len(base):,} respondents with definite diabetes and cost answers, {len(complete):,} had known age, income, and insurance and were retained for **all** rows below; {len(base)-len(complete):,} were excluded because at least one was unknown. Income nonresponse is substantial and may be nonrandom, so this complete-case population may differ from the broader comparison sample. Group counts are {raw['diabetes']['n']:,} reporting diabetes and {raw['no_diabetes']['n']:,} reporting no diabetes. The results cannot be interpreted as applying automatically to people with missing income or insurance data.

## Comparison using the same complete-case sample

{chr(10).join(rows)}

The standard population for each row is the pooled weighted distribution of complete cases in the specified strata. Age is grouped 18–44, 45–64, and 65+; income is household income below $25,000, $25,000–<$50,000, or $50,000 and above; insurance is any versus none. The final specification has 18 joint strata. The smallest unweighted diabetes-status group in a cell is shown to help assess overlap; cell-level rates and weights are in the JSON file.

Changing the factors or the standard population changes the descriptive question. Income and insurance are not necessarily independent confounders: they can be connected to illness, employment, age, and healthcare needs. Standardization here does not identify whether diabetes itself causes the difference and must not be interpreted as the effect of changing coverage or income. Residual confounding, missingness, self-report, survey selection, and broad categories remain.

## Interpretation and next work

These are point estimates without fully validated confidence intervals. The [uncertainty and sparse-cell probe](access-uncertainty-probe.md) retains the full design and documents exploratory intervals; a [nonlinear package check](access-svy-nonlinear-validation.md) reproduces their computation, and a [resampling diagnostic](access-bootstrap-probe.md) examines stability. These checks do not resolve nonresponse or validate interval coverage. Further work should investigate sparse cells and missingness and replicate with a separately developed survey implementation.

## Reproduce

Run `python brfss_access_standardization.py` after preparing the 2023 extract. The code writes `brfss-access-standardization-results.json` including all strata. Requires pandas and NumPy. The source is a checksum-verified third-party conversion; see the main survey report for provenance and codebook cross-checks.
'''
    (HERE/'brfss-access-standardization.md').write_text(report,encoding='utf-8')
    print('\n'.join(rows))


if __name__=='__main__':main()
