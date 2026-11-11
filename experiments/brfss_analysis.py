"""Descriptive weighted point estimates from 2023 BRFSS survey data.

Requires pandas and numpy; prepare the selected extract first. This deliberately
does not estimate confidence intervals without independently validated survey software.
"""
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
AGE=[('18–44',1,5),('45–64',6,9),('65+',10,13)]


def weighted_rate(df, condition):
    return float(np.sum(df['_LLCPWT']*condition)/df['_LLCPWT'].sum())


def measure(df, code, condition):
    values=df[code]
    return {'n':len(df),'unweighted_rate':float(condition(values).mean()),
            'weighted_rate':weighted_rate(df,condition(values).astype(float))}


def standardize_age(df, bands=AGE, reference='pooled'):
    age_data=df[df['_AGEG5YR'].between(1,13)].copy()
    rates=[];weights=[]; strata=[]
    for label,low,high in bands:
        section=age_data[age_data['_AGEG5YR'].between(low,high)]
        reference_section = section if reference=='pooled' else section[section.DIABETE4==1]
        row={'age':label,'weight':float(reference_section['_LLCPWT'].sum()),'groups':{}}
        for name,code in [('diabetes',1),('no_diabetes',3)]:
            g=section[section.DIABETE4==code]
            if g.empty: raise ValueError('Missing age/diabetes stratum')
            row['groups'][name]=measure(g,'MEDCOST1',lambda x:x==1)
        rates.append([row['groups']['diabetes']['weighted_rate'],row['groups']['no_diabetes']['weighted_rate']]);weights.append(row['weight']);strata.append(row)
    normalized=np.asarray(weights)/sum(weights)
    return {'age_known_n':len(age_data),'standard_rates':(normalized@np.asarray(rates)).tolist(),'strata':strata}


def main():
    d=pd.read_csv(HERE/'brfss2023-selected.csv.gz')
    meta=json.loads((HERE/'brfss2023-metadata.json').read_text(encoding='utf-8'))
    if len(d)!=433323: raise ValueError('Unexpected survey row count')
    # Benchmark against the 2023 CDC codebook, which includes territories and
    # uses all survey weights in the denominator for this displayed frequency.
    benchmark_n=int((d.DIABETE4==1).sum())
    benchmark=weighted_rate(d,(d.DIABETE4==1).astype(float))
    if benchmark_n!=59786 or abs(benchmark-0.1204)>0.0001:
        raise ValueError(f'Codebook benchmark mismatch: {benchmark_n}, {benchmark}')
    # State FIPS 1..56 cover the states and DC, but KY and PA are absent in 2023.
    us=d[d['_STATE'].between(1,56) & (d['_LLCPWT']>0)].copy()
    valid_diabetes=us[us.DIABETE4.isin([1,2,3,4])]
    prevalence=measure(valid_diabetes,'DIABETE4',lambda x:x==1)
    diabetes=us[us.DIABETE4==1]
    # For cost comparisons, exclude pregnancy-only and borderline responses, as
    # well as missing/refused/not sure for the survey question.
    cost_base=us[us.DIABETE4.isin([1,3])]
    cost=cost_base[cost_base.MEDCOST1.isin([1,2])]
    cost_missing=len(cost_base)-len(cost)
    diabetes_cost=cost[cost.DIABETE4==1]; no_cost=cost[cost.DIABETE4==3]
    cost_rates={'diabetes':measure(diabetes_cost,'MEDCOST1',lambda x:x==1),
                'no_diabetes':measure(no_cost,'MEDCOST1',lambda x:x==1)}
    standardized=standardize_age(cost)
    fine_standardized=standardize_age(cost,[(str(i),i,i) for i in range(1,14)])
    diabetes_standardized=standardize_age(cost,reference='diabetes')
    dm_health=diabetes[diabetes.GENHLTH.isin([1,2,3,4,5])]
    health=measure(dm_health,'GENHLTH',lambda x:x.isin([4,5]))
    check_base=diabetes[diabetes.CHECKUP1.isin([1,2,3,4,8])]
    check=measure(check_base,'CHECKUP1',lambda x:x==1)
    summary={'source':meta,'all_codebook_benchmark':{'n_yes':benchmark_n,'weighted_pct_all_responses':benchmark},'states_dc_n':len(us),'diabetes_valid_n':len(valid_diabetes),'diabetes_known_n':len(diabetes),'diagnosed_prevalence':prevalence,'cost_response_missing_n':cost_missing,'cost_rates':cost_rates,'cost_age_standardized':standardized,'cost_fine_age_standardized':fine_standardized,'cost_diabetes_age_standardized':diabetes_standardized,'health_fair_poor':health,'checkup_last_year':check}
    (HERE/'brfss2023-results.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    def pct(x):return f'{100*x:.1f}%'
    table=['| Age group | Diabetes: respondents; weighted cost barrier | No diabetes reported: respondents; weighted cost barrier |','|---|---:|---:|']
    for row in standardized['strata']:
        a=row['groups']['diabetes'];b=row['groups']['no_diabetes']
        table.append(f"| {row['age']} | {a['n']:,}; {pct(a['weighted_rate'])} | {b['n']:,}; {pct(b['weighted_rate'])} |")
    std=standardized['standard_rates']
    report=f'''# 2023 BRFSS: diabetes and access to care

Run date: {date.today().isoformat()}. This is a descriptive, survey-weighted analysis of an independently collected population survey, not a continuation of the historical hospital readmission cohort.

## Data and verification

The [CDC 2023 BRFSS documentation](https://www.cdc.gov/brfss/annual_data/annual_2023.html) describes a telephone survey of noninstitutionalized adults. The CDC download returned HTTP 403 in this environment, so we used a [documented third-party Parquet conversion](https://muntasirmasum.github.io/brfssdata/articles/datasets.html) of the CDC data. Its published SHA-256 was checked: `{meta['mirror_sha256']}`. The file has {len(d):,} rows. We did not independently compare every record with the original CDC file.

As a basic source and coding check, the full file contains {benchmark_n:,} responses coded “yes” to having been told of diabetes, and those responses account for {pct(benchmark)} of the full weighted denominator. Both agree with the [2023 codebook](https://topofire.dbs.umt.edu/public_data/federal_public_datasets/CDC%20Behavioral%20Risk%20Factor%20Surveillance%20System%20/2023%20Annual%20Survey%20Data/Survey%20Data%20Information/USCODE23_LLCP_091024.HTML) at displayed precision. This benchmark includes territories and all response categories in the denominator; the analyses below exclude territories and unknown responses as described. The 2023 public file excludes Kentucky and Pennsylvania; these point estimates cover 48 states and DC, not the entire United States.

The following figures use `_LLCPWT` survey weights; respondent counts are unweighted. They are exploratory point estimates only. Although PSU and strata variables were retained, complex-design standard errors have **not** been validated or calculated here, so comparisons have no confidence intervals and should not be presented as statistically established differences.

## Self-reported diagnosis

Among {len(valid_diabetes):,} respondents in the 48 available states and DC with a definite diabetes response (yes, no, pregnancy only, or borderline), the weighted proportion reporting a diabetes diagnosis other than pregnancy-only was **{pct(prevalence['weighted_rate'])}**; the unweighted proportion was {pct(prevalence['unweighted_rate'])}. This is self-reported diagnosed diabetes of any type, not laboratory-defined total diabetes and not type 2 alone. People unaware of diabetes are not identified as having it by this question.

## Affordability of a doctor visit

Among people answering the cost question, {pct(cost_rates['diabetes']['weighted_rate'])} of those reporting diabetes (unweighted n={cost_rates['diabetes']['n']:,}) and {pct(cost_rates['no_diabetes']['weighted_rate'])} of those answering “no diabetes” (n={cost_rates['no_diabetes']['n']:,}) reported a time in the past 12 months when they needed to see a doctor but could not afford it. These groups are not age-matched. The comparison excludes pregnancy-only and borderline responses; {cost_missing:,} records in the two comparison groups lacked a definite yes/no cost response and were excluded from this outcome.

{chr(10).join(table)}

After standardizing each group's age-specific cost-barrier percentages to the weighted age distribution of the pooled comparison respondents with known age, the values were **{pct(std[0])}** and **{pct(std[1])}**, respectively. This direct age standardization includes {standardized['age_known_n']:,} respondents. It is an exploratory descriptive comparison, not causal adjustment: income, coverage, health status, and many other factors remain unaccounted for.

As sensitivity checks, using all 13 available age categories and the pooled age distribution gives {pct(fine_standardized['standard_rates'][0])} versus {pct(fine_standardized['standard_rates'][1])}; using the age distribution of respondents reporting diabetes as the common standard, with the three broad age groups, gives {pct(diabetes_standardized['standard_rates'][0])} versus {pct(diabetes_standardized['standard_rates'][1])}. The reference population changes the question being summarized, so these estimates need not match. They remain unadjusted for other factors and lack validated design-based intervals.

## Other self-reported measures among people reporting diabetes

- **{pct(health['weighted_rate'])}** rated their general health fair or poor (n={health['n']:,} with a definite answer).
- **{pct(check['weighted_rate'])}** reported a routine checkup within the past year (n={check['n']:,} with a definite answer, including “never” in the denominator).

These answers are self-reported and are not measures of whether diabetes care met clinical guidelines.

## Limitations and next work

- This is a telephone survey of noninstitutionalized adults and excludes people who cannot be reached or do not respond. Weighting reduces, but cannot eliminate, nonresponse and coverage bias.
- Self-report can misclassify diagnosis, cost barriers, and healthcare utilization. A cost barrier concerns any doctor visit, not necessarily diabetes care.
- All analyses are cross-sectional and cannot determine whether diabetes causes cost barriers or poor health, nor whether barriers precede outcomes.
- Age standardization uses three broad groups, and unknown age is excluded. Missingness and remaining confounding can alter comparisons.
- Survey-weighted point estimates alone do not characterize uncertainty. Before publication or policy use, recompute with validated complex-survey software using `_STSTR`, `_PSU`, and `_LLCPWT`, and cross-check definitions and domains against current CDC guidance.
- The 2023 data are a different population, era, and outcome from the 1999–2008 hospital readmission data. The two analyses do not independently replicate each other.

## Reproduce

Install pandas, NumPy, and DuckDB. Run `python brfss_prepare_mirror.py` then `python brfss_analysis.py` in this folder. The preparation script verifies the mirror checksum and writes a reduced CSV and provenance metadata. `brfss2023-results.json` contains counts and values. A separate `brfss_prepare.py` attempts to download the original CDC archive and failed with HTTP 403 in this environment; it is retained for another environment where access succeeds.
'''
    (HERE/'brfss2023-findings.md').write_text(report,encoding='utf-8')
    print(f"All-regions codebook check {benchmark_n:,}; weighted {pct(benchmark)}")
    print(f"48 states+DC diabetes {pct(prevalence['weighted_rate'])}; cost barrier diabetes {pct(cost_rates['diabetes']['weighted_rate'])}; no diabetes {pct(cost_rates['no_diabetes']['weighted_rate'])}")
    print(f"Age-standardized cost barrier {pct(std[0])} vs {pct(std[1])}")


if __name__=='__main__':main()
