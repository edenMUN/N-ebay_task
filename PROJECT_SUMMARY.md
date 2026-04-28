# Project Summary — eBay UI Automation

## Architecture and Design Patterns

This framework is implemented with:
- **OOP + Page Object Model (POM):** each page class encapsulates UI locators and actions.
- **Data-Driven Testing:** runtime values (credentials, search query, limits, budget, viewport) come from `data/data.json`.
- **Centralized Test Orchestration:** test file coordinates business flow while page objects remain action-focused.
- **Allure + Playwright Tracing (Optional):** every critical step is reportable with execution evidence; trace capture is enabled via `--trace-on`.

## Key Implementation Decisions

- **Search + Paging Logic:** `SearchPage.search_items_by_name_under_price()` applies max-price filtering, validates result visibility, parses each card price, and paginates until limit reached or no more pages.
- **Price Filter Validation:** after submitting max-price input, the test waits for active filter UI indicators before collecting data.
- **Variant Handling in Product Pages:** dropdown selectors (size/color/quantity) are detected dynamically; random valid options are selected when available.
- **Budget Validation:** cart subtotal is parsed with a dedicated utility that handles symbols and separators; assertion compares against `budget_per_item * items_count`.

## Challenges and Solutions

- **Dynamic eBay DOM / locator changes:** implemented locator fallbacks for search headers, price inputs, add-to-cart controls, and cart subtotal.
- **Multiple add-to-cart UX behaviors (drawer vs navigation):** confirmation is validated by checking either explicit success UI or cart counter presence.
- **Currency/string parsing reliability:** centralized normalization in `utils/price_parser.py` avoids duplicated conversion logic.

## Reporting Configuration

- Page object actions are decorated with `@allure.step`.
- `tests/conftest.py` starts tracing only when `--trace-on` is passed, with:
  - `screenshots=True`
  - `snapshots=True`
  - `sources=True`
- Trace files are saved to `results/{test_name}_trace.zip` (conditional on `--trace-on`).
- Session bootstrap clears `results/` and `allure-results/` to prevent stale evidence.
- On failure, a full-page screenshot is captured and attached via `pytest_runtest_makereport`.
- Product add-to-cart attaches per-item business screenshots (`Item {index} added`).
- Cart budget validation always captures and attaches a full-page cart screenshot (pass/fail).
- `run_tests.py` standardizes execution using `pytest --alluredir=allure-results`, supports forwarding args and `--trace-on`, serves Allure locally, and skips `allure serve` in CI (`CI` env guard).
- If Allure CLI cannot be launched from the current shell session, `run_tests.py` logs a warning and keeps the pytest exit code behavior stable.

## Future Improvements

- CI/CD integration (GitHub Actions) with automatic Allure artifact publishing.
- Parallel execution strategy across browsers and datasets.
- Optional service layer abstraction for richer business workflows.
- More resilient anti-flakiness utilities (custom retry wrappers for known unstable elements).
