import pytest
from httpx import AsyncClient
from typing import Dict, Any
import datetime

pytestmark = pytest.mark.asyncio

@pytest.mark.run(order=7)
class TestFlowRitual:

    async def _create_session(
        self, 
        client: AsyncClient, 
        team_id: str,
        minutes: int = 30,
        task: str = "默认任务"
    ) -> Dict[str, Any]:
        """辅助函数：创建一个专注会话并返回其完整对象。"""
        payload = {
            "start_time": datetime.datetime.utcnow().isoformat(), 
            "duration_minutes": minutes,
            "task_description": task
        }
        
        create_resp = await client.post(
            f"/teams/{team_id}/flow-sessions/",
            json=payload
        )
        assert create_resp.status_code == 201
        
        # 获取新创建的会话
        get_resp = await client.get(f"/teams/{team_id}/flow-sessions/")
        assert get_resp.status_code == 200
        
        session = next(
            (s for s in get_resp.json() if s["task_description"] == task),
            None
        )
        assert session is not None, "未能找到刚创建的 flow session"
        return session

    async def test_create_and_get_flow_session(self, created_team: Dict[str, Any]):
        """
        测试创建 (POST) 和获取 (GET) 专注会话。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        task_desc = "测试创建和获取"
        
        # 1. (Test) 创建
        session = await self._create_session(
            client, 
            team_id, 
            minutes=25, 
            task=task_desc
        )
        
        # 2. (Verify) 验证
        assert session["duration_minutes"] == 25
        assert session["task_description"] == task_desc

    async def test_modify_flow_session(self, created_team: Dict[str, Any]):
        """
        测试修改 (PUT) 一个已存在的专注会话。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        # 1. (Setup) 创建
        session = await self._create_session(client, team_id, task="初始任务")
        session_id = session["id"]
        
        # 2. (Test) 修改
        new_task_desc = "已修改的任务描述"
        modify_payload = {
            "id": session_id,
            "task_description": new_task_desc
        }
        modify_resp = await client.put(
            f"/teams/{team_id}/flow-sessions/modify/",
            json=modify_payload
        )
        assert modify_resp.status_code == 200
        
        # 3. (Verify) 验证
        get_resp = await client.get(f"/teams/{team_id}/flow-sessions/")
        modified_session = next(s for s in get_resp.json() if s["id"] == session_id)
        assert modified_session["task_description"] == new_task_desc

    async def test_delete_flow_session(self, created_team: Dict[str, Any]):
        """
        测试删除 (DELETE) 一个专注会话。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        # 1. (Setup) 创建
        session = await self._create_session(client, team_id, task="将被删除")
        session_id = session["id"]
        
        # 2. (Test) 删除
        delete_resp = await client.request(
            "DELETE",
            f"/teams/{team_id}/flow-sessions/delete/",
            json={"id": session_id}
        )
        assert delete_resp.status_code == 200
        
        # 3. (Verify) 验证
        get_resp = await client.get(f"/teams/{team_id}/flow-sessions/")
        assert not any(s["id"] == session_id for s in get_resp.json())

    async def test_dashboard_focus_time_integration(self, created_team: Dict[str, Any]):
        """
        (集成测试)
        测试创建一个专注会话后，仪表盘的 /focus-time/ 端点是否正确更新。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        # 1. (Setup) 创建一个 60 分钟的会话
        await self._create_session(client, team_id, minutes=60, task="仪表盘测试")
        
        # 2. (Test) 检查仪表盘
        dash_resp = await client.get(
            f"/dashboard/teams/{team_id}/focus-time/?period=day"
        )
        assert dash_resp.status_code == 200
        
        data = dash_resp.json()
        # 60 分钟 = 1.0 小时
        assert data["total_hours"] == pytest.approx(1.0)
        
        # 3. (Setup) 再创建一个 30 分钟的会话
        await self._create_session(client, team_id, minutes=30, task="仪表盘测试2")
        
        # 4. (Test) 再次检查仪表盘
        dash_resp_2 = await client.get(
            f"/dashboard/teams/{team_id}/focus-time/?period=day"
        )
        assert dash_resp_2.status_code == 200
        # 总时长应为 1.0 + 0.5 = 1.5 小时
        assert dash_resp_2.json()["total_hours"] == pytest.approx(1.5)
    async def test_get_flow_sessions_by_date(self, created_team: Dict[str, Any]):
        """
        測試根據日期篩選專注會話。
        路徑: GET /teams/{team_id}/flow-sessions_bydate/?date=YYYY-MM-DD
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        # 1. 創建一個今天的 Session
        # 注意：後端使用的是中國時間 (China Now)，測試時盡量確保測試環境時間一致，
        # 或者是直接創建後，獲取當天日期進行查詢。
        await self._create_session(client, team_id, minutes=45, task="今天要做的事")
        
        # 獲取今天的日期 (模擬後端 China Time 的日期邏輯，或者直接用 utcnow().date() 近似)
        # 為了保險起見，我們假設測試環境與後端一致，取當前日期的字串格式
        today_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date().isoformat()
        
        # 2. 使用正確的日期查詢
        resp_today = await client.get(
            f"/teams/{team_id}/flow-sessions_bydate/",
            params={"date": today_str}
        )
        assert resp_today.status_code == 200
        data_today = resp_today.json()
        assert len(data_today) >= 1
        assert data_today[0]["task_description"] == "今天要做的事"
        
        # 3. 使用錯誤的日期查詢 (例如明天，或很久以前)
        wrong_date_str = "2000-01-01"
        resp_wrong = await client.get(
            f"/teams/{team_id}/flow-sessions_bydate/",
            params={"date": wrong_date_str}
        )
        assert resp_wrong.status_code == 200
        data_wrong = resp_wrong.json()
        # 應該查不到數據
        assert len(data_wrong) == 0