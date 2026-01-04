import pytest
from httpx import AsyncClient
from typing import Dict, Any

# 假设 BASE_URL 在 conftest.py 中定义并被 httpx.AsyncClient 使用
from faker import Faker 

pytestmark = pytest.mark.asyncio

@pytest.mark.run(order=2) # 标记为第二组运行
class TestTeams:

    async def test_create_team_unauthenticated(self, api_client: AsyncClient):
        """
        测试未认证用户无法创建团队。
        """
        response = await api_client.post("/teams/", json={"name": "No Auth Team"})
        assert response.status_code in [401, 403, 422]

    async def test_get_my_teams_list(self, created_team: Dict[str, Any]):
        """
        测试 GET /teams/ 能否列出用户（所有者）加入的团队。
        `created_team` 夹具会自动创建并清理一个团队。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        response = await client.get("/teams/")
        
        assert response.status_code == 200
        teams_list = response.json()
        assert isinstance(teams_list, list)
        
        # 检查我们刚创建的团队是否在列表中
        assert any(team["id"] == team_id for team in teams_list)

    async def test_get_team_members(self, created_team: Dict[str, Any]):
        """
        测试获取团队成员列表，应包含所有者。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        owner_id = created_team["owner_id"]
        
        response = await client.get(f"/teams/{team_id}/members/")
        
        assert response.status_code == 200
        data = response.json()
        assert "owner" in data
        assert "members" in data
        assert data["owner"]["id"] == owner_id
        assert isinstance(data["members"], list)

    async def test_modify_team_name_by_owner(self, created_team: Dict[str, Any], fake: Faker):
        """
        测试团队所有者可以修改团队名称。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        new_name = f"modified-name-{fake.uuid4()}"
        
        response = await client.put(
            f"/teams/{team_id}/modify/", 
            json={"name": new_name}
        )
        assert response.status_code == 200
        
        # 验证：再次获取团队列表，检查名称是否已更新
        get_response = await client.get("/teams/")
        teams_list = get_response.json()
        modified_team = next((t for t in teams_list if t["id"] == team_id), None)
        
        assert modified_team is not None
        assert modified_team["name"] == new_name

    async def test_delete_team_by_owner(self, owner_auth_data: Dict[str, Any], fake: Faker):
        """
        显式测试团队删除功能（不使用 created_team 夹具）。
        """
        client = owner_auth_data["client"]
        
        # 1. (Setup) 手动创建一个团队
        team_name = f"delete-test-{fake.uuid4()}"
        create_response = await client.post("/teams/", json={"name": team_name})
        assert create_response.status_code == 201
        
        # 2. (Setup) 获取ID
        get_response = await client.get("/teams/")
        team_id = next(t["id"] for t in get_response.json() if t["name"] == team_name)
        
        # 3. (Test) 执行删除
        delete_response = await client.delete(f"/teams/{team_id}/delete/")
        assert delete_response.status_code == 200
        
        # 4. (Verify) 验证团队是否已消失
        get_response_after_delete = await client.get("/teams/")
        assert not any(t["id"] == team_id for t in get_response_after_delete.json())

    async def test_owner_cannot_leave_team(self, created_team: Dict[str, Any]):
        """
        测试所有者（管理员）不能使用“退出群组”API。
        (根据您的API文档: "退出群组 (管理員不能使用)")
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        response = await client.delete(f"/teams/{team_id}/leave/")
        
        # 假设此业务规则错误返回 400 Bad Request
        assert response.status_code == 403
        
    # --- 多用户测试 ---
    # 诸如 test_kick_member, test_modify_owner, 
    # test_non_owner_leaves_team, test_non_owner_cannot_delete_team
    # 的测试需要第二个和第三个已认证的用户。
    # 将在 test_03_invitations.py 中实现它们。

    async def test_member_can_leave_team(self, team_with_member: Dict[str, Any]):
        """
        测试普通成员 (test2) 可以成功退出团队。
        """
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        member_id = team_with_member["member_info"]["id"]
        
        # 1. 成员 (test2) 退出
        response = await member_client.delete(f"/teams/{team_id}/leave/")
        assert response.status_code == 200
        
        # 2. 验证：所有者 (test1) 检查成员列表，test2 应该已消失
        owner_client = team_with_member["owner_client"]
        members_resp = await owner_client.get(f"/teams/{team_id}/members/")
        assert not any(
            m["id"] == member_id for m in members_resp.json()["members"]
        )

    async def test_owner_can_kick_member(self, team_with_member: Dict[str, Any]):
        """
        测试所有者 (test1) 可以踢出成员 (test2)。
        """
        owner_client = team_with_member["owner_client"]
        team_id = team_with_member["team_id"]
        member_id = team_with_member["member_info"]["id"]
        
        # 1. 所有者 (test1) 踢出成员 (test2)
        kick_payload = {"id": member_id}
        response = await owner_client.request(
            "DELETE",
            f"/teams/{team_id}/kick/",
            json=kick_payload
        )
        assert response.status_code == 200
        
        # 2. 验证：成员 (test2) 应该已从列表中消失
        members_resp = await owner_client.get(f"/teams/{team_id}/members/")
        assert not any(
            m["id"] == member_id for m in members_resp.json()["members"]
        )

    async def test_member_cannot_delete_team(self, team_with_member: Dict[str, Any]):
        """
        测试普通成员 (test2) 无法解散团队。
        """
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        
        response = await member_client.delete(f"/teams/{team_id}/delete/")
        # 假设权限不足返回 403 Forbidden
        assert response.status_code == 403

    async def test_member_cannot_modify_team_name(self, team_with_member: Dict[str, Any]):
        """
        测试普通成员 (test2) 无法修改团队名称。
        """
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        
        response = await member_client.put(
            f"/teams/{team_id}/modify/", 
            json={"name": "New Name By Member"}
        )
        assert response.status_code == 403

    async def test_owner_can_transfer_ownership(self, team_with_member: Dict[str, Any]):
        """
        测试所有者 (test1) 可以将所有权转让给成员 (test2)。
        """
        owner_client = team_with_member["owner_client"]
        team_id = team_with_member["team_id"]
        member_id = team_with_member["member_info"]["id"]
        
        # 1. 所有者 (test1) 转让所有权
        transfer_payload = {"id": member_id}
        response = await owner_client.put(
            f"/teams/{team_id}/modify_owner/", 
            json=transfer_payload
        )
        assert response.status_code == 200
        
        # 2. 验证：获取成员列表，新的所有者应该是 test2
        members_resp = await owner_client.get(f"/teams/{team_id}/members/")
        assert members_resp.status_code == 200
        
        new_owner = members_resp.json()["owner"]
        assert new_owner["id"] == member_id