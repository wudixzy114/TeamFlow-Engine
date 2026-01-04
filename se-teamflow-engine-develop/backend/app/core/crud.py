from sqlalchemy.orm import Session, joinedload, load_only
import asyncio
import functools
from sqlalchemy import func, case
from sqlalchemy.exc import IntegrityError
from concurrent.futures import ThreadPoolExecutor
from datetime import date as dt_date
# from uuid import UUID
import asyncio
from . import models, schemas
from . import utils
from .security import get_password_hash
from typing import Any, Dict, Literal, List, Tuple, Set , Optional
from collections import Counter
import re
import jieba
from pathlib import Path
from sqlalchemy import select, update, delete, insert, and_, or_, literal, cast, Date
import logging
from sqlalchemy import func
from datetime import date, datetime, timedelta # 確保導入了 date 和 timedelta
import secrets
import string
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from .models import team_members_table, china_now 
from sqlalchemy.exc import SQLAlchemyError

_executor = ThreadPoolExecutor()

async def run_in_executor(func, *args, **kwargs):
    """輔助函數：將同步函數丟入線程池執行"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, functools.partial(func, *args, **kwargs))

PeriodLiteral = Literal["day", "week", "month"]
logger = logging.getLogger(__name__)

# --- User CRUD ---

async def get_user_basic(db: AsyncSession, user_id: str):
    return await db.get(models.User, user_id)
    
async def get_user(db: AsyncSession, user_id: str):
    query = select(models.User).options(selectinload(models.User.teams)).where(models.User.id == user_id)  #
    result = await db.execute(query)
    return result.scalars().first()

async def user_exist(db: AsyncSession, username: str) -> bool:   # bool
    query = select(literal(1)).where(models.User.username == username).limit(1)
    result = await db.execute(query)
    return result.first() is not None

async def get_user_by_email(db: AsyncSession, email: str) -> models.User | None:
    query = select(models.User).where(models.User.email == email)
    result = await db.execute(query)
    return result.scalars().first()

async def get_user_by_email_or_username(db: AsyncSession, email_or_username: str) -> models.User | None:    
    query = select(models.User).where(
        or_(
            models.User.email == email_or_username,
            models.User.username == email_or_username
        )
    )
    result = await db.execute(query)
    return result.scalars().first()

async def get_user_by_username(db: AsyncSession, username: str) -> models.User | None:
    query = select(models.User).where(models.User.username == username)
    result = await db.execute(query)
    return result.scalars().first()

async def create_user(db: AsyncSession, username: str, email: str, hashed_password: str, gender: str, nickname: str, age: str, profession: str) -> bool:
    db_user = models.User(email=email, hashed_password=hashed_password, username=username, gender=gender, nickname=nickname, age=age, profession=profession)
    db.add(db_user)
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False
    # return db_user

async def create_team(db: AsyncSession, team: schemas.TeamCreate, owner: models.User) -> bool:
    """
    創建一個新的團隊。
    - team: 包含團隊名稱的 Pydantic 模型。
    - owner: 創建此團隊的用戶，他將成為 owner 和第一個成員。
    """
    db_team = models.Team(name=team.name, owner_id=owner.id)
    db_team.members.append(owner)
    
    # 預先創建一個空的 Charter，避免後續查詢時的併發寫入問題
    db_charter = models.Charter(team=db_team, content="")
    db.add(db_charter)
    
    db.add(db_team)
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False
    # return db_team

# 【新增】一個函數來獲取用戶加入的所有團隊
async def get_teams_for_user(db: AsyncSession, user: models.User) -> List[models.Team]:
    """
    查詢並返回指定用戶作為成員的所有團隊列表。
    """
    query = select(models.Team).where(models.Team.members.any(id=user.id)).options(selectinload(models.Team.owner)) #,selectinload(models.Team.members)
    result = await db.execute(query)
    return result.scalars().all()

async def update_user_email(db: AsyncSession, user_id: str, new_email: str) -> bool:
    """
    更新指定用户的邮箱地址。
    """
    user = await db.get(models.User, user_id)

    if user:
        user.email = new_email
        db.add(user) 
        try:
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            return False
    return False

# --- Team CRUD (IDOR 防護關鍵) ---
async def get_team_for_user(db: AsyncSession, team_id: str, user: models.User) -> models.Team | None:
    stmt = (
        select(models.Team)
        .join(models.team_members_table) 
        .where(
            models.Team.id == team_id,
            models.team_members_table.c.user_id == user.id
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first()

# --- Dashboard CRUD ---
async def get_team_compass_data(db: AsyncSession, team_id: str, period: PeriodLiteral) -> Dict[str, Any]:
    """
    依据团队与周期返回情绪罗盘数据。
    将情绪分类与趋势聚合逻辑放到 utils 中。
    """
    start_date = utils.get_start_date(period)

    # 優化：只選取需要的欄位
    query = select(models.Checkin).options(
        load_only(
            models.Checkin.challenge_level, 
            models.Checkin.skill_level, 
            models.Checkin.created_at
        )
    ).where(
        models.Checkin.team_id == team_id,
        models.Checkin.created_at >= start_date
    )
    
    result = await db.execute(query)
    checkins = result.scalars().all()

    # 聚合邏輯 (Python 端計算，但因為數據量已瘦身，速度很快)
    emotion_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for c in checkins:
        emo = utils.classify_emotion(c)
        emotion_counts[emo] = emotion_counts.get(emo, 0) + 1

    total_checkins = sum(emotion_counts.values())
    distribution = {
        "positive": (emotion_counts["positive"] / total_checkins) * 100 if total_checkins else 0,
        "neutral": (emotion_counts["neutral"] / total_checkins) * 100 if total_checkins else 0,
        "negative": (emotion_counts["negative"] / total_checkins) * 100 if total_checkins else 0,
    }

    trend_data = utils.aggregate_trend_by_date(checkins)

    return {
        "period": period,
        "distribution": distribution,
        "trend_data": trend_data,
    }

async def get_team_focus_time_data(db: AsyncSession, team_id: str, period: PeriodLiteral) -> Dict[str, Any]:
    """
    异步：依据团队与周期返回专注时长数据（小时）和每日趋势。
    """
    start_date = utils.get_start_date(period)

    query = select(
        func.date(models.FlowSession.start_time).label("date"),
        func.sum(models.FlowSession.duration_minutes).label("total_minutes"),
    ).where(
        models.FlowSession.team_id == team_id,
        models.FlowSession.start_time >= start_date
    ).group_by(func.date(models.FlowSession.start_time)).order_by(func.date(models.FlowSession.start_time))

    result = await db.execute(query)
    rows = result.all()

    daily_trend = [{"date": row.date, "hours": round((row.total_minutes or 0) / 60, 2)} for row in rows]
    total_minutes = sum(row.total_minutes or 0 for row in rows)

    return {
        "period": period,
        "total_hours": round(total_minutes / 60, 2),
        "daily_trend": daily_trend,
    }

async def get_team_insights_data(db: AsyncSession, team_id: str, period: PeriodLiteral) -> Dict[str, List[Dict[str, Any]]]:
    """
    异步：获取团队签到文本并生成词云（使用 utils.generate_wordcloud）。
    """
    start_date = utils.get_start_date(period)

    query = select(models.Checkin.achievement_text, models.Checkin.obstacle_text).where(
        models.Checkin.team_id == team_id,
        models.Checkin.created_at >= start_date
    )
    result = await db.execute(query)
    rows = result.all()

    boosters = [r.achievement_text for r in rows if r.achievement_text]
    blockers = [r.obstacle_text for r in rows if r.obstacle_text]

    boosters_wordcloud, blockers_wordcloud = await asyncio.gather(
        utils.generate_wordcloud(boosters),
        utils.generate_wordcloud(blockers)
    )

    return {
        "boosters_wordcloud": boosters_wordcloud,
        "blockers_wordcloud": blockers_wordcloud,
    }

# --- Recognition (Highlight, Like) CRUD ---

async def get_highlight(db: AsyncSession, highlight_id: str) -> models.Highlight | None:
    """通过ID获取单个高光时刻。"""
    query = select (models.Highlight).where(models.Highlight.id == highlight_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def like_highlight(db: AsyncSession, highlight_id: str, user_id: str) -> models.Like | None:
    """为一个高光时刻创建一条'赞'的记录。"""
    try:
        db_like = models.Like(highlight_id=highlight_id, user_id=user_id)
        db.add(db_like)
        await db.commit()
        return db_like
    except IntegrityError:
        await db.rollback()
        return None

async def unlike_highlight(db: AsyncSession, highlight_id: str, user_id: str) -> bool: # 更名
    """移除一个高光时刻的'赞'。"""
    query = delete(models.Like).where(models.Like.highlight_id == highlight_id, models.Like.user_id == user_id)
    result = await db.execute(query)
    await db.commit()
    
    return result.rowcount > 0
        
# --- "Me" (Current User) CRUD ---

async def list_received_kudos_for_user(db: AsyncSession, user_id: str) -> List[models.Kudos]:
    """获取指定用户收到的所有 Kudos。"""
    query = (
        select(models.Kudos)
        .where(models.Kudos.receiver_id == user_id)
        .options(selectinload(models.Kudos.sender))
        .order_by(models.Kudos.created_at.desc())
    )
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_user_weekly_digest(db: AsyncSession, user_id: str, query_date: date) -> Dict[str, Any]:
    """
    为指定用户生成周报数据（DB 操作使用 AsyncSession；文本/情绪/趋势的纯逻辑放在 utils 中）。
    """
    start_of_week = query_date - timedelta(days=query_date.weekday())
    end_of_week = start_of_week + timedelta(days=7)

    # 1. 構建查詢 (不立即執行)
    # 優化: SQL 聚合 Sum
    query_focus = select(func.sum(models.FlowSession.duration_minutes)).where(
        models.FlowSession.user_id == user_id,
        models.FlowSession.start_time >= start_of_week,
        models.FlowSession.start_time < end_of_week,
    )

    # 優化: SQL 聚合 Count
    query_kudos = select(func.count(models.Kudos.id)).where(
        models.Kudos.receiver_id == user_id,
        models.Kudos.created_at >= start_of_week,
        models.Kudos.created_at < end_of_week,
    )

    # 獲取 Checkins 用於分析 (依然需要 raw data，但使用 load_only 優化 IO)
    query_checkins = select(models.Checkin).options(
        load_only(
            models.Checkin.achievement_text, 
            models.Checkin.obstacle_text, 
            models.Checkin.challenge_level, 
            models.Checkin.skill_level,
            models.Checkin.created_at
        )
    ).where(
        models.Checkin.user_id == user_id,
        models.Checkin.created_at >= start_of_week,
        models.Checkin.created_at < end_of_week,
    )

    # 2. 【優化 4】並行執行所有 DB 查詢
    res_focus, res_kudos, res_checkins = await asyncio.gather(
        db.execute(query_focus),
        db.execute(query_kudos),
        db.execute(query_checkins)
    )

    # 3. 提取結果
    total_focus_minutes = res_focus.scalar() or 0
    kudos_received_count = res_kudos.scalar() or 0
    checkins = res_checkins.scalars().all()

    # 4. 數據處理 (詞雲部分丟入線程池)
    boosters_texts = [c.achievement_text for c in checkins if c.achievement_text]
    blockers_texts = [c.obstacle_text for c in checkins if c.obstacle_text]

    # 並行生成詞雲
    top_booster_list, top_blocker_list = await asyncio.gather(
        utils.generate_wordcloud(boosters_texts),
        utils.generate_wordcloud(blockers_texts)
    )

    top_booster_str = top_booster_list[0]["name"] if top_booster_list else ""
    top_blocker_str = top_blocker_list[0]["name"] if top_blocker_list else ""

    # 5. 情緒與趨勢計算 (Python 內存操作，速度快)
    emotion_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for c in checkins:
        emo = utils.classify_emotion(c)
        emotion_counts[emo] = emotion_counts.get(emo, 0) + 1

    total_checkins = sum(emotion_counts.values())
    distribution = {
        emotion: (count / total_checkins) * 100 if total_checkins else 0
        for emotion, count in emotion_counts.items()
    }

    trend_data = utils.aggregate_trend_by_date(checkins)

    mindset_trend = {
        "period": "week",
        "distribution": {
            "positive": distribution.get("positive", 0),
            "neutral": distribution.get("neutral", 0),
            "negative": distribution.get("negative", 0),
        },
        "trend_data": trend_data,
    }

    return {
        "week_range": {"start": start_of_week, "end": end_of_week - timedelta(days=1)},
        "mindset_trend": mindset_trend,
        "total_focus_hours": round(total_focus_minutes / 60, 2),
        "top_booster": top_booster_str,  
        "top_blocker": top_blocker_str,
        "kudos_received": kudos_received_count,
    }

async def create_invitation(db: AsyncSession, team_id: str, inviter_id: str, invitee_email: str) -> bool:
    # 1. 生成一個唯一的邀請碼
    # (在一個高併發的系統中，這裡需要一個迴圈來確保 code 的唯一性，但目前這樣可以)
    invite_code = utils.generate_invite_code()
    
    db_invitation = models.Invitation(team_id=team_id,inviter_id=inviter_id,invitee_email=invitee_email,invite_code=invite_code)
    db.add(db_invitation)
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False

async def is_user_in_team(db: AsyncSession, team_id: str, user_id: str) -> bool:
    stmt = select(models.team_members_table.c.team_id).where(
        models.team_members_table.c.team_id == team_id,
        models.team_members_table.c.user_id == user_id
    ).limit(1)
    
    result = await db.scalar(stmt)
    return result is not None

async def has_pending_invitation(db: AsyncSession, team_id: str, invitee_email: str) -> bool:
    query = select(literal(1)).where(
        models.Invitation.team_id == team_id,
        models.Invitation.invitee_email == invitee_email,
        models.Invitation.status == "pending"
    ).limit(1)
    result = await db.execute(query)
    return result.first() is not None
    
async def get_valid_invitation_by_code(db: AsyncSession, invite_code: str, current_user_email: str) -> models.Invitation | None:
    """
    根據邀請碼查找一個處於 'pending' 狀態的邀請。
    關鍵安全檢查：同時驗證該邀請的目標 email 是否與當前用戶的 email 匹配。
    """
    query = select(models.Invitation).where(
        models.Invitation.invite_code == invite_code,
        models.Invitation.invitee_email == current_user_email,
        models.Invitation.status == "pending"
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def accept_invitation_and_join_team(db: AsyncSession, invitation: models.Invitation, user: models.User) -> models.Team | None:    #這個也改過
    """
    處理接受邀請的完整資料庫事務。
    1. 查找邀請對應的團隊。
    2. 檢查用戶是否已是成員。
    3. 如果檢查通過，將用戶加入團隊並刪除邀請。
    4. 返回加入的團隊物件，如果失敗則返回 None。
    """
    team = await db.get(models.Team, invitation.team_id)
    if not team or await is_user_in_team(db=db, team_id=str(team.id), user_id=str(user.id)):
        return None

    stmt = insert(team_members_table).values(
        user_id=user.id,
        team_id=team.id
    )
    await db.execute(stmt)
    
    new_message = models.Message(
        content=f"{user.username} 已加入團隊", 
        receiver_id=team.owner_id
    )
    db.add(new_message)
    await db.delete(invitation)
    await db.commit()
    return team

# 【已修正】 創建一個新的簽到記錄
async def checkin_create(db: AsyncSession, checkin: schemas.CheckinCreate, team_id: str, user: models.User) -> bool:
    """
    為指定用戶和團隊創建一條新的簽到記錄。
    """
    db_checkin = models.Checkin(
        user_id=user.id,
        team_id=team_id,
        challenge_level=checkin.challenge_level,
        skill_level=checkin.skill_level,
        achievement_text=checkin.achievement_text,
        obstacle_text=checkin.obstacle_text
    )
    db.add(db_checkin)
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False

# 【已修正】 判斷用戶今天是否已經在某個團隊簽到
async def has_checked_in_today(db: AsyncSession, user_id: str, team_id: str) -> bool:
    now_china = china_now() 
    today = now_china.date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)

    query = select(models.Checkin).where(
        models.Checkin.user_id == user_id,
        models.Checkin.team_id == team_id,
        models.Checkin.created_at >= start_of_day,
        models.Checkin.created_at < end_of_day
    )
    
    result = await db.execute(query)
    return result.scalars().first() is not None
    
async def get_highlights_data( db: AsyncSession, user_id: str, team_id: str) -> Tuple[List[models.Highlight], Set[str]]: 
    """
    (數據層) 獲取團隊高光時刻列表，以及當前用戶的點讚ID集合。
    """
    highlights_query = (
        select(models.Highlight)
        .options(
            selectinload(models.Highlight.user),
            selectinload(models.Highlight.likes)
        )
        .where(models.Highlight.team_id == team_id)
        .order_by(models.Highlight.created_at.desc())
    )
    highlights_result = await db.execute(highlights_query)
    team_highlights = highlights_result.scalars().all()

    if not team_highlights:
        return [], set()

    # 2. 計算點讚 (這部分邏輯保持不變，安全可靠)
    highlight_ids = [h.id for h in team_highlights]
    likes_query = select(models.Like.highlight_id).where(
        models.Like.user_id == user_id,
        models.Like.highlight_id.in_(highlight_ids)
    )
    likes_result = await db.execute(likes_query)
    liked_highlight_ids = set(likes_result.scalars().all())
    
    return team_highlights, liked_highlight_ids

async def post_highlights(db: AsyncSession, user_id: str, team_id: str, highlights: str) -> bool:
    new_highlight = models.Highlight(user_id=user_id, team_id=team_id, content=highlights)
    db.add(new_highlight)

    sender_result = await db.execute(select(models.User).where(models.User.id == user_id))
    sender = sender_result.scalar_one() # 假設 user_id 一定存在

    stmt = (
        select(models.User)
        .join(models.team_members_table)
        .where(
            and_(
                models.team_members_table.c.team_id == team_id,
                models.User.id != user_id  # SQL 層面直接排除自己
            )
        )
    )
    result = await db.execute(stmt)
    members_to_notify = result.scalars().all()
    dissolve_messages = [
        models.TeamMessage(
            content=f"{sender.username} send a new highlight", 
            receiver_id=member.id,
            team_id=team_id,
            tag="highlights"
        ) for member in members_to_notify
    ]

    if dissolve_messages:
        db.add_all(dissolve_messages)
    
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False

async def update_highlight(db: AsyncSession, highlight_id: str, user_id: str, team_id: str, content: str) -> bool:
    """
    安全的更新高光時刻。
    利用 SQL 的 WHERE 條件同時檢查：
    1. ID 是否存在
    2. 是否屬於該用戶 (user_id)
    3. 是否屬於該團隊 (team_id)
    """
    stmt = (
        update(models.Highlight)
        .where(models.Highlight.id == highlight_id)
        .where(models.Highlight.user_id == user_id)  # 權限鎖：只有作者能改
        .where(models.Highlight.team_id == team_id)  # 範圍鎖：確保在當前團隊
        .values(content=content)
    )
    
    result = await db.execute(stmt)
    await db.commit()

    return result.rowcount > 0

async def delete_highlight(db: AsyncSession, highlight_id: str, team_id: str, user_id: str, is_team_owner: bool) -> bool:
    """
    安全刪除：
    - 如果是 Owner (is_team_owner=True)：只要 ID 和 TeamID 對上就能刪。
    - 如果是 成員 (is_team_owner=False)：除了 ID 和 TeamID，還必須 user_id 匹配 (只能刪自己的)。
    """
    stmt = delete(models.Highlight).where(
        models.Highlight.id == highlight_id,
        models.Highlight.team_id == team_id
    )

    if not is_team_owner:
        stmt = stmt.where(models.Highlight.user_id == user_id)

    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

async def post_flow_sessions(db: AsyncSession, user_id: str, team_id: str, flow_sessions: schemas.FlowSessionCreate) -> bool:
    
    submit_time = utils.to_china_naive(flow_sessions.start_time)
    new_flow_session = models.FlowSession(
        user_id=user_id, 
        team_id=team_id, 
        start_time=submit_time, 
        duration_minutes=flow_sessions.duration_minutes, 
        task_description=flow_sessions.task_description
    )
    
    db.add(new_flow_session)
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False
    
    # return new_flow_session
        
async def get_flow_sessions(db: AsyncSession, user_id: str, team_id: str, skip: int = 0, limit: int = 50) -> List[models.FlowSession]:   #應該是全部都要
    query = (select(models.FlowSession).where(models.FlowSession.user_id == user_id,models.FlowSession.team_id == team_id)).order_by(models.FlowSession.start_time.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_flow_sessions_bydate(db: AsyncSession, user_id: str, team_id: str, date: dt_date, skip: int = 0, limit: int = 50) -> List[models.FlowSession]:   #應該是全部都要
    query = (select(models.FlowSession).where(models.FlowSession.user_id == user_id,models.FlowSession.team_id == team_id, cast(models.FlowSession.start_time, Date) == date)).order_by(models.FlowSession.start_time.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
    
async def get_user_all_invite(db: AsyncSession, user_email: str) -> List[Tuple[models.Invitation, str, str]]:   #"""獲取用戶所有發出的邀請"""
    query = (
        select(
            models.Invitation,
            models.Team.name.label("team_name"),
            models.User.username.label("inviter_username")
        )
        .join(models.Team, models.Invitation.team_id == models.Team.id)
        .join(models.User, models.Invitation.inviter_id == models.User.id)
        .where(models.Invitation.invitee_email == user_email)
    )
    
    result = await db.execute(query)
    return result.all()

async def create_kudos(db: AsyncSession, kudos_data: schemas.KudosCreate, sender_id: str, team_id: str) -> bool:
    """创建一条新的 Kudos 记录。"""
    db_kudos = models.Kudos(**kudos_data.model_dump(),sender_id=sender_id,team_id=team_id)
    db.add(db_kudos)
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False
# --- Culture & Growth (Charter, SkillTree) CRUD ---

async def get_charter_for_team(db: AsyncSession, team_id: str) -> models.Charter:
    """
    获取团队的心流公约。如果不存在，则在数据库中创建一个并返回。
    """
    query = select(models.Charter).options(selectinload(models.Charter.last_updated_by)).where(models.Charter.team_id == team_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def update_charter_for_team(db: AsyncSession, team_id: str, user_id: str, content: str) -> models.Charter|None:
    """
    更新指定团队的心流公约内容。
    """
    stmt = (
        update(models.Charter)
        .where(models.Charter.team_id == team_id)
        .values(
            content=content,
            last_updated_by_id=user_id,
            updated_at=datetime.utcnow()
        )
    )
    result = await db.execute(stmt)
    if result.rowcount == 0:
        return None

    members_stmt = (
        select(models.team_members_table.c.user_id)
        .where(
            and_(
                models.team_members_table.c.team_id == team_id,
                models.team_members_table.c.user_id != user_id # 排除自己
            )
        )
    )
    
    members_result = await db.execute(members_stmt)
    receiver_ids = members_result.scalars().all()

    if receiver_ids:
        new_messages = [
            models.TeamMessage(
                team_id=team_id,
                receiver_id=mid,  # 假設你的 TeamMessage 用的是 receiver_id
                content="團隊公約已更新!", 
                tag="charter"
            ) for mid in receiver_ids
        ]
        db.add_all(new_messages)

    await db.commit()
    return await get_charter_for_team(db, team_id)

async def delete_charter_for_team(db: AsyncSession, team_id: str) -> bool:
    """
    删除指定团队的心流公约。
    """
    stmt = (
        update(models.Charter)
        .where(models.Charter.team_id == team_id)
        .values(
            content="",           
            last_updated_by_id=None, 
            updated_at=datetime.utcnow()
        )
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

async def get_skill_tree_for_team(db: AsyncSession, team_id: str) -> Dict[str, Any]:
    """
    获取团队技能树。
    """
    # 步骤 1: 获取团队所有成员
    stmt_members = (
        select(models.User)
        .join(models.team_members_table)
        .where(models.team_members_table.c.team_id == team_id)
    )
    members_res = await db.execute(stmt_members)
    members = members_res.scalars().all()

    # 初始化成员节点 Map
    members_node_map = {}
    for m in members:
        u_name = m.username
        u_nickname = m.nickname if m.nickname else u_name
        members_node_map[m.id] = {
            "id": m.id,
            "name": u_nickname,
            "type": "USER",
            "children": []
        }

    # 步骤 2: 获取所有技能数据
    stmt_skills = select(models.TeamSkill).where(models.TeamSkill.team_id == team_id)
    skills_res = await db.execute(stmt_skills)
    all_skills = skills_res.scalars().all()

    # 临时 Map 用于组装技能树，Key 是 TeamSkill.id
    skill_node_map = {}
    for skill in all_skills:
        skill_node_map[skill.id] = {
            "id": skill.id, 
            "name": skill.name, 
            "value": 1,
            "meta_data": skill.meta_data if skill.meta_data else {},
            "type": "SKILL",
            "_user_id": skill.user_id,
            "_parent_id": skill.parent_id,
            "children": []
        }

    root_children = [] 

    # 步骤 3: 组装树结构
    for skill_id, node in skill_node_map.items():
        parent_id = node["_parent_id"]
        user_id = node["_user_id"]

        if parent_id and parent_id in skill_node_map:
            skill_node_map[parent_id]["children"].append(node)
        else:
            if user_id and user_id in members_node_map:
                members_node_map[user_id]["children"].append(node)
            elif user_id is None:
                root_children.append(node)

    # 步骤 4: 清理辅助字段
    for node in skill_node_map.values():
        node.pop("_user_id", None)
        node.pop("_parent_id", None)

    # 步骤 5: 合并结果 (将成员节点加入根列表)
    root_children.extend(list(members_node_map.values()))

    return {"name": "团队技能树", "children": root_children}

async def update_user_password(db: AsyncSession, user: models.User, new_password_hash: str) -> models.User:
    """
    更新指定用户的密码哈希值。
    """
    user.hashed_password = new_password_hash
    db.add(user)
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False

async def get_team_members(db: AsyncSession, team_id: str) -> Dict[str, Any] | None:
    """
    获取团队的 owner 和 members 列表。
    """
    query = (
        select(models.Team)
        .where(models.Team.id == team_id)
        .options(
            selectinload(models.Team.owner),      # 預載入 owner
            selectinload(models.Team.members)     # 預載入 members
        )
    )
    
    result = await db.execute(query)
    team = result.scalar_one_or_none()
    if not team:
        return None
    return {"owner": team.owner, "members": team.members}

async def update_user_info(db: AsyncSession, user_id: str, nickname: str, age: str, profession: str, gender: str, username: str) -> bool:
    """
    更新指定用户的个人信息。
    """
    user = await db.get(models.User, user_id)

    if not user:
        return None
    
    # 2. 逐一更新欄位，這部分邏輯與同步版本完全相同
    if age:
        user.age = age
    if nickname:
        user.nickname = nickname
    if profession:
        user.profession = profession
    if gender:
        user.gender = gender
    if username:
        user.username = username
        
    # 3. 添加到會話 (好習慣)，並異步提交和刷新
    db.add(user)
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False

async def delete_team(db: AsyncSession, team_id: str) -> bool: 
    """
    删除指定团队。
    """
    query = select(models.Team).options(selectinload(models.Team.members)).where(models.Team.id == team_id)
    result = await db.execute(query)
    team_to_delete = result.scalar_one_or_none()

    if not team_to_delete:
        return False
    
    team_name = team_to_delete.name
    members = team_to_delete.members
    
    dissolve_messages = [
        models.Message(
            content=f"群組 {team_name} 已解散", 
            receiver_id=member.id
        ) for member in members
    ]

    if dissolve_messages:
        db.add_all(dissolve_messages)

    await db.delete(team_to_delete)
    await db.commit()
    return True

async def remove_member_from_team(db: AsyncSession, team_id: str, user_id: str) -> bool:
    """
    从指定团队中移除指定成员，并并行清理该成员在该团队中的所有关联数据。
    """
    team = await db.get(models.Team, team_id)
    if not team:
        return False

    await db.execute(delete(models.Checkin).where(
        models.Checkin.user_id == user_id, 
        models.Checkin.team_id == team_id
    ))
    
    await db.execute(delete(models.FlowSession).where(
        models.FlowSession.user_id == user_id, 
        models.FlowSession.team_id == team_id
    ))
    
    await db.execute(delete(models.Highlight).where(
        models.Highlight.user_id == user_id, 
        models.Highlight.team_id == team_id
    ))
    
    await db.execute(delete(models.Kudos).where(
        models.Kudos.team_id == team_id, 
        or_(models.Kudos.sender_id == user_id, models.Kudos.receiver_id == user_id)
    ))
    
    await db.execute(delete(models.Invitation).where(
        models.Invitation.inviter_id == user_id, 
        models.Invitation.team_id == team_id
    ))

    await db.execute(
        delete(team_members_table).where(
            team_members_table.c.user_id == user_id,
            team_members_table.c.team_id == team_id
        )
    )

    message = models.Message(content=f"管理員已將您移出群組「{team.name}」", receiver_id=user_id)
    db.add(message)
    
    await db.commit()
    return True

async def update_team(db: AsyncSession, team_id: str, user_id:str, name: str) -> bool:
    """
    更新指定团队的信息。
    """
    team = await db.get(models.Team, team_id)
    
    if team:
        origin = team.name
        team.name = name
        # message = models.Message(content=f"群組名稱{origin} 已更換為{name}", team_id=team_id)
        #db.add(message)
        db.add(team)
        members_stmt = (
            select(models.team_members_table.c.user_id)
            .where(
                and_(
                    models.team_members_table.c.team_id == team_id,
                    models.team_members_table.c.user_id != user_id # 排除自己
                )
            )
        )
        members_result = await db.execute(members_stmt)
        receiver_ids = members_result.scalars().all()
        if receiver_ids:
            new_messages = [
                models.Message(
                    team_id=team_id,
                    receiver_id=mid, 
                    content=f"群組名稱{origin} 已更換為{name}"
                ) for mid in receiver_ids
            ]
            db.add_all(new_messages)
        
        try:
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            return False
        
    return None

async def update_team_owner(db: AsyncSession, team_id: str, user_id:str, new_owner: models.User) -> bool:
    """
    更新指定团队的所有者。
    """
    query = select(models.Team).where(models.Team.id == team_id)
    team = (await db.execute(query)).scalar_one_or_none()
    if not team:
        return None  

    team.owner = new_owner
    team.owner_id = new_owner.id
    
    #message = models.Message(content=f"群組{team.name}的管理員已更換為{new_owner.username}", team_id=team_id)
    #db.add(message)
        
    db.add(team)
    members_stmt = (
        select(models.team_members_table.c.user_id)
        .where(
            and_(
                models.team_members_table.c.team_id == team_id,
                models.team_members_table.c.user_id != user_id # 排除自己
            )
        )
    )
    members_result = await db.execute(members_stmt)
    receiver_ids = members_result.scalars().all()
    if receiver_ids:
        new_messages = [
            models.Message(
                team_id=team_id,
                receiver_id=mid, 
                content=f"群組{team.name}的管理員已更換為{new_owner.username}"
            ) for mid in receiver_ids
        ]
        db.add_all(new_messages)
        
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False

async def decline_team_invitation(db: AsyncSession, invitation_code: str) -> bool:
    """
    拒绝指定团队的邀请。
    """
    query = delete(models.Invitation).where(models.Invitation.invite_code == invitation_code)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0

async def delete_session_flow(db: AsyncSession, session_id: str) -> bool:
    """
    删除指定会话流程。
    """
    query = delete(models.FlowSession).where(models.FlowSession.id == session_id)
    result = await db.execute(query)
    await db.commit()
    
    return result.rowcount > 0

async def update_session_flow(db: AsyncSession, session_flow: schemas.SessionModify) -> bool:
    """
    更新指定会话流程。
    """
    query = select(models.FlowSession).where(models.FlowSession.id == session_flow.id)
    session = (await db.execute(query)).scalar_one_or_none()
    if not session:
        return None

    if session.task_description is not None:
        session.task_description = session_flow.task_description
    
    db.add(session)
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False

async def get_message(db: AsyncSession, user_id: str, skip: int = 0, limit: int = 100) -> List[models.Message] | None:   #這個改過
    """
    获取指定消息。
    """
    # user_teams_subquery = select(team_members_table.c.team_id).where(
    #     team_members_table.c.user_id == user_id
    # )

    # 2. 主查詢：查找 (接收者是 user) OR (team_id 在子查詢結果中)
    query = select(models.Message).where(
            models.Message.receiver_id == user_id,
    ).order_by(models.Message.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def delete_message(db: AsyncSession, user_id: str, message_id: str) -> bool:
    """
    删除指定消息。
    """
    query = delete(models.Message).where(models.Message.id == message_id, models.Message.receiver_id == user_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0

async def get_skill_tree_for_user(db: AsyncSession, user_id: str) -> Dict[str, Any]:
    """
    根据当前用户在 UserSkill 表中保存的技能，生成个人技能树 (递归结构)。
    """
    # 1. 获取该用户所有技能 (平铺列表)
    query = select(models.UserSkill).where(
        models.UserSkill.user_id == user_id
    ).order_by(models.UserSkill.name)
    
    result = await db.execute(query)
    all_skills = result.scalars().all() 

    # 2. 使用字典映射 ID -> Node，方便构建树
    node_map = {}
    for skill in all_skills:
        node_map[skill.id] = {
            "id": skill.id,
            "name": skill.name,
            "value": 1,
            "meta_data": skill.meta_data if skill.meta_data else {},
            "parent_id": skill.parent_id, 
            "children": []
        }

    # 3. 组装树结构
    root_nodes = []
    for skill_id, node in node_map.items():
        parent_id = node["parent_id"]
        if parent_id and parent_id in node_map:
            node_map[parent_id]["children"].append(node)
        else:
            root_nodes.append(node)

    for node in node_map.values():
        node.pop("parent_id", None)

    return {
        "name": "个人技能树",
        "children": root_nodes,
    }

async def add_user_skill(db: AsyncSession, user_id: str, 
                         skill: schemas.UserSkillItem, parent_id: str | None = None) -> str | None:
    """
    添加技能到指定父节点下，返回新生成的 ID。
    """
    name = skill.name.strip()
    if not name:
        return None
    if parent_id:
        parent_query = select(models.UserSkill).where(
            models.UserSkill.id == parent_id,
            models.UserSkill.user_id == user_id
        )
        parent_result = await db.execute(parent_query)
        parent_node = parent_result.scalar_one_or_none()
        if not parent_node:
            return None
    check_query = select(models.UserSkill).where(
        models.UserSkill.user_id == user_id,
        models.UserSkill.name == name
    )
    if parent_id:
        check_query = check_query.where(models.UserSkill.parent_id == parent_id)
    else:
        check_query = check_query.where(models.UserSkill.parent_id.is_(None))
    
    existing_skill = await db.execute(check_query)
    if existing_skill.scalar_one_or_none():
        return None
    # 1. 插入 UserSkill
    new_skill = models.UserSkill(
        user_id=user_id, 
        name=name, 
        parent_id=parent_id, 
        meta_data=skill.meta_data
    )
    db.add(new_skill)
    try:
        await db.flush() 
    except IntegrityError:
        await db.rollback()
        return None 
    except SQLAlchemyError:
        await db.rollback()
        return None

    # 2. 同步逻辑：更新该用户所在的所有 TeamSkill
    subquery = select(team_members_table.c.team_id).where(team_members_table.c.user_id == user_id)
    user_team_ids_result = await db.execute(subquery)
    user_team_ids = user_team_ids_result.scalars().all()

    if user_team_ids:
        # 如果新技能有 parent_id，我们需要先找出这个 parent 在 UserSkill 中的名字
        parent_name = None
        if parent_id:
            p_res = await db.get(models.UserSkill, parent_id)
            if p_res:
                parent_name = p_res.name
        stmt_existing = select(models.TeamSkill.team_id).where(
            models.TeamSkill.user_id == user_id,
            models.TeamSkill.name == name,
            models.TeamSkill.team_id.in_(user_team_ids)
        )
        existing_res = await db.execute(stmt_existing)
        existing_team_ids = set(existing_res.scalars().all())
        new_team_skills = []
        
        for tid in user_team_ids:
            if tid in existing_team_ids:
                continue
            team_skill_parent_id = None
            if parent_name:
                stmt_find_parent = select(models.TeamSkill.id).where(
                    models.TeamSkill.team_id == tid,
                    models.TeamSkill.user_id == user_id,
                    models.TeamSkill.name == parent_name 
                )
                ts_parent_res = await db.execute(stmt_find_parent)
                team_skill_parent_id = ts_parent_res.scalar_one_or_none()
            new_team_skills.append(models.TeamSkill(
                team_id=tid,
                user_id=user_id,
                name=name,
                parent_id=team_skill_parent_id, 
                meta_data=skill.meta_data 
            ))
        if new_team_skills:
            db.add_all(new_team_skills)
    try:
        await db.commit()
        return new_skill.id 
    except IntegrityError:
        await db.rollback()
        return None 
    except SQLAlchemyError:
        await db.rollback()
        return None

async def modify_user_skill(
    db: AsyncSession, 
    user_id: str, 
    node_id: str, 
    payload: schemas.UserSkillModify
) -> bool:
    # 1. 通过 ID 获取原节点
    skill = await db.get(models.UserSkill, node_id)
    
    if not skill or skill.user_id != user_id:
        return False

    old_name = skill.name
    new_name = payload.new_name.strip() if payload.new_name else old_name
    new_meta = payload.meta_data if payload.meta_data is not None else skill.meta_data

    if new_name != old_name:
        query_check = select(models.UserSkill).where(
            models.UserSkill.user_id == user_id, 
            models.UserSkill.name == new_name
        )
        existing_new = await db.execute(query_check)
        if existing_new.scalar_one_or_none():
            return False 

    # 2. 更新 UserSkill
    skill.name = new_name
    skill.meta_data = new_meta
    db.add(skill)

    # 3. 同步：更新 TeamSkill
    stmt_team = (
        update(models.TeamSkill)
        .where(models.TeamSkill.user_id == user_id, models.TeamSkill.name == old_name)
        .values(name=new_name, meta_data=new_meta)
    )
    await db.execute(stmt_team)

    try:
        await db.commit()
        return True
    except SQLAlchemyError:
        await db.rollback()
        return False

async def delete_user_skill(db: AsyncSession, user_id: str, node_id: str) -> bool:
    # 1. 获取 UserSkill
    skill = await db.get(models.UserSkill, node_id)
    if not skill or skill.user_id != user_id:
        return False
    target_name = skill.name
    # 2. 删除 UserSkill
    # 删除这个 parent skill 会自动触发 SQLAlchemy 递归删除其所有 children。
    await db.delete(skill)
    # 3. 同步：删除 TeamSkill
    stmt_team = delete(models.TeamSkill).where(
        models.TeamSkill.user_id == user_id, 
        models.TeamSkill.name == target_name
    )
    await db.execute(stmt_team)
    try:
        await db.commit()
        return True
    except SQLAlchemyError:
        await db.rollback()
        return False

async def get_team_message(db: AsyncSession, user_id: str, team_id: str) -> List[models.TeamMessage]:    #db=db, user_id=current_user.id, team_id=current_team.id
    """
    获取团队內信息。
    """
    query = select(models.TeamMessage).where(models.TeamMessage.team_id == team_id, models.TeamMessage.receiver_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()

async def delete_team_message(db: AsyncSession, user_id: str, message_id: str, team_id: str) -> bool:    #db=db, user_id=current_user.id, team_id=current_team.id
    """
    刪除团队內已閱信息。
    """
    query = delete(models.TeamMessage).where(models.TeamMessage.team_id == team_id, models.TeamMessage.receiver_id == user_id, models.TeamMessage.id == message_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0

async def add_team_message(db: AsyncSession, receiver_id: str, team_id: str, tag: str, content: str) -> bool:    
    """
    添加团队內信息。
    """
    db.add(models.TeamMessage(team_id=team_id, receiver_id=receiver_id, content=content,tag=tag))
    await db.commit()
    return True

async def get_highlight_comments(db: AsyncSession, highlight_id: str, skip: int = 0 , limit: int = 50) -> List[models.Comment]:
    query = select(models.Comment).where(models.Comment.highlight_id == highlight_id).order_by(models.Comment.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
    
async def create_highlight_comment(db: AsyncSession, highlight_id: str, user_id: str, comment: str) -> bool:
    new_comment = models.Comment(highlight_id=highlight_id, user_id=user_id, content=comment)
    db.add(new_comment)
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False

async def delete_highlight_comment(db: AsyncSession, highlight_id: str, user_id: str, comment_id: str) -> bool:
    query = delete(models.Comment).where(models.Comment.highlight_id == highlight_id, models.Comment.user_id == user_id, models.Comment.id == comment_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0

async def modify_highlight_comment(db: AsyncSession, comment: str, comment_id: str, user_id: str) -> bool:
    modify = update(models.Comment).where(models.Comment.id == comment_id, models.Comment.user_id == user_id).values(content=comment)
    result = await db.execute(modify)
    await db.commit()
    return result.rowcount > 0

async def get_chat_messages(db: AsyncSession, team_id: str, before_msg_id: Optional[str] = None , after_msg_id: Optional[str] =  None, limit: int = 50) -> List[models.TeamChat]:
    query = select(models.TeamChat).where(models.TeamChat.team_id == team_id)
    if before_msg_id:
        query = query.where(models.TeamChat.id < before_msg_id)
    elif after_msg_id:
        query = query.where(models.TeamChat.id > after_msg_id)

    query = query.order_by(models.TeamChat.id.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()

async def post_chat_messages(db: AsyncSession, team_id: str, sender_id: str, content: str, tag: str) -> bool :
    new_message = models.TeamChat(
        team_id=team_id, 
        sender_id=sender_id, 
        content=content, 
        tag=tag
    )
    
    db.add(new_message)
    try:
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        return False

async def delete_chat_messages(db: AsyncSession, team_id: str, sender_id: str, message_id: str) -> bool:
    query = select(models.TeamChat).where(
        models.TeamChat.team_id == team_id, 
        models.TeamChat.id == message_id, 
        models.TeamChat.sender_id == sender_id
    )
    result = await db.execute(query)
    message = result.scalar_one_or_none() # 修正：必須這樣取值
    
    if not message:
        return False
    
    if message.tag == "file" or message.tag == "image":    
        # message.content 存的是 "/static/uploads/..."
        await utils.delete_file_from_disk(message.content)
    
    # 3. 數據庫刪除
    await db.delete(message)
    await db.commit()
    return True

# --- Forum Section CRUD ---

async def get_forum_sections(db: AsyncSession, team_id: str) -> List[models.ForumSection]:
    """获取指定团队的所有版块"""
    query = select(models.ForumSection).where(models.ForumSection.team_id == team_id).order_by(models.ForumSection.created_at)
    result = await db.execute(query)
    return result.scalars().all()

async def create_forum_section(db: AsyncSession, team_id: str, section_data: schemas.ForumSectionCreate) -> models.ForumSection | None:
    """创建新版块"""
    db_section = models.ForumSection(
        team_id=team_id,
        name=section_data.name,
        description=section_data.description
    )
    db.add(db_section)
    try:
        await db.commit()
        await db.refresh(db_section)
        return db_section
    except SQLAlchemyError:
        await db.rollback()
        return None

async def update_forum_section(db: AsyncSession, section_id: str, team_id: str, section_data: schemas.ForumSectionModify) -> models.ForumSection | None:
    """更新版块 (需确保是该 team 的 section)"""
    section = await db.get(models.ForumSection, section_id)
    
    if not section or section.team_id != team_id:
        return None
        
    if section_data.name is not None:
        section.name = section_data.name
    if section_data.description is not None:
        section.description = section_data.description
        
    db.add(section)
    try:
        await db.commit()
        await db.refresh(section) 
        return section
    except SQLAlchemyError:
        await db.rollback()
        return None

async def delete_forum_section(db: AsyncSession, section_id: str, team_id: str) -> bool:
    """删除版块"""
    query = delete(models.ForumSection).where(
        models.ForumSection.id == section_id,
        models.ForumSection.team_id == team_id
    )
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0

async def get_forum_section_by_id(db: AsyncSession, section_id: str) -> models.ForumSection | None:
    """辅助函数：通过 ID 获取版块"""
    return await db.get(models.ForumSection, section_id)

# --- Forum Post CRUD ---

async def get_forum_posts(
    db: AsyncSession, 
    team_id: str, 
    section_id: str, 
    skip: int = 0, 
    limit: int = 20
) -> Tuple[List[models.ForumPost], Set[str]]:
    """
    获取帖子列表。
    这里不返回 liked_by_current_user 的状态，只返回帖子对象列表。
    状态判断逻辑放到 Router 或单独的辅助函数中，避免 CRUD 函数参数过载。
    """
    query = (
        select(models.ForumPost)
        .where(
            models.ForumPost.team_id == team_id, 
            models.ForumPost.section_id == section_id
        )
        .options(
            selectinload(models.ForumPost.author),
            selectinload(models.ForumPost.likes),     # 预加载以计算数量
            selectinload(models.ForumPost.comments)   # 预加载以计算数量
        )
        .order_by(models.ForumPost.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()

async def get_user_liked_post_ids(db: AsyncSession, user_id: str, post_ids: List[str]) -> Set[str]:
    """辅助函数：获取用户在给定帖子ID列表中点过赞的帖子ID集合"""
    if not post_ids:
        return set()
        
    query = select(models.ForumPostLike.post_id).where(
        models.ForumPostLike.user_id == user_id,
        models.ForumPostLike.post_id.in_(post_ids)
    )
    result = await db.execute(query)
    return set(result.scalars().all())

async def create_forum_post(
    db: AsyncSession, 
    team_id: str, 
    section_id: str, 
    user_id: str, 
    post_data: schemas.ForumPostCreate
) -> models.ForumPost | None:
    """发布新帖子"""
    db_post = models.ForumPost(
        team_id=team_id,
        section_id=section_id,
        author_id=user_id,
        title=post_data.title,
        content=post_data.content
    )
    db.add(db_post)
    try:
        await db.commit()
        await db.refresh(db_post)
        query = (
            select(models.ForumPost)
            .where(models.ForumPost.id == db_post.id)
            .options(
                selectinload(models.ForumPost.author), 
                selectinload(models.ForumPost.likes),   
                selectinload(models.ForumPost.comments) 
            )
        )
        result = await db.execute(query)
        loaded_post = result.scalar_one()
        return loaded_post
    except SQLAlchemyError:
        await db.rollback()
        return None

async def get_forum_post_detail(db: AsyncSession, post_id: str) -> models.ForumPost | None:
    """获取帖子详情"""
    query = (
        select(models.ForumPost)
        .where(models.ForumPost.id == post_id)
        .options(
            selectinload(models.ForumPost.author),
            selectinload(models.ForumPost.likes),
            selectinload(models.ForumPost.comments)
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def update_forum_post(
    db: AsyncSession, 
    post_id: str, 
    user_id: str, 
    post_data: schemas.ForumPostModify
) -> models.ForumPost | None:
    """更新帖子 (仅限作者)"""
    # 先检查权限和存在性
    post = await db.get(models.ForumPost, post_id)
    if not post or post.author_id != user_id:
        return None
        
    if post_data.title is not None:
        post.title = post_data.title
    if post_data.content is not None:
        post.content = post_data.content
    
    post.updated_at = china_now() # 手动更新修改时间
    db.add(post)
    
    try:
        await db.commit()
        await db.refresh(post)
        query = (
            select(models.ForumPost)
            .where(models.ForumPost.id == post_id)
            .options(
                selectinload(models.ForumPost.author),  
                selectinload(models.ForumPost.likes),   
                selectinload(models.ForumPost.comments) 
            )
        )
        result = await db.execute(query)
        updated_post = result.scalar_one()
        
        return updated_post
    except SQLAlchemyError:
        await db.rollback()
        return None

async def delete_forum_post(
    db: AsyncSession, 
    post_id: str, 
    user_id: str, 
    is_admin: bool
) -> bool:
    """删除帖子 (作者或管理员)"""
    query = select(models.ForumPost).where(models.ForumPost.id == post_id)
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        return False
        
    # 权限检查：必须是作者 或者 是管理员(team owner)
    if post.author_id != user_id and not is_admin:
        return False
        
    await db.delete(post)
    await db.commit()
    return True

# --- Forum Interaction (Likes & Comments) CRUD ---

async def get_forum_post_comments(
    db: AsyncSession, 
    post_id: str, 
    skip: int = 0, 
    limit: int = 50
) -> List[models.ForumComment]:
    """获取指定帖子的评论列表"""
    query = (
        select(models.ForumComment)
        .where(models.ForumComment.post_id == post_id)
        .options(selectinload(models.ForumComment.user))
        .order_by(models.ForumComment.created_at.asc()) # 评论通常按时间正序排列
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()

async def create_forum_comment(
    db: AsyncSession, 
    post_id: str, 
    user_id: str, 
    content: str
) -> models.ForumComment | None:
    """创建评论"""
    db_comment = models.ForumComment(
        post_id=post_id,
        user_id=user_id,
        content=content
    )
    db.add(db_comment)
    try:
        await db.commit()
        await db.refresh(db_comment)
        query = (
            select(models.ForumComment)
            .where(models.ForumComment.id == db_comment.id)
            .options(selectinload(models.ForumComment.user))
        )
        result = await db.execute(query)
        return result.scalar_one()
    except SQLAlchemyError:
        await db.rollback()
        return None

async def delete_forum_comment(
    db: AsyncSession, 
    comment_id: str, 
    user_id: str, 
    is_team_owner: bool
) -> bool:
    """
    删除评论
    权限逻辑：评论作者 或者 团队Owner 可以删除。
    """
    query = select(models.ForumComment).where(models.ForumComment.id == comment_id)
    result = await db.execute(query)
    comment = result.scalar_one_or_none()
    
    if not comment:
        return False
        
    # 权限检查
    if comment.user_id != user_id and not is_team_owner:
        return False
        
    await db.delete(comment)
    await db.commit()
    return True

async def get_forum_comment_detail(db: AsyncSession, comment_id: str) -> models.ForumComment | None:
    """获取评论详情（包含关联的 post 信息，用于权限检查）"""
    query = (
        select(models.ForumComment)
        .where(models.ForumComment.id == comment_id)
        .options(selectinload(models.ForumComment.post)) 
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def like_forum_post(db: AsyncSession, post_id: str, user_id: str) -> bool:
    """点赞帖子"""
    try:
        db_like = models.ForumPostLike(post_id=post_id, user_id=user_id)
        db.add(db_like)
        await db.commit()
        return True
    except IntegrityError:
        await db.rollback()
        return False
    except SQLAlchemyError:
        await db.rollback()
        return False

async def unlike_forum_post(db: AsyncSession, post_id: str, user_id: str) -> bool:
    """取消点赞帖子"""
    query = delete(models.ForumPostLike).where(
        models.ForumPostLike.post_id == post_id,
        models.ForumPostLike.user_id == user_id
    )
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0

async def get_all_checkin_record(db: AsyncSession, user_id: str, team_id: str, query_date: date | None = None, limit: int = 10) -> List[models.Checkin]:
    """回傳指定的遷到日期和條數紀錄"""
    target_date = query_date if query_date else china_now().date()
    
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)
    
    query = (
        select(models.Checkin)
        .where(
            models.Checkin.user_id == user_id,
            models.Checkin.team_id == team_id,
            models.Checkin.created_at >= start_of_day,
            models.Checkin.created_at < end_of_day
        )
        .order_by(models.Checkin.id.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return result.scalars().all()
    