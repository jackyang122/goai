# Personal Learning OS 产品文档

> 基于 DeepTutor 构建的智能体原生个性化学习操作系统。将辅导、解题、测验、研究、可视化与掌握度练习整合在统一的工作区中，让 AI 真正成为终身学习伙伴。

- **版本**: v1.5.11
- **架构**: Agent-Native
- **技术栈**: Next.js 16 + Python 3.11+

---

## 系统架构

```
                         Personal Learning OS
                                │
                        Next.js Application
                                │
                ┌────────────────┼────────────────┐
                ↓                ↓                ↓

              首页              学习              作业
          (Home)           (Learning)        (Homework)

           shadcn/ui      DeepTutor UI      DeepTutor Quiz
                             +                   +
                         React-PDF          assistant-ui
                             +                   +
                       assistant-ui           tool-ui

                                │
                                ↓
                              我的
                          (Profile)

                   DeepTutor Knowledge
                   DeepTutor Memory
                   DeepTutor Settings
```

Personal Learning OS 采用四模块架构，以 Next.js 为应用容器，后端由 DeepTutor 提供统一的 Agent 运行时、知识管理与记忆系统支持。

---

## 核心模块

### 首页 (Home) — 智能对话中枢

**技术栈**: shadcn/ui

- Agent 选择与切换 — 支持多种 LLM 驱动的智能体
- Capability 配置 — 按需启用 Chat / Solve / Research / Visualize 等能力
- Persona 预设 — 切换 Teacher / Peer / Research Assistant 等角色
- 知识库关联 — 在对话中随时绑定 KB 进行 RAG 检索
- 会话管理 — 历史会话树、分支、续写、删除

### 学习 (Learning) — 沉浸式学习体验

**技术栈**: DeepTutor UI + React-PDF + assistant-ui

- 智能教科书 — AI 自动生成交互式教材，包含文本、代码、动画、测验等区块
- React-PDF 预览 — 在浏览器中直接预览 PDF 教材和文档
- Mastery Path 精通路径 — 自适应学习路径，按知识点类型逐步掌握
- Co-Writer 协作写作 — AI 辅助的文档协作编辑，支持实时修改
- 笔记本 — 从对话中保存笔记，构建个人知识体系
- Flash Cards 闪卡 — 自动生成复习卡片，巩固记忆

### 作业 (Homework) — 智能测验与作业系统

**技术栈**: DeepTutor Quiz + assistant-ui + tool-ui

- 智能测验生成 — 自动从教材内容生成选择题、填空题、问答题
- 自动批改 — AI 驱动的答案评判，支持多题型自动评分
- 错题本 — 自动收录错题至题库，支持针对性复习
- Deep Question 深度提问 — 从概念出发自动生成探究性问题
- tool-ui 工具集成 — 支持代码执行、数学计算等工具辅助解题

### 我的 (Profile) — 个性化学习管理

**技术栈**: DeepTutor Knowledge / Memory / Settings

- 知识库管理 — 创建多引擎 KB（LlamaIndex / PageIndex / GraphRAG / LightRAG）
- 记忆系统 — 三级记忆架构（L1 追踪 → L2 摘要 → L3 综合），可审计、可编辑
- Memory Graph — 可视化记忆图谱，追溯每条结论到原始证据
- 设置中心 — 模型配置、LLM 提供商、嵌入引擎、搜索、工具等全局设置
- 个人资料 — 头像、用户名、多语言偏好

---

## 导航与路由

| 路由 | 页面 | 布局分组 |
|------|------|----------|
| `/home` | Home 智能对话 | `(workspace)` |
| `/partners` | Partners 伙伴 | `(workspace)` |
| `/agents` | My Agents 智能体 | `(utility)` |
| `/co-writer` | Co-Writer 协作写作 | `(workspace)` |
| `/book` | Book 智能教科书 | `(workspace)` |
| `/space` | Learning Space 学习空间 | `(utility)` |
| `/memory` | Memory 记忆系统 | `(utility)` |
| `/knowledge` | Knowledge Center 知识库 | `(utility)` |
| `/settings` | Settings 设置中心 | `(utility)` |
| `/notebook` | Notebook 笔记本 | `(utility)` |
| `/profile` | Profile 个人资料 | `(utility)` |
| `/login` | Login 登录 | `(auth)` |
| `/register` | Register 注册 | `(auth)` |
| `/admin/users` | 用户管理 | `(admin)` |

### 布局分组说明

- **`(workspace)`** — 工作区布局，含侧边栏会话列表：Home、Partners、Co-Writer、Book、Playground
- **`(utility)`** — 工具布局，含侧边栏导航：Agents、Knowledge、Memory、Notebook、Profile、Settings、Space
- **`(auth)`** — 认证布局：Login、Register
- **`(admin)`** — 管理员布局：用户管理

---

## 技术栈

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- shadcn/ui
- Framer Motion

### Backend

- Python 3.11+
- FastAPI
- WebSocket
- Pydantic
- LlamaIndex
- LightRAG

### AI / LLM

- OpenAI / Anthropic / Gemini
- Claude Code / Codex 集成
- Multi-Provider Gateway
- Tool-Use & Function Calling
- RAG / GraphRAG / PageIndex

### Infrastructure

- Docker / Compose
- PocketBase (Auth)
- MCP Server
- WebSocket Streaming
- Standalone Next.js Output

---

## 核心特性

### 统一的 Agent 运行时

Chat、Quiz、Research、Visualize、Solve 和 Mastery Path 运行在同一个 Agent 循环上。切换的是目标，而非引擎，上下文始终随学习者流转。

### 互联的学习上下文

知识库、书籍、Co-Writer 草稿、笔记本、题库、人格预设和 Memory 在每个工作流中始终可用，而不是各自孤立。

### 子智能体与 Partners

在任意对话轮次中调用实时运行的编程 CLI（Claude Code、Codex）或 Partner，导入其历史对话，并在同一大脑上运行持久化的 IM 伴侣。

### 多引擎知识库

跨 LlamaIndex、PageIndex、GraphRAG、LightRAG 或链接的 Obsidian vault 的版本化 RAG 知识库，支持可插拔的文档解析引擎。

---

## 学习流程

```
                    ┌─────────────────┐
                    │   首页 / Home    │
                    │   Agent 对话中枢  │
                    └────────┬────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    ↓                        ↓                        ↓
┌───────────────┐    ┌──────────────────┐    ┌────────────────┐
│   学习 / Book  │    │   作业 / Quiz    │    │ 我的 / Profile  │
│   智能教科书    │    │   智能测验生成    │    │ 知识库 / 记忆   │
│   Mastery Path │    │   自动批改       │    │ 设置 / 个人资料  │
│   Co-Writer    │    │   错题本         │    │                │
└───────┬───────┘    └────────┬─────────┘    └────────────────┘
        │                     │
        └─────────────────────┘
                    │
                    ↓
           ┌─────────────────┐
           │   精通与巩固      │
           │   Flash Cards    │
           │   记忆持久化      │
           │   知识图谱        │
           └─────────────────┘
```

从首页的 Agent 对话开始，用户可进入学习模块阅读智能教科书、完成作业测验，所有学习数据通过知识库和记忆系统沉淀，形成持续进化的个性化学习闭环。

---

## 快速开始

```bash
# 安装 DeepTutor
pip install -U deeptutor

# 初始化配置
deeptutor init

# 启动应用
deeptutor start
```

启动后打开浏览器访问默认地址 [http://127.0.0.1:3782](http://127.0.0.1:3782) 即可进入 Personal Learning OS。

---

> Personal Learning OS — 基于 [DeepTutor](https://github.com/HKUDS/DeepTutor) 构建
>
> Apache 2.0 License · [官方文档 deeptutor.info](https://deeptutor.info/)