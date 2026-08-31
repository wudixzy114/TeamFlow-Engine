from fastapi import Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from uuid import UUID
from . import crud, models, schemas
from .config import settings
from .database import SessionLocal
from fastapi import Header
import logging  
import redis


logger = logging.getLogger(__name__)

# --- 1. 建立一個可重複使用的 Redis 客戶端 ---
#    這個客戶端在應用程式啟動時只會被建立一次。
#    它會自動管理連線池，非常高效。
#    我們從環境變數讀取配置，而不是寫死 'localhost'。
redis_client = redis.Redis(
    host=settings.REDIS_HOST, # 假設您在 config.py 中設定了 REDIS_HOST
    port=settings.REDIS_PORT, # 假設您在 config.py 中設定了 REDIS_PORT
    db=0,
    decode_responses=True # 讓回傳的結果是 string 而非 bytes
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 2. 建立一個 Redis 的依賴注入函式 ---
def get_redis() -> redis.Redis:
    """Dependency to provide the Redis client instance."""
    return redis_client

# --- 3. 優化您的 token 驗證函式 ---
def verify_token_and_get_user(
    token: str, 
    db: Session, 
    redis: redis.Redis # <-- 接收注入的 redis 客戶端，而不是自己建立
) -> models.User:
    """
    驗證 JWT Token (包含黑名單檢查) 並從資料庫中獲取用戶。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 使用注入進來的 redis 客戶端，而不是每次都新建連線
    if redis.exists(f"blacklist:{token}"):
        logger.info(f"Attempted to use a blacklisted token.")
        raise credentials_exception

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        token_type: str | None = payload.get("type")
        if token_type != "access":
            raise credentials_exception
        
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError as e:
        logger.info(f"JWT validation failed: {e}")
        raise credentials_exception from e

    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception

    return user

# --- 4. 升級 get_current_user 來提供 Redis 依賴 ---
def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
    redis: redis.Redis = Depends(get_redis) # <-- 在這裡注入 Redis
) -> models.User:
    """
    從 Authorization Header 中提取並驗證 token，返回當前用戶。
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing"
        )

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Must be 'Bearer <token>'"
        )

    token = parts[1]
    
    # 將 db 和 redis 依賴傳遞給核心驗證函式
    user = verify_token_and_get_user(token=token, db=db, redis=redis)
    
    return user

def get_team_and_verify_membership(
    team_id: str = Path(..., title="The UUID of the team"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> models.Team:
    team = crud.get_team_for_user(db=db, team_id=team_id, user=current_user)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found or permission denied")
    return team

def get_highlight_and_verify_access(
    highlight_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Highlight:
    """
    一個依賴項，功能如下：
    1. 根據 highlight_id 獲取高光時刻。
    2. 如果找不到，拋出 404 錯誤。
    3. 驗證當前用戶是否屬於該高光時刻所在的團隊。
    4. 如果不屬於，拋出 403 錯誤。
    5. 如果一切正常，返回 highlight 物件。
    """
    highlight = crud.get_highlight(db, highlight_id=highlight_id)
    if not highlight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Highlight not found"
        )

    # 驗證用戶是否是該團隊的成員
    # any() 函數會在找到第一個 True 後立即停止，效率較高
    if not any(team.id == highlight.team_id for team in current_user.teams):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission for this highlight",
        )
    return highlight
