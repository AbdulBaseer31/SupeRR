# Pressure Players: SupeRR Selector

Pipeline to rank the best T20 batters and bowlers under match pressure from ball-by-ball data.

## Project Structure
- `pressure/`: Pipeline modules (loaders, match state prep, par tables, win probability, leverage, shrinkage, bootstrap, sensitivity).
- `tests/`: Acceptance tests and synthetic fixture generator (`tests/make_fixture.py`).
- `data/`: Raw competition CSV data (confidential, excluded from version control).
- `out/`: Diagnostic logs, ledgers, rankings, and exhibits (excluded from version control).

## Setup & Virtual Environment
Create and activate the virtual environment:
```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage
Run the synthetic fixture generator:
```bash
python tests/make_fixture.py
```

Run test suite:
```bash
pytest tests/
```
