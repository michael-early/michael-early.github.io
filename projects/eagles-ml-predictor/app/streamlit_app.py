from __future__ import annotations

import base64
from html import escape
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"

PRIMARY = "#004c54"
INK = "#14242b"
MUTED = "#66747b"
SILVER = "#a5acaf"
WIN = "#0f766e"
LOSS = "#b42318"


st.set_page_config(page_title="NFL Game Prediction System", layout="wide")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def confidence_label(probability: float) -> str:
    edge = abs(probability - 0.5)
    if edge < 0.035:
        return "Coin flip"
    if edge < 0.085:
        return "Lean"
    if edge < 0.15:
        return "Moderate"
    return "Strong"


def display_model_name(model: str) -> str:
    labels = {
        "logistic_regression": "Logistic",
        "hist_gradient_boosting": "Gradient Boosting",
        "elo": "Elo",
    }
    return labels.get(model, model.replace("_", " ").title())


def inject_css() -> None:
    st.html(
        f"""
<style>
    :root {{
        --primary: {PRIMARY};
        --ink: {INK};
        --muted: {MUTED};
        --silver: {SILVER};
        --paper: #f6f7f4;
        --panel: #ffffff;
        --line: #dfe4e2;
        --win: {WIN};
        --loss: {LOSS};
    }}

    .stApp {{
        background:
            linear-gradient(180deg, rgba(0, 76, 84, 0.12) 0, rgba(246, 247, 244, 0) 330px),
            var(--paper);
        color: var(--ink);
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    #MainMenu {{
        visibility: hidden;
    }}

    .block-container {{
        max-width: min(1580px, calc(100vw - 48px));
        padding-top: 1.35rem;
        padding-bottom: 3rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }}

    div[data-testid="stHorizontalBlock"] {{
        align-items: stretch;
    }}

    .hero {{
        border: 1px solid rgba(0, 76, 84, 0.18);
        border-radius: 8px;
        display: grid;
        grid-template-columns: minmax(0, 1.35fr) minmax(420px, 0.85fr);
        gap: 28px;
        align-items: stretch;
        padding: 30px 32px;
        background:
            linear-gradient(135deg, rgba(0, 76, 84, 0.97), rgba(20, 36, 43, 0.97)),
            var(--primary);
        color: white;
        box-shadow: 0 18px 44px rgba(20, 36, 43, 0.18);
        position: relative;
        overflow: hidden;
    }}

    .hero::after {{
        content: "";
        position: absolute;
        inset: auto -80px -150px auto;
        width: 420px;
        height: 420px;
        border-radius: 50%;
        background: rgba(165, 172, 175, 0.12);
        pointer-events: none;
    }}

    .hero-copy,
    .hero-stat-grid {{
        position: relative;
        z-index: 1;
    }}

    .eyebrow {{
        color: #d8e4e4;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }}

    .hero h1 {{
        font-size: clamp(2.1rem, 3vw, 3.35rem);
        line-height: 1.08;
        margin: 0;
        color: #ffffff;
        letter-spacing: 0;
    }}

    .hero p {{
        color: #e6eeee;
        max-width: 850px;
        margin: 0.85rem 0 0;
        font-size: 1.04rem;
        line-height: 1.55;
    }}

    .hero-stat-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin-top: 0;
    }}

    .hero-stat {{
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 8px;
        padding: 18px 18px;
        background: rgba(255, 255, 255, 0.095);
        min-width: 0;
        min-height: 112px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}

    .hero-stat .label {{
        color: #cbd9da;
        font-size: 0.75rem;
        font-weight: 650;
        margin-bottom: 5px;
        text-transform: uppercase;
    }}

    .hero-stat .value {{
        color: white;
        font-size: clamp(1.25rem, 2vw, 1.85rem);
        font-weight: 800;
        line-height: 1.1;
        overflow-wrap: anywhere;
    }}

    .section-title {{
        color: var(--ink);
        font-size: 1.15rem;
        font-weight: 800;
        margin: 1.35rem 0 0.75rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }}

    .section-title::before {{
        content: "";
        width: 5px;
        height: 19px;
        border-radius: 999px;
        background: var(--primary);
    }}

    .panel {{
        border: 1px solid var(--line);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.92);
        padding: 20px;
        box-shadow: 0 8px 24px rgba(20, 36, 43, 0.06);
        overflow-x: auto;
    }}

    .chart-card {{
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #ffffff;
        padding: 18px;
        box-shadow: 0 8px 24px rgba(20, 36, 43, 0.06);
    }}

    .chart-card img {{
        display: block;
        width: 100%;
        height: auto;
    }}

    .game-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.92rem;
        table-layout: fixed;
        min-width: 1080px;
    }}

    .game-table th {{
        color: var(--muted);
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0;
        text-align: left;
        padding: 10px 8px;
        border-bottom: 1px solid var(--line);
    }}

    .game-table td {{
        padding: 11px 8px;
        border-bottom: 1px solid #edf0ef;
        vertical-align: middle;
    }}

    .game-table th:nth-child(1),
    .game-table td:nth-child(1) {{
        width: 58px;
    }}

    .game-table th:nth-child(2),
    .game-table td:nth-child(2) {{
        width: 120px;
    }}

    .game-table th:nth-child(3),
    .game-table td:nth-child(3) {{
        width: 88px;
    }}

    .game-table th:nth-child(4),
    .game-table td:nth-child(4) {{
        width: 250px;
    }}

    .game-table th:nth-child(5),
    .game-table td:nth-child(5) {{
        width: 64px;
    }}

    .game-table th:nth-child(6),
    .game-table td:nth-child(6) {{
        width: 112px;
    }}

    .game-table tr:last-child td {{
        border-bottom: 0;
    }}

    .team-cell {{
        font-weight: 750;
        color: var(--ink);
        white-space: nowrap;
    }}

    .muted {{
        color: var(--muted);
        overflow-wrap: anywhere;
    }}

    .pill {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 34px;
        border-radius: 999px;
        padding: 4px 9px;
        font-weight: 800;
        font-size: 0.78rem;
    }}

    .pill.win {{
        background: rgba(15, 118, 110, 0.12);
        color: var(--win);
    }}

    .pill.loss {{
        background: rgba(180, 35, 24, 0.12);
        color: var(--loss);
    }}

    .prob-wrap {{
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 160px;
    }}

    .prob-track {{
        flex: 1;
        height: 8px;
        border-radius: 999px;
        background: #d9dfdd;
        overflow: hidden;
    }}

    .prob-fill {{
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, var(--primary), #34a0a4);
    }}

    .prob-text {{
        min-width: 48px;
        text-align: right;
        font-variant-numeric: tabular-nums;
        font-weight: 700;
    }}

    .metric-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
        table-layout: fixed;
        min-width: 760px;
    }}

    .metric-table th,
    .metric-table td {{
        padding: 10px 9px;
        border-bottom: 1px solid var(--line);
        text-align: left;
        overflow-wrap: anywhere;
    }}

    .metric-table th:nth-child(1),
    .metric-table td:nth-child(1) {{
        width: 46px;
    }}

    .metric-table th:nth-child(2),
    .metric-table td:nth-child(2) {{
        width: 170px;
    }}

    .metric-table th {{
        color: var(--muted);
        font-size: 0.76rem;
        text-transform: uppercase;
    }}

    .model-rank {{
        font-weight: 800;
        color: var(--primary);
    }}

    .calibration-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.86rem;
        table-layout: fixed;
        min-width: 560px;
    }}

    .calibration-label {{
        color: #d9e5e4;
        font-size: 0.76rem;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 10px;
        overflow-wrap: anywhere;
    }}

    .calibration-table th {{
        color: #f5f8f7;
        background: var(--ink);
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0;
        text-align: left;
        padding: 10px 9px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    }}

    .calibration-table td {{
        color: #eaf0ef;
        background: #111b21;
        padding: 9px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        font-variant-numeric: tabular-nums;
    }}

    .calibration-table tr:last-child td {{
        border-bottom: 0;
    }}

    .calibration-table .model-name {{
        color: #ffffff;
        font-weight: 750;
    }}

    .calibration-table .bucket {{
        color: #bfc9c9;
    }}

    .note-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
    }}

    .note-card {{
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #ffffff;
        padding: 16px;
        min-height: 126px;
    }}

    .note-card h3 {{
        font-size: 0.94rem;
        margin: 0 0 8px;
        color: var(--ink);
    }}

    .note-card p {{
        color: var(--muted);
        margin: 0;
        font-size: 0.88rem;
        line-height: 1.45;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
    }}

    @media (max-width: 920px) {{
        .hero {{
            grid-template-columns: 1fr;
        }}

        .hero h1 {{
            font-size: 1.9rem;
        }}

        .prob-wrap {{
            min-width: 120px;
        }}
    }}

    @media (max-width: 760px) {{
        div[data-testid="stHorizontalBlock"] {{
            flex-direction: column;
        }}

        div[data-testid="stHorizontalBlock"] > div {{
            width: 100% !important;
        }}
    }}

    @media (max-width: 680px) {{
        .block-container {{
            padding-left: 0.85rem;
            padding-right: 0.85rem;
        }}

        .hero {{
            padding: 22px 18px;
        }}

        .hero-stat-grid,
        .note-grid {{
            grid-template-columns: 1fr;
        }}

        .section-title {{
            font-size: 1.02rem;
        }}
    }}
</style>
"""
    )


def render_hero(predictions: pd.DataFrame, metrics: pd.DataFrame) -> None:
    if predictions.empty:
        record = "No forecast"
        games = "0"
        model = "N/A"
    else:
        wins = int((predictions["projected_result"] == "W").sum())
        losses = int((predictions["projected_result"] == "L").sum())
        record = f"{wins}-{losses}"
        games = str(len(predictions))
        model = display_model_name(str(predictions.get("model_used", pd.Series(["elo"])).iloc[0]))

    if metrics.empty:
        brier = "N/A"
    else:
        summary = metric_summary(metrics)
        brier = f"{summary.iloc[0]['brier']:.3f}"

    st.html(
        f"""
<section class="hero">
    <div class="hero-copy">
        <div class="eyebrow">Portfolio MVP / NFL Forecasting</div>
        <h1>NFL game prediction and calibration system.</h1>
        <p>
            A reusable analytics workflow with historical feature engineering,
            season-forward model validation, calibration artifacts, and a featured
            2026 Eagles forecast.
        </p>
    </div>
    <div class="hero-stat-grid">
        <div class="hero-stat">
            <div class="label">Eagles Projection</div>
            <div class="value">{record}</div>
        </div>
        <div class="hero-stat">
            <div class="label">Games Forecast</div>
            <div class="value">{games}</div>
        </div>
        <div class="hero-stat">
            <div class="label">Selected Model</div>
            <div class="value">{model}</div>
        </div>
        <div class="hero-stat">
            <div class="label">Best Brier</div>
            <div class="value">{brier}</div>
        </div>
    </div>
</section>
"""
    )


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
        .sort_values("brier")
    )


def figure_to_html(fig: plt.Figure, alt: str) -> str:
    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return (
        '<div class="chart-card">'
        f'<img alt="{escape(alt)}" src="data:image/png;base64,{encoded}" />'
        "</div>"
    )


def render_model_chart(metrics: pd.DataFrame) -> None:
    if metrics.empty:
        st.info("Run model evaluation to generate the comparison chart.")
        return

    summary = metric_summary(metrics).sort_values("brier", ascending=False)
    labels = [display_model_name(str(model)) for model in summary["model"]]
    values = summary["brier"].astype(float).tolist()
    colors = ["#586267", "#a5b9bf", PRIMARY]

    fig, ax = plt.subplots(figsize=(7.2, 3.2), dpi=170)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    bars = ax.barh(labels, values, color=colors[: len(values)], height=0.58)
    ax.set_title("Average Brier Score by Model", fontsize=12, fontweight="bold", color=INK, pad=12)
    ax.set_xlabel("Lower is better", color=MUTED, fontsize=9)
    ax.tick_params(axis="both", colors=INK, labelsize=8)
    ax.grid(axis="x", color="#e6ebe9", linewidth=0.9)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(values) * 1.16)

    for bar, value in zip(bars, values, strict=False):
        ax.text(
            value + max(values) * 0.025,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.3f}",
            va="center",
            ha="left",
            fontsize=9,
            color=INK,
            fontweight="bold",
        )

    for spine in ax.spines.values():
        spine.set_visible(False)

    st.html(figure_to_html(fig, "Model comparison chart"))


def render_calibration_chart(calibration: pd.DataFrame) -> None:
    if calibration.empty:
        st.info("Run model evaluation to generate the calibration chart.")
        return

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=170)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    palette = {
        "logistic_regression": PRIMARY,
        "hist_gradient_boosting": "#7a959b",
        "elo": "#d3812f",
    }

    for model, group in calibration.groupby("model"):
        ordered = group.sort_values("mean_predicted_probability")
        ax.plot(
            ordered["mean_predicted_probability"],
            ordered["actual_home_win_rate"],
            marker="o",
            linewidth=2,
            markersize=4.5,
            color=palette.get(str(model), SILVER),
            label=display_model_name(str(model)),
        )

    ax.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        color="#9aa4a6",
        linewidth=1.2,
        label="perfect calibration",
    )
    ax.set_title(
        "Calibration by Probability Bucket",
        fontsize=12,
        fontweight="bold",
        color=INK,
        pad=12,
    )
    ax.set_xlabel("Mean predicted home win probability", color=MUTED, fontsize=9)
    ax.set_ylabel("Actual home win rate", color=MUTED, fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(color="#e6ebe9", linewidth=0.9)
    ax.tick_params(axis="both", colors=INK, labelsize=8)
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    for spine in ax.spines.values():
        spine.set_visible(False)

    st.html(figure_to_html(fig, "Calibration chart"))


def selected_calibration_model(calibration: pd.DataFrame, metrics: pd.DataFrame) -> str | None:
    if calibration.empty:
        return None
    if not metrics.empty:
        best_model = str(metric_summary(metrics).iloc[0]["model"])
        if best_model in set(calibration["model"].astype(str)):
            return best_model
    return str(calibration.iloc[0]["model"])


def render_calibration_table(calibration: pd.DataFrame, metrics: pd.DataFrame) -> None:
    model = selected_calibration_model(calibration, metrics)
    if model is None:
        st.info("Calibration output is generated by the evaluation command.")
        return

    display = calibration[calibration["model"].astype(str) == model].copy()
    display = display.sort_values("mean_predicted_probability")
    model_label = escape(display_model_name(model))
    rows = []
    for _, row in display.iterrows():
        predicted = float(row["mean_predicted_probability"])
        actual = float(row["actual_home_win_rate"])
        gap = actual - predicted
        rows.append(
            f"""
<tr>
    <td class="bucket">{escape(str(row["bucket"]))}</td>
    <td>{int(row["games"])}</td>
    <td>{percent(predicted)}</td>
    <td>{percent(actual)}</td>
    <td>{gap:+.1%}</td>
</tr>
"""
        )

    st.html(
        f"""
<div class="panel" style="background:#111b21; border-color:#26343a;">
    <div class="calibration-label">
        Featured calibration: <span style="color:#ffffff;">{model_label}</span>
    </div>
    <table class="calibration-table">
        <thead>
            <tr>
                <th>Bucket</th>
                <th>Games</th>
                <th>Predicted</th>
                <th>Actual</th>
                <th>Gap</th>
            </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
</div>
"""
    )


def render_forecast_table(predictions: pd.DataFrame) -> None:
    if predictions.empty:
        st.warning("No prediction file found. Run `eagles-ml predict-2026` first.")
        return

    rows = []
    for _, game in predictions.iterrows():
        probability = float(game["eagles_win_probability"])
        result = str(game["projected_result"])
        pill_class = "win" if result == "W" else "loss"
        date = "" if pd.isna(game.get("date")) else str(game.get("date"))
        note = "" if pd.isna(game.get("notes")) else str(game.get("notes"))
        opponent = escape(str(game["opponent"]))
        site = escape(str(game["site"]).title())
        rows.append(
            f"""
<tr>
    <td class="muted">{int(game["week"])}</td>
    <td>
        <div class="team-cell">{opponent}</div>
        <div class="muted">{escape(date)}</div>
    </td>
    <td class="muted">{site}</td>
    <td>
        <div class="prob-wrap">
            <div class="prob-track">
                <div class="prob-fill" style="width: {probability * 100:.1f}%"></div>
            </div>
            <div class="prob-text">{percent(probability)}</div>
        </div>
    </td>
    <td><span class="pill {pill_class}">{escape(result)}</span></td>
    <td class="muted">{confidence_label(probability)}</td>
    <td class="muted">{escape(note)}</td>
</tr>
"""
        )

    st.html(
        f"""
<div class="panel">
    <table class="game-table">
        <thead>
            <tr>
                <th>Week</th>
                <th>Opponent</th>
                <th>Site</th>
                <th>Win Probability</th>
                <th>Pick</th>
                <th>Confidence</th>
                <th>Context</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
</div>
"""
    )


def render_model_table(metrics: pd.DataFrame) -> None:
    if metrics.empty:
        st.info(
            "No model metrics yet. Run "
            "`eagles-ml evaluate --dataset data/processed/historical_games.csv`."
        )
        return

    summary = metric_summary(metrics).reset_index(drop=True)
    rows = []
    for index, row in summary.iterrows():
        rank = index + 1
        rows.append(
            f"""
<tr>
    <td class="model-rank">{rank}</td>
    <td>{escape(display_model_name(str(row["model"])))}</td>
    <td>{int(row["seasons"])}</td>
    <td>{int(row["games"])}</td>
    <td>{row["brier"]:.4f}</td>
    <td>{row["log_loss"]:.4f}</td>
    <td>{row["accuracy"]:.1%}</td>
</tr>
"""
        )

    st.html(
        f"""
<div class="panel">
    <table class="metric-table">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Model</th>
                <th>Seasons</th>
                <th>Games</th>
                <th>Brier</th>
                <th>Log Loss</th>
                <th>Accuracy</th>
            </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
</div>
"""
    )


def render_notes() -> None:
    st.html(
        """
<div class="note-grid">
    <div class="note-card">
        <h3>Leak-free features</h3>
        <p>
            Rolling form, Elo state, rest, market context, and environment are computed
            from information available before kickoff.
        </p>
    </div>
    <div class="note-card">
        <h3>Time-aware validation</h3>
        <p>
            Models train on earlier seasons and predict later seasons, which better
            matches the forecasting problem than random splits.
        </p>
    </div>
    <div class="note-card">
        <h3>Preseason caveat</h3>
        <p>
            The 2026 table does not yet include injuries, depth-chart changes, weather
            forecasts, or late market movement.
        </p>
    </div>
</div>
"""
    )


inject_css()

predictions = read_csv(OUTPUTS / "eagles_2026_predictions.csv")
metrics = read_csv(OUTPUTS / "model_metrics.csv")
calibration = read_csv(OUTPUTS / "calibration.csv")

render_hero(predictions, metrics)

st.html('<div class="section-title">2026 Eagles Forecast</div>')
render_forecast_table(predictions)

left, right = st.columns([1.05, 0.95], gap="large")
with left:
    st.html('<div class="section-title">Model Leaderboard</div>')
    render_model_table(metrics)

with right:
    st.html('<div class="section-title">Model Comparison Chart</div>')
    render_model_chart(metrics)

st.html('<div class="section-title">Calibration</div>')
chart_col, table_col = st.columns([0.95, 1.05], gap="large")
with chart_col:
    render_calibration_chart(calibration)
with table_col:
    render_calibration_table(calibration, metrics)

st.html('<div class="section-title">How To Read This</div>')
render_notes()
