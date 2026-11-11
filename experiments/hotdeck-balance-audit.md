# Donor-pool balance audit: observed general health

Run date: 2026-11-01. This diagnostic compares an observed auxiliary variable that was **not** used to construct the donor pools. It does not establish whether donors represent recipients on missing income or insurance.

For the [donor-draw experiment](hotdeck-sensitivity.md), donor pools match age band, diabetes response, cost-barrier response, and any observed income/insurance category. Among 85,827 recipients with missing income or insurance, 85,356 have a definite general-health answer. Within each pool, we calculate the weighted fair-or-poor health rate among recipients and among eligible donors with definite health answers. Donor rates are then averaged using **recipient pool weights**, so the two columns compare the same pool mix. General health codes 4 and 5 represent fair or poor health; codes 1–3 are the comparison, according to the [CDC 2023 variable documentation](https://www.cdc.gov/brfss/annual_data/2023/pdf/2023-calculated-variables-version4-508.pdf). Unknown health is excluded separately among donors and recipients.

| Recipient subgroup | Known-health recipients, n | Recipients reporting fair/poor health | Donor-pool rate with recipient-pool weights | Donor minus recipient, percentage points |
|---|---:|---:|---:|---:|
| All recipients | 85,356 | 20.7% | 18.6% | -2.11 |
| Reports no diabetes | 73,105 | 17.1% | 15.2% | -1.86 |
| Reports diabetes | 12,251 | 46.9% | 43.0% | -3.90 |
| Income missing only | 69,324 | 20.9% | 18.6% | -2.28 |
| Insurance missing only | 9,012 | 21.4% | 20.7% | -0.72 |
| Both missing | 7,020 | 18.5% | 16.0% | -2.47 |

The recipient-pool-weighted mean **absolute** donor-minus-recipient difference across pools is 3.00 percentage points; signed differences can cancel in the overall row. A difference on observed general health may indicate that the matching variables leave meaningful differences between donors and recipients, but this descriptive comparison has no design-based interval and cannot determine the reason for the difference. Similarity on general health would not prove similarity in the missing fields or establish a missing-at-random assumption. Within-pool rates may be unstable in small groups, and donor pools can overlap across patterns, so donor counts must not be summed as unique people.

## Reproduce

Run `python hotdeck_balance_audit.py` with NumPy and pandas after preparing the 2023 extract. Pool-level summaries are in `hotdeck-balance-audit-results.json`; no person-level donor links are saved.
