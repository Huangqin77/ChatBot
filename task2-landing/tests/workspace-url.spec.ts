import { expect, test } from '@playwright/test'
import { resolveWorkspaceTarget } from '../src/lib/workspace-url'

test('生产版没有公开工作台配置时，始终回到本页演示', () => {
  for (const value of [undefined, '', 'bad-url', 'javascript:alert(1)', 'http://localhost:5173', 'https://localhost:5173', 'https://localhost.', 'https://127.0.0.1', 'https://192.168.1.2', 'https://[::1]', 'https://workspace.internal', 'https://workspace.local', 'https://user:password@workspace.collabai.com']) {
    expect(resolveWorkspaceTarget(value, false), String(value)).toEqual({ href: '#product-preview', demo: true })
  }
})

test('公开 HTTPS 工作台可以启用，本地开发保留任务一默认地址', () => {
  expect(resolveWorkspaceTarget('https://workspace.collabai.com', false)).toEqual({ href: 'https://workspace.collabai.com/', demo: false })
  expect(resolveWorkspaceTarget(undefined, true)).toEqual({ href: 'http://localhost:5173', demo: false })
})
