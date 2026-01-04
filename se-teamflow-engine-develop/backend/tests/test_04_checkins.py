import pytest
from typing import Dict, Any

# 假設你把 router 定義在 main 或 api.v1... 
# 這裡不需要 router 定義，只需要測試 class

pytestmark = pytest.mark.asyncio

@pytest.mark.run(order=4)
class TestCheckins:

    async def test_owner_can_submit_checkin(self, created_team: Dict[str, Any]):
        """
        測試團隊所有者 (test1) 可以成功提交簽到。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        payload = {
            "challenge_level": 0.5,
            "skill_level": 0.8,
            "achievement_text": "完成了測試用例",
            "obstacle_text": "無"
        }
        
        response = await client.post(
            f"/teams/{team_id}/checkins/", 
            json=payload
        )
        
        assert response.status_code == 201
        assert "message" in response.json()

    async def test_member_can_submit_checkin(self, team_with_member: Dict[str, Any]):
        """
        測試團隊成員 (test2) 也可以成功提交簽到。
        """
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        
        payload = {
            "challenge_level": 0.2,
            "skill_level": 0.1,
            "achievement_text": "評審了代碼",
            "obstacle_text": "會議太多"
        }
        
        response = await member_client.post(
            f"/teams/{team_id}/checkins/", 
            json=payload
        )
        
        assert response.status_code == 201

    async def test_can_checkin_multiple_times(self, created_team: Dict[str, Any]):
        """
        測試用戶在同一天內可以重複提交簽到 (取代原本的不能重複測試)。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        # 1. 第一次簽到
        payload1 = {"challenge_level": 0.1, "skill_level": 0.1, "achievement_text": "First"}
        response1 = await client.post(f"/teams/{team_id}/checkins/", json=payload1)
        assert response1.status_code == 201
        
        # 2. 第二次簽到 (現在應該要成功)
        payload2 = {"challenge_level": 0.5, "skill_level": 0.5, "achievement_text": "Second"}
        response2 = await client.post(f"/teams/{team_id}/checkins/", json=payload2)
        
        # 修改斷言：現在應該回傳 201 成功
        assert response2.status_code == 201 

    async def test_get_all_records_verify_order(self, created_team: Dict[str, Any]):
        """
        測試獲取所有紀錄，並驗證排序是否為「最新在最上面」(Desc)。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]

        # 為了確保測試環境乾淨，我們連續打三次卡
        # 這裡利用 achievement_text 來識別順序
        checkins_data = [
            "Checkin_A_Oldest",
            "Checkin_B_Middle",
            "Checkin_C_Newest"
        ]

        # 依序寫入 (A -> B -> C)
        for text in checkins_data:
            payload = {
                "challenge_level": 0.5,
                "skill_level": 0.5,
                "achievement_text": text,
                "obstacle_text": "Test sorting"
            }
            res = await client.post(f"/teams/{team_id}/checkins/", json=payload)
            assert res.status_code == 201

        # 呼叫獲取列表 API
        response = await client.get(f"/teams/{team_id}/checkins/all_record/")
        assert response.status_code == 200
        
        data = response.json()
        
        # 驗證 1: 數量應該至少有 3 筆 (如果其他測試有用同一個 DB session 可能更多，但我們只看最新的 3 筆)
        assert len(data) >= 3

        # 驗證 2: 檢查排序
        # 我們期望列表的第一個元素 (index 0) 是最後寫入的 "Checkin_C_Newest"
        assert data[0]["achievement_text"] == "Checkin_C_Newest"
        assert data[1]["achievement_text"] == "Checkin_B_Middle"
        assert data[2]["achievement_text"] == "Checkin_A_Oldest"

        # 額外驗證: ID 排序
        # 因為使用 UUIDv7，最新的紀錄 ID 應該大於舊的紀錄 ID
        assert data[0]["id"] > data[1]["id"]
        assert data[1]["id"] > data[2]["id"]