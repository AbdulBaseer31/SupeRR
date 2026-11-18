"""CSV data loaders with strict validation and safe typing."""
from pathlib import Path
from typing import Dict
import pandas as pd

CSV_FILES = [
    "competitions.csv",
    "teams.csv",
    "competition_team_player_mapping.csv",
    "matches.csv",
    "playing_eleven.csv",
    "ball_by_ball.csv",
]

def load_all_csvs(data_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load all 6 required CSVs into DataFrames from the specified directory."""
    dfs: Dict[str, pd.DataFrame] = {}
    for filename in CSV_FILES:
        path = data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Required CSV not found: {path}")
        df = pd.read_csv(path, low_memory=False)
        name = filename.replace(".csv", "")
        dfs[name] = df
    return dfs
