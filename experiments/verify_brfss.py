"""Independent SQL cross-check of selected weighted estimates against the Parquet source."""
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
try:
    import duckdb
except ModuleNotFoundError:
    sys.path.insert(0,str(HERE/'.deps'))
    import duckdb


def main():
    results=json.loads((HERE/'brfss2023-results.json').read_text(encoding='utf-8'))
    source=str(HERE/'brfss-2023-mirror.parquet')
    db=duckdb.connect()
    benchmark=db.execute('''SELECT count(*) FILTER (WHERE DIABETE4=1),
        sum(CASE WHEN DIABETE4=1 THEN "_LLCPWT" ELSE 0 END)/sum("_LLCPWT")
        FROM read_parquet(?)''',[source]).fetchone()
    assert benchmark[0]==results['all_codebook_benchmark']['n_yes']
    assert abs(benchmark[1]-results['all_codebook_benchmark']['weighted_pct_all_responses'])<1e-10
    query='''SELECT DIABETE4, count(*),
        sum(CASE WHEN MEDCOST1=1 THEN "_LLCPWT" ELSE 0 END)/sum("_LLCPWT")
        FROM read_parquet(?) WHERE "_STATE" BETWEEN 1 AND 56 AND "_LLCPWT">0
        AND DIABETE4 IN (1,3) AND MEDCOST1 IN (1,2) GROUP BY DIABETE4 ORDER BY DIABETE4'''
    output=db.execute(query,[source]).fetchall()
    for code,n,value in output:
        expected=results['cost_rates']['diabetes' if code==1 else 'no_diabetes']
        assert n==expected['n'] and abs(value-expected['weighted_rate'])<1e-10
    print('Independent SQL checks passed: codebook benchmark and both cost-barrier estimates.')


if __name__=='__main__':main()
