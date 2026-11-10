import { resolveWorkspaceTarget } from './workspace-url'

const workspace = resolveWorkspaceTarget(import.meta.env.VITE_APP_URL, import.meta.env.DEV)
export const APP_URL = workspace.href
export const IS_WORKSPACE_DEMO = workspace.demo
export const navigation = [
  { label: '产品功能', href: '#features' },
  { label: '工作流程', href: '#workflow' },
  { label: '应用场景', href: '#use-cases' },
  { label: '常见问题', href: '#faq' },
]
