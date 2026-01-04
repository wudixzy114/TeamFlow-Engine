import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# --- 配置 ---
BASE_URL = "http://localhost"
API_PREFIX = "/api/v1"
UNIQUE_ID = int(time.time())

# --- 定义两个不同的用户 ---
OWNER_EMAIL = f"owner{UNIQUE_ID}@example.com"
OWNER_USERNAME = f"owner{UNIQUE_ID}"
OWNER_PASSWORD = "Password123"

MEMBER_EMAIL = f"member{UNIQUE_ID}@example.com"
MEMBER_USERNAME = f"member{UNIQUE_ID}"
MEMBER_PASSWORD = "Password123"

TEAM_NAME = f"E2E Test Team {UNIQUE_ID}"

# --- 数据库连接设置 ---
load_dotenv(dotenv_path='./backend/.env') # 加载 .env 文件
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_tests():
    """主测试函数，按顺序执行一个完整的端到端流程"""
    print("--- 启动纯黑盒端到端仪表盘接口测试 ---")

    # --- 1. 设置阶段 ---
    print("\n[STEP 1] 注册并登录团队所有者 (Owner)")
    owner_headers = register_and_login(OWNER_EMAIL, OWNER_USERNAME, OWNER_PASSWORD)
    if not owner_headers: return

    print("\n[STEP 2] 注册并登录团队成员 (Member)")
    member_headers = register_and_login(MEMBER_EMAIL, MEMBER_USERNAME, MEMBER_PASSWORD)
    # print(member_headers)
    if not member_headers: return

    print(f"\n[STEP 3] Owner 创建团队: {TEAM_NAME}")
    team_id = create_team(owner_headers, TEAM_NAME)
    if not team_id: return

    print(f"\n[STEP 4] Owner 邀请 Member 加入团队")
    invite_member_via_api(owner_headers, team_id, MEMBER_USERNAME)
    
    print(f"\n[STEP 5] Member 获取自己的待处理邀请")
    invitation_code = get_my_invitation_code(member_headers, team_id)
    if not invitation_code: return

    print(f"\n[STEP 6] Member 使用邀请码 '{invitation_code}' 接受邀请")
    accept_invitation(member_headers, invitation_code)

    print(f"\n[STEP 7] Member 为团队提交测试数据")
    create_checkin(member_headers, team_id, {
        "challenge_level": 0.8, "skill_level": 0.9,
        "achievement_text": "完成了核心功能开发", "obstacle_text": "部署环境遇到问题"
    })
    create_checkin(member_headers, team_id, {
        "challenge_level": -0.5, "skill_level": 0.7,
        "achievement_text": "重构了部分代码", "obstacle_text": "第三方API不稳定"
    })
    create_flow_session(member_headers, team_id, {"duration_minutes": 60, "task_description": "核心功能开发"})
    print("  [SUCCESS] 数据准备完成。")

    print("\n[STEP 7.1] 获取团队成员信息")
    members = get_team_members(owner_headers, team_id)
    member_id = next((m["id"] for m in members if m["username"] == MEMBER_USERNAME), None)
    if not member_id:
        print("  [ERROR] 未找到成员 ID。")
        return

    print("\n[STEP 7.2] 发送 Kudos")
    send_kudos(owner_headers, team_id, member_id)

    print("\n[STEP 7.3] 测试团队心流公约")
    test_charter_endpoints(owner_headers, team_id)

    print("\n[STEP 7.4] 测试技能树接口")
    test_skill_tree_endpoint(owner_headers, team_id)
    

    print("\n--- [STEP 8] Member 开始测试 Dashboard Endpoints ---")
    test_compass_endpoint(member_headers, team_id)
    test_focus_time_endpoint(member_headers, team_id)
    test_insights_endpoint(member_headers, team_id)

    print("\n--- 所有测试执行完毕 ---")

# --- API 辅助函数 ---

def register_and_login(email, username, password):
    """注册并登录用户，返回认证头"""
    try:
        reg_res = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register/", json={"email": email, "password": password, "username": username})
        if reg_res.status_code != 201:
            print(f"  [ERROR] 注册失败: {reg_res.status_code} {reg_res.text}")
            return None
        
        login_res = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login/", json={"email": email, "password": password})
        login_res.raise_for_status()
        token = login_res.json()["access"]
        print(f"  [SUCCESS] 用户 '{username}' 登录成功")
        return {"Authorization": f"Bearer {token}"}
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] 注册或登录时发生网络错误: {e}")
        return None

def create_team(headers, team_name):
    """创建团队，返回团队ID"""
    try:
        res = requests.post(f"{BASE_URL}{API_PREFIX}/teams/", headers=headers, json={"name": team_name})
        res.raise_for_status()
        team_id = res.json()["id"]
        print(f"  [SUCCESS] 团队创建成功, ID: {team_id}")
        return team_id
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] 创建团队时发生网络错误: {e}")
        return None

def invite_member_via_api(headers, team_id, member_username):
    """调用API发送邀请"""
    try:
        res = requests.post(f"{BASE_URL}{API_PREFIX}/teams/{team_id}/invitations", headers=headers, json={"email_username": member_username})
        res.raise_for_status()
        print(f"  [SUCCESS] API 调用成功: {res.json().get('message')}")
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] 邀请成员时发生网络错误: {e}")
        raise

def get_my_invitation_code(member_headers, target_team_id):
    """调用 API 获取当前用户收到的邀请，并找到特定团队的邀请码"""
    try:
        res = requests.get(f"{BASE_URL}{API_PREFIX}/me/all_invite", headers=member_headers) # 修正了 URL 路径
        res.raise_for_status()
        invitations = res.json()
        print(f"  [INFO] 找到 {len(invitations)} 条待处理邀请。")
        
        for inv in invitations:
            print(inv)
            if inv.get("team_id") == target_team_id:
                code = inv.get("invite_code")
                if code:
                    print(f"  [SUCCESS] 找到目标团队 '{target_team_id}' 的邀请码: {code}")
                    return code
        
        print(f"  [ERROR] 未在待处理邀请中找到来自团队 '{target_team_id}' 的邀请。")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] 获取待处理邀请时发生网络错误: {e}")
        return None

def accept_invitation(headers, code):
    """接受团队邀请"""
    try:
        res = requests.post(f"{BASE_URL}{API_PREFIX}/teams/invitations/accept", headers=headers, json={"code": code})
        res.raise_for_status()
        print(f"  [SUCCESS] 邀请已接受")
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] 接受邀请时发生网络错误: {e}")
        raise

def create_checkin(headers, team_id, data):
    """提交一次签到"""
    try:
        res = requests.post(f"{BASE_URL}{API_PREFIX}/teams/{team_id}/checkins/", headers=headers, json=data)
        res.raise_for_status()
        print(f"  [SUCCESS] 提交签到数据: challenge={data['challenge_level']}, skill={data['skill_level']}")
    except requests.exceptions.RequestException as e:
        print(f"  [WARN] 提交签到数据失败: {e}")

def create_flow_session(headers, team_id, data):
    """提交一次专注记录"""
    try:
        if "start_time" not in data:
            data["start_time"] = datetime.utcnow().isoformat() + "Z"
        res = requests.post(f"{BASE_URL}{API_PREFIX}/teams/{team_id}/flow-sessions/", headers=headers, json=data)
        res.raise_for_status()
        print(f"  [SUCCESS] 提交专注记录: {data['duration_minutes']} 分钟")
    except requests.exceptions.RequestException as e:
        print(f"  [WARN] 提交专注记录失败: {e}")

def get_team_members(headers, team_id):
    try:
        res = requests.get(
            f"{BASE_URL}{API_PREFIX}/teams/{team_id}/",
            headers=headers
        )
        res.raise_for_status()
        return res.json().get("members", [])
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] 获取团队成员时发生网络错误: {e}")
        return []

def send_kudos(headers, team_id, receiver_id):
    try:
        res = requests.post(
            f"{BASE_URL}{API_PREFIX}/teams/{team_id}/kudos/",
            headers=headers,
            json={
                "receiver_id": receiver_id,
                "card_type": "最佳团队伙伴",
                "message": "感谢你的帮助！"
            }
        )
        res.raise_for_status()
        print("  [SUCCESS] Kudos 发送成功。")
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] 发送 Kudos 时发生网络错误: {e}")

def test_charter_endpoints(owner_headers, team_id):
    try:
        get_res = requests.get(
            f"{BASE_URL}{API_PREFIX}/teams/{team_id}/charter/",
            headers=owner_headers
        )
        get_res.raise_for_status()
        print("  [SUCCESS] Charter 初始获取成功。")

        new_content = f"团队公约更新 {UNIQUE_ID}"
        put_res = requests.put(
            f"{BASE_URL}{API_PREFIX}/teams/{team_id}/charter/",
            headers=owner_headers,
            json={"content": new_content, "last_updated_by": None, "updated_at": get_res.json()["updated_at"]}
        )
        put_res.raise_for_status()
        print("  [SUCCESS] Charter 更新成功。")
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] 测试 Charter 接口时发生网络错误: {e}")

def test_skill_tree_endpoint(headers, team_id):
    try:
        res = requests.get(
            f"{BASE_URL}{API_PREFIX}/teams/{team_id}/skill-tree/",
            headers=headers
        )
        res.raise_for_status()
        print(res.json())
        print("  [SUCCESS] 技能树数据获取成功。")
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] 获取技能树时发生网络错误: {e}")


# --- 测试函数  ---
def test_compass_endpoint(headers, team_id):
    print("\n[TEST] GET /dashboard/teams/{team_id}/compass/")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/dashboard/teams/{team_id}/compass/", headers=headers)
        print(response)
        if response.status_code == 200:
            data = response.json()
            if "distribution" in data and "trend_data" in data:
                print(f"  [SUCCESS] 状态码 200, 响应结构正确。情绪分布: {data['distribution']}")
            else:
                print(f"  [FAIL] 状态码 200, 但响应结构不正确: {data}")
        else:
            print(f"  [FAIL] 期望状态码 200, 实际为 {response.status_code}. 响应: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] 请求失败: {e}")

def test_focus_time_endpoint(headers, team_id):
    print("\n[TEST] GET /dashboard/teams/{team_id}/focus-time/")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/dashboard/teams/{team_id}/focus-time/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "total_hours" in data and data["total_hours"] >= 0:
                print(f"  [SUCCESS] 状态码 200, 响应结构正确。总专注时长: {data['total_hours']} 小时")
            else:
                print(f"  [FAIL] 状态码 200, 但数据不符合预期: {data}")
        else:
            print(f"  [FAIL] 期望状态码 200, 实际为 {response.status_code}. 响应: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] 请求失败: {e}")

def test_insights_endpoint(headers, team_id):
    print("\n[TEST] GET /dashboard/teams/{team_id}/insights/")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/dashboard/teams/{team_id}/insights/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "boosters_wordcloud" in data and "blockers_wordcloud" in data:
                print(f"  [SUCCESS] 状态码 200, 响应结构正确。")
                print(data)
            else:
                print(f"  [FAIL] 状态码 200, 但数据不符合预期: {data}")
        else:
            print(f"  [FAIL] 期望状态码 200, 实际为 {response.status_code}. 响应: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] 请求失败: {e}")

if __name__ == "__main__":
    run_tests()