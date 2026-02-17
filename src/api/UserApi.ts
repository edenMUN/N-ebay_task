import { APIRequestContext, expect } from '@playwright/test';
import { ReqresEndpoints } from '@/utils/endpoints'

// Example for API testing
export class UserApi {
    private request: APIRequestContext;

    constructor(request: APIRequestContext) {
        this.request = request;
    }

    async createUser(name: string, job: string) {
        if (!process.env['API_KEY']) {
            throw new Error('Missing API_KEY in environment variables!');
        }
        const response = await this.request.post(ReqresEndpoints.USERS, {
            data: { name, job },
            headers: {
                'x-api-key': process.env['API_KEY']
            }
        });
        
        if (!response.ok()) {
            throw new Error(`Failed to create user: ${response.statusText()}`);
        }
        expect(response.status()).toBe(201);
        
        return await response.json();
    }
}