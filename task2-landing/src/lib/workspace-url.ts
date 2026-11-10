export function resolveWorkspaceTarget(value: string | undefined, development: boolean) {
  const fallback = { href: development ? 'http://localhost:5173' : '#product-preview', demo: !development }
  if (!value?.trim()) return fallback
  try {
    const url = new URL(value.trim())
    if (url.username || url.password) return fallback
    if (development && ['http:', 'https:'].includes(url.protocol)) return { href: url.href, demo: false }
    const host = url.hostname.toLowerCase().replace(/\.$/, '')
    const reservedHost = /(^|\.)(localhost|local|internal|lan|home|test|invalid|example)$/.test(host)
    const ipAddress = host.includes(':') || /^\d+(\.\d+){3}$/.test(host)
    if (url.protocol === 'https:' && host.includes('.') && !reservedHost && !ipAddress) {
      return { href: url.href, demo: false }
    }
  } catch { /* 未配置可公开访问的工作台时，生产版始终留在官网演示。 */ }
  return fallback
}
