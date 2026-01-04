import uuid 
import uuid6
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, ForeignKey, Table, DateTime, Integer, JSON, Float, Text, PrimaryKeyConstraint, Index, desc, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from .database import Base

def generate_uuid():
    return str(uuid6.uuid7())

def china_now():
    return datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)

# 多對多關聯表：連接 User 和 Team ， 一個team可以有好多成員，一個成員也可以在好多team
team_members_table = Table('team_members', Base.metadata,
    Column('user_id', String, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('team_id', String, ForeignKey('teams.id', ondelete="CASCADE"), primary_key=True))

class User(Base):    #儲存所有使用者的信息
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    username = Column(String, index=True)
    nickname = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    age = Column(String, nullable=True)
    profession = Column(String, nullable=True)
    
    teams = relationship("Team", secondary=team_members_table, back_populates="members")
    highlights = relationship("Highlight", back_populates="user", cascade="all, delete-orphan") #
    flow_sessions = relationship("FlowSession", back_populates="user", cascade="all, delete-orphan")
    owned_teams = relationship("Team", back_populates="owner")
    checkins = relationship("Checkin", back_populates="user", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    sent_kudos = relationship("Kudos", foreign_keys="[Kudos.sender_id]", back_populates="sender", cascade="all, delete-orphan")
    received_kudos = relationship("Kudos", foreign_keys="[Kudos.receiver_id]", back_populates="receiver", cascade="all, delete-orphan")
    received_messages = relationship("Message", foreign_keys="[Message.receiver_id]", back_populates="receiver", cascade="all, delete-orphan") #已經說過不需要sender功能
    updated_charters = relationship("Charter", back_populates="last_updated_by")
    sent_invitations = relationship("Invitation", foreign_keys="[Invitation.inviter_id]", back_populates="inviter", cascade="all, delete-orphan")
    received_team_messages = relationship("TeamMessage", back_populates="receiver", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    sent_team_chats = relationship("TeamChat", back_populates="sender", cascade="all, delete-orphan")
    
class Team(Base):    #儲存關於所有團隊的所有信息
    __tablename__ = "teams"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True, nullable=False)
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    
    # --- 新增以下關聯和 cascade 設定 ---
    owner = relationship("User",back_populates="owned_teams")
    members = relationship("User", secondary=team_members_table, back_populates="teams")
    invitations = relationship("Invitation", back_populates="team", cascade="all, delete-orphan")
    checkins = relationship("Checkin", back_populates="team", cascade="all, delete-orphan")
    flow_sessions = relationship("FlowSession", back_populates="team", cascade="all, delete-orphan")
    highlights = relationship("Highlight", back_populates="team", cascade="all, delete-orphan")
    kudos = relationship("Kudos", back_populates="team", foreign_keys='[Kudos.team_id]', cascade="all, delete-orphan")
    charter = relationship("Charter", back_populates="team", uselist=False, cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="team", cascade="all, delete-orphan")
    team_messages = relationship("TeamMessage", back_populates="team", cascade="all, delete-orphan")
    team_chats = relationship("TeamChat", back_populates="team", cascade="all, delete-orphan")
    forum_sections = relationship("ForumSection", back_populates="team", cascade="all, delete-orphan")
    
class Comment(Base):
    __tablename__ = 'comments'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    highlight_id = Column(String, ForeignKey('highlights.id', ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=china_now)  # 使用中國時間
    
    # 這裡如果不常反查，可以不加 lazy="selectin"，保持預設
    user = relationship("User", back_populates="comments")
    highlight = relationship("Highlight", back_populates="comments")

class Invitation(Base):    #儲存使用者收到的所有團隊邀請
    __tablename__ = 'invitations'
    id = Column(String, primary_key=True, default=generate_uuid)
    team_id = Column(String, ForeignKey('teams.id', ondelete="CASCADE"), nullable=False)
    inviter_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    invitee_email = Column(String, nullable=False)
    invite_code = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=china_now)
    
    team = relationship("Team", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="sent_invitations")

class Checkin(Base):     #儲存使用者打卡信息
    __tablename__ = 'checkins'
    id = Column(String, primary_key=True, default=generate_uuid)   #uuidv7
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    team_id = Column(String, ForeignKey('teams.id', ondelete="CASCADE"), nullable=False)
    challenge_level = Column(Float, nullable=False)
    skill_level = Column(Float, nullable=False)
    achievement_text = Column(Text)
    obstacle_text = Column(Text)
    created_at = Column(DateTime, default=china_now)
    
    __table_args__ = (
        Index('user_cheking_order', 'user_id', 'team_id', desc('id')),  #加速查詢
    )
    
    user = relationship("User", back_populates="checkins")
    team = relationship("Team", back_populates="checkins")

class FlowSession(Base):     #群組成員可以記錄自己的心流狀態，這部分只能使用者自己看到，組內其他成員看不見自己的
    __tablename__ = 'flow_sessions'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    team_id = Column(String, ForeignKey('teams.id', ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, default=china_now, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    task_description = Column(String)
    
    user = relationship("User", back_populates="flow_sessions")
    team = relationship("Team", back_populates="flow_sessions")

class Highlight(Base):      #在群組內可以發送自己的highlight 讓組內的人都知道
    __tablename__ = 'highlights'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    team_id = Column(String, ForeignKey('teams.id', ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=china_now)
    
    user = relationship("User", back_populates="highlights") #
    likes = relationship("Like", back_populates="highlight", cascade="all, delete-orphan")
    team = relationship("Team", back_populates="highlights")
    comments = relationship("Comment", back_populates="highlight", cascade="all, delete-orphan", lazy="selectin")

class Like(Base):        #同一群組內的組員可以對highlight點讚或取消按讚
    __tablename__ = 'likes'
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    highlight_id = Column(String, ForeignKey('highlights.id', ondelete="CASCADE"), primary_key=True)
    
    user = relationship("User", back_populates="likes")
    highlight = relationship("Highlight", back_populates="likes")

class Kudos(Base):     #同一群組內的組員可以相互發送kudos能量卡
    __tablename__ = 'kudos'
    id = Column(String, primary_key=True, default=generate_uuid)
    sender_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    receiver_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    team_id = Column(String, ForeignKey('teams.id', ondelete="CASCADE"), nullable=False)
    card_type = Column(String, nullable=False)
    message = Column(Text)
    created_at = Column(DateTime, default=china_now)
    
    sender = relationship("User", foreign_keys=[sender_id],back_populates="sent_kudos")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_kudos")
    team = relationship("Team", back_populates="kudos")

class Charter(Base):   #儲存每個群組的charter，只能由管理員更新
    __tablename__ = 'charters'
    team_id = Column(String, ForeignKey('teams.id', ondelete="CASCADE"), primary_key=True)
    content = Column(Text, default="")
    last_updated_by_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"))
    updated_at = Column(DateTime, default=china_now, onupdate=china_now)
    
    team = relationship("Team", back_populates="charter")
    last_updated_by = relationship("User", back_populates="updated_charters")
    
class Message(Base):   #儲存不同人所會收到的消息包含群組的或個人的，這個本身只是用來存其他組員做了什麼事之類的，並不是使用者之間可以傳信息的功能
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=generate_uuid)
    receiver_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=True)   #因為有些地方是傳team id 有些地方是傳receiver id
    team_id = Column(String, ForeignKey('teams.id', ondelete="CASCADE"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=china_now)
    
    team = relationship("Team", foreign_keys=[team_id], back_populates="messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")  #message只有接收者，我們沒有使用者之間可以傳信息的功能

class TeamMessage(Base):   #紀錄群組kudos點讚之類的消息
    __tablename__ = "team_messages"
    id = Column(String, primary_key=True, default=generate_uuid)
    team_id = Column(String, ForeignKey('teams.id', ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    tag = Column(String, nullable=False)
    created_at = Column(DateTime, default=china_now)
    receiver_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=True)
    
    team = relationship("Team", foreign_keys=[team_id],back_populates="team_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_team_messages")
    
class TeamChat(Base):
    __tablename__ = "team_chats"
    id = Column(String, primary_key=True, default=generate_uuid)
    team_id = Column(String, ForeignKey('teams.id', ondelete="CASCADE"), nullable=False)
    sender_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)    #存內容或文件路徑
    tag = Column(String, nullable=False)      #存這則信息的屬性
    created_at = Column(DateTime, default=china_now)
    
    __table_args__ = (
        Index('idx_team_chat_order', 'team_id', desc('id')),  #加速查詢
    )

    team = relationship("Team", foreign_keys=[team_id], back_populates="team_chats")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_team_chats")
    

class UserSkill(Base):
    """
    用于存储用户自定义技能的关联表。
    """
    __tablename__ = "user_skills"
    
    id = Column(String, primary_key=True, default=generate_uuid) # 新增独立主键
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    meta_data = Column(JSON, default={}, nullable=True)
    parent_id = Column(String, ForeignKey("user_skills.id", ondelete="CASCADE"), nullable=True)

    children = relationship(
        "UserSkill",
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan"
    )

    # 确保同一个用户的技能名不重复
    __table_args__ = (
        UniqueConstraint('user_id', 'name','parent_id', name='uix_user_skill_name'),
    )


class TeamSkill(Base):
    """
    用于存储团队技能树的数据。
    所有条目都有独立 ID，均可被管理员修改。
    """
    __tablename__ = "team_skills"

    id = Column(String, primary_key=True, default=generate_uuid)
    team_id = Column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) 
    name = Column(String, nullable=False)
    meta_data = Column(JSON, default={}, nullable=True)
    parent_id = Column(String, ForeignKey("team_skills.id", ondelete="CASCADE"), nullable=True)
    user = relationship("User")

    children = relationship(
        "TeamSkill",
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', 'name','parent_id', name='uix_team_skill_member'),
    )

# 论坛版块

class ForumSection(Base):
    __tablename__ = "forum_sections"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    team_id = Column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=china_now)
    
    # 关联
    team = relationship("Team", back_populates="forum_sections")
    posts = relationship("ForumPost", back_populates="section", cascade="all, delete-orphan")



class ForumPost(Base):
    __tablename__ = "forum_posts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    team_id = Column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(String, ForeignKey("forum_sections.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=china_now)
    updated_at = Column(DateTime, default=china_now, onupdate=china_now)
    
    # 关联
    team = relationship("Team") # 如果 Team 不需要反向查 Post，这里可以不加 back_populates
    section = relationship("ForumSection", back_populates="posts")
    author = relationship("User")
    
    # 级联删除
    likes = relationship("ForumPostLike", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("ForumComment", back_populates="post", cascade="all, delete-orphan")

class ForumPostLike(Base):
    __tablename__ = "forum_post_likes"
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    post_id = Column(String, ForeignKey('forum_posts.id', ondelete="CASCADE"), primary_key=True)
    
    post = relationship("ForumPost", back_populates="likes")
    user = relationship("User")

class ForumComment(Base):
    __tablename__ = "forum_comments"
    id = Column(String, primary_key=True, default=generate_uuid)
    post_id = Column(String, ForeignKey('forum_posts.id', ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=china_now)
    
    post = relationship("ForumPost", back_populates="comments")
    user = relationship("User")

if __name__ == "__main__":
    print(generate_uuid())