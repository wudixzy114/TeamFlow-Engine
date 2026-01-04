import pytest
from httpx import AsyncClient
from typing import Dict, Any

pytestmark = pytest.mark.asyncio

@pytest.mark.run(order=10)
class TestForum:

    # --- 辅助函数 ---

    async def _create_section(
        self, 
        client: AsyncClient, 
        team_id: str, 
        name: str = "默认版块", 
        description: str = "默认描述"
    ) -> Dict[str, Any]:
        """创建一个版块并返回对象"""
        payload = {"name": name, "description": description}
        resp = await client.post(f"/teams/{team_id}/forum/sections/", json=payload)
        assert resp.status_code == 201
        return resp.json()

    async def _create_post(
        self, 
        client: AsyncClient, 
        team_id: str, 
        section_id: str, 
        title: str = "测试帖子", 
        content: str = "内容"
    ) -> Dict[str, Any]:
        """创建一个帖子并返回对象"""
        payload = {"title": title, "content": content}
        resp = await client.post(
            f"/teams/{team_id}/forum/sections/{section_id}/posts/", 
            json=payload
        )
        assert resp.status_code == 201
        return resp.json()

    # --- 版块管理测试 (Section Management) ---

    async def test_section_lifecycle_owner(self, created_team: Dict[str, Any]):
        """
        测试管理员(Owner)对版块的完整操作：增 -> 查 -> 改 -> 删。
        """
        client = created_team["client"]
        team_id = created_team["team_id"]
        
        # 1. 创建版块
        section = await self._create_section(client, team_id, name="技术分享", description="讨论技术")
        section_id = section["id"]
        assert section["name"] == "技术分享"

        # 2. 获取列表
        get_resp = await client.get(f"/teams/{team_id}/forum/sections/")
        assert get_resp.status_code == 200
        sections = get_resp.json()
        assert any(s["id"] == section_id for s in sections)

        # 3. 修改版块
        update_payload = {"name": "高阶技术分享", "description": "进阶内容"}
        put_resp = await client.put(
            f"/teams/{team_id}/forum/sections/{section_id}/", 
            json=update_payload
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["name"] == "高阶技术分享"

        # 4. 删除版块
        del_resp = await client.delete(f"/teams/{team_id}/forum/sections/{section_id}/")
        assert del_resp.status_code == 200
        
        # 验证删除
        get_resp_after = await client.get(f"/teams/{team_id}/forum/sections/")
        assert not any(s["id"] == section_id for s in get_resp_after.json())

    async def test_member_cannot_manage_sections(self, team_with_member: Dict[str, Any]):
        """
        测试普通成员无法创建、修改或删除版块。
        """
        owner_client = team_with_member["owner_client"]
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]

        # Owner 先创建一个版块供测试
        section = await self._create_section(owner_client, team_id)
        section_id = section["id"]

        # 1. 成员尝试创建 -> 403
        resp = await member_client.post(
            f"/teams/{team_id}/forum/sections/", 
            json={"name": "黑客入侵"}
        )
        assert resp.status_code == 403

        # 2. 成员尝试修改 -> 403
        resp = await member_client.put(
            f"/teams/{team_id}/forum/sections/{section_id}/", 
            json={"name": "被篡改的版块"}
        )
        assert resp.status_code == 403

        # 3. 成员尝试删除 -> 403
        resp = await member_client.delete(f"/teams/{team_id}/forum/sections/{section_id}/")
        assert resp.status_code == 403

    # --- 帖子管理测试 (Post Management) ---

    async def test_post_lifecycle_member(self, team_with_member: Dict[str, Any]):
        """
        测试成员发布帖子、查看详情、修改自己帖子、删除自己帖子的流程。
        """
        owner_client = team_with_member["owner_client"]
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]
        member_id = team_with_member["member_info"]["id"]

        # Setup: Owner 创建版块
        section = await self._create_section(owner_client, team_id, name="闲聊")
        section_id = section["id"]

        # 1. Member 发布帖子
        post = await self._create_post(
            member_client, team_id, section_id, 
            title="新人报到", content="大家好！"
        )
        post_id = post["id"]
        assert post["author"]["id"] == member_id

        # 2. Member 获取帖子详情
        get_resp = await member_client.get(f"/teams/{team_id}/forum/posts/{post_id}/")
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == "新人报到"

        # 3. 获取版块下的帖子列表
        list_resp = await member_client.get(f"/teams/{team_id}/forum/sections/{section_id}/posts/")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

        # 4. Member 修改自己的帖子
        put_resp = await member_client.put(
            f"/teams/{team_id}/forum/posts/{post_id}/",
            json={"title": "新人报到(修改版)", "content": "请多关照"}
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["content"] == "请多关照"

        # 5. Member 删除自己的帖子
        del_resp = await member_client.delete(f"/teams/{team_id}/forum/posts/{post_id}/")
        assert del_resp.status_code == 200

    async def test_owner_can_delete_member_post(self, team_with_member: Dict[str, Any]):
        """
        测试管理员(Owner)可以删除成员发布的帖子（内容管理）。
        """
        owner_client = team_with_member["owner_client"]
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]

        # Setup
        section = await self._create_section(owner_client, team_id)
        post = await self._create_post(member_client, team_id, section["id"], title="违规内容")
        post_id = post["id"]

        # Owner 删除
        del_resp = await owner_client.delete(f"/teams/{team_id}/forum/posts/{post_id}/")
        assert del_resp.status_code == 200
        
        # 验证消失
        get_resp = await owner_client.get(f"/teams/{team_id}/forum/posts/{post_id}/")
        assert get_resp.status_code == 404

    async def test_member_cannot_edit_others_post(self, team_with_member: Dict[str, Any]):
        """
        测试成员(Owner也是一种成员角色，但在修改帖子逻辑中，通常只有作者能改)
        这里测试 Owner 尝试修改 Member 的帖子内容（通常应该被禁止，除非需求允许管理员改内容）。
        根据通用逻辑，只有作者能改内容。
        """
        owner_client = team_with_member["owner_client"]
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]

        section = await self._create_section(owner_client, team_id)
        post = await self._create_post(member_client, team_id, section["id"])
        
        # Owner 尝试修改 Member 的帖子
        resp = await owner_client.put(
            f"/teams/{team_id}/forum/posts/{post['id']}/",
            json={"title": "管理员强行修改"}
        )
        assert resp.status_code == 403

    # --- 互动功能测试 (Comments & Likes) ---

    async def test_comment_interaction(self, team_with_member: Dict[str, Any]):
        """
        测试评论流程：发布评论 -> 获取列表 -> 删除评论。
        """
        owner_client = team_with_member["owner_client"]
        member_client = team_with_member["member_client"]
        team_id = team_with_member["team_id"]

        # Setup: Owner 发帖
        section = await self._create_section(owner_client, team_id)
        post = await self._create_post(owner_client, team_id, section["id"], title="讨论贴")
        post_id = post["id"]

        # 1. Member 评论
        comment_content = "我是成员，我来评论了"
        resp = await member_client.post(
            f"/teams/{team_id}/forum/posts/{post_id}/comments/",
            json={"content": comment_content}
        )
        assert resp.status_code == 201
        comment_id = resp.json()["id"]

        # 2. 获取评论列表
        list_resp = await owner_client.get(f"/teams/{team_id}/forum/posts/{post_id}/comments/")
        assert list_resp.status_code == 200
        comments = list_resp.json()
        assert len(comments) == 1
        assert comments[0]["content"] == comment_content
        assert comments[0]["user"]["id"] == team_with_member["member_info"]["id"]

        # 3. 验证帖子详情中的评论数 (computed field)
        post_resp = await owner_client.get(f"/teams/{team_id}/forum/posts/{post_id}/")
        assert post_resp.json()["comments_count"] == 1

        # 4. Member 删除自己的评论
        del_resp = await member_client.delete(f"/teams/{team_id}/forum/comments/{comment_id}/")
        assert del_resp.status_code == 200

        # 5. 再次验证数量
        post_resp = await owner_client.get(f"/teams/{team_id}/forum/posts/{post_id}/")
        assert post_resp.json()["comments_count"] == 0

    async def test_like_interaction(self, team_with_member: Dict[str, Any]):
        """
        测试点赞流程：点赞 -> 验证状态 -> 取消点赞 -> 验证状态。
        """
        owner_client = team_with_member["owner_client"] # Test1
        member_client = team_with_member["member_client"] # Test2
        team_id = team_with_member["team_id"]

        # Setup: Test1 发帖
        section = await self._create_section(owner_client, team_id)
        post = await self._create_post(owner_client, team_id, section["id"])
        post_id = post["id"]

        # 1. Test2 点赞
        resp = await member_client.put(f"/teams/{team_id}/forum/posts/{post_id}/like/")
        assert resp.status_code == 200

        # 2. 验证：
        #    - Test2 看到的详情：liked_by_current_user = True
        #    - Test1 看到的详情：likes_count = 1
        
        # Test2 视角
        post_resp_mem = await member_client.get(f"/teams/{team_id}/forum/posts/{post_id}/")
        assert post_resp_mem.json()["liked_by_current_user"] is True
        assert post_resp_mem.json()["likes_count"] == 1

        # Test1 视角 (自己没点赞)
        post_resp_own = await owner_client.get(f"/teams/{team_id}/forum/posts/{post_id}/")
        assert post_resp_own.json()["liked_by_current_user"] is False
        assert post_resp_own.json()["likes_count"] == 1

        # 3. Test2 取消点赞
        resp = await member_client.delete(f"/teams/{team_id}/forum/posts/{post_id}/dislike/")
        assert resp.status_code == 200

        # 4. 验证归零
        post_resp_mem = await member_client.get(f"/teams/{team_id}/forum/posts/{post_id}/")
        assert post_resp_mem.json()["likes_count"] == 0
        assert post_resp_mem.json()["liked_by_current_user"] is False