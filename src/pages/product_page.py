import re
from typing import List

import allure
from playwright.sync_api import Page, expect

from src.pages.base_page import BasePage
from src.utils.exceptions import AutomationStepError


class ProductPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.add_to_cart_button = (
            self.page.get_by_role("button", name=re.compile(r"add to (cart|basket)", re.IGNORECASE))
            .or_(self.page.locator("#atcBtn_btn_1"))
            .or_(self.page.get_by_role("link", name=re.compile(r"add to (cart|basket)", re.IGNORECASE)))
            .first
        )
        self.added_to_cart_confirmation = (
            self.page.get_by_role(
                "status",
                name=re.compile(r"(added to cart|item added|added)", re.IGNORECASE),
            )
            .or_(self.page.get_by_text(re.compile(r"added to cart", re.IGNORECASE)))
            .first
        )
        self.see_in_cart = self.page.get_by_role(
            "link", name=re.compile(r"(see in cart|view in cart)", re.IGNORECASE)
        )
        self.cart_counter = (
            self.page.locator("#gh-cart-n")
            .or_(self.page.get_by_label(re.compile(r"shopping cart contains \d+ items?", re.IGNORECASE)))
            .or_(self.page.locator("[aria-label*='shopping cart contains']"))
            .first
        )
        self.cart_icon = (
            self.page.get_by_label(re.compile(r"shopping cart contains", re.IGNORECASE))
            .or_(self.page.get_by_role("link", name=re.compile(r"shopping cart", re.IGNORECASE)))
            .first
        )
        self.go_to_cart_link = self.page.get_by_role(
            "link", name=re.compile(r"(go to cart|view cart|cart)", re.IGNORECASE)
        )

    def _cart_count(self) -> int:
        # Preferred: visible cart badge text.
        if self.cart_counter.count() > 0:
            raw = (self.cart_counter.inner_text() or "").strip()
            if raw.isdigit():
                return int(raw)
        if self.cart_icon.count() > 0:
            label = self.cart_icon.get_attribute("aria-label") or ""
            match = re.search(r"contains\s+(\d+)\s+items?", label.lower())
            if match:
                return int(match.group(1))
        return 0

    def _assert_added_to_cart(self) -> None:
        try:
            expect(self.added_to_cart_confirmation).to_be_visible(timeout=12000)
            return
        except Exception:
            if self.see_in_cart.count() and self.see_in_cart.is_visible():
                return

            raise AutomationStepError("Could not verify cart addition after clicking 'Add to cart'.")

    def _is_placeholder_or_unavailable(self, text: str, value: str = "") -> bool:
        normalized = (text or "").strip().lower()
        normalized_value = (value or "").strip().lower()
        return (
            normalized in ("", "select", "- select -", "choose", "choose an option")
            or normalized.startswith("select ")
            or normalized_value in ("", "-1", "select", "none")
            or "out of stock" in normalized
            or "unavailable" in normalized
            or "sold out" in normalized
        )

    def _select_first_from_native_select(self, select_locator) -> bool:
        options = select_locator.locator("option")
        for idx in range(options.count()):
            option = options.nth(idx)
            option_text = (option.inner_text() or "").strip()
            option_value = option.get_attribute("value") or ""
            disabled_attr = option.get_attribute("disabled")
            aria_disabled = option.get_attribute("aria-disabled")
            if disabled_attr is not None or aria_disabled == "true":
                continue
            if self._is_placeholder_or_unavailable(option_text, option_value):
                continue
            select_locator.select_option(value=option_value)
            self.page.wait_for_timeout(350)
            return True
        return False

    def _select_first_from_custom_listbox(self, listbox_trigger) -> bool:
        listbox_trigger.click()
        self.page.wait_for_timeout(300)

        controls_id = listbox_trigger.get_attribute("aria-controls") or ""
        if controls_id:
            options = self.page.locator(
                f"#{controls_id} [role='option']:visible, "
                f"#{controls_id} li[role='option']:visible, "
                f"#{controls_id} .listbox__option:visible"
            )
        else:
            options = self.page.locator(
                "[role='option']:visible, li[role='option']:visible, .listbox__option:visible"
            )

        for idx in range(options.count()):
            option = options.nth(idx)
            option_text = (option.inner_text() or "").strip()
            aria_disabled = option.get_attribute("aria-disabled")
            class_name = (option.get_attribute("class") or "").lower()
            sku_value_name = option.get_attribute("data-sku-value-name") or ""
            if aria_disabled == "true" or "disabled" in class_name:
                continue
            if self._is_placeholder_or_unavailable(option_text, sku_value_name):
                continue
            option.click()
            self.page.wait_for_timeout(350)
            return True

        try:
            self.page.keyboard.press("Escape")
        except Exception:
            pass
        return False

    def _add_to_cart_enabled(self) -> bool:
        if self.add_to_cart_button.count() == 0:
            return False
        try:
            button = self.add_to_cart_button.first
            if not button.is_visible():
                return False
            disabled_attr = button.get_attribute("disabled")
            aria_disabled = button.get_attribute("aria-disabled")
            classes = (button.get_attribute("class") or "").lower()
            return (
                disabled_attr is None
                and aria_disabled != "true"
                and "disabled" not in classes
            )
        except Exception:
            return False

    def _select_labeled_variant_if_present(self) -> bool:
        # Iterate all variant blocks and select first valid option in each.
        variant_blocks = self.page.locator(".vim.x-sku:visible, .vim-x-sku:visible")
        selected_any = False
        for idx in range(variant_blocks.count()):
            block = variant_blocks.nth(idx)
            custom_trigger = block.locator(
                "button.listbox-button__control[aria-haspopup='listbox'][aria-controls]:visible, "
                "button[aria-haspopup='listbox'][aria-controls]:visible"
            ).first
            try:
                if custom_trigger.count() > 0:
                    if self._select_first_from_custom_listbox(custom_trigger):
                        selected_any = True
                    continue
                native_select = block.locator("select.listbox__native:visible, select:visible").first
                if native_select.count() > 0 and self._select_first_from_native_select(native_select):
                    selected_any = True
            except Exception:
                continue
        return selected_any

    def _handle_item_customizations(self) -> None:
        try:
            self._select_labeled_variant_if_present()
        except Exception:
            pass

    def _click_add_to_cart_once(self) -> None:
        if self.add_to_cart_button.count() == 0:
            raise AutomationStepError("Add to cart button not found on the current item page.")
        try:
            self.add_to_cart_button.click(timeout=10000)
        except Exception:
            self.add_to_cart_button.click(timeout=10000, force=True)

    @allure.step("Add items to cart from collected URLs")
    def add_items_to_cart(self, urls: List[str], search_page_url: str) -> int:
        if not urls:
            return 0
        added_count = 0

        for item_index, url in enumerate(urls, start=1):
            try:
                self.goto(url)
                self.page.wait_for_load_state("domcontentloaded")

                self._handle_item_customizations()
                if not self._add_to_cart_enabled():
                    # One more pass helps pages where selecting one variant re-renders others.
                    self.page.wait_for_timeout(400) # Wait for potential DOM re-render after variant selection
                    self._handle_item_customizations()
                self._click_add_to_cart_once()
                self._assert_added_to_cart()

                self.page.screenshot(path=f"results/item_{item_index}_added.png", full_page=True)
                allure.attach.file(
                    f"results/item_{item_index}_added.png",
                    name=f"Item {item_index} added",
                    attachment_type=allure.attachment_type.PNG,
                )
                print(f"[+] Added item to cart: {url}")
                added_count += 1
            except Exception as item_error:
                print(f"[!] Skipping item (could not add): {url} | reason: {item_error}")
                try:
                    self.page.screenshot(path=f"results/item_{item_index}_failed.png", full_page=True)
                except Exception:
                    pass

        try:
            if not self.page.is_closed():
                self.goto(search_page_url)
        except Exception:
            # Keep return stable even if eBay closes/redirects unexpectedly.
            pass

        return added_count
