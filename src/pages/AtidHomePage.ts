import { Page, Locator, expect } from '@playwright/test';

export class AtidHomePage {
  readonly page: Page;
  readonly homePageInMenu: Locator;
  readonly header: Locator;
  readonly shopNewButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.homePageInMenu = page
      .locator('#menu-item-381')
      .getByRole('link', { name: 'Home' });
    this.header = page.getByRole('heading', { name: 'ATID Demo Store' });
    this.shopNewButton = page.getByRole('button', { name: 'Shop Now' }).first();
  }

  async navigateToHomePage() {
    // Uses baseURL from Playwright config, so '/' resolves to https://atid.store
    await this.page.goto('/');
  }

  async verifyHomePage() {
    await expect(this.homePageInMenu).toBeVisible();
    await expect(this.header).toBeVisible();
    await expect(this.shopNewButton).toBeVisible();
  }

  async clickShopNewButton() {
    await this.shopNewButton.click();
  }
}
