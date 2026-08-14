# Personal Learning OS

> Agent 原生的个性化学习操作系统 —— 让 AI 成为终身学习伙伴。基于 [DeepTutor](https://github.com/HKUDS/DeepTutor) 构建。

本仓库包含 **Personal Learning OS（PLOS）** 的产品前端与后端接口协议与**完整后端实现**。前端是一个 Next.js 16 应用（`web/`），通过一套可替换的 API 客户端消费后端（FastAPI）；后端 `后端 backbone/` 已完整实现协议定义的全部 21 个端点 + WebSocket 流式。

## 状态

- ✅ **可运行 Demo**：开箱即用，内置本地 Mock 后端，无需任何外部服务即可体验全部页面与交互。
- **✅ 完整后端已实现**：`后端 backbone/`（Python 3.12+ / FastAPI）落地协议全部 21 端点 + `/ws/chat`，含 MasteryEngine（pyBKT）、三层 Memory（mem0）、多引擎 RAG（LlamaIndex）、FSRS 间隔重复、PocketBase 鉴权。运行见 [`后端 backbone/README.md`](后端%20backbone/README.md)。
- 📐 **接口协议完整**：见 [`docs/API协议.md`](docs/API协议.md)，21 端点完整目录 + `ChatMessage.payload` 判别联合 + 数据模型 + 组件映射。

## 快速开始

```bash
cd web
npm install          # Node 18+ / 22 已验证
npm run dev          # 默认 http://localhost:3000
```

打开浏览器即可看到仪表盘（Dashboard）首页。默认使用本地 Mock，状态栏会显示「本地演示 · Mock」。

## 切换到真实 DeepTutor 后端

Demo 默认 `NEXT_PUBLIC_USE_MOCK=true`。接入真实 DeepTutor 实例：

1. 启动 DeepTutor：`pip install -U deeptutor && deeptutor init && deeptutor start`（前端 :3782，后端 FastAPI :8001）。
2. 在 `web/` 下创建 `.env.local`：

   ```bash
   NEXT_PUBLIC_USE_MOCK=false
   NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:3782
   NEXT_PUBLIC_DEFAULT_PERSONA=teacher
   ```

3. `npm run build && npm run start`。Next.js 中间件会把 `/api/*`、`/ws/*` 转发到 DeepTutor 后端。

> 注意：DeepTutor 原生提供 chat / KB / memory / quiz / mastery 等能力；PLOS 的 LearnerState / Skills / MasteryEngine 是其上的薄扩展。

## 运行 PLOS 后端（`后端 backbone/`）

仓库自带完整后端实现，可替代 Mock 供前端联调（或独立部署）：

```bash
cd "后端 backbone"
pip install -e ".[all,dev]"                 # 依赖（按需选 extras）
docker compose up -d postgres               # 起 Postgres + pgvector（仓库根执行）
alembic upgrade head && python -m src.cli seed   # 建表 + 种子（stu_001）
uvicorn src.app.main:app --port 8001       # 起服务
```

`web/.env.local` 指向后端即可联调（`NEXT_PUBLIC_USE_MOCK=false` + `NEXT_PUBLIC_API_BASE_URL=http://localhost:8001`）。Provider 缝（LLM/Embedding/RAG/Memory/Auth）默认全 Stub，零外部依赖也能起；逐步配置见 [`后端 backbone/.env.example`](后端%20backbone/.env.example) 与 [`后端 backbone/README.md`](后端%20backbone/README.md)。

## 当前前端、PLOS 后端与 DeepTutor 的调用关系

当前系统将产品 API 与 Agent 运行时分开：浏览器只调用 PLOS 后端；PLOS 后端在启用 `deeptutor` LLM provider 后，作为客户端调用独立运行的 DeepTutor 服务。DeepTutor 不直接面向浏览器，也不替代 PLOS 的领域数据、学习状态和业务 API。

```text
浏览器（Next.js 前端）
        │
        ├─ HTTP REST / JSON ───────────────► PLOS FastAPI
        │  /api/*                              :8001
        │
        └─ WebSocket / JSON  ───────────────► /ws/chat
                                                 │
                                                 │ 仅当 PLOS_LLM_ENGINE=deeptutor
                                                 ▼
                                      DeepTutor Agent Service
                                      :8002 /api/v1/ws
                                      （能力编排、工具调用、模型访问）
```

| 链路 | 协议与端点 | 说明 |
| --- | --- | --- |
| 前端 → PLOS | HTTP REST + JSON，`/api/*` | 学习者状态、技能、线程、知识库、测验、卡片和记忆等产品业务接口。 |
| 前端 ↔ PLOS | WebSocket + JSON，`/ws/chat` | PLOS 向前端推送 `skill`、`citation`、`content`、`payload`、`done`、`error`、`ping` 等事件。 |
| PLOS → DeepTutor | WebSocket + JSON，`/api/v1/ws` | PLOS 发送 `{ "type": "message", "content": "...", "capability": "chat", "language": "zh" }`；读取 DeepTutor 的 `content`、`error`、`done` 事件。 |

PLOS 会保留自己的对话线程、学习者状态、掌握度、RAG 和记忆逻辑；调用模型生成时，将系统提示与历史对话整理为 DeepTutor 的单次 `message` 请求。DeepTutor 的 `content` 增量随后被转回 PLOS 原有的对话响应流，因此前端无需因接入 DeepTutor 改动协议。

DeepTutor 的统一 Agent API **不是** OpenAI `/v1/chat/completions`。如其启用了认证，PLOS 使用 `PLOS_DEEPTUTOR_TOKEN`，并在 WebSocket 连接中以 `?token=...` 传递；未启用认证时无需配置 token。为避免端口冲突，建议 PLOS 使用 `8001`，DeepTutor 使用 `8002`：

```bash
# 终端 1：DeepTutor Agent 服务
cd deeptutor-ref
uv run deeptutor serve --port 8002

# 终端 2：PLOS 后端（src/.env 中启用 deeptutor provider 后）
cd src
uv run plos run --port 8001 --reload
```

## 项目结构

```
.
├── web/                      # Next.js 16 前端（PLOS 产品层）
│   ├── app/                  # App Router 页面：/ /home /learn /practice /me
│   ├── components/           # AppShell + 极简设计系统（shadcn 风格）
│   ├── lib/api/              # ★ 接口契约层：types / mock / client（mock↔real 可换）
│   └── lib/hooks.ts          # 前端数据 hook
├── 后端 backbone/            # ★ FastAPI 后端（完整实现，见 后端 backbone/README.md）
│   ├── src/                  # api / ws / domain / db / providers / schemas / seed / alembic
│   ├── tests/                # DB-free 逻辑测试（pytest）
│   └── pyproject.toml
├── docker-compose.yml        # 本地 Postgres + pgvector
└── docs/
    ├── index.md              # 产品文档（系统架构 / 模块 / 路由 / 技术栈）
    ├── 产品设计计划.md        # 产品设计计划（定位 / IA / 模块 / 路线图）
    ├── 实施方案.md            # 实施方案（架构 / 数据流 / 阶段 / 验收）
    ├── 后端逻辑设计.md        # 后端行为规约（8 场景 / 统一管线 / BKT / 记忆 / 端点）
    ├── API协议.md             # ★ 后端接口协议（端点 / 模式 / 数据模型 / 组件映射）
    └── 模块方案.md            # 各模块未来实现方案与开源组件选型
```

## 核心架构

```
              ┌─────────────────────────────┐
              │   Unified Learning Agent     │  单一 Agent + 6 Skills
              └──────────────┬──────────────┘
                             │ 读 / 写
              ┌──────────────▼──────────────┐
              │      Learner State (核心)     │  贯穿全局的持久状态
              └──┬─────────┬────────────┬─────┘
        Knowledge/RAG   Question Bank   Mastery Engine   Session Memory
                             │
   ┌─────────┬───────────────┼───────────────┬─────────────┐
   ▼         ▼               ▼               ▼             ▼
Dashboard  学习            练习            对话            我的
(/)       /learn          /practice       /home          /me
```

## 技术栈

- **前端**：Next.js 16 · React 19 · TypeScript · Tailwind CSS v3 · lucide-react · framer-motion
- **后端（PLOS `src/`，已实现）**：Python 3.9+ · FastAPI · WebSocket · SQLAlchemy 2 (async) + asyncpg + Alembic
- **知识追踪 / 记忆 / RAG**：pyBKT（离线拟合）+ 闭式前向滤波 · mem0（三层记忆）· LlamaIndex（hybrid RAG）· py-fsrs（间隔重复）
- **AI 网关**：LiteLLM（多模型统一）· BGE-M3（embedding dim=1024）· Docling/MinerU（文档解析）
- **存储 / 鉴权**：PostgreSQL + pgvector（HNSW）· PocketBase
- **AI**：多 Provider 网关（OpenAI / Anthropic / Gemini）· Tool-Use · RAG

## 文档导航

| 文档 | 内容 |
|------|------|
| [产品文档](docs/index.md) | 系统架构、核心模块、路由、技术栈 |
| [产品设计计划](docs/产品设计计划.md) | 定位、信息架构、模块设计、设计系统、路线图 |
| [实施方案](docs/实施方案.md) | 架构落地、数据流、分阶段交付、验收标准 |
| [后端逻辑设计](docs/后端逻辑设计.md) | 后端行为规约：8 对话场景、统一管线、BKT、三层记忆、端点 |
| [API 协议](docs/API协议.md) | 端点契约、数据模型、DeepTutor 映射、组件选型 |
| [模块方案](docs/模块方案.md) | 各模块未来实现方案与开源组件选型 |

## License

Apache 2.0 · 基于 [DeepTutor](https://github.com/HKUDS/DeepTutor)（HKUDS）
