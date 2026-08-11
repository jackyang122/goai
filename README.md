# Personal Learning OS

> Agent 原生的个性化学习操作系统 —— 让 AI 成为终身学习伙伴。基于 [DeepTutor](https://github.com/HKUDS/DeepTutor) 构建。

本仓库包含 **Personal Learning OS（PLOS）** 的产品前端与后端接口协议。前端是一个 Next.js 16 应用（`web/`），通过一套可替换的 API 客户端消费 **DeepTutor 后端**（FastAPI）以及三个 PLOS 扩展（Learner State、6 Skills、Mastery Engine）。

## 状态

- ✅ **可运行 Demo**：开箱即用，内置本地 Mock 后端，无需任何外部服务即可体验全部页面与交互。
- 📐 **接口协议已定义**：见 [`docs/API协议.md`](docs/API协议.md)，每个方法都映射到 DeepTutor 原生能力或 PLOS 扩展端点。
- 🚧 **模块逻辑待实现**：各模块的具体后端逻辑可未来实现，方案见 [`docs/模块方案.md`](docs/模块方案.md)。

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

> 注意：DeepTutor 原生提供 chat / KB / memory / quiz / mastery 等能力；PLOS 的 LearnerState / Skills / MasteryEngine 是其上的薄扩展，端点协议见 [`docs/API协议.md`](docs/API协议.md)，后端逻辑待实现。

## 项目结构

```
.
├── web/                      # Next.js 16 前端（PLOS 产品层）
│   ├── app/                  # App Router 页面：/ /home /learn /practice /me
│   ├── components/           # AppShell + 极简设计系统（shadcn 风格）
│   ├── lib/api/              # ★ 接口契约层：types / mock / client（mock↔real 可换）
│   └── lib/hooks.ts          # 前端数据 hook
└── docs/
    ├── index.md              # 产品文档（系统架构 / 模块 / 路由 / 技术栈）
    ├── 产品设计计划.md        # 产品设计计划（定位 / IA / 模块 / 路线图）
    ├── 实施方案.md            # 实施方案（架构 / 数据流 / 阶段 / 验收）
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
- **后端（DeepTutor）**：Python 3.11+ · FastAPI · WebSocket · LlamaIndex / LightRAG / GraphRAG / PageIndex
- **存储**：PostgreSQL + pgvector
- **AI**：多 Provider 网关（OpenAI / Anthropic / Gemini）· Tool-Use · RAG

## 文档导航

| 文档 | 内容 |
|------|------|
| [产品文档](docs/index.md) | 系统架构、核心模块、路由、技术栈 |
| [产品设计计划](docs/产品设计计划.md) | 定位、信息架构、模块设计、设计系统、路线图 |
| [实施方案](docs/实施方案.md) | 架构落地、数据流、分阶段交付、验收标准 |
| [API 协议](docs/API协议.md) | 端点契约、数据模型、DeepTutor 映射、组件选型 |
| [模块方案](docs/模块方案.md) | 各模块未来实现方案与开源组件选型 |

## License

Apache 2.0 · 基于 [DeepTutor](https://github.com/HKUDS/DeepTutor)（HKUDS）
