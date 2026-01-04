# TeamFlow (团队心流引擎)

> **赋能个体专注，深化团队连接。**
> TeamFlow 是一款集成了本地化 AI、去中心化 P2P 通信、3D 知识可视化以及离线优先架构的现代化团队协作工具。

---

## 🌟 项目亮点

- **离线优先架构**：本地与云端分离，核心功能在断网状态下依然能够正常使用。
- **本地化 AI 驱动**：基于 `node-llama-cpp` 实现本地大模型集成，通过 Tool Calling 控制应用功能。
- **去中心化连接**：利用 mDNS 与 P2P 技术，实现局域网内零配置的即时通讯与高速文件共享。
- **3D 技能可视化**：使用 Three.js 将团队技能结构映射为璀璨的 3D 星系。
- **极致视觉体验**：支持全响应式布局与多主题切换（亮色/暗色），经过专项 UI 效果调优。

---

## 🛠️ 技术栈

### 前端 (Frontend)
- **框架**: Vue 3 + TypeScript
- **状态管理**: Pinia
- **样式**: UnoCSS + HeadlessUI
- **桌面集成**: Electron
- **3D 渲染**: Three.js (WebGL/WebGPU)
- **包管理**: pnpm

### 后端 (Backend)
- **框架**: FastAPI (Python)
- **数据库**: PostgreSQL + Redis
- **ORM**: SQLAlchemy (Async)
- **迁移**: Alembic
- **容器化**: Docker & Docker Compose

---

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://git.tsinghua.edu.cn/se_group/se-teamflow-engine.git
cd se-teamflow-engine
```

### 2. 前端环境配置与运行
确保你已安装 [Node.js](https://nodejs.org/) 和 [pnpm](https://pnpm.io/)。

```bash
# 进入前端目录

# 安装依赖
pnpm install

# 启动开发环境 (包含 Electron 窗口)
pnpm dev

```

### 3. 后端环境配置与运行
推荐使用 Docker 快速部署环境。

```bash
# 进入后端目录

# 使用 Docker Compose 一键启动 (含 DB, Redis, API)
docker-compose up --build -d

# 如果是本地开发调试
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

---

## 🧪 测试说明

### 前端 UI 与功能测试
- 使用 **Vitest** 进行单元测试。
- 执行专项 **UI 效果测试**，针对响应式断点及 3D 渲染性能进行调优。

### 后端自动化测试
- 使用 **Pytest** 对所有 RESTful 接口进行覆盖测试。
```bash
pytest
```

---

## 👥 团队成员 (C4组)

- **前端开发**: 谢宗羽、王梓壑
- **后端开发**: 向硒、鞠坤达

---

## 📄 许可证
本项目仅用于清华大学软件工程课程展示。

---

### 💡 开发贴士
- **本地 AI**: 首次启动前端时，应用会自动配置本地模型环境，请确保磁盘空间充足。
- **P2P 互联**: 请确保测试设备处于同一局域网，以便 mDNS 能够正常发现节点。
- **API 文档**: 后端启动后，可访问 `http://localhost:8080/docs` 查看 Swagger UI。