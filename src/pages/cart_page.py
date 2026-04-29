import allure
import re
from playwright.sync_api import Page, expect

from src.pages.base_page import BasePage
from src.utils.currency_converter import convert_amount, extract_currency_code
from src.utils.price_parser import parse_price_to_float


class CartPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.cart_link = (
            self.page.get_by_role(
                "link",
                name=re.compile(r"(your shopping cart contains|shopping cart|cart)", re.IGNORECASE),
            )
            .or_(self.page.get_by_role("link", name=re.compile(r"cart", re.IGNORECASE)))
            .first
        )
        self.cart_buckets = (
            self.page.locator("[data-test-id='cart-bucket']")
            .or_(self.page.locator("div.cart-bucket"))
            .or_(self.page.locator("li[data-test-id*='line-item'], .cart-bucket-line-item"))
        )

        subtotal_container = self.page.locator("div[data-test-id='SUBTOTAL']").first
        subtotal_text_node = subtotal_container.locator("span").filter(
            has_text=re.compile(r"(?:[A-Z]{3}|[$€£₪])\s*\d", re.IGNORECASE)
        )
        self.subtotal_locator = subtotal_text_node.last.or_(subtotal_container).first

        self.remove_buttons = self.page.get_by_role("button", name=re.compile(r"remove", re.IGNORECASE))
        self.remove_links = self.page.get_by_role("link", name=re.compile(r"remove", re.IGNORECASE))
        self.empty_cart_indicators = self.page.locator(
            "text=Your cart is empty, text=You don't have any items in your cart"
        )
        self.alert_close_buttons = self.page.get_by_role("button", name=re.compile(r"close", re.IGNORECASE))
    
    @allure.step("Clear cart to start test from fresh state")
    def clear_cart(self) -> None:
        self.click(self.cart_link)
        self.page.wait_for_load_state("domcontentloaded")

        max_rounds = 20
        for _ in range(max_rounds):
            if self.empty_cart_indicators.count() > 0 and self.empty_cart_indicators.first.is_visible():
                break

            bucket_count = self.cart_buckets.count()
            if bucket_count == 0:
                break

            # Remove only items currently shown on the page, based on current bucket count.
            for idx in range(bucket_count):
                # Always target first visible bucket because DOM reindexes after each removal.
                bucket = self.cart_buckets.first
                bucket_remove_button = bucket.get_by_role("button", name=re.compile(r"remove", re.IGNORECASE)).first
                bucket_remove_link = bucket.get_by_role("link", name=re.compile(r"remove", re.IGNORECASE)).first

                target = None
                if bucket_remove_button.count() > 0:
                    target = bucket_remove_button
                elif bucket_remove_link.count() > 0:
                    target = bucket_remove_link

                if target is None:
                    # Fallback to global remove controls if bucket-level controls are not discoverable.
                    if self.remove_buttons.count() > 0:
                        target = self.remove_buttons.first
                    elif self.remove_links.count() > 0:
                        target = self.remove_links.first
                    else:
                        break

                try:
                    target.click(timeout=5000)
                except Exception:
                    if self.alert_close_buttons.count() > 0:
                        try:
                            self.alert_close_buttons.first.click(timeout=2000)
                        except Exception:
                            pass
                    try:
                        target.click(force=True, timeout=5000)
                    except Exception:
                        # If this row cannot be removed reliably, move on and avoid failing setup.
                        continue

                self.page.wait_for_timeout(700)

    @allure.step("Assert cart subtotal does not exceed budget threshold")
    def assert_cart_total_not_exceeds(
        self, budget_per_item: float, items_count: int, budget_currency: str
    ) -> None:
        threshold = budget_per_item * items_count
        self.click(self.cart_link)

        if items_count == 0:
            self.page.screenshot(path="results/cart_page.png", full_page=True)
            allure.attach.file(
                "results/cart_page.png",
                name="cart_page",
                attachment_type=allure.attachment_type.PNG,
            )
            return

        expect(self.subtotal_locator).to_be_visible(timeout=15000)

        subtotal_text = self.subtotal_locator.inner_text()
        subtotal_value = parse_price_to_float(subtotal_text)
        subtotal_currency = extract_currency_code(subtotal_text) or budget_currency
        subtotal_in_budget_currency = convert_amount(
            subtotal_value, from_currency=subtotal_currency, to_currency=budget_currency
        )

        self.page.screenshot(path="results/cart_page.png", full_page=True)
        allure.attach.file(
            "results/cart_page.png",
            name="cart_page",
            attachment_type=allure.attachment_type.PNG,
        )

        assert subtotal_in_budget_currency <= threshold, (
            f"Cart subtotal {subtotal_value:.2f} {subtotal_currency} "
            f"({subtotal_in_budget_currency:.2f} {budget_currency}) "
            f"exceeds threshold {threshold:.2f} {budget_currency}"
        )
