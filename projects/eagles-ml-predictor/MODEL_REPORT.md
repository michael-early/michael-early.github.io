# NFL Game Prediction Model Report

## Headline

This project evaluates NFL game prediction models with season-forward validation and uses the
best-calibrated approach to produce a 2026 Philadelphia Eagles forecast.

Best model by average Brier score: `logistic_regression`.

## Dataset

- Historical feature table: `data/processed/historical_games.csv`
- Validation seasons: 2018-2025
- Feature columns: `home_elo_diff`, `home_elo_prob`, `recent_margin_diff`, `recent_win_rate_diff`, `rest_diff`, `spread_line`, `total_line`, `temp`, `wind`, `div_game`

Features are built from pregame state only. Team ratings and rolling form are updated after each
game, so each row uses information that would have been available before kickoff.

## Model Comparison

| model | seasons | games | brier | log_loss | accuracy |
| --- | --- | --- | --- | --- | --- |
| logistic_regression | 8 | 2127 | 0.2111 | 0.6100 | 0.6642 |
| hist_gradient_boosting | 8 | 2127 | 0.2210 | 0.6372 | 0.6538 |
| elo | 8 | 2127 | 0.2312 | 0.6629 | 0.6357 |

## Validation Method

The evaluation uses season-forward validation. For each test season, models train on all earlier
seasons and predict that season's games. This better matches real forecasting than a random split,
which can leak future football context into training.

Primary metrics:

- Brier score: probability error, lower is better.
- Log loss: punishes overconfident misses, lower is better.
- Accuracy: simple win/loss hit rate, useful but secondary.
- Calibration: compares predicted probabilities to actual win rates by bucket.

## 2026 Eagles Forecast

The Eagles forecast is written to `outputs/eagles_2026_predictions.csv`. The selected model
currently projects a 9-8 record. It remains a preseason projection until 2026 injuries, market
lines, and current-season performance data are available.

## Limitations

- The current feature set is schedule-based and market-aware when spread lines exist; it does not
  yet include injuries, depth charts, or quarterback availability.
- Weather is used only when present in the source schedule data.
- Betting-market lines are useful predictors, but this project is designed as a Data/ML portfolio
  system, not betting advice.
