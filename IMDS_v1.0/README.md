# IMDS v1.0 — Indian Multibagger Discovery System

A local-first research toolkit built from the supplied NSE `EQUITY_L.csv` file. It creates an Excel research workbook and a Python scoring/report pipeline.

## What's included

- `IMDS_v1.0.xlsx` — workbook with `Start_Here`, `StockList`, `ConstituentMap`, `Fundamentals`, `Technicals`, `Ranking`, and `QuarterlyMonitor` tabs.
- `data/input/EQUITY_L.csv` — original supplied NSE equity master.
- `src/prepare_universe.py` — normalizes the NSE master into `stock_universe.csv`.
- `src/imds_engine.py` — calculates available-data fundamental/technical scores and combined rankings.
- `data/input/fundamentals_template.csv`, `technicals_template.csv` — input schemas.
- `run_imds.bat` / `run_imds.sh` — launchers.

## Important universe note

The source CSV contains 2,630 NSE equity symbols, not the Nifty 750. The project preserves all rows as an NSE master. The Nifty 750 mapping must be loaded from point-in-time/current official constituent lists: Nifty 500 plus Nifty Microcap 250, deduplicated. In the workbook, paste symbols into `ConstituentMap` and choose `NIFTY 500` or `MICROCAP 250`. Python input `stock_universe.csv` has a `UNIVERSE` column for this mapping.

## Install and run (Windows)

1. Install Python 3.10+.
2. Open a terminal in the extracted `IMDS_v1` folder.
3. Run:
   ```bash
   python -m pip install -r requirements.txt
   python src/prepare_universe.py
   ```
4. Fill `data/input/fundamentals.csv` and `data/input/technicals.csv` using the templates (or export sheets to CSV with those exact filenames).
5. Run `run_imds.bat` or:
   ```bash
   python src/imds_engine.py
   ```
6. Results appear in `data/output/imds_ranked.csv`.

Linux/macOS: `chmod +x run_imds.sh && ./run_imds.sh`.

## Input conventions

### fundamentals.csv

- `SALES_CAGR_3Y`, `PAT_CAGR_3Y`, latest/previous growth rates: decimal fractions (`0.15` means 15%).
- `ROCE`, `PROMOTER_HOLDING_PCT`, `PROMOTER_PLEDGE_PCT`: percentage points (`22` means 22%).
- `CFO_PAT`: 3-year cumulative operating cash flow divided by 3-year cumulative PAT. Leave blank if PAT denominator is non-positive.
- `DEBT_EQUITY`: ratio (e.g. `0.6`).
- `PE`, `SECTOR_PE`: valuation inputs. The current Python score pipeline reserves these for the next calibration iteration; it does not silently infer sector valuations.

### technicals.csv

- Boolean flags: `1` or `0` (or TRUE/FALSE).
- `RS_6M_PP`: stock six-month return minus Nifty 500 six-month return, in percentage points. Example: stock +34%, index +12% -> `22`.
- `BREAKOUT_VOLUME_RATIO`: current session volume / prior 20-session average volume.
- Add close, moving averages, resistance and average traded value for manual liquidity review.

## Score model

- Fundamental and technical scores are normalized over available metrics; completeness is reported separately. This avoids treating missing data as a zero score, but a score with low completeness is not decision-grade.
- Combined score = 60% fundamental + 40% technical, only when both component scores exist.
- Red risk flag: debt/equity above 2 or promoter pledge above 20% (screening alert, not an automatic conclusion).
- Banks/NBFCs require sector-specific metrics and should not be ranked using industrial debt/cash-conversion rules without adaptation.
- Python is the scoring source of truth; Excel is the editable monitoring workbook. Excel ranking formulas are a starter view and should be reconciled against the Python report before relying on ranks.

## Data quality and limitations

- No live market/fundamental data is fetched by this package. Populate inputs from reliable, licensed or official sources and record as-of dates.
- Yahoo ticker mapping (`.NS`) is convenience metadata, not proof that every symbol is available through Yahoo Finance.
- This is not a point-in-time historical database. For a 2020–2026 backtest, use historical index constituents including delisted/removed companies, filing-publication dates, corporate-action-adjusted prices, and next-session execution. Current constituents introduce survivorship/look-ahead bias.
- Microcap liquidity, traded value, free float, price impact, governance and accounting quality need additional filters before any real-money decision.
- No performance claim is made until a reproducible backtest has been run.

## Output

`data/output/imds_ranked.csv` includes component scores, completeness, combined score, risk flag, rank and classification.

This is a research/shortlisting system, not financial advice or an automated buy/sell signal.
