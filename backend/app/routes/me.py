from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date
import logging

from ..core import crud, schemas, models
from ..core.dependencies import get_current_user, get_db

router = APIRouter(prefix="/me", tags=["Me"])


@router.get(
    "/kudos/received/",
    response_model=List[schemas.Kudos],
    summary="获取我收到的Kudos",
)
def list_my_kudos(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户收到的所有 Kudos 能量卡列表。
    """
    return crud.list_received_kudos_for_user(db=db, user_id=str(current_user.id))


@router.get(
    "/weekly-digest/",
    response_model=schemas.WeeklyDigestData,
    summary="获取我的周报数据",
)
def get_my_weekly_digest(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    query_date: date = Query(..., alias="date", description="查询周的任意一天, 格式 YYYY-MM-DD"),
):
    """
    根据指定的日期，生成并返回该日期所在周的个人周报数据。
    """
    return crud.get_user_weekly_digest(db=db, user_id=str(current_user.id), query_date=query_date)


@router.get(
    "/all_invite/",
    response_model=List[schemas.InviteInfo],
    summary="获取我的所有邀請紀錄",
)
def get_all_my_invite(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = crud.get_user_all_invite(db=db, user_email=current_user.email)

    # 將查詢結果組裝成 Pydantic 模型列表
    # result 的每一項是一個元組 (invitation_obj, team_name, inviter_username)
    response = [
        schemas.InviteInfo(
            **invitation.__dict__,       # 將 invitation 物件的所有屬性解包
            team_name=team_name,         # 附加上 team_name
            inviter_username=inviter_username # 附加上 inviter_username
        )
        for invitation, team_name, inviter_username in results
    ]
    
    return response