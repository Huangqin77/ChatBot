import { expect, test } from '@playwright/test'

for (const width of [375, 768, 1440]) {
  test(`${width}px：布局、资源、导航、FAQ、演示场景和工作台入口`, async ({ page, baseURL }) => {
    await page.setViewportSize({ width, height: 1000 })
    const errors: string[] = []
    const externalRequests: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    page.on('requestfailed', request => errors.push(`${request.url()}: ${request.failure()?.errorText}`))
    page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`) })
    page.on('request', request => { if (!request.url().startsWith(new URL(baseURL!).origin) && !request.url().startsWith('data:')) externalRequests.push(request.url()) })
    await page.goto('/')
    await expect(page).toHaveTitle(/CollabAI/)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    const sections = ['features', 'workflow', 'use-cases', 'faq']
    for (const id of sections) await expect(page.locator(`#${id}`)).toBeVisible()

    if (width < 768) {
      const menu = page.getByRole('button', { name: /导航菜单/ })
      await expect(page.getByRole('navigation', { name: '移动端导航' })).toBeHidden()
      await menu.click()
      await expect(menu).toHaveAttribute('aria-expanded', 'true')
      await page.keyboard.press('Escape')
      await expect(menu).toHaveAttribute('aria-expanded', 'false')
      await menu.click()
      await page.getByRole('navigation', { name: '移动端导航' }).getByRole('link', { name: '产品功能' }).click()
      await expect(page).toHaveURL(/#features$/)
      await expect(menu).toHaveAttribute('aria-expanded', 'false')
      await menu.click()
      await page.getByRole('button', { name: '关闭导航菜单' }).click()
      await expect(menu).toHaveAttribute('aria-expanded', 'false')
    } else {
      for (const [index, label] of ['产品功能', '工作流程', '应用场景', '常见问题'].entries()) {
        await page.getByRole('navigation', { name: '主导航', exact: true }).getByRole('link', { name: label }).click()
        await expect(page).toHaveURL(new RegExp(`#${sections[index]}$`))
      }
    }

    const faq = page.getByRole('button', { name: '可以让多个 AI Bot 一起完成任务吗？' })
    await faq.click()
    await expect(faq).toHaveAttribute('aria-expanded', 'true')
    await expect(page.locator('#faq-panel-1')).toBeVisible()
    await faq.click()
    await expect(faq).toHaveAttribute('aria-expanded', 'false')
    await expect(page.locator('#faq-panel-1')).toBeHidden()

    await page.getByRole('button', { name: '研究资料整理', exact: true }).click()
    await expect(page.getByText('主题研究与来源索引.md')).toBeVisible()
    await page.getByRole('button', { name: '数据分析看板', exact: true }).click()
    await expect(page.getByText('项目数据分析报告.md')).toBeVisible()

    const dataTab = page.getByRole('tab', { name: '数据分析辅助' })
    await dataTab.click()
    await expect(dataTab).toHaveAttribute('aria-selected', 'true')
    await expect(page.getByRole('tabpanel')).toContainText('和数据聊一聊')
    await page.keyboard.press('ArrowRight')
    await expect(page.getByRole('tab', { name: '日常办公自动化' })).toBeFocused()
    await expect(page.getByRole('tabpanel')).toContainText('重复的事交给 AI')

    if (process.env.PLAYWRIGHT_PRODUCTION === '1') {
      await expect(page.getByText('当前为产品演示 · 工作台尚未公开部署')).toBeVisible()
      const ctaLinks = page.locator('a[data-workspace-mode="demo"]')
      expect(await ctaLinks.count()).toBeGreaterThanOrEqual(4)
      for (const link of await ctaLinks.all()) await expect(link).toHaveAttribute('href', '#product-preview')
      const localLinks = await page.locator('a[href]').evaluateAll(links => links.filter(link => {
        const href = link.getAttribute('href')!
        return /^(https?:)?\/\//.test(href) && /localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]/i.test(href)
      }).map(link => link.getAttribute('href')))
      expect(localLinks).toEqual([])
      await ctaLinks.first().click()
      await expect(page).toHaveURL(/#product-preview$/)
      await expect(page.getByText('产品交互示意 · 点击左侧聊天室切换场景')).toBeVisible()
    } else {
      const start = page.getByRole('link', { name: '开始体验' })
      await expect(start).toHaveAttribute('href', 'http://localhost:5173')
      expect(await page.locator('a[href="http://localhost:5173"]').count()).toBeGreaterThanOrEqual(5)
      // 拦截导航验证目标，测试不依赖任务一服务是否在线。
      await page.route('http://localhost:5173/**', route => route.fulfill({ contentType: 'text/html', body: '<title>CollabAI Workspace</title><h1>工作台</h1>' }))
      await start.click()
      await expect(page).toHaveTitle('CollabAI Workspace')
    }
    await page.goto('/')

    const layout = await page.evaluate(() => ({ viewport: window.innerWidth, document: document.documentElement.scrollWidth }))
    expect(layout.document).toBeLessThanOrEqual(layout.viewport)
    const invalidAnchors = await page.locator('a[href^="#"]').evaluateAll(links => links.filter(link => !document.getElementById(link.getAttribute('href')!.slice(1))).map(link => link.getAttribute('href')))
    expect(invalidAnchors).toEqual([])
    expect(errors).toEqual([])
    expect(externalRequests.filter(url => !url.startsWith('http://localhost:5173'))).toEqual([])
    await page.screenshot({ path: `test-results/landing-${width}.png`, fullPage: true })
  })
}

test('键盘访问与减少动态效果偏好', async ({ page }) => {
  await page.goto('/')
  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: '跳到主要内容' })).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/#main$/)
  const hasAnimation = await page.locator('.hero h1').evaluate(element => getComputedStyle(element).animationName !== 'none')
  expect(hasAnimation).toBe(false)
})
