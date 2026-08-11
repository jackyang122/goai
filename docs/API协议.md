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
- **时间**：ISO 8601 UTC 字符串。
- **ID**：字符串，建议 `<type>_<ulid>`。
- **分页**：列表端点支持 `?limit=20&cursor=<id>`，响应含 `{ items, nextCursor }`。

---

## 3. 鉴权

- 由 DeepTutor 的 **PocketBase** 账号体系承载。
- 请求头：`Authorization: Bearer <pb_token>`。
- `learnerId` 由 token 解析得出，服务端校验归属，忽略客户端传入的越权 `learnerId`。

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
| GET | `/api/learners/{id}/threads` | 会话列表 | Mock ✅ |
| GET | `/api/threads/{threadId}` | 单个会话 | Mock ✅ |
| POST | `/api/threads/{threadId}/messages` | 发送消息（非流式回执） | Mock ✅ |
| WS | `/ws/chat` | 流式聊天（生产用） | 待实现 |

POST 请求：
```json
{ "learnerId": "stu_001", "content": "二次函数顶点怎么求？", "persona": "teacher" }
```
响应：`ChatMessage`（assistant）。

消息结构对齐 [assistant-ui](https://www.assistant-ui.com/) 的 thread/message 模型：`{ id, role, content, createdAt, citations[], skill, status }`。生产环境用 `/ws/chat` 推送增量（见 §8）。

> **DeepTutor 映射**：会话与流式直接复用 DeepTutor 的 chat capability + `/ws`；PLOS 仅在消息上附加 `skill` 与 `citations`。

### 6.4 Knowledge Base（多引擎 RAG）

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/kbs` | 知识库列表 | Mock ✅ |
| POST | `/api/kbs` | 创建 KB（指定 engine） | 待实现 |
| POST | `/api/kbs/{id}/documents` | 上传文档并索引 | 待实现 |
| POST | `/api/kbs/{id}/search` | 检索（RAG） | 待实现 |

`engine ∈ { llamaindex, pageindex, graphrag, lightrag, obsidian }`。

> **DeepTutor 映射**：完全复用 DeepTutor Knowledge Center 的 kb 生命周期（create/add/search）与可插拔解析引擎（Text/MinerU/Docling/markitdown/PyMuPDF4LLM）。

### 6.5 Practice / Quiz

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | `/api/quiz/generate` | 从主题生成题目 | Mock ✅ / 待实现 |
| POST | `/api/quiz/grade` | 批改单题 | Mock ✅ / 待实现 |
| GET | `/api/learners/{id}/errors` | 错题本 | Mock ✅ |

> **DeepTutor 映射**：`generate` 映射 `deep_question` capability；`grade` 用 Agent + 评判 prompt。

### 6.6 Memory（三层）

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/learners/{id}/memory` | 三层记忆（L1/L2/L3） | Mock ✅ |
| POST | `/api/memory` | 写入记忆 | 待实现 |
| GET | `/api/learners/{id}/memory/graph` | Memory Graph（可追溯证据） | 待实现 |

> **DeepTutor 映射**：复用 DeepTutor 三层 Memory（L1 traces / L2 facts / L3 synthesis）与 `read_memory` / `write_memory` 工具。

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

连接：`wss://<origin>/ws/chat?token=<pb_token>`。客户端发送消息，服务端推送 NDJSON 事件：

| 事件 | 负载 | 说明 |
|------|------|------|
| `content` | `{ delta }` | 文本增量（assistant-ui 的 text stream） |
| `tool_call` | `{ tool, args }` | 调用工具（rag/exec/...） |
| `tool_result` | `{ tool, result }` | 工具结果 |
| `citation` | `{ id, source, snippet, locator }` | 引用片段 |
| `skill` | `{ skill }` | 命中的 Skill（用于 UI 角标） |
| `done` | `{ messageId }` | 本轮结束 |
| `error` | `{ code, message }` | 错误 |

心跳：服务端每 20s 发 `ping`，客户端回 `pong`；自动重连。

> 与 assistant-ui 对接：用 `useExternalStoreRuntime` 把上述事件折叠成 `ThreadMessage`；`content`/`tool_call`/`tool_result` 对应其 message parts。

---

## 9. 数据模型（PostgreSQL + pgvector）

```sql
-- 学习者与偏好
CREATE TABLE learners (
  id TEXT PRIMARY KEY,
  name TEXT, streak INT DEFAULT 0,
  study_time_total_min INT DEFAULT 0,
  preferences JSONB DEFAULT '{}',
  updated_at TIMESTAMPTZ
);

-- 知识点掌握度（MasteryEngine 唯一写入）
CREATE TABLE mastery (
  learner_id TEXT REFERENCES learners(id),
  topic TEXT, subject TEXT,
  level REAL CHECK (level BETWEEN 0 AND 1),
  trend TEXT, error_count INT DEFAULT 0,
  last_practiced_at TIMESTAMPTZ,
  PRIMARY KEY (learner_id, topic)
);

-- 目标与任务
CREATE TABLE goals ( id TEXT PRIMARY KEY, learner_id TEXT, title TEXT,
  subject TEXT, progress REAL, deadline DATE, source TEXT );
CREATE TABLE plan_tasks ( id TEXT PRIMARY KEY, goal_id TEXT, title TEXT,
  est_minutes INT, type TEXT, done BOOLEAN, ref JSONB );

-- 题库与错题
CREATE TABLE questions ( id TEXT PRIMARY KEY, type TEXT, prompt TEXT,
  options JSONB, answer TEXT, explanation TEXT, topic TEXT );
CREATE TABLE error_book ( id TEXT PRIMARY KEY, learner_id TEXT, question_id TEXT,
  user_answer TEXT, error_type TEXT, ts TIMESTAMPTZ, reviewed BOOLEAN );

-- 闪卡（间隔重复）
CREATE TABLE flash_cards ( id TEXT PRIMARY KEY, learner_id TEXT, front TEXT,
  back TEXT, topic TEXT, due TIMESTAMPTZ, stability REAL, difficulty REAL );

-- 会话与消息
CREATE TABLE threads ( id TEXT PRIMARY KEY, learner_id TEXT, title TEXT,
  persona TEXT, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ );
CREATE TABLE messages ( id TEXT PRIMARY KEY, thread_id TEXT, role TEXT,
  content TEXT, skill TEXT, status TEXT, citations JSONB, created_at TIMESTAMPTZ );

-- 记忆三层
CREATE TABLE memory ( id TEXT PRIMARY KEY, learner_id TEXT, layer TEXT,  -- L1/L2/L3
  content TEXT, source TEXT, created_at TIMESTAMPTZ );

-- 知识库（向量）
CREATE TABLE kb_documents (
  id TEXT PRIMARY KEY, kb_id TEXT, title TEXT, chunk_index INT,
  embedding VECTOR(1536),             -- pgvector
  content TEXT, locator TEXT, created_at TIMESTAMPTZ
);
CREATE INDEX ON kb_documents USING ivfflat (embedding vector_cosine_ops);
```

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

---

## 11. 实现优先级（与 [实施方案](实施方案.md) 一致）

1. **P1**：LearnerState 读写 + `/api/skills/invoke`（先打通 `learning-plan`、`personal-explain`、`adaptive-practice`）。
2. **P2**：接 DeepTutor 原生 chat `/ws` + KB。
3. **P3**：MasteryEngine + Memory Graph + Quiz 生成/批改。
4. **P4**：Partners / 多引擎 KB 全量。
