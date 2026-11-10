# ChatBot · AI Coding Interview

两个独立 Coding 项目：Relay 多人 AI 协作聊天室，以及 CollabAI 产品官网。保留已有实现与页面设计，以最小修改完成联合验收。

本轮结论：任务一 **PASS WITH LIMITATIONS**，任务二 **PASS**。真实 LLM 供应商端到端测试为 **NOT RUN：缺少有效 API Key**。源码已上传至 [Public GitHub 仓库 ChatBot](https://github.com/Huangqin77/ChatBot)，任何人可直接查看和克隆；默认分支 `main`，全新远程 clone 的依赖安装、构建和后端测试已通过。网页尚未公开部署。完整证据见 [SUBMISSION_ACCEPTANCE.md](SUBMISSION_ACCEPTANCE.md)。

## 题目要求与实现对应

下表依据本次提供的面试任务与最终验收要求整理；未提供的独立原始题面没有另行补造。

| 任务 | 提供的要求 | 对应实现 |
| --- | --- | --- |
| 一：多人 AI 协作聊天室 | 昵称进入；创建、加入聊天室；多人实时消息 | React 工作台、FastAPI REST / WebSocket、独立标签页身份 |
| 一：Bot 与 Agent | 创建管理多个 Bot；@ 触发；计算、时间、跨 Bot 委派及汇总 | 服务端 calculator / get_current_time / delegate_to_bot；父子任务与工具执行记录；Demo 和 Live 两种模式 |
| 一：可靠性 | 消息、任务、工具轨迹持久化；刷新恢复；深度、工具次数、超时限制与失败状态 | SQLite；全链 6 次工具预算、委派深度 2、总超时 120 秒；单进程并行上限 |
| 二：产品官网 | 导航、Hero、功能、流程、场景、FAQ、Footer 与 CTA | CollabAI 完整本地 React 组件；可交互演示、FAQ、场景选项卡与移动菜单 |
| 二：独立运行与响应式 | 手机、平板、桌面；独立安装和构建；合理工作台入口 | 375 / 768 / 1440px 验收；独立 lock 文件；生产版无公网地址时显示演示并留在官网 |

## 技术栈与目录

- 任务一：React 19、TypeScript 5.9、Vite 7、Tailwind CSS 4；Python / FastAPI、SQLModel / SQLite、httpx、WebSocket、pytest、Playwright。
- 任务二：React 19、TypeScript 5.8、Vite 6、Tailwind CSS 4、lucide-react、Playwright。
- 两个前端分别安装依赖，无根目录 npm workspace；Vite 和 TypeScript 版本独立，不要求强行统一。

```text
ChatBot/
├── README.md
├── SUBMISSION_ACCEPTANCE.md
├── .gitignore
├── scripts/audit_submission.py
├── task1-chatroom/
│   ├── README.md / ACCEPTANCE.md / REAL_LLM_VALIDATION.md
│   ├── backend/       # Python 依赖、示例配置、源码与 pytest
│   ├── frontend/      # 前端源码、lock 文件与 E2E
│   └── scripts/       # 启动、安全扫描与真实 LLM 验证
└── task2-landing/
    ├── README.md / DELIVERY.md
    ├── src/ / public/ / tests/ / scripts/
    └── package.json / package-lock.json / .env.example
```

本地目录名称可以不同，源码无需移动或重新创建。每个项目还保留独立 README。

## 环境依赖

Windows PowerShell、Git、Node.js 20.19+ 或 22.12+、npm 10+、Python 3.11+。本轮实际使用 Node 24.19.0、npm 11.17.0、Python 3.14.7、Microsoft Edge。其他 Python / Node / 操作系统组合本轮未测试。

浏览器 E2E 默认使用已安装的 Edge。Demo 不需要 API Key，也不需要 Docker、Redis、外部数据库或额外环境变量；缺失 SQLite 时由后端创建初始演示数据。

## 完整启动命令

以下终端均从仓库根目录开始。首次安装按顺序执行：

```powershell
cd task1-chatroom/backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
cd ../frontend
npm.cmd ci
cd ../../task2-landing
npm.cmd ci
```

终端 1，启动任务一后端：

```powershell
cd task1-chatroom/backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --ws-max-size 16384
```

终端 2，启动任务一前端：

```powershell
cd task1-chatroom/frontend
npm.cmd run dev
```

访问 [聊天室](http://127.0.0.1:5173)，后端 [API 文档](http://127.0.0.1:8000/docs)。正常启动默认代理至 8000；仅测试服务器使用内部 `RELAY_BACKEND_URL` 切换隔离后端，不向浏览器暴露模型配置。

终端 3，独立启动任务二官网：

```powershell
cd task2-landing
npm.cmd run dev -- --strictPort
```

访问 [本地官网](http://localhost:5174)。官网无需启动任务一即可展示全部页面；开发版工作台按钮默认连接本地 5173，需同时启动聊天室后使用。

官网生产预览（从根目录另开终端）：

```powershell
cd task2-landing
npm.cmd run build
npm.cmd run preview -- --strictPort
```

访问 [本地生产预览](http://localhost:4174)。当前没有公网工作台地址，保持 `VITE_APP_URL` 为空；生产版 CTA 显示「查看产品演示」，指向本页 `#product-preview`，不导向访问者的 localhost。只在聊天室真实部署并验证后配置 HTTPS 工作台地址。

正常端口：后端 8000、聊天室 5173、官网 5174、各自生产预览 4173 / 4174，互不冲突。Ctrl+C 停止对应终端。

## Demo 演示步骤

1. 用两个标签页分别以两个昵称进入聊天室，互发消息。
2. 创建聊天室，让第二位用户加入；创建 Bot 并通过「管理队友」加入/移除。
3. 在默认协作实验室发送 `@计算员 计算 (128 + 256) * 3`，验证 1152；发送 `@计算员 现在时间是几点`，查看服务端时间。
4. 发送 `@策划官 请委派给计算员计算 99 * 12，并汇总结果`，检查 1188、主子任务、委派返回路径、工具输入输出。
5. 刷新页面，确认消息和执行链仍在；发送 `@计算员 计算 1 / 0`，检查失败任务与工具轨迹。
6. 打开官网，切换产品演示和应用场景、展开 FAQ、检查手机菜单和导航。生产预览的 CTA 留在产品演示。

Mock / Demo 可直接验证，工具、数据库与 WebSocket 真实执行，模型决策与总结为明确标注的规则演示。真实 LLM 需要在后端 `.env` 配置模型服务：`LLM_MODE=live`、`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`。真实供应商调用尚未验收通过，不能把受控 HTTP Fixture 当成真实模型结果。配置与单独验证命令见 [REAL_LLM_VALIDATION.md](task1-chatroom/REAL_LLM_VALIDATION.md)。

## 自动化测试与实际结果

从根目录分别执行：

```powershell
cd task1-chatroom/backend
.\.venv\Scripts\python.exe -m pytest -q --basetemp=./.test-tmp
.\.venv\Scripts\python.exe -m pip check
cd ../frontend
npx.cmd tsc --noEmit
npm.cmd run build
npm.cmd run test:e2e
cd ../../task2-landing
npm.cmd run build
npm.cmd run test:e2e
$env:PLAYWRIGHT_PRODUCTION='1'
npm.cmd run test:e2e
Remove-Item Env:PLAYWRIGHT_PRODUCTION
```

| 本轮实际执行，2026-11-10 | 结果 |
| --- | --- |
| 原项目后端 pytest | 57 passed，1 条 Starlette/httpx 弃用提示 |
| 两个原项目前端 build | PASS，均包含 TypeScript 检查 |
| 独立新 venv、requirements-lock 安装与 pip check | PASS |
| 独立新 venv 中 pytest | 57 passed，1 条相同弃用提示 |
| 两个干净副本 npm ci、TypeScript 与生产构建 | PASS |
| 干净副本任务一 Edge E2E | 4 passed |
| 干净副本任务二开发版 / 生产版 Edge E2E | 各 6 passed；375 / 768 / 1440px |
| 真实 LLM 验收脚本 | NOT RUN：无有效 API Key；0 次外部请求 |

E2E 使用专用端口：任务一 18000 / 15173，任务二开发 15174、生产 14174，不复用现有服务。任务一自动创建系统临时 SQLite 并强制 Demo，不写入日常数据库；测试截图和执行数据不提交。测试端口被占用时先处理冲突，不要改为复用未知服务。官网 `PLAYWRIGHT_BASE_URL` 仅用于显式验证已部署地址。

## 源码安全与 GitHub 交付

根 `.gitignore` 排除依赖、私有环境、SQLite 与旁文件、缓存、构建、日志、压缩包与真实执行证据；保留 `.env.example`、锁文件、全部源代码和测试。根目录安全脚本只读审查 Git 暂存区实际 blob，输出路径和计数，不输出凭据：

```powershell
py -3 scripts/audit_submission.py
git diff --cached --check
git diff --cached --stat
```

已通过本机保存的 GitHub 凭据验证账号 `Huangqin77`。仓库最初按 Private 创建和验收，随后根据用户明确要求重命名为 **[ChatBot](https://github.com/Huangqin77/ChatBot)** 并切换为 **Public**；本地 `origin` 已同步，未 force push，未覆盖已有项目。远程 75 个文件与本地逐 blob 一致，真实 `.env`、SQLite、依赖、构建产物和本地执行记录均未上传。全新 GitHub clone 安装与构建通过，后端 57 项测试通过。

将仓库链接直接分享给面试官即可查看源码，无需邀请或授权。也可以直接克隆：

```bash
git clone https://github.com/Huangqin77/ChatBot.git
```

GitHub 源码仓库地址不是聊天室在线访问地址，上传源码也不代表网站已部署。

## 当前限制

真实供应商兼容性、额度、工具选择和总结质量均未实测。聊天室是单进程本地演示，不含生产账号权限、多进程广播、崩溃任务续跑、Bot 配置编辑/删除、附件与 token 流式输出。管理功能为创建 Bot 和房间成员管理。官网尚未公开部署，也没有公网工作台。GitHub 源码上传完成不代表网页已上线。
