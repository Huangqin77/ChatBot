# 最终交付验收记录

> 以下保留任务一独立交付时的验收记录。本轮联合交付在干净副本重新执行 57 项后端测试与 4 项浏览器测试，均通过；E2E 现使用专用端口、强制 Demo 和临时 SQLite，不复用日常数据库。当前 Git、安全和 GitHub 状态见 [联合验收报告](../SUBMISSION_ACCEPTANCE.md)。

验收日期：2026-11-10，Asia/Shanghai。基于现有项目完成检查与必要修复，未重新创建项目，未修改或重构前端业务源码，未新增依赖。

## 实际运行结果

| 检查 | 命令 / 证据 | 结果 |
| --- | --- | --- |
| 后端核心与交付测试 | backend 中 `.\.venv\Scripts\python.exe -m pytest -q --basetemp=./.test-tmp` | **57 passed, 1 warning**；原有 45 项保持通过，提示为 Starlette 对 httpx 测试适配层的弃用提示 |
| 前端类型与生产构建 | frontend 中 `npm.cmd run build` | **通过**；TypeScript 通过，Vite 构建完成 |
| 浏览器端到端 | frontend 中 `npm.cmd run test:e2e` | **4 passed**，18.5 秒；实际无头 Microsoft Edge |
| 服务健康检查 | GET `http://127.0.0.1:8000/api/health` | `status=ok`、`mode=demo` |
| 前端访问 | GET `http://127.0.0.1:5173/` | HTTP **200** |
| 当前文件安全扫描 | backend 中 `.\.venv\Scripts\python.exe ..\scripts\security_check.py` | 无发现；无已配置 API Key；无持久化日志文件；Git 历史不适用，详见下文 |

## 核心业务 A–G

| 用例 | 已执行的验收 | 结果与边界 |
| --- | --- | --- |
| A 双客户端实时交换消息 | 两个独立 Edge 浏览器上下文，用不同昵称加入同一新房间，双向发送并核对内容和发送人 | **通过**；另验证同浏览器两个标签页独立昵称 |
| B 创建规划助手、数据助手并 @ | 浏览器实际填写两个 Bot 表单，加入房间；名称带时间后缀防重名；输入框选择 @，并发送直接提及 | **通过，Demo**；System Prompt 与工具配置持久化 |
| C calculator | 数据助手计算 `(128 + 256) * 3`，核对 1152，以及工具输入、输出和 completed 状态 | **通过，真实服务端工具执行** |
| D 规划助手委派数据助手 | `@规划助手<后缀> 请委派给数据助手<后缀>计算 99 * 12，并汇总结果` | **通过，Demo 的确定性委派决策**；持久化两个任务与 delegate_to_bot / calculator 记录 |
| E 子 Bot 回传与主 Bot 总结 | 第二客户端收到 1188 和规划助手 → 数据助手 → 规划助手链路；受控 Live HTTP 协议测试核对主 Bot 后续请求包含子 Bot 返回的 tool 结果 | **业务闭环与 Live 代码路径通过**；Demo 总结由规则生成，外部模型自由推理效果未验证 |
| F 刷新后持久化 | 浏览器刷新后核对 Bot、协作消息、任务树、工具记录；后端另测试销毁/重建应用仍加载同一 SQLite | **通过** |
| G 错误与状态 | 浏览器真实触发 `1 / 0`，检查系统错误、任务 failed、工具 failed，刷新再次核对；后端覆盖 HTTP 401/429、请求超时、无效 JSON、无效 tool_calls、截断响应与任务总超时 | **通过**；工具重试成功允许任务 completed，失败尝试记录保留 |

## 真实 LLM 链路检查

- Key、Base URL、Model 分别由后端 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL` 配置；环境变量优先于 `.env`。
- Live 使用原生 Chat Completions Function Calling。请求包含工具 JSON Schema，读取 `tool_calls`，服务端执行 calculator / delegate_to_bot 后，用原 `tool_call_id` 回填 `role=tool`，再发起下一轮模型请求。
- 子 Bot 有独立任务与模型上下文，返回结果进入主 Bot 工具结果；HTTP Transport Fixture 验证了「主 Bot 委派 → 子 Bot 计算 → 子 Bot 返回 → 主 Bot 最终总结」的 4 次请求，以及工具失败后重试的 5 次请求。
- 委派后代共享总共 6 次工具预算（含委派），委派深度最多 2，禁止自身委派；测试覆盖实际多层 Agent 循环，不只调用单个保护函数。
- 每个 Bot 最多 8 轮模型循环，每次请求最多 45 秒，主任务与全部后代总时限 120 秒。受控缩短时限测试验证超时后主任务、子任务和活动工具记录均进入 failed。
- `auto` 无 Key 为 Demo，`live` 无 Key 明确报错；Live 的供应商错误不回退到 Mock。
- **当前 `api_key_configured=false`，后端 `.env` 已由示例生成空 Key 的本地模板。没有发起任何外部真实 LLM 请求，也没有验证供应商模型是否按提示选择工具。** 已运行新增的真实验收脚本，八项 NOT RUN，外部请求尝试 0 次；报告与复现命令见 [REAL_LLM_VALIDATION.md](REAL_LLM_VALIDATION.md)。Fixture 的响应仍为测试数据，不能当作真实模型验收。

本轮最小补充：工具 Schema 和执行端共用严格 Pydantic 参数模型；工具记录新增可空 `provider_call_id`，保存模型原始调用 ID，旧 SQLite 增量添加字段；新增有凭据门禁、最多 7 次默认请求预算的真实验收脚本。新测试覆盖无 Key 零请求、预算、无工具直接回答必须失败、Schema、旧库兼容迁移、ID 关联和报告凭据清理。生产前端与 Agent 架构未变，未新增依赖。

协议依据：[OpenAI 官方 Function Calling 文档](https://developers.openai.com/api/docs/guides/function-calling)。

## 发现并修复的问题

1. **失败工具可能对应 completed 主任务。** 现在在最终返回前检查每种工具的最后一次尝试；存在未恢复失败则主任务 failed，并在聊天室显示错误。Live 可修正参数重试，同名工具成功后正常完成，历史失败记录保留。
2. **供应商响应结构缺少校验。** 补充 content、tool_calls、工具类型、唯一非空 ID、函数名和参数字符串校验；截断、拦截、空响应与损坏响应按任务失败处理，避免内部类型错误或把残缺结果当成最终答案。
3. **配置表示与未知异常可能暴露凭据。** Key 不再出现在 Settings repr；可公开错误替换当前 Key，未知异常日志只记录异常类型，不打印可能携带凭据的异常正文与堆栈。Base URL 拒绝用户凭据、查询参数和片段；空白 Key 视为未配置。
4. **环境文件忽略规则不足。** 扩展为 `.env` / `.env.*`，仅保留示例模板白名单；新增只读扫描脚本。
5. **新增验收测试选择器不够精确。** 规划助手 Prompt 引用了数据助手名称，导致全卡片文字匹配多个元素；改为 summary 内的精确名称匹配后，四项浏览器测试全部通过。

## 安全检查的证据与边界

- 当前业务源码和前端构建扫描没有发现典型 Key / 私钥模式或已配置 Key 的精确匹配；当前实际没有配置 Key。
- 本轮仅创建空 Key 的本地 `backend/.env` 模板，该文件被忽略，没有真实密钥，也没有执行 Git 提交。此目录及其父级当前不是 Git 仓库，**无法审计 Git 历史**，不能将此项表述为历史扫描通过。
- 没有持久化 `.log` 文件，扫描报告日志数为 0。日志捕获测试植入测试凭据，确认供应商错误正文、网络错误及非预期异常不会把该凭据写入日志、任务或系统消息；未审计全部历史终端输出。
- calculator 使用有长度、AST 节点数、指数和数值范围限制的 AST 白名单解释器，不执行 eval、exec、Shell、函数调用、属性访问或下标；恶意表达式和除零测试通过。
- 委派只面向同房间其他 Bot；深度 2、全链 6 次预算和总超时防止无限递归或无限工具循环。

## 交付范围与未验证事项

可交付本地 Coding 作业：前后端可运行、业务闭环已实测、README 含 Windows 启动、技术架构、Demo/Live 配置、演示流程与已知限制。现有前端业务界面保持不变。

仍未验证外部 LLM 的可用额度、供应商兼容性、实际工具决策与总结质量；需要在后端自行配置有效 Key 后验证，无需将密钥发送到对话中。项目仍不包含生产权限系统、多进程广播、任务崩溃自动续跑、Bot 编辑/删除、附件或 token 流式输出。

端到端测试生成的验收房间、Bot 与消息保留在本地数据库，便于复核；测试截图位于 `artifacts/desktop.png`、`artifacts/second-client.png`、`artifacts/mobile.png`。数据库、截图、依赖、缓存和本地环境文件均不属于源码提交内容。
