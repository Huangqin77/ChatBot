# 真实 LLM Tool Calling 与多 Bot 验收

> 本轮联合验收再次在干净环境执行此脚本：八项 NOT RUN、外部请求 0 次，仍缺少有效 API Key。下文早先的本地证据路径仅供原机器复核，artifacts 不提交 GitHub。最新联合结论见 [联合验收报告](../SUBMISSION_ACCEPTANCE.md)。

## 当前结论：C，未配置凭据，真实测试 NOT RUN

2026-11-10 检查结果：`OPENAI_API_KEY` 未配置，默认 Base URL 为 `https://api.openai.com/v1`，Model 为 `gpt-4.1-mini`，配置模式 `auto`，聊天室实际为 `demo`。供应商可配置；默认服务地址不能证明该模型或账号实际可用。

已生成仅含空 Key 的本地 `backend/.env`（来自 `.env.example`，没有覆盖已有文件）。已实际运行 `scripts/validate_real_llm.py`，没有启动外部模型测试，也没有回退到 Mock。外部请求尝试数为 **0**。

本轮脱敏证据文件：`artifacts/real-llm/20261110T125333Z-508461/report.json`。没有真实 Task ID、主子 Bot ID 或模型 Tool Call ID 可供报告，不能用之前的 Demo 记录充当真实调用链。

| 测试项 | 本轮结果 | 说明 |
| --- | --- | --- |
| 模型连通性 | NOT RUN | 无 API Key，未验证认证、额度或模型名 |
| 原生 calculator Tool Calling | NOT RUN | 未收到外部模型的结构化响应 |
| 工具结果返回模型 | NOT RUN | 无真实调用 ID 可关联 |
| delegate_to_bot | NOT RUN | 未触发真实模型委派 |
| 子 Bot 真实执行 | NOT RUN | 未调用数据助手的外部 LLM |
| 主 Bot 继续推理与总结 | NOT RUN | 仅既有受控协议测试通过 |
| WebSocket 推送真实模型结果 | NOT RUN | Demo WebSocket 回归另行通过 |
| SQLite 保存真实模型任务 | NOT RUN | Demo 与受控路径持久化回归另行通过 |

## 只在本地配置凭据

编辑 `backend/.env`，沿用项目现有环境变量：

```dotenv
LLM_MODE=live
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

请在本地填写真实 Key，Base URL 和 Model 改为你所用服务支持的值。Key 不应出现在前端、命令行参数、聊天、报告或 URL 中。供应商必须支持原生 Chat Completions Function Calling，Base URL 包含 API 前缀，后端追加 `/chat/completions`。系统环境变量优先于 `.env`；若系统已有同名变量，应在本地核对，不要把值粘贴到对话中。

`auto` 有 Key 为 Live、无 Key 为明示 Demo；`demo` 始终规则演示；`live` 无 Key 明确失败。修改普通聊天室配置后需重启后端。真实验收脚本独立读取配置并强制其临时后端使用 Live，即使普通聊天室仍是 Demo，也不会借用 Demo 响应。

## 一条命令执行真实验收

```powershell
# 从联合仓库根目录开始
cd task1-chatroom/backend
.\.venv\Scripts\python.exe ..\scripts\validate_real_llm.py
```

没有 Key 时直接输出 C / NOT RUN 并退出，不建立网络连接。Python 脚本退出码：0 为脚本后端检查通过，1 为测试失败，2 为缺少凭据；PowerShell 可通过 `$LASTEXITCODE` 查看。

脚本使用现有 FastAPI 应用与 AgentRunner，在随机本地端口启动单个临时服务，建立真实 HTTP / WebSocket 客户端，并使用独立 SQLite。不会重启普通聊天室、覆盖现有 Bot 或修改主数据库。无需新增依赖。

默认最多 **7 次模型请求**，没有自动重试：

1. 连通性：1 次纯文本请求。
2. 场景 A：模型原生 calculator 调用 + 工具结果返回后的最终答复，通常 2 次。
3. 场景 B：主 Bot 委派、子 Bot calculator、子 Bot 最终回复、主 Bot 最终总结，通常 4 次。
4. WebSocket 重连与 SQLite 独立连接核对不再触发模型请求。

额外模型轮次会消耗相同预算；超限立即失败，不盲目重试。确有需要时可显式提高到最多 12 次，例如 `--max-requests 9`，但应先查看失败原因。网络失败、模型不调用指定工具或首次链路失败会停止后续场景。

脚本仅在验收进程内给原 `llm.complete` 加观察包装，计数并记录协议元数据；所有请求仍调用原 HTTP 实现，**没有替换返回值、没有 Mock Transport、没有关键词伪造 Tool Calling**。自动化单元测试中的受控 Transport 只用于测试脚本本身，不产生真实验收报告。

## 严格通过条件与证据

场景 A 使用原始请求：

> @数据助手 请使用计算工具计算 128 × 36，并告诉我计算结果。

必须存在 calculator 原生响应及服务端工具记录，结果为 4608，工具结果按原始 ID 回填模型，最终收到 Live Bot 消息、completed 任务。模型直接回答 4608 而没有工具调用，脚本判为 **FAIL**。

场景 B 使用原始请求：

> @规划助手 请把“计算 128 × 36”这个任务委派给数据助手，等待数据助手返回计算结果后，再由你总结并回复我。

脚本创建独立的规划助手（仅启用 delegate_to_bot）和数据助手（仅启用 calculator），使用不同的 System Prompt。核对主任务、子任务、不同 Bot ID、委派工具的 child_task_id、子 Bot calculator、4608 结果、原生调用与工具回填 ID，以及主 Bot 携带委派结果的后续模型请求。

`report.json` 记录时间、模型、执行模式、请求预算/次数、Task/Bot ID、原生 `provider_call_id`、数据库记录 ID、工具输入输出、状态、请求的 Bot 和 System Prompt 摘要哈希、回填工具结果，以及失败原因。不记录 Authorization、Key、昵称身份 Token 或全部对话上下文。失败时保留已观察的真实任务与工具状态，绝不拼造成功链路。

数据库 `validation.db` 仅用于本轮隔离验收。原生 ID 与本地记录 ID 分开保存；两个独立 Bot 的模型即使复用调用 ID，也按 Bot 与任务关联验证。

## 测试范围与浏览器复核

此脚本自动覆盖真实 API、原生工具、真实 HTTP/WS 入口、重连快照、SQLite 独立读取；**不自动驱动真实模型的浏览器页面**，报告固定标明 `real_browser_ui=NOT RUN`。脚本全部后端项通过，仍应单独记录真实页面复核结果，不能用 Demo 浏览器测试替代。

配置后重启普通后端，再打开 `http://127.0.0.1:5173`，确认顶部为 LIVE MODEL。在一个新房间加入「规划助手」「数据助手」，按以上两条请求操作；核对最终答案、执行记录与刷新保留。若不想增加费用，先只进行脚本验收；浏览器再次发送两条请求会额外调用模型。当前没有凭据，因此本轮也没有执行这一步。

## 错误定位与已知边界

| 表现 | 优先检查 |
| --- | --- |
| HTTP 401 / 403 | Key、账号权限和供应商认证要求 |
| HTTP 404 | Base URL 是否包含正确前缀、Model 是否存在 |
| HTTP 400 / 422 | 供应商是否兼容 tools / tool_choice / tool_call_id 与工具 JSON Schema |
| HTTP 429 | 额度、限流；本脚本不会自动重试 |
| 连接失败 / 超时 | 网络、代理、服务地址；每次请求 45 秒、根任务 120 秒 |
| 无原生 calculator / delegate_to_bot | 模型工具能力或 Prompt；直接回答不算通过 |
| 工具 failed 或任务 failed | 参数 Schema、计算表达式、目标 Bot、共享 6 次预算与深度 2 |

原有安全 AST 计算器、共享预算、深度与总时限仍由业务代码执行。严格 Schema 同时拒绝额外字段、错误类型及缺失值。生产代码不硬编码 4608 或本次验收路径；4608 仅作为脚本测试断言。

当前只能判定 **C：未配置有效 API Key，仅完成受控协议和回归测试**。填入非空 Key 也不代表 Key 有效；必须执行连通性及两条链路后再更新结果。

`.env`、`.env.*`、数据库、依赖、缓存和 `artifacts/` 均不应打包上传。验收数据库含本地身份 Token，应保留在本机；若需分享证据，只在人工核对后分享脱敏 JSON，不分享数据库或真实环境文件。
