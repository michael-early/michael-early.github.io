from __future__ import annotations

from pathlib import Path

import pandas as pd

from eagles_ml.evaluation import EvaluationResult, metric_summary


def write_charts(result: EvaluationResult, *, output_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    summary = metric_summary(result.metrics)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(summary["model"], summary["brier"], color=["#004c54", "#acc0c6", "#565a5c"])
    ax.set_title("Model Comparison: Lower Brier Is Better")
    ax.set_ylabel("Average Brier Score")
    ax.set_xlabel("Model")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    metrics_path = output_dir / "model_comparison.png"
    fig.savefig(metrics_path, dpi=160)
    plt.close(fig)
    paths.append(metrics_path)

    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    for model_name, group in result.calibration.groupby("model"):
        ax.plot(
            group["mean_predicted_probability"],
            group["actual_home_win_rate"],
            marker="o",
            label=model_name,
        )
    ax.plot([0, 1], [0, 1], linestyle="--", color="#444444", label="perfect calibration")
    ax.set_title("Calibration by Probability Bucket")
    ax.set_xlabel("Mean predicted home win probability")
    ax.set_ylabel("Actual home win rate")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend()
    fig.tight_layout()
    calibration_path = output_dir / "calibration.png"
    fig.savefig(calibration_path, dpi=160)
    plt.close(fig)
    paths.append(calibration_path)
    return paths


def write_model_report(
    result: EvaluationResult,
    *,
    output_path: Path,
    dataset_path: Path,
    predictions_path: Path,
) -> Path:
    summary = metric_summary(result.metrics)
    table = _markdown_table(summary)
    content = f"""# NFL Game Prediction Model Report

## Headline

This project evaluates NFL game prediction models with season-forward validation and uses the
best-calibrated approach to produce a 2026 Philadelphia Eagles forecast.

Best model by average Brier score: `{result.best_model}`.

## Dataset

- Historical feature table: `{dataset_path}`
- Validation seasons: {int(result.metrics["season"].min())}-{int(result.metrics["season"].max())}
- Feature columns: {", ".join(f"`{name}`" for name in result.feature_names)}

Features are built from pregame state only. Team ratings and rolling form are updated after each
game, so each row uses information that would have been available before kickoff.

## Model Comparison

{table}

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

The Eagles forecast is written to `{predictions_path}`. It remains a preseason projection until
2026 injuries, market lines, and current-season performance data are available.

## Limitations

- The current feature set is schedule-based and market-aware when spread lines exist; it does not
  yet include injuries, depth charts, or quarterback availability.
- Weather is used only when present in the source schedule data.
- Betting-market lines are useful predictors, but this project is designed as a Data/ML portfolio
  system, not betting advice.
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path


def _markdown_table(frame: pd.DataFrame) -> str:
    rounded = frame.copy()
    for column in ["brier", "log_loss", "accuracy"]:
        rounded[column] = rounded[column].map(lambda value: f"{value:.4f}")
    columns = list(rounded.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in rounded.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(lines)
