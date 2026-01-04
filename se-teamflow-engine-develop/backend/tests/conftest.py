import pytest
import pytest_asyncio  
import asyncio
import httpx         
from faker import Faker
from typing import Generator, Dict, Any

# --- 导入数据库和模型 ---
from app.core.database import AsyncSessionLocal
from app.core.models import User
from app.core.security import get_password_hash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi.concurrency import run_in_threadpool 

# --- 常量与配置 ---
BASE_URL = "http://nginx/api/v1"

TEST_USER_EMAIL = "test1@gmail.com"
TEST_USER_PASSWORD = "test1"

# --- Faker 实例 ---
_fake_instance = Faker()

@pytest.fixture(scope="session")
def fake() -> Faker:
    """提供一个会话级别的 Faker 实例。"""
    return _fake_instance

# --- 为 pytest-asyncio 配置事件循环 ---
@pytest.fixture(scope="session")
def event_loop():
    """为每个测试会话创建一个事件循环实例。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# --- 自动预植入用户 ---
@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_database(event_loop): # 依赖于事件循环
    """
    在所有测试开始前运行一次，自动预植入用户。
    'autouse=True' 意味着所有测试都会自动使用它，无需手动请求。
    """
    print("\n[Setup] 正在使用测试用户预植入数据库...")
    async with AsyncSessionLocal() as db:
        users_to_create = [
            {"username": "test1", "email": "test1@gmail.com", "password": "test1"}, 
            {"username": "test2", "email": "test2@gmail.com", "password": "test2"}, 
            {"username": "test3", "email": "test3@gmail.com", "password": "test3"}, 
        ]

        for u in users_to_create:
            query = select(User).where(User.email == u["email"]) 
            result = await db.execute(query)
            if not result.scalars().first():
                # 在线程池中运行同步的哈希函数
                hashed_password = await run_in_threadpool(get_password_hash, u["password"]) #

                user = User(
                    username=u["username"],
                    email=u["email"],
                    hashed_password=hashed_password, #
                )
                db.add(user) #
                try:
                    await db.commit() #
                    print(f"✅ 已创建用户: {u['username']}") #
                except IntegrityError: #
                    await db.rollback() #
                    print(f"⚠️  已跳过重复用户: {u['email']}") #
    
    print("[Setup] 数据库预植入完成。")
    yield
    print("\n[Teardown] 测试会话结束。")


# --- 基础 HTTP 客户端 Fixture ---

@pytest_asyncio.fixture(scope="function")
async def api_client() -> httpx.AsyncClient:
    """
    提供一个 *未认证* 的、干净的异步 httpx.AsyncClient。
    用于测试公共端点或注册流程。
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        client.headers["User-Agent"] = "TeamFlow-Async-Test-Suite/1.0"
        yield client
        
# --- 核心认证 Fixtures ---
@pytest_asyncio.fixture(scope="function")
async def owner_auth_data(initialize_database) -> Dict[str, Any]:
    """
    为 'test1' (所有者) 提供一个 *独立的、已认证的* 客户端会话。
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. 登录
        login_payload = {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        login_response = await client.post("/auth/login/", json=login_payload)

        if login_response.status_code != 200:
            pytest.fail(f"无法登录为所有者 (test1): {login_response.text}")

        tokens = login_response.json()
        access_token = tokens.get("access")
        client.headers["Authorization"] = f"Bearer {access_token}"
        
        # 2. 获取用户信息 (增加错误检查)
        me_response = await client.get("/auth/me/")

        # --- 新增的检查 ---
        if me_response.status_code != 200:
            pytest.fail(
                f"登录成功后，使用 token 访问 /auth/me/ 失败。\n"
                f"状态码: {me_response.status_code}\n"
                f"响应: {me_response.text}"
            )
        # --- 检查结束 ---

        user_info = me_response.json()

        # 3. Yield
        yield {
            "client": client,
            "user_info": user_info,
            "token": access_token
        }

@pytest_asyncio.fixture(scope="function")
async def user2_auth_data(initialize_database) -> Dict[str, Any]:
    """
    为 'test2' (潜在成员) 提供一个 *独立的、已认证的* 客户端会话。
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. 登录 'test2'
        login_payload = {"email": "test2@gmail.com", "password": "test2"}
        login_response = await client.post("/auth/login/", json=login_payload)

        if login_response.status_code != 200:
            pytest.fail(f"无法登录为用户2 (test2): {login_response.text}")

        tokens = login_response.json()
        access_token = tokens.get("access")
        client.headers["Authorization"] = f"Bearer {access_token}"

        # 2. 获取用户信息 (增加错误检查)
        me_response = await client.get("/auth/me/")

        # --- 新增的检查 ---
        if me_response.status_code != 200:
            pytest.fail(
                f"用户2登录成功后，使用 token 访问 /auth/me/ 失败。\n"
                f"状态码: {me_response.status_code}\n"
                f"响应: {me_response.text}"
            )
        # --- 检查结束 ---

        user_info = me_response.json()

        # 3. Yield
        yield {
            "client": client,
            "user_info": user_info,
            "token": access_token
        }

# --- 7. 核心资源 Fixtures ---

@pytest_asyncio.fixture(scope="function")
async def created_team(owner_auth_data: Dict[str, Any], fake: Faker) -> Generator[Dict[str, Any], None, None]:
    """
    依赖于 `owner_auth_data` 来创建和清理团队。
    """
    
    client = owner_auth_data["client"]
    owner_id = owner_auth_data["user_info"]["id"]
    team_name = f"e2e-team-{fake.uuid4()}"
    team_id = None
    
    try:
        create_response = await client.post("/teams/", json={"name": team_name})
        assert create_response.status_code == 201, f"创建团队失败: {create_response.text}"
        
        get_teams_response = await client.get("/teams/")
        assert get_teams_response.status_code == 200
        
        teams_list = get_teams_response.json()
        created_team_obj = next((t for t in teams_list if t["name"] == team_name), None)
        assert created_team_obj is not None, f"未能找到刚创建的团队: {team_name}"
        
        team_id = created_team_obj["id"]
        
        print(f"\n[Setup] 已创建团队 '{team_name}' (ID: {team_id})")
        yield {
            "team_id": team_id,
            "team_name": team_name,
            "client": client,      # 这是所有者的客户端
            "owner_id": owner_id
        }
        
    finally:
        if team_id:
            print(f"\n[Teardown] 清理团队 '{team_name}' (ID: {team_id})...")
            await client.delete(f"/teams/{team_id}/delete/")

# --- 高级组合 Fixture ---

@pytest_asyncio.fixture(scope="function")
async def team_with_member(
    created_team: Dict[str, Any],
    owner_auth_data: Dict[str, Any],
    user2_auth_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    提供一个 *已包含一名成员* 的团队。
    它会自动完成 "邀请 -> 接受" 的流程。
    用于测试 踢人、离开、转让所有权 等功能。
    """
    team_id = created_team["team_id"]
    owner_client = owner_auth_data["client"]
    user2_client = user2_auth_data["client"]
    user2_email = user2_auth_data["user_info"]["email"]
    
    # 1. 所有者 (test1) 邀请 用户2 (test2)
    invite_payload = {"email_username": user2_email}
    invite_resp = await owner_client.post(
        f"/teams/{team_id}/invitations/", 
        json=invite_payload
    )
    assert invite_resp.status_code == 201, "所有者邀请失败"
    
    # 2. 用户2 (test2) 获取邀请码
    invites_resp = await user2_client.get("/me/all_invite/")
    assert invites_resp.status_code == 200
    
    invites_list = invites_resp.json()
    invite = next((i for i in invites_list if i["team_id"] == team_id), None)
    assert invite is not None, f"用户2未能找到来自团队 {team_id} 的邀请"
    
    # 3. 用户2 (test2) 接受邀请
    accept_payload = {"code": invite["invite_code"]}
    accept_resp = await user2_client.post(
        "/teams/invitations/accept/", 
        json=accept_payload
    )
    assert accept_resp.status_code == 200, "用户2接受邀请失败"

    print(f"\n[Setup] 用户2 (ID: {user2_auth_data['user_info']['id']}) 已加入团队 {team_id}")
    
    # 4. Yield 完整的设置
    yield {
        "team_id": team_id,
        "owner_client": owner_client,
        "owner_info": owner_auth_data["user_info"],
        "member_client": user2_client,
        "member_info": user2_auth_data["user_info"]
    }
    # 团队的清理由 `created_team` 自动处理

@pytest.fixture(scope="function")
def unique_user_data(fake: Faker) -> Dict[str, str]:
    """
    生成一组用于 *注册新用户* 的唯一随机数据。
    (依赖于 'fake' fixture)
    """
    # 1. 生成符合 API 规则的密码
    base_pass = fake.pystr(min_chars=6, max_chars=10) # 6-10个随机字母/数字
    password = f"aB1{base_pass}" # 确保包含: 小写 'a', 大写 'B', 数字 '1'

    # 2. 生成符合 API 规则的用户名
    username = fake.pystr(min_chars=8, max_chars=12) 

    return {
        "email": f"test-{fake.uuid4()}@example.com",
        "username": username,
        "password": password
    }