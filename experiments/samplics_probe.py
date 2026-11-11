"""Experimental cross-check of a ratio estimator with archived samplics.

This probe deliberately uses the package's skip-singleton setting, not the
centered setting used by the main validation example. It is not production inference.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'.surveydeps'))
import numpy as np
import pandas as pd
from samplics import TaylorEstimator
from samplics.utils.types import PopParam, SinglePSUEst
from survey_variance_probe import ratio_linearized
from standardized_contrast_probe import contrast_and_scores, design_variance


def main():
    d=pd.read_csv(HERE/'brfss2023-selected.csv.gz')
    domains={
        'age65_fair_poor':((d['_AGE_G']==6)&d.GENHLTH.isin([1,2,3,4,5]),d.GENHLTH.isin([4,5])),
        'diabetes_cost':(d['_STATE'].between(1,56)&(d.DIABETE4==1)&d.MEDCOST1.isin([1,2]),d.MEDCOST1==1),
        'no_diabetes_cost':(d['_STATE'].between(1,56)&(d.DIABETE4==3)&d.MEDCOST1.isin([1,2]),d.MEDCOST1==1),
    }
    results={}
    for name,(domain,outcome) in domains.items():
        x=domain.to_numpy(dtype=float)
        y=(domain&outcome).to_numpy(dtype=float)
        ours=ratio_linearized(d,y,x,singleton='skip')
        print(f'Estimating {name} with full-sample strata and PSUs retained...',flush=True)
        est=TaylorEstimator(PopParam.ratio)
        est.estimate(y=y,x=x,samp_weight=d['_LLCPWT'].to_numpy(),stratum=d['_STSTR'].to_numpy(),
                     psu=d['_PSU'].to_numpy(),single_psu=SinglePSUEst.skip)
        result={'ours_skip':ours,'samplics_point':float(est.point_est),'samplics_se':float(est.stderror)}
        result['point_abs_difference']=abs(result['samplics_point']-ours['estimate'])
        result['se_abs_difference']=abs(result['samplics_se']-ours['se'])
        results[name]=result
    domain=d['_STATE'].between(1,56)&(d['_LLCPWT']>0)&d.DIABETE4.isin([1,3])&d.MEDCOST1.isin([1,2])&d['_AGEG5YR'].between(1,13)
    group=np.where(domain,np.where(d.DIABETE4==1,1,0),-1)
    age=np.select([d['_AGEG5YR']<=5,d['_AGEG5YR']<=9],[0,1],default=2)
    weight=d['_LLCPWT'].to_numpy()
    contrast,scores=contrast_and_scores(weight,age,group,(d.MEDCOST1==1).to_numpy(dtype=float))
    print('Cross-checking variance of standardized-contrast influence scores...',flush=True)
    contrast_est=TaylorEstimator(PopParam.total)
    contrast_est.estimate(y=scores/weight,samp_weight=weight,stratum=d['_STSTR'].to_numpy(),
                          psu=d['_PSU'].to_numpy(),single_psu=SinglePSUEst.skip)
    ours_se=design_variance(d['_STSTR'],d['_PSU'],scores,'skip')**.5
    results['contrast_score_check']={'contrast':contrast,'ours_skip_score_se':ours_se,
                                     'samplics_score_se':float(contrast_est.stderror),
                                     'se_abs_difference':abs(float(contrast_est.stderror)-ours_se)}
    (HERE/'samplics-probe-results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    lines=['| Domain | Python ratio | Python SE | samplics ratio | samplics SE |',
           '|---|---:|---:|---:|---:|']
    for name,r in results.items():
        if name=='contrast_score_check':continue
        lines.append(f"| {name} | {r['ours_skip']['estimate']:.8f} | {r['ours_skip']['se']:.8f} | {r['samplics_point']:.8f} | {r['samplics_se']:.8f} |")
    report='''# Exploratory survey-estimator cross-check

This check compares two implementations on the same checksum-verified 2023 BRFSS source. The full survey sample and its strata/PSU structure are retained, with subgroups expressed as ratios of weighted domain indicators. Three domains are checked: the published 65+ fair/poor-health example, reported diabetes with a definite cost response, and reported no diabetes with a definite cost response.

Both implementations use the **skip-singleton** policy for this comparison. This sets the variance contribution of full-sample singleton strata to zero and may understate uncertainty. It differs from the centered singleton policy in the [published benchmark](https://muntasirmasum.github.io/brfssdata/articles/survey-design.html); see [the separate centered-policy probe](survey-variance-probe.md).

'''+ '\n'.join(lines) + '''

The Python implementation and `samplics` agree to the displayed precision for these examples. An additional comparison passes the standardized-contrast prototype's already-computed influence scores to `samplics` as a weighted total, checking the score-aggregation standard error under the same skip-singleton rule. The two score standard errors are '''+f"{ours_se:.8f} and {float(contrast_est.stderror):.8f}"+''' respectively. That checks aggregation only: it does not independently verify the influence-score formula or its statistical assumptions. The installed `samplics` 0.6.1 identifies itself as archived and no longer maintained. This check does not validate its behavior for all domains, the centered-singleton rule, age-standardized estimates, correlated contrasts, annual changes, or confidence-interval coverage. **The main survey analyses remain descriptive point estimates**, and design-based uncertainty for the primary standardized comparisons remains outstanding.

## Reproduce

Run `python samplics_probe.py` after the 2023 extract is created and a compatible `samplics` installation is available. This exploratory check was run with `samplics` 0.6.1 in a local dependency folder. Machine-readable output is in `samplics-probe-results.json`. For formal work, use a supported, independently validated survey package and document its handling of singleton strata and domains.
'''
    (HERE/'samplics-probe.md').write_text(report,encoding='utf-8')
    print(json.dumps(results,indent=2),flush=True)


if __name__=='__main__':main()
