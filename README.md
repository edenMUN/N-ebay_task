# eBay UI Automation Project (Playwright + Python)

This project automates an end-to-end eBay shopping scenario using **Playwright (Python)**, **Pytest**, **Page Object Model (POM)**, and **Allure reporting**.

Implemented flow:
1. Login to eBay.
2. Search items by query.
3. Apply max-price filtering.
4. Collect up to N item URLs with paging.
5. Add items to cart (including variant handling when dropdowns exist).
6. Assert cart subtotal does not exceed `budget_per_item * items_count`.

## Tech Stack

- Python 3.10+
- Playwright (sync API)
- Pytest + pytest-playwright
- allure-pytest
- Data-driven configuration (`data/data.json` per environment; credentials from `.env`)

## Brief Architecture Overview

- **Test orchestration:** `tests/Test_e2e_add_to_cart.py` drives one end-to-end scenario and performs business assertions.
- **Page Object Model:** `pages/` encapsulates locators and UI actions (`login`, `search`, `product`, `cart`) to keep tests readable.
- **Shared fixtures/hooks:** `tests/conftest.py` manages env data loading, browser context setup (viewport + locale), login/cart preconditions, screenshots, and optional tracing.
- **Utilities layer:** `utils/` contains config loading, price parsing, currency extraction/conversion, and custom exceptions.
- **Reporting pipeline:** pytest writes raw artifacts to `allure-results/`; `run_tests.py` standardizes execution and opens Allure locally outside CI.

## Project Structure

```text
pages/
  base_page.py
  login_page.py
  search_page.py
  product_page.py
  cart_page.py
tests/
  conftest.py
  Test_e2e_add_to_cart.py
data/
  data.json              # default env (--env default)
  data.<env>.json        # optional per-environment copies
utils/
  config_loader.py
  price_parser.py
  currency_converter.py
  exceptions.py
results/                 # screenshots + optional traces (--trace-on)
allure-results/          # raw allure artifacts (recreated each run)
run_tests.py             # unified runner + local allure serve (non-CI)
README.md
PROJECT_SUMMARY.md
requirements.txt
pytest.ini
```

## Prerequisites & Installation

```powershell
python -m pip install -r requirements.txt
python -m playwright install
```

### Allure CLI (required to open HTML report locally)

`run_tests.py` uses `allure serve allure-results` after test execution on local runs.  
Make sure the Allure CLI is installed and available on `PATH`:

```powershell
choco install allure
allure --version
```

## How To Run

### Prerequisites

| Goal | Command |
|---|---|
| Install Python deps | `python -m pip install -r requirements.txt` |
| Install Playwright browsers | `python -m playwright install` |
| Verify Allure CLI (local HTML) | `allure --version` |

### Main Commands

| Goal | Command |
|---|---|
| Run e2e test (headed) | `python -m pytest tests/Test_e2e_add_to_cart.py -v --browser chromium --headed` |
| Run e2e test (headless) | `python -m pytest tests/Test_e2e_add_to_cart.py -v --browser chromium` |
| Run with environment selection | `python -m pytest tests/Test_e2e_add_to_cart.py -v --env default --browser chromium --headed` |
| Run with runner script (auto Allure serve, local) | `python run_tests.py --browser chromium --headed` |
| Run with runner script + trace | `python run_tests.py --trace-on --browser chromium --headed` |
| Generate Allure artifacts only | `python -m pytest --alluredir=allure-results` |
| Open Allure report server manually | `allure serve allure-results` |
| Generate static Allure HTML only | `allure generate allure-results -o allure-report --clean` |
| Open generated static report folder | `allure open allure-report` |

### Credentials

Set secrets in `.env` (gitignored), not in committed JSON:

```env
EBAY_USERNAME=your_username
EBAY_PASSWORD=your_password
```

Optional: for `--env staging`, you can add `.env.staging` to override variables for that run (loaded after `.env`).

Base test data lives in `data/data.json`. For `--env <name>`, use `data/data.<name>.json` (e.g. `data/data.staging.json`).

## Limitations & Assumptions

- **Login-only setup (no guest fallback):** the autouse fixture attempts authenticated login and cart cleanup before each test. If login/cart setup is blocked by anti-bot or transient UI issues, the test is skipped rather than continuing as guest.
- **Live marketplace volatility:** eBay DOM, inventory, prices, and seller states can change between runs; locator fallbacks and retries reduce but do not eliminate flakiness.
- **Currency conversion is static:** budget checks use fixed FX rates in `utils/currency_converter.py` (deterministic by design), not live exchange-rate APIs.
- **Locale is browser-context level:** `locale` from `data/data.json` is passed into Playwright context; site behavior may still depend on account, region, cookie, or domain routing.
- **Allure local serve is interactive:** `python run_tests.py` starts `allure serve` (non-CI) and keeps a foreground process running until user stops it.

### Authentication & Security

Due to eBay's strict anti-bot measures, the login flow includes a Smart Wait mechanism:

- The script attempts to log in using credentials from the `.env` file.
- If a security challenge (Captcha) is detected, the automation prints a warning and pauses up to 45 seconds, allowing manual resolution in the browser window.
- Once resolved, the test continues automatically.
- If login still fails after the Smart Wait, a full-page screenshot is attached to Allure and the test fails with a clear error.

To support this, always run tests in headed mode (`--headed`) during local demonstrations.

## Run Commands

Default pytest options and markers are defined in `pytest.ini` (`--strict-markers`, `-ra`).

### Run all tests (default Chromium, headless)

```powershell
python -m pytest
```

### Run the e2e suite file explicitly

```powershell
python -m pytest tests/Test_e2e_add_to_cart.py -v
```

### Environment-specific data (`--env`)

- `default` (or omitted): loads `data/data.json`.
- Any other value: loads `data/data.<env>.json` and, if present, `.env.<env>` after `.env`.

```powershell
python -m pytest tests/Test_e2e_add_to_cart.py -v --env default
python -m pytest tests/Test_e2e_add_to_cart.py -v --env staging
```

### Markers (`sanity`, `regression`, `logic`)

```powershell
python -m pytest -m sanity -v
python -m pytest -m regression -v
python -m pytest -m logic -v
python -m pytest -m "sanity or regression" -v
```

### Browser and headed mode (pytest-playwright)

```powershell
python -m pytest tests/Test_e2e_add_to_cart.py -v --browser chromium --headed
python -m pytest tests/Test_e2e_add_to_cart.py -v --browser firefox
```

### Allure

```powershell
python -m pytest --alluredir=allure-results
allure serve allure-results
```

### Allure Quick Start (Professional Flow)

Use the runner script to keep reporting consistent across local and CI executions:

```powershell
python run_tests.py
python run_tests.py --env default --browser chromium --headed
python run_tests.py --trace-on --env default --browser chromium --headed
```

What it does:
- Always runs tests with `--alluredir=allure-results`.
- Forwards any extra CLI flags directly to `pytest`.
- Automatically opens `allure serve allure-results` only for local runs.
- Skips `allure serve` when `CI` is set (CI/CD safe and non-blocking).
- Supports `--trace-on` to enable Playwright tracing per test and attach trace zips to Allure.

### Combine flags (example)

```powershell
python -m pytest tests/Test_e2e_add_to_cart.py -v --env staging -m regression --browser chromium --headed --alluredir=allure-results
```

## Allure Reporting

- Generate results: `python -m pytest --alluredir=allure-results`
- Open report: `allure serve allure-results`
- To view the interactive Allure report: Download and extract `allure-report.zip`, then run `allure open allure-report` from your terminal.

### Troubleshooting (Allure does not open)

If tests pass but Allure does not open automatically, check one of these:
- Allure CLI is missing from `PATH`.
- Java is not configured (`JAVA_HOME` / `java` command missing).
- Current terminal session has stale environment variables (open a new terminal).
- `run_tests.py` prints a warning and skips opening Allure when CLI startup fails.

Fix:
1. Install Allure CLI (`choco install allure`)
2. Restart terminal
3. Verify `allure --version`
4. Verify `java -version`
5. Re-run: `python run_tests.py --headed --browser chromium`
6. If needed, open report manually: `allure serve allure-results`

## Debugging with Trace Viewer

When tracing is enabled (`--trace-on`), traces are saved under `results/`.

```powershell
playwright show-trace results/trace.zip
```

Per-test trace files look like: `results/<test_name>_trace.zip` (only with `--trace-on`).

## POM Design Notes

- Page objects stay lean: locators and user actions only.
- Business assertions and orchestration remain in test layer.
- All actions in page objects use `@allure.step` for readable execution trails.
- Price text normalization is centralized in `utils/price_parser.py`.

## Reporting and Evidence

- Tracing is optional and enabled only with `--trace-on` (`screenshots=True`, `snapshots=True`, `sources=True`).
- On failure: screenshot is auto-attached to Allure.
- During add-to-cart flow: per-item screenshots are saved and attached.
- During cart budget validation: full-page cart screenshot is always attached (pass/fail).
- At session start: `results/` and `allure-results/` are cleaned to avoid stale data pollution.
