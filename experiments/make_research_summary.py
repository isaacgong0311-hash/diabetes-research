"""Assemble an executive synthesis from the saved experiment results."""
import json
from datetime import date
from pathlib import Path

HERE=Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))


def p(x):return f'{100*x:.1f}%'


def main():
    hospital=load('results.json');model=load('model_results.json');robust=load('robustness_results.json')
    a1c=load('standardization_results.json');survey=load('brfss2023-results.json')
    context=load('brfss2023-access-results.json');three=load('brfss-3year-results.json')
    sensitivity=load('brfss-access-standardization-results.json')
    simulation=load('contrast-simulation-results.json')
    crosscheck=load('svy-contrast-validation-results.json')
    cluster=load('cluster-simulation-results.json')
    annual=load('annual-contrast-probe-results.json')
    annual_sim=load('annual-simulation-results.json')
    access_uncertainty=load('access-uncertainty-probe-results.json')
    access_bootstrap=load('access-bootstrap-probe-results.json')
    missingness=load('missingness-standardized-probe-results.json')
    missing_audit=load('access-missingness-audit-results.json')
    prior=hospital['prior_inpatient'];split=robust['random_splits']
    yearrows=[]
    for year in ('2023','2024','2025'):
        x=three['years'][year];a=x['standardized_rates']['diabetes'];b=x['standardized_rates']['no_diabetes']
        yearrows.append(f'| {year} | {x["n"]:,} | {p(a)} | {p(b)} |')
    specs=[]
    for key,label in [('age_only','Age'),('age_income','Age + income'),('age_income_insurance','Age + income + insurance')]:
        x=sensitivity['estimates'][key];a,b=x['standardized_rates']
        specs.append(f'| {label} | {p(a)} | {p(b)} | {x["smallest_group_n"]:,} |')
    report=f'''# Diabetes research: synthesis and evidence boundaries

Updated: {date.today().isoformat()}. This working synthesis brings together analyses from two different public-data sources. It is exploratory research, not clinical guidance.

## What was studied

1. **Hospital records:** the UCI Diabetes 130-US Hospitals dataset, covering 1999–2008 inpatient encounters involving any diabetes type. The main analysis selects one encounter per patient, then excludes death/hospice, leaving {hospital['primary_cohort']:,} records. Outcome: recorded readmission in less than 30 days.
2. **Population survey:** CDC BRFSS telephone survey data, accessed through checksum-verified third-party conversions. The 2023 public data cover 48 states and DC after territories are excluded. Outcome of interest: self-reported inability to afford a needed doctor visit in the past year. Diabetes status is self-reported and does not identify type 2 specifically.

These studies ask different questions. The survey does not independently validate the hospital model, and the hospital cohort does not estimate the experiences of all people with diabetes.

## Findings worth investigating

### 1. Prior inpatient use and recorded readmission

The hospital cohort's recorded <30-day readmission rates were {p(prior[0]['rate'])} after zero prior inpatient visits, {p(prior[1]['rate'])} after one, and {p(prior[2]['rate'])} after two or more. These are unadjusted associations. They may reflect illness severity, access, care patterns, or other factors; they do not prove that prior visits cause readmission.

The simple expanded model had test AUC {model['models']['expanded']['auc']:.3f} on one patient split. Across five overlapping random splits, its AUC ranged from {min(x['expanded']['auc'] for x in split):.3f} to {max(x['expanded']['auc'] for x in split):.3f}. This is modest discrimination, not external validation. Dataset vintage, outcome capture, and absence of verifiable dates and hospital identifiers limit transportability.

Details: [initial hospital analysis](findings.md), [held-out model](extended-findings.md), [robustness checks](robustness-findings.md), and [hospital figure](figure_hospital_readmission.png).

### 2. Recorded A1C and hospital readmission

The crude recorded-minus-not-recorded A1C comparison was {100*(a1c['raw_rates'][1]-a1c['raw_rates'][0]):+.2f} percentage points; standardizing for broad age and prior-inpatient-use strata changed the difference to {100*a1c['difference_recorded_minus_not_recorded']:+.2f} percentage points. The patient-bootstrap interval was {100*a1c['bootstrap_ci'][0]:+.2f} to {100*a1c['bootstrap_ci'][1]:+.2f} points. A missing recorded result is not proof that testing did not occur. Remaining confounding prevents a conclusion about effects of ordering A1C tests.

Details: [A1C standardization analysis](standardization-findings.md).

### 3. Age can obscure cost-barrier comparisons

In the 2023 survey sample, weighted crude doctor-visit cost-barrier rates were {p(survey['cost_rates']['diabetes']['weighted_rate'])} among respondents reporting diabetes and {p(survey['cost_rates']['no_diabetes']['weighted_rate'])} among those reporting no diabetes. Standardized to the pooled age distribution, the rates were {p(survey['cost_age_standardized']['standard_rates'][0])} and {p(survey['cost_age_standardized']['standard_rates'][1])}. This illustrates why sample composition matters; it does not establish why the groups differ. The estimate is for respondents in 48 states and DC, not the entire United States.

On a narrower common complete-case sample, changing the standardization produced the following descriptive rates:

| Common standard | Diabetes | No diabetes reported | Smallest unweighted group/cell |
|---|---:|---:|---:|
{chr(10).join(specs)}

These rows are not competing causal estimates. The standard population differs across specifications, the most detailed specification contains small cells, and {sensitivity['excluded_n']:,} comparison respondents were omitted from this complete-case analysis due to missing age, income, or insurance data. An [exploratory uncertainty analysis](access-uncertainty-probe.md) retains the full survey design, and a [nonlinear survey-package check](access-svy-nonlinear-validation.md) reproduces the calculations under the same assumptions. Interval coverage is not established. The smallest joint group/cell contains {access_uncertainty['minimum_group_n']} respondents, and a joint group/cell had zero events in {access_bootstrap['replicates_with_any_zero_event_joint_group_cell']} of {access_bootstrap['attempted']} [bootstrap replicates](access-bootstrap-probe.md).

In the broader eligible sample, {100*missing_audit['groups']['diabetes']['excluded_weighted_fraction']:.1f}% of weighted respondents reporting diabetes and {100*missing_audit['groups']['no_diabetes']['excluded_weighted_fraction']:.1f}% reporting no diabetes were excluded for at least one unknown covariate. In an exploratory [shared-age comparison](missingness-standardized-probe.md), the complete-minus-incomplete difference in the diabetes cost-barrier gap was {100*missingness['estimates']['complete_minus_incomplete']['contrast']:+.2f} percentage points, with an approximate 95% interval of {100*missingness['estimates']['complete_minus_incomplete']['normal_95_low']:+.2f} to {100*missingness['estimates']['complete_minus_incomplete']['normal_95_high']:+.2f} points. This does not prove missingness is ignorable or recover the unknown income and insurance values.

For the separate 2023 pooled-age-standardized comparison above, a supported survey package independently computed the full nonlinear contrast and a design-based approximate 95% interval of {100*crosscheck['domain_policies']['standard']['lci']:.2f} to {100*crosscheck['domain_policies']['standard']['uci']:.2f} percentage points. It agrees numerically with the prototype under the stated survey-design and singleton assumptions. This checks the calculation, not causal interpretation or actual coverage for BRFSS. See the [survey-contrast cross-check](svy-contrast-validation.md).

Details: [2023 survey analysis](brfss2023-findings.md), [cost-barrier figure](figure_brfss_cost_barriers.png), and [complete-case sensitivity](brfss-access-standardization.md).

### 4. A common-footprint check across three years

To compare 2023–2025 consistently, all years exclude California, Kentucky, Mississippi, Nevada, Pennsylvania, and Tennessee because they are absent from at least one release. The analysis therefore covers 44 states and DC, not the whole country. Rates are standardized to the same 2023 pooled age distribution:

| Year | Respondents | Diabetes | No diabetes reported |
|---|---:|---:|---:|
{chr(10).join(yearrows)}

The samples are cross-sectional and differ each year. There are no validated design-based intervals here, so these numbers do not establish a time trend or statistically significant change.

An [exploratory annual uncertainty probe](annual-contrast-probe.md) accounts for the shared estimated 2023 age reference and, assuming independent annual samples, estimates a 2024-versus-2023 change in the group contrast of {100*annual['comparisons']['2024']['difference_in_contrasts']:+.2f} percentage points (approximate 95% interval {100*annual['comparisons']['2024']['normal_95_low']:+.2f} to {100*annual['comparisons']['2024']['normal_95_high']:+.2f}) and a 2025-versus-2023 change of {100*annual['comparisons']['2025']['difference_in_contrasts']:+.2f} points (interval {100*annual['comparisons']['2025']['normal_95_low']:+.2f} to {100*annual['comparisons']['2025']['normal_95_high']:+.2f}). Both intervals include zero. These are provisional calculations, not independently validated tests or evidence of a trend. A [synthetic check](annual-simulation.md) covered its known target in {100*annual_sim['coverage']:.1f}% of {annual_sim['valid']:,} simulated samples, which does not validate the BRFSS assumptions.

Details: [three-year check](brfss-3year-check.md) and [two-year check](brfss-year-comparison.md).

### 5. Access context

Among 2023 respondents aged 18–64 reporting diabetes and giving definite responses, {p(context['insurance_groups']['Any insurance']['weighted_rate'])} with any reported insurance and {p(context['insurance_groups']['No insurance']['weighted_rate'])} without reported insurance reported a doctor-visit cost barrier. The groups may differ in many ways; these values do not estimate the effect of obtaining insurance. Unknown insurance and income responses were excluded from their respective analyses.

Details: [access context](brfss2023-access-context.md).

## What is not established

- A treatment effect, causal explanation, or patient-specific risk score.
- A validated prediction system, benefit from a clinical intervention, or evidence of current hospital performance.
- Type 2-specific estimates or nationally representative results for all states in the 2023–2025 survey comparison.
- A validated statistical test or trend across survey years: the annual uncertainty probe relies on an independence assumption and has not been independently validated end to end.
- Validated coverage for the experimental standardized-contrast uncertainty method. In one synthetic design, nominal 95% intervals covered the known answer in {100*simulation['scenarios'][0]['normal_95_interval_coverage']:.1f}%, {100*simulation['scenarios'][1]['normal_95_interval_coverage']:.1f}%, and {100*simulation['scenarios'][2]['normal_95_interval_coverage']:.1f}% of 1,000 samples at increasing sample sizes. These simulations are not BRFSS validation; see [simulation details](contrast-simulation.md).
- Reliable 95% coverage under every sampling design. In a separate synthetic clustered population, the cluster-aware normal interval covered its known target in {100*cluster['cluster_psu']['coverage']:.1f}% of {cluster['valid_samples']:,} samples; see the [cluster experiment](cluster-simulation.md). This hypothetical design is not BRFSS.
- Complete provenance verification against every original CDC record; the copies were checksum-verified and checked against selected official codebook benchmarks.

## Highest-value next steps

1. Replicate the complete-case and annual uncertainty calculations with a separately developed survey implementation. Investigate sparse-cell interval coverage and cross-year dependence.
2. Obtain the official source files when accessible and cross-check all variables, state participation, and annual coding. Document nonresponse and conduct sensitivity analyses for missing income and insurance.
3. Define a narrow research question and a causal diagram before adding covariates or interpreting the access differences. Decide whether a policy, clinical, or descriptive question is intended.
4. If developing a readmission model, use a current dataset with hospital and encounter dates, a prespecified intended use, external or temporal validation, subgroup calibration, and prospective evaluation before any deployment.

## Reproduce

See the [experiment index](README.md) for dependencies, exact commands, data provenance, checksums, and links to machine-readable results. Run the scripts sequentially on a memory-constrained machine. `make_research_summary.py` regenerates this document from saved results.
'''
    (HERE/'research-synthesis.md').write_text(report,encoding='utf-8')
    print('Wrote research-synthesis.md')


if __name__=='__main__':main()
