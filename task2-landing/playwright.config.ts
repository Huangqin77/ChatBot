import { defineConfig } from '@playwright/test'

const externalUrl = process.env.PLAYWRIGHT_BASE_URL
const production = process.env.PLAYWRIGHT_PRODUCTION === '1'
const testPort = production ? 14174 : 15174
const localUrl = `http://127.0.0.1:${testPort}`

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  reporter: 'list',
  use: {
    baseURL: externalUrl || localUrl,
    headless: true,
    channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge',
    reducedMotion: 'reduce',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: externalUrl ? undefined : {
    command: production ? `npm run preview -- --port ${testPort} --strictPort` : `npm run dev -- --port ${testPort} --strictPort`,
    url: localUrl,
    reuseExistingServer: false,
    timeout: 30_000,
  },
})
