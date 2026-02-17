import { test, expect } from '@playwright/test';
import { UserApi } from '../../api/UserApi';

test.describe('User API Tests', () => {
    
    test('should successfully create a new user', async ({ request }) => {
        const userApi = new UserApi(request);

        const name = 'Eden';
        const job = 'QA Automation';

        const responseData = await userApi.createUser(name, job);
        
        expect(responseData.name).toBe(name);
        expect(responseData.job).toBe(job);
        
        console.log('User created with ID:', responseData.id);
    });

});