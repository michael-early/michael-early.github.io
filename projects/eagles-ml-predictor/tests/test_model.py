import pandas as pd
import pytest

from eagles_ml.features import build_historical_game_features, default_feature_names
from eagles_ml.model import brier_score, fit_logistic_game_model


def test_logistic_model_fits_small_synthetic_schedule() -> None:
    schedules = pd.DataFrame(
        [
            {
                "season": 2024,
                "week": 1,
                "home_team": "A",
                "away_team": "B",
                "home_score": 28,
                "away_score": 17,
                "spread_line": -3.5,
            },
            {
                "season": 2024,
                "week": 2,
                "home_team": "B",
                "away_team": "A",
                "home_score": 14,
                "away_score": 24,
                "spread_line": 2.5,
            },
            {
                "season": 2024,
                "week": 3,
                "home_team": "A",
                "away_team": "C",
                "home_score": 31,
                "away_score": 10,
                "spread_line": -7.0,
            },
            {
                "season": 2024,
                "week": 4,
                "home_team": "C",
                "away_team": "B",
                "home_score": 20,
                "away_score": 21,
                "spread_line": 1.0,
            },
        ]
    )
    features = build_historical_game_features(schedules)
    names = default_feature_names(features)
    model = fit_logistic_game_model(features, feature_names=names, target_name="home_win")
    probabilities = model.predict_proba(features)
    assert len(probabilities) == len(features)
    assert 0 <= brier_score(features["home_win"].to_numpy(), probabilities) <= 1


def test_feature_generation_uses_only_prior_games_for_rolling_features() -> None:
    schedules = pd.DataFrame(
        [
            {
                "season": 2024,
                "week": 1,
                "home_team": "A",
                "away_team": "B",
                "home_score": 40,
                "away_score": 0,
            },
            {
                "season": 2024,
                "week": 2,
                "home_team": "A",
                "away_team": "B",
                "home_score": 10,
                "away_score": 20,
            },
        ]
    )
    features = build_historical_game_features(schedules)
    first_game = features.iloc[0]
    second_game = features.iloc[1]
    assert first_game["home_recent_margin"] == 0
    assert first_game["away_recent_margin"] == 0
    assert first_game["home_recent_win_rate"] == 0.5
    assert second_game["home_recent_margin"] == 40
    assert second_game["away_recent_margin"] == -40


def test_sklearn_classifier_fits_when_dependency_is_installed() -> None:
    pytest.importorskip("sklearn")
    from eagles_ml.model import fit_sklearn_classifier

    schedules = pd.DataFrame(
        [
            {
                "season": 2021,
                "week": 1,
                "home_team": "A",
                "away_team": "B",
                "home_score": 28,
                "away_score": 17,
            },
            {
                "season": 2021,
                "week": 2,
                "home_team": "B",
                "away_team": "A",
                "home_score": 14,
                "away_score": 24,
            },
            {
                "season": 2021,
                "week": 3,
                "home_team": "A",
                "away_team": "C",
                "home_score": 31,
                "away_score": 10,
            },
            {
                "season": 2021,
                "week": 4,
                "home_team": "C",
                "away_team": "B",
                "home_score": 20,
                "away_score": 21,
            },
        ]
    )
    features = build_historical_game_features(schedules)
    names = default_feature_names(features)
    classifier = fit_sklearn_classifier("logistic_regression", features, feature_names=names)
    probabilities = classifier.predict_proba(features[names])
    assert probabilities.shape == (4, 2)
