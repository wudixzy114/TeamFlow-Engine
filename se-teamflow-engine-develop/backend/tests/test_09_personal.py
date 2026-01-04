import pytest
from httpx import AsyncClient
from typing import Dict, Any
import datetime
import io

pytestmark = pytest.mark.asyncio

@pytest.mark.run(order=9)
class TestPersonalEndpoints:

    async def test_get_my_invitations_after_invite(
        self,
        created_team: Dict[str, Any],
        owner_auth_data: Dict[str, Any],
        user2_auth_data: Dict[str, Any]
    ):
        """
        测试 test2 在被邀请后，能否在 /me/all_invite/ 列表中看到该邀请。
        """
        owner_client = owner_auth_data["client"]
        user2_client = user2_auth_data["client"]
        team_id = created_team["team_id"]
        user2_email = user2_auth_data["user_info"]["email"]
        
        # 1. (Setup) 所有者发送邀请
        await owner_client.post(
            f"/teams/{team_id}/invitations/", 
            json={"email_username": user2_email}
        )
        
        # 2. (Test) 用户2 检查邀请列表
        response = await user2_client.get("/me/all_invite/")
        assert response.status_code == 200
        
        invites_list = response.json()
        assert isinstance(invites_list, list)
        assert any(invite["team_id"] == team_id for invite in invites_list)

    async def test_get_and_delete_message(self, team_with_member: Dict[str, Any]):
        """
        测试获取和删除通知消息。
        (假设: 接受邀请会为 *所有者* 生成一条通知)
        """
        owner_client = team_with_member["owner_client"]
        
        # 1. (Test) 获取通知
        # `team_with_member` 已经触发了 "test2" 加入团队的事件
        get_resp = await owner_client.get("/me/message/")
        assert get_resp.status_code == 200
        
        messages = get_resp.json()
        assert isinstance(messages, list)
        
        # 假设至少有一条通知
        assert len(messages) > 0
        message_to_delete = messages[0]
        message_id = message_to_delete["id"]
        
        # 2. (Test) 删除通知
        delete_resp = await owner_client.request(
            "DELETE",
            f"/me/message/delete/",
            json={"message_id": message_id}
        )
        assert delete_resp.status_code == 200
        
        # 3. (Verify) 验证删除
        get_resp_after = await owner_client.get("/me/message/")
        assert not any(m["id"] == message_id for m in get_resp_after.json())

    async def test_get_weekly_digest(self, owner_auth_data: Dict[str, Any]):
        """
        测试获取个人周报。
        """
        client = owner_auth_data["client"]
        
        # 获取今天的日期 (YYYY-MM-DD)
        today_str = datetime.date.today().isoformat()
        
        response = await client.get(f"/me/weekly-digest/?date={today_str}")
        assert response.status_code == 200
        
        data = response.json()
        # 验证 API 文档中的关键字段
        assert "week_range" in data
        assert "total_focus_hours" in data
        assert "kudos_received" in data
        assert "mindset_trend" in data
        
    async def test_post_text_message_and_list(self, created_team: Dict[str, Any]):
        """
        測試流程：
        1. 發送純文字訊息 (POST)
        2. 獲取訊息列表 (GET) 驗證是否包含剛剛發送的內容
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        content = "Hello, TeamFlow!"
        tag = "text"

        # 1. 發送文字訊息
        post_payload = {"content": content, "tag": tag}
        post_resp = await client.post(
            f"/teams/{team_id}/chat/post_messages/",
            json=post_payload
        )
        assert post_resp.status_code == 200
        assert post_resp.json() == {"message": "Message posted successfully."}

        # 2. 獲取列表驗證
        get_resp = await client.get(f"/teams/{team_id}/chat/messages/")
        assert get_resp.status_code == 200
        
        messages = get_resp.json()
        assert isinstance(messages, list)
        assert len(messages) > 0
        
        # 驗證最新的一條消息內容
        latest_msg = messages[0]
        assert latest_msg["content"] == content
        assert latest_msg["tag"] == tag
        assert "id" in latest_msg

    async def test_post_file_message(self, created_team: Dict[str, Any]):
        """
        測試流程：
        1. 模擬檔案上傳 (POST multipart/form-data)
        2. 驗證伺服器回傳成功
        3. 獲取列表驗證 tag 和路徑格式
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        # 模擬一個圖片檔案
        file_content = b"fake_image_bytes_content"
        filename = "test_image.jpg"
        
        # 構造 Multipart 請求
        # files 格式: {'欄位名': ('檔名', 內容, 'MIME類型')}
        files = {
            "file": (filename, io.BytesIO(file_content), "image/jpeg")
        }
        # 其他 Form 欄位 (tag)
        data = {"tag": "image"}

        # 1. 發送檔案
        post_resp = await client.post(
            f"/teams/{team_id}/chat/post_file/",
            files=files,
            data=data
        )
        assert post_resp.status_code == 200
        assert post_resp.json() == {"message": "File posted successfully."}

        # 2. 獲取列表驗證
        get_resp = await client.get(f"/teams/{team_id}/chat/messages/")
        assert get_resp.status_code == 200
        
        messages = get_resp.json()
        latest_msg = messages[0] # 因為是按時間倒序，最新的在第一個
        
        assert latest_msg["tag"] == "image"
        # 驗證 content 是一個路徑 (包含 static/uploads)
        assert "/static/uploads/" in latest_msg["content"]
        assert filename in latest_msg["content"]

    async def test_delete_own_message(self, created_team: Dict[str, Any]):
        """
        測試流程：
        1. 發送一條訊息
        2. 獲取該訊息的 ID
        3. 刪除該訊息 (DELETE)
        4. 再次獲取列表，確認訊息已消失
        """
        client = created_team["client"]
        team_id = created_team["team_id"]

        # 1. 準備數據：先發送一條要刪除的訊息
        await client.post(
            f"/teams/{team_id}/chat/post_messages/",
            json={"content": "To be deleted", "tag": "text"}
        )

        # 2. 獲取 ID：因為 POST 只回傳 success message，必須從 GET 列表拿 ID
        get_resp = await client.get(f"/teams/{team_id}/chat/messages/")
        messages = get_resp.json()
        target_msg = messages[0]
        msg_id = target_msg["id"]

        # 3. 執行刪除
        # 注意：使用 request("DELETE", ..., json=...) 因為標準 delete() 方法在某些版本不支援 json body
        delete_resp = await client.request(
            "DELETE",
            f"/teams/{team_id}/chat/delete_messages/",
            json={"id": msg_id}
        )
        assert delete_resp.status_code == 200
        assert delete_resp.json() == {"message": "Message deleted successfully."}

        # 4. 驗證刪除結果
        get_resp_after = await client.get(f"/teams/{team_id}/chat/messages/")
        messages_after = get_resp_after.json()
        
        # 確保剛剛那個 ID 不在列表中
        ids_after = [m["id"] for m in messages_after]
        assert msg_id not in ids_after