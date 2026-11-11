# Repeated artificial-masking checks for donor matching

Run date: 2026-11-01. This is a repeatability check among respondents with known answers; it cannot validate imputation for the actually missing cases.

Starting with 316,267 complete respondents, we created 8 independently generated random holdout splits, each targeting 20% of records (seed 83710). For each split we masked income only, insurance only, or both; holdout records could not donate. The original and health-matched donor rules each generated 10 random completed datasets per pattern and split. Both use the same fixed complete-case reference distribution and the known complete-case comparison gap of +3.467 percentage points. Each table row summarizes the split-level mean of the donor draws. Matching rules and fallback are described in the [health-matched experiment](hotdeck-health-sensitivity.md).

| Hidden fields | Rule | Mean weighted accuracy | SD across split accuracies, percentage points | Mean gap error, points | SD across split gap errors, points |
|---|---|---:|---:|---:|---:|
| Income only | Original | 48.5% | 0.17 | +0.020 | 0.137 |
| Income only | Health matched | 49.8% | 0.22 | -0.001 | 0.089 |
| Insurance only | Original | 87.1% | 0.17 | -0.022 | 0.126 |
| Insurance only | Health matched | 87.1% | 0.20 | -0.018 | 0.136 |
| Income and insurance | Original | 43.0% | 0.22 | -0.041 | 0.128 |
| Income and insurance | Health matched | 44.3% | 0.16 | -0.081 | 0.114 |

Gap error is the reconstructed gap minus the known complete-case gap. Both-field accuracy requires both categories to match. Split SDs summarize this small set of overlapping random splits, including finite donor-draw noise; they are **not** independent-study standard errors or confidence intervals. Accuracies target individual guesses, while the gap error targets a population summary, so one can improve without the other. The smallest health-matched pool observed across all splits contained 1 donor(s).

Random masking of observed cases is much easier to study than real nonresponse. These results do not establish that missing answers are missing at random, demonstrate donor exchangeability for those respondents, include complex-survey variance, or justify clinical conclusions. The true missing-income or insurance distributions remain unknown. Pool details and split results are in `hotdeck-repeated-masking-results.json`.

## Reproduce

Run `python hotdeck_repeated_masking.py` after producing the complete-case analysis, with NumPy and pandas installed. Seed 83710 and the numbers of splits and draws are fixed in the script. No individual imputations or donor links are saved.
