# 双项目联合交付验收报告

验收日期：2026-11-10，Asia/Shanghai。基于实际代码、现有测试和独立干净副本执行。原有项目、页面设计、单元测试和 E2E 全部保留；原始数据库与用户配置未删除、覆盖或用于本轮浏览器验收。

## 最终结论

| 范围 | 结论 | 限制 / 交付状态 |
| --- | --- | --- |
| 任务一 task1-chatroom | **PASS WITH LIMITATIONS** | Demo 业务、真实工具和持久化通过；真实供应商 LLM 未执行 |
| 任务二 task2-landing | **PASS** | 本地独立运行、响应式、交互与生产演示回退通过；尚未公开部署 |
| 联合本地源码验收 | **PASS WITH LIMITATIONS** | 已完成干净安装、测试和安全审查，详情如下 |
| GitHub 交付 | **PASS** | main 已推送；按用户要求改名 ChatBot 并切换 Public，任何人可查看与克隆；远程源码、安全和全新 clone 验证通过 |

## 任务一：实际功能验收

已阅读 README、ACCEPTANCE、REAL_LLM_VALIDATION，并检查实际 React / FastAPI / Agent / SQLite 源码。

| 功能 | 实际证据 | 结果 |
| --- | --- | --- |
| 昵称进入、创建和加入聊天室 | Edge 两个独立浏览器上下文；创建房间、第二端加入；同浏览器多标签页保留独立身份 | PASS |
| 多客户端 WebSocket 与消息展示 | 双向发送、核对对端内容与发送人、在线人数与 Bot 回复 | PASS |
| Bot 创建和管理、@ 触发 | 浏览器创建规划与数据助手、提及菜单与直接 @；后端验证房间 Bot 加入/移除与房间隔离 | PASS |
| calculator | 服务端执行 `(128 + 256) * 3 = 1152`；输入输出和 completed 状态；AST 安全边界测试 | PASS |
| get_current_time | 服务端 Asia/Shanghai / UTC 时间工具测试，浏览器触发真实时间工具 | PASS |
| delegate_to_bot 与返回汇总 | 规划助手 → 数据助手 → 规划助手；99 * 12 = 1188；两任务与两个工具轨迹；另一端收到最终汇总 | PASS（Demo 规则决策） |
| 深度、次数与超时限制 | 后端测试覆盖全链 6 次预算、深度 2、自身委派限制、根任务超时后清理子任务和工具 | PASS |
| 失败状态 | 浏览器除零触发错误，任务与工具 failed，刷新仍在；后端覆盖供应商错误、超时与损坏响应 | PASS |
| 消息、任务和工具轨迹 SQLite 持久化 | 浏览器刷新检查；后端应用重建、重连、历史分页与中断恢复测试 | PASS |

Bot 管理范围为创建和房间成员管理，未实现 Bot 配置编辑/删除。Demo 的工具执行、WebSocket 和数据库真实，模型决策与总结为规则；不宣称模型自由推理通过。

### 实际自动化结果

| 环境 / 命令 | 结果 |
| --- | --- |
| 原项目 backend：`.venv/Scripts/python.exe -m pytest -q --basetemp=./.test-tmp` | **57 passed，1 warning，2.74s** |
| 原项目 frontend：`npx tsc --noEmit`、`npm run build` | **PASS**；最终配置还在干净副本重新检查、构建 |
| 新 venv：相同 pytest 命令 | **57 passed，1 warning，2.77s** |
| 新 venv：`python -m pip check` | **PASS**：No broken requirements found |
| 干净 frontend：`npm ci`、`npm run build` | **PASS**，build 包含严格 TypeScript 检查 |
| 干净 frontend：`npm run test:e2e` | **4 passed，19.6s**，实际 Edge 浏览器 |

warning 为 Starlette 对 httpx 测试适配层的弃用提示，无测试失败。页面刷新/关闭连接时 Vite 记录过 ECONNABORTED，四项浏览器断言及页面无运行时错误检查均通过，不作为未执行测试的替代证据。

### 真实 LLM

**NOT RUN：缺少有效 API Key。** 本轮在干净副本执行 `scripts/validate_real_llm.py`，其八项供应商检查均为 NOT RUN，外部请求尝试 **0 次**。报告 `execution_mode=not_run`、`api_key_configured=false`。脚本缺凭据的预期退出码为 2；不计为真实模型 PASS，也没有回退 Mock 伪造报告。

现有 Live 集成代码、严格工具 Schema、原生 tool_call_id / provider_call_id、子 Bot 结果回填和主 Bot 继续调用代码均保留。受控 HTTP Transport Fixture 只验证协议和业务代码路径，不能证明实际供应商认证、额度、模型兼容性、工具选择或总结质量。真实浏览器供应商验证同为 NOT RUN。

其他已知限制：单进程、本地昵称身份、缺少生产权限、多进程共享、崩溃续跑、附件和 token 流式回复。本轮实测 Windows / Python 3.14 / Node 24 / Edge，其他平台未实测。

## 任务二：实际验收

已阅读 README、DELIVERY，检查页面组件、样式、CTA 配置与实际测试。导航、Hero、产品功能、工作流程、应用场景、FAQ、Footer、CTA 均存在并可显示。

| 项目 | 证据 | 结果 |
| --- | --- | --- |
| 响应式 375 / 768 / 1440px | 开发版与生产版各运行三种宽度；检查横向溢出、锚点、页面异常和资源失败；复核三张生产全页截图 | PASS |
| 导航与移动菜单 | 桌面四个导航目标；手机展开、Escape 关闭、选择后关闭与按钮关闭 | PASS |
| FAQ 与展示组件 | FAQ 展开/收起；产品演示场景切换；应用场景切换、方向键与焦点 | PASS |
| CTA | 开发目标通过拦截验证；生产所有工作台按钮指向 #product-preview 并标明演示；无 localhost 工作台链接 | PASS |
| 无公开工作台配置 | 默认空配置和 localhost / 内网 / 非 HTTPS 等 URL 防护测试 | PASS |
| 独立安装 | 干净副本 `npm ci`，不使用原 node_modules | PASS |
| 原项目与干净副本 `npm run build` | 均完成 TypeScript 与 Vite 生产构建 | PASS |
| 干净开发服务器及 Edge 测试 | **6 passed，10.2s**；自动启动新服务 | PASS |
| 干净生产预览及 Edge 测试 | **6 passed，9.7s**；`PLAYWRIGHT_PRODUCTION=1` | PASS |
| 公网部署与匿名 HTTPS | 没有公开官网 / 工作台地址，本轮不部署 | NOT RUN |

公网工作台未部署时保留明确产品演示，未伪造域名。普通开发端口 5174，普通生产预览 4174；测试用 15174 / 14174。

## 干净环境复现与联合检查

使用被忽略的独立 `.submission-work/clean/`，从现有源代码复制时排除 node_modules、.venv、真实 .env、数据库、构建、缓存与执行产物。

1. 使用系统 Python 创建全新 venv，按照 README 的 `requirements-lock.txt` 安装，未引用原虚拟环境；`pip check` 通过。
2. 两前端分别 `npm ci`，未复制原 node_modules；安装审计均报告 0 vulnerabilities（仅代表当次 npm 审计数据库）。
3. 从后端 `.env.example` 与官网 `.env.example` 生成干净副本配置；未复制用户私有配置。
4. 两前端严格类型检查与生产构建通过；后端 57 项测试、聊天室 4 项 E2E、官网开发及生产各 6 项全部通过。
5. 聊天室浏览器测试使用新临时 SQLite、独立进程与专用端口，强制 Demo；验证页面刷新与真实 WS。后端 pytest 还覆盖重建应用后的持久化。
   另按示例 `.env` 直接启动全新后端（隔离端口 18001，无额外 Demo 环境变量）：health=demo、初始一房间两 Bot；创建房间后关闭并重启进程，再次读取房间成功，跨进程 SQLite 持久化 PASS。
6. 默认开发端口 8000 / 5173 / 5174 和预览端口 4173 / 4174 合理；两个 npm 工程依赖隔离，无需全局统一 Vite / TypeScript。
7. Demo 无需额外配置 Key；必要依赖与锁文件齐全，浏览器实际资源检查无缺失，本地资源路径有效。

最初沙箱导致 realpath EPERM / Python 安装路径解析受限，授权在沙箱外重跑后通过。最初独立测试因默认端口已有服务退出，随后修正为专用端口并全部重跑；这些中间失败没有标记 PASS，也未停止或复用原有服务。

## 本轮最小修改

- 任务一 E2E 强制 Demo、临时 SQLite、18000 / 15173 专用端口且不复用现有服务，防止测试污染用户数据或意外调用收费模型。
- 任务一 Vite 代理支持仅服务端的 `RELAY_BACKEND_URL`，默认仍为 8000；改后重新 TypeScript 检查、构建与 4 项 E2E 通过。
- 任务二 E2E 使用 15174 / 14174 专用端口且不复用现有服务；改后开发与生产各 6 项通过。
- 补根 README、此报告、根 .gitignore 与只读暂存安全扫描脚本；修正项目文档个人路径及测试启动说明。无页面、框架或 Agent 业务重构，无删除测试。

## 安全审查

实际暂存检查 **75 个文件，PASS，0 个阻断发现**；最大文件 86,318 bytes，无超过 5 MiB 的文件、数据库或不明二进制。扫描对象为 `git ls-files --stage` 对应的实际 blob，而非仅扫描工作区文件。检查典型供应商 / GitHub / AWS / Google / Slack 凭据、私钥、数据库、环境文件、生成产物、二进制、超大文件和个人绝对路径，并核对必要依赖和测试文件。`git diff --cached --check` 通过；实际暂存清单、配置 diff 和 ignore 命中已检查。

发现并处理：原目录有 `.env`、SQLite / WAL、node_modules、venv、截图、真实验收 JSON、缓存与旧源码 zip，全部留在本机并由 ignore 排除；README 中的个人绝对路径替换为仓库相对启动方式。未发现实际凭据泄露，不需要撤销真实 Key。

补充检查字面凭据赋值、邮箱和手机号：候选均为三个后端测试文件中的假凭据，以及 URL 防护测试中的 `user:password@workspace.collabai.com` 测试 URL，不包含真实身份隐私；无手机号发现。项目已有安全脚本另扫描 44 个文件（含前端构建），无发现；未配置 Key、持久化日志 0 个。扫描不保证覆盖未知格式凭据；人工另审查配置、测试用凭据、URL 与源码差异。未将运行时身份 Token 或数据库加入源码。未审计用户全部终端历史或其他仓库。

## GitHub 交付

| 项目 | 实际状态 |
| --- | --- |
| Git | 已安装，2.56.0.windows.4 |
| GitHub CLI | 初始未安装；已在忽略的临时工具目录下载官方 2.103.3 便携版，并核对官方 SHA256 |
| 身份认证 | `gh auth status`：已验证账号 Huangqin77；使用本机 Git Credential Manager 保存的凭据，仅在当前进程供 gh 使用，未写入源码或索取 Token |
| 原有仓库 / 远程 | 恢复交付时已有本地 main / 0c61f7c，无远程；本次仅绑定新创建的本人仓库 |
| 仓库 URL | **https://github.com/Huangqin77/ChatBot** |
| 仓库可见性 | **Public**（API private=false、visibility=public）；用户明确要求向所有人开放查看和克隆 |
| 默认分支 | **main**（本地、远程一致） |
| 已验证源码 Commit Hash | **0c61f7ce41903abaaa6c0ec8ef47507e0a3f8f31**，首次推送与远程逐 blob 比对通过 |
| GitHub 最新 Commit Hash | 交付文档随后独立提交；[main 最新提交](https://github.com/Huangqin77/ChatBot/commits/main) 以 `git ls-remote origin refs/heads/main` 为准，最终精确 Hash 另在交付回复中列明，避免文档自引用提交 Hash |
| 上传时间 | **2026-11-10 21:25（Asia/Shanghai）首次源码上传**；本报告同步随后完成 |
| 同名仓库存在性 | 创建前本人账号下查询返回 HTTP 404，之后正常创建，无覆盖或 force push |
| 远程存在、main、两个源码目录、README、依赖和测试完整性 | **PASS**：API 文件树 75 个文件，与本地源码 blob 全部一致；README API 可读取；两个 .env.example、验收报告、源码、依赖清单及全部测试齐全 |
| 远程敏感文件复查 | **PASS**：GitHub 全新 clone 的暂存 / 跟踪 blob 75 个，0 个扫描发现；无真实 .env、数据库、依赖、构建、日志或本地私密执行记录 |
| 全新 GitHub clone 安装、构建 | **PASS**：两个前端 npm ci / npm run build；独立新 venv 安装锁定依赖、pip check、pytest 57 passed / 1 warning |

远程验证在被忽略的独立 `.submission-work/github-clone/` 完成。任务一首次 npm ci 遇到 ECONNRESET 网络中断，使用此前下载的包缓存重试后安装与构建通过；未修改依赖版本、源码或测试。任务二安装与构建、后端安装与 57 项测试均通过。本轮只补做 GitHub 交付与 clone 验证，浏览器 E2E 结果沿用上文本轮联合验收，不宣称本次再次运行。

后续可从仓库根目录验证远程提交：

```powershell
git remote -v
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

业务功能与已验收设计均未修改；本次只同步根 README 和本报告的实际 GitHub 状态。仓库最初按 Private 交付，随后于 2026-11-10 按用户明确要求重命名 ChatBot 并切换 Public；仓库 ID 1452697220 保持不变，本地 origin 已同步为新地址。直接分享仓库链接即可让面试官查看和克隆，无需逐个邀请。

**联合源码结论：PASS WITH LIMITATIONS（真实 LLM 仍缺 Key）。GitHub 源码交付：PASS。上传源码不等于聊天室或官网已公开部署。**
