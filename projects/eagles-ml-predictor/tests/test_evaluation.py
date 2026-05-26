import pandas as pd
import pytest

from eagles_ml.evaluation import MODEL_NAMES, season_forward_evaluation
from eagles_ml.features import build_historical_game_features


def test_evaluation_produces_metrics_for_each_model_and_season() -> None:
    pytest.importorskip("sklearn")
    schedules = _synthetic_multi_season_schedule()
    features = build_historical_game_features(schedules)
    result = season_forward_evaluation(features, first_test_season=2022, last_test_season=2023)
    assert set(result.metrics["model"]) == set(MODEL_NAMES)
    assert set(result.metrics["season"]) == {2022, 2023}
    assert result.metrics["brier"].between(0, 1).all()
    assert not result.calibration.empty


def _synthetic_multi_season_schedule() -> pd.DataFrame:
    rows = []
    teams = ["A", "B", "C", "D"]
    for season in [2020, 2021, 2022, 2023]:
        for week in range(1, 7):
            home = teams[(week + season) % len(teams)]
            away = teams[(week + season + 1) % len(teams)]
            home_is_stronger = home in {"A", "B"}
            rows.append(
                {
                    "season": season,
                    "week": week,
                    "game_id": f"{season}_{week}",
                    "home_team": home,
                    "away_team": away,
                    "home_score": 27 if home_is_stronger else 17,
                    "away_score": 17 if home_is_stronger else 24,
                    "spread_line": -3.0 if home_is_stronger else 2.5,
                    "total_line": 44.5,
                    "home_rest": 7,
                    "away_rest": 7,
                    "div_game": int({home, away} <= {"A", "B"}),
                }
            )
    return pd.DataFrame(rows)
