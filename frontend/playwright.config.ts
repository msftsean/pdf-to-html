import { defineConfig, devices } from '@playwright/test';

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:3000';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // Tests depend on upload state
  retries: 1,
  timeout: 120_000, // 2 minutes — conversions take time
  expect: { timeout: 30_000 },
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
