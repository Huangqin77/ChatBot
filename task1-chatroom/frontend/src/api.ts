import type { User } from './types'

const KEY = 'relay.user'
export function savedUser(): User | null {
  try { return JSON.parse(sessionStorage.getItem(KEY) || 'null') } catch { return null }
}
export function saveUser(user: User | null) {
  if (user) sessionStorage.setItem(KEY, JSON.stringify(user))
  else sessionStorage.removeItem(KEY)
}
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const user = savedUser()
  const response = await fetch('/api' + path, { ...options, headers: {
    'Content-Type': 'application/json', ...(user ? { Authorization: `Bearer ${user.token}` } : {}), ...options.headers,
  } })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(typeof body.detail === 'string' ? body.detail : `请求失败 (${response.status})，请检查输入和服务状态`)
  }
  return response.json()
}
export function merge<T extends { id: string }>(old: T[], incoming: T[]): T[] {
  const rows = new Map(old.map(row => [row.id, row]))
  incoming.forEach(row => rows.set(row.id, row))
  return [...rows.values()]
}
