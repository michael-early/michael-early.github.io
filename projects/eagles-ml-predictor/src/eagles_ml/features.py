from __future__ import annotations

from collections import defaultdict, deque

import numpy as np
import pandas as pd

from eagles_ml.elo import DEFAULT_ELO, win_probability_from_diff


def build_historical_game_features(schedules: pd.DataFrame) -> pd.DataFrame:
    """Create leak-free pregame features from an nflverse-style schedule table.

    Expected columns include season, week, home_team, away_team, home_score, away_score.
    Optional columns such as spread_line, home_rest, away_rest, roof, temp, and wind are used
    when present. Rows are updated chronologically so each game sees only earlier games.
    """
    required = {"season", "week", "home_team", "away_team", "home_score", "away_score"}
    missing = required - set(schedules.columns)
    if missing:
        raise ValueError(f"Missing required schedule columns: {sorted(missing)}")

    games = schedules.copy()
    if "game_type" in games.columns:
        games = games[games["game_type"].fillna("REG") == "REG"]
    sort_cols = [col for col in ["season", "week", "gameday", "game_id"] if col in games.columns]
    games = games.dropna(subset=["home_score", "away_score"]).sort_values(sort_cols)

    ratings = defaultdict(lambda: DEFAULT_ELO)
    recent_margin: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=8))
    recent_wins: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=8))
    rows: list[dict[str, float | int | str]] = []

    for _, game in games.iterrows():
        home = game["home_team"]
        away = game["away_team"]
        home_score = float(game["home_score"])
        away_score = float(game["away_score"])
        home_rating = ratings[home]
        away_rating = ratings[away]
        home_elo_diff = home_rating - away_rating
        home_win = float(home_score > away_score)

        row = {
            "season": int(game["season"]),
            "week": int(game["week"]),
            "game_id": game.get("game_id", ""),
            "gameday": game.get("gameday", ""),
            "home_team": home,
            "away_team": away,
            "home_win": home_win,
            "home_margin": home_score - away_score,
            "home_elo_diff": home_elo_diff,
            "home_elo_prob": win_probability_from_diff(home_elo_diff + 55.0),
            "home_recent_margin": _mean_or_zero(recent_margin[home]),
            "away_recent_margin": _mean_or_zero(recent_margin[away]),
            "home_recent_win_rate": _mean_or_half(recent_wins[home]),
            "away_recent_win_rate": _mean_or_half(recent_wins[away]),
            "rest_diff": _value_or_default(game.get("home_rest", 7), 7)
            - _value_or_default(game.get("away_rest", 7), 7),
            "spread_line": float(game.get("spread_line", np.nan)),
            "total_line": float(game.get("total_line", np.nan)),
            "temp": float(game.get("temp", np.nan)),
            "wind": float(game.get("wind", np.nan)),
            "div_game": float(game.get("div_game", 0) or 0),
        }
        rows.append(row)

        margin = home_score - away_score
        expected = win_probability_from_diff(home_elo_diff + 55.0)
        k = 20.0 * np.log1p(abs(margin))
        ratings[home] += k * (home_win - expected)
        ratings[away] += k * ((1.0 - home_win) - (1.0 - expected))
        recent_margin[home].append(margin)
        recent_margin[away].append(-margin)
        recent_wins[home].append(home_win)
        recent_wins[away].append(1.0 - home_win)

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["recent_margin_diff"] = frame["home_recent_margin"] - frame["away_recent_margin"]
    frame["recent_win_rate_diff"] = frame["home_recent_win_rate"] - frame["away_recent_win_rate"]
    return frame


def default_feature_names(frame: pd.DataFrame) -> list[str]:
    candidates = [
        "home_elo_diff",
        "home_elo_prob",
        "recent_margin_diff",
        "recent_win_rate_diff",
        "rest_diff",
        "spread_line",
        "total_line",
        "temp",
        "wind",
        "div_game",
    ]
    return [name for name in candidates if name in frame.columns and not frame[name].isna().all()]


def _mean_or_zero(values: deque[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _mean_or_half(values: deque[float]) -> float:
    return float(np.mean(values)) if values else 0.5


def _value_or_default(value: object, default: float) -> float:
    if value is None or pd.isna(value):
        return float(default)
    return float(value)
