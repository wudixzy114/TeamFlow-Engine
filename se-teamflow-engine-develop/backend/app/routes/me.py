from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..core import crud, schemas, models
from ..core.dependencies import get_current_user, get_db, get_team_and_verify_membership

router = APIRouter(prefix="/me", tags=["Me"])


@router.get(
    "/kudos/received/",
    response_model=List[schemas.Kudos],
    summary="获取我收到的Kudos",
)
async def list_my_kudos(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户收到的所有 Kudos 能量卡列表。
    """
    return await crud.list_received_kudos_for_user(db=db, user_id=str(current_user.id))


@router.get(
    "/weekly-digest/",
    response_model=schemas.WeeklyDigestData,
    summary="获取我的周报数据",
)
async def get_my_weekly_digest(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    query_date: date = Query(..., alias="date", description="查询周的任意一天, 格式 YYYY-MM-DD"),
):
    """
    根据指定的日期，生成并返回该日期所在周的个人周报数据。
    """
    return await crud.get_user_weekly_digest(db=db, user_id=str(current_user.id), query_date=query_date)


@router.get(
    "/all_invite/",
    response_model=List[schemas.InviteInfo],
    summary="获取我的所有邀請紀錄",
)
async def get_all_my_invite(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    results = await crud.get_user_all_invite(db=db, user_email=current_user.email)

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

@router.get("/message/", response_model = List[schemas.Message], status_code=status.HTTP_200_OK)
async def get_message(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return await crud.get_message(db=db, user_id=current_user.id)

@router.delete("/message/delete/", status_code=status.HTTP_200_OK)
async def delete_message(message_id: schemas.Delete_message, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    success = await crud.delete_message(db=db, user_id=current_user.id, message_id=message_id.message_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete message.")

    return {"message": "message deleted successfully."}

@router.get(
    "/skill_tree/",
    response_model=schemas.SkillTreeData,
    summary="获取我的技能树",
)
async def get_my_skill_tree(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    返回当前用户基于签到成就的技能树。
    """
    return await crud.get_skill_tree_for_user(db=db, user_id=str(current_user.id))

@router.post(
    "/skill_tree/node/", 
    status_code=status.HTTP_201_CREATED,
    summary="添加根节点"
)
async def add_root_node(
    skill: schemas.UserSkillItem,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_id = await crud.add_user_skill(db, current_user.id, skill, parent_id=None)
    
    if not new_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Skill already exists or invalid input."
        )
        
    return {"message": "Root skill added successfully.", "node_id": new_id}

@router.post(
    "/skill_tree/node/{parent_id}/",
    status_code=status.HTTP_201_CREATED,
    summary="添加个人技能节点",
)
async def add_my_skill_node(
    parent_id: str,
    skill: schemas.UserSkillItem,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    添加一个新的技能节点到个人技能树，并自动同步到所在的团队。
    """
    new_id = await crud.add_user_skill(db=db, user_id=str(current_user.id)
                                       , parent_id=parent_id, skill=skill)
    
    if not new_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Skill already exists or invalid input."
        )
        
    return {"message": "Skill added successfully.", "node_id": new_id}


@router.put(
    "/skill_tree/node/{node_id}/",
    status_code=status.HTTP_200_OK,
    summary="修改个人技能节点",
)
async def modify_my_skill_node(
    node_id: str,
    payload: schemas.UserSkillModify,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    修改指定的技能节点（名称或元数据）。
    """
    success = await crud.modify_user_skill(
        db=db, 
        user_id=str(current_user.id), 
        node_id=node_id, 
        payload=payload
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Node not found or new name conflicts with existing skill."
        )
    return {"message": "Skill modified successfully."}


@router.delete(
    "/skill_tree/node/{node_id}/", 
    status_code=status.HTTP_200_OK,
    summary="删除个人技能节点",
)
async def delete_my_skill_node(
    node_id: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除指定的技能节点，同时会移除团队中对应的该技能。
    """
    success = await crud.delete_user_skill(db=db, user_id=str(current_user.id), node_id=node_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Node not found."
        )
    return {"message": "Skill deleted successfully."}


    
@router.get("/{team_id}/message/", response_model = List[schemas.TeamMessage], status_code=status.HTTP_200_OK)
async def get_team_message(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db), current_team: str = Depends(get_team_and_verify_membership)):
    return await crud.get_team_message(db=db, user_id=current_user.id, team_id=current_team.id)

@router.delete("/{team_id}/message/delete/", status_code=status.HTTP_200_OK)

async def delete_team_message(message_id: schemas.Delete_message, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db), current_team: str = Depends(get_team_and_verify_membership)):
    success = await crud.delete_team_message(db=db, user_id=current_user.id, message_id=message_id.message_id, team_id=current_team.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_INTERNAL_SERVER_ERROR, detail="Failed to delete message.")

    return {"message": "message deleted successfully."}