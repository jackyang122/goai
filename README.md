# 聆心 (LingXin) - 个性化学习操作系统

> Agent 原生的个性化学习操作系统 —— 让 AI 成为终身学习伙伴

## 运行入口

### 1. DeepTutor 后端服务 (端口 8003)

```bash
# Windows
cd main
start_deeptutor.bat

# Linux/Mac
cd main
./start_deeptutor.sh
```

**服务地址**: http://localhost:8003
**API 文档**: http://localhost:8003/docs

### 2. 前端界面 (端口 3000)

```bash
cd main/web
npm install      # 首次运行
npm run dev
```

**访问地址**: http://localhost:3000

## 依赖说明

### 系统依赖

| 依赖 | 版本要求 | 用途 |
|------|----------|------|
| Node.js | 18+ / 22 | 前端运行环境 |
| Python | 3.11 - 3.13 | 后端运行环境 |
| uv | 最新版 | Python 包管理器 |

### 前端依赖

```json
{
  "next": "16.2.3",
  "react": "19.x",
  "typescript": "5.x",
  "tailwindcss": "3.x"
}
```

### 后端依赖

```toml
[dependencies]
fastapi = "*"
uvicorn = "*"
pydantic = "2.*"
anthropic = "*"
```

## 配置文件

### DeepTutor 配置 (`main/.env`)

```bash
# 服务端口
DEEPTUTOR_PORT=8003
DEEPTUTOR_HOST=0.0.0.0

# LLM API 密钥
# DASHSCOPE_API_KEY=your_api_key_here
```

### 前端配置 (`main/web/.env.local`)

```bash
DEEPTUTOR_API_BASE_URL=http://127.0.0.1:8003
```

## 样例输入输出

### 对话输入样例

```json
{
  "type": "message",
  "content": "请解释什么是机器学习中的过拟合现象",
  "capability": "chat",
  "language": "zh"
}
```

### 流式输出样例

```json
{"type": "content", "data": "过拟合是机器学习中的"}
{"type": "content", "data": "一个重要概念..."}
{"type": "citation", "source": "knowledge_base"}
{"type": "done"}
```

### 记忆模块样例

**写入记忆**:
```json
{
  "op": "add",
  "text": "用户正在学习机器学习基础",
  "reason": "学习进度跟踪"
}
```

**读取记忆**:
```json
{
  "layer": "L3",
  "key": "profile",
  "content": "## 学习者档案\n\n- 正在学习: 机器学习\n- 水平: 初学者"
}
```

## 运行证据

### 服务健康检查

```bash
# DeepTutor 后端
curl http://localhost:8003/docs
# 返回: <title>DeepTutor API - Swagger UI</title>

# 前端
curl http://localhost:3000
# 返回: <title>聆心 - Personal Learning OS</title>
```

### 页面验证

1. **左上角品牌名称**: 显示 "聆心"
2. **底部版权信息**: "© 2026 聆心. All rights reserved. | Powered by deeptutor"
3. **侧边栏**: 无 GitHub 链接，保留文档链接
4. **记忆模块**: 可访问 /memory 路径查看三层记忆
5. **对话功能**: 可在 /home 页面进行 AI 对话

### API 端点验证

| 端点 | 方法 | 状态 | 说明 |
|------|------|------|------|
| /api/v1/sessions | GET | ✅ | 获取会话列表 |
| /api/v1/ws | WS | ✅ | WebSocket 流式对话 |
| /memory/overview | GET | ✅ | 记忆概览 |
| /knowledge/list | GET | ✅ | 知识库列表 |

## 启动顺序

1. **DeepTutor 后端** (8003) - LLM 服务
2. **前端界面** (3000) - 用户界面

## 故障排查

### 前端连接错误

确保 DeepTutor 后端正在运行在端口 8003，并检查 `main/web/.env.local` 配置正确。

### 端口冲突

```bash
# 检查端口占用
netstat -ano | grep ":8003"

# 更改端口配置
# 编辑 main/.env 中的 DEEPTUTOR_PORT
```

### 记忆功能异常

检查 DeepTutor 后端日志，确认记忆服务正常运行。

## 项目结构

```
goai/
├── main/              # 主项目代码
│   ├── web/           # Next.js 前端
│   ├── deeptutor/     # DeepTutor 核心代码
│   ├── deeptutor_cli/ # CLI 工具
│   └── .venv/         # Python 虚拟环境
├── docs/              # 项目文档
└── README.md          # 本文件
```

## License

Apache 2.0 · 基于 [DeepTutor](https://github.com/HKUDS/DeepTutor)
