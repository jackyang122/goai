# Personal Learning OS — 后端接口协议

> 本文档定义 Personal Learning OS（PLOS）前端与后端之间的完整接口契约。它是后端实现的唯一依据：只要后端实现这些端点，前端无需改动即可切换到真实服务。代码中的类型定义见 [`web/lib/api/types.ts`](../web/lib/api/types.ts)，客户端见 [`web/lib/api/client.ts`](../web/lib/api/client.ts)。

---

## 1. 概述

PLOS 后端由两部分组成：

| 层 | 说明 | 复用 |
|----|------|------|
| **DeepTutor 原生** | chat / KB / memory / quiz / mastery 等能力，FastAPI（:8001），经 DeepTutor 自带 Next.js 中间件（`web/proxy.ts`）把 `/api/*`、`/ws/*` 代理到后端 | 直接复用，不重写 |
| **PLOS 扩展** | Learner State、6 Skills、Mastery Engine —— DeepTutor 没有的薄扩展层 | 需新建，协议见本文 |

前端只与**单一来源**（DeepTutor 的 Next.js origin，默认 :3782）通信；部署 PLOS 独立前端时，通过 Next.js `rewrites` 把 `/api/*`、`/ws/*` 转发到该 origin（见 [`web/next.config.mjs`](../web/next.config.mjs)）。

```
浏览器 ──▶ PLOS Next.js (:3000)
              │  /api/*  /ws/*   ← rewrites 转发
              ▼
        DeepTutor origin (:3782)
              │  /api/*  /ws/*   ← DeepTutor 自带 proxy
              ▼
        FastAPI 后端 (:8001)
          ├─ DeepTutor 原生路由（chat/kb/memory/quiz/...）
          └─ PLOS 扩展路由（learners / skills / mastery）★ 待实现
```

---

## 2. 通用约定

- **Base URL**：前端同源；通过环境变量 `NEXT_PUBLIC_API_BASE_URL` 指向 DeepTutor origin。
- **REST**：`/api/*`，JSON 请求/响应，UTF-8。
- **流式**：`/ws/*`，WebSocket（聊天、Agent 事件）。
- **作用域**：所有学习者数据以 `learnerId`（即 DeepTutor 用户 id）为键。
- **时间**：ISO 8601 UTC 字符串（如 `2026-08-13T09:30:00Z`）。
- **ID**：字符串，统一 `<type>_<ulid>`（如 `msg_01kzxny4ck...`、`kb_math`）。后端用 [`python-ulid`](https://pypi.org/project/python-ulid/) 生成。
- **命名**：请求/响应字段一律 **camelCase**，与 `types.ts` 字节对齐（后端 Pydantic schema 用 `populate_by_name`，序列化输出 camelCase）。
- **分页（双模）**：列表端点**默认返回裸数组**（`client.ts` 直接读数组，前端零改动）；当请求带 `?limit=&cursor=` 时，响应切换为信封 `{ items, nextCursor }`。`nextCursor` 为 `null` 表示无更多数据。`memory` 端点额外支持 `?layer=L1&topic=二次函数` 过滤。

---

## 3. 鉴权

- 由 DeepTutor 的 **PocketBase** 账号体系承载。
- 请求头：`Authorization: Bearer <pb_token>`（WebSocket 走查询参数 `?token=<pb_token>`）。
- `learnerId` 由 token 解析得出，服务端校验归属，忽略客户端传入的越权 `learnerId`（不符返回 `403`）。
- **严格 / 宽放双模**（后端 `PLOS_POCKETBASE_URL` 驱动）：
  - **已配置**（生产）：严格校验 bearer，调 PocketBase `/api/collection/users/auth-refresh` 取 `record.id`，TTL 缓存；路径/body 的 `learnerId` 与 token 不符 → `403`。
  - **未配置**（开发）：宽放，接受前端硬编码的 `stu_001`，便于零外部依赖联调。

---

## 4. 错误模型

所有错误使用统一信封：

```json
{ "error": { "code": "not_found", "message": "thread not found", "details": {} } }
```

HTTP 状态码：`400` 参数错误 · `401` 未认证 · `403` 越权 · `404` 不存在 · `409` 冲突 · `422` 校验失败 · `5xx` 服务端错误。

---

## 5. Learner State（核心数据模型）

贯穿全局的持久状态。完整 TypeScript 定义见 `types.ts` 的 `LearnerState`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `learnerId` | string | 用户 id |
| `name` | string | 显示名 |
| `streak` | int | 连续学习天数 |
| `studyTimeTodayMin` | int | 今日学习分钟 |
| `studyTimeTotalMin` | int | 累计分钟 |
| `overallMastery` | float 0..1 | 整体掌握度 |
| `weeklyChange` | float | 本周掌握度变化（如 0.06） |
| `sessionCount` | int | 会话数 |
| `weeklyQuestionCount` | int | 本周做题数 |
| `goals[]` | Goal[] | 学习目标（含任务） |
| `mastery[]` | MasteryPoint[] | 各知识点掌握度 |
| `weakPoints[]` | MasteryPoint[] | 派生：level < 0.6 |
| `dueCards[]` | FlashCard[] | 待复习闪卡 |
| `recentActivity[]` | Activity[] | 最近活动 |
| `preferences` | LearnerPreferences | persona / difficulty / dailyGoalMin / language |
| `updatedAt` | ISO string | — |

**写入规则**：`mastery` / `weakPoints` 的唯一权威写入方是 **MasteryEngine**；Skill 只能产出 `sideEffects`（声明式 delta），由 MasteryEngine 校验后落库。这避免多 Skill 互相覆盖。

---

## 6. 端点参考

### 6.0 完整端点目录（21）

> **归属**列：`PlosApi 原生` = 前端 `RealApi`（`client.ts`）实际调用的 13 个方法；`PLOS 扩展` = 后端已实现、支撑服务端流程与未来前端的能力，暂未进入 `PlosApi` 接口枚举。两类后端均已实现（✅）。另有运维端点 `GET /api/health`（返回 `{db, providers}` 状态）不计入协议。

| # | 方法 | 路径 | 归属 | `PlosApi` 方法 | 状态 |
|---|------|------|------|----------------|------|
| 1 | GET | `/api/learners/{id}/state` | 原生 | `getLearnerState` | ✅ |
| 2 | PATCH | `/api/learners/{id}/preferences` | 原生 | `updatePreferences` | ✅ |
| 3 | GET | `/api/learners/{id}/threads` | 原生 | `listThreads` | ✅ |
| 4 | GET | `/api/learners/{id}/errors` | 原生 | `listErrorBook` | ✅ |
| 5 | GET | `/api/learners/{id}/memory` | 原生 | `listMemory` | ✅（支持 `?layer&topic&limit&cursor`） |
| 6 | GET | `/api/skills` | 原生 | `listSkills` | ✅ |
| 7 | POST | `/api/skills/invoke` | 原生 | `invokeSkill` | ✅ |
| 8 | GET | `/api/threads/{id}` | 原生 | `getThread` | ✅ |
| 9 | POST | `/api/threads/{id}/messages` | 原生 | `sendMessage` | ✅（返 `ChatMessage` + 可选 `payload`） |
| 10 | WS | `/ws/chat` | 流式 | —（WS 客户端直连） | ✅ |
| 11 | GET | `/api/kbs` | 原生 | `listKnowledgeBases` | ✅ |
| 12 | POST | `/api/quiz/generate` | 原生 | `generateQuiz` | ✅ |
| 13 | POST | `/api/quiz/grade` | 原生 | `gradeAnswer` | ✅（返 `QuizResult` + 可选 `score/rationale`） |
| 14 | POST | `/api/kbs` | 扩展 | — | ✅ |
| 15 | POST | `/api/kbs/{id}/documents` | 扩展 | — | ✅ `202 indexing` |
| 16 | POST | `/api/kbs/{id}/search` | 扩展 | — | ✅ → `Citation[]` |
| 17 | POST | `/api/threads/{id}/attachments` | 扩展 | — | ✅ `202 indexing` |
| 18 | GET | `/api/learners/{id}/cards?due=true` | 扩展 | — | ✅（FSRS 到期卡） |
| 19 | POST | `/api/cards/{id}/review` | 扩展 | — | ✅（FSRS 复习 + 软证据） |
| 20 | POST | `/api/memory` | 扩展 | — | ✅（写记忆） |
| 21 | GET | `/api/learners/{id}/memory/graph` | 扩展 | — | ✅ → `{nodes, edges}` |

**单写者铁律**：`mastery` / `weakPoints` 的唯一写入方是 **MasteryEngine**——`POST /quiz/grade`、`POST /cards/{id}/review`、`POST /skills/invoke`（诊断 sideEffects）三条证据路径都经 MasteryEngine 落库，端点本身不直接写掌握度。

### 6.1 Learner State

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/learners/{id}/state` | 读取完整 LearnerState | Mock ✅ / 待实现 |
| PATCH | `/api/learners/{id}/preferences` | 更新偏好（persona 等） | Mock ✅ / 待实现 |

请求示例（PATCH preferences）：
```json
{ "persona": "teacher", "difficulty": "adaptive", "dailyGoalMin": 45 }
```
响应：完整 `LearnerState`。

### 6.2 Skills（统一 Agent 入口）

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/skills` | 列出 6 个 Skill 元信息（含 reads/writes） | Mock ✅ / 待实现 |
| POST | `/api/skills/invoke` | 调用某个 Skill | Mock ✅ / 待实现 |

请求（`SkillRequest`）：
```json
{
  "skill": "adaptive-practice",
  "learnerId": "stu_001",
  "input": { "topic": "二次函数", "count": 3 },
  "context": { "kbIds": ["kb_math"], "persona": "teacher" }
}
```
响应（`SkillResult`）：
```json
{
  "skill": "adaptive-practice",
  "output": { "questions": [ /* Question[] */ ] },
  "sideEffects": { "mastery": [ /* delta */ ] },
  "citations": [{ "id": "c1", "source": "kb_math", "snippet": "..." }],
  "trace": [{ "step": "选题 topic=二次函数" }]
}
```

> **DeepTutor 映射**：`invokeSkill` 在后端映射到 DeepTutor 的单 Agent 循环（capability pipeline），`skill` 决定装配哪组 tool/prompt。DeepTutor 原生 capability（chat/deep_solve/deep_question/...）可作为 Skill 的底层实现。

### 6.3 Chat（assistant-ui 兼容）

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/learners/{id}/threads` | 会话列表 | ✅ |
| GET | `/api/threads/{threadId}` | 单个会话（含 `messages[]`） | ✅ |
| POST | `/api/threads/{threadId}/messages` | 发送消息（非流式回执） | ✅ |
| POST | `/api/threads/{threadId}/attachments` | 上传附件（PDF/图片），后台解析入 KB | ✅ `202 indexing` |
| WS | `/ws/chat` | 流式聊天（生产用） | ✅ |

POST `/messages` 请求：
```json
{ "learnerId": "stu_001", "content": "二次函数顶点怎么求？", "persona": "teacher" }
```
响应：`ChatMessage`（assistant，含可选 `payload`，见下）。

**`ChatMessage` 结构**（对齐 assistant-ui 的 thread/message 模型）：
```
{ id, role, content, createdAt, citations?, skill?, status?, payload? }
```
`role ∈ {user|assistant|system|tool}`，`status ∈ {streaming|complete|error}`。生产环境用 `/ws/chat` 推送增量（见 §8）。

> **DeepTutor 映射**：会话与流式直接复用 DeepTutor 的 chat capability + `/ws`；PLOS 在消息上附加 `skill`、`citations` 与 `payload`。

#### 6.3.1 `payload` —— 8 场景结构化富内容〔协议扩展〕

`types.ts` 的 `ChatMessage` 不含 `payload`；这是 PLOS 为驱动「对话模块 8 场景」（[功能介绍/对话模块.md](功能介绍/对话模块.md)）新增的可选字段。一条 assistant 消息**至多携带一个** `payload`，由 `kind` 判别；纯文本消息省略之。前端按 `kind` 渲染对应结构化卡片，与 `citations` 并存。8 场景 → 6 Skill → `payload` 的映射：

| 场景 | Skill | `payload.kind` | 结构 |
|------|-------|----------------|------|
| 学习规划 | `learning-plan` | `plan` | `{ tasks: PlanTask[], rationale? }` |
| 作业辅导 | `homework-coach` | `coach` | `{ steps: StepTrace[] }` |
| 错因诊断 | `error-diagnosis` | `diagnosis` | `{ diagnosis: { cause, evidence?, remedy? } }` |
| 个性化讲解 | `personal-explain` | —（纯文本 + `citations`） | — |
| 出题/练习 | `adaptive-practice` | `quiz` | `{ question: Question }` |
| 错题归纳 | `mistake-summary` | `summary` | `{ patterns: {type,count,trend?}[], suggestion? }` |
| 答疑 | 路由命中讲解/辅导 | —（纯文本 + `citations`） | — |
| 知识库引用 | 任一 | —（通过 `citations[]` 渲染） | — |

> 判别联合在 TS 中即 `type ChatPayload = PlanPayload | CoachPayload | QuizPayload | DiagnosisPayload | SummaryPayload`（`kind` 为判别字段）。`PlanTask`/`StepTrace`/`Question` 复用 `types.ts` 既有定义，确保字段名 camelCase 一致。REST `POST /messages` 与 WS `payload` 事件都携带同一结构。

### 6.4 Knowledge Base（多引擎 RAG）

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/kbs` | 知识库列表（裸数组） | ✅ |
| POST | `/api/kbs` | 创建 KB（指定 engine） | ✅ |
| POST | `/api/kbs/{id}/documents` | 上传文档并索引（后台解析） | ✅ `202 indexing` |
| POST | `/api/kbs/{id}/search` | 检索（RAG）→ `Citation[]` | ✅ |

`engine ∈ { llamaindex, pageindex, graphrag, lightrag, obsidian }`。真实引擎装配 `llamaindex`（hybrid 检索 + bge-reranker）；其余/未配置返 `501` 并降级到关键词 Stub（保证链路可跑）。

POST `/kbs/{id}/search` 请求：
```json
{ "query": "二次函数顶点公式", "topK": 5 }
```
响应：`Citation[]`（`{ id, source, snippet, locator? }`），`source` 形如 `kb_math · 二次函数.pdf p.4`。附件上传（§6.3）解析后同样进入 KB，检索命中即作为 `citation` 注入对话。

> **DeepTutor 映射**：完全复用 DeepTutor Knowledge Center 的 kb 生命周期（create/add/search）与可插拔解析引擎（Text/MinerU/Docling/markitdown/PyMuPDF4LLM）。

### 6.5 Practice / Quiz

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | `/api/quiz/generate` | 从主题生成题目（LLM） | ✅ |
| POST | `/api/quiz/grade` | 批改单题（语义批改 + 写 MasteryEngine + 错题本） | ✅ |
| GET | `/api/learners/{id}/errors` | 错题本（裸数组） | ✅ |

POST `/quiz/generate` 请求：`{ learnerId, topic, count }` → `Question[]`。
POST `/quiz/grade` 请求：`{ learnerId, question, userAnswer }` → `QuizResult`。

**`QuizResult` 结构**（`types.ts` 基线 + PLOS 扩展字段）：
```json
{
  "questionId": "q_...", "correct": false, "userAnswer": "(2, 1)", "topic": "二次函数",
  "score": 0.0, "rationale": "符号方向错误：将 -b/2a 误写为 b/2a"
}
```
`questionId/correct/userAnswer/topic` 为 `types.ts` 基线（前端必读）；`score ∈ [0,1]`、`rationale` 为〔协议扩展〕——开放题按 rubric 给分、附批改理由，选择题/填空题则 `score ∈ {0,1}`。批改后 `correct=false` 自动写入错题本，并经 MasteryEngine 以 `obs ∈ {correct,wrong}` 调 BKT 前向更新掌握度（见 §6.1 铁律）。

> **DeepTutor 映射**：`generate` 映射 `deep_question` capability；`grade` 用 Agent + 评判 prompt。

### 6.6 Memory（三层）

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/learners/{id}/memory` | 三层记忆（L1/L2/L3），裸数组 | ✅ |
| POST | `/api/memory` | 写入记忆（L2 显式写入） | ✅ |
| GET | `/api/learners/{id}/memory/graph` | Memory Graph（节点 + 可追溯证据边） | ✅ |

GET `/memory` 查询参数：`?layer=L1&topic=二次函数&limit=20&cursor=<id>`（不带 `limit/cursor` 返裸数组，带则返 `{items,nextCursor}` 信封）。

POST `/memory` 请求：`{ learnerId, content, source?, layer?, topic? }` → `MemoryItem`。对话流程中 **L1 trace 同步落库**（同事务，永不丢）；**L2 事实轮末异步抽取/去重**（mem0 + `derived_from` 边）；**L3 会话末 LLM 合成**。

GET `/memory/graph` 响应：
```json
{ "nodes": [ MemoryItem... ], "edges": [ { "from": "mem_a", "to": "mem_b", "kind": "derived_from" } ] }
```
检索注入时，命中记忆以 `Citation(source="Memory L2·事实…")` 形式返回，前端复用 KB citation 渲染（零改动）。

> **DeepTutor 映射**：复用 DeepTutor 三层 Memory（L1 traces / L2 facts / L3 synthesis）与 `read_memory` / `write_memory` 工具。

### 6.7 Cards（FSRS 间隔重复）〔PLOS 扩展〕

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/learners/{id}/cards?due=true` | 列出到期闪卡（裸数组） | ✅ |
| POST | `/api/cards/{cardId}/review` | 复习一张卡，重排 + 软证据更新掌握度 | ✅ |

GET 请求：`?due=true` 只返回到期卡；返回 `FlashCard[]`。
POST `/cards/{id}/review` 请求：`{ rating: 1|2|3|4 }`（FSRS 评级，1=Again … 4=Easy）→ `{ card: FlashCard, nextDue: ISO }`。

调度：装了 [`py-fsrs`](https://pypi.org/project/fsrs/) 用真实 FSRS-5 调度，否则用稳定区间回退调度器；复习结果以 `weight` 软证据经 MasteryEngine 调 BKT（正确回忆→掌握度微升，遗忘→回退）。错题（§6.5）可自动生成闪卡补入此队列。

---

## 7. 六大 Skill 契约

| Skill | input | output | reads | writes |
|-------|-------|--------|-------|--------|
| `learning-plan` | `{ goal?, availableMin? }` | `{ plan: PlanTask[], rationale }` | mastery, goals, preferences | goals |
| `homework-coach` | `{ material \| question }` | `{ steps: string[] }` | mastery, preferences | recentActivity |
| `error-diagnosis` | `{ question, userAnswer }` | `{ cause, remedy }` | mastery | weakPoints, mastery |
| `personal-explain` | `{ concept, depth? }` | `{ explanation }` | mastery, preferences | recentActivity |
| `adaptive-practice` | `{ topic?, count }` | `{ questions: Question[] }` | mastery, weakPoints | mastery（批改后） |
| `mistake-summary` | `{ range? }` | `{ patterns: {type,count}[] }` | weakPoints | mastery, weakPoints |

闭环：`error-diagnosis → mistake-summary → adaptive-practice → mastery↑ → learning-plan 调整`。

---

## 8. WebSocket 流式协议（聊天 / Agent）

连接：`wss://<origin>/ws/chat?token=<pb_token>`（token 走查询参数）。客户端发送 JSON `{ threadId, learnerId, content, persona?, kbIds? }`，服务端推送 **NDJSON**（每行一个事件）。

**事件信封**：每行是扁平对象 `{"type": <事件>, ...负载}`。一轮对话的典型事件序列：

```
{"type":"skill","skill":"learning-plan"}
{"type":"citation","id":"c1","source":"Memory L2·…","snippet":"…"}
{"type":"citation","id":"c2","source":"kb_math · …","snippet":"…"}
{"type":"content","delta":"根据你当前的掌握度"}
{"type":"content","delta":"，建议今天的轨道是…"}
{"type":"payload","payload":{"kind":"plan","tasks":[…],"rationale":"…"}}
{"type":"done","messageId":"msg_…"}
```

| 事件 | 负载字段 | 说明 |
|------|----------|------|
| `skill` | `skill` | 命中的 Skill（UI 角标） |
| `citation` | `id, source, snippet, locator?` | 引用片段（记忆 / KB 命中） |
| `tool_call` | `tool, args` | 调用工具（rag/exec/...） |
| `tool_result` | `tool, result` | 工具结果 |
| `content` | `delta` | 文本增量（assistant-ui 的 text stream，LaTeX `$…$` 原样透传） |
| `payload` | `payload` | 结构化富内容（§6.3.1 判别联合，与 REST `ChatMessage.payload` 同构） |
| `done` | `messageId` | 本轮结束，消息已落库 |
| `error` | `code, message` | 错误（`unauthorized`/`forbidden`/`bad_request`/`internal`） |
| `ping` | — | 心跳（无负载） |

心跳：服务端每 `PLOS_WS_PING_INTERVAL`（默认 20s）发 `{"type":"ping"}`，客户端回 `pong`；自动重连。鉴权失败在 `accept` 后立即发 `error{code:"unauthorized"}` 并关闭。

> REST `POST /messages` = 把上述流「收割」成单条 `ChatMessage`（`content` 拼接、`citations`/`payload` 收集），二者共用 `ChatTurnOrchestrator.run_stream` 同一管线。
> 与 assistant-ui 对接：用 `useExternalStoreRuntime` 把事件折叠成 `ThreadMessage`；`content`/`tool_call`/`tool_result` 对应其 message parts，`payload` 建模为按 `kind` 渲染的自定义 part。

---

## 9. 数据模型（PostgreSQL + pgvector）

> 16 张表，与 Alembic `0001_initial` 一致。向量列 `VECTOR(<EMBEDDING_DIM>)`，**BGE-M3 = 1024**（由 `PLOS_EMBEDDING_DIM` 参数化；原文档按 OpenAI 写的 1536 已废弃）。索引用 **HNSW**（免预加载，优于 ivfflat）；`CREATE EXTENSION vector` 自包含在迁移首行。

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- 学习者与偏好
CREATE TABLE learners (
  id TEXT PRIMARY KEY, name TEXT, streak INT DEFAULT 0,
  study_time_today_min INT DEFAULT 0, study_time_today_date DATE,
  study_time_total_min INT DEFAULT 0, weekly_change REAL DEFAULT 0,
  session_count INT DEFAULT 0, weekly_question_count INT DEFAULT 0,
  preferences JSONB DEFAULT '{}', updated_at TIMESTAMPTZ
);

-- 知识点掌握度（MasteryEngine 唯一写入；level∈[0,1]）
CREATE TABLE mastery (
  id TEXT PRIMARY KEY, learner_id TEXT REFERENCES learners(id),
  topic TEXT, subject TEXT, level REAL CHECK (level BETWEEN 0 AND 1),
  trend TEXT DEFAULT 'flat', error_count INT DEFAULT 0,
  last_practiced_at TIMESTAMPTZ,
  UNIQUE(learner_id, topic)
);

-- BKT 参数（离线 pybkt.fit 重标定；默认 L0=.5 T=.1 S=.2 G=.2，UC-B 用 T=.10 S=.30 G=.30）
CREATE TABLE mastery_params (
  id TEXT PRIMARY KEY, learner_id TEXT REFERENCES learners(id),
  topic TEXT, l0 REAL DEFAULT 0.5, t_transit REAL DEFAULT 0.1,
  slip REAL DEFAULT 0.2, guess REAL DEFAULT 0.2, updated_at TIMESTAMPTZ,
  UNIQUE(learner_id, topic)
);

-- 目标与任务
CREATE TABLE goals ( id TEXT PRIMARY KEY, learner_id TEXT, title TEXT,
  subject TEXT, progress REAL, deadline DATE, source TEXT, created_at TIMESTAMPTZ );
CREATE TABLE plan_tasks ( id TEXT PRIMARY KEY, goal_id TEXT, title TEXT,
  est_minutes INT, type TEXT, done BOOLEAN, ref JSONB, ordering INT );

-- 题库与错题
CREATE TABLE questions ( id TEXT PRIMARY KEY, type TEXT, prompt TEXT,
  options JSONB, answer TEXT, explanation TEXT, topic TEXT, skill TEXT );
CREATE TABLE error_book ( id TEXT PRIMARY KEY, learner_id TEXT, question_id TEXT,
  question_snapshot JSONB, user_answer TEXT, error_type TEXT, ts TIMESTAMPTZ, reviewed BOOLEAN );

-- 闪卡（FSRS-5 调度列）
CREATE TABLE flash_cards ( id TEXT PRIMARY KEY, learner_id TEXT, front TEXT, back TEXT,
  topic TEXT, due TIMESTAMPTZ, stability REAL, difficulty REAL, state INT DEFAULT 0,
  reps INT DEFAULT 0, lapses INT DEFAULT 0, last_review TIMESTAMPTZ,
  elapsed_days INT DEFAULT 0, scheduled_days INT DEFAULT 0, created_at TIMESTAMPTZ );

-- 会话、消息、附件
CREATE TABLE threads ( id TEXT PRIMARY KEY, learner_id TEXT, title TEXT,
  persona TEXT, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ, seq INT );
CREATE TABLE messages ( id TEXT PRIMARY KEY, thread_id TEXT, learner_id TEXT, role TEXT,
  content TEXT, skill TEXT, status TEXT DEFAULT 'complete',
  citations JSONB, payload JSONB,             -- payload = §6.3.1 判别联合
  created_at TIMESTAMPTZ, seq INT );
CREATE TABLE attachments ( id TEXT PRIMARY KEY, thread_id TEXT, learner_id TEXT,
  filename TEXT, mime TEXT, size INT, storage_path TEXT, kb_id TEXT,
  status TEXT DEFAULT 'indexing', created_at TIMESTAMPTZ );  -- 202 后台解析入 KB

-- 记忆三层 + 可追溯证据边
CREATE TABLE memory ( id TEXT PRIMARY KEY, learner_id TEXT, layer TEXT,  -- L1/L2/L3
  content TEXT, source TEXT, topic TEXT, confidence REAL DEFAULT 1.0,
  evidence JSONB, embedding VECTOR(1024), created_at TIMESTAMPTZ );
CREATE INDEX ix_memory_embedding_hnsw ON memory USING hnsw (embedding vector_cosine_ops);
CREATE TABLE memory_edge ( id TEXT PRIMARY KEY, learner_id TEXT,
  src_memory_id TEXT REFERENCES memory(id), dst_memory_id TEXT REFERENCES memory(id),
  relation TEXT, weight REAL DEFAULT 1.0, created_at TIMESTAMPTZ );  -- relation=derived_from

-- 知识库（向量）+ 活动
CREATE TABLE kb ( id TEXT PRIMARY KEY, owner_learner_id TEXT, name TEXT,
  engine TEXT DEFAULT 'llamaindex', document_count INT DEFAULT 0,
  status TEXT DEFAULT 'indexing', created_at TIMESTAMPTZ );
CREATE TABLE kb_documents ( id TEXT PRIMARY KEY, kb_id TEXT REFERENCES kb(id),
  title TEXT, chunk_index INT, embedding VECTOR(1024), content TEXT,
  locator TEXT, created_at TIMESTAMPTZ );
CREATE INDEX ix_kb_documents_embedding_hnsw ON kb_documents USING hnsw (embedding vector_cosine_ops);
CREATE TABLE activity ( id TEXT PRIMARY KEY, learner_id TEXT, type TEXT, label TEXT, ts TIMESTAMPTZ );
```

**派生 vs 落库**：`weakPoints`（`level < PLOS_WEAK_THRESHOLD`，默认 0.6）、`overallMastery`（各 `mastery.level` 均值）、`weeklyChange`（存 `learners.weekly_change`）在 `GET /state` 实时计算返回，不单列存储。

---

## 10. 开源组件映射（快速实现指引）

| 协议域 | 推荐开源组件 | 角色 |
|--------|-------------|------|
| Agent 运行时 / Skills | **DeepTutor + ADK**（Agent Development Kit） | 单 Agent 循环 + capability 装配 |
| 聊天 UI | **assistant-ui** | thread/message 渲染 + runtime |
| 多引擎 RAG | **LlamaIndex** / **LightRAG** / **GraphRAG** / **PageIndex** | KB 检索 |
| 文档解析 | MinerU / Docling / markitdown / PyMuPDF4LLM | KB 摄入 |
| 向量存储 | **PostgreSQL + pgvector** | 嵌入检索 |
| 认证 | **PocketBase** | 账号 / token |
| PDF 预览 | **react-pdf** | Reader |
| 数学渲染 | **KaTeX** | Book / Quiz |
| 后端框架 | **FastAPI** + WebSocket | REST + 流式 |
| 子智能体 | Claude Code / Codex CLI | Partners |

### 10.1 已落地实现栈（`后端 backbone/`）

| 协议域 | 实现组件（真实 ↔ Stub 降级） |
|--------|------------------------------|
| LLM | **LiteLLM**（统一多模型 + 流式）↔ Stub（镜像 `mock.ts` canned reply） |
| Embedding | **BGE-M3**（dim=1024，Sentence-Transformers）↔ Hash Stub（确定性向量） |
| RAG | **LlamaIndex**（hybrid + bge-reranker）↔ 关键词 Stub |
| Memory | **mem0**（抽取/去重/检索 + 可选 Neo4j 图）↔ 启发式 Stub（L1 + 朴素 L2） |
| 文档解析 | **Docling** / MinerU（线程池）↔ Stub |
| 知识追踪 | **pyBKT**（离线 `.fit()` 重标定）+ 自实现闭式前向滤波（在线） |
| 间隔重复 | **py-fsrs**（FSRS-5）↔ 区间回退调度 |
| 鉴权 | **PocketBase**（bearer 校验）↔ Dev 宽放 |
| ORM / 迁移 | **SQLAlchemy 2 (async)** + asyncpg + **Alembic**（async） |
| 向量 | **pgvector**（HNSW 索引） |

每条「缝」都是 ABC + 真实实现 + Stub，由 `providers/registry.py` 按 `Settings` 装配；未配置项降级到 Stub 并打 warning，保证零外部依赖也能起服务。

---

## 11. 实现状态

本文档定义的全部 21 个端点已由 `后端 backbone/`（Python 3.12+ / FastAPI）实现，覆盖原路线图 P1–P4：

- ✅ **P1**：LearnerState 读写 + `/api/skills/invoke`（6 Skill 全通）。
- ✅ **P2**：`/ws/chat` 流式 + KB（create/documents/search + 附件）。
- ✅ **P3**：MasteryEngine（pyBKT 闭式前向，复现 UC-B 0.55→0.41→0.66）+ 三层 Memory + Memory Graph + Quiz 生成/语义批改。
- ✅ **P4**：FSRS 间隔重复 + 软证据、provider 缝全装配（LiteLLM/mem0/LlamaIndex/BGE-M3/Docling）、PocketBase 严鉴权、离线 `recompute-mastery --fit` 重标定。

**运行**（详见 [`后端 backbone/README.md`](../后端%20backbone/README.md)）：
```bash
cd "后端 backbone"
pip install -e ".[all,dev]"           # 装依赖（按需选 extras）
docker compose up -d postgres          # 起 Postgres+pgvector（见仓库根 docker-compose.yml）
alembic upgrade head && python -m src.cli seed   # 建表 + 种子（stu_001 可用）
uvicorn src.app.main:app --port 8001  # 起服务
```
前端联调：`web/.env.local` 设 `NEXT_PUBLIC_USE_MOCK=false` + `NEXT_PUBLIC_API_BASE_URL=http://localhost:8001`。

**契约对齐**：后端 Pydantic schema 是 `web/lib/api/types.ts` 的 1:1 camelCase 镜像；JSON 字节级一致，前端 `RealApi` 无需改动即可切换。三条铁律（契约对齐 / MasteryEngine 唯一写 / `weakPoints=level<0.6`）由 schema 校验 + 仓库写权限收敛 + CI grep 守护。
