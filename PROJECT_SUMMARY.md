# Project Summary — BPI Monitor

## Requirements → tests

| # | Requirement | Pytest |
| --- | --- | --- |
| 1 | HTTP GET to API | `test_requirement_01_http_get_coinbase_spot_api` |
| 2 | Extract BTC USD price | `test_requirement_02_extract_bitcoin_price_usd` |
| 3 | Collect on interval, save JSON | `test_requirement_03_collect_and_save_prices_to_json_on_interval` |
| 4 | Generate BPI graph | `test_requirement_04_generate_bpi_graph_after_collecting_data` |
| 5 | Email max price + graph | `test_requirement_05_send_email_max_price_and_bpi_graph` |

Tests **1–4** call the **live** Coinbase API (no mocked HTTP). **Test 5** uses **live** `smtplib` when credentials exist.

## OOP & logging

- **api_client:** page (URL, timeout) + steps (GET / parse).  
- **business_logic:** orchestrator, storage, chart, stats — **all** user-visible actions log through `business_logger(...)`.  
- **utils:** configuration and SMTP transport only.

## Commands

- Monitor: `python run_automation.py`  
- Tests: `python -m pytest tests/Test_bpi_requirements.py -v`

See `README.md` for `.env` and submission artifacts.
