"""Experimental Taylor-linearized ratio check; not yet validated for reporting."""
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
Z=1.959963984540054


def ratio_linearized(data, numerator, denominator, singleton='center'):
    """With-replacement stratum/PSU variance; center full-sample singleton at 0.

    This probe has not been independently validated for all survey domains.
    Inputs numerator/denominator are full-sample arrays and include domain zeros.
    """
    w=data['_LLCPWT'].to_numpy()
    denom=float(np.sum(w*denominator)); num=float(np.sum(w*numerator))
    if denom<=0:raise ValueError('Nonpositive denominator')
    estimate=num/denom
    score=w*(numerator-estimate*denominator)/denom
    psus=pd.DataFrame({'stratum':data['_STSTR'],'psu':data['_PSU'],'score':score}).groupby(['stratum','psu'],sort=False)['score'].sum()
    grouped=psus.groupby(level=0).agg(['count','sum',lambda v:float(np.dot(v,v))])
    grouped.columns=['n','total','sum_square']
    multi=grouped[grouped.n>1]; single=grouped[grouped.n==1]
    if singleton not in ('center','skip'):raise ValueError('Unknown singleton policy')
    variance=float((multi.n/(multi.n-1)*(multi.sum_square-multi.total**2/multi.n)).sum() + (single.sum_square.sum() if singleton=='center' else 0))
    return {'estimate':estimate,'se':variance**.5,'normal_ci':[estimate-Z*variance**.5,estimate+Z*variance**.5],
            'full_sample_singletons':len(single),'n_strata':len(grouped)}


def main():
    d=pd.read_csv(HERE/'brfss2023-selected.csv.gz')
    # External benchmark: all participating regions, age 65+, valid general health.
    domain=(d['_AGE_G']==6)&d.GENHLTH.isin([1,2,3,4,5])
    numerator=(domain&d.GENHLTH.isin([4,5])).to_numpy(dtype=float)
    denominator=domain.to_numpy(dtype=float)
    benchmark=ratio_linearized(d,numerator,denominator)
    target={'estimate':0.254,'lower':0.249,'upper':0.260,'rounding_tolerance':0.0015}
    match=(abs(benchmark['estimate']-target['estimate'])<target['rounding_tolerance'] and
           abs(benchmark['normal_ci'][0]-target['lower'])<target['rounding_tolerance'] and
           abs(benchmark['normal_ci'][1]-target['upper'])<target['rounding_tolerance'])
    result={'benchmark':benchmark,'published_rounded_reference':target,'matches_rounded_reference':bool(match),
            'reference':'https://muntasirmasum.github.io/brfssdata/articles/survey-design.html'}
    (HERE/'survey-variance-probe-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    report=f'''# Survey variance probe: external benchmark

Run date: {date.today().isoformat()}. This is an implementation experiment, not a validated analysis for publication.

## Benchmark

The [brfssdata survey-design vignette](https://muntasirmasum.github.io/brfssdata/articles/survey-design.html) reports a weighted fair/poor health proportion of approximately 0.254 (95% interval 0.249–0.260) for 2023 respondents aged 65 and older (`_AGE_G` = 6) in all participating reporting areas. It constructs a survey design in R and uses singleton adjustments. The published figures are rounded to three decimals. The age code here deliberately matches that benchmark; `_AGEG5YR` is a different calculated variable and gives a different sample count.

The exploratory Python calculation on the checksum-verified converted source gives a ratio estimate of **{benchmark['estimate']:.6f}**, standard error **{benchmark['se']:.6f}**, and approximate normal interval **{benchmark['normal_ci'][0]:.6f}–{benchmark['normal_ci'][1]:.6f}**. It has {benchmark['n_strata']:,} full-sample strata, including {benchmark['full_sample_singletons']:,} singleton strata. Agreement within the selected 0.0015 tolerance for each rounded reference value: **{match}**.

## Method and limits

The exploratory code represents the domain ratio as weighted numerator and denominator over the full sample, linearizes the ratio, sums scores within PSU, computes with-replacement within-stratum variance, and centers full-sample singleton PSU scores at zero. It uses a normal critical value. The reference uses a survey package's own domain and singleton handling; the reference gives only rounded values, and its exact configuration or interval method may differ. Matching one example within rounding is a **sanity check**, not independent validation for all domains, contrasts, standardization, sparse cells, or annual differences.

Before reporting uncertainty for the diabetes comparisons, compare against an established complex-survey implementation on identical data, explicitly verify domain and singleton behavior, and correctly propagate covariance for standardized contrasts. Continue treating the main diabetes figures as point estimates until that check is complete.

## Reproduce

Run `python survey_variance_probe.py` after preparing the 2023 extract. The result is also stored in `survey-variance-probe-results.json`. Requires NumPy and pandas.
'''
    (HERE/'survey-variance-probe.md').write_text(report,encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
