"""Configuration parameters for the pressure pipeline."""
from pathlib import Path

# Randomness
SEED: int = 42

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "out"
FIXTURE_DIR = BASE_DIR / "tests" / "fixture_data"

# Leverage & Pressure Cutoffs
LEVERAGE_QUANTILES = [0.67, 0.75, 0.80]
DEFAULT_PRESSURE_QUANTILE = 0.75

# Eligibility Floor Defaults (to be tuned after diagnostic scan)
MIN_PRESSURE_BALLS: int = 60
MIN_PRESSURE_MATCHES: int = 6

# Bootstrap Parameters
BOOTSTRAP_ROUNDS: int = 1000
