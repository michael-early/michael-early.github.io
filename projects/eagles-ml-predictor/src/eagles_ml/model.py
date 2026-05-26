from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize


@dataclass
class LogisticGameModel:
    feature_names: list[str]
    coefficients: np.ndarray
    intercept: float
    means: np.ndarray
    scales: np.ndarray

    def _standardize(self, frame: pd.DataFrame) -> np.ndarray:
        x = frame[self.feature_names].to_numpy(dtype=float)
        return (x - self.means) / self.scales

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        x = self._standardize(frame)
        logits = self.intercept + x @ self.coefficients
        return 1.0 / (1.0 + np.exp(-logits))


def fit_logistic_game_model(
    frame: pd.DataFrame,
    *,
    feature_names: list[str],
    target_name: str,
    l2: float = 1.0,
) -> LogisticGameModel:
    """Fit an L2-regularized logistic model for calibrated game probabilities."""
    x_raw = frame[feature_names].to_numpy(dtype=float)
    y = frame[target_name].to_numpy(dtype=float)
    means = np.nanmean(x_raw, axis=0)
    scales = np.nanstd(x_raw, axis=0)
    scales[scales == 0.0] = 1.0
    x = np.nan_to_num((x_raw - means) / scales)

    def objective(params: np.ndarray) -> float:
        intercept = params[0]
        beta = params[1:]
        logits = intercept + x @ beta
        loss = np.mean(np.logaddexp(0.0, logits) - y * logits)
        penalty = l2 * np.sum(beta * beta) / (2.0 * len(y))
        return float(loss + penalty)

    result = minimize(objective, np.zeros(len(feature_names) + 1), method="BFGS")
    if not result.success:
        raise RuntimeError(f"Model fit failed: {result.message}")
    return LogisticGameModel(
        feature_names=feature_names,
        intercept=float(result.x[0]),
        coefficients=result.x[1:],
        means=means,
        scales=scales,
    )


def brier_score(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    return float(np.mean((probabilities - y_true) ** 2))


def log_loss(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    clipped = np.clip(probabilities, 1e-6, 1.0 - 1e-6)
    return float(-np.mean(y_true * np.log(clipped) + (1.0 - y_true) * np.log(1.0 - clipped)))


def fit_sklearn_classifier(model_name: str, frame: pd.DataFrame, *, feature_names: list[str]):
    """Fit a scikit-learn classifier for model-comparison workflows."""
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise RuntimeError(
            "Install project dependencies before running ML evaluation: "
            "python -m pip install -e '.[nflverse,dev]'"
        ) from exc

    x = frame[feature_names]
    y = frame["home_win"].to_numpy(dtype=int)
    if len(set(y)) < 2:
        raise ValueError("Training data must include both home wins and home losses.")

    if model_name == "logistic_regression":
        classifier = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        C=1.0,
                        max_iter=1000,
                        random_state=42,
                    ),
                ),
            ]
        )
    elif model_name == "hist_gradient_boosting":
        classifier = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        learning_rate=0.05,
                        l2_regularization=0.01,
                        max_iter=200,
                        random_state=42,
                    ),
                ),
            ]
        )
    else:
        raise ValueError(f"Unknown sklearn model: {model_name}")

    return classifier.fit(x, y)
