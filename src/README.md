# Personal Learning OS Backend

这份文档只描述当前 `src/` 里的后端实现。

## 总览

这是一个以 FastAPI 为核心的单体后端应用，按“接口层 -> 业务层 -> 基础设施层”组织，包名为 `plos`（见 `pyproject.toml`）。所有外部能力（LLM、Embedding、Memory、Auth、Parser）都通过 `providers/` 抽象，未配置时自动降级到 stub，因此后端可以在不接任何外部服务时启动。

## 目录结构

```
src/
├── pyproject.toml          # 包定义（plos 0.1.0）+ 依赖（核心/可选组 llm/embed/mem0/parse/bkt/dev）+ 入口点
├── uv.lock                 # uv 锁定文件
├── .env.example            # 环境变量样例（PLOS_ 前缀）
│
├── src/                    # 后端源码包
│   ├── cli.py              # CLI 入口：`uv run plos run|seed`（等价 `python -m src.cli`）
│   │
│   ├── app/                # 应用装配层
│   │   ├── main.py         # FastAPI 应用工厂：挂载 REST/WS 路由、CORS、/api/health
│   │   ├── deps.py         # 依赖注入：get_session / get_auth / get_providers / get_token
│   │   ├── errors.py       # 统一异常处理（bad_request/not_found/forbidden…）
│   │   └── lifespan.py     # 应用生命周期（启动/关闭）
│   │
│   ├── api/                # HTTP 路由层（薄传输层：只做参数校验 + 身份解析 + 服务调用）
│   │   ├── learners.py     # /api/learners/{id}/state、preferences、threads、errors、cards
│   │   ├── threads.py      # /api/threads/{id}、messages（非流式对话）、attachments
│   │   ├── skills.py       # /api/skills、/api/skills/invoke（技能直调）
│   │   ├── quiz.py         # /api/quiz/generate、/api/quiz/grade
│   │   ├── cards.py        # 闪卡到期查询 / 复习（FSRS + BKT 软证据）
│   │   ├── kbs.py          # /api/kbs、documents 上传索引、search 检索
│   │   ├── memory.py       # 记忆读写（L1/L2/L3）+ 记忆图谱
│   │   └── _pagination.py  # 分页工具
│   │
│   ├── ws/                 # WebSocket 流式聊天
│   │   ├── chat.py         # /ws/chat 主循环：接收 JSON → 逐事件推送 NDJSON
│   │   ├── events.py       # 事件行序列化（skill/citation/content/payload/done/error/ping）
│   │   └── manager.py      # 连接管理 + 20s 心跳
│   │
│   ├── domain/             # 业务编排层（核心逻辑）
│   │   ├── chat.py         # ChatTurnOrchestrator：统一对话管线（REST 与 WS 共用）
│   │   ├── learner_state.py # LearnerStateService：聚合 learner/mastery/goal/card/activity
│   │   ├── memory.py       # MemoryService：L1 写入、检索引用、L2/L3 抽取
│   │   ├── rag.py          # RagOrchestrator：KB 向量检索编排
│   │   ├── quiz.py / grading.py / cards.py / attachments.py  # 测验、批改、闪卡、附件解析
│   │   ├── mapping.py      # ORM → 前端契约（ChatThread/ChatMessage）映射
│   │   ├── mastery/        # 掌握度引擎
│   │   │   ├── engine.py   # MasteryEngine：读写 mastery 的唯一入口
│   │   │   └── bkt.py      # pyBKT 贝叶斯知识追踪（可选）
│   │   └── skills/         # 技能系统（Agent 的能力集）
│   │       ├── router.py   # SkillRouter：6 技能注册表 + 分发
│   │       ├── base.py     # Skill 抽象基类 + SkillContext
│   │       ├── routing.py  # 关键词路由 pick_skill + canned_reply（stub 回复）
│   │       ├── plan.py / coach.py / diagnosis.py / explain.py / practice.py / summary.py
│   │       └──            # 6 个内置技能实现
│   │
│   ├── providers/          # 外部能力抽象层（每个都有 stub 降级）
│   │   ├── llm.py          # LiteLLMProvider（真实）/ StubLLM（确定性回复）
│   │   ├── embedding.py    # BGE-M3（可选）/ Stub
│   │   ├── memory.py       # mem0（可选）/ Stub
│   │   ├── auth.py         # DevAuth（固定 stu_001）/ PocketBase
│   │   ├── parser.py       # docling 文档解析（可选）
│   │   └── registry.py     # ProviderContainer：按 *_engine 配置装配真实或 stub
│   │
│   ├── db/                 # 数据访问层
│   │   ├── engine.py       # asyncpg 连接池（含 pgbouncer 事务池模式）
│   │   ├── base.py         # SQLAlchemy 基类
│   │   ├── vector.py       # pgvector 向量列支持
│   │   ├── models/         # ORM 模型：learners/chat/mastery/cards/quiz/goals/memory/kb
│   │   └── repositories/   # 仓储：按实体封装查询（learner/chat/mastery/cards/quiz/goals/memory/kb）
│   │
│   ├── schemas/            # Pydantic 契约（与 web/lib/api/types.ts 对齐）
│   │   ├── common.py       # SkillId/PersonaId 等公共枚举
│   │   ├── learner.py      # LearnerState/MasteryPoint/PlanTask…
│   │   ├── chat.py         # ChatMessage/ChatThread/ChatPayload 判别联合
│   │   ├── skill.py        # SkillMeta/SkillRequest/SkillResult/Citation
│   │   ├── quiz.py / card.py / kb.py / memory.py
│   │   └──                # 各领域 DTO
│   │
│   ├── seed/               # 演示数据
│   │   ├── seed.py         # 幂等 seeder：`uv run plos seed` 导入演示数据
│   │   └── data.py         # 演示数据集定义
│   │
│   ├── alembic/            # 数据库迁移
│   │   ├── env.py
│   │   └── versions/0001_initial.py  # 初始建表迁移
│   │
│   └── core/               # 基础工具
│       ├── config.py       # pydantic-settings 配置（PLOS_ 前缀）
│       ├── ids.py          # ID 生成（msg_/thr_/act_…）
│       ├── time.py         # 时间工具
│       ├── units.py        # 数值工具（clamp/round_mastery）
│       └── logging.py      # 日志
│
├── tests/                  # pytest 测试（test_skills/test_bkt/test_cards/test_grading…）
├── test_api_direct.py      # 手动冒烟脚本：直调 LLM/后端
└── test_msg.py             # 手动冒烟脚本：POST 一条对话消息
```

## 启动方式

```bash
# 进入 src/，安装依赖（首次）
uv sync

# 启动后端（开发模式，热重载）
uv run plos run --port 8001 --reload

# 导入演示数据（幂等，可重复执行）
uv run plos seed
```

## 调用 DeepTutor 服务

DeepTutor 使用自身的统一 WebSocket 协议，不是 OpenAI Chat Completions 端点。先单独启动它（避免与 PLOS 的 `8001` 端口冲突）：

```bash
cd ../deeptutor-ref
uv run deeptutor serve --port 8002
```

然后在 `src/.env` 设置：

```dotenv
PLOS_LLM_ENGINE=deeptutor
PLOS_DEEPTUTOR_BASE_URL=http://127.0.0.1:8002
PLOS_DEEPTUTOR_CAPABILITY=chat
PLOS_DEEPTUTOR_LANGUAGE=zh
# 仅在 DeepTutor 启用认证时填写
# PLOS_DEEPTUTOR_TOKEN=...
```

PLOS 会将对话转为 DeepTutor `/api/v1/ws` 的 `message` 事件，并把 `content` 事件转回自身 REST/WS 响应。

配置通过 `src/.env`（`PLOS_` 前缀）管理；数据库用 Supabase 时需用 asyncpg 格式连接串并设 `PLOS_DB_POOL_MODE=pgbouncer`。

## 对外接口

- 学习者服务：`/api/learners/{learner_id}/state`、`/api/learners/{learner_id}/preferences`、`/api/learners/{learner_id}/threads`、`/api/learners/{learner_id}/errors`
- 技能服务：`/api/skills`、`/api/skills/invoke`
- 对话服务：`/api/threads/{thread_id}`、`/api/threads/{thread_id}/messages`、`/api/threads/{thread_id}/attachments`
- 知识库服务：`/api/kbs`、`/api/kbs/{kb_id}/documents`、`/api/kbs/{kb_id}/search`
- 测验服务：`/api/quiz/generate`、`/api/quiz/grade`
- 卡片复习服务：`/api/learners/{learner_id}/cards`、`/api/cards/{card_id}/review`
- 记忆服务：`/api/learners/{learner_id}/memory`、`/api/memory`、`/api/learners/{learner_id}/memory/graph`
- WebSocket：`/ws/chat`

## 关键业务流程

- `LearnerStateService` 聚合 learner、mastery、goal、card、activity 等数据，生成前端仪表盘所需状态。
- `ChatTurnOrchestrator` 是统一对话编排器，负责 thread 创建、消息持久化、记忆写入、技能路由、RAG 检索、LLM 生成、结构化 payload 和 L2 抽取；REST（`send_message`）和 WS（`/ws/chat`）共用 `run_stream` 同一条管线。
- `SkillRouter` 维护 6 个内置技能：`learning-plan`、`homework-coach`、`error-diagnosis`、`personal-explain`、`adaptive-practice`、`mistake-summary`。
- `ProviderContainer` 根据 `PLOS_*_ENGINE` 配置装配真实能力或 stub 实现，因此后端可以在不接外部服务时启动。

## 运行特性

- 默认 CORS 允许所有来源
- 健康检查接口是 `GET /api/health`（返回 db 连通性与各 provider 实际使用的 engine）
- `providers` 默认使用 stub，除非显式切换到真实服务
- WebSocket `/ws/chat` 会保持心跳，支持流式返回 skill、citation、content、payload 和 done 事件
