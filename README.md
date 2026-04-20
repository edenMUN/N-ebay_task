# Bitcoin Price Index (BPI) Monitor

Small **object-oriented** Python automation that meets five requirements:

1. **HTTP GET** to the Coinbase BTC-USD spot API  
2. **Extract** the current Bitcoin price (USD) from the response  
3. **Collect** that price on a schedule and **save** each sample to a **JSON** file (default: every **60 seconds** × **60 samples** ≈ one hour)
4. After the window, **generate a BPI graph** (PNG, timestamps on the X axis)  
5. **Send an email** (SMTP — Gmail or any server) with the **maximum** price in the window and the **graph** attachment  

**Logging:** all operational steps are logged from the **business logic** layer (`bpi.business.*` loggers).

## Layout

```
src/api_client/       CoinbaseBtcUsdSpotPage + CoinbaseBtcUsdSpotSteps (real GET)
src/business_logic/   Orchestrator, JSON repository, chart, models, statistics
src/utils/            dotenv config, logging setup, SMTP helper (no BL logging inside)
run_automation.py     Entry point
tests/Test_bpi_requirements.py   Five pytest cases = five requirements (live API)
data/                 Default JSON + PNG output
```

The framework uses a centralized conftest.py for shared fixtures and environment bootstrapping to ensure scalability and clean test code.

## Run the monitor (full hour by default)

```powershell
python -m pip install -r requirements.txt
python run_automation.py
```

Optional overrides:

```powershell
python run_automation.py --target-samples 60 --interval-seconds 60
```

## Run the five requirement tests (pytest)

Uses **real** Coinbase HTTP for tests 1–4. Test 5 sends a **real** email and is **skipped** unless `SMTP_USER` and `SMTP_PASSWORD` are set (e.g. Gmail with an [app password](https://support.google.com/accounts/answer/185833)).

```powershell
python -m pytest tests/Test_bpi_requirements.py -v
```

## Submission checklist

1. **ZIP** — archive this repository (code + tests).  
2. **Email screenshot** — inbox showing the BPI report (after a successful `run_automation.py` or requirement 5 test).  
3. **Graph screenshot** — `data/` PNG with timestamps and BPI title.  
4. **JSON file** — `data/<BPI_JSON_FILE>` after a full run.
