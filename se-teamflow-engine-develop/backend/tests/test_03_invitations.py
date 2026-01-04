import pytest
from httpx import AsyncClient
from typing import Dict, Any

pytestmark = pytest.mark.asyncio

@pytest.mark.run(order=3)
class TestInvitations:

    async def test_owner_can_invite_user(
        self,
        created_team: Dict[str, Any],
        owner_auth_data: Dict[str, Any],
        user2_auth_data: Dict[str, Any]
    ):
        """
        测试团队所有者 (test1) 可以成功发送邀请给 test2。
        """
        owner_client = owner_auth_data["client"]
        team_id = created_team["team_id"]
        user2_email = user2_auth_data["user_info"]["email"]
        
        payload = {"email_username": user2_email}
        response = await owner_client.post(
            f"/teams/{team_id}/invitations/", 
            json=payload
        )
        
        assert response.status_code == 201
        assert "message" in response.json()

    async def test_user_can_see_pending_invitations(
        self,
        created_team: Dict[str, Any],
        owner_auth_data: Dict[str, Any],
        user2_auth_data: Dict[str, Any]
    ):
        """
        测试 test2 可以在 /me/all_invite/ 中看到 test1 的邀请。
        """
        owner_client = owner_auth_data["client"]
        user2_client = user2_auth_data["client"]
        team_id = created_team["team_id"]
        user2_email = user2_auth_data["user_info"]["email"]
        
        # 1. 所有者发送邀请
        await owner_client.post(
            f"/teams/{team_id}/invitations/", 
            json={"email_username": user2_email}
        )
        
        # 2. 用户2 检查邀请列表
        response = await user2_client.get("/me/all_invite/")
        assert response.status_code == 200
        
        invites_list = response.json()
        assert isinstance(invites_list, list)
        assert len(invites_list) > 0
        
        # 检查邀请是否在列表中
        assert any(invite["team_id"] == team_id for invite in invites_list)

    async def test_user_can_accept_invitation(self, team_with_member: Dict[str, Any]):
        """
        测试接受邀请的完整流程。
        `team_with_member` fixture 已经处理了 邀请 和 接受 的所有步骤。
        如果 fixture 成功运行，这个测试就自动通过了。
        我们只需验证成员确实在团队中。
        """
        owner_client = team_with_member["owner_client"]
        team_id = team_with_member["team_id"]
        member_id = team_with_member["member_info"]["id"]
        
        response = await owner_client.get(f"/teams/{team_id}/members/")
        assert response.status_code == 200
        
        members_data = response.json()
        assert "members" in members_data
        
        # 检查 test2 是否在成员列表中
        assert any(member["id"] == member_id for member in members_data["members"])

    async def test_user_can_decline_invitation(
        self,
        created_team: Dict[str, Any],
        owner_auth_data: Dict[str, Any],
        user2_auth_data: Dict[str, Any]
    ):
        """
        测试用户可以拒绝一个邀请。
        """
        owner_client = owner_auth_data["client"]
        user2_client = user2_auth_data["client"]
        team_id = created_team["team_id"]
        user2_email = user2_auth_data["user_info"]["email"]
        
        # 1. 所有者发送邀请
        await owner_client.post(
            f"/teams/{team_id}/invitations/", 
            json={"email_username": user2_email}
        )
        
        # 2. 用户2 获取邀请码
        invites_resp = await user2_client.get("/me/all_invite/")
        invite = next(i for i in invites_resp.json() if i["team_id"] == team_id)
        invite_code = invite["invite_code"]
        
        # 3. 用户2 拒绝邀请
        decline_resp = await user2_client.request(
            "DELETE",
            "/teams/invitations/decline/",
            json={"code": invite_code}
        )
        assert decline_resp.status_code == 200
        
        # 4. 验证：用户2 不在团队成员列表中
        members_resp = await owner_client.get(f"/teams/{team_id}/members/")
        member_id = user2_auth_data["user_info"]["id"]
        assert not any(
            m["id"] == member_id for m in members_resp.json()["members"]
        )