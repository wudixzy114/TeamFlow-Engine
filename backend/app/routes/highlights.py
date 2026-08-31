from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from ..core import crud, models, schemas
from ..core.dependencies import get_db, get_current_user, get_highlight_and_verify_access


router = APIRouter(prefix="/highlights", tags=["Highlights"])

@router.post(
    "/{highlight_id}/like/",
    status_code=status.HTTP_200_OK,
    tags=["Recognition"],
    summary="点赞一个高光时刻",
)
def like_highlight(
    highlight: models.Highlight = Depends(get_highlight_and_verify_access), # 使用新的依賴項
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """为指定的高光时刻点赞。"""
    response = crud.like_highlight(db=db, highlight_id=highlight.id, user_id=str(current_user.id))
    if not response :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Highlight already liked")
    return {"message": "Highlight liked successfully"}


@router.post(
    "/{highlight_id}/dislike/", 
    status_code=status.HTTP_200_OK,
    tags=["Recognition"],
    summary="取消点赞高光时刻",
)
def unlike_highlight(
    highlight: models.Highlight = Depends(get_highlight_and_verify_access), # 同樣使用新的依賴項
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取消对指定高光时刻的点赞。"""
    success = crud.unlike_highlight(db=db, highlight_id=highlight.id, user_id=str(current_user.id))
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Highlight not liked")
    return {"message": "Highlight unliked successfully"}

