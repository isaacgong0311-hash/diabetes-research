# Stelo prospective N-of-1 glucose study

Protocol version: 0.1  
Preregistered: November 10, 2026  
Status: planned; no Stelo data inspected  
Study type: prospective, randomized, paired N-of-1 crossover  

This protocol is deliberately separate from the population-level diabetes review. It can estimate whether a defined behavior changes this participant's short-term interstitial-glucose response under the studied conditions. It cannot diagnose diabetes, establish long-term health benefit, or generalize to other people.

## Safety and eligibility boundary

- Follow the current Stelo instructions and labeling. Stelo is an over-the-counter glucose biosensor for people not using insulin. It is not designed for people with problematic hypoglycemia and does not provide the low-glucose alerting expected from a therapeutic CGM.
- Do not start, stop, or change any medication or dose because of this study or a sensor reading. Discuss medication and treatment decisions with a qualified clinician.
- Do not deliberately provoke extreme glucose values, fast beyond the participant's normal routine, perform unsafe exercise, or consume a large sugar challenge for the study.
- Use only ordinary meals and activity that are already safe for the participant. The walking experiment should be omitted if walking after a meal is unsafe or medically restricted.
- A sensor value is not a diagnosis. Symptoms, repeated unusual patterns, or concern about diabetes should be evaluated clinically with appropriate confirmatory testing. If symptoms do not match the sensor, follow the device instructions, consider an appropriate blood-glucose check, and seek medical advice when needed.
- Remove the sensor for MRI, CT, or diathermy as directed by the device labeling.

## Research question

For one participant under ordinary living conditions, does a 10-minute moderate walk beginning 20 minutes after the first bite of a standardized dinner reduce the 0–120-minute incremental glucose area under the curve compared with remaining sedentary for the same period?

The study tests an immediate glucose-response effect only. It does not test weight loss, A1C, diabetes prevention, cardiovascular benefit, or clinical outcomes.

## Prespecified hypothesis and estimand

- **Primary hypothesis:** the post-meal walk lowers the paired 0–120-minute net incremental area under the glucose curve (net iAUC) relative to sedentary control.
- **Primary estimand:** the mean within-pair difference in net iAUC, walk minus control, across six two-day blocks.
- **Direction:** a negative difference favors walking.
- **Unit:** mg/dL × minute.

## Design

### Preferred design: two sensors

Stelo supports up to 15 days of wear per sensor, but not every sensor lasts the full period. The design therefore includes buffer days.

**Sensor 1: observational run-in**

- Day 1: acclimation and data-quality check; exclude from primary summaries because first-day agreement can be poorer.
- Days 2–12: usual routine with prospective logging; no intentional glucose experiments.
- Days 13–15: buffer for missed logging, sensor loss, or additional baseline observation.

**Sensor 2: randomized paired crossover**

- Day 1: acclimation; no primary challenge.
- Days 2–13: six two-day blocks. Each block contains one control dinner and one walking dinner, using the same meal, portion, meal time, and relevant routine as closely as practical.
- Days 14–15: buffer or replacement of a prospectively invalidated block. A replacement is labeled and never silently substituted.

### Randomization schedule

Condition A is sedentary control. Condition B is the 10-minute moderate walk. The locked order is:

| Block | First day | Second day |
|---|---|---|
| 1 | B | A |
| 2 | A | B |
| 3 | B | A |
| 4 | B | A |
| 5 | A | B |
| 6 | A | B |

The order must not be changed after seeing glucose data. If a day is invalid, record the reason before reviewing its post-meal curve and repeat the entire two-day block during buffer time when possible.

### One-sensor fallback

If only one sensor is available, treat the work as exploratory:

- Day 1: acclimation.
- Days 2–5: ordinary-routine baseline.
- Days 6–13: four paired blocks using blocks 1–4 of the locked schedule.
- Days 14–15: buffer.

With four pairs, emphasize plots and paired effect sizes. Do not call a result confirmatory, regardless of a p-value.

## Challenge standardization

Before the first randomized block, lock the challenge meal and do not optimize it using sensor feedback.

Record:

- first-bite timestamp to the nearest minute;
- every food and drink, brand or preparation method, and measured portion where practical;
- estimated carbohydrate, protein, fat, fiber, and calories;
- caffeine and alcohol during the prior 6 hours;
- medication and supplement timing without changing the regimen;
- exercise during the prior 3 hours and following 3 hours;
- previous meal time;
- sleep duration and subjective sleep quality;
- illness, unusual stress, and any relevant menstrual-cycle information the participant chooses to record;
- walking start and stop times, duration, and perceived intensity.

For control days, remain sedentary from first bite through 60 minutes after the meal except for ordinary essential movement. For walk days, begin the 10-minute walk at +20 minutes. Do not compensate with extra exercise during the remaining observation window.

## Outcomes

### Primary outcome

**Net iAUC from 0 to 120 minutes:**

1. Define baseline as the median valid sensor value from −15 through 0 minutes relative to first bite.
2. Linearly interpolate the glucose series to a regular 5-minute grid only across gaps no longer than 15 minutes.
3. Subtract baseline from each value.
4. Integrate the signed baseline-adjusted series from 0 to 120 minutes using the trapezoidal rule.

Signed area is primary so values below baseline are retained rather than selectively discarded.

### Secondary outcomes

- Positive iAUC from 0 to 120 minutes, truncating values below baseline at zero.
- Peak rise from baseline within 0–120 minutes.
- Time to peak.
- Glucose change at 120 minutes, using the closest value within ±10 minutes.
- Minutes above 140 mg/dL and above 180 mg/dL during 0–180 minutes, reported descriptively rather than as diagnostic thresholds.
- Premeal baseline glucose.
- Full-day mean glucose, standard deviation, coefficient of variation, and data completeness.
- Standard CGM time-in-range summaries when appropriate, clearly labeled as descriptive. Clinical CGM targets developed for people with diabetes are not diagnostic criteria for someone without diabetes.

## Data-quality and exclusion rules

A challenge is invalid only for a prespecified reason:

- fewer than 80% of expected readings from −30 to +180 minutes;
- no valid baseline readings in the −15-to-0-minute window;
- first-bite time uncertain by more than 5 minutes;
- challenge meal or portion materially differs from the locked meal;
- wrong randomized condition, walk starts more than 10 minutes from its planned time, or control activity is violated;
- acute illness, vomiting, fever, a new medication, or a medication-dose change;
- sensor failure, confirmed compression artifact, or a documented device problem.

Do not exclude a challenge merely because the glucose response is large, small, surprising, or unfavorable to the hypothesis. Preserve all raw rows and maintain a separate exclusion log with timestamps and reasons.

## Sensor-specific limitations

- Stelo measures interstitial rather than blood glucose, so rapid changes can appear later than blood-glucose changes.
- First-day readings may differ more from a blood-glucose meter.
- Pressure on the sensor can create apparent low readings; sleeping position and pressure should be logged when relevant.
- Signal loss and early sensor failure create nonrandom missingness. Report completeness by day and condition.
- One sensor is indicated for up to 15 days, but Dexcom reports that 77.9% lasted the full 15 days in its sensor-survival study. The buffer days are therefore part of the design, not optional cleanup.

## Data acquisition and provenance

1. Use a single Stelo/Dexcom account throughout the study.
2. Keep the Stelo app running and preserve event timestamps.
3. At the end of each sensor period, use Dexcom Clarity to export the raw glucose values and events as CSV.
4. Save each original CSV unchanged in a dated `raw/` folder. Never edit the raw export in place.
5. Save the contemporaneous study log separately.
6. Record file size, SHA-256 hash, export date, sensor start/end times, time zone, app version, and any clock changes.
7. Run analysis from scripted copies only. Every table and figure should be reproducible from the raw exports and locked log.

No personal CGM data should be uploaded to a shared cluster or repository until the participant has explicitly chosen the privacy boundary and identifiers have been removed.

## Statistical analysis plan

1. Parse and validate timestamps, units, duplicate rows, impossible ordering, and missing intervals.
2. Produce a CONSORT-style event flow: scheduled challenges, completed challenges, prespecified exclusions, replacements, and analyzed pairs.
3. Plot every challenge curve before aggregation, labeled by randomized condition and block.
4. Calculate outcomes with the locked definitions above.
5. Report every block's walk-minus-control difference.
6. Report the mean and median paired difference, range, and a bootstrap confidence interval labeled exploratory.
7. Use an exact paired randomization test across the six blocks as a secondary analysis. With only six pairs, power is low and the smallest attainable two-sided p-value is limited; interpretation must prioritize effect size, consistency, and uncertainty.
8. Run sensitivity analyses using positive iAUC, 180-minute windows, and complete observed readings without interpolation.
9. Do not search many meal windows, thresholds, or subgroups and then present the best-looking result as prespecified. Any post hoc analysis is labeled exploratory.

## Interpretation rules

- A consistent negative paired effect supports a short-term within-person effect of this specific walking routine after this specific meal during this study period.
- An inconsistent or imprecise effect is inconclusive, not proof of no effect.
- A favorable glucose curve does not establish that a food is “healthy,” that a behavior prevents diabetes, or that long-term outcomes improve.
- A single person's result does not estimate a population treatment effect.
- Unexpectedly high or low readings are reported as observations, not diagnoses, and are handled according to device instructions and clinical advice.

## Planned deliverables after data export

- immutable raw-data manifest with hashes;
- cleaned analysis dataset and exclusion log;
- paired meal-response figure with all individual curves;
- daily glucose and completeness summaries;
- primary and sensitivity-analysis table;
- concise report separating prespecified from exploratory findings;
- reproducible analysis script and environment record.

## Sources informing device and metric handling

- [FDA decision summary for Stelo](https://www.accessdata.fda.gov/cdrh_docs/reviews/K234070.pdf)
- [FDA announcement of OTC clearance](https://www.fda.gov/news-events/press-announcements/fda-clears-first-over-counter-continuous-glucose-monitor)
- [Dexcom Stelo sensor-wear information](https://www.stelo.com/faqs/using-stelo/how-long-can-i-wear-my-stelo-glucose-biosensor)
- [Dexcom guidance on sensor and blood-glucose differences](https://www.stelo.com/en-us/faqs/troubleshooting/what-should-i-do-if-my-glucose-readings-seem-inaccurate)
- [Dexcom Clarity raw CSV export documentation](https://productstore.clarity.dexcom.com/Documentation/en/Dexcom_Clarity_User_Guide_Home_User.pdf)
- [ADA Standards of Care 2026: glycemic goals and CGM metrics](https://diabetesjournals.org/care/article/49/Supplement_1/S132/163927/6-Glycemic-Goals-Hypoglycemia-and-Hyperglycemic)
