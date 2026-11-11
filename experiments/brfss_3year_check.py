"""Three-year common-geography replication check, 2023–2025 BRFSS."""
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from urllib.request import urlopen

HERE=Path(__file__).resolve().parent
try:
    import duckdb
except ModuleNotFoundError:
    sys.path.insert(0,str(HERE/'.deps'))
    import duckdb
import numpy as np
import pandas as pd

from brfss_year_comparison import age_rates, load_2024

URL='https://github.com/muntasirmasum/brfssdata/releases/download/data-2025/brfss_2025.parquet'
HASH='6cd8bd7137b69d15f3d08d8739a14f820df0af71d7d2b0eddeefa1eb50d754d7'
FILE=HERE/'brfss-2025-mirror.parquet'
EXCLUDED={6,21,28,32,42,47}


def load2025():
    if not FILE.exists():
        print('Downloading 2025 BRFSS mirror...',flush=True)
        with urlopen(URL,timeout=180) as response: raw=response.read()
        if hashlib.sha256(raw).hexdigest()!=HASH:raise ValueError('2025 download checksum mismatch')
        FILE.write_bytes(raw)
    if hashlib.sha256(FILE.read_bytes()).hexdigest()!=HASH:raise ValueError('2025 local checksum mismatch')
    fields=['_STATE','_LLCPWT','_AGEG5YR','DIABETE4','MEDCOST1']
    db=duckdb.connect()
    cols=[r[0] for r in db.execute('DESCRIBE SELECT * FROM read_parquet(?)',[str(FILE)]).fetchall()]
    mapping={c.upper():c for c in cols}
    if set(fields)-set(mapping):raise ValueError('Required variables absent in 2025 mirror')
    query=', '.join('"'+mapping[c]+'" AS "'+c+'"' for c in fields)
    return db.execute(f'SELECT {query} FROM read_parquet(?)',[str(FILE)]).df()


def restrict(d):
    return d[d['_STATE'].between(1,56)&~d['_STATE'].isin(EXCLUDED)&(d['_LLCPWT']>0)&
             d.DIABETE4.isin([1,3])&d.MEDCOST1.isin([1,2])&d['_AGEG5YR'].between(1,13)]


def main():
    y23=pd.read_csv(HERE/'brfss2023-selected.csv.gz');y24=load_2024();y25=load2025()
    if len(y25)!=356158:raise ValueError('Unexpected 2025 row count')
    if y25['_STATE'].isin([6,28,32]).any():raise ValueError('2025 unexpectedly includes an excluded state')
    yes=int((y25.DIABETE4==1).sum())
    yes_weighted=float((y25['_LLCPWT']*(y25.DIABETE4==1)).sum()/y25['_LLCPWT'].sum())
    cost_yes=int((y25.MEDCOST1==1).sum())
    cost_weighted=float((y25['_LLCPWT']*(y25.MEDCOST1==1)).sum()/y25['_LLCPWT'].sum())
    if yes!=51827 or cost_yes!=34602 or abs(yes_weighted-.1251)>.0001 or abs(cost_weighted-.1269)>.0001:
        raise ValueError('2025 CDC codebook benchmark did not match')
    samples={year:restrict(df) for year,df in [(2023,y23),(2024,y24),(2025,y25)]}
    for year,frame in samples.items():
        if frame['_STATE'].nunique()!=45:raise ValueError(f'{year} missing a common geography')
    age={year:age_rates(frame) for year,frame in samples.items()}
    reference=np.asarray([r['weight'] for r in age[2023]]);reference/=reference.sum()
    result={'reference_weights_2023':reference.tolist(),'geography':'44 states and DC; excludes CA, KY, MS, NV, PA, TN','2025_source':URL,'2025_sha256':HASH,'2025_codebook_check':{'diabetes_yes_n':yes,'diabetes_yes_weighted_all':yes_weighted,'cost_yes_n':cost_yes,'cost_yes_weighted_all':cost_weighted},'years':{}}
    table=['| Year | Respondents | Reports diabetes | Reports no diabetes | Difference |','|---|---:|---:|---:|---:|']
    for year in (2023,2024,2025):
        rates={group:float(np.dot(reference,[r['groups'][group]['weighted_rate'] for r in age[year]])) for group in ('diabetes','no_diabetes')}
        result['years'][year]={'n':len(samples[year]),'age_rows':age[year],'standardized_rates':rates}
        table.append(f"| {year} | {len(samples[year]):,} | {100*rates['diabetes']:.1f}% | {100*rates['no_diabetes']:.1f}% | {100*(rates['diabetes']-rates['no_diabetes']):+.1f} pp |")
    (HERE/'brfss-3year-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    report=f'''# 2023–2025 BRFSS: three-year common-footprint check

Run date: {date.today().isoformat()}. This is a descriptive sensitivity check using annual cross-sectional samples and survey-weighted point estimates. It is not a longitudinal study, and design-based confidence intervals and trend tests have not been calculated.

## Harmonized geography and sample

The [CDC 2023 release](https://www.cdc.gov/brfss/annual_data/annual_2023.html) excludes Kentucky and Pennsylvania, the [2024 release](https://www.cdc.gov/brfss/annual_data/annual_2024.html) excludes Tennessee, and the [2025 release](https://www.cdc.gov/brfss/annual_data/annual_2025.html) excludes California, Mississippi and Nevada. All three analyses therefore exclude these six states and territories. The resulting **44 states plus DC do not represent the entire United States**, especially because California is absent.

For each year, we keep definite yes/no responses to the diabetes and doctor-visit affordability questions and known age, using the same definitions as [the 2023–2024 check](brfss-year-comparison.md). The question asks whether respondents needed a doctor in the preceding 12 months but could not afford to see one; the reason for the visit is unknown. Counts are unweighted and percentages use `_LLCPWT`.

Both comparison groups in each year are standardized to the same weighted age distribution from the 2023 common-footprint sample: 18–44 {100*reference[0]:.1f}%, 45–64 {100*reference[1]:.1f}%, and 65+ {100*reference[2]:.1f}%.

{chr(10).join(table)}

The difference is within-year diabetes minus no-diabetes in percentage points. Changes across years are descriptive; the samples differ, six states are excluded, and uncertainty has not been quantified. The results cannot establish a causal effect of diabetes, age, insurance, income, or an intervention.

## Source and validation

The 2025 file has {len(y25):,} rows, consistent with the CDC's listed file size. Its [third-party conversion](https://muntasirmasum.github.io/brfssdata/articles/datasets.html) was checked against published SHA-256 `{HASH}`. Across all 2025 records, {yes:,} reported diabetes ({100*yes_weighted:.2f}% weighted) and {cost_yes:,} reported a cost barrier ({100*cost_weighted:.2f}% weighted), matching the [CDC 2025 codebook](https://www.cdc.gov/brfss/annual_data/2025/zip/codebook25_llcp-v2-508.zip) at its displayed precision. These benchmark percentages include territories and all response categories; they differ from the comparison denominators above. The 2023 and 2024 conversions and checks are documented in the prior reports. We have not compared every row to the original CDC files; annual questionnaire and coding changes, nonresponse and selection still require review before formal time-trend analysis.

## Reproduce

Run `python brfss_3year_check.py` after creating the 2023 extract with `brfss_prepare_mirror.py`. The script uses the cached 2024 mirror and downloads the 2025 mirror if absent; it validates the 2025 checksum and writes `brfss-3year-results.json`. Requires NumPy, pandas, and DuckDB.
'''
    (HERE/'brfss-3year-check.md').write_text(report,encoding='utf-8')
    print('\n'.join(table))


if __name__=='__main__':main()
