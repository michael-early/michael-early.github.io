# Research Notes

This project predicts Eagles game outcomes as probabilities first and winner labels second.
Accuracy alone is not enough for NFL games because a 52% pick and an 80% pick should not be
treated the same.

## Data Sources

- Official 2026 Eagles schedule: Philadelphia Eagles schedule-release article, published
  May 14, 2026.
- Historical training data: `nfl_data_py`, which exposes nflfastR/nflverse schedules,
  play-by-play, scoring lines, rosters, and team metadata.
- Model-feature foundation: nflfastR/nflverse play-by-play data, including EPA, CPOE,
  win-probability, schedule, and scoring-line fields.

## Modeling Decision

Use a two-layer approach:

1. Elo-style baseline for preseason predictions.
2. Logistic probability model trained on historical games once nflverse schedules are fetched.

The logistic model is deliberately the first ML model because football has a small sample size,
strong year-to-year noise, and many correlated features. Research on open NFL win-probability
models shows that simple logistic models can be well calibrated and that more complex non-linear
models do not automatically improve results. The baseline remains useful because it is transparent
and robust when current-season data is thin.

Gradient-boosted trees are a strong candidate for a later second model after there is enough
feature coverage and a strict time-split validation setup. They can capture non-linear
interactions, but they also need calibration checks and careful leakage control.

## Best Variables To Prioritize

- Market expectation: closing spread and total when available.
- Team strength: Elo, rolling point differential, rolling win rate, rolling EPA/play.
- Offense and defense split strength: offensive EPA, defensive EPA allowed, success rate,
  early-down efficiency, explosive-play rate.
- Quarterback context: starter continuity, QB EPA/CPOE, injuries, and depth-chart changes.
- Rest and travel: rest-day differential, short week, long road travel, international games.
- Venue and environment: home field, dome/outdoor, temperature, wind, precipitation where present.
- Schedule context: divisional familiarity, bye week, late-season rest/starter uncertainty.

## Validation Method

Use season-forward validation, not random splits. A proper evaluation trains on earlier seasons
and tests on later seasons to mimic the actual forecasting problem.

Primary metrics:

- Brier score for probability quality.
- Log loss for punishing overconfident misses.
- Calibration by probability bucket.
- Accuracy only as a secondary, reader-friendly summary.

## Current Prediction Caveat

The included prediction table is a preseason prior because the 2026 season has not been played.
It uses 2025 records, home field, neutral-site/travel penalties, and schedule context. Refresh it
after installing `nfl-data-py` and fetching nflverse schedules, then add market lines as they
become available.

## Source Links

- Official Eagles schedule: https://www.philadelphiaeagles.com/news/eagles-schedule-release-2026
- nfl-data-py: https://pypi.org/project/nfl-data-py/
- nflfastR win probability: https://nflfastr.com/reference/calculate_win_probability.html
- nfelo model overview: https://www.nfeloapp.com/about/
- Open Source Football logistic model example:
  https://opensourcefootball.com/posts/2021-01-21-nfl-game-prediction-using-logistic-regression/
- iWinRNFL paper: https://arxiv.org/abs/1704.00197
