from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from ..core import crud, models, schemas
from ..core.dependencies import get_db, get_current_user, get_highlight_and_verify_access


router = APIRouter(prefix="/highlights", tags=["Highlights"])

@router.put(
    "/{highlight_id}/like/",
    status_code=status.HTTP_200_OK,
    tags=["Recognition"],
    summary="点赞一个高光时刻",
)
async def like_highlight(
    highlight: models.Highlight = Depends(get_highlight_and_verify_access), # 使用新的依賴項
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """为指定的高光时刻点赞。"""
    response = await crud.like_highlight(db=db, highlight_id=highlight.id, user_id=str(current_user.id))
    if not response :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Highlight already liked")
    
    success = await crud.add_team_message(db=db, receiver_id=highlight.user_id, team_id=highlight.team_id, tag="highlights", content=f"{current_user.username} likes your highlight!")
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to send notification")
    
    return {"message": "Highlight liked successfully"}


@router.delete(
    "/{highlight_id}/dislike/", 
    status_code=status.HTTP_200_OK,
    tags=["Recognition"],
    summary="取消点赞高光时刻",
)
async def unlike_highlight(
    highlight: models.Highlight = Depends(get_highlight_and_verify_access), # 同樣使用新的依賴項
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消对指定高光时刻的点赞。"""
    success = await crud.unlike_highlight(db=db, highlight_id=highlight.id, user_id=str(current_user.id))
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Highlight not liked")
    return {"message": "Highlight unliked successfully"}

@router.get("/{highlight_id}/all_comments/", response_model=List[schemas.Comment], status_code=status.HTTP_200_OK, tags=["Comments"], summary="获取高光时刻的所有评论")
async def get_highlight_comments(highlight: models.Highlight = Depends(get_highlight_and_verify_access), current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取指定高光时刻的所有评论。"""
    return await crud.get_highlight_comments(db=db, highlight_id=highlight.id)


@router.post("/{highlight_id}/comments/", status_code=status.HTTP_201_CREATED, tags=["Comments"], summary="评论高光时刻")
async def create_highlight_comment(comment: schemas.CommentContent, highlight: models.Highlight = Depends(get_highlight_and_verify_access), current_user: models.User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    """为指定的高光时刻创建一条评论。"""
    result = await crud.create_highlight_comment(db=db, highlight_id=highlight.id, user_id=current_user.id, comment=comment.content)
    if not result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create comment")
    return {"message": "Comment created successfully"}

@router.delete("/{highlight_id}/comments/delete/", status_code=status.HTTP_200_OK, tags=["Comments"], summary="删除高光时刻的评论")
async def delete_highlight_comment(commentid: schemas.CommentID, highlight: models.Highlight = Depends(get_highlight_and_verify_access), current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除指定高光时刻的评论。"""
    success = await crud.delete_highlight_comment(db=db, highlight_id=highlight.id , user_id=current_user.id, comment_id=commentid.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete comment")
    return {"message": "Comment deleted successfully"}
    
@router.put("/{highlight_id}/comments/modify/", status_code=status.HTTP_200_OK, tags=["Recognition"], summary="修改高光时刻的评论")
async def modify_highlight_comment(comment: schemas.CommentModify, highlight: models.Highlight = Depends(get_highlight_and_verify_access), current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """修改指定高光時刻"""
    success = await crud.modify_highlight_comment(db=db, comment=comment.content, comment_id=comment.id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to modify comment")
    return {"message": "Comment modified successfully"}