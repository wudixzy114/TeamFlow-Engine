from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from ..core import schemas, models, crud, utils
from ..core.dependencies import get_db, get_current_user, get_team_and_verify_membership
import asyncio

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_team(
    team_create: schemas.TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    team = await crud.create_team(db=db, team=team_create, owner=current_user)
    if not team:
        raise HTTPException(status_code=400, detail="Team creation failed")
    
    return {"message": "Team created successfully"}

@router.get("/", response_model=List[schemas.Team])
async def list_my_teams(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    teams = await crud.get_teams_for_user(db=db, user=current_user)
    return teams

@router.get("/{team_id}/members/", response_model=schemas.TeamMembersResponse)
async def list_team_members(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db)
):
    team_details = await crud.get_team_members(db=db, team_id=team.id)

    # 如果 crud 函數找不到 team，可能需要處理這種情況
    if not team_details:
        raise HTTPException(status_code=404, detail="Team not found")

    return team_details

@router.post("/{team_id}/invitations/", status_code=status.HTTP_201_CREATED)  #邀請成員加入
async def invite_team(
    credential : schemas.EmailORUsername,
    team: models.Team = Depends(get_team_and_verify_membership), 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)   #這個user是邀請者
    
):
    # user = await crud.get_user_by_email_or_username(db, email_or_username=credential.email_username)#這個user是被邀請者
    # if user is None:
    #     raise HTTPException(status_code=400, detail="User not found")
    
    # team = await crud.get_team_for_user(db=db, team_id=team.id, user=current_user)   #已經依賴注入
    # if not team:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this team")
    
    #中間細節之後處裡
      # 4. 查找被邀請者
    invitee = await crud.get_user_by_email_or_username(db, email_or_username=credential.email_username)
    
    if not invitee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to invite not found")

    # 5. 防止邀請自己
    if invitee.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot invite yourself")

    is_member = await crud.is_user_in_team(db=db, team_id=team.id, user_id=invitee.id)
    if is_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this team")

    has_pending = await crud.has_pending_invitation(db=db, team_id=team.id, invitee_email=invitee.email)
    if has_pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user already has a pending invitation")

    # 7. 創建邀請 (注意傳遞的參數)
    response = await crud.create_invitation(db=db, team_id=team.id, inviter_id=current_user.id, invitee_email=invitee.email)
    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create invitation")
    
    return {"message": "The invitation has been sent successfully."}

@router.post("/invitations/accept/", status_code=status.HTTP_200_OK)
async def accept_invite(
    invite_data: schemas.InviteCode,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 步驟 1: 驗證邀請碼是否有效且屬於當前用戶
    invitation = await crud.get_valid_invitation_by_code(
        db=db, 
        invite_code=invite_data.code, 
        current_user_email=current_user.email
    )

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation code, or this invitation is not for you."
        )
 
    # 步驟 2: 調用封裝好的 CRUD 函數處理所有資料庫操作
    joined_team = await crud.accept_invitation_and_join_team(
        db=db, 
        invitation=invitation, 
        user=current_user
    )
    
    # 步驟 3: 根據 CRUD 函數的結果返回 HTTP 響應
    if not joined_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to join the team. The team may not exist or you are already a member."
        )
    
    return {"message": f"Successfully joined the team: {joined_team.name}."}

@router.post("/{team_id}/checkins/", status_code=status.HTTP_201_CREATED)
async def create_team_checkin(
    checkin: schemas.CheckinCreate,
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入來驗證團隊成員身份
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. 檢查今天是否已經簽到，防止重複提交
    # if await crud.has_checked_in_today(db=db, user_id=current_user.id, team_id=team.id):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="You have already checked in for this team today."
    #     )

    # 2. 創建簽到記錄
    # 注意：將 crud 函數的參數名從 'current_user' 改為 'user' 以匹配其定義
    create = await crud.checkin_create(db=db, checkin=checkin, team_id=team.id, user=current_user)
    if not create:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create check-in record."
        )
        
    return {"message": "Check-in successful."}

@router.get("/{team_id}/checkins/all_record/", status_code=status.HTTP_200_OK, response_model=List[schemas.CheckinRecord])
async def get_all_checkin_record_endpoint(
    date: date | None = Query(default=None), # 修改 3: 正確的 Query 定義方式
    limit: int = Query(10, ge=1, le=100),
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: AsyncSession = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
) -> List[schemas.CheckinRecord]:
    
    return await crud.get_all_checkin_record(db=db, user_id=current_user.id, team_id=team.id, query_date=date, limit=limit)
    
    
@router.get("/{team_id}/checkins/today/", status_code=status.HTTP_200_OK)
async def get_today_checkin_status(
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: AsyncSession = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
):
    # 1. 調用修正後的 CRUD 函數
    has_checked_in = await crud.has_checked_in_today(db=db, user_id=current_user.id, team_id=team.id)
    
    # 2. 按照 Pydantic 模型和 OpenAPI 文件返回結果
    return {"has_checked_in": has_checked_in}

@router.get("/{team_id}/highlights/", response_model=List[schemas.Highlight])
async def get_highlights(
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: AsyncSession = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
):
    team_highlights, liked_ids = await crud.get_highlights_data(db=db, user_id=str(current_user.id), team_id=str(team.id))

    for highlight in team_highlights:   #這裡N+1沒關係了
        highlight.liked_by_current_user = highlight.id in liked_ids

    return team_highlights

@router.post("/{team_id}/highlights/", status_code=status.HTTP_201_CREATED)
async def post_highlights(
    highlights: schemas.HighlightBase,
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: AsyncSession = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
):
    high_lights = await crud.post_highlights(db=db, user_id=current_user.id, team_id=team.id, highlights = highlights.content)
    if not high_lights:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create highlights")
    
    return {"message": "发布成功"}

@router.put("/{team_id}/highlights/modify/", status_code=status.HTTP_200_OK)
async def modify_highlight(
    highlight_data: schemas.HighlightModify,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    修改指定的高光时刻。只有创建者本人才能修改。
    """
    success = await crud.update_highlight(
        db=db, 
        highlight_id=highlight_data.id, 
        user_id=str(current_user.id),  # 傳入當前用戶ID
        team_id=str(team.id),          # 傳入當前團隊ID
        content=highlight_data.content
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Highlight not found or you don't have permission to modify it."
        )

    return {"message": "Highlight modified successfully."}

@router.delete("/{team_id}/highlights/delete/", status_code=status.HTTP_200_OK)
async def delete_highlight(
    highlight_data: schemas.HighlightId,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    删除指定的高光时刻。创建者本人或团队所有者可以删除。
    """
    is_owner = (str(team.owner_id) == str(current_user.id))

    # 2. 調用安全刪除函數 (1次 DB 交互)
    success = await crud.delete_highlight(
        db=db,
        highlight_id=highlight_data.id,
        team_id=str(team.id),
        user_id=str(current_user.id),
        is_team_owner=is_owner
    )

    if not success:
        # 這裡失敗意味著：要麼高光時刻不存在，要麼它存在但你不擁有它
        # 返回 404 是安全的做法，避免惡意用戶掃描存在的 ID
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Highlight not found or you don't have permission to delete it."
        )

    return {"message": "Highlight deleted successfully."}


@router.post("/{team_id}/flow-sessions/", status_code=status.HTTP_201_CREATED)
async def post_flow_sessions(
    flow_sessions: schemas.FlowSessionCreate,
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: AsyncSession = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
): 
    response = await crud.post_flow_sessions(db=db, user_id=current_user.id, team_id=team.id, flow_sessions=flow_sessions)
    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create flow sessions")

    return {"message": "记录成功"}

@router.get("/{team_id}/flow-sessions/", response_model=List[schemas.ReturnFlowSession])
async def get_flow_sessions(
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: AsyncSession = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
): 
    return await crud.get_flow_sessions(db=db, user_id=current_user.id, team_id=team.id)

@router.get("/{team_id}/flow-sessions_bydate/", response_model=List[schemas.ReturnFlowSession])
async def get_flow_sessions_bydate(
    search_date: date = Query(..., alias="date", description="Format: YYYY-MM-DD"), 
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: AsyncSession = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
): 
    return await crud.get_flow_sessions_bydate(db=db, user_id=current_user.id, team_id=team.id, date=search_date)

@router.post("/{team_id}/kudos/", status_code=status.HTTP_201_CREATED, tags=["Recognition"])
async def send_kudos(  
    kudos_data: schemas.KudosCreate,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # team = await crud.get_team_for_user(db=db, team_id=team.id, user=current_user) #已經有依賴注入
    if not team:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this team")

    is_receiver_in_team = await crud.is_user_in_team(db=db, team_id=team.id, user_id=kudos_data.receiver_id)
    if not is_receiver_in_team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found in this team")

    response = await crud.create_kudos(db=db, kudos_data=kudos_data, sender_id=current_user.id, team_id=team.id)
    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to send kudos")
    
    success = await crud.add_team_message(db=db, receiver_id=kudos_data.receiver_id, team_id=team.id, tag="kudos", content=f"{current_user.username} sent you a kudos!")
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to send notification")
    
    return {"message": "Kudos sent successfully."}

@router.get("/{team_id}/charter/",response_model=schemas.Charter,tags=["Culture & Growth"],summary="获取团队心流公约")
async def get_charter(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db)
):
    """获取指定团队的心流公约。如果不存在，则会返回一个默认的空公约。"""
    return await crud.get_charter_for_team(db=db, team_id=str(team.id))

@router.put("/{team_id}/charter/",tags=["Culture & Growth"],summary="更新团队心流公约 (管理员)")
async def update_charter(
    charter_data: schemas.CharterUpdate,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    更新团队的心流公约。只有团队所有者(Owner)才有权限更新。
    """
    # 验证权限：只有团队所有者可以更新
    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can update the charter."
        )
        
    response = await crud.update_charter_for_team(db=db,team_id=str(team.id),user_id=str(current_user.id),content=charter_data.content)
    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update charter")
    return {"message": "Charter updated successfully."}

@router.delete("/{team_id}/delete-charter/", status_code=status.HTTP_200_OK, tags=["Culture & Growth"], summary="删除团队心流公约 (管理员)")
async def delete_charter(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    删除团队的心流公约。只有团队所有者(Owner)才有权限删除。
    """
    # 验证权限：只有团队所有者可以删除
    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can delete the charter."
        )

    success = await crud.delete_charter_for_team(db=db, team_id=str(team.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charter not found or could not be deleted."
        )
        
    return {"message": "Charter deleted successfully."}


@router.get("/{team_id}/skill-tree/",response_model=schemas.SkillTreeData,tags=["Culture & Growth"],summary="获取团队技能树数据")
async def get_skill_tree(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db)
):
    """
    获取团队技能树。数据包含两部分：
    1. 成员技能汇聚：来自成员个人添加并同步过来的技能。
    2. 团队目标/标签：管理员手动添加的。
    """
    return await crud.get_skill_tree_for_team(db=db, team_id=str(team.id))

@router.delete("/{team_id}/delete/", status_code=status.HTTP_200_OK)
async def delete_team(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    删除指定团队。只有团队所有者(Owner)才有权限删除。
    """
    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can delete the team."
        )

    success = await crud.delete_team(db=db, team_id=str(team.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete the team."
        )
        
    return {"message": "Team deleted successfully."}

@router.delete("/{team_id}/kick/",status_code=status.HTTP_200_OK) 
async def kick_member(
    member_id: schemas.KickMember,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    将指定成员从团队中移除。只有团队所有者(Owner)才有权限执行此操作。
    """
    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    if str(member_id.id) == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot kick yourself.")

    # 【優化】移除 get_user 和 is_user_in_team 的檢查
    # 直接執行移除操作，利用返回值判斷是否成功
    success = await crud.remove_member_from_team(db=db, team_id=str(team.id), user_id=str(member_id.id))
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this team."
        )
        
    return {"message": "Member removed successfully."}

@router.put("/{team_id}/modify/", status_code=status.HTTP_200_OK) 
async def modify_team(
    team_name: schemas.Teamname,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    修改指定团队的信息。只有团队所有者(Owner)才有权限执行此操作。
    """
    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can modify the team."
        )
    team = await crud.update_team(db=db, team_id=str(team.id), user_id=current_user.id, name=team_name.name)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found."
        )
    return {"message": "Team modified successfully."}

@router.put("/{team_id}/modify_owner/", status_code=status.HTTP_200_OK)
async def modify_team_owner(
    new_owner: schemas.TeamOwner,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")
    
    if str(new_owner.id) == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot transfer to yourself.")

    target_user = await crud.get_user(db, user_id=new_owner.id)
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    is_in_team = await crud.is_user_in_team(db=db, team_id=str(team.id), user_id=new_owner.id)
    if not is_in_team:
         raise HTTPException(status_code=400, detail="The new owner must be a member of the team.")

    updated_team = await crud.update_team_owner(db=db, team_id=str(team.id), user_id=current_user.id, new_owner=target_user)
    
    if not updated_team:
        raise HTTPException(status_code=404, detail="Team not found.")

    return {"message": "Team owner modified successfully."}

@router.delete("/{team_id}/leave/", status_code=status.HTTP_200_OK)
async def leave_team(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    成员离开团队。
    """
    if str(team.owner_id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team owner cannot leave the team."
        )
        
    success = await crud.remove_member_from_team(db=db, team_id=str(team.id), user_id=str(current_user.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to leave the team."
        )
        
    return {"message": "You have left the team successfully."}

@router.delete("/invitations/decline/", status_code=status.HTTP_200_OK)
async def decline_invitation(
    invite_data: schemas.InviteCode,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    拒绝团队邀请。
    """
    success = await crud.decline_team_invitation(db=db, invitation_code=str(invite_data.code))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found."
        )
    return {"message": "Team invitation declined successfully."}

@router.delete("/{team_id}/flow-sessions/delete/", status_code=status.HTTP_200_OK)
async def delete_flow_sessions(
    session_flow: schemas.Sessionflow_id,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    删除指定团队。只有团队所有者(Owner)才有权限执行此操作。
    """
    success = await crud.delete_session_flow(db=db, session_id=session_flow.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session flow delete error."
        )
    return {"message": "Session flow deleted successfully."}

@router.put("/{team_id}/flow-sessions/modify/", status_code=status.HTTP_200_OK)
async def modify_flow_session(
    session_flow: schemas.SessionModify,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    修改指定团队。只有团队所有者(Owner)才有权限执行此操作。
    """
    response = await crud.update_session_flow(db=db, session_flow=session_flow)
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="flow-session modified error."
        )
        
    return {"message": "flow-session modified successfully."}

@router.get("/{team_id}/chat/messages/", status_code=status.HTTP_200_OK)
async def get_chat_messages(
    before_msg_id: Optional[str] = Query(None, description="游標：當前列表最舊一條消息的ID"),
    after_msg_id: Optional[str] = Query(None, description="游標：當前列表最新一條消息的ID"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> List[schemas.TeamChat]:
    """4xm4
    獲取群組信息
    """
    messages = await crud.get_chat_messages(db=db, team_id=team.id, before_msg_id=before_msg_id, after_msg_id=after_msg_id)
    return messages

@router.post("/{team_id}/chat/post_messages/", status_code=status.HTTP_200_OK)
async def post_chat_messages(
    new_message: schemas.NewTeamChat,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) :
    """
    添加群組信息
    """
    messages = await crud.post_chat_messages(db=db, team_id=team.id, sender_id=current_user.id, content=new_message.content, tag=new_message.tag)
    if not messages:
        raise HTTPException(status_code=400, detail="Failed to post message.")
    return {"message": "Message posted successfully."}


@router.post("/{team_id}/chat/post_file/", status_code=status.HTTP_200_OK)
async def post_chat_file(
    file: UploadFile = File(...),
    tag: str = Form(...), 
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) :
    """
    添加群組信息
    """
    saved_file_path = await utils.save_raw_file(file, team.id)
    
    # 2. 寫入數據庫
    success = await crud.post_chat_messages(
        db=db, 
        team_id=team.id, 
        sender_id=current_user.id, 
        content=saved_file_path, 
        tag=tag   #前端會直接傳過來給我，不需要特殊判斷
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to save file record.")
        
    # 返回完整對象給前端 (這樣前端能立刻拿到 URL 顯示)
    return {"message": "File posted successfully."}

@router.delete("/{team_id}/chat/delete_messages/", status_code=status.HTTP_200_OK)
async def delete_chat_messages(
    delete_message: schemas.NewTeamChatID,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) :
    """
    刪除自己發的群組信息
    """
    success = await crud.delete_chat_messages(db=db, team_id=team.id, sender_id=current_user.id, message_id=delete_message.id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete message.")
    return {"message": "Message deleted successfully."}