# TeamFlow Backend

FastAPI + PostgreSQL + Redis 后端服务，实现团队协作的认证、数据持久化、消息路由。

## 路由总览

所有业务路由统一前缀 `/api/v1`：

| 模块 | 路径前缀 | 关键端点 |
|---|---|---|
| 认证 | `/api/v1/auth` | `POST /register/` · `POST /login/` · `POST /logout/` · `POST /token/refresh/` · `POST /forgot-password/` · `POST /reset-password/` |
| 团队 | `/api/v1/teams` | `GET/POST /` · `GET/PUT/DELETE /{id}` · `POST /{id}/invitations` |
| 个人 | `/api/v1/me` | `GET /` · `PUT /` · `PUT /password` |
| 高光时刻 | `/api/v1/highlight` | `GET/POST /` · `DELETE /{id}` |
| 仪表盘 | `/api/v1/dashboard` | `GET /` · `GET /team-summary` |
| 论坛 | `/api/v1/forum` | `GET/POST /topics` · `GET/POST /topics/{id}/replies` |

## 关键模块

### `app/core/`
- **`config.py`** — pydantic-settings 加载 `.env`
- **`database.py`** — async SQLAlchemy engine + session
- **`models.py`** — User / Team / Membership / Invitation / Highlight / ForumTopic / ForumReply ORM
- **`schemas.py`** — Pydantic 数据契约（请求/响应）
- **`security.py`** — JWT 签发 / 验证 / 密码哈希（bcrypt）
- **`crud.py`** — 通用数据库操作

### `app/routes/`
- **`auth.py`** — 注册 / 登录 / 刷新 / 登出 / 忘记密码（带 Resend 邮件 + Redis 黑名单）
- **`teams.py`** — 团队 CRUD + 邀请流
- **`me.py`** — 个人资料管理
- **`highlights.py`** — 团队高光时刻（成就记录）
- **`dashboard.py`** — 个人 / 团队仪表盘数据聚合

### `alembic/`
- 数据库迁移版本管理

## 本地开发

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env
# 编辑 .env：
#   - DATABASE_URL 指向你的 PostgreSQL
#   - SECRET_KEY 用 python -c "import secrets; print(secrets.token_hex(32))" 生成
#   - RESEND_API_KEY 留空则禁用邮件功能

# 跑迁移
alembic upgrade head

# 启动
uvicorn app.main:app --reload --port 8080
```

## Docker 部署

```bash
docker-compose up --build -d
```

会拉起：
- `db` — PostgreSQL 16
- `redis` — Redis 7
- `api` — FastAPI + Uvicorn
- `nginx` — 反向代理

数据卷：`./data/postgres` 和 `./data/redis`

## 测试

```bash
pytest                 # 所有测试
pytest tests/test_auth  # 单模块
pytest -v              # 详细输出
```

测试覆盖：
- `test_01_authentication.py` — 注册 / 登录 / 刷新 / 登出
- `test_02_teams.py` — 团队 CRUD
- `test_03_invitations.py` — 邀请流
- `test_04_checkins.py` — 打卡
- `test_05_dashboard.py` — 仪表盘
- `test_06_recognition.py` — 团队认可
- `test_07_flow_ritual.py` — 心流仪式
- `test_08_culture.py` — 团队文化
- `test_09_personal.py` — 个人功能
- `test_10_forum.py` — 论坛
- `test_dashboard_api.py` / `test_password_reset.py` / `test_user_and_team_features.py`

## 目录结构

```
backend/
├─ app/
│  ├─ main.py                # FastAPI 入口
│  ├─ core/                  # 配置 / DB / 模型 / 安全 / CRUD
│  ├─ routes/                # REST 路由
│  └─ tests/                 # Pytest 套件
├─ alembic/                  # DB 迁移版本
├─ alembic.ini
├─ docker-compose.yml
├─ Dockerfile
├─ nginx.conf
├─ openapi_v3.yaml           # 自动生成的 OpenAPI 规范
├─ requirements.txt
└─ .env.example
```
