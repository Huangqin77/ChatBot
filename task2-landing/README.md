# CollabAI 产品官网

可独立运行的中文 SaaS 产品官网，使用 React、Vite、TypeScript、Tailwind CSS 和 lucide-react。无需后端、数据库或认证。

## 本地运行

需要 Node.js 20.19+ 或 22.12+。

```bash
npm ci
npm run dev
```

打开 http://localhost:5174。官网使用 5174，避免与任务一聊天室默认的 5173 冲突。

## 配置工作台

将 `.env.example` 复制为 `.env.local`，按需修改：

```dotenv
VITE_APP_URL=
```

所有工作台 CTA 共用此配置。开发模式未配置时默认连接任务一 `http://localhost:5173`；生产构建未配置或配置为 localhost、内网 IP、非 HTTPS 等地址时，回退到本页 `#product-preview`，并明确显示「演示」及「工作台尚未公开部署」。任务一未上线时，保持 `VITE_APP_URL` 为空。

任务一真正公开上线后，才填写其实际可访问的 HTTPS 域名。URL 防护不代替对目标服务的在线验证。环境变量在构建时注入，修改后需要重启开发服务或重新构建；`VITE_` 变量会公开给浏览器，禁止包含密钥。

官网本身完全独立；要使用工作台功能，请另外启动同目录下的任务一聊天室。官网中的产品预览明确标注为演示，不会执行真实 AI 请求。

## 构建与验证

```bash
npm run build
npm run preview
npm run test:e2e
```

`build` 先执行严格 TypeScript 检查，再构建静态资源到 `dist/`。`preview` 地址为 http://localhost:4174。

本次交付验收：`npm run build` 通过；开发模式与生产构建分别通过 6 项测试，375 / 768 / 1440px 均无横向溢出、资源加载失败或页面运行时错误。包括生产工作台 URL 防护测试。工作台本身由任务一提供，未在本项目中实现。实际部署状态与公开地址见 [DELIVERY.md](./DELIVERY.md)，本地构建通过不等于已经公开上线。

端到端测试使用 Playwright，默认调用本机 Microsoft Edge（无需额外下载浏览器）。测试会自动在专用 15174 端口启动开发服务器，不复用日常服务，验证 375、768、1440px 布局，导航、移动菜单、FAQ、场景切换、键盘交互、CTA 目标、资源加载与横向溢出；全页截图保存到 `test-results/`。工作台导航测试通过拦截目标地址完成，不依赖任务一服务在线。

其他系统可安装 Chromium 并切换浏览器：

```bash
npx playwright install chromium
# macOS / Linux
PLAYWRIGHT_CHANNEL=chromium npm run test:e2e
# PowerShell
$env:PLAYWRIGHT_CHANNEL='chromium'; npm run test:e2e
```

## 实现内容

- Sticky 导航、区块锚点跳转、移动菜单（Escape 关闭、外部点击关闭、选择后关闭）。
- 渐变 Hero、深色聊天室 React 展示组件，可切换项目、研究、数据三种演示。
- 四张功能卡、四步协作流程、四种可切换应用场景。
- FAQ 手风琴、页底 CTA 和完整页脚。
- 所有产品展示、图案和图标由本地代码构建，无远程图片、字体、虚构客户背书。
- 键盘焦点、跳过导航链接、语义标签、ARIA 状态、选项卡方向键与 Home/End 导航。
- `prefers-reduced-motion` 支持，桌面、平板、手机响应式布局。

## 目录

```text
src/
  components/   # Header、Hero、ProductPreview、Features、Workflow 等
  lib/config.ts # 工作台 URL、导航配置
  App.tsx       # 页面组合
  main.tsx      # React 入口
  styles.css    # Tailwind 入口、设计规范和响应式样式
public/         # 本地 SVG favicon
tests/          # Playwright 端到端测试
```

生产部署可将 `dist/` 目录交给任何静态文件服务器。页面不需要 SPA 路由回退规则。

## 锁定依赖与生产构建验收

面试官解压源码包后，进入包含 `package.json` 的 `task2-landing` 目录，推荐使用 lock 文件安装：

```bash
npm ci
npm run dev -- --host 0.0.0.0 --port 5174 --strictPort
```

访问 http://localhost:5174/，保留终端运行；关闭终端或 Ctrl+C 会停止服务。npm 10+，本次实际验证环境为 Node.js 24.19、Windows、Microsoft Edge。

生产静态预览（另开终端）：

```bash
npm run build
npm run preview -- --host 0.0.0.0 --port 4174 --strictPort
```

访问 http://localhost:4174/。Vite preview 仅用于本地检查，不是公开部署。

生产构建浏览器验收（PowerShell）：

```powershell
$env:PLAYWRIGHT_PRODUCTION='1'
npm run test:e2e
Remove-Item Env:PLAYWRIGHT_PRODUCTION
```

macOS / Linux 使用 `PLAYWRIGHT_CHANNEL=chromium PLAYWRIGHT_PRODUCTION=1 npm run test:e2e`，先按前文安装 Chromium。生产测试自动在专用 14174 端口启动预览，不复用日常 4174 服务；页面测试使用全新浏览器上下文，不加载日常浏览器登录状态。测试端口被占用时直接退出。当前生产测试针对未配置工作台的演示版本，后续接入真实工作台时应更新 CTA 断言。

## Vercel 部署

已提供 `vercel.json`，明确指定 Vite、`npm ci`、`npm run build`、`dist`。`.vercelignore` 排除真实环境配置、Git、依赖目录和测试产物。正式部署需要你自己的 Vercel 账号，不需要将账号 Token 发给任何人。

在项目目录执行：

```bash
npx --yes vercel login
npx --yes vercel deploy --prod
```

按 CLI 提示打开授权页并登录，选择你的账号或团队，创建或关联项目，目录选当前 `task2-landing`，使用已有构建配置。以 CLI 真实返回的 Production HTTPS URL 为准，不能用 localhost 或示例域名代替。

也可以使用 `npx --yes vercel deploy --temporary` 创建无需登录的临时部署。其有效期和认领地址以 CLI 返回为准；未认领的临时链接不能描述为永久上线，长期交付前需先认领。[Vercel CLI 官方文档](https://vercel.com/docs/cli/deploy)

任务一尚未公开上线时，Vercel 的 Production 环境中保持 `VITE_APP_URL` 为空。上线后才能填写真实工作台 HTTPS URL 并重新部署。

### 公开 HTTPS 与匿名访问检查

1. 在 Vercel **Settings → Deployment Protection** 检查 Production 的访问限制，面试交付域名必须允许面试官未登录访问。
2. 使用浏览器无痕窗口打开实际公开 HTTPS URL，确认不是 Vercel 登录页面。
3. 运行不携带 Cookie、Authorization 或保护绕过参数的资源检查：

```bash
node scripts/verify-public.mjs https://你的实际生产域名
```

4. 用无登录状态的 Playwright 检查公开网站（PowerShell）：

```powershell
$env:PLAYWRIGHT_BASE_URL='https://你的实际生产域名'
$env:PLAYWRIGHT_PRODUCTION='1'
npm run test:e2e
Remove-Item Env:PLAYWRIGHT_BASE_URL
Remove-Item Env:PLAYWRIGHT_PRODUCTION
```

## 源码交付打包

源码包保留 React / Vite / TypeScript 全部源代码、package.json、package-lock.json、README、无密钥 `.env.example`、部署配置、测试与验证脚本。产品展示始终为本地 React/CSS/SVG，不依赖付费或远程图片。

压缩包不包含 `node_modules`、`.git`、`.vercel`、真实 `.env`、API Key、构建缓存、测试运行产物。打包脚本以白名单选择文件；不是简单压缩整个工作目录。

可选的重复打包命令（PowerShell 7+）：

```powershell
pwsh -NoProfile -File ./scripts/package-source.ps1
```

默认在上级目录生成 `task2-landing-source.zip`。为防止覆盖，文件已存在时报错，可使用 `-OutputPath` 指定新的目标文件名。

新增交付文件：`DELIVERY.md`（实际状态报告）、`vercel.json` / `.vercelignore`（部署配置）、`scripts/verify-public.mjs`（匿名 HTTPS 资源检查）、`scripts/package-source.ps1`（白名单打包）、`tests/workspace-url.spec.ts`（生产入口防护测试）。
