from playwright.sync_api import Locator, Page, expect


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded")

    def wait_visible(self, locator: Locator, timeout: int = 15000) -> None:
        expect(locator).to_be_visible(timeout=timeout)

    def click(self, locator: Locator, timeout: int = 15000) -> None:
        locator.wait_for(state="visible", timeout=timeout)
        locator.click()

    def fill(self, locator: Locator, value: str, timeout: int = 15000) -> None:
        locator.wait_for(state="visible", timeout=timeout)
        locator.fill(value)
