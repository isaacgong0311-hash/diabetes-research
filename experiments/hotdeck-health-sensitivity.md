# Sensitivity to adding general health to donor matching

Run date: 2026-11-01. This is an exploratory alternative donor assumption, not causal evidence or a validated imputation model.

The [balance audit](hotdeck-balance-audit.md) found a difference in observed general health between recipients and their original donor pools. Here we split those pools by general health: excellent/very good/good, fair/poor, or unknown. When a split has recipients but no donors, we fall back to the original unsplit pool; this occurred for 3 recipients, representing 0.01% of recipient survey weight. Observed income and insurance responses are retained, and recipient survey weights stay fixed. We draw 200 completed datasets with seed 725200, using the same fixed complete-case standard population as the original [donor experiment](hotdeck-sensitivity.md).

| Matching strategy | Mean standardized gap, percentage points | SD between donor draws, points |
|---|---:|---:|
| Original donor pools | +3.33 | 0.08 |
| Add general-health matching | +3.28 | 0.08 |

The two sets use different seeds; the difference in their means reflects both changed assumptions and finite-draw variation. The between-draw SD is **not** a confidence interval and excludes survey sampling and donor-model uncertainty. Splitting produces 195 recipient pools; 145 recipients (0.2% of recipient weight) have fewer than 30 eligible donors, with a minimum of 1 donors. The minimum weight-only donor effective size is 1.0. Small or highly weighted pools can make the result sensitive to a few donors.

Matching on observed health can address that specific imbalance when no fallback is needed, but does not prove similarity on missing income or insurance, correct nonresponse, establish a missing-at-random assumption, or make the results causal. A more elaborate matching rule is not automatically more valid. Income, insurance, health, and cost barriers are self-reported, and people with unknown age are excluded. Pool counts and diagnostics are available in `hotdeck-health-sensitivity-results.json` without individual donor links.

## Reproduce

Run `python hotdeck_sensitivity.py`, then `python hotdeck_health_sensitivity.py`, with pandas and NumPy installed.
