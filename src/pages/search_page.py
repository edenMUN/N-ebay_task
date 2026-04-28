import re
from time import monotonic
from typing import List

import allure
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect

from pages.base_page import BasePage
from utils.exceptions import AutomationStepError
from utils.price_parser import parse_price_to_float


class SearchPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.search_input = self.page.get_by_role("combobox", name="Search for anything")
        self.search_button = self.page.get_by_role("button", name="Search", exact=True)
        self.results_heading = self.page.locator(
            "h1.srp-controls__count-heading, .srp-controls__count-heading"
        )
        self.max_price_input_by_role = self.page.get_by_role(
            "textbox", name=re.compile(r"maximum value", re.IGNORECASE)
        )
        self.max_price_input_by_label = self.page.get_by_label("Maximum value", exact=False)
        self.max_price_input_css_fallback = self.page.locator(
            "input[aria-label*='Maximum value'], input[aria-label*='Maximum Value']"
        ).first
        self.submit_price_range_button = self.page.get_by_role("button", name="Submit price range").first
        self.active_price_filter_indicator = self.page.locator(
            ".x-refine__main__value--name, .srp-format-tabs-h2, li[aria-label*='To']"
        )
        self.results_list = self.page.locator("ul.srp-results").first
        self.result_cards = self.page.locator("li.s-item, li.srp-results__item, li:has(a.s-card__link)")
        self.next_page_button = self.page.get_by_role("link", name="Go to next search page")

    def _wait_out_search_challenge(self, timeout_seconds: int = 45) -> None:
        if "/splashui/challenge" not in self.page.url:
            return

        print("[!] Security challenge detected after search. Please resolve manually...")
        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            if "/splashui/challenge" not in self.page.url:
                return
            self.page.wait_for_timeout(1000)

        raise AutomationStepError(
            "eBay anti-bot challenge is still active after smart wait. "
            "Retry with headed mode and resolve it manually."
        )

    # @allure.step("Open eBay home page")
    # def open_home(self, base_url: str) -> None:
    #     self.goto(base_url)

    @allure.step("Search for query: {query}")
    def search(self, query: str) -> None:
        self.fill(self.search_input, query)
        self.click(self.search_button)
        self._wait_out_search_challenge(timeout_seconds=45)
        expect(self.results_heading).to_be_visible()

    @allure.step("Apply maximum price filter: {max_price}")
    def apply_max_price_filter(self, max_price: float) -> None:
        max_input = None
        for candidate in (
            self.max_price_input_by_role.first,
            self.max_price_input_by_label.first,
            self.max_price_input_css_fallback,
        ):
            try:
                candidate.wait_for(state="visible", timeout=3000)
                max_input = candidate
                break
            except Exception:
                continue

        if max_input is None:
            print("[!] Price filter sidebar not found on this page. Proceeding without filtering.")
            allure.attach(
                "Price filter not found - possibly due to page layout or single result.",
                name="Filter Info",
                attachment_type=allure.attachment_type.TEXT
            )
            return

        max_input.click()
        max_input.fill(str(int(max_price)))
        self.page.wait_for_timeout(500)

        try:
            expect(self.submit_price_range_button).to_be_enabled(timeout=5000)
            self.click(self.submit_price_range_button)
        except (PlaywrightTimeoutError, AssertionError):
            # Some eBay layouts apply price range when pressing Enter in the max field.
            max_input.press("Enter")

        expect(self.active_price_filter_indicator.first).to_be_visible(timeout=10000)

    def _eligible_item_cards_for_price(self, max_price: float):
        del max_price  # filtering is finalized in Python after robust parsing.
        return self.result_cards.filter(
            has=self.page.locator("a.s-item__link, a.s-card__link, a[href*='/itm/'], a[href*='ebay.com/itm']")
        )

    def _extract_price_text_from_card(self, card) -> str:
        price_candidates = card.locator(
            ".s-item__price, .s-card__price, [data-testid*='price'], "
            "span:has-text('ILS'), span:has-text('₪'), span:has-text('$')"
        )
        for idx in range(price_candidates.count()):
            candidate = price_candidates.nth(idx)
            try:
                if candidate.is_visible(timeout=500):
                    text = candidate.inner_text(timeout=1000).strip()
                    if text:
                        return text
            except Exception:
                continue

        # Fallback: parse entire card text when dedicated price nodes vary by layout.
        return card.inner_text(timeout=2000).strip()

    def _collect_item_urls_from_current_page(
        self, max_price: float, remaining_slots: int, seen_urls: set[str]
    ) -> List[str]:
        self.results_list.wait_for(state="visible", timeout=15000)
        try:
            self.result_cards.first.wait_for(state="visible", timeout=5000)
        except Exception:
            return []

        cards_to_scan = self._eligible_item_cards_for_price(max_price)
        if cards_to_scan.count() == 0:
            return []

        urls: List[str] = []
        for index in range(cards_to_scan.count()):
            if len(urls) >= remaining_slots:
                break

            card = cards_to_scan.nth(index)
            card_link = card.locator(
                "a.s-item__link, a.s-card__link, a[href*='/itm/'], a[href*='ebay.com/itm']"
            ).first

            href = card_link.get_attribute("href")
            if href and "?" in href:
                href = href.split("?")[0]
            try:
                price_text = self._extract_price_text_from_card(card)
            except Exception:
                continue
            if not href or href in seen_urls or not price_text:
                continue
            if not self._is_valid_item_url(href):
                continue

            # Final integrity validation in Python, even after XPath filtering.
            try:
                normalized_price_text = self._extract_primary_price_text(price_text)
                item_price = parse_price_to_float(normalized_price_text)
            except ValueError:
                continue

            if item_price <= max_price:
                seen_urls.add(href)
                urls.append(href)

        return urls

    def _extract_primary_price_text(self, raw_price_text: str) -> str:
        # eBay often includes range/shipping in the same label.
        # Take the first numeric amount so integrity parsing can still work.
        match = re.search(r"\d[\d,]*(?:\.\d{1,2})?", raw_price_text)
        if not match:
            raise ValueError(f"Could not extract numeric value from price text: {raw_price_text}")
        return match.group(0)

    def _is_valid_item_url(self, href: str) -> bool:
        return bool(
            re.match(r"^https?://(?:www\.)?ebay\.[^/]+/itm/\d{9,}(?:/|$)", href.strip(), re.IGNORECASE)
        )

    def _can_go_to_next_page(self) -> bool:
        return self.next_page_button.count() > 0 and self.next_page_button.first.is_enabled()

    @allure.step("Collect up to {limit} item URLs under max price")
    def search_items_by_name_under_price(self, query: str, max_price: float, limit: int = 5) -> List[str]:
        self.search(query)
        self.apply_max_price_filter(max_price)

        collected_urls: List[str] = []
        seen_urls: set[str] = set()
        while len(collected_urls) < limit:
            self.results_list.wait_for(state="visible", timeout=15000)
            remaining = limit - len(collected_urls)
            page_urls = self._collect_item_urls_from_current_page(max_price, remaining, seen_urls)
            collected_urls.extend(page_urls)

            if len(collected_urls) >= limit:
                break
            if not self._can_go_to_next_page():
                break
            self.next_page_button.first.click()
            try:
                self.page.wait_for_load_state("domcontentloaded")
            except Exception:
                break

        print(f"Collected URLs: {collected_urls}")
        return collected_urls
