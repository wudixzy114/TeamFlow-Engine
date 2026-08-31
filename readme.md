# TeamFlow (团队心流引擎)

> **赋能个体专注，深化团队连接。**
> 集成本地化 AI、去中心化 P2P 通信、3D 知识可视化、离线优先架构的现代化团队协作工具。

## 🌟 项目亮点

- **离线优先架构**：本地与云端分离，核心功能在断网状态下依然能够正常使用
- **本地化 AI 驱动**：基于 `node-llama-cpp` 在客户端本地跑大模型，通过 Tool Calling 控制应用功能
- **去中心化连接**：利用 mDNS 与 P2P 技术，实现局域网内零配置的即时通讯与高速文件共享
- **3D 技能可视化**：使用 Three.js 将团队技能结构映射为 3D 知识星系
- **极致视觉体验**：全响应式布局 + 多主题切换（亮色/暗色）

## 🛠️ 技术栈

### 前端 (Frontend)
- **框架**：Vue 3 + TypeScript
- **状态管理**：Pinia
- **样式**：UnoCSS + HeadlessUI
- **桌面集成**：Electron
- **3D 渲染**：Three.js (WebGL/WebGPU)
- **包管理**：pnpm

### 后端 (Backend)
- **框架**：FastAPI (Python) + Async SQLAlchemy
- **数据库**：PostgreSQL + Redis
- **迁移**：Alembic
- **容器化**：Docker & Docker Compose
- **认证**：JWT（access + refresh token + Redis 黑名单）

## 📦 仓库结构

```
TeamFlow/
├─ readme.md                      # 本文件
├─ LICENSE                        # MIT
├─ docs/                          # 设计文档与会议记录
│  ├─ 团队心流引擎.docx           # 总体设计文档
│  ├─ 团队心流引擎__TeamFlow_Engine__API.openapi.yaml   # OpenAPI 规范
│  └─ 会议记录
└─ teamflow-app/                  # Electron + Vue 3 桌面应用
   ├─ src/                        # 主进程 / 预加载 / 渲染进程
   ├─ resources/                  # 图标 / 静态资源
   ├─ electron.vite.config.ts
   ├─ electron-builder.yml        # 打包配置
   ├─ uno.config.ts
   ├─ package.json
   ├─ pnpm-lock.yaml
   └─ .env.example                # 配置样例（实际 .env 需自行创建）
```

## 🚀 快速开始

### 1. 克隆 & 安装

```bash
git clone https://github.com/wudixzy114/TeamFlow-Engine.git
cd TeamFlow-Engine/teamflow-app
pnpm install
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env：填入你的后端 API 地址
# 默认 VITE_API_BASE_URL=http://localhost:8080/api/v1
```

### 3. 启动开发模式

```bash
pnpm dev   # 启动 Electron 窗口
```

### 4. 启动后端

后端代码仓库（私有），如需自部署：

```bash
# 推荐用 Docker
docker-compose up --build -d

# 或本地开发
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

API 文档启动后访问 `http://localhost:8080/docs`。

## 🧪 测试

```bash
# 前端：Vitest 单元测试 + 专项 UI 效果测试
pnpm test

# 后端：Pytest 覆盖所有 RESTful 接口
pytest
```

## 🏗️ 架构要点

- **离线优先**：核心数据本地 SQLite 缓存，网络仅用于同步
- **本地 AI**：`node-llama-cpp` 加载 GGUF 模型，Tool Calling 桥接应用功能
- **P2P**：mDNS 节点发现 + WebRTC 数据通道
- **3D 知识图谱**：Three.js 力导向布局，把团队成员的技能 / 项目 / 文档映射成可探索的 3D 星系

## 👥 团队

| 角色 | 成员 | 贡献 |
|---|---|---|
| **组长 / 主要作者** | **谢宗羽**（[@wudixzy114](https://github.com/wudixzy114)） | 前端 / Electron 集成 / 3D 渲染 / 本地 AI 集成 / P2P 通信，**约 90% 代码由本人完成** |
| 团队成员 | 王梓壑 | 前端 |
| 团队成员 | 向硒 | 后端 |
| 团队成员 | 鞠坤达 | 后端 |

> 原始开发环境：清华大学软件工程课程 C4 组（2025 春）。开源版本经全团队同意发布。

## 📄 License

[MIT](./LICENSE)
