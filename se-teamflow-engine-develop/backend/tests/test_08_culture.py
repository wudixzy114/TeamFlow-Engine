import pytest
from httpx import AsyncClient
import json
from typing import Dict, Any

pytestmark = pytest.mark.asyncio

@pytest.mark.run(order=8)
class TestCultureAndGrowth:

    # --- 团队公约 (Charter) 测试 (保持不变) ---

    async def test_get_initial_charter(self, created_team: Dict[str, Any]):
        """
        测试新团队的公约（Charter）是否可以被获取。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        response = await client.get(f"/teams/{team_id}/charter/")
        assert response.status_code == 200
        
        data = response.json()
        assert "content" in data
        
    async def test_owner_can_update_and_delete_charter(self, created_team: Dict[str, Any]):
        """
        测试所有者可以更新 (PUT) 和删除 (DELETE) 团队公约。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        owner_id = created_team["owner_id"]
        charter_content = "# 我们的团队公约\n- 规则1"
        
        # 1. (Test) 更新公约
        update_payload = {"content": charter_content}
        update_resp = await client.put(
            f"/teams/{team_id}/charter/", 
            json=update_payload
        )
        assert update_resp.status_code == 200
        
        # 2. (Verify) 验证更新
        get_resp = await client.get(f"/teams/{team_id}/charter/")
        data = get_resp.json()
        assert data["content"] == charter_content
        assert data["last_updated_by"]["id"] == owner_id
        
        # 3. (Test) 删除公约
        delete_resp = await client.delete(f"/teams/{team_id}/delete-charter/")
        assert delete_resp.status_code == 200
        
        # 4. (Verify) 验证删除 (假设删除后内容重置为空)
        get_resp_after = await client.get(f"/teams/{team_id}/charter/")
        assert get_resp_after.json()["content"] == "" 

    async def test_member_cannot_update_charter(self, team_with_member: Dict[str, Any]):
        """
        测试普通成员 (test2) 无法更新团队公约。
        """
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        
        update_payload = {"content": "成员的修改"}
        response = await member_client.put(
            f"/teams/{team_id}/charter/", 
            json=update_payload
        )
        assert response.status_code == 403

    async def test_member_cannot_delete_charter(self, team_with_member: Dict[str, Any]):
        """
        测试普通成员 (test2) 无法删除团队公约。
        """
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        
        response = await member_client.delete(f"/teams/{team_id}/delete-charter/")
        assert response.status_code == 403

    # --- 技能树 (Skill Tree) 测试 ---
    
    async def _cleanup_skills(self, client, skill_names):
        """
        辅助函数：清理指定名称的技能节点，防止测试数据冲突。
        """
        resp = await client.get("/me/skill_tree/")
        if resp.status_code == 200:
            tree = resp.json()
            # 只需要尝试删除根节点，如果目标节点是子节点，可能需要更复杂的查找逻辑，
            # 但针对当前测试用例，我们通常知道我们在操作根还是子。
            # 这里简单遍历根节点。
            for node in tree.get("children", []):
                if node["name"] in skill_names:
                    await client.delete(f"/me/skill_tree/node/{node['id']}/")

    async def test_personal_skill_sync_lifecycle(self, team_with_member: Dict[str, Any]):
        """
        测试个人技能树(根节点)的原子操作及其向团队技能树的同步：
        1. Member 添加根节点 (带 meta_data) -> 验证团队树同步。
        2. Member 修改节点 (改名 + 改 meta_data) -> 验证团队树同步。
        3. Member 删除节点 -> 验证团队树同步删除。
        """
        owner_client = team_with_member["owner_client"]
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        member_info = team_with_member["member_info"]
        member_id = member_info["id"]

        skill_name = "FastAPI"
        new_skill_name = "FastAPI (Advanced)"
        
        # 清理环境
        await self._cleanup_skills(member_client, [skill_name, new_skill_name])

        # 初始检查
        resp = await owner_client.get(f"/teams/{team_id}/skill-tree/")
        assert resp.status_code == 200
        
        # --- A. 测试添加根节点 (POST /me/skill_tree/node) ---
        meta_data_initial = {"proficiency": "Intermediate", "difficulty": "High"}
        
        add_payload = {
            "name": skill_name, 
            "meta_data": meta_data_initial
        }
        # 注意：这里不需要传 parent_id，使用的是添加根节点的路由
        resp = await member_client.post("/me/skill_tree/node/", json=add_payload)
        assert resp.status_code == 201
        resp_data = resp.json()
        assert "node_id" in resp_data
        node_id = resp_data["node_id"] 

        # 验证同步到团队树
        resp = await owner_client.get(f"/teams/{team_id}/skill-tree/")
        tree = resp.json()
        
        # 找到成员节点 -> 找到技能节点
        member_node = next((n for n in tree["children"] if n["id"] == member_id), None)
        assert member_node is not None, "团队树中未找到成员节点"
        
        skill_node = next((s for s in member_node["children"] if s["name"] == skill_name), None)
        assert skill_node is not None, "团队树中未同步新添加的技能"
        assert skill_node["meta_data"] == meta_data_initial

        # --- B. 测试修改 (PUT /me/skill_tree/node/{node_id}) ---
        meta_data_updated = {"proficiency": "Expert", "difficulty": "Extreme"}
        
        modify_payload = {
            "new_name": new_skill_name,
            "meta_data": meta_data_updated
        }
        resp = await member_client.put(f"/me/skill_tree/node/{node_id}/", json=modify_payload)
        assert resp.status_code == 200

        # 验证同步到团队树
        resp = await owner_client.get(f"/teams/{team_id}/skill-tree/")
        tree = resp.json()
        member_node = next((n for n in tree["children"] if n["id"] == member_id), None)
        
        old_skill_node = next((s for s in member_node["children"] if s["name"] == skill_name), None)
        assert old_skill_node is None, "旧技能名未被移除/更新"
        
        new_skill_node = next((s for s in member_node["children"] if s["name"] == new_skill_name), None)
        assert new_skill_node is not None, "新技能名未同步"
        assert new_skill_node["meta_data"] == meta_data_updated

        # --- C. 测试删除 (DELETE /me/skill_tree/node/{node_id}) ---
        resp = await member_client.delete(f"/me/skill_tree/node/{node_id}/")
        assert resp.status_code == 200

        # 验证同步到团队树
        resp = await owner_client.get(f"/teams/{team_id}/skill-tree/")
        tree = resp.json()
        member_node = next((n for n in tree["children"] if n["id"] == member_id), None)
        
        deleted_skill_node = next((s for s in member_node["children"] if s["name"] == new_skill_name), None)
        assert deleted_skill_node is None, "技能未从团队树中同步删除"

    async def test_nested_skill_tree_lifecycle(self, team_with_member: Dict[str, Any]):
        """
        【新增】测试嵌套技能树（多级节点）的生命周期及级联删除：
        1. Member 添加根节点 'Backend'。
        2. Member 在 'Backend' 下添加子节点 'Python'。
        3. 验证个人树结构嵌套。
        4. 验证团队树结构嵌套。
        5. 删除 'Backend'，验证 'Python' 也被级联删除。
        """
        owner_client = team_with_member["owner_client"]
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        member_id = team_with_member["member_info"]["id"]

        root_name = "Backend"
        child_name = "Python"
        
        # 清理
        await self._cleanup_skills(member_client, [root_name])

        # 1. 添加根节点
        resp = await member_client.post("/me/skill_tree/node/", json={"name": root_name})
        assert resp.status_code == 201
        root_id = resp.json()["node_id"]

        # 2. 添加子节点 (使用新路由 /me/skill_tree/node/{parent_id})
        resp = await member_client.post(f"/me/skill_tree/node/{root_id}/", json={"name": child_name})
        assert resp.status_code == 201
        child_id = resp.json()["node_id"]

        # 3. 验证个人技能树嵌套结构
        resp = await member_client.get("/me/skill_tree/")
        assert resp.status_code == 200
        tree = resp.json()
        
        # 查找根节点
        root_node = next((n for n in tree["children"] if n["id"] == root_id), None)
        assert root_node is not None, "根节点未找到"
        assert root_node["name"] == root_name
        
        # 查找子节点 (应在 root_node['children'] 中，体现递归结构)
        # 注意：这里验证了后端是否正确返回了嵌套结构 A->B
        child_node = next((n for n in root_node["children"] if n["id"] == child_id), None)
        assert child_node is not None, "子节点未嵌套在根节点下"
        assert child_node["name"] == child_name

        # 4. 验证团队技能树同步
        resp = await owner_client.get(f"/teams/{team_id}/skill-tree/")
        assert resp.status_code == 200
        team_tree = resp.json()
        
        # 找到成员 -> 根节点 -> 子节点
        member_tree_root = next((n for n in team_tree["children"] if n["id"] == member_id), None)
        assert member_tree_root is not None
        
        team_skill_root = next((n for n in member_tree_root["children"] if n["name"] == root_name), None)
        assert team_skill_root is not None, "团队树中未找到根节点"
        
        team_skill_child = next((n for n in team_skill_root["children"] if n["name"] == child_name), None)
        assert team_skill_child is not None, "团队树中子节点未正确嵌套"

        # 5. 测试级联删除
        # 删除根节点，子节点应一并被删
        resp = await member_client.delete(f"/me/skill_tree/node/{root_id}/")
        assert resp.status_code == 200

        # 验证个人树空了
        resp = await member_client.get("/me/skill_tree/")
        tree = resp.json()
        root_node_check = next((n for n in tree["children"] if n["id"] == root_id), None)
        assert root_node_check is None

        # 验证团队树空了
        resp = await owner_client.get(f"/teams/{team_id}/skill-tree/")
        team_tree = resp.json()
        member_tree_root = next((n for n in team_tree["children"] if n["id"] == member_id), None)
        team_skill_root_check = next((n for n in member_tree_root["children"] if n["name"] == root_name), None)
        assert team_skill_root_check is None

    async def test_duplicate_skill_prevention(self, team_with_member: Dict[str, Any]):
        """
        测试个人技能树的重复添加防护 (原子操作)。
        """
        member_client = team_with_member["member_client"]
        skill_name = "Python"

        await self._cleanup_skills(member_client, [skill_name])

        # 1. 第一次添加
        resp = await member_client.post("/me/skill_tree/node/", json={"name": skill_name})
        assert resp.status_code == 201

        # 2. 第二次添加相同名字 (应该失败)
        resp = await member_client.post("/me/skill_tree/node/", json={"name": skill_name})
        assert resp.status_code == 400