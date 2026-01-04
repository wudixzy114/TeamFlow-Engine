# 测试命令
# 运行所有测试 ( 需要先启动docker )
docker compose exec backend pytest -v -s
# 运行特定测试文件
docker compose exec backend pytest -v -s tests/test_04_authentication.py

以下是每个测试文件所覆盖的功能模块和主要测试的 API 接口：

模块 1: 认证与用户管理 (test_01_authentication.py)
- 内容: 测试用户注册、登录、登出、获取个人信息、修改个人资料、刷新 Token 和忘记密码。
- 主要接口:
    POST /auth/register/
    POST /auth/login/
    POST /auth/logout/
    GET /auth/me/
    PUT /auth/modify_selfinfo/
    POST /auth/token/refresh/
    POST /auth/forgot-password/

模块 2: 团队管理 (test_02_teams.py)
- 内容: 测试团队的完整生命周期（CRUD），以及复杂的成员管理和权限控制（如踢人、转让所有权）。
- 主要接口:
    POST /teams/
    GET /teams/
    GET /teams/{team_id}/members/
    PUT /teams/{team_id}/modify/
    DELETE /teams/{team_id}/delete/
    DELETE /teams/{team_id}/leave/
    DELETE /teams/{team_id}/kick/
    PUT /teams/{team_id}/modify_owner/

模块 3: 团队邀请 (test_03_invitations.py)
- 内容: 专项测试团队邀请的完整工作流程，包括发送、查看、接受和拒绝邀请。
- 主要接口:
    POST /teams/{team_id}/invitations/
    GET /me/all_invite/
    POST /teams/invitations/accept/
    DELETE /teams/invitations/decline/

模块 4: 每日签到 (test_04_checkins.py)
- 内容: 测试团队成员的核心功能：每日状态签到，包括防止重复签到。
- 主要接口:
    POST /teams/{team_id}/checkins/
    GET /teams/{team_id}/checkins/today/

模块 5: 仪表盘 (test_05_dashboard.py)
- 内容: 测试数据聚合和可视化的仪表盘端点。重点测试签到和专注数据能否被正确聚合。
- 主要接口:
    GET /dashboard/teams/{team_id}/compass/
    GET /dashboard/teams/{team_id}/focus-time/
    GET /dashboard/teams/{team_id}/insights/

模块 6: 认可与高光 (test_06_recognition.py)
- 内容: 测试“高光时刻”(Highlights) 和 "Kudos 能量卡" 功能。包括 CRUD、点赞/取消点赞以及发送/接收 Kudos。
- 主要接口:
    POST /teams/{team_id}/highlights/
    GET /teams/{team_id}/highlights/
    PUT /teams/{team_id}/highlights/modify/
    DELETE /teams/{team_id}/highlights/delete/
    PUT /highlights/{highlight_id}/like/
    DELETE /highlights/{highlight_id}/dislike/
    POST /teams/{team_id}/kudos/
    GET /me/kudos/received/

模块 7: 心流仪式 (test_07_flow_ritual.py)
- 内容: 测试专注会话（Flow Session）的 CRUD 操作，并集成验证数据是否流入仪表盘。
- 主要接口:
    POST /teams/{team_id}/flow-sessions/
    GET /teams/{team_id}/flow-sessions/
    PUT /teams/{team_id}/flow-sessions/modify/
    DELETE /teams/{team_id}/flow-sessions/delete/

模块 8: 团队文化 (test_08_culture.py)
- 内容: 测试团队公约 (Charter) 和团队技能树 (Skill Tree) 功能，包括所有者的权限验证。
- 主要接口:
    GET /teams/{team_id}/charter/
    PUT /teams/{team_id}/charter/
    DELETE /teams/{team_id}/delete-charter/
    GET /teams/{team_id}/skill-tree/

模块 9: 个人中心 (test_09_personal.py)
- 内容: 测试所有剩余的、挂在 /me/ 路径下的个人端点，如邀请列表、消息通知、个人技能树和周报。
- 主要接口:
    GET /me/all_invite/
    GET /me/message/
    DELETE /me/message/delete/
    GET /me/skill_tree/
    PUT /me/skill_tree/
    GET /me/weekly-digest/