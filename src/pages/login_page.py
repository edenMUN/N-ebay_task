import allure
from time import monotonic
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect

from pages.base_page import BasePage
from utils.exceptions import AutomationStepError


class LoginPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.username_input = self.page.locator(
            "#userid, input[name='userid'], input[autocomplete='username']"
        ).first
        self.continue_button = self.page.locator(
            "#signin-continue-btn, button:has-text('Continue')"
        ).first
        self.password_input = self.page.locator(
            "#pass, input[name='pass'], input[autocomplete='current-password']"
        ).first
        self.submit_login_button = self.page.locator("#sgnBt, button:has-text('Sign in')").first
        self.account_button = self.page.get_by_role("button", name="My eBay")
        self.sign_out_link = self.page.get_by_role("link", name="Sign out")
        self.signed_in_indicators = self.page.locator(
            "#gh-ug, a[href*='Signout'], button:has-text('My eBay')"
        )
        self.not_now_button = self.page.get_by_role("button", name="Not now")
        self.skip_for_now_link = self.page.get_by_role("link", name="Skip for now")
        self.not_now_text = self.page.get_by_text("Not now")
        self.home_sign_in_link = self.page.get_by_role("link", name="Sign in")
        self.signin_continue_error = self.page.locator(
            "#errf, .page-notice--status, .textbox--error, [data-testid='signin-error-message']"
        )

    @allure.step("Open eBay sign in page")
    def open_sign_in(self, base_url: str) -> None:
        self.goto(base_url)
        if self.home_sign_in_link.is_visible(timeout=5000):
            self.home_sign_in_link.click()
            self.page.wait_for_load_state("domcontentloaded")
            return
        self.goto(f"{base_url}/signin/")

    def _dismiss_optional_pin_prompt(self) -> None:
        for locator in (self.not_now_button, self.skip_for_now_link, self.not_now_text):
            try:
                if locator.first.is_visible(timeout=1000):
                    locator.first.click()
                    return
            except Exception:
                continue

    def _wait_for_signin_form_or_manual_challenge(self, timeout_seconds: int = 45) -> None:
        if self.username_input.is_visible(timeout=5000):
            return

        print("[!] Security challenge (Captcha) suspected before login form. Please resolve manually...")
        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            if self.username_input.is_visible(timeout=1000):
                return
        raise AutomationStepError(
            "Sign-in form did not appear after smart wait. Resolve captcha/security challenge manually "
            "and retry in headed mode."
        )

    def _wait_for_password_step_or_manual_resolution(self, timeout_seconds: int = 45) -> None:
        if self.password_input.is_visible(timeout=3000):
            return

        print("[!] Waiting for password step or challenge resolution...")
        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            if self.password_input.is_visible(timeout=1000):
                return

            # Retry continue in case eBay didn't advance to password step.
            try:
                if self.continue_button.is_visible(timeout=500) and self.continue_button.is_enabled():
                    self.continue_button.click()
            except Exception:
                pass

            # If challenge route appears, wait for manual solve and continue.
            if "/splashui/captcha" in self.page.url or "/splashui/challenge" in self.page.url:
                self.page.wait_for_timeout(1000)

            # Surface known inline sign-in errors fast.
            try:
                if self.signin_continue_error.first.is_visible(timeout=500):
                    message = self.signin_continue_error.first.inner_text(timeout=1000)
                    raise AutomationStepError(f"Sign-in did not proceed to password step: {message}")
            except AutomationStepError:
                raise
            except Exception:
                pass

        raise AutomationStepError(
            "Password step did not appear after smart wait. "
            "Resolve challenge manually and verify the username is accepted."
        )

    @allure.step("Login with provided credentials")
    def login(self, username: str, password: str) -> None:
        self._wait_for_signin_form_or_manual_challenge(timeout_seconds=45)
        self.fill(self.username_input, username)
        self.click(self.continue_button)
        self._wait_for_password_step_or_manual_resolution(timeout_seconds=45)
        self.fill(self.password_input, password)
        self.click(self.submit_login_button)
        self._dismiss_optional_pin_prompt()

        try:
            expect(self.signed_in_indicators.first).to_be_visible(timeout=10000)
            return
        except PlaywrightTimeoutError:
            print("[!] Security challenge (Captcha) suspected. Please resolve manually...")

        deadline = monotonic() + 45
        while monotonic() < deadline:
            self._dismiss_optional_pin_prompt()
            if self.account_button.is_visible() or self.sign_out_link.is_visible():
                return
            try:
                expect(self.signed_in_indicators.first).to_be_visible(timeout=2000)
                return
            except PlaywrightTimeoutError:
                continue

        screenshot_path = "results/login_security_challenge_failure.png"
        self.page.screenshot(path=screenshot_path, full_page=True)
        allure.attach.file(
            screenshot_path,
            name="login_security_challenge_failure",
            attachment_type=allure.attachment_type.PNG,
        )
        raise AutomationStepError(
            "Login failed after smart wait. Resolve captcha/security challenge manually "
            "and retry in headed mode."
        )

    @allure.step("Verify login succeeded")
    def assert_logged_in(self) -> None:
        if self.account_button.is_visible() or self.sign_out_link.is_visible():
            return

        try:
            expect(self.signed_in_indicators.first).to_be_visible(timeout=5000)
        except PlaywrightTimeoutError as exc:
            raise AutomationStepError(
                "Login validation failed. Signed-in indicator not visible after smart wait."
            ) from exc
