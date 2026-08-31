import uuid 
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Table, DateTime, Integer, Float, Text
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

# 多對多關聯表：連接 User 和 Team
team_members_table = Table('team_members', Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('team_id', String, ForeignKey('teams.id'), primary_key=True))

class User(Base):
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
    highlights = relationship("Highlight", back_populates="user") #
    flow_sessions = relationship("FlowSession", back_populates="user", cascade="all, delete-orphan")

class Team(Base):
    __tablename__ = "teams"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True, nullable=False)
    owner_id = Column(String, ForeignKey("users.id"))
    owner = relationship("User")
    members = relationship("User", secondary=team_members_table, back_populates="teams")
    
    # --- 新增以下關聯和 cascade 設定 ---
    invitations = relationship("Invitation", backref="team", cascade="all, delete-orphan")
    checkins = relationship("Checkin", backref="team", cascade="all, delete-orphan")
    flow_sessions = relationship("FlowSession", backref="team", cascade="all, delete-orphan")
    highlights = relationship("Highlight", backref="team", cascade="all, delete-orphan")
    kudos = relationship("Kudos", backref="team", foreign_keys='[Kudos.team_id]', cascade="all, delete-orphan")
    charter = relationship("Charter", back_populates="team", uselist=False, cascade="all, delete-orphan")

class Invitation(Base):
    __tablename__ = 'invitations'
    id = Column(String, primary_key=True, default=generate_uuid)
    team_id = Column(String, ForeignKey('teams.id'), nullable=False)
    inviter_id = Column(String, ForeignKey('users.id'), nullable=False)
    invitee_email = Column(String, nullable=False)
    invite_code = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

class Checkin(Base):
    __tablename__ = 'checkins'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    team_id = Column(String, ForeignKey('teams.id'), nullable=False)
    challenge_level = Column(Float, nullable=False)
    skill_level = Column(Float, nullable=False)
    achievement_text = Column(Text)
    obstacle_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class FlowSession(Base):
    __tablename__ = 'flow_sessions'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    team_id = Column(String, ForeignKey('teams.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    task_description = Column(String)
    user = relationship("User", back_populates="flow_sessions")

class Highlight(Base):
    __tablename__ = 'highlights'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    team_id = Column(String, ForeignKey('teams.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="highlights") #
    likes = relationship("Like", back_populates="highlight", cascade="all, delete-orphan")

class Like(Base):
    __tablename__ = 'likes'
    user_id = Column(String, ForeignKey('users.id'), primary_key=True)
    highlight_id = Column(String, ForeignKey('highlights.id'), primary_key=True)
    user = relationship("User")
    highlight = relationship("Highlight", back_populates="likes")

class Kudos(Base):
    __tablename__ = 'kudos'
    id = Column(String, primary_key=True, default=generate_uuid)
    sender_id = Column(String, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(String, ForeignKey('users.id'), nullable=False)
    team_id = Column(String, ForeignKey('teams.id'), nullable=False)
    card_type = Column(String, nullable=False)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

class Charter(Base):
    __tablename__ = 'charters'
    team_id = Column(String, ForeignKey('teams.id'), primary_key=True)
    content = Column(Text, default="")
    last_updated_by_id = Column(String, ForeignKey('users.id'))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    team = relationship("Team", back_populates="charter")
    last_updated_by = relationship("User")
    
class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=generate_uuid)
    sender_id = Column(String, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(String, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    kind = Column(String, nullable=False)  # 可選欄位，用於區分消息類型
    
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


if __name__ == "__main__":
    print(generate_uuid())