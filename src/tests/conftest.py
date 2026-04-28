from pathlib import Path
import shutil
from typing import Dict, Generator

import allure
import pytest
from playwright.sync_api import Page

from pages.cart_page import CartPage
from pages.login_page import LoginPage
from pages.product_page import ProductPage
from pages.search_page import SearchPage
from utils.config_loader import data_file_for_env, load_test_data
from utils.exceptions import AutomationStepError


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--env",
        action="store",
        default="default",
        help=(
            "Test data environment: 'default' uses data/data.json; "
            "any other value uses data/data.<env>.json and optionally .env.<env>."
        ),
    )
    parser.addoption(
        "--trace-on",
        action="store_true",
        default=False,
        help="Enable Playwright tracing and attach per-test trace zip to Allure.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session: pytest.Session) -> None:
    if session.config.getoption("collectonly"):
        return

    for output_dir in (Path("results"), Path("allure-results")):
        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
        output_dir.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def test_data(request: pytest.FixtureRequest) -> Dict:
    env = request.config.getoption("--env")
    data_path = data_file_for_env(env)
    return load_test_data(data_path, dotenv_suffix=env)


@pytest.fixture(scope="session")
def base_url(test_data: Dict) -> str:
    return test_data["base_url"]


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, test_data: Dict):  # type: ignore[no-untyped-def]
    context_args = {
        **browser_context_args,
        "viewport": {
            "width": test_data.get("viewport", {}).get("width", 1440),
            "height": test_data.get("viewport", {}).get("height", 900),
        },
        "locale": test_data.get("locale", "en-US"),
    }
    return context_args


@pytest.fixture
def traced_page(page: Page, request: pytest.FixtureRequest) -> Generator[Page, None, None]:
    trace_on = bool(request.config.getoption("--trace-on"))
    if trace_on:
        page.context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield page

    if not trace_on:
        return

    trace_path = Path("results") / f"{request.node.name}_trace.zip"
    try:
        page.context.tracing.stop(path=str(trace_path))
        allure.attach.file(
            str(trace_path),
            name=f"{request.node.name}_trace",
            attachment_type=allure.attachment_type.ZIP,
        )
    except Exception:
        # Context/browser may already be closed on abrupt failures.
        pass


@pytest.fixture
def pages(traced_page: Page):
    return {
        "login": LoginPage(traced_page),
        "search": SearchPage(traced_page),
        "product": ProductPage(traced_page),
        "cart": CartPage(traced_page),
    }


@pytest.fixture(autouse=True)
def clear_cart_before_each_test(pages, base_url, test_data):  # type: ignore[no-untyped-def]
    login_page = pages["login"]
    cart_page = pages["cart"]

    credentials = test_data.get("credentials", {})
    username = credentials.get("username", "")
    password = credentials.get("password", "")

    # Retry once because eBay frequently gates login with transient anti-bot steps.
    for attempt in range(2):
        try:
            login_page.open_sign_in(base_url)
            login_page.login(username, password)
            login_page.assert_logged_in()
            cart_page.clear_cart()
            return
        except (AutomationStepError, Exception):
            if attempt == 1:
                pytest.skip(
                    "Setup blocked by eBay security/cart transient issue (captcha, login flow, or cart UI actions)."
                )
            continue


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):  # type: ignore[no-untyped-def]
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or report.passed:
        return

    page = item.funcargs.get("traced_page")
    if not page:
        return

    screenshot_path = Path("results") / f"{item.name}_failure.png"
    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
        allure.attach.file(
            str(screenshot_path),
            name=f"{item.name}_failure",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception:
        # Avoid INTERNALERROR when page/context is already closed.
        return
