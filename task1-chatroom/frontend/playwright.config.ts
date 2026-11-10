import { defineConfig } from '@playwright/test'
import path from 'node:path'
import os from 'node:os'
import { mkdtempSync } from 'node:fs'

// Browser acceptance must never reuse a developer's server, credentials or database.
const testDataDir = mkdtempSync(path.join(os.tmpdir(), 'relay-e2e-'))
const apiPort = 18000
const frontendPort = 15173

export default defineConfig({
  testDir: './tests',
  timeout: 45000,
  expect: { timeout: 10000 },
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    channel: 'msedge',
    headless: true,
    viewport: { width: 1440, height: 960 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: [
    { command: `.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port ${apiPort}`,
      cwd: path.resolve(import.meta.dirname, '../backend'), url: `http://127.0.0.1:${apiPort}/api/health`,
      env: { LLM_MODE: 'demo', OPENAI_API_KEY: '', DATABASE_URL: `sqlite:///${path.join(testDataDir, 'chatroom.db').replaceAll('\\', '/')}` },
      reuseExistingServer: false },
    { command: `npm run dev -- --port ${frontendPort}`, url: `http://127.0.0.1:${frontendPort}`,
      env: { RELAY_BACKEND_URL: `http://127.0.0.1:${apiPort}` }, reuseExistingServer: false },
  ],
})
