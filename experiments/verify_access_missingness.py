"""Independently verify the missingness audit with SQL over the source extract."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / '.deps'))
import duckdb


def close(actual, expected):
    return abs(float(actual) - float(expected)) <= 1e-8 * max(1, abs(float(expected)))


def main():
    saved = json.loads((HERE / 'access-missingness-audit-results.json').read_text(encoding='utf-8'))
    con = duckdb.connect()
    sql = '''
        WITH base AS (
          SELECT *,
            COALESCE("_AGEG5YR" BETWEEN 1 AND 13, FALSE)
              AND COALESCE("_INCOMG1" BETWEEN 1 AND 7, FALSE)
              AND COALESCE("_HLTHPL1" IN (1, 2), FALSE) AS complete_case
          FROM read_csv_auto(?)
          WHERE "_STATE" BETWEEN 1 AND 56 AND "_LLCPWT" > 0
            AND DIABETE4 IN (1, 3) AND MEDCOST1 IN (1, 2)
        )
        SELECT DIABETE4, count(*) AS total_n,
          count(*) FILTER (WHERE complete_case) AS complete_n,
          count(*) FILTER (WHERE NOT complete_case) AS excluded_n,
          count(*) FILTER (WHERE NOT COALESCE("_INCOMG1" BETWEEN 1 AND 7, FALSE)) AS missing_income_n,
          sum("_LLCPWT") AS weight,
          sum("_LLCPWT") FILTER (WHERE NOT complete_case) AS excluded_weight,
          sum(CASE WHEN MEDCOST1=1 THEN "_LLCPWT" ELSE 0 END)
             FILTER (WHERE NOT complete_case) AS excluded_event_weight
        FROM base GROUP BY DIABETE4 ORDER BY DIABETE4
    '''
    rows = con.execute(sql, [str(HERE / 'brfss2023-selected.csv.gz')]).fetchall()
    if len(rows) != 2:
        raise ValueError('Unexpected number of diabetes groups')
    for row in rows:
        code, total_n, complete_n, excluded_n, income_n, weight, excluded_weight, event_weight = row
        name = {1: 'diabetes', 3: 'no_diabetes'}[int(code)]
        group = saved['groups'][name]
        checks = [(total_n, group['total']['n']), (complete_n, group['complete']['n']),
                  (excluded_n, group['excluded']['n']), (income_n, group['missing']['missing_income']['n']),
                  (weight, group['total']['weight']), (excluded_weight, group['excluded']['weight']),
                  (event_weight / excluded_weight, group['excluded']['cost_rate'])]
        if any(not close(a, b) for a, b in checks):
            raise ValueError(f'SQL cross-check failed for {name}: {checks}')
    print('Independent SQL audit passed: group counts, income missingness, weights, and excluded-group cost rates.')


if __name__ == '__main__':
    main()
