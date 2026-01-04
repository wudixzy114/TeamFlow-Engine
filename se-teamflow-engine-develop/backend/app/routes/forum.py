from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from ..core import schemas, models, crud
from ..core.dependencies import get_db, get_current_user, get_team_and_verify_membership
from fastapi import Query

router = APIRouter(tags=["Forum"])

# 1. 获取版块列表 (GET) - 所有成员可用
@router.get("/teams/{team_id}/forum/sections/", response_model=List[schemas.ForumSection])
async def list_forum_sections(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取团队所有论坛版块"""
    return await crud.get_forum_sections(db=db, team_id=team.id)

# 2. 创建新版块 (POST) - 仅限 Owner
@router.post("/teams/{team_id}/forum/sections/", status_code=status.HTTP_201_CREATED, response_model=schemas.ForumSection)
async def create_forum_section(
    section_data: schemas.ForumSectionCreate,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """(管理员) 创建新的论坛版块"""
    # 权限检查：只有 Owner 可以创建
    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only the team owner can create forum sections."
        )
        
    new_section = await crud.create_forum_section(db=db, team_id=team.id, section_data=section_data)
    if not new_section:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create forum section.")
        
    return new_section

# 3. 修改版块 (PUT) - 仅限 Owner
@router.put("/teams/{team_id}/forum/sections/{section_id}/", response_model=schemas.ForumSection)
async def update_forum_section(
    section_data: schemas.ForumSectionModify,
    section_id: str = Path(..., title="Section ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """(管理员) 修改论坛版块信息"""
    # 权限检查
    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only the team owner can update forum sections."
        )
        
    updated_section = await crud.update_forum_section(
        db=db, 
        section_id=section_id, 
        team_id=team.id, 
        section_data=section_data
    )
    
    if not updated_section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
        
    return updated_section

# 4. 删除版块 (DELETE) - 仅限 Owner
@router.delete("/teams/{team_id}/forum/sections/{section_id}/", status_code=status.HTTP_200_OK)
async def delete_forum_section(
    section_id: str = Path(..., title="Section ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """(管理员) 删除论坛版块"""
    # 权限检查
    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only the team owner can delete forum sections."
        )
        
    success = await crud.delete_forum_section(db=db, section_id=section_id, team_id=team.id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
        
    return {"message": "Forum section deleted successfully."}

# --- Forum Post Management ---

# 1. 获取帖子列表 (分页 + 搜索逻辑)
@router.get("/teams/{team_id}/forum/sections/{section_id}/posts/", response_model=List[schemas.ForumPostResponse])
async def list_forum_posts(
    section_id: str = Path(..., title="Section ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=200, description="每页数量"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取某版块下的帖子列表，按时间倒序"""
    skip = (page - 1) * size
    
    # 1. 获取帖子列表
    posts = await crud.get_forum_posts(
        db=db, 
        team_id=team.id, 
        section_id=section_id, 
        skip=skip, 
        limit=size
    )
    
    # 2. 批量查询当前用户点赞状态
    if posts:
        post_ids = [p.id for p in posts]
        liked_post_ids = await crud.get_user_liked_post_ids(db=db, user_id=current_user.id, post_ids=post_ids)
        
        # 3. 注入状态
        for p in posts:
            p.liked_by_current_user = p.id in liked_post_ids
            
    return posts

# 2. 发布新帖子
@router.post("/teams/{team_id}/forum/sections/{section_id}/posts/", status_code=status.HTTP_201_CREATED, response_model=schemas.ForumPostResponse)
async def create_forum_post(
    post_data: schemas.ForumPostCreate,
    section_id: str = Path(..., title="Section ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """在指定版块发布内容"""
    # 检查 Section 是否存在
    section = await crud.get_forum_section_by_id(db, section_id)
    if not section or section.team_id != team.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum section not found in this team.")

    new_post = await crud.create_forum_post(
        db=db, 
        team_id=team.id, 
        section_id=section_id, 
        user_id=current_user.id, 
        post_data=post_data
    )
    
    if not new_post:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create post.")
    
    new_post.liked_by_current_user = False
    
    return new_post

# 3. 获取帖子详情
@router.get("/teams/{team_id}/forum/posts/{post_id}/", response_model=schemas.ForumPostResponse)
async def get_forum_post_detail(
    post_id: str = Path(..., title="Post ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取帖子详情"""
    post = await crud.get_forum_post_detail(db=db, post_id=post_id)
    
    if not post or post.team_id != team.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
        
    # 查询当前用户是否点赞
    liked_ids = await crud.get_user_liked_post_ids(db=db, user_id=current_user.id, post_ids=[post.id])
    post.liked_by_current_user = post.id in liked_ids
    
    return post

# 4. 修改帖子 (仅限作者)
@router.put("/teams/{team_id}/forum/posts/{post_id}/", response_model=schemas.ForumPostResponse)
async def update_forum_post(
    post_data: schemas.ForumPostModify,
    post_id: str = Path(..., title="Post ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """修改帖子，仅限作者"""
    updated_post = await crud.update_forum_post(
        db=db, 
        post_id=post_id, 
        user_id=current_user.id, 
        post_data=post_data
    )
    
    if not updated_post:
        existing = await crud.get_forum_post_detail(db, post_id)
        if existing and existing.team_id == team.id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied. Only author can edit.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    
    # 填充 liked_by_current_user 状态
    liked_ids = await crud.get_user_liked_post_ids(db=db, user_id=current_user.id, post_ids=[updated_post.id])
    updated_post.liked_by_current_user = updated_post.id in liked_ids
    
    return updated_post

# 5. 删除帖子 (作者或管理员)
@router.delete("/teams/{team_id}/forum/posts/{post_id}/", status_code=status.HTTP_200_OK)
async def delete_forum_post(
    post_id: str = Path(..., title="Post ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """删除帖子，作者或团队所有者可删除"""
    is_admin = (str(team.owner_id) == str(current_user.id))
    
    success = await crud.delete_forum_post(
        db=db, 
        post_id=post_id, 
        user_id=current_user.id, 
        is_admin=is_admin
    )
    
    if not success:
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND, 
             detail="Post not found or permission denied."
         )
         
    return {"message": "Post deleted successfully."}


# --- Forum Interaction (Comments & Likes) ---

# 1. 获取帖子评论列表
@router.get("/teams/{team_id}/forum/posts/{post_id}/comments/", response_model=List[schemas.ForumCommentResponse])
async def list_post_comments(
    post_id: str = Path(..., title="Post ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取该帖子的所有评论"""
    # 验证 Post 是否存在且属于该 Team
    post = await crud.get_forum_post_detail(db, post_id)
    if not post or post.team_id != team.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found in this team.")

    return await crud.get_forum_post_comments(db=db, post_id=post_id)

# 2. 发表评论
@router.post("/teams/{team_id}/forum/posts/{post_id}/comments/", status_code=status.HTTP_201_CREATED, response_model=schemas.ForumCommentResponse)
async def create_post_comment(
    comment_data: schemas.ForumCommentCreate,
    post_id: str = Path(..., title="Post ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """对帖子进行回复"""
    # 验证 Post 是否存在且属于该 Team
    post = await crud.get_forum_post_detail(db, post_id)
    if not post or post.team_id != team.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found in this team.")

    comment = await crud.create_forum_comment(
        db=db, 
        post_id=post_id, 
        user_id=current_user.id, 
        content=comment_data.content
    )
    
    if not comment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create comment.")
    
    # 手动填充 user 信息以便返回
    comment.user = current_user
    return comment

# 3. 删除评论
@router.delete("/teams/{team_id}/forum/comments/{comment_id}/", status_code=status.HTTP_200_OK)
async def delete_post_comment(
    comment_id: str = Path(..., title="Comment ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """删除评论：仅限评论作者或团队管理员"""
    # 1. 获取评论详情并检查归属
    comment = await crud.get_forum_comment_detail(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
    
    # 2. 确保评论所属的帖子在当前团队中 (安全性检查)
    if comment.post.team_id != team.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found in this team.")
    
    is_team_owner = (str(team.owner_id) == str(current_user.id))
    
    success = await crud.delete_forum_comment(
        db=db, 
        comment_id=comment_id, 
        user_id=current_user.id, 
        is_team_owner=is_team_owner
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")
        
    return {"message": "Comment deleted successfully."}

# 4. 点赞帖子
@router.put("/teams/{team_id}/forum/posts/{post_id}/like/", status_code=status.HTTP_200_OK)
async def like_post(
    post_id: str = Path(..., title="Post ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """点赞帖子"""
    # 验证 Post 是否存在且属于该 Team
    post = await crud.get_forum_post_detail(db, post_id)
    if not post or post.team_id != team.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    success = await crud.like_forum_post(db=db, post_id=post_id, user_id=current_user.id)
    if not success:
        # 重复点赞通常不视为错误，或者返回 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already liked or failed.")
        
    return {"message": "Post liked successfully."}

# 5. 取消点赞帖子
@router.delete("/teams/{team_id}/forum/posts/{post_id}/dislike/", status_code=status.HTTP_200_OK)
async def dislike_post(
    post_id: str = Path(..., title="Post ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """取消点赞帖子"""
    # 验证 Post 是否存在且属于该 Team
    post = await crud.get_forum_post_detail(db, post_id)
    if not post or post.team_id != team.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    success = await crud.unlike_forum_post(db=db, post_id=post_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post not liked yet.")
        
    return {"message": "Post unliked successfully."}