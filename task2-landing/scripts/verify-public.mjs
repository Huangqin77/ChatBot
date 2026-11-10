// 不携带 Cookie、Authorization 或 Vercel 绕过参数，验证匿名 HTTPS 访问。
const input = process.argv[2]
if (!input) throw new Error('用法：node scripts/verify-public.mjs https://你的实际生产域名')
const target = new URL(input)
if (target.protocol !== 'https:' || /localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]/i.test(target.hostname)) {
  throw new Error('必须提供真实公开 HTTPS 地址；localhost 不能作为部署验收地址。')
}
const response = await fetch(target, { redirect: 'follow', signal: AbortSignal.timeout(30_000) })
if (!response.ok) throw new Error(`首页匿名访问失败：HTTP ${response.status}`)
const html = await response.text()
if (!/<title>CollabAI/.test(html)) throw new Error('没有获得 CollabAI 页面；请检查域名和 Deployment Protection 登录限制。')
console.log(`HTTP ${response.status} ${response.url}（未发送登录凭据）`)
const resources = [...html.matchAll(/(?:src|href)=["']([^"']+\.(?:js|css|svg)(?:\?[^"']*)?)["']/g)].map(match => new URL(match[1], response.url).href)
if (!resources.some(url => /\.js(?:\?|$)/.test(url)) || !resources.some(url => /\.css(?:\?|$)/.test(url))) throw new Error('缺少生产 JS/CSS 引用。')
for (const url of new Set(resources)) {
  const asset = await fetch(url, { redirect: 'follow', signal: AbortSignal.timeout(30_000) })
  const type = asset.headers.get('content-type') || ''
  if (!asset.ok || type.includes('text/html')) throw new Error(`资源加载失败：${asset.status} ${type} ${url}`)
  console.log(`HTTP ${asset.status} ${url} (${type})`)
}
console.log('公开首页与 HTML 引用的 JS/CSS/SVG 资源通过匿名 HTTP 验证。仍需运行无登录浏览器测试。')
