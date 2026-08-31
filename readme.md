# TeamFlow · 团队心流引擎

> **赋能个体专注，深化团队连接。**
> 集成本地化 AI、去中心化 P2P 通信、3D 知识可视化、离线优先架构的现代化团队协作工具。

<p align="center">
  <img alt="Electron" src="https://img.shields.io/badge/Electron-2B2E3A?style=flat-square&logo=electron&logoColor=9FEAF9"/>
  <img alt="Vue 3" src="https://img.shields.io/badge/Vue_3-4FC08D?style=flat-square&logo=vue.js&logoColor=white"/>
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white"/>
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white"/>
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white"/>
  <img alt="Three.js" src="https://img.shields.io/badge/Three.js-000?style=flat-square&logo=three.js&logoColor=white"/>
  <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square"/>
</p>

## ✨ 核心特性

| 特性 | 说明 |
|---|---|
| 🤖 **本地化 AI** | 基于 `node-llama-cpp` 在客户端本地跑大模型，通过 Tool Calling 桥接应用功能，**数据不出本机** |
| 🌐 **去中心化 P2P** | mDNS 自动发现 + WebRTC 数据通道，局域网内**零配置**即时通讯与文件共享 |
| 🧊 **离线优先** | 核心数据本地 SQLite 缓存，断网状态下所有功能仍可使用 |
| 🌌 **3D 知识可视化** | Three.js 力导向布局，把团队成员的技能 / 项目 / 文档映射为可探索的 3D 星系 |
| 🎨 **极致视觉** | 全响应式布局 + 亮色/暗色双主题，针对断点与 3D 渲染性能专项调优 |

## 🏗️ 系统架构

```
┌────────────────────────────────────────────────────────────────┐
│                      teamflow-app (Electron)                    │
│  ┌──────────────────────┐    ┌──────────────────────────┐     │
│  │   Main Process       │    │   Renderer Process       │     │
│  │   (Node.js)          │◀──▶│   (Vue 3 + Three.js)    │     │
│  │                      │    │                          │     │
│  │  • mDNS 节点发现     │    │  • 3D 知识星系渲染        │     │
│  │  • WebRTC P2P        │    │  • 离线优先 UI            │     │
│  │  • node-llama-cpp    │    │  • Pinia 状态管理         │     │
│  │  • SQLite 本地缓存   │    │  • UnoCSS + HeadlessUI   │     │
│  └──────────┬───────────┘    └─────────────┬────────────┘     │
│             │             WebSocket / HTTPS                  │
└─────────────┼──────────────────────────────────────────────────┘
              │                                                  ┌──────────────┐
              ▼                                                  │   第三方     │
┌────────────────────────────────────────────────────────────────┐  │  Resend     │
│                    backend (FastAPI)                           │  │  (邮件)     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  └──────────────┘
│  │   auth   │  │  teams   │  │   me     │  │highlights│        │
│  │  /auth/* │  │ /teams/* │  │  /me/*   │  │/highlight│        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │dashboard │  │  forum   │  │  alembic │   JWT 认证            │
│  │/dashboard│  │ /forum/* │  │ 迁移     │   Redis 黑名单       │
│  └──────────┘  └──────────┘  └──────────┘                       │
│            │              │                                    │
│            ▼              ▼                                    │
│      ┌──────────┐    ┌──────────┐                              │
│      │PostgreSQL│    │  Redis   │                              │
│      └──────────┘    └──────────┘                              │
└────────────────────────────────────────────────────────────────┘
```

## 🛠️ 技术栈

### 前端 `teamflow-app/`
- **桌面框架**：Electron 30+（主进程 / 预加载 / 渲染进程隔离）
- **UI 框架**：Vue 3.5 + TypeScript 5 + `<script setup>` SFC
- **状态管理**：Pinia 3
- **样式方案**：UnoCSS + HeadlessUI + 多主题切换
- **3D 渲染**：Three.js (WebGL/WebGPU 双后端) + 力导向布局
- **本地 AI**：`node-llama-cpp` 加载 GGUF 模型 + Tool Calling
- **P2P 通信**：mDNS 节点发现 + WebRTC 数据通道
- **包管理 / 构建**：pnpm 10 + electron-vite + electron-builder

### 后端 `backend/`
- **Web 框架**：FastAPI + Uvicorn (async)
- **ORM**：SQLAlchemy 2.0 async + Alembic 迁移
- **数据库**：PostgreSQL 16 + Redis 7
- **认证**：JWT (access + refresh token + Redis 黑名单)
- **邮件**：Resend SDK
- **中文分词**：jieba
- **容器化**：Docker + Docker Compose + Nginx 反代
- **测试**：Pytest 覆盖所有 RESTful 接口

## 📦 仓库结构

```
TeamFlow-Engine/
├─ readme.md                                # 本文件
├─ LICENSE                                  # MIT
├─ .gitignore
├─ docs/                                    # 设计与会议文档
│  ├─ 团队心流引擎.docx                     # 总体设计文档
│  ├─ 团队心流引擎__TeamFlow_Engine__API.openapi.yaml   # OpenAPI 3.0 规范
│  └─ 会议记录
├─ teamflow-app/                            # Electron + Vue 3 桌面应用
│  ├─ src/main/                             # Electron 主进程
│  │  ├─ index.ts                           #   窗口管理 / 系统集成
│  │  ├─ mDNS-discovery.ts                  #   局域网节点发现
│  │  ├─ p2p-connection.ts                  #   WebRTC 数据通道
│  │  └─ llama-cpp-bridge.ts                #   本地模型桥接
│  ├─ src/preload/                          # 预加载脚本（contextBridge）
│  ├─ src/renderer/                         # Vue 3 渲染进程
│  │  ├─ src/views/                         #   页面级路由
│  │  ├─ src/components/                    #   业务组件
│  │  ├─ src/stores/                        #   Pinia 状态
│  │  └─ src/three/                         #   Three.js 3D 场景
│  ├─ electron.vite.config.ts
│  ├─ electron-builder.yml
│  └─ .env.example                          # 前端配置样例
└─ backend/                                 # FastAPI 后端服务
   ├─ app/
   │  ├─ main.py                            # FastAPI 入口（CORS / 路由挂载）
   │  ├─ core/                              #   配置 / 数据库 / 模型 / 安全
   │  │  ├─ config.py                       #     pydantic-settings
   │  │  ├─ database.py                     #     async engine / session
   │  │  ├─ models.py                       #     SQLAlchemy ORM
   │  │  ├─ schemas.py                      #     Pydantic 数据契约
   │  │  ├─ security.py                     #     JWT / 密码哈希
   │  │  └─ crud.py                         #     数据库操作
   │  ├─ routes/                            #   RESTful 路由
   │  │  ├─ auth.py                         #     注册 / 登录 / 刷新 / 忘记密码
   │  │  ├─ teams.py                        #     团队 CRUD / 邀请
   │  │  ├─ me.py                           #     个人资料 / 设置
   │  │  ├─ highlights.py                   #     高光时刻（团队成就）
   │  │  └─ dashboard.py                    #     个人仪表盘
   │  └─ tests/                             #   Pytest 测试套件
   ├─ alembic/                              #   数据库迁移版本
   ├─ alembic.ini
   ├─ docker-compose.yml                    # 一键启动 db + redis + api
   ├─ Dockerfile
   ├─ nginx.conf                            # 反向代理
   ├─ openapi_v3.yaml                       # 自动生成的 API 规范
   ├─ requirements.txt
   └─ .env.example                          # 后端配置样例
```

## 🚀 快速开始

### 前置依赖

- Node.js 20+ 和 pnpm 10+
- Python 3.11+（如需跑后端）
- Docker Desktop（推荐，5 分钟起完整后端栈）

### 1. 克隆仓库

```bash
git clone https://github.com/wudixzy114/TeamFlow-Engine.git
cd TeamFlow-Engine
```

### 2. 启动后端（5 分钟）

```bash
cd backend
cp .env.example .env
# 编辑 .env：填入 SECRET_KEY（用 python -c "import secrets; print(secrets.token_hex(32))" 生成）

# 推荐：Docker 一键起 db + redis + api
docker-compose up --build -d

# 或本地开发
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

启动后访问 `http://localhost:8080/docs` 看 Swagger UI。

### 3. 启动前端

```bash
cd ../teamflow-app
cp .env.example .env
# 默认 VITE_API_BASE_URL=http://localhost:8080/api/v1（如后端在其他机器请改）

pnpm install
pnpm dev   # 启动 Electron 窗口
```

### 4. 验证

```bash
# 后端测试
cd backend && pytest

# 前端测试
cd teamflow-app && pnpm test
```

## 🧪 API 文档

- **运行时 Swagger UI**：`http://localhost:8080/docs`
- **OpenAPI 3.0 规范**：[`backend/openapi_v3.yaml`](./backend/openapi_v3.yaml) / [`docs/团队心流引擎__TeamFlow_Engine__API.openapi.yaml`](./docs/)
- **REST 风格**：所有业务路由统一前缀 `/api/v1`

## 🎯 关键设计决策

| 决策 | 理由 |
|---|---|
| **本地 AI 而不是云端 LLM** | 团队协作数据敏感；本地模型能保证**数据不出本机**，符合企业合规 |
| **mDNS + WebRTC 而不是中央服务器** | 分布式团队 / 跨地域小团队**零配置组网**；中继只在跨地域场景用 |
| **PostgreSQL + Alembic** | 业务关系复杂（团队 / 成员 / 高光 / 邀请）需要强约束 + 可演化的 schema |
| **Redis 存 JWT 黑名单** | 登出 / 改密场景需要立即失效 access token，纯 JWT 无法满足 |
| **离线优先 + 本地 SQLite 缓存** | 飞机 / 高铁 / 弱网场景是高频场景，不能因为网络问题影响思考流 |
| **Three.js 力导向布局** | 团队技能关系网是高维图结构，2D 表格塞不下，3D 比表格更直观 |

## 👥 团队

| 角色 | 成员 | 主要贡献 |
|---|---|---|
| **组长 / 主要作者** | **谢宗羽** ([@wudixzy114](https://github.com/wudixzy114)) | 前端 / Electron 集成 / 3D 渲染 / 本地 AI 集成 / P2P 通信，**约 90% 代码由本人完成** |
| 团队成员 | 王梓壑 | 前端 |
| 团队成员 | 向硒 | 后端 |
| 团队成员 | 鞠坤达 | 后端 |

> 原始开发环境：**清华大学软件学院软件工程课程 C4 组**（2025 春）。开源版本经全团队同意发布。

## 📄 License

[MIT](./LICENSE) — 4 位作者共同署名。

## 🙏 致谢

- 课程导师与同组同学的指导与协作
- Vue 3 / Electron / Three.js / FastAPI / PostgreSQL 等开源社区
