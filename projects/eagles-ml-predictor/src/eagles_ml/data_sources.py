from __future__ import annotations

from pathlib import Path

import pandas as pd

NFLVERSE_GAMES_CSV_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"


def fetch_schedules_with_nfl_data_py(years: list[int]) -> pd.DataFrame:
    """Fetch schedules through nfl_data_py, falling back to nflverse's raw schedules CSV."""
    try:
        import nfl_data_py as nfl  # type: ignore
    except ImportError:
        schedules = pd.read_csv(NFLVERSE_GAMES_CSV_URL)
    else:
        schedules = nfl.import_schedules(years)
    return schedules[schedules["season"].isin(years)].copy()


def save_schedules(years: list[int], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schedules = fetch_schedules_with_nfl_data_py(years)
    schedules.to_csv(output_path, index=False)
    return output_path
