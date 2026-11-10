# Relay · 多人 AI 协作聊天室

React + Vite + TypeScript + Tailwind CSS 前端，FastAPI + WebSocket 后端，SQLite + SQLModel 持久化。单进程开发服务，无 Docker、Redis 或任务队列。

## 项目功能与架构

- 昵称身份、创建与切换聊天室、多客户端实时广播、在线人数、历史分页和断线重连。
- 创建多个 Bot，持久化名称、角色、System Prompt 与工具权限；将 Bot 加入房间后通过 `@名称` 触发。
- 安全计算器、当前时间、Bot 子任务委派；主任务、子任务和工具状态实时推送并持久化，刷新可回溯。
- 桌面三栏界面与手机收起侧栏；加载态、空态、错误消息与失败任务详情。
- 明示 Demo 规则演示与真实 LLM 模式，真实模式不会因调用失败而偷偷回退到 Demo。

```text
React 页面 ── REST（房间/Bot/历史）── FastAPI ── SQLModel / SQLite WAL
         └── WebSocket（消息/状态）── 房间广播与 AgentRunner
                                       ├── Demo：确定性规则
                                       └── Live：Chat Completions 原生 Tool Calling
                                             └── 服务端工具 / 子 Bot → tool 结果 → 主 Bot 再推理 → 最终回复
```

所有模型请求都在后端发起。工具 Schema 放入请求的 `tools`，模型返回结构化 `tool_calls`；后端保留原 assistant 工具调用消息，执行白名单工具，再以对应的 `tool_call_id` 回填 `role=tool` 消息。委派结果也按此协议回填，所以主 Bot 会继续调用模型生成总结，而不是由前端拼接假回复。Demo 的总结是显式规则汇总，不代表模型推理。

## Windows PowerShell 启动

需要 Node.js 20.19+（或 22.12+）、Python 3.11+。本项目实际验证环境为 Node 24.19、Python 3.14.7、Windows、Microsoft Edge。

先进入项目目录：

```powershell
cd task1-chatroom
```

首次安装后端依赖（无需激活虚拟环境，也无需修改 PowerShell 执行策略）：

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

如果已安装 `uv`，也可以这样创建、安装（本次环境实际使用此路径）：

```powershell
uv --cache-dir ../.cache/uv venv --python 3.14 .venv
uv --cache-dir ../.cache/uv pip install --python .venv/Scripts/python.exe --index-url https://pypi.org/simple -r requirements-lock.txt
```

可通过 `uv --python` 选择已安装的 Python 版本；也可用 `py -0p` 查询。已有虚拟环境时跳过创建步骤。

终端 1，启动后端（在 `backend` 中）：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --ws-max-size 16384
```

终端 2，安装并启动前端：

```powershell
# 从联合仓库根目录开始
cd task1-chatroom/frontend
npm.cmd ci
npm.cmd run dev
```

打开 [http://127.0.0.1:5173](http://127.0.0.1:5173)，API 文档位于 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)。Vite 代理 `/api` 和 `/ws` 到后端，因此浏览器始终访问同一个前端来源。两个终端按 Ctrl+C 停止。安装后也可在项目根目录分别运行 `powershell -ExecutionPolicy Bypass -File .\scripts\backend.ps1` 与 `powershell -ExecutionPolicy Bypass -File .\scripts\frontend.ps1`。

## 无 API Key 的完整验收流程

默认 `LLM_MODE=auto`，没有 Key 时自动进入 **Demo / Mock** 模式；页面顶部、Bot 消息和任务记录均明确标记。Demo 通过确定性规则解析简单任务，不进行语言模型推理；计算、当前时间、委派和数据库写入都由服务端真实执行。

1. 在两个浏览器窗口或两个新标签页打开页面，分别输入不同昵称，进入默认「协作实验室」。身份保存在 **sessionStorage**，每个标签页独立，刷新保留；通过左下角按钮切换昵称。此身份机制仅供本地 Demo。
2. 任意一端发送消息，另一端立即收到；顶部展示当前房间在线用户数。
3. 发送 `@计算员 计算 (128 + 256) * 3`，获得 `1152`；点击回复下方「查看任务与工具记录」，展开 `calculator` 查看输入、输出和状态。
4. 发送 `@计算员 现在时间是几点？`，查看服务端真实北京时间。
5. 发送 `@策划官 请委派给计算员计算 99 * 12，并汇总结果`，获得 `1188`。右侧记录显示「策划官 → 计算员 → 策划官」、两个任务和两个工具调用。
6. 右侧「创建 Bot」填写名称、角色描述、System Prompt、启用工具。创建后自动加入当前房间；「管理队友」可添加/移除已有 Bot。新房间默认不添加 Bot，需要手动管理队友。
7. 输入框输入 `@` 选择 Bot，或输入 `@Bot名称 空格 任务`。只有当前房间的 Bot 会被触发，一条消息最多提及 4 个 Bot。名称支持中文、字母、数字、下划线、短横线。
8. 刷新页面，昵称、当前房间、消息、Bot、任务和工具记录保留。消息按每页 100 条向前加载，工作台默认加载最近 50 个主任务及其完整子任务；旧消息上的任务入口可以按 ID 继续加载更早的完整执行链路。

Demo 的自建 Bot 同样可运行，但角色和 System Prompt 仅被保存、展示；按 Prompt 自由推理需使用真实模型。委派演示需为 Bot 启用 `delegate_to_bot`，并保证房间内还有至少一个其他 Bot。真实模型是否调用某个工具取决于模型决策及 Prompt。

## 真实模型配置

真实 API 最小验收的命令、请求预算、证据格式与本轮 NOT RUN 结果见 [REAL_LLM_VALIDATION.md](REAL_LLM_VALIDATION.md)。现有环境变量名保持不变，不使用另一套 LLM_API_KEY 命名。本轮已创建本地 `backend/.env` 空 Key 模板，需要你仅在本地填写后运行验收；不要在对话中发送密钥。

只编辑 `backend/.env`，然后重启后端：

```dotenv
LLM_MODE=live
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=你的支持工具调用的模型名
```

- `auto`：有 Key 使用真实模型，无 Key 使用明确标记的 Demo。
- `demo`：始终规则演示，即使环境存在 Key。
- `live`：必须有 Key；缺失、网络错误、超时、HTTP 失败、空响应等会产生失败任务及聊天室系统消息，**不会静默降级为 Mock**。
- Base URL 必须包含供应商的 API 前缀（通常 `/v1`），后端追加 `/chat/completions`。供应商必须支持 Chat Completions 的 `tools` / `tool_calls` / `tool_call_id` 协议；本项目用 `httpx` 直接请求以保持兼容。
- Base URL 只接受 HTTP(S)，不得把 Key 放在 URL 用户信息、查询参数或片段中，以免 HTTP 日志泄露。系统环境变量优先于 `.env`；修改后需重启后端。`Settings` 的对象表示不会显示 Key。
- Key 只通过服务端环境变量读取；后端加载自己的 `.env`，不向前端下发 Key 或供应商原始错误响应。`.env` 已被 `.gitignore` 排除。
- 使用最多 30 条房间历史，每条截取 800 字符，并以触发消息时间为上下文截止点；委派子任务也可读取适量房间上下文。模型最终回复整体广播，不逐 token 流式输出；任务和工具状态实时广播。
- 模型调用协议参考 [OpenAI 官方 Function Calling 文档](https://developers.openai.com/api/docs/guides/function-calling)。

## 工具、委派与运行限制

| 工具 | 参数 | 行为 |
| --- | --- | --- |
| `calculator` | `expression` | AST 白名单解析数字和 `+ - * / // % **`、括号、正负号。无 `eval`/`exec`，不允许函数调用、属性、下标、Shell。限制 200 字符、64 AST 节点、常量绝对值不超过 1e12、指数绝对值不超过 12、有限实数结果绝对值不超过 1e100。 |
| `get_current_time` | `timezone` | 读取服务端当前时间，支持 `Asia/Shanghai` 和 `UTC`。 |
| `delegate_to_bot` | `bot_name`, `task` | 只可委派给同一房间的其他 Bot，子任务结果返回调用方，由主 Bot 汇总到聊天室。 |

每个主任务与全部后代**共享 6 次工具调用预算**（委派本身计入一次）。主任务深度 0，子任务深度 1，孙任务深度 2，超过即拒绝；禁止自身委派。失败或被拒绝的工具调用也计入预算并记录为 `failed`。超出预算的第 7 次不会执行。每个根任务总时限 120 秒，每次模型请求最多 45 秒；最多 4 个根任务并行，运行及待处理总数最多 16。单进程内管理 WebSocket 连接和后台任务；用户断开连接不会取消已启动任务。

每个 Bot 的模型循环最多 8 轮，且受上述共享工具预算和根任务总时限约束。工具失败首先作为工具结果反馈给真实模型，允许模型修正参数重试；如果同名工具最后一次尝试仍失败，任务最终标记 `failed` 并广播系统错误。若重试成功，该任务可为 `completed`，早先失败的工具记录仍保留。Demo 失败也会正确标记任务失败。供应商返回格式损坏、工具调用 ID 缺失/重复、内容为空、回复被截断或拦截时，任务失败，不将其伪装为完整结果。

工具 Schema 与执行端共用严格参数模型，拒绝额外字段、错误类型、缺失字段及越界值。Live 工具记录新增 `provider_call_id`，保存模型原始调用 ID；`id` 仍是数据库记录 ID，Demo 的 `provider_call_id` 为 null。旧 SQLite 启动时自动增量添加此可空字段，保留原数据。

## 面试官端到端演示（自建两个 Bot）

1. 用「规划同学」「数据同学」两个昵称打开同一房间，互发两条消息，观察双方实时收到。
2. 创建「数据助手」：角色为数据核验，System Prompt 为「你是数据助手，计算必须调用 calculator，使用中文返回结果」，启用 `calculator`。
3. 创建「规划助手」：角色为任务规划，System Prompt 为「你是规划助手，将计算子任务用 delegate_to_bot 委派给数据助手，收到结果后生成最终总结」，启用 `delegate_to_bot`。确认两者都已加入当前房间。
4. 发送 `@数据助手 计算 (128 + 256) * 3`，核对 `1152` 与工具记录。
5. 发送 `@规划助手 请委派给数据助手计算 99 * 12，并汇总结果`，核对 `1188`、两个任务、`delegate_to_bot` 与 `calculator` 记录以及「规划助手 → 数据助手 → 规划助手」。
6. 刷新两个页面，再检查消息、Bot、主子任务状态和工具输入输出。
7. 发送 `@数据助手 计算 1 / 0`：应出现除零错误，任务与工具均为失败，刷新仍可看到。真实模型可能自行改正表达式重试，失败尝试仍保留；是否最终失败取决于工具是否被成功重试。

此流程在 Demo 下验证真实业务和工具执行；在 Live 下还验证供应商模型的工具决策与后续推理，两种结果应分别记录。

## 交付安全检查

```powershell
# 在 backend 中执行；只打印路径、计数和结论，不打印密钥。
.\.venv\Scripts\python.exe ..\scripts\security_check.py
```

扫描范围包括业务源码、前端生产构建和持久化日志（若存在），排除依赖、缓存、数据库及合法的后端本地 `.env`；检查典型 Key/私钥模式和当前配置 Key 的精确匹配。若位于 Git 仓库中，还检查已跟踪环境文件、历史环境文件与历史典型 Key 模式。该扫描不保证识别所有供应商的未知格式密钥。

本轮联合仓库和暂存内容状态以根目录 `SUBMISSION_ACCEPTANCE.md` 为准。`.env` 与 `.env.*` 被忽略，仅允许 `.env.example` 模板。日志测试使用人为植入的测试凭据，验证供应商错误正文、网络超时与非预期异常不会把凭据写入任务、消息或捕获的日志；非预期异常只记录类型。没有持久化日志文件时，扫描会如实报告 0 个，不等同于审计所有终端历史。

SQLite 使用外键约束与 WAL；服务重启后，未完成任务与工具调用标为 `failed`，避免永远显示执行中。默认数据文件为 **`backend/chatroom.db`**（按上述命令从 backend 启动）。不要删除此文件，除非希望重置数据。Demo 数据只在空数据库初始化：一个聊天室、策划官、计算员、欢迎系统消息。`users / rooms / bots / room_bots / messages / tasks / tool_calls` 全部真实入库。

## 测试与构建

后端（在 backend 目录）：

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=./.test-tmp
```

测试使用独立临时 SQLite，覆盖双客户端广播、房间隔离、Bot 创建及调用、计算器安全、时间、委派返回、共享预算、自身委派和深度限制、真实模型协议的受控替身、模型错误反馈、消息去重、历史分页、应用重启持久化和中断恢复。替身测试不访问真实付费模型。

最新交付回归（2026-11-10）：**后端 57 passed**，原有 45 项保持通过（Starlette 测试适配层有一条 httpx 弃用提示，不影响运行）；**TypeScript 检查和 Vite 生产构建通过**；**4 项真实 Edge 端到端测试通过**，覆盖两个独立浏览器上下文、自建规划助手和数据助手、同浏览器不同标签页、工具与委派、刷新持久化、失败状态、390px 手机布局。真实 API 验收脚本已运行但因无 Key 全部 NOT RUN，外部请求 0 次。详细结果见 [ACCEPTANCE.md](ACCEPTANCE.md) 和 [REAL_LLM_VALIDATION.md](REAL_LLM_VALIDATION.md)。

新增的受控 HTTP Transport 测试没有替换 `llm.complete`，完整经过 JSON 请求、Authorization、Base URL、Model、工具 Schema、模型结构化响应校验、子 Bot 运行与主 Bot 后续请求；返回值仍由测试 Fixture 提供，**不代表调用了外部真实 LLM**。当前环境未配置 API Key，外部模型效果与供应商兼容性仍未实测。

前端（在 frontend 目录）：

```powershell
npm.cmd run build
npm.cmd run test:e2e
```

端到端测试使用已安装的 Microsoft Edge（`channel: 'msedge'`），自动启动专用后端 18000 与前端 15173，不复用日常服务。后端强制 Demo、清空进程内 Key，并使用系统临时目录的新 SQLite，不接触 `backend/chatroom.db`。前端测试代理通过仅服务端读取的 `RELAY_BACKEND_URL` 连接隔离后端；正常启动无需设置该变量，仍连接 8000。测试端口被占用会直接退出。若未安装 Edge，可执行 `npx.cmd playwright install msedge` 安装，或在 `playwright.config.ts` 改为本机可用浏览器。测试创建带时间后缀的验收房间与 Bot；临时数据库和截图均不属于源码提交内容。截图输出到 `artifacts/desktop.png`、`artifacts/second-client.png`、`artifacts/mobile.png`。

## API / WebSocket

写接口使用昵称进入时获得的本地 `Authorization: Bearer <token>`。这只是身份隔离，不是生产账号系统；房间与历史在本地 Demo 内公开。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 服务状态、Demo/Live、模型名及工具限制 |
| POST | `/api/users` | `{nickname}` 创建本地身份，返回 id / nickname / token |
| GET | `/api/me` | 当前本地身份 |
| GET / POST | `/api/rooms` | 房间列表 / `{name, description}` 创建房间 |
| GET / POST | `/api/bots` | Bot 列表 / `{name, role, system_prompt, tools}` 创建 Bot |
| PUT | `/api/rooms/{id}/bots` | `{bot_ids: [...]}` 设置房间 Bot |
| GET | `/api/rooms/{id}/state` | 房间、Bot、最近消息和任务工具快照 |
| GET | `/api/rooms/{id}/messages?before_id=...&limit=100` | 历史消息分页 |
| GET | `/api/rooms/{id}/tasks` | 最近主任务、子任务及工具记录 |
| GET | `/api/tasks/{id}` | 按任务 ID 获取该根任务完整链路，支持旧消息回溯 |
| WS | `/ws/rooms/{id}?token=...` | 双向实时通信 |

客户端消息：`{"type":"message","content":"@计算员 计算 6*7","client_id":"每条消息的唯一ID"}`。服务端持久化后广播确认，重复 `client_id` 不会重复写入或重复启动 Bot。服务端事件：`snapshot`、`presence`、`message`、`task`、`tool_call`、`bots_changed`、`rooms_changed`、`error`、`pong`。心跳使用 `{"type":"ping"}`。前端断线自动指数退避重连，重连后重新加载持久化快照。

## 文件结构

```text
task1-chatroom/
├── README.md
├── ACCEPTANCE.md                  # 最终验收证据、修复与未验证项
├── REAL_LLM_VALIDATION.md         # 真实 API 配置、脚本与独立结果
├── .gitignore
├── backend/
│   ├── .env.example
│   ├── requirements.txt           # 直接依赖及兼容范围
│   ├── requirements-lock.txt      # 实际验证过的完整版本
│   ├── pytest.ini
│   ├── app/
│   │   ├── main.py                # API、身份、WebSocket 与消息分发
│   │   ├── config.py              # 后端环境配置
│   │   ├── models.py              # SQLModel 表
│   │   ├── db.py                  # SQLite 初始化与 Demo seed
│   │   ├── hub.py                 # 房间广播和在线状态
│   │   ├── agent.py               # 任务、工具循环、委派与共享预算
│   │   ├── llm.py                 # OpenAI 兼容请求 / 明示 Demo
│   │   └── tools.py               # 安全计算器、时间、工具 Schema
│   └── tests/                    # 核心验收与安全测试
├── frontend/
│   ├── package.json / package-lock.json
│   ├── vite.config.ts / tsconfig.json
│   ├── playwright.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── App.tsx                # 登录、房间、Bot 表单与执行详情
│   │   ├── api.ts / types.ts
│   │   ├── main.tsx / style.css
│   └── tests/chatroom.spec.ts     # 真实浏览器端到端验收
└── scripts/
    ├── backend.ps1
    ├── frontend.ps1
    ├── security_check.py          # 不打印密钥的只读交付扫描
    └── validate_real_llm.py       # 凭据门禁、7 次预算、真实 HTTP/WS 验收
```

## 边界与未包含事项

真实付费模型需要用户提供有效 Key 与支持工具调用的模型，本次交付不伪装外部模型验收结果。未实现生产注册登录、房间权限、Bot 配置编辑/删除、消息编辑/删除、上传附件、多进程共享、崩溃任务自动续跑与 token 流式输出；它们不属于本次必需范围。当前实现面向单机 Coding 考核和本地多人演示。
