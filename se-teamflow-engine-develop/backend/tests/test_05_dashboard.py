import pytest
from httpx import AsyncClient
from typing import Dict, Any

pytestmark = pytest.mark.asyncio

@pytest.mark.run(order=5)
class TestDashboard:

    async def test_get_compass_data_with_checkins(self, team_with_member: Dict[str, Any]):
        """
        测试情绪罗盘是否能正确聚合已提交的签到数据。
        """
        owner_client = team_with_member["owner_client"]
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        
        # 1. 两个用户分别签到
        await owner_client.post(
            f"/teams/{team_id}/checkins/",
            json={"challenge_level": 0.8, "skill_level": 0.6} # Test1
        )
        await member_client.post(
            f"/teams/{team_id}/checkins/",
            json={"challenge_level": 0.2, "skill_level": 0.4} # Test2
        )
        
        # 2. 获取 "day" 周期的罗盘数据
        # 使用 owner_client 或 member_client 应该看到相同的结果
        response = await owner_client.get(f"/dashboard/teams/{team_id}/compass/?period=day")
        assert response.status_code == 200
        
        data = response.json()
        assert data["period"] == "day"
        
        # 3. 验证聚合是否正确
        # 假设 trend_data[0] 是今天的数据
        assert len(data["trend_data"]) >= 1
        today_data = data["trend_data"][0] 
        
        # 平均挑战 = (0.8 + 0.2) / 2 = 0.5
        assert today_data["avg_challenge"] == pytest.approx(0.5)
        # 平均技能 = (0.6 + 0.4) / 2 = 0.5
        assert today_data["avg_skill"] == pytest.approx(0.5)
        
        # 验证分布 (假设API会返回正确的象限)
        assert "distribution" in data
        assert len(data["distribution"].keys()) > 0

    async def test_get_focus_time_smoke_test(self, created_team: Dict[str, Any]):
        """
        测试 focus-time 端点在没有数据时是否能正常返回。
        (一个更完整的测试需要依赖 test_07_flow_ritual 来创建数据)
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        response = await client.get(f"/dashboard/teams/{team_id}/focus-time/")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_hours" in data
        assert data["total_hours"] == 0 

    async def test_get_insights_smoke_test(self, created_team: Dict[str, Any]):
        """
        (冒烟测试) 测试 AI 洞察墙端点在没有数据时是否能正常返回。
        (注意：一个更完整的测试会提交带'obstacle_text'的签到，并检查词云)
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        response = await client.get(f"/dashboard/teams/{team_id}/insights/")
        assert response.status_code == 200
        
        data = response.json()
        assert "boosters_wordcloud" in data
        assert "blockers_wordcloud" in data