from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from eagles_ml.elo import (
    Matchup,
    prior_elo_from_record,
    smoothed_win_pct,
    win_probability_from_diff,
)
from eagles_ml.features import default_feature_names
from eagles_ml.model import fit_sklearn_classifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEDULE_PATH = PROJECT_ROOT / "data" / "processed" / "eagles_2026_schedule.csv"
DEFAULT_PRIORS_PATH = PROJECT_ROOT / "data" / "processed" / "team_priors_2026.csv"


def load_schedule(path: Path = DEFAULT_SCHEDULE_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def load_priors(path: Path = DEFAULT_PRIORS_PATH) -> pd.DataFrame:
    priors = pd.read_csv(path)
    priors["prior_elo"] = priors.apply(
        lambda row: prior_elo_from_record(row["wins"], row["losses"], row.get("ties", 0)),
        axis=1,
    )
    return priors


def _situational_adjustment(row: pd.Series) -> float:
    notes = str(row.get("notes", "")).lower()
    adjustment = 0.0
    if row["site"] == "neutral" and "london" in notes:
        adjustment -= 12.0
    if "thanksgiving" in notes and row["site"] == "away":
        adjustment -= 8.0
    if "thursday" in notes:
        adjustment -= 5.0
    if "date/time tbd" in notes:
        adjustment -= 2.0
    return adjustment


def project_eagles_games(
    schedule: pd.DataFrame | None = None,
    priors: pd.DataFrame | None = None,
) -> pd.DataFrame:
    schedule = load_schedule() if schedule is None else schedule.copy()
    priors = load_priors() if priors is None else priors.copy()
    ratings = priors.set_index("team")["prior_elo"].to_dict()

    eagles_rating = ratings["PHI"]
    rows: list[dict[str, object]] = []
    for _, game in schedule.iterrows():
        if game["site"] == "bye":
            continue
        opponent = game["opponent"]
        matchup = Matchup(
            team_rating=eagles_rating,
            opponent_rating=ratings[opponent],
            site=game["site"],
            situational_elo=_situational_adjustment(game),
        )
        probability = matchup.team_probability()
        rows.append(
            {
                "week": game["week"],
                "date": game["date"],
                "time_et": game["time_et"],
                "opponent": opponent,
                "site": game["site"],
                "venue": game["venue"],
                "network": game["network"],
                "notes": game["notes"],
                "eagles_win_probability": round(probability, 3),
                "projected_result": "W" if probability >= 0.5 else "L",
                "confidence_band": confidence_band(probability),
            }
        )
    return pd.DataFrame(rows)


def project_eagles_games_with_model(
    historical_features: pd.DataFrame,
    *,
    model_name: str,
    schedule: pd.DataFrame | None = None,
    priors: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Train an ML model on historical rows and apply it to the 2026 Eagles schedule."""
    if model_name == "elo":
        predictions = project_eagles_games(schedule=schedule, priors=priors)
        predictions["model_used"] = "elo"
        return predictions

    schedule = load_schedule() if schedule is None else schedule.copy()
    priors = load_priors() if priors is None else priors.copy()
    feature_names = default_feature_names(historical_features)
    model = fit_sklearn_classifier(model_name, historical_features, feature_names=feature_names)
    future = build_2026_model_feature_frame(
        schedule=schedule,
        priors=priors,
        feature_names=feature_names,
    )
    home_probabilities = model.predict_proba(future[feature_names])[:, 1]
    eagles_probabilities = [
        probability if bool(row["eagles_is_home_team"]) else 1.0 - probability
        for probability, (_, row) in zip(home_probabilities, future.iterrows(), strict=True)
    ]

    baseline = project_eagles_games(schedule=schedule, priors=priors)
    baseline["eagles_win_probability"] = [
        round(float(probability), 3) for probability in eagles_probabilities
    ]
    baseline["projected_result"] = [
        "W" if probability >= 0.5 else "L" for probability in eagles_probabilities
    ]
    baseline["confidence_band"] = [
        confidence_band(float(probability)) for probability in eagles_probabilities
    ]
    baseline["model_used"] = model_name
    return baseline


def build_2026_model_feature_frame(
    *,
    schedule: pd.DataFrame,
    priors: pd.DataFrame,
    feature_names: list[str],
) -> pd.DataFrame:
    ratings = priors.set_index("team")["prior_elo"].to_dict()
    records = priors.set_index("team")[["wins", "losses", "ties"]].to_dict("index")
    rows: list[dict[str, object]] = []
    for _, game in schedule.iterrows():
        if game["site"] == "bye":
            continue
        opponent = game["opponent"]
        if game["site"] == "home":
            home_team = "PHI"
            away_team = opponent
            eagles_is_home_team = True
            home_field = 55.0
        elif game["site"] == "away":
            home_team = opponent
            away_team = "PHI"
            eagles_is_home_team = False
            home_field = 55.0
        else:
            home_team = opponent
            away_team = "PHI"
            eagles_is_home_team = False
            home_field = 0.0

        home_elo_diff = ratings[home_team] - ratings[away_team]
        home_record = records[home_team]
        away_record = records[away_team]
        row = {
            "season": 2026,
            "week": int(game["week"]),
            "home_team": home_team,
            "away_team": away_team,
            "eagles_is_home_team": eagles_is_home_team,
            "home_elo_diff": home_elo_diff,
            "home_elo_prob": win_probability_from_diff(home_elo_diff + home_field),
            "home_recent_margin": _record_margin_prior(home_record),
            "away_recent_margin": _record_margin_prior(away_record),
            "home_recent_win_rate": smoothed_win_pct(**home_record),
            "away_recent_win_rate": smoothed_win_pct(**away_record),
            "rest_diff": 0.0,
            "spread_line": np.nan,
            "total_line": np.nan,
            "temp": np.nan,
            "wind": np.nan,
            "div_game": 1.0 if opponent in {"DAL", "NYG", "WAS"} else 0.0,
        }
        row["recent_margin_diff"] = row["home_recent_margin"] - row["away_recent_margin"]
        row["recent_win_rate_diff"] = row["home_recent_win_rate"] - row["away_recent_win_rate"]
        for feature_name in feature_names:
            row.setdefault(feature_name, np.nan)
        rows.append(row)
    return pd.DataFrame(rows)


def confidence_band(probability: float) -> str:
    edge = abs(probability - 0.5)
    if edge < 0.035:
        return "coin-flip"
    if edge < 0.085:
        return "lean"
    if edge < 0.15:
        return "moderate"
    return "strong"


def _record_margin_prior(record: dict[str, float]) -> float:
    return float(record["wins"] - record["losses"]) / 17.0 * 7.0
