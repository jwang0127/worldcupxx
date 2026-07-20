# Settlement Methodology

## Metric definitions

Use the 90-minute score for every accuracy metric, including knockout matches. Store extra-time score, penalties, and advancement separately.

| Metric | Prediction used | Hit rule |
|---|---|---|
| Total goals | Published core value or explicit interval | Actual 90-minute total equals the value or falls inside the interval |
| Main score | First pre-match score only | Exact 90-minute score equality |
| Score pool | First three distinct pre-match scores | Actual 90-minute score appears in the ranked top three |
| Win/draw/loss | Direction mapped from the single main score | Exact home/draw/away equality |

Do not let candidate totals, an unranked full score pool, “防平”, double chance, or advancement direction inflate a primary hit rate.

## Joining records

Prefer a stable provider match ID. Otherwise use tournament match number plus teams and kickoff. A lottery match number can repeat on different business dates, so never use that number alone across dates.

Keep the latest snapshot that is demonstrably pre-kickoff. Reject post-match edits as prediction evidence. When daily and knockout records disagree, preserve both raw sources and document which field won and why.

## Coverage and denominators

Publish these counts separately:

1. total tournament matches;
2. matches with a frozen pre-match prediction and verified result;
3. missing or unresolved pre-match archives;
4. raw settled predictions;
5. calibration samples after pre-declared exclusions.

An exclusion never removes the row from the page. Show its result and misses, then exclude it only from calibration metrics. Do not invent exclusions after seeing an extreme score.

## Review hierarchy

Diagnose errors in this order:

1. schedule or team mapping;
2. settlement basis (90 minutes versus advancement);
3. single win/draw/loss calibration;
4. total-goal core and interval width;
5. main-score ordering;
6. top-three score-pool composition;
7. tail-risk explanations.

Convert observations into conditional rules such as resilient-underdog draws, weak-side first goals, favorite clean sheets, low-price away blowouts, and late-chase score expansion. Never extrapolate “yesterday was big/small” as a global rule.

## Output integrity

The JSON is the canonical artifact. The HTML must show identical counts and rates. Include every settled row, mark exclusions, link result sources, and preserve the entertainment-analysis disclaimer.

