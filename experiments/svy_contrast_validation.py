"""Independent nonlinear-contrast check using the supported svy package.

Needs svy 0.36+, numpy, pandas. This research check is not a clinical tool.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import json
import sys
import gc
from datetime import date
from pathlib import Path

HERE=Path(__file__).resolve().parent
try:
    import svy
except ModuleNotFoundError:
    sys.path.insert(0,str(HERE/'.surveydeps'))
    import svy
import numpy as np
import pandas as pd
import polars as pl


def main():
    d=pd.read_csv(HERE/'brfss2023-selected.csv.gz')
    dom=d['_STATE'].between(1,56)&(d['_LLCPWT']>0)&d.DIABETE4.isin([1,3])&d.MEDCOST1.isin([1,2])&d['_AGEG5YR'].between(1,13)
    age=np.select([d['_AGEG5YR']<=5,d['_AGEG5YR']<=9],[0,1],default=2)
    grp=np.where(d.DIABETE4==1,1,0);event=np.where(d.MEDCOST1==1,1,0)
    cell=np.full(len(d),'outside',dtype='<U8')
    for a in range(3):
        for g in (0,1):
            for e in (0,1):cell[dom&(age==a)&(grp==g)&(event==e)]=f'a{a}g{g}e{e}'
    if len(d[['_STSTR','_PSU']].drop_duplicates())!=len(d):
        raise ValueError('Omitting PSU requires one distinct PSU per record within stratum')
    frame=pd.DataFrame({'stratum':d['_STSTR'],'weight':d['_LLCPWT'],
                        'domain':dom.astype(int),'cell':cell})
    print(f'Building full survey design on {len(frame):,} records...',flush=True)
    # Every stratum/PSU pair identifies exactly one row, so row-level PSUs are equivalent.
    design=svy.Design(stratum='stratum',wgt='weight',singleton=svy.Singleton('center',domains='standard'))
    sample=svy.Sample(pl.from_pandas(frame),design)
    del d,frame,dom,age,grp,event,cell
    gc.collect()
    expected={f'a{a}g{g}e{e}' for a in range(3) for g in (0,1) for e in (0,1)}
    terms=[]
    for a in range(3):
        z={(g,e):svy.estd(f'a{a}g{g}e{e}') for g in (0,1) for e in (0,1)}
        age_share=z[0,0]+z[0,1]+z[1,0]+z[1,1]
        terms.append(age_share*(z[1,1]/(z[1,0]+z[1,1])-z[0,1]/(z[0,0]+z[0,1])))
    expression=terms[0]+terms[1]+terms[2]
    results={}
    for domain_policy in ('standard','apply'):
        if domain_policy=='apply':
            sample=sample.update_design(singleton=svy.Singleton('center',domains='apply'))
        print(f'Estimating 12 cell proportions with domain policy {domain_policy}...',flush=True)
        estimates=sample.estimation.prop('cell',where=(svy.col('domain')==1))
        keys=set(estimates.keys())
        if not expected.issubset(keys) or keys-expected not in (set(),{'outside'}):
            raise ValueError(f'Unexpected contrast keys: {keys}')
        table=estimates.to_polars()
        if 'outside' in keys:
            outside=table.filter(pl.col('cell')=='outside')
            if outside.height!=1 or abs(outside['est'][0])>1e-12:
                raise ValueError('Out-of-domain category has nonzero estimated probability')
        # Nonlinear delta-method contrast uses the full covariance of the 12
        # estimated cells; it does not reuse the prototype's influence scores.
        contrast=estimates.contrast(expression)
        results[domain_policy]=contrast.to_polars().to_dicts()[0]
        print(json.dumps(results[domain_policy],default=str),flush=True)
    prototype=json.loads((HERE/'standardized-contrast-probe-results.json').read_text(encoding='utf-8'))
    print('Prototype:',prototype['contrast'],prototype['se_centered_candidate'],flush=True)
    standard=results['standard']
    if not all(np.isfinite(results[policy][key]) for policy in results for key in ('est','se','lci','uci')):
        raise ValueError('Non-finite survey estimate or uncertainty')
    if not np.isclose(standard['est'],prototype['contrast'],atol=1e-10,rtol=0):
        raise ValueError('Independent point estimates do not agree')
    if not np.isclose(standard['se'],prototype['se_centered_candidate'],atol=1e-10,rtol=0):
        raise ValueError('Independent standard errors do not agree')
    # Persist an export without claiming validation until the results are audited.
    result={'svy_version':svy.__version__,'cell_keys':sorted(keys),'domain_policies':results,
            'prototype_point':prototype['contrast'],'prototype_centered_se':prototype['se_centered_candidate'],
            'warning':'Exploratory validation only; survey domain singleton settings and confidence coverage require review.'}
    (HERE/'svy-contrast-validation-results.json').write_text(json.dumps(result,indent=2,default=str)+'\n',encoding='utf-8')
    a=results['standard']; b=results['apply']
    report=f'''# Independent survey-contrast cross-check

Run date: {date.today().isoformat()}. This is a computational methods check, not causal or clinical evidence.

## Method

The 2023 BRFSS extract includes 433,323 records from all reporting areas. Each record has a unique stratum/PSU pair, so this check treats each record as a PSU while retaining the full-sample strata and weights. It defines the 48-state-plus-DC comparison domain and encodes each eligible record into one of 12 cells: three age groups × two diabetes-response groups × two cost-response groups. Records outside the domain retain their design structure.

Using [svy](https://svylab.com/docs/svy/) version {svy.__version__}, the program estimates the 12 weighted cell proportions and their joint covariance. It then evaluates the pooled-age-standardized difference as a nonlinear expression of those proportions, allowing the package to compute a delta-method standard error without using the prototype's individual influence scores. Both calculations use centered handling of full-sample singleton strata.

## Results and singleton sensitivity

| Calculation | Difference, proportion scale | Standard error | Approximate 95% interval |
|---|---:|---:|---:|
| Python prototype; standard domain rule | {prototype['contrast']:.8f} | {prototype['se_centered_candidate']:.8f} | Not promoted |
| svy; standard domain rule | {a['est']:.8f} | {a['se']:.8f} | {a['lci']:.5f} to {a['uci']:.5f} |
| svy; apply centered rule to domain singletons | {b['est']:.8f} | {b['se']:.8f} | {b['lci']:.5f} to {b['uci']:.5f} |

The point estimate is expressed as a proportion; multiply by 100 for percentage points. The prototype and svy standard-domain calculation differ by {abs(a['est']-prototype['contrast']):.3g} in the point estimate and {abs(a['se']-prototype['se_centered_candidate']):.3g} in the standard error. Agreement checks two computational paths for the same data and chosen design, not all underlying assumptions. The `svy` and `samplics` packages have a shared developer, so they should not be counted as fully independent replications from different research teams.

The standard domain rule treats PSUs outside the domain as zero contributions. The alternative also applies the centered singleton rule to strata with only one domain PSU. Both are stated policy choices; their similarity or difference here does not prove one universally correct. The intervals are package-generated design-based approximations, not causal intervals. Self-report, selection, missingness, confounding, and absent Kentucky and Pennsylvania remain. The separate [synthetic simulation](contrast-simulation.md) found less-than-nominal coverage in one small-sample setting; it does not represent this survey but argues against assuming universal coverage.

## Scope and next steps

This validates the **calculation against a second implementation**, not the scientific validity of comparing these groups or applying results to other years, to type 2 diabetes specifically, or to all U.S. states. The source is a checksum-verified third-party conversion, with codebook checks rather than row-by-row validation. Further review should independently replicate with another survey implementation and test sensitivity to missing income, sparse joint strata, weighting, and annual sampling. The original survey reports continue to present the primary comparisons as descriptive until such review.

## Reproduce

Install `svy`, pandas, NumPy, and Polars, prepare the 2023 extract, and run `python svy_contrast_validation.py`. The 12 cell keys, package version, two policies, and full numerical results are recorded in `svy-contrast-validation-results.json`.
'''
    (HERE/'svy-contrast-validation.md').write_text(report,encoding='utf-8')


if __name__=='__main__':main()
