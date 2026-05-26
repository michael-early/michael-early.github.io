from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from eagles_ml.data_sources import save_schedules
from eagles_ml.evaluation import (
    metric_summary,
    season_forward_evaluation,
    write_evaluation_artifacts,
)
from eagles_ml.features import build_historical_game_features, default_feature_names
from eagles_ml.model import brier_score, fit_logistic_game_model, log_loss
from eagles_ml.projections import project_eagles_games, project_eagles_games_with_model
from eagles_ml.reporting import write_charts, write_model_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict the 2026 Philadelphia Eagles season.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    predict_parser = subparsers.add_parser("predict", help="Write Eagles 2026 predictions.")
    predict_parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/eagles_2026_predictions.csv"),
    )

    fetch_parser = subparsers.add_parser("fetch-schedules", help="Fetch nflverse schedules.")
    fetch_parser.add_argument("--start", type=int, default=1999)
    fetch_parser.add_argument("--end", type=int, default=2025)
    fetch_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/nflverse_schedules.csv"),
    )

    train_parser = subparsers.add_parser("train", help="Train/evaluate a logistic game model.")
    train_parser.add_argument("--schedules", type=Path, required=True)

    dataset_parser = subparsers.add_parser(
        "build-dataset",
        help="Fetch schedules and build a leak-free historical feature table.",
    )
    dataset_parser.add_argument("--start", type=int, default=1999)
    dataset_parser.add_argument("--end", type=int, default=2025)
    dataset_parser.add_argument(
        "--input-schedules",
        type=Path,
        help="Use an existing nflverse schedules CSV instead of fetching.",
    )
    dataset_parser.add_argument(
        "--raw-output",
        type=Path,
        default=Path("data/raw/nflverse_schedules.csv"),
    )
    dataset_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/historical_games.csv"),
    )

    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Run season-forward model comparison and write portfolio artifacts.",
    )
    evaluate_parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/processed/historical_games.csv"),
    )
    evaluate_parser.add_argument("--first-test-season", type=int, default=2018)
    evaluate_parser.add_argument("--last-test-season", type=int)
    evaluate_parser.add_argument("--output-dir", type=Path, default=Path("outputs"))

    portfolio_predict_parser = subparsers.add_parser(
        "predict-2026",
        help="Write 2026 Eagles predictions with the selected portfolio model.",
    )
    portfolio_predict_parser.add_argument(
        "--model",
        choices=["best", "elo", "logistic_regression", "hist_gradient_boosting"],
        default="best",
    )
    portfolio_predict_parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/processed/historical_games.csv"),
    )
    portfolio_predict_parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("outputs/model_metrics.csv"),
    )
    portfolio_predict_parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/eagles_2026_predictions.csv"),
    )

    args = parser.parse_args()
    if args.command == "predict":
        output_path: Path = args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        predictions = project_eagles_games()
        predictions.to_csv(output_path, index=False)
        print(f"Wrote {len(predictions)} predictions to {output_path}")
    elif args.command == "fetch-schedules":
        years = list(range(args.start, args.end + 1))
        path = save_schedules(years, args.output)
        print(f"Wrote schedules for {args.start}-{args.end} to {path}")
    elif args.command == "train":
        schedules = pd.read_csv(args.schedules)
        features = build_historical_game_features(schedules)
        feature_names = default_feature_names(features)
        model = fit_logistic_game_model(
            features,
            feature_names=feature_names,
            target_name="home_win",
        )
        probabilities = model.predict_proba(features)
        y = features["home_win"].to_numpy(dtype=float)
        print(f"Rows: {len(features)}")
        print(f"Features: {', '.join(feature_names)}")
        print(f"Brier: {brier_score(y, probabilities):.4f}")
        print(f"Log loss: {log_loss(y, probabilities):.4f}")
    elif args.command == "build-dataset":
        if args.input_schedules:
            schedules = pd.read_csv(args.input_schedules)
        else:
            years = list(range(args.start, args.end + 1))
            save_schedules(years, args.raw_output)
            schedules = pd.read_csv(args.raw_output)
        features = build_historical_game_features(schedules)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        features.to_csv(args.output, index=False)
        print(f"Wrote {len(features)} historical feature rows to {args.output}")
    elif args.command == "evaluate":
        dataset = pd.read_csv(args.dataset)
        result = season_forward_evaluation(
            dataset,
            first_test_season=args.first_test_season,
            last_test_season=args.last_test_season,
        )
        write_evaluation_artifacts(result, output_dir=args.output_dir)
        write_charts(result, output_dir=args.output_dir)
        predictions_path = args.output_dir / "eagles_2026_predictions.csv"
        write_model_report(
            result,
            output_path=Path("MODEL_REPORT.md"),
            dataset_path=args.dataset,
            predictions_path=predictions_path,
        )
        print(metric_summary(result.metrics).to_string(index=False))
        print(f"Best model by Brier score: {result.best_model}")
        print("Wrote metrics, calibration, charts, and MODEL_REPORT.md")
    elif args.command == "predict-2026":
        model_name = _resolve_model_name(args.model, args.metrics)
        if model_name == "elo" or not args.dataset.exists():
            predictions = project_eagles_games()
            predictions["model_used"] = "elo"
            if args.model != "elo" and not args.dataset.exists():
                print(
                    f"Historical dataset not found at {args.dataset}; "
                    "using Elo preseason baseline."
                )
        else:
            dataset = pd.read_csv(args.dataset)
            predictions = project_eagles_games_with_model(dataset, model_name=model_name)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        predictions.to_csv(args.output, index=False)
        wins = int((predictions["projected_result"] == "W").sum())
        losses = int((predictions["projected_result"] == "L").sum())
        print(f"Wrote {len(predictions)} predictions to {args.output}")
        print(f"Projected record: {wins}-{losses}")
        print(f"Model used: {predictions['model_used'].iloc[0]}")

def _resolve_model_name(requested: str, metrics_path: Path) -> str:
    if requested != "best":
        return requested
    if not metrics_path.exists():
        return "elo"
    metrics = pd.read_csv(metrics_path)
    if metrics.empty or "brier" not in metrics.columns:
        return "elo"
    return str(metrics.groupby("model")["brier"].mean().sort_values(kind="mergesort").index[0])


if __name__ == "__main__":
    main()
