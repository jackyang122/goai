# Personal Learning OS — Backend (`src/plos/`)

Production **Python 3.9+ / FastAPI** backend that implements the full protocol in
[`docs/API协议.md`](../docs/API协议.md) (21 endpoints + `/ws/chat`) and lands the design in
[`docs/后端逻辑设计.md`](../docs/后端逻辑设计.md). The Pydantic schemas are a 1:1 camelCase
mirror of [`web/lib/api/types.ts`](../web/lib/api/types.ts), so the frontend `RealApi`
client switches to this backend with **zero changes**.

## 三条铁律（Iron rules）

1. **契约对齐** — `schemas/*` 是 `web/lib/api/types.ts` 的字节级镜像（camelCase）。
2. **MasteryEngine 唯一写** — `mastery` / `weakPoints` 的唯一写入方是 `MasteryEngine`；`MasteryRepository.commit_update` 是唯一写路径，用 `SELECT…FOR UPDATE` 按主题串行。Skill / 端点只产出 `sideEffects`，经 Engine 落库。
3. **派生语义** — `weakPoints = level < 0.6`（`PLOS_WEAK_THRESHOLD`），`mastery.level ∈ [0,1]`，`overallMastery` = 各主题均值，均在 `GET /state` 实时计算。

## 分层

```
api / ws        传输层（薄）：校验 + 委托
  ↓
domain          传输无关的业务核心
                  ChatTurnOrchestrator.run / run_stream  ← REST 与 WS 共用的统一管线
                  MasteryEngine · LearnerStateService · MemoryService
                  RagOrchestrator · QuizService · SemanticGrader · FsrsCardService
                  skills/{router, plan, coach, diagnosis, explain, practice, summary}
  ↓
db.repositories  唯一发 SQL 的层（BaseRepository + 各聚合）
providers        唯一触外部服务的层（每缝 ABC + 真实 + Stub，registry 按 Settings 装配）
```

## 快速开始

```bash
# 1. 依赖（Python 3.9+；按需选 extras：llm/embed/rag/mem0/bkt/fsrs/parse/dev/all）
pip install -e ".[all,dev]"

# 2. Postgres + pgvector（仓库根）
docker compose up -d postgres

# 3. 配置（可选：默认全是 stub/dev，零外部依赖也能起）
cp .env.example .env

# 4. 建表 + 种子（stu_001 demo 数据，幂等）
alembic upgrade head
python -m plos.cli seed

# 5. 起服务
uvicorn plos.app.main:app --port 8001 --reload
#   健康检查：GET http://localhost:8001/api/health
```

前端联调：`web/.env.local`
```
NEXT_PUBLIC_USE_MOCK=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

## CLI

```bash
python -m plos.cli run                 # 等同 uvicorn plos.app.main:app
python -m plos.cli seed                # 幂等种子
python -m plos.cli recompute-mastery   # 用闭式重算所有主题 trend
python -m plos.cli recompute-mastery --fit   # 离线 pyBKT 拟合重标定 mastery_params（仅离线！）
```

## Provider 缝（配置驱动，未配置即降级）

| 缝 | 真实 | Stub（默认） | 开启 |
|----|------|--------------|------|
| `llm` | LiteLLM（流式） | canned reply（镜像 `mock.ts`） | `PLOS_LLM_ENGINE=litellm` + key |
| `embedding` | BGE-M3（dim=1024） | 确定性 hash 向量 | `PLOS_EMBEDDING_ENGINE=bge` |
| `rag` | LlamaIndex（hybrid + reranker） | 关键词 | `PLOS_RAG_ENGINE=llamaindex` |
| `memory` | mem0（抽取/去重/检索 + 图） | 启发式 L1+L2 | `PLOS_MEMORY_ENGINE=mem0` |
| `parser` | Docling / MinerU | Stub | 附件/KB 文档摄入时 |
| `auth` | PocketBase（strict） | Dev 宽放（接受 `stu_001`） | `PLOS_AUTH_ENGINE=pocketbase` + url |

未配置项降级到 Stub 并打 warning；`GET /api/health` 返回 `{db, providers}` 状态。

## 关键设计要点

- **BKT 闭式前向**（`domain/mastery/bkt.py`）：在线用自实现 `posterior → transit` 闭式滤波（设计文档 §6.1），参数存 `mastery_params`；`pybkt.fit()` **仅离线** CLI 重标定。复现 UC-B：`二次函数` 答错 0.55→0.4094，答对→0.6561。
- **三层记忆**：L1 trace 同步落库（同事务，永不丢）；L2 事实轮末异步抽取/去重（mem0 + `derived_from` 边）；L3 会话末/闲置 LLM 合成。检索命中以 `Citation(source="Memory L{layer}·…")` 注入，前端复用 KB citation 渲染。
- **统一管线**：`ChatTurnOrchestrator.run` = `run_stream` 收割成单条 `ChatMessage`；WS 推送 NDJSON 事件 `skill → citation → content{delta} → payload → done`。8 对话场景 → 6 Skill → `ChatMessage.payload` 判别联合。
- **FSRS 间隔重复**：装了 `py-fsrs` 用 FSRS-5，否则区间回退；复习以软证据经 MasteryEngine 调 BKT。
- **分页双模**：列表端点默认裸数组（前端零改动）；带 `?limit=&cursor=` 返 `{items,nextCursor}` 信封。

## 测试

```bash
pytest                       # DB-free 逻辑测试（schema 判别联合 / 批改 / FSRS / 路由 / BKT）
```

端到端（需 Postgres+pgvector）参见 [`docs/API协议.md`](../docs/API协议.md) §11。

## 项目布局

```
src/plos/
├── app/        main(create_app) · lifespan(engine+providers+seed) · deps
├── api/        learners · skills · threads · kbs · quiz · cards · memory  (薄路由)
├── ws/         chat(/ws/chat) · events(NDJSON) · manager
├── schemas/    common · learner · skill · chat(+payload) · quiz · memory · kb · card  (镜像 types.ts)
├── domain/     learner_state · mastery(engine+bkt) · memory · chat · rag · quiz · grading · cards · attachments · skills/*
├── db/         engine · base · models/* · repositories/*
├── providers/  registry · llm · embedding · parser · memory · auth  (ABC + 真实 + Stub)
├── core/       config · logging · ids · time · units
├── seed/       data(镜像 web/lib/api/seed.ts) · seed(幂等)
├── alembic/    env(async) · versions/0001_initial(16 表 + HNSW)
└── cli.py
```
