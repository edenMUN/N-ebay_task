import allure
import pytest


@allure.title("Complete eBay flow: login, search, add to cart, validate budget")
@allure.description(
    "Logs into eBay, searches items under a maximum price with paging, adds items to cart, "
    "and validates cart subtotal does not exceed configured budget."
)
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
def test_ebay_login_search_add_and_validate_budget(pages, test_data, base_url) -> None:
    search_query = test_data["search"]["query"]
    max_price = float(test_data["search"]["max_price"])
    result_limit = int(test_data["search"]["limit"])
    budget_per_item = float(test_data["budget"]["per_item"])
    budget_currency = str(test_data["budget"]["currency"])

    allure.dynamic.title(f"eBay flow: '{search_query}' under {max_price:.2f}")

    search_page = pages["search"]
    product_page = pages["product"]
    cart_page = pages["cart"]

    with allure.step("Prepare test parameters"):
        # Login + cart cleanup are handled by autouse fixture in conftest.py.
        pass

    with allure.step("Search for items under maximum price"):
        item_urls = search_page.search_items_by_name_under_price(
            query=search_query,
            max_price=max_price,
            limit=result_limit,
        )
        assert len(item_urls) > 0, f"Search for '{search_query}' returned 0 results. Check query or selectors."

    with allure.step("Add selected items to cart"):
        search_page_url = search_page.page.url
        added_items_count = product_page.add_items_to_cart(item_urls, search_page_url)

        assert added_items_count > 0, (
            f"Items were found but NONE could be added to cart. "
            f"This might indicate missing 'Add to Cart' buttons or Selector issues."
        )

    with allure.step("Verify cart subtotal is within budget"):
        cart_page.assert_cart_total_not_exceeds(
            budget_per_item=budget_per_item,
            items_count=added_items_count,
            budget_currency=budget_currency,
        )
