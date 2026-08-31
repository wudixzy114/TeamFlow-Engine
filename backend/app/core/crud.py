from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from . import models, schemas
from .security import get_password_hash
from typing import Any, Dict, Literal, List, Tuple
from collections import Counter
import re
import jieba
from pathlib import Path
import logging
from sqlalchemy import func
from datetime import date, datetime, timedelta # 確保導入了 date 和 timedelta
import secrets
import string
from sqlalchemy import or_

PeriodLiteral = Literal["day", "week", "month"]
logger = logging.getLogger(__name__)


# --- User CRUD ---
def get_user(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def user_exist(db: Session, username: str) -> bool:   # bool
    return db.query(models.User).filter(models.User.username == username).first() is not None

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, username: str, email: str, hashed_password: str, gender: str, nickname: str, age: str, profession: str) -> models.User:
    db_user = models.User(email=email, hashed_password=hashed_password, username=username, gender=gender, nickname=nickname, age=age, profession=profession)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_team(db: Session, team: schemas.TeamCreate, owner: models.User) -> models.Team:
    """
    創建一個新的團隊。
    - team: 包含團隊名稱的 Pydantic 模型。
    - owner: 創建此團隊的用戶，他將成為 owner 和第一個成員。
    """
    db_team = models.Team(
        name=team.name,
        owner_id=owner.id
    )
    
    # 關鍵：創建者自動成為團隊的第一個成員
    db_team.members.append(owner)
    
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

# 【新增】一個函數來獲取用戶加入的所有團隊
def get_teams_for_user(db: Session, user: models.User) -> List[models.Team] | None:
    """
    查詢並返回指定用戶作為成員的所有團隊列表。
    """
    return db.query(models.Team).filter(models.Team.members.any(id=user.id)).all()

def update_user_email(db: Session, user_id: str, new_email: str) -> models.User | None:
    """
    更新指定用户的邮箱地址。
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    
    user.email = new_email
    db.commit()
    db.refresh(user)
    return user

# --- Team CRUD (IDOR 防護關鍵) ---
def get_team_for_user(db: Session, team_id: str, user: models.User) -> models.Team | None:
    return db.query(models.Team).filter(
        models.Team.id == team_id,
        models.Team.members.any(id=user.id)
    ).first()


# --- Dashboard CRUD ---

def _get_start_date(period: PeriodLiteral) -> datetime:
    """根据周期计算查询的起始日期。"""
    now = datetime.utcnow()
    if period == "day":
        return now - timedelta(days=1)
    elif period == "week":
        return now - timedelta(weeks=1)
    elif period == "month":
        return now - timedelta(days=30)  # 近30天
    return now - timedelta(weeks=1)  # 默认


def get_team_compass_data(db: Session, team_id: str, period: PeriodLiteral) -> Dict[str, Any]:
    """
    依据团队与周期返回情绪罗盘数据, 结构遵循 schemas.CompassData。
    """
    start_date = _get_start_date(period)
    
    emotion_case = case(
        (
            (models.Checkin.challenge_level > 3.5) & (models.Checkin.skill_level > 3.5),
            "positive",
        ),
        (
            ((models.Checkin.challenge_level > 3.5) & (models.Checkin.skill_level < 2.5)) |
            ((models.Checkin.challenge_level < 2.5) & (models.Checkin.skill_level < 2.5)),
            "negative",
        ),
        else_="neutral",
    )

    # 查询总体情绪分布
    summary_query = (
        db.query(
            emotion_case.label("emotion"),
            func.count(models.Checkin.id).label("count"),
        )
        .filter(models.Checkin.team_id == team_id, models.Checkin.created_at >= start_date)
        .group_by("emotion")
        .all()
    )
    summary_counts = {row.emotion: row.count for row in summary_query}
    total_checkins = sum(summary_counts.values())
    
    distribution = {
        emotion: (count / total_checkins) * 100 if total_checkins > 0 else 0
        for emotion, count in summary_counts.items()
    }

    # 查询趋势数据 (按天分组计算平均挑战和技能)
    trend_query = (
        db.query(
            func.date(models.Checkin.created_at).label("date"),
            func.avg(models.Checkin.challenge_level).label("avg_challenge"),
            func.avg(models.Checkin.skill_level).label("avg_skill"),
        )
        .filter(models.Checkin.team_id == team_id, models.Checkin.created_at >= start_date)
        .group_by(func.date(models.Checkin.created_at))
        .order_by(func.date(models.Checkin.created_at))
        .all()
    )

    return {
        "period": period,
        "distribution": {
            "positive": distribution.get("positive", 0),
            "neutral": distribution.get("neutral", 0),
            "negative": distribution.get("negative", 0),
        },
        "trend_data": trend_query,
    }


def get_team_focus_time_data(db: Session, team_id: str, period: PeriodLiteral) -> Dict[str, Any]:
    """
    依据团队与周期返回专注时长数据, 结构遵循 schemas.FocusTimeData。
    """
    start_date = _get_start_date(period)
    
    # 使用数据库聚合函数，更高效
    daily_totals_query = (
        db.query(
            func.date(models.FlowSession.start_time).label("date"),
            func.sum(models.FlowSession.duration_minutes).label("total_minutes"),
        )
        .filter(
            models.FlowSession.team_id == team_id,
            models.FlowSession.start_time >= start_date,
        )
        .group_by(func.date(models.FlowSession.start_time))
        .order_by(func.date(models.FlowSession.start_time))
        .all()
    )

    total_minutes = sum(row.total_minutes for row in daily_totals_query)
    daily_trend = [{"date": row.date, "hours": round(row.total_minutes / 60, 2)} for row in daily_totals_query]

    return {
        "period": period,
        "total_hours": round(total_minutes / 60, 2),
        "daily_trend": daily_trend,
    }

def load_stopwords(file_path: Path) -> set:
    """从文件加载停用词列表。"""
    if not file_path.is_file():
        logger.warning(f"停用词文件未找到: {file_path}。将使用空停用词列表。")
        return set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            stopwords = {line.strip() for line in f if line.strip()}
        logger.info(f"成功从 {file_path} 加载 {len(stopwords)} 个停用词。")
        return stopwords
    except Exception as e:
        logger.error(f"加载停用词文件 {file_path} 时出错: {e}")
        return set()


# 构建停用词文件的正确路径 
STOPWORDS_PATH = Path(__file__).parent/ 'assets' / 'stopwords.txt'
STOPWORDS = load_stopwords(STOPWORDS_PATH)

# 生成词云的辅助函数
def generate_wordcloud(texts: List[str]) -> List[Dict[str, Any]]:
    if not texts:
        return []
    
    all_text = " ".join(texts)
    words = jieba.cut(all_text)
    
    meaningful_words = [
        word for word in words if word not in STOPWORDS and len(word) > 1
    ]
    
    word_counts = Counter(meaningful_words)
    
    return [{"name": name, "value": value} for name, value in word_counts.most_common(30)]

def get_team_insights_data(db: Session, team_id: str, period: PeriodLiteral) -> Dict[str, List[str]]:
    """
    进行分词和词频统计，最终输出洞察列表。
    """
    start_date = _get_start_date(period)

    checkins = db.query(models.Checkin.achievement_text, models.Checkin.obstacle_text).filter(
        models.Checkin.team_id == team_id,
        models.Checkin.created_at >= start_date
    ).all()

    boosters = [c.achievement_text for c in checkins if c.achievement_text]
    blockers = [c.obstacle_text for c in checkins if c.obstacle_text]

    return {
        "boosters_wordcloud": generate_wordcloud(boosters),
        "blockers_wordcloud": generate_wordcloud(blockers),
    }


# --- Recognition (Highlight, Like) CRUD ---

def get_highlight(db: Session, highlight_id: str) -> models.Highlight | None:
    """通过ID获取单个高光时刻。"""
    return db.query(models.Highlight).filter(models.Highlight.id == highlight_id).first()

def like_highlight(db: Session, highlight_id: str, user_id: str) -> models.Like | None:
    """为一个高光时刻创建一条'赞'的记录。"""
    # 檢查是否存在，避免不必要的資料庫寫入嘗試
    existing_like = db.query(models.Like).filter_by(highlight_id=highlight_id, user_id=user_id).first()
    if existing_like:
        return # 如果已存在，直接返回

    db_like = models.Like(highlight_id=highlight_id, user_id=user_id)
    db.add(db_like)
    db.commit()
    return db_like

def unlike_highlight(db: Session, highlight_id: str, user_id: str) -> bool: # 更名
    """移除一个高光时刻的'赞'。"""
    like = db.query(models.Like).filter(
        models.Like.highlight_id == highlight_id, 
        models.Like.user_id == user_id
    ).first()

    if like:
        db.delete(like)
        db.commit()
        return True
    return False
        

# --- "Me" (Current User) CRUD ---

def list_received_kudos_for_user(db: Session, user_id: str) -> List[models.Kudos]:
    """获取指定用户收到的所有 Kudos。"""
    return (
        db.query(models.Kudos)
        .filter(models.Kudos.receiver_id == user_id)
        .options(joinedload(models.Kudos.sender)) # 预加载发送者信息
        .order_by(models.Kudos.created_at.desc())
        .all()
    )


def get_user_weekly_digest(db: Session, user_id: str, query_date: date) -> Dict[str, Any]:
    """为指定用户生成周报数据。"""
    # 1. 计算周的起止日期
    start_of_week = query_date - timedelta(days=query_date.weekday())
    end_of_week = start_of_week + timedelta(days=7)

    # 2. 获取专注时长
    total_focus_minutes = (
        db.query(func.sum(models.FlowSession.duration_minutes))
        .filter(
            models.FlowSession.user_id == user_id,
            models.FlowSession.start_time >= start_of_week,
            models.FlowSession.start_time < end_of_week,
        )
        .scalar() or 0
    )

    # 3. 获取收到的 Kudos 数量
    kudos_received_count = (
        db.query(func.count(models.Kudos.id))
        .filter(
            models.Kudos.receiver_id == user_id,
            models.Kudos.created_at >= start_of_week,
            models.Kudos.created_at < end_of_week,
        )
        .scalar() or 0
    )

    # 4. 获取周内的所有签到文本
    checkins = db.query(models.Checkin.achievement_text, models.Checkin.obstacle_text).filter(
        models.Checkin.user_id == user_id,
        models.Checkin.created_at >= start_of_week,
        models.Checkin.created_at < end_of_week,
    ).all()

    # 5. 词云分析提取最高频关键词
    boosters_texts = [c.achievement_text for c in checkins if c.achievement_text]
    blockers_texts = [c.obstacle_text for c in checkins if c.obstacle_text]
    
    top_booster = generate_wordcloud(boosters_texts)
    top_blocker = generate_wordcloud(blockers_texts)

    # 6. 个人心态趋势计算
    emotion_case = case(
        (
            (models.Checkin.challenge_level > 3.5) & (models.Checkin.skill_level > 3.5),
            "positive",
        ),
        (
            ((models.Checkin.challenge_level > 3.5) & (models.Checkin.skill_level < 2.5)) |
            ((models.Checkin.challenge_level < 2.5) & (models.Checkin.skill_level < 2.5)),
            "negative",
        ),
        else_="neutral",
    )

    # 计算情绪分布
    summary_counts = Counter(
        emotion_case.eval(
            bind=db.connection(),
            challenge_level=c.challenge_level,
            skill_level=c.skill_level
        ) for c in checkins
    )
    total_checkins = len(checkins)
    distribution = {
        emotion: (count / total_checkins) * 100 if total_checkins > 0 else 0
        for emotion, count in summary_counts.items()
    }

    # 计算趋势数据
    trend_data_points = {}
    for c in checkins:
        date_key = c.created_at.date()
        if date_key not in trend_data_points:
            trend_data_points[date_key] = {'challenges': [], 'skills': []}
        trend_data_points[date_key]['challenges'].append(c.challenge_level)
        trend_data_points[date_key]['skills'].append(c.skill_level)

    trend_data = [
        {
            "date": date_key,
            "avg_challenge": sum(vals['challenges']) / len(vals['challenges']),
            "avg_skill": sum(vals['skills']) / len(vals['skills']),
        }
        for date_key, vals in sorted(trend_data_points.items())
    ]

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
        "top_booster": top_booster,
        "top_blocker": top_blocker,
        "kudos_received": kudos_received_count,
    }

def generate_invite_code(length: int = 48) -> str:  # 生成一個隨機的邀請碼
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def create_invitation(db: Session, team_id: UUID, inviter_id: UUID, invitee_email: str) -> models.Invitation:
    # 1. 生成一個唯一的邀請碼
    # (在一個高併發的系統中，這裡需要一個迴圈來確保 code 的唯一性，但目前這樣可以)
    invite_code = generate_invite_code()
    
    # 2. 創建 Invitation 物件，包含 invite_code
    db_invitation = models.Invitation(
        team_id=team_id,
        inviter_id=inviter_id,
        invitee_email=invitee_email,
        invite_code=invite_code
    )
    db.add(db_invitation)
    db.commit()
    db.refresh(db_invitation)
    return db_invitation

def is_user_in_team(db: Session, team_id: str, user_id: str) -> bool:
    return db.query(models.Team).filter(
        models.Team.id == team_id,
        models.Team.members.any(id=user_id)
    ).first() is not None

def has_pending_invitation(db: Session, team_id: str, invitee_email: str) -> bool:
    return db.query(models.Invitation).filter(
        models.Invitation.team_id == team_id,
        models.Invitation.invitee_email == invitee_email,
        models.Invitation.status == "pending"
    ).first() is not None
    
    
def get_valid_invitation_by_code(db: Session, invite_code: str, current_user_email: str) -> models.Invitation | None:
    """
    根據邀請碼查找一個處於 'pending' 狀態的邀請。
    關鍵安全檢查：同時驗證該邀請的目標 email 是否與當前用戶的 email 匹配。
    """
    return db.query(models.Invitation).filter(
        models.Invitation.invite_code == invite_code,
        models.Invitation.invitee_email == current_user_email, # 安全性：確保是本人在接受邀請
        models.Invitation.status == "pending"
    ).first()

def accept_invitation_and_join_team(db: Session, invitation: models.Invitation, user: models.User) -> models.Team | None:
    """
    處理接受邀請的完整資料庫事務。
    1. 查找邀請對應的團隊。
    2. 檢查用戶是否已是成員。
    3. 如果檢查通過，將用戶加入團隊並刪除邀請。
    4. 返回加入的團隊物件，如果失敗則返回 None。
    """
    # 1. 獲取團隊
    team = db.query(models.Team).filter(models.Team.id == invitation.team_id).first()
    
    # 如果團隊不存在或用戶已是成員，則操作失敗
    if not team or is_user_in_team(db=db, team_id=team.id, user_id=user.id):
        return None

    # 2. 加入團隊
    user.teams.append(team)
    db.delete(invitation)
    db.commit()
    return team


# 【已修正】 創建一個新的簽到記錄
def checkin_create(db: Session, checkin: schemas.CheckinCreate, team_id: str, user: models.User) -> models.Checkin:
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
    db.commit()
    db.refresh(db_checkin)
    return db_checkin # 返回創建的對象，這是一個好習慣

# 【已修正】 判斷用戶今天是否已經在某個團隊簽到
def has_checked_in_today(db: Session, user_id: str, team_id: str) -> bool:
    today_start = date.today() # 獲取今天的日期，例如 2025-10-12
    return db.query(models.Checkin).filter(
        models.Checkin.user_id == user_id,
        models.Checkin.team_id == team_id,
        func.date(models.Checkin.created_at) == today_start
    ).first() is not None
    
def get_highlights(db: Session, user_id: str, team_id: str) -> List[models.Highlight]:
    """
    获取指定团队内所有成员的高光时刻。
    同时，为每个高光时刻附加一个布尔值，标记当前用户是否已点赞。
    """
    # 获取团队内所有的高光时刻，并预加载用户信息
    team_highlights = db.query(models.Highlight).options(
        joinedload(models.Highlight.user)
    ).filter(models.Highlight.team_id == team_id).order_by(models.Highlight.created_at.desc()).all()

    if not team_highlights:
        return []

    # 一次性查询出当前用户在这些高光时刻中的所有点赞记录
    highlight_ids = [h.id for h in team_highlights]
    user_likes = db.query(models.Like.highlight_id).filter(
        models.Like.user_id == user_id,
        models.Like.highlight_id.in_(highlight_ids)
    ).all()
    
    # 将点赞过的 highlight_id 存入一个 Set 中，以便快速查找
    liked_highlight_ids = {like.highlight_id for like in user_likes}

    # 遍历高光时刻，设置 liked_by_current_user 字段
    for highlight in team_highlights:
        highlight.liked_by_current_user = highlight.id in liked_highlight_ids
        
    return team_highlights

def post_highlights(db: Session, user_id: str, team_id: str, highlights: str) -> models.Highlight:
    highlights = models.Highlight(user_id=user_id, team_id=team_id, content=highlights)
    db.add(highlights)
    db.commit()
    db.refresh(highlights)
    return highlights

def update_highlight(db: Session, highlight_id: str, content: str) -> models.Highlight | None:
    """
    更新指定高光时刻的内容。
    """
    highlight = db.query(models.Highlight).filter(models.Highlight.id == highlight_id).first()
    if not highlight:
        return None
    highlight.content = content
    db.commit()
    db.refresh(highlight)
    return highlight

def delete_highlight(db: Session, highlight_id: str) -> bool:
    """
    删除指定的高光时刻。
    """
    highlight = db.query(models.Highlight).filter(models.Highlight.id == highlight_id).first()
    if not highlight:
        return False
    db.delete(highlight)
    db.commit()
    return True

def post_flow_sessions(db: Session, user_id: str, team_id: str, flow_sessions: schemas.FlowSessionCreate) -> models.FlowSession:
    flow_sessions = models.FlowSession(user_id=user_id, team_id=team_id, start_time=flow_sessions.start_time, duration_minutes=flow_sessions.duration_minutes, task_description=flow_sessions.task_description)
    db.add(flow_sessions)
    db.commit()
    db.refresh(flow_sessions)
    return flow_sessions
        
def get_flow_sessions(db: Session, user_id: str, team_id: str) -> List[models.FlowSession]:   #應該是全部都要
    return db.query(models.FlowSession).filter(models.FlowSession.user_id == user_id,models.FlowSession.team_id == team_id).all()
    
def get_user_all_invite(db: Session, user_email: str) -> List[Tuple[models.Invitation, str, str]]:   #"""獲取用戶所有發出的邀請"""
    query = db.query(
        models.Invitation,
        models.Team.name.label("team_name"),
        models.User.username.label("inviter_username")
    )

    # 2. 在「食譜」中加入 JOIN 指令，告訴它如何連接三張表
    query = query.join(models.Team, models.Invitation.team_id == models.Team.id)
    query = query.join(models.User, models.Invitation.inviter_id == models.User.id)

    # 3. 在「食譜」中加入 WHERE 過濾條件
    query = query.filter(models.Invitation.invitee_email == user_email)

    # 4. 所有指令都定義好了，現在執行查詢，把「菜餚」端上來！
    results = query.all()
    
    return results

def create_kudos(db: Session, kudos_data: schemas.KudosCreate, sender_id: str, team_id: str) -> models.Kudos:
    """创建一条新的 Kudos 记录。"""
    db_kudos = models.Kudos(
        **kudos_data.dict(),
        sender_id=sender_id,
        team_id=team_id
    )
    db.add(db_kudos)
    db.commit()
    db.refresh(db_kudos)
    return db_kudos


# --- Culture & Growth (Charter, SkillTree) CRUD ---

def get_charter_for_team(db: Session, team_id: str) -> models.Charter:
    """
    获取团队的心流公约。如果不存在，则在数据库中创建一个并返回。
    """
    charter = db.query(models.Charter).options(joinedload(models.Charter.last_updated_by)).filter(models.Charter.team_id == team_id).first()
    
    if not charter:
        # 如果公约不存在，创建一个默认的空公约并保存
        charter = models.Charter(team_id=team_id, content="")
        db.add(charter)
        db.commit()
        db.refresh(charter)
        # 手动加载关系，因为新创建的对象没有 last_updated_by
        charter.last_updated_by = None

    return charter


def update_charter_for_team(db: Session, team_id: str, user_id: str, content: str) -> models.Charter:
    """
    更新指定团队的心流公约内容。
    """
    charter = get_charter_for_team(db, team_id) # 复用 get 函数，确保对象存在
    
    charter.content = content
    charter.last_updated_by_id = user_id
    # updated_at 会由 onupdate 自动更新
    
    db.commit()
    db.refresh(charter)
    # 重新加载更新者信息以在响应中完整显示
    db.expire(charter)
    return db.query(models.Charter).options(joinedload(models.Charter.last_updated_by)).filter(models.Charter.team_id == team_id).one()

def delete_charter_for_team(db: Session, team_id: str) -> bool:
    """
    删除指定团队的心流公约。
    """
    charter = db.query(models.Charter).filter(models.Charter.team_id == team_id).first()
    if not charter:
        return False  # 公约不存在

    db.delete(charter)
    db.commit()
    return True

def get_skill_tree_for_team(db: Session, team_id: str) -> Dict[str, Any]:
    """
    根据团队成员的签到成就，动态生成技能树数据。
    """
    checkins = (
        db.query(models.Checkin)
        .filter(
            models.Checkin.team_id == team_id,
            models.Checkin.achievement_text.isnot(None),
            models.Checkin.achievement_text != ""
        )
        .all()
    )

    user_cache: Dict[str, models.User | None] = {}
    skills_by_member: Dict[str, Dict[str, Any]] = {}

    for checkin in checkins:
        user_id = checkin.user_id
        if user_id not in user_cache:
            user_cache[user_id] = get_user(db, user_id)
        user = user_cache[user_id]
        if not user:
            continue

        member_id = str(user.id)
        member_name = user.username or "未知成员"

        if member_id not in skills_by_member:
            skills_by_member[member_id] = {
                "name": member_name,
                "skills": set()
            }

        words = jieba.cut(checkin.achievement_text)
        for word in words:
            if word not in STOPWORDS and len(word) > 1:
                skills_by_member[member_id]["skills"].add(word)

    children_nodes = []
    for member_data in skills_by_member.values():
        skill_nodes = [{"name": skill} for skill in member_data["skills"]]
        if skill_nodes:
            children_nodes.append({
                "name": member_data["name"],
                "children": skill_nodes
            })

    return {
        "name": "团队技能树",
        "children": children_nodes
    }


def update_user_password(db: Session, user: models.User, new_password_hash: str) -> models.User:
    """
    更新指定用户的密码哈希值。
    """
    user.hashed_password = new_password_hash
    db.commit()
    db.refresh(user)
    return user


def get_team_members(db: Session, team_id: str) -> Dict[str, Any]:
    team = (
        db.query(models.Team)
        .options(
            joinedload(models.Team.owner),      # 預先載入 owner
            joinedload(models.Team.members)     # 預先載入 members
        )
        .filter(models.Team.id == team_id)
        .first()
    )

    if not team:
        return None # 或可以拋出 Exception，由 API 端點處理

    # 回傳符合新格式的字典
    return {"owner": team.owner, "members": team.members}

def update_user_info(db: Session, user_id: str, nickname: str, age: str, profession: str, gender: str, username: str) -> models.User | None:
    """
    更新指定用户的个人信息。
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None  # 或拋出異常
    
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
    db.commit()
    db.refresh(user)
    return user

def delete_team(db: Session, team_id: str) -> bool: 
    """
    删除指定团队。
    """
    team = db.query(models.Team).filter(models.Team.id == team_id).first()  #但是其他數據表裏面也有跟這個team相關的數據 也都要刪除
    if not team:
        return False  # 或者抛出异常

    db.delete(team)
    db.commit()
    return True

def remove_member_from_team(db: Session, team_id: str, user_id: str) -> bool:
    """
    从指定团队中移除指定成员。
    """
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    member_to_remove = db.query(models.User).filter(models.User.id == user_id).first()
    if not team or not member_to_remove:
        return False  # 或者抛出异常

    db.query(models.Checkin).filter_by(user_id=user_id, team_id=team_id).delete(synchronize_session=False)   #不是應該用models.Checkin.user_id == user_id 嗎
    db.query(models.FlowSession).filter_by(user_id=user_id, team_id=team_id).delete(synchronize_session=False)
    
    # 刪除 Highlight 會自動級聯刪除其關聯的 Like (因為你在 Highlight 模型中已設定 cascade)
    db.query(models.Highlight).filter_by(user_id=user_id, team_id=team_id).delete(synchronize_session=False)

    # 對於 Kudos，需要考慮該成員是發送者或接收者的情況
    db.query(models.Kudos).filter(  #這裡不管是發送者還是接收者 只要跟 這個user有關 都刪除
        models.Kudos.team_id == team_id,
        or_(
            models.Kudos.sender_id == user_id,
            models.Kudos.receiver_id == user_id
        )
    ).delete(synchronize_session=False)
    
    team.members.remove(member_to_remove)

    db.commit()
    return True

def update_team(db: Session, team_id: str, name: str) -> models.Team | None:
    """
    更新指定团队的信息。
    """
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        return None  # 或抛出异常

    team.name = name
    db.commit()
    db.refresh(team)
    return team

def update_team_owner(db: Session, team_id: str, new_owner: models.User) -> models.Team | None:
    """
    更新指定团队的所有者。
    """
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        return None  # 或抛出异常

    team.owner = new_owner
    team.owner_id = new_owner.id
    db.commit()
    db.refresh(team)
    return team

def decline_team_invitation(db: Session, invitation_code: str) -> bool:
    """
    拒绝指定团队的邀请。
    """
    invitation = db.query(models.Invitation).filter(models.Invitation.invite_code == invitation_code).first()
    if not invitation:
        return False  # 或抛出异常

    db.delete(invitation)
    db.commit()
    return True

def delete_session_flow(db: Session, session_id: str) -> bool:
    """
    删除指定会话流程。
    """
    session = db.query(models.FlowSession).filter(models.FlowSession.id == session_id).first()
    if not session:
        return False  # 或抛出异常

    db.delete(session)
    db.commit()
    return True

def update_session_flow(db: Session, session_flow: schemas.SessionModify) -> models.FlowSession | None:
    """
    更新指定会话流程。
    """
    session = db.query(models.FlowSession).filter(models.FlowSession.id == session_flow.id).first()
    if not session:
        return None  # 或抛出异常

    if not session.task_description is None:
        session.task_description = session_flow.task_description
        
    db.commit()
    db.refresh(session)
    return session
