# --- 檔案: app/core/schemas.py ---
# 功能: 定義所有 Pydantic 數據校驗模型 (UUID 使用 String 類型)
from pydantic import computed_field, Field
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, date

# --- Base Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    username: str     #必須填入
    
class modifyUserInfo(BaseModel):
    username: Optional[str] = None
    nickname: Optional[str] = None
    gender : Optional[str] = None
    age : Optional[str] = None
    profession : Optional[str] = None
    
    
class User(UserBase):
    id: str
    nickname: Optional[str] = None
    gender : Optional[str] = None
    age : Optional[str] = None
    profession : Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class TeamMembersResponse(BaseModel):
    owner: User
    members: List[User]
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str
    model_config = ConfigDict(from_attributes=True)

class InviteCode(BaseModel):
    code: str

class InviteInfo(BaseModel):
    team_id: str
    status: str
    created_at: datetime
    invite_code: str
    
    team_name: str
    inviter_username: str
    model_config = ConfigDict(from_attributes=True)
    
class EmailORUsername(BaseModel):
    email_username: str

class EmailVerificationRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="6位验证码")


class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    pass

class UserLogin(BaseModel):
    email: str
    password: str
    model_config = ConfigDict(from_attributes=True)

class Team(TeamBase):
    id: str
    owner: User
    model_config = ConfigDict(from_attributes=True)

class TokenRefresh(BaseModel):
    refresh: str

class AccessToken(BaseModel):
    access: str

class TeamDetail(Team):
    members: List[User] = []

class TokenPair(BaseModel):
    access: str
    refresh: str
    model_config = ConfigDict(from_attributes=True)

class TokenData(BaseModel):
    user_id: Optional[str] = None

# --- Check-in Schemas ---
class CheckinCreate(BaseModel):
    challenge_level: float
    skill_level: float
    achievement_text: Optional[str] = None
    obstacle_text: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class Checkin(CheckinCreate):
    id: str
    user: User
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Dashboard Schemas ---
class TrendDataPoint(BaseModel):
    date: date
    avg_challenge: float
    avg_skill: float
    model_config = ConfigDict(from_attributes=True)

class CompassData(BaseModel):
    period: str
    trend_data: List[TrendDataPoint]
    distribution: Dict[str, float]
    model_config = ConfigDict(from_attributes=True)

class DailyFocus(BaseModel):
    date: date
    hours: float
    model_config = ConfigDict(from_attributes=True)

class FocusTimeData(BaseModel):
    period: str
    total_hours: float
    daily_trend: List[DailyFocus]
    model_config = ConfigDict(from_attributes=True)

class WordCloudItem(BaseModel):
    name: str
    value: int
    model_config = ConfigDict(from_attributes=True)

class AIInsights(BaseModel):
    boosters_wordcloud: List[WordCloudItem]
    blockers_wordcloud: List[WordCloudItem]
    model_config = ConfigDict(from_attributes=True)

# --- Flow Ritual Schemas ---
class FlowSessionCreate(BaseModel):
    start_time: datetime
    duration_minutes: int
    task_description: str
    model_config = ConfigDict(from_attributes=True)
    
class SessionModify(BaseModel):
    id: str
    task_description: str
    model_config = ConfigDict(from_attributes=True)
    
class ReturnFlowSession(FlowSessionCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)

# --- Recognition Schemas ---
class HighlightBase(BaseModel):
    content: str

class HighlightCreate(HighlightBase):
    pass

class Highlight(BaseModel):
    id: str
    user: User  # 假設 User schema 已定義
    content: str
    created_at: datetime

    likes: List[Any] = Field(exclude=True)

    @computed_field
    @property
    def likes_count(self) -> int:
        # 這裡直接使用 self.likes 即可
        return len(self.likes)
    
    liked_by_current_user: bool = False

    model_config = ConfigDict(from_attributes=True)

class KudosCreate(BaseModel):
    receiver_id: str
    card_type: str
    message: str
    model_config = ConfigDict(from_attributes=True)

class Kudos(KudosCreate):
    id: str
    sender: User
    receiver: User
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Culture & Growth Schemas ---
class Charter(BaseModel):
    content: str
    last_updated_by: Optional[User] = None
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CharterUpdate(BaseModel):
    content: str

class SkillTreeNode(BaseModel):
    name: str
    children: List['SkillTreeNode'] = []
    model_config = ConfigDict(from_attributes=True)

class SkillTreeData(BaseModel):
    name: str = "团队技能"
    children: List[SkillTreeNode] = []
    model_config = ConfigDict(from_attributes=True)

class WeekRange(BaseModel):
    start: date
    end: date
    model_config = ConfigDict(from_attributes=True)

class WeeklyDigestData(BaseModel):
    week_range: WeekRange
    mindset_trend: CompassData
    total_focus_hours: float
    top_booster: Optional[str] = None
    top_blocker: Optional[str] = None
    kudos_received: int
    model_config = ConfigDict(from_attributes=True)
    
class boolcheckin(BaseModel):
    has_checked_in: bool
    
class ForgotPasswordRequest(BaseModel):
    """忘记密码请求体"""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """重置密码请求体"""
    email: EmailStr
    code: str = Field(..., min_length=16, max_length=16, description="16位数字验证码")
    new_password: str

class ResetEmailRequest(BaseModel):
    """修改邮箱请求体（发送验证码）"""
    new_email: EmailStr

class VerifyEmailResetRequest(BaseModel):
    """修改邮箱验证请求体"""
    code: str = Field(..., min_length=6, max_length=6, description="6位验证码")
    
class KickMember(BaseModel):
    id: str # 或者使用 str，UUID4 更嚴謹
    
class Teamname(BaseModel):
    name: str
    
class TeamOwner(BaseModel):
    id: str

class Sessionflow_id(BaseModel):
    id: str

class HighlightModify(BaseModel):
    id: str
    content: str

class HighlightId(BaseModel):
    id: str