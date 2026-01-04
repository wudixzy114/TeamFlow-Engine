import pytest
from httpx import AsyncClient
from typing import Dict, Any
from datetime import date, datetime

pytestmark = pytest.mark.asyncio

@pytest.mark.run(order=6)
class TestRecognition:

    # --- 辅助函数 ---
    async def _create_highlight(self, client: AsyncClient, team_id: str, content: str) -> Dict[str, Any]:
        """一个辅助函数，用于创建一个高光并返回其 ID。"""
        post_resp = await client.post(
            f"/teams/{team_id}/highlights/", 
            json={"content": content}
        )
        assert post_resp.status_code == 201
        
        # 获取 ID
        get_resp = await client.get(f"/teams/{team_id}/highlights/")
        highlight = next((h for h in get_resp.json() if h["content"] == content), None)
        assert highlight is not None
        return highlight

    # --- 高光时刻 (Highlights) 测试 ---

    async def test_create_get_and_delete_highlight(self, created_team: Dict[str, Any]):
        """
        测试高光时刻的完整生命周期：POST -> GET -> DELETE。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        content = "我完成了一个重要功能！"
        
        # 1. 创建
        highlight = await self._create_highlight(client, team_id, content)
        highlight_id = highlight["id"]
        
        # 2. GET
        get_resp = await client.get(f"/teams/{team_id}/highlights/")
        assert get_resp.status_code == 200
        assert any(h["id"] == highlight_id for h in get_resp.json())
        
        # 3. Delete
        delete_resp = await client.request(
            "DELETE",
            f"/teams/{team_id}/highlights/delete/",
            json={"id": highlight_id}
        )
        assert delete_resp.status_code == 200
        
        # 4. 验证已删除
        get_resp_after = await client.get(f"/teams/{team_id}/highlights/")
        assert not any(h["id"] == highlight_id for h in get_resp_after.json())

    async def test_modify_highlight(self, created_team: Dict[str, Any]):
        """
        测试修改一个已发布的高光时刻。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        # 1. 创建
        highlight = await self._create_highlight(client, team_id, "原始内容")
        highlight_id = highlight["id"]
        
        # 2. 修改
        new_content = "已修改的内容"
        modify_resp = await client.put(
            f"/teams/{team_id}/highlights/modify/",
            json={"id": highlight_id, "content": new_content}
        )
        assert modify_resp.status_code == 200
        
        # 3. 验证修改
        get_resp = await client.get(f"/teams/{team_id}/highlights/")
        modified_highlight = next(h for h in get_resp.json() if h["id"] == highlight_id)
        assert modified_highlight["content"] == new_content

    async def test_user_can_like_and_dislike_highlight(self, team_with_member: Dict[str, Any]):
        """
        测试多用户点赞/取消点赞功能。
        test1 (所有者) 发布, test2 (成员) 点赞和取消点赞。
        """
        owner_client = team_with_member["owner_client"]
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        
        # 1.  test1 发布
        highlight = await self._create_highlight(owner_client, team_id, "一个值得点赞的高光")
        highlight_id = highlight["id"]
        
        # 2. test2 点赞
        like_resp = await member_client.put(f"/highlights/{highlight_id}/like/")
        assert like_resp.status_code == 200
        
        # 3. 验证点赞数
        get_resp_1 = await owner_client.get(f"/teams/{team_id}/highlights/")
        liked_highlight = next(h for h in get_resp_1.json() if h["id"] == highlight_id)
        assert liked_highlight["likes_count"] == 1
        assert liked_highlight["liked_by_current_user"] == False # test1 未点赞
        
        # 4. test2 取消点赞
        dislike_resp = await member_client.delete(f"/highlights/{highlight_id}/dislike/")
        assert dislike_resp.status_code == 200 # 根据 API 文档
        
        # 5. 验证点赞数已归零
        get_resp_2 = await owner_client.get(f"/teams/{team_id}/highlights/")
        unliked_highlight = next(h for h in get_resp_2.json() if h["id"] == highlight_id)
        assert unliked_highlight["likes_count"] == 0

    # --- Kudos 能量卡测试 ---

    async def test_send_and_receive_kudos(self, team_with_member: Dict[str, Any]):
        """
        测试 test1 (所有者) 向 test2 (成员) 发送 Kudos,
        然后 test2 检查 /me/kudos/received/。
        """
        owner_client = team_with_member["owner_client"]
        owner_id = team_with_member["owner_info"]["id"]
        member_client = team_with_member["member_client"]
        member_id = team_with_member["member_info"]["id"]
        team_id = team_with_member["team_id"]
        
        # 1. test1 发送 Kudos 给 test2
        kudos_payload = {
            "receiver_id": member_id,
            "card_type": "最佳战友卡",
            "message": "干得漂亮！"
        }
        send_resp = await owner_client.post(
            f"/teams/{team_id}/kudos/",
            json=kudos_payload
        )
        assert send_resp.status_code == 201
        
        # 2. test2 检查收到的 Kudos
        get_resp = await member_client.get("/me/kudos/received/")
        assert get_resp.status_code == 200
        
        kudos_list = get_resp.json()
        assert isinstance(kudos_list, list)
        assert len(kudos_list) >= 1
        
        # 3. 验证收到的 Kudos 内容
        received_kudos = kudos_list[0] # 假设是最新的一条
        assert received_kudos["message"] == "干得漂亮！"
        assert received_kudos["card_type"] == "最佳战友卡"
        assert received_kudos["sender"]["id"] == owner_id
        assert received_kudos["receiver"]["id"] == member_id
    # --- 評論功能 (Comments) 測試 (新增部分) ---

    async def test_create_and_get_comment(self, created_team: Dict[str, Any]):
        """
        測試 1: 為高光時刻創建評論 (POST) 並獲取列表 (GET)。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        # 1. 先創建一個 Highlight
        highlight = await self._create_highlight(client, team_id, "準備被評論的高光")
        highlight_id = highlight["id"]
        
        # 2. 創建評論 (修正路徑：加上 /highlights 前綴)
        comment_content = "這是一條測試評論"
        create_resp = await client.post(
            f"/highlights/{highlight_id}/comments/",
            json={"content": comment_content}
        )
        assert create_resp.status_code == 201
        
        # 3. 獲取所有評論 (修正路徑：加上 /highlights 前綴)
        get_resp = await client.get(f"/highlights/{highlight_id}/all_comments/")
        assert get_resp.status_code == 200
        comments = get_resp.json()
        
        # 4. 驗證
        assert len(comments) == 1
        assert comments[0]["content"] == comment_content
        assert comments[0]["highlight_id"] == highlight_id

    async def test_modify_comment(self, created_team: Dict[str, Any]):
        """
        測試 2: 修改已存在的評論 (PUT)。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        # 1. 準備數據
        highlight = await self._create_highlight(client, team_id, "準備被修改評論的高光")
        highlight_id = highlight["id"]
        
        # 先創建一條
        await client.post(
            f"/highlights/{highlight_id}/comments/",
            json={"content": "原始評論"}
        )
        
        # 獲取評論 ID
        comments = (await client.get(f"/highlights/{highlight_id}/all_comments/")).json()
        comment_id = comments[0]["id"]
        
        # 2. 修改評論 (修正路徑：加上 /highlights 前綴)
        new_content = "修改後的評論內容"
        modify_payload = {
            "id": comment_id,
            "content": new_content
        }
        
        modify_resp = await client.put(
            f"/highlights/{highlight_id}/comments/modify/",
            json=modify_payload
        )
        assert modify_resp.status_code == 200
        
        # 3. 驗證
        get_resp = await client.get(f"/highlights/{highlight_id}/all_comments/")
        modified_comment = get_resp.json()[0]
        assert modified_comment["content"] == new_content

    async def test_delete_comment(self, created_team: Dict[str, Any]):
        """
        測試 3: 刪除評論 (DELETE)。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        # 1. 準備數據
        highlight = await self._create_highlight(client, team_id, "準備刪除評論的高光")
        highlight_id = highlight["id"]
        
        await client.post(f"/highlights/{highlight_id}/comments/", json={"content": "即將消失"})
        
        comments = (await client.get(f"/highlights/{highlight_id}/all_comments/")).json()
        comment_id = comments[0]["id"]
        
        # 2. 刪除評論 (修正路徑：加上 /highlights 前綴)
        delete_resp = await client.request(
            "DELETE",
            f"/highlights/{highlight_id}/comments/delete/",
            json={"id": comment_id}
        )
        assert delete_resp.status_code == 200
        
        # 3. 驗證列表為空
        get_resp = await client.get(f"/highlights/{highlight_id}/all_comments/")
        assert len(get_resp.json()) == 0

    async def test_member_can_comment_on_owner_highlight(self, team_with_member: Dict[str, Any]):
        """
        測試 4: 跨用戶互動 - 成員 (member) 評論 隊長 (owner) 的高光。
        """
        owner_client = team_with_member["owner_client"]
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        
        # 1. Owner 發布
        highlight = await self._create_highlight(owner_client, team_id, "我是隊長")
        highlight_id = highlight["id"]
        
        # 2. Member 評論 (修正路徑)
        reply_content = "隊長好！我是成員"
        reply_resp = await member_client.post(
            f"/highlights/{highlight_id}/comments/",
            json={"content": reply_content}
        )
        assert reply_resp.status_code == 201
        
        # 3. Owner 查看
        get_resp = await owner_client.get(f"/highlights/{highlight_id}/all_comments/")
        comments = get_resp.json()
        
        assert len(comments) == 1
        assert comments[0]["content"] == reply_content
        assert comments[0]["user_id"] == team_with_member["member_info"]["id"]