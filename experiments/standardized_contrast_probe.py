"""Experimental linearization of a data-standardized two-group contrast.

Research diagnostic only; do not treat as validated survey inference.
"""
from datetime import date
from pathlib import Path
import json

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent


def contrast_and_scores(weight, category, group, outcome):
    """Return pooled-standardized difference and derivative for each record.

    group 1 and 0 are comparison groups; group -1 denotes an out-of-domain record.
    The weights defining the standard population are estimated from the same sample.
    Returned scores are derivatives w.r.t. multiplicative weight perturbations.
    """
    weight=np.asarray(weight,dtype=float);category=np.asarray(category);group=np.asarray(group);outcome=np.asarray(outcome,dtype=float)
    domain=group>=0
    total=float(weight[domain].sum())
    if total<=0:raise ValueError('Empty domain')
    categories=np.unique(category[domain])
    components=[]
    for c in categories:
        cell=domain&(category==c); cell_weight=float(weight[cell].sum())
        group_info=[]
        for g in (1,0):
            mask=cell&(group==g); w=float(weight[mask].sum())
            if w<=0:raise ValueError('A stratum has no positive-weight observations in a group')
            mu=float(np.dot(weight[mask],outcome[mask])/w)
            group_info.append((mask,w,mu))
        components.append((cell,cell_weight,*group_info))
    difference=sum(w/total*(one[2]-zero[2]) for _,w,one,zero in components)
    scores=np.zeros(len(weight),dtype=float)
    for cell,w,one,zero in components:
        scores[cell]+=weight[cell]/total*((one[2]-zero[2])-difference)
        for sign,(mask,group_weight,mu) in [(1,one),(-1,zero)]:
            scores[mask]+=sign*w/total*weight[mask]*(outcome[mask]-mu)/group_weight
    return float(difference),scores


def design_variance(strata,psu,scores,singleton='center'):
    """With-replacement stratum/PSU variance of supplied linearized scores."""
    psu_scores=pd.DataFrame({'stratum':strata,'psu':psu,'score':scores}).groupby(['stratum','psu'],sort=False)['score'].sum()
    grouped=psu_scores.groupby(level=0).agg(['count','sum',lambda v:float(np.dot(v,v))])
    grouped.columns=['n','total','square']
    multi=grouped[grouped.n>1]; single=grouped[grouped.n==1]
    if singleton not in ('center','skip'):raise ValueError('Unknown singleton policy')
    v=float((multi.n/(multi.n-1)*(multi.square-multi.total**2/multi.n)).sum())
    if singleton=='center':v+=float(single.square.sum())
    return v


def main():
    d=pd.read_csv(HERE/'brfss2023-selected.csv.gz')
    domain=d['_STATE'].between(1,56)&(d['_LLCPWT']>0)&d.DIABETE4.isin([1,3])&d.MEDCOST1.isin([1,2])&d['_AGEG5YR'].between(1,13)
    group=np.where(domain,np.where(d.DIABETE4==1,1,0),-1)
    category=np.select([d['_AGEG5YR']<=5,d['_AGEG5YR']<=9],[0,1],default=2)
    outcome=(d.MEDCOST1==1).to_numpy(dtype=float)
    weights=d['_LLCPWT'].to_numpy()
    delta,scores=contrast_and_scores(weights,category,group,outcome)
    centered=design_variance(d['_STSTR'],d['_PSU'],scores,'center')**.5
    skipped=design_variance(d['_STSTR'],d['_PSU'],scores,'skip')**.5
    # Validate selected individual derivatives by perturbing their survey weights.
    selected=[]
    for age_code in range(3):
        for group_code in (0,1):
            for outcome_code in (0,1):
                candidates=np.flatnonzero((category==age_code)&(group==group_code)&(outcome==outcome_code))
                if len(candidates)<3:raise ValueError('Too few records to exercise all derivative cases')
                selected.extend(candidates[[0,len(candidates)//2,-1]])
    selected.extend(np.flatnonzero(group<0)[:2])
    checks=[]; step=1e-4
    for i in selected:
        up=weights.copy();down=weights.copy();up[i]*=1+step;down[i]*=1-step
        hi,_=contrast_and_scores(up,category,group,outcome)
        lo,_=contrast_and_scores(down,category,group,outcome)
        numeric=(hi-lo)/(2*step)
        checks.append(abs(numeric-scores[i]))
    result={'description':'Experimental, not independently validated for publication',
            'contrast':delta,'se_centered_candidate':centered,'se_skipped_candidate':skipped,
            'score_sum':float(scores.sum()),'derivatives_checked':len(checks),'max_abs_derivative_error':max(checks),
            'domain_n':int(domain.sum())}
    (HERE/'standardized-contrast-probe-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    report=f'''# Experimental standardization-variance diagnostic

Run date: {date.today().isoformat()}. This file documents a **research prototype**, not a validated confidence interval or clinical result. The main [2023 survey report](brfss2023-findings.md) remains a point-estimate analysis.

## What was checked

The contrast is the difference in the two cost-barrier proportions standardized to the weighted age distribution of the pooled eligible sample. Unlike a fixed external standard, this reference distribution is estimated from the same sample. The prototype linearizes both the age-specific rates and the estimated reference weights, retains out-of-domain records with zero scores, and aggregates the scores using full-sample strata and PSUs.

For {int(domain.sum()):,} eligible respondents, the contrast is {100*delta:+.3f} percentage points. The sum of individual influence scores is {scores.sum():.3g}. Numerical perturbations of {len(checks)} selected survey weights produced a maximum absolute derivative discrepancy of {max(checks):.3g} on the proportion scale. This is an implementation check, not an independent validation of the survey variance or interval coverage.

The prototype also computes candidate standard errors under two full-sample singleton-stratum policies. Those diagnostic quantities are retained in `standardized-contrast-probe-results.json`. The policies are modeling choices. A separate [estimator check](samplics-probe.md) compares aggregation of these influence scores against another package under one policy, but does not independently verify the score formula. A further [nonlinear-contrast check](svy-contrast-validation.md) uses a supported package to compute the whole contrast from cell proportions and their covariance, and examines domain-singleton policies. Further uncertainty assessment across annual survey comparisons remains necessary.

## Reproduce

Run `python standardized_contrast_probe.py` after preparing the 2023 extract. Requires pandas and NumPy. Do not use this prototype for policy conclusions or patient-level decisions.
'''
    (HERE/'standardized-contrast-probe.md').write_text(report,encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
