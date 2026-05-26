# Portfolio Positioning

## GitHub Repository Description

End-to-end NFL game prediction system with leak-free feature engineering, season-forward model
validation, calibration analysis, and a Streamlit dashboard featuring the 2026 Eagles forecast.

## Suggested GitHub Topics

```text
machine-learning
sports-analytics
nfl
scikit-learn
streamlit
python
calibration
portfolio-project
```

## Resume Version

**Project title:** NFL Game Prediction and Calibration System

**Short description:** Built a reusable NFL win-probability pipeline that ingests historical
nflverse schedules, engineers leak-free pregame features, compares baseline and ML models with
season-forward validation, and presents 2026 Eagles predictions in a Streamlit dashboard.

**Bullet options:**

- Built an end-to-end NFL win-probability system in Python using nflverse data, leak-free rolling
  features, season-forward validation, and calibrated probability evaluation.
- Benchmarked Elo, logistic regression, and histogram gradient boosting across 2,127 validation
  games, selecting logistic regression by average Brier score and reporting log loss, accuracy, and
  calibration buckets.
- Developed a Streamlit dashboard and model report that communicate model performance,
  game-by-game 2026 Eagles probabilities, feature rationale, and forecast limitations.

## LinkedIn / Portfolio Summary

I built an NFL game prediction system focused on calibrated probabilities instead of only win/loss
picks. The project uses historical nflverse data, leak-free pregame features, season-forward
validation, and model comparison across Elo, logistic regression, and histogram gradient boosting.
The final artifact is a local Streamlit dashboard that presents model metrics, calibration, and a
2026 Eagles forecast.

## GitHub Upload Checklist

1. Create a new GitHub repository named `nfl-game-prediction-system` or
   `eagles-ml-predictor`.
2. Initialize Git locally if needed:

   ```bash
   git init
   git add .
   git commit -m "Initial NFL prediction portfolio project"
   ```

3. Add the GitHub remote:

   ```bash
   git remote add origin git@github.com:<your-username>/<repo-name>.git
   git branch -M main
   git push -u origin main
   ```

4. Confirm GitHub Actions passes.
5. Add the dashboard screenshot from `outputs/dashboard_screenshot.png` to the README preview.
6. Pin the repository on your GitHub profile.

## Interview Talking Points

- Why season-forward validation is better than random splits for sports forecasting.
- How leakage can enter sports prediction datasets and how this project avoids it.
- Why Brier score and calibration matter when the output is a probability.
- Why Elo remains useful as a transparent baseline even after adding ML models.
- What features you would add next: injuries, quarterback availability, EPA/play, depth charts,
  and current betting-market movement.
