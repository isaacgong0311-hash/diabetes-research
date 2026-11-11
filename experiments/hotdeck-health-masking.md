# Holdout comparison of donor matching rules

Run date: 2026-11-01. This is an artificial masking experiment, not a validation on actually missing responses.

We reuse the same 63,063-person random holdout of complete respondents from the [original masking experiment](hotdeck-masking-validation.md). For each hidden-field pattern, the original donor matching rule is compared with splitting pools by general health as in the [health-matched sensitivity experiment](hotdeck-health-sensitivity.md). General health unknown is treated as its own category; when no donor exists in a health category, the original pool is used. The health-matched runs use 50 donor draws per pattern. Both methods use the same held-out respondents and fixed complete-case reference distribution, but different random donor draws.

| Hidden fields | Original weighted accuracy | Health-matched weighted accuracy | Original gap error, points | Health-matched gap error, points | Holdouts using fallback |
|---|---:|---:|---:|---:|---:|
| Income only | 48.6% | 50.1% | +0.144 | +0.116 | 2 |
| Insurance only | 87.3% | 87.3% | +0.211 | +0.227 | 1 |
| Income and insurance | 43.3% | 44.6% | +0.403 | +0.353 | 0 |

Gap error means mean reconstructed standardized gap minus the fully observed gap (+3.467 percentage points). Accuracy for the two-field pattern requires both categories to be correct. These results are descriptive for **one random split**; the variance of donor draws and uncertainty across holdout splits are not shown in the table. The smallest health-matched donor pool across patterns had 1 donor(s). Additional conditioning may improve, worsen, or barely change a particular metric while creating sparse pools.

Holdouts have observed income and insurance and were masked randomly, unlike genuinely missing cases. Similar or higher accuracy on them does not establish validity for nonrespondents, and matching general health does not prove missing-at-random or a causal effect. Survey-design variance and donor-model uncertainty are not estimated. Full summaries are in `hotdeck-health-masking-results.json`.

## Reproduce

Run `python hotdeck_masking_validation.py` followed by `python hotdeck_health_masking.py` with NumPy and pandas installed. No person-level donor links are saved.
