from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from eagles_ml.features import default_feature_names
from eagles_ml.model import brier_score, fit_sklearn_classifier, log_loss

MODEL_NAMES = ["elo", "logistic_regression", "hist_gradient_boosting"]


@dataclass(frozen=True)
class EvaluationResult:
    metrics: pd.DataFrame
    predictions: pd.DataFrame
    calibration: pd.DataFrame
    best_model: str
    feature_names: list[str]


def season_forward_evaluation(
    frame: pd.DataFrame,
    *,
    first_test_season: int = 2018,
    last_test_season: int | None = None,
    model_names: list[str] | None = None,
) -> EvaluationResult:
    """Evaluate models by training on earlier seasons and testing on one future season."""
    if frame.empty:
        raise ValueError("Cannot evaluate an empty feature table.")
    required = {"season", "home_win", "home_elo_prob"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required evaluation columns: {sorted(missing)}")

    models = model_names or MODEL_NAMES
    seasons = sorted(int(season) for season in frame["season"].dropna().unique())
    if not seasons:
        raise ValueError("No seasons found in feature table.")
    last = max(seasons) if last_test_season is None else last_test_season
    test_seasons = [season for season in seasons if first_test_season <= season <= last]
    if not test_seasons:
        raise ValueError(
            f"No test seasons found between {first_test_season} and {last}; "
            f"available seasons: {min(seasons)}-{max(seasons)}"
        )

    feature_names = default_feature_names(frame)
    metrics_rows: list[dict[str, object]] = []
    prediction_rows: list[pd.DataFrame] = []

    for season in test_seasons:
        train = frame[frame["season"] < season].copy()
        test = frame[frame["season"] == season].copy()
        if train.empty or test.empty:
            continue
        y_true = test["home_win"].to_numpy(dtype=float)
        for model_name in models:
            probabilities = _predict_model(model_name, train, test, feature_names)
            metrics_rows.append(
                {
                    "model": model_name,
                    "season": season,
                    "games": len(test),
                    "brier": brier_score(y_true, probabilities),
                    "log_loss": log_loss(y_true, probabilities),
                    "accuracy": float(np.mean((probabilities >= 0.5) == y_true)),
                }
            )
            output_columns = ["season", "week", "game_id", "home_team", "away_team", "home_win"]
            output = test[[column for column in output_columns if column in test.columns]].copy()
            output["model"] = model_name
            output["predicted_home_win_probability"] = probabilities
            prediction_rows.append(output)

    metrics = pd.DataFrame(metrics_rows)
    if metrics.empty:
        raise ValueError("Evaluation produced no metric rows.")
    predictions = pd.concat(prediction_rows, ignore_index=True)
    calibration = build_calibration_table(predictions)
    best_model = (
        metrics.groupby("model")["brier"].mean().sort_values(kind="mergesort").index[0]
    )
    return EvaluationResult(
        metrics=metrics,
        predictions=predictions,
        calibration=calibration,
        best_model=str(best_model),
        feature_names=feature_names,
    )


def build_calibration_table(predictions: pd.DataFrame, *, bucket_count: int = 10) -> pd.DataFrame:
    frame = predictions.copy()
    probabilities = frame["predicted_home_win_probability"].clip(0.0, 0.999999)
    bucket_index = np.floor(probabilities * bucket_count).astype(int)
    frame["bucket_low"] = bucket_index / bucket_count
    frame["bucket_high"] = (bucket_index + 1) / bucket_count
    grouped = (
        frame.groupby(["model", "bucket_low", "bucket_high"], as_index=False)
        .agg(
            games=("home_win", "size"),
            mean_predicted_probability=("predicted_home_win_probability", "mean"),
            actual_home_win_rate=("home_win", "mean"),
        )
        .sort_values(["model", "bucket_low"])
    )
    grouped["bucket"] = grouped.apply(
        lambda row: f"{row['bucket_low']:.1f}-{row['bucket_high']:.1f}",
        axis=1,
    )
    return grouped[
        [
            "model",
            "bucket",
            "bucket_low",
            "bucket_high",
            "games",
            "mean_predicted_probability",
            "actual_home_win_rate",
        ]
    ]


def write_evaluation_artifacts(
    result: EvaluationResult,
    *,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    result.metrics.to_csv(output_dir / "model_metrics.csv", index=False)
    result.predictions.to_csv(output_dir / "validation_predictions.csv", index=False)
    result.calibration.to_csv(output_dir / "calibration.csv", index=False)


def metric_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    return (
        metrics.groupby("model", as_index=False)
        .agg(
            seasons=("season", "nunique"),
            games=("games", "sum"),
            brier=("brier", "mean"),
            log_loss=("log_loss", "mean"),
            accuracy=("accuracy", "mean"),
        )
        .sort_values("brier", kind="mergesort")
    )


def _predict_model(
    model_name: str,
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_names: list[str],
) -> np.ndarray:
    if model_name == "elo":
        return test["home_elo_prob"].to_numpy(dtype=float).clip(1e-6, 1.0 - 1e-6)
    classifier = fit_sklearn_classifier(model_name, train, feature_names=feature_names)
    probabilities = classifier.predict_proba(test[feature_names])[:, 1]
    return probabilities.clip(1e-6, 1.0 - 1e-6)
