# CollabAI 官网交付报告

> 下文保留早先独立源码包与部署尝试记录。本轮 GitHub 联合交付以当前源码及 [联合验收报告](../SUBMISSION_ACCEPTANCE.md) 为准：干净 npm ci、生产构建、开发 / 生产各 6 项 Edge 测试重新通过。旧 zip 不作为本轮交付物，不覆盖原包；本轮未重试 Vercel，仍无公开工作台地址。

## 部署状态

- 正式部署：尚未完成。
- 公开地址：尚未取得并验证。
- Vercel CLI：65.14.0，可通过 npx 使用。
- 登录状态：`vercel whoami --non-interactive` 返回 `Logged out`。
- 官方临时部署尝试同样被 CLI 拒绝：`Temporary deployments aren't available for this attempt`，返回 `login_required` / `userActionRequired: true`。
- 当前阻塞点是 Vercel 账号登录，尚未创建部署；不存在可交付的公开 HTTPS 地址。
- 用户选择本轮先交付源码包和部署命令，不再继续登录或尝试在线部署。

## 功能与边界

- 保留原有设计、React/Vite/TypeScript/Tailwind 工程与完整组件代码。
- 展示图均为本地资源，无付费素材、远程图片或远程字体依赖。
- 生产构建默认显示「查看产品演示」及「工作台尚未公开部署」，CTA 指向本页产品预览。
- 生产环境拒绝 localhost、内网 IP、非 HTTPS 等工作台地址，不会误导访问者进入自己电脑的服务。
- 本地开发默认连接任务一 `http://localhost:5173`，工作台本身不属于官网项目。
- 聊天室与应用场景的任务结果是明确标记的示意，不执行真实 AI 请求。

## 验证结果

- `npm run build`：通过，包含严格 TypeScript 检查。
- 开发版 Playwright：6/6 通过。
- 生产构建 Playwright：6/6 通过。
- 源码包解压到全新临时目录后，`npm ci` 与 `npm run build` 均通过，不依赖原项目的 node_modules。
- 源码包 32 个文件的内容已逐一与当前工程进行 SHA256 对比，全部一致；未包含禁打包目录或真实环境配置。
- 375、768、1440px 布局、导航、移动菜单、FAQ、场景切换、键盘操作及减少动态效果：通过。
- 页面运行时错误及资源加载失败：未发现。
- 生产链接检查：不存在指向 localhost / 回环地址的工作台链接，CTA 演示回退正常。
- 公开 HTTPS、匿名浏览器、远程资源验证：因尚未部署而无法进行，不宣称通过。README 已提供完整验证命令。

## 本地运行

```bash
cd task2-landing
npm ci
npm run dev -- --host 0.0.0.0 --port 5174 --strictPort
```

访问 http://localhost:5174/，保持终端运行。生产预览另开终端：

```bash
npm run build
npm run preview -- --host 0.0.0.0 --port 4174 --strictPort
```

## 交付物

- 源码压缩包：项目上级目录 `task2-landing-source.zip`。
- 保留源码、依赖清单与 lock、README、示例配置、Vercel 配置、测试和交付脚本。
- 不包含 node_modules、.git、.vercel、真实环境私密配置、API Key、测试运行产物或构建缓存。
- zip 生成后验证清单，SHA256 单独提供，避免包内记录自身校验值形成循环。

## 需要手动操作

正式部署尚未完成时，在项目目录执行 `npx --yes vercel login`，按页面完成登录，再执行 `npx --yes vercel deploy --prod`。如果已获得临时部署，先用私下提供的认领地址将项目认领到账号。

正式交付前确认 Production 允许匿名访问，再按 README 执行 HTTPS 资源验证与无登录浏览器测试。任务一公开上线前保持 `VITE_APP_URL` 为空。
