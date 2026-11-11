"""Synthetic, design-based check of the experimental standardized contrast.

This simulation is not a validation for BRFSS or evidence about real patients.
"""
import json
from datetime import date
from pathlib import Path

import numpy as np

from standardized_contrast_probe import contrast_and_scores,design_variance

HERE=Path(__file__).resolve().parent
SEED=7321
SIMULATIONS=1000


def main():
    rng=np.random.default_rng(SEED)
    # Three independent sampling strata with different population sizes and age mixes.
    sizes=[5000,3500,2500];base_sample_sizes=[300,240,180]
    age_probs=[[.65,.25,.10],[.30,.45,.25],[.12,.33,.55]]
    populations=[]
    for n,probs in zip(sizes,age_probs):
        age=rng.choice(3,size=n,p=probs)
        diabetes=rng.binomial(1,np.array([.08,.17,.29])[age])
        probability=np.array([.18,.10,.04])[age]+diabetes*np.array([.06,.04,.02])[age]
        outcome=rng.binomial(1,probability)
        populations.append((age,diabetes,outcome))
    pop_age=np.concatenate([x[0] for x in populations]);pop_group=np.concatenate([x[1] for x in populations]);pop_outcome=np.concatenate([x[2] for x in populations])
    truth,_=contrast_and_scores(np.ones(len(pop_age)),pop_age,pop_group,pop_outcome)
    scenarios=[]
    for multiplier in (1,2,4):
        sample_sizes=[n*multiplier for n in base_sample_sizes]
        estimates=[];ses=[];contains=[];excluded=0
        for _ in range(SIMULATIONS):
            ages=[];groups=[];outcomes=[];weights=[];strata=[]
            for k,((age,group,outcome),N,n) in enumerate(zip(populations,sizes,sample_sizes)):
                pick=rng.integers(0,N,size=n)  # with-replacement PSU sampling within each design stratum
                ages.append(age[pick]);groups.append(group[pick]);outcomes.append(outcome[pick])
                weights.append(np.full(n,N/n));strata.append(np.full(n,k))
            age=np.concatenate(ages);group=np.concatenate(groups);outcome=np.concatenate(outcomes)
            weight=np.concatenate(weights);stratum=np.concatenate(strata);psu=np.arange(len(age))
            try:
                estimate,scores=contrast_and_scores(weight,age,group,outcome)
            except ValueError:
                excluded+=1;continue
            se=design_variance(stratum,psu,scores)**.5
            estimates.append(estimate);ses.append(se);contains.append(estimate-1.959963984540054*se<=truth<=estimate+1.959963984540054*se)
        estimates=np.asarray(estimates);ses=np.asarray(ses);n_ok=len(estimates)
        scenarios.append({'sample_size':sum(sample_sizes),'valid_samples':n_ok,'invalid_samples_missing_cell':excluded,
            'mean_estimate':float(estimates.mean()),'empirical_bias':float(estimates.mean()-truth),
            'empirical_sd':float(estimates.std(ddof=1)),'mean_estimated_se':float(ses.mean()),
            'normal_95_interval_coverage':float(np.mean(contains))})
        print(f"Sample {sum(sample_sizes):,}: coverage {100*np.mean(contains):.1f}%",flush=True)
    result={'seed':SEED,'attempts_per_scenario':SIMULATIONS,'finite_population_size':sum(sizes),
            'true_contrast':truth,'scenarios':scenarios}
    (HERE/'contrast-simulation-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    rows=['| Sample size | Valid / attempted | Mean contrast | Empirical SD | Mean prototype SE | 95% interval coverage |','|---:|---:|---:|---:|---:|---:|']
    for r in scenarios:
        rows.append(f"| {r['sample_size']:,} | {r['valid_samples']:,} / {SIMULATIONS:,} | {r['mean_estimate']:.4f} | {r['empirical_sd']:.4f} | {r['mean_estimated_se']:.4f} | {100*r['normal_95_interval_coverage']:.1f}% |")
    report=f'''# Synthetic simulation: standardized contrast prototype

Run date: {date.today().isoformat()}. This synthetic simulation checks a calculation when the population answer is known. It is **not** evidence about people with diabetes and does not validate an analysis of BRFSS.

## Setup

We generated a fixed synthetic finite population of {sum(sizes):,} individuals in three sampling strata with different age distributions. Each individual has a simulated binary group, three-level age, and a binary outcome. The simulated group and outcome probabilities vary by age. The true target is the group difference in outcome rates directly standardized to the full synthetic population's pooled age distribution.

For each of three sample sizes, we drew {SIMULATIONS:,} independent samples with replacement, with unequal sampling fractions across design strata and inverse-probability weights. Each draw was treated as a separate PSU. For each sample with both groups represented in every age category, we calculated the contrast and a linearized with-replacement standard error, then formed an approximate normal 95% interval. Seed: {SEED}.

## Results

The true synthetic-population contrast is **{truth:.4f}** on the proportion scale.

{chr(10).join(rows)}

Coverage is the proportion of simulations whose intervals contained the fixed synthetic truth. At coverage near 95%, the Monte Carlo standard error is roughly 0.7 percentage points for 1,000 independent simulations. Samples lacking a group in any age cell are excluded and counted in the JSON results. The target standard population in each sample is estimated from the pooled sample, so the prototype includes variation in both age-specific rates and the reference distribution. A shortfall relative to nominal 95% in any scenario is a reason for further investigation, not proof of a particular cause.

## Interpretation

This tests one favorable, fully observed, with-replacement design at three sample sizes and one set of event rates. It does not establish coverage for BRFSS, which has different sampling, weights, nonresponse, missingness, singleton strata, and data distributions. The uncertainty analysis in the main survey reports remains unvalidated for use in population inference. See the [supported-package calculation check](svy-contrast-validation.md) and a separate [hypothetical cluster-sampling simulation](cluster-simulation.md).

## Reproduce

Run `python contrast_simulation.py` with NumPy and pandas available. Results are in `contrast-simulation-results.json`. The simulation calls functions from `standardized_contrast_probe.py` and uses no patient records.
'''
    (HERE/'contrast-simulation.md').write_text(report,encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
