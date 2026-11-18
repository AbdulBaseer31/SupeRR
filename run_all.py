"""Pipeline orchestrator: Stage 1 (Load, diagnostics, ledger)."""
import argparse
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pressure import config
from pressure.io_load import load_all_csvs
from pressure.ledger import compute_diagnostics_and_ledger

def run_stage_1(data_dir: Path, out_dir: Path) -> None:
    """Run stage 1: load files, generate diagnostics, and build exclusion ledger."""
    print(f"Loading data from: {data_dir}")
    dfs = load_all_csvs(data_dir)
    print("Files loaded successfully. Computing diagnostics and ledger...")
    ledger, dup_names, diag_text = compute_diagnostics_and_ledger(dfs, out_dir)
    print(diag_text)
    print("\nLedger Summary:")
    print(ledger.to_string(index=False))
    print(f"\nOutputs written to {out_dir}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run Pressure Pipeline")
    parser.add_argument("--fixture", action="store_true", help="Run on synthetic fixture data")
    args = parser.parse_args()

    data_dir = config.FIXTURE_DIR if args.fixture else config.DATA_DIR
    out_dir = config.OUT_DIR
    run_stage_1(data_dir, out_dir)

if __name__ == "__main__":
    main()
