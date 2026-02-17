#!/usr/bin/env ts-node

import { execSync } from 'child_process';

interface TestModules {
  [key: string]: string;
}

const testModules: TestModules = {
  'sanity': 'npm run test:sanity',
  'logic': 'npm run test:logic', 
  'error': 'npm run test:error',
  'all': 'npm test',
  'headed': 'npm run test:headed',
  'debug': 'npm run test:debug',
  'api_test': 'npm run test:api_test'
};

const module = process.argv[2];

if (!module || !testModules[module]) {
  console.log('Available test modules:');
  console.log('  sanity  - Run sanity tests only');
  console.log('  logic   - Run logic tests only');
  console.log('  error   - Run error handling tests only');
  console.log('  all     - Run all tests');
  console.log('  headed  - Run all tests with browser UI');
  console.log('  debug   - Run all tests in debug mode');
  console.log('\nUsage: npx ts-node run-tests.ts <module>');
  process.exit(1);
}

console.log(`Running ${module} tests...`);
console.log(`Command: ${testModules[module]}`);

try {
  execSync(testModules[module], { stdio: 'inherit' });
} catch (error) {
  console.error('Test execution failed:', error instanceof Error ? error.message : 'Unknown error');
  process.exit(1);
} 