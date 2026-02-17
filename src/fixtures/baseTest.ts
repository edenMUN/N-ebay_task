import { test as base } from '@playwright/test';
import { aiFixture, type AiFixture } from '@zerostep/playwright';
import { AtidHomePage } from '../pages/AtidHomePage';
import { AtidStorePage } from '../pages/AtidStorePage';
// Define the types for your fixtures
type MyFixtures = {
    atidHomePage: AtidHomePage;
    atidStorePage: AtidStorePage;
} & AiFixture;

// Extend the base test
export const test = base.extend<MyFixtures>({
    ...aiFixture(base),
    atidHomePage: async ({ page }, use) => {
        // Instantiate the page object
        const homePage = new AtidHomePage(page);
        // "use" makes it available to the tests
        await use(homePage);
    },

    atidStorePage: async ({ page }, use) => {
        const storePage = new AtidStorePage(page);
        await use(storePage);
    },
});

export { expect } from '@playwright/test';
