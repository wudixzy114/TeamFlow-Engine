from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from ..core import schemas, models, crud
from ..core.dependencies import get_db, get_current_user, get_team_and_verify_membership

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_team(
    team_create: schemas.TeamCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    team = crud.create_team(db=db, team=team_create, owner=current_user)
    if not team:
        raise HTTPException(status_code=400, detail="Team creation failed")
    
    return {"message": "Team created successfully"}

@router.get("/", response_model=List[schemas.Team])
def list_my_teams(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    teams = crud.get_teams_for_user(db=db, user=current_user)
    return teams

@router.get("/{team_id}/members/", response_model=schemas.TeamMembersResponse)
def list_team_members(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db)
):
    team_details = crud.get_team_members(db=db, team_id=team.id)

    # 如果 crud 函數找不到 team，可能需要處理這種情況
    if not team_details:
        raise HTTPException(status_code=404, detail="Team not found")

    return team_details

@router.post("/{team_id}/invitations/", status_code=status.HTTP_201_CREATED)  #邀請成員加入
def invite_team(
    credential : schemas.EmailORUsername,
    team: models.Team = Depends(get_team_and_verify_membership), 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)   #這個user是邀請者
    
):
    user = crud.get_user_by_email(db, email=credential.email_username) or crud.get_user_by_username(db, username=credential.email_username)   #這個user是被邀請者
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")
    
    team = crud.get_team_for_user(db=db, team_id=team.id, user=current_user)
    if not team:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this team")
    
    #中間細節之後處裡
      # 4. 查找被邀請者
    invitee = crud.get_user_by_email(db, email=credential.email_username) or \
              crud.get_user_by_username(db, username=credential.email_username)
    
    if not invitee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to invite not found")

    # 5. 防止邀請自己
    if invitee.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot invite yourself")

    # 6. 檢查是否已是成員或已被邀請
    if crud.is_user_in_team(db=db, team_id=team.id, user_id=invitee.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this team")

    if crud.has_pending_invitation(db=db, team_id=team.id, invitee_email=invitee.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user already has a pending invitation")

    # 7. 創建邀請 (注意傳遞的參數)
    response = crud.create_invitation(db=db, team_id=team.id, inviter_id=current_user.id, invitee_email=invitee.email)
    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create invitation")
    
    return {"message": "The invitation has been sent successfully."}

@router.post("/invitations/accept/", status_code=status.HTTP_200_OK)
def accept_invite(
    invite_data: schemas.InviteCode,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 步驟 1: 驗證邀請碼是否有效且屬於當前用戶
    invitation = crud.get_valid_invitation_by_code(
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
    joined_team = crud.accept_invitation_and_join_team(
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
def create_team_checkin(
    checkin: schemas.CheckinCreate,
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入來驗證團隊成員身份
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. 檢查今天是否已經簽到，防止重複提交
    if crud.has_checked_in_today(db=db, user_id=current_user.id, team_id=team.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already checked in for this team today."
        )

    # 2. 創建簽到記錄
    # 注意：將 crud 函數的參數名從 'current_user' 改為 'user' 以匹配其定義
    create = crud.checkin_create(db=db, checkin=checkin, team_id=team.id, user=current_user)
    if not create:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create check-in record."
        )
        
    return {"message": "Check-in successful."}

@router.get("/{team_id}/checkins/today/", status_code=status.HTTP_200_OK)
def get_today_checkin_status(
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: Session = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
):
    # 1. 調用修正後的 CRUD 函數
    has_checked_in = crud.has_checked_in_today(db=db, user_id=current_user.id, team_id=team.id)
    
    # 2. 按照 Pydantic 模型和 OpenAPI 文件返回結果
    return {"has_checked_in": has_checked_in}

@router.get("/{team_id}/highlights/", response_model=List[schemas.Highlight])
def get_highlights(
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: Session = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
):
    return crud.get_highlights(db=db, user_id=current_user.id, team_id=team.id)

@router.post("/{team_id}/highlights/", status_code=status.HTTP_201_CREATED)
def post_highlights(
    highlights: schemas.HighlightBase,
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: Session = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
):
    high_lights = crud.post_highlights(db=db, user_id=current_user.id, team_id=team.id, highlights = highlights.content)
    if not high_lights:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create highlights")
    
    return {"message": "发布成功"}

@router.put("/{team_id}/highlights/modify/", status_code=status.HTTP_200_OK)
def modify_highlight(
    highlight_data: schemas.HighlightModify,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    修改指定的高光时刻。只有创建者本人才能修改。
    """
    highlight = crud.get_highlight(db, highlight_id=highlight_data.id)
    if not highlight or str(highlight.team_id) != str(team.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Highlight not found in this team.")

    if str(highlight.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can modify this highlight.")

    updated_highlight = crud.update_highlight(db, highlight_id=highlight_data.id, content=highlight_data.content)
    if not updated_highlight:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update highlight.")

    return {"message": "Highlight modified successfully."}

@router.delete("/{team_id}/highlights/delete/", status_code=status.HTTP_200_OK)
def delete_highlight(
    highlight_data: schemas.HighlightId,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    删除指定的高光时刻。创建者本人或团队所有者可以删除。
    """
    highlight = crud.get_highlight(db, highlight_id=highlight_data.id)
    if not highlight or str(highlight.team_id) != str(team.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Highlight not found in this team.")

    is_author = str(highlight.user_id) == str(current_user.id)
    is_owner = str(team.owner_id) == str(current_user.id)

    if not is_author and not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this highlight.")

    success = crud.delete_highlight(db, highlight_id=highlight_data.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete highlight.")

    return {"message": "Highlight deleted successfully."}


@router.post("/{team_id}/flow-sessions/", status_code=status.HTTP_201_CREATED)
def post_flow_sessions(
    flow_sessions: schemas.FlowSessionCreate,
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: Session = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
): 
    response = crud.post_flow_sessions(db=db, user_id=current_user.id, team_id=team.id, flow_sessions=flow_sessions)
    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create flow sessions")

    return {"message": "记录成功"}

@router.get("/{team_id}/flow-sessions/", response_model=List[schemas.ReturnFlowSession])
def get_flow_sessions(
    team: models.Team = Depends(get_team_and_verify_membership), # 使用依賴注入驗證團隊成員
    db: Session = Depends(get_db),  
    current_user: models.User = Depends(get_current_user)  
): 
    return crud.get_flow_sessions(db=db, user_id=current_user.id, team_id=team.id)

@router.post("/{team_id}/kudos/", status_code=status.HTTP_201_CREATED, tags=["Recognition"])
def send_kudos(  
    kudos_data: schemas.KudosCreate,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    team = crud.get_team_for_user(db=db, team_id=team.id, user=current_user)
    if not team:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this team")

    receiver = crud.get_user(db=db, user_id=kudos_data.receiver_id)
    if not receiver or not crud.is_user_in_team(db=db, team_id=team.id, user_id=receiver.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found in this team")

    response = crud.create_kudos(db=db, kudos_data=kudos_data, sender_id=current_user.id, team_id=team.id)
    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to send kudos")
    
    return {"message": "Kudos sent successfully."}

@router.get("/{team_id}/charter/",response_model=schemas.Charter,tags=["Culture & Growth"],summary="获取团队心流公约")
def get_charter(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db)
):
    """获取指定团队的心流公约。如果不存在，则会返回一个默认的空公约。"""
    return crud.get_charter_for_team(db=db, team_id=str(team.id))

@router.put("/{team_id}/charter/",tags=["Culture & Growth"],summary="更新团队心流公约 (管理员)")
def update_charter(
    charter_data: schemas.CharterUpdate,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
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
        
    response = crud.update_charter_for_team(db=db,team_id=str(team.id),user_id=str(current_user.id),content=charter_data.content)
    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update charter")
    return {"message": "Charter updated successfully."}

@router.delete("/{team_id}/delete-charter/", status_code=status.HTTP_200_OK, tags=["Culture & Growth"], summary="删除团队心流公约 (管理员)")
def delete_charter(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
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

    success = crud.delete_charter_for_team(db=db, team_id=str(team.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charter not found or could not be deleted."
        )
        
    return {"message": "Charter deleted successfully."}


@router.get("/{team_id}/skill-tree/",response_model=schemas.SkillTreeData,tags=["Culture & Growth"],summary="获取团队技能树数据")
def get_skill_tree(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db)
):
    """
    根据团队成员的签到数据，动态生成技能树。
    技能来源于成员在签到时填写的'成就'，并按成员进行分组。
    """
    return crud.get_skill_tree_for_team(db=db, team_id=str(team.id))

@router.delete("/{team_id}/delete/", status_code=status.HTTP_200_OK)
def delete_team(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
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

    success = crud.delete_team(db=db, team_id=str(team.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete the team."
        )
        
    return {"message": "Team deleted successfully."}

@router.delete("/{team_id}/kick/",status_code=status.HTTP_200_OK) 
def kick_member(
    member_id: schemas.KickMember,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    将指定成员从团队中移除。只有团队所有者(Owner)才有权限执行此操作。
    """
    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can remove members."
        )

    if str(member_id.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team owner cannot remove themselves."
        )

    member = crud.get_user(db=db, user_id=member_id.id)
    if not member or not crud.is_user_in_team(db=db, team_id=str(team.id), user_id=member_id.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this team."
        )

    sucess = crud.remove_member_from_team(db=db, team_id=str(team.id), user_id=str(member_id.id))
    if not sucess:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove member from team."
        )
        
    return {"message": "Member removed successfully."}

@router.put("/{team_id}/modify/", status_code=status.HTTP_200_OK) 
def modify_team(
    team_name: schemas.Teamname,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
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
    team = crud.update_team(db=db, team_id=str(team.id), name=team_name.name)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found."
        )
    return {"message": "Team modified successfully."}

@router.put("/{team_id}/modify_owner/", status_code=status.HTTP_200_OK)
def modify_team_owner(
    new_owner: schemas.TeamOwner,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    修改指定团队的所有者。只有团队所有者(Owner)才有权限执行此操作。
    """
    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can modify the team owner."
        )
    
    if str(new_owner.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New owner cannot be the same as the current owner."
        )

    now_owner = crud.get_user(db=db, user_id=new_owner.id)
    if not now_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New owner not found."
        )

    team = crud.update_team_owner(db=db, team_id=str(team.id), new_owner =now_owner )
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found."
        )

    return {"message": "Team owner modified successfully."}

@router.delete("/{team_id}/leave/", status_code=status.HTTP_200_OK)
def leave_team(
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
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
        
    success = crud.remove_member_from_team(db=db, team_id=str(team.id), user_id=str(current_user.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to leave the team."
        )
        
    return {"message": "You have left the team successfully."}

@router.delete("/invitations/decline/", status_code=status.HTTP_200_OK)
def decline_invitation(
    invite_data: schemas.InviteCode,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    拒绝团队邀请。
    """
    success = crud.decline_team_invitation(db=db, invitation_code=str(invite_data.code))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found."
        )
    return {"message": "Team invitation declined successfully."}

@router.delete("/{team_id}/flow-sessions/delete/", status_code=status.HTTP_200_OK)
def delete_team(
    session_flow: schemas.Sessionflow_id,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    删除指定团队。只有团队所有者(Owner)才有权限执行此操作。
    """
    success = crud.delete_session_flow(db=db, session_id=session_flow.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session flow delete error."
        )
    return {"message": "Session flow deleted successfully."}

@router.put("/{team_id}/flow-sessions/modify/", status_code=status.HTTP_200_OK)
def modify_team(
    session_flow: schemas.SessionModify,
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    修改指定团队。只有团队所有者(Owner)才有权限执行此操作。
    """
    response = crud.update_session_flow(db=db, session_flow=session_flow)
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="flow-session modified error."
        )
        
    return {"message": "flow-session modified successfully."}

