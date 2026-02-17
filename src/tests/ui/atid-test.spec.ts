import { test } from '../../fixtures/baseTest';

test('Navigate to store page and change order', async ({ atidHomePage, atidStorePage }) => {
    await test.step('Navigate to home page and verify home page loaded successfully', async () => {
        await atidHomePage.navigateToHomePage();
        await atidHomePage.verifyHomePage();
    });

    await test.step('Navigate to store page and verify store page', async () => {
        await atidHomePage.clickShopNewButton();
        await atidStorePage.verifyStorePage();
    });  
    
    await test.step('Go to page 2 in store page and change order by date', async () => {
        await atidStorePage.clickStorePageTwo();
        await atidStorePage.changeOrderOfStoreResult('date');
    }); 
});
