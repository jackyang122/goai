# Personal Learning OS — 前端

Next.js 16 前端应用，连接 PLOS 后端（FastAPI）或使用本地 Mock 运行。

## 快速启动（Mock 模式，零外部依赖）

```bash
cd web
npm install
npm run dev
```

默认 `http://localhost:3000`，状态栏显示「本地演示 · Mock」。

## 完整启动（后端 + 数据库）

### 1. 启动数据库

```bash
# 在项目根目录执行
docker compose up -d postgres
```

### 2. 启动后端

```bash
cd src
uv sync                        # 首次运行，安装依赖
uv run plos run --port 8001 --reload
```

> 首次启动会自动建表并填充种子数据（学习者 `stu_001`）。

### 3. 启动前端

```bash
cd web
npm install
npm run dev
```

### 4. 配置 `.env.local`

`web/.env.local` 已预配为连接本地后端：

```
NEXT_PUBLIC_USE_MOCK=false
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8001
```

如需切回 Mock 模式，将 `NEXT_PUBLIC_USE_MOCK` 设为 `true`。

## 项目结构

```
web/
├── app/                    # Next.js App Router 页面
│   ├── page.tsx            # 仪表盘首页
│   ├── home/               # 对话页面
│   ├── learn/              # 学习页面
│   ├── practice/           # 练习页面
│   └── me/                 # 个人中心
├── components/             # UI 组件
│   ├── ui/                 # 基础组件（button, card, badge...）
│   ├── app-shell.tsx       # 应用外壳
│   └── theme-provider.tsx  # 主题
├── lib/
│   ├── api/                # API 客户端层
│   │   ├── client.ts       # 工厂：mock ↔ real 切换
│   │   ├── mock.ts         # 本地 Mock 实现
│   │   ├── types.ts        # 类型定义
│   │   └── seed.ts         # Mock 种子数据
│   ├── hooks.ts            # 前端数据 hooks
│   └── features.ts         # 功能开关
├── .env.local              # 本地环境变量（已 gitignore）
├── .env.example            # 环境变量模板
└── package.json
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `NEXT_PUBLIC_USE_MOCK` | `true` | `false` 时连接真实后端 |
| `NEXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:3782` | 后端地址 |
| `NEXT_PUBLIC_DEFAULT_PERSONA` | `teacher` | 默认 Agent 角色 |