import pytest
from httpx import AsyncClient
from typing import Dict, Any
import time 

from faker import Faker 
# (不需要导入 conftest.py, pytest 会自动加载)
# BASE_URL 在 conftest.py 中定义并被 httpx.AsyncClient 使用
TEST_USER_EMAIL = "test1@gmail.com"
TEST_USER_PASSWORD = "test1"
# 标记整个文件中的所有测试为 asyncio
pytestmark = pytest.mark.asyncio

@pytest.mark.run(order=1) # 标记为第一组运行
class TestAuthentication:

    async def test_user_registration_success(self, api_client: AsyncClient, unique_user_data: Dict[str, str]):
        """
        测试新用户能否成功注册。
        假设: 注册后无需立即验证即可登录，或者验证是下一步。
        此测试仅验证注册端点是否返回 201。
        """
        response = await api_client.post("/auth/register/", json=unique_user_data)
        
        assert response.status_code == 201
        assert "message" in response.json()

    async def test_user_registration_duplicate_email(self, api_client: AsyncClient, owner_auth_data: Dict[str, Any]):
        """
        测试使用重复的邮箱（来自预植入的 test1 用户）注册会失败。
        """
        existing_user_email = owner_auth_data["user_info"]["email"]
        
        payload = {
            "email": existing_user_email,
            "username": "duplicate_user",
            "password": "password123"
        }
        
        response = await api_client.post("/auth/register/", json=payload)
        # 假设服务器对重复键返回 400 Bad Request
        assert response.status_code == 400

    async def test_user_login_success(self, api_client: AsyncClient):
        """
        测试预植入的用户 (test1@gmail.com) 能否成功登录。
        不使用 auth_data 夹具，因为我们正在测试登录本身。
        """
        
        payload = {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        response = await api_client.post("/auth/login/", json=payload)
        
        assert response.status_code == 200
        tokens = response.json()
        assert "access" in tokens
        assert "refresh" in tokens

    async def test_user_login_wrong_password(self, api_client: AsyncClient):
        """
        测试使用错误密码登录会失败。
        """
        
        payload = {"email": TEST_USER_EMAIL, "password": "wrong-password"}
        response = await api_client.post("/auth/login/", json=payload)
        
        # 登录失败通常返回 400 (Bad Request) 或 401 (Unauthorized)
        assert response.status_code in [400, 401]

    async def test_get_me_success(self, owner_auth_data: Dict[str, Any]):
        """
        测试 /auth/me/ 能否在认证后正确返回用户信息。
        此测试依赖 `owner_auth_data` 夹具来自动登录。
        """
        client = owner_auth_data["client"]
        response = await client.get("/auth/me/")
        
        assert response.status_code == 200
        user_info = response.json()
        assert user_info["id"] == owner_auth_data["user_info"]["id"]
        assert user_info["email"] == owner_auth_data["user_info"]["email"]

    async def test_get_me_unauthenticated(self, api_client: AsyncClient):
        """
        测试在未认证时访问受保护端点 /auth/me/ 会失败。
        """
        response = await api_client.get("/auth/me/")
        # 401 (Unauthorized) 或 403 (Forbidden) 是标准响应
        assert response.status_code in [401, 403, 422]

    async def test_logout_success(self, api_client: AsyncClient):
            """
            测试 /auth/logout/ 端点。
            流程：登录 -> 获取Token -> 登出该Token -> 使用该Token尝试访问受保护接口(应失败)
            """
            # 1. 手动登录以获取完整的 TokenPair (Access + Refresh)
            # 我们不能用 owner_auth_data，因为那个 fixture 好像没保存 refresh token
            payload = {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
            login_response = await api_client.post("/auth/login/", json=payload)
            assert login_response.status_code == 200
            
            token_pair = login_response.json()
            access_token = token_pair["access"]
            
            # 2. 调用登出接口，传入刚刚获取的 access 和 refresh token
            # 根据你的后端代码，这里需要传入 TokenPair 模型
            logout_response = await api_client.post("/auth/logout/", json=token_pair)
            assert logout_response.status_code == 200
            
            # 3. 验证 Access Token 是否已失效
            # 关键：我们要明确使用刚刚被登出的那个 access_token 来发请求
            verify_headers = {"Authorization": f"Bearer {access_token}"}
            
            me_response = await api_client.get("/auth/me/", headers=verify_headers)
            
            # 4. 断言：应该返回 401 Unauthorized (或 403)
            assert me_response.status_code in [401, 403]
        
    async def test_token_refresh(self, api_client: AsyncClient):
        """
        测试 /auth/token/refresh/ 端点。
        """
        
        # 1. 先登录以获取 refresh token
        payload = {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        login_response = await api_client.post("/auth/login/", json=payload)
        refresh_token = login_response.json().get("refresh")
        assert refresh_token
        
        # 2. 使用 refresh token 获取新的 access token
        refresh_payload = {"refresh": refresh_token}
        refresh_response = await api_client.post("/auth/token/refresh/", json=refresh_payload)
        
        assert refresh_response.status_code == 200
        assert "access" in refresh_response.json()

    async def test_modify_self_info(self, owner_auth_data: Dict[str, Any], fake: Faker):
        """
        测试修改个人信息。
        """
        client = owner_auth_data["client"]
        new_nickname = f"TestNickname {fake.uuid4()}"
        
        payload = {
            "nickname": new_nickname,
            "age": "30",
            "gender": "male",
            "profession": "QA"
        }
        
        # 1. 修改信息
        modify_response = await client.put("/auth/modify_selfinfo/", json=payload)
        assert modify_response.status_code == 200
        
        # 2. 验证信息是否已更新
        me_response = await client.get("/auth/me/")
        assert me_response.status_code == 200
        user_info = me_response.json()
        assert user_info["nickname"] == new_nickname
        assert user_info["age"] == "30"

    async def test_forgot_password_request(self, api_client: AsyncClient):
        """
        测试请求重置密码（发送验证码）。
        我们只能测试请求是否成功，无法测试邮件是否收到。
        """
        
        payload = {"email": TEST_USER_EMAIL}
        response = await api_client.post("/auth/forgot-password/", json=payload)
        
        assert response.status_code == 200
        assert "message" in response.json()
        
        # (测试 /auth/reset-password/ 需要验证码，无法在黑盒测试中完成)