import asyncio
from fastapi import Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from typing import AsyncGenerator
from jose import JWTError, jwt
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from . import crud, models, schemas
from .config import settings
from .database import AsyncSessionLocal
from fastapi import Header
import logging  
import redis.asyncio as redis
import orjson

logger = logging.getLogger(__name__)

# --- 1. 建立一個可重複使用的 Redis 客戶端 ---
#    這個客戶端在應用程式啟動時只會被建立一次。
#    它會自動管理連線池，非常高效。
#    我們從環境變數讀取配置，而不是寫死 'localhost'。
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True,
    max_connections=1000,   
    socket_timeout=1,       # 縮短超時時間，快速失敗比卡死好
    socket_connect_timeout=1
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# --- 2. 建立一個 Redis 的依賴注入函式 ---
async def get_redis() -> redis.Redis:
    """Dependency to provide the Redis client instance."""
    return redis_client

# --- 3. 優化您的 token 驗證函式 ---
async def verify_token_and_get_user(
    token: str, 
    db: AsyncSession, 
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
    if await redis.exists(f"blacklist:{token}"):
        logger.info(f"Attempted to use a blacklisted token.")
        raise credentials_exception

    try:
        loop = asyncio.get_running_loop()
        payload = await loop.run_in_executor(
            None, 
            lambda: jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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
    
    cache_key = f"user_cache:{user_id}"
    cached_user_data = await redis.get(cache_key)
    
    if cached_user_data:
        try:
            data = orjson.loads(cached_user_data)
            user_temp = models.User(**data) 
            user = await db.merge(user_temp)
            return user
        except Exception as e:
            pass


    user = await crud.get_user_basic(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    
    try:
        user_dto = schemas.User.model_validate(user) 
        user_dict = user_dto.model_dump() 
        await redis.set(
            cache_key, 
            orjson.dumps(user_dict), 
            ex=1200
        )
    except Exception as e:
        logger.error(f"Failed to cache user: {e}")

    return user

# --- 4. 升級 get_current_user 來提供 Redis 依賴 ---
async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
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
    user = await verify_token_and_get_user(token=token, db=db, redis=redis)
    return user

async def get_team_and_verify_membership(
    team_id: str = Path(..., title="The UUID of the team"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> models.Team:
    team = await crud.get_team_for_user(db=db, team_id=team_id, user=current_user)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found or permission denied")
    return team

async def get_highlight_and_verify_access(
    highlight_id: str,
    db: AsyncSession = Depends(get_db),
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
    highlight = await crud.get_highlight(db, highlight_id=highlight_id)
    if not highlight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Highlight not found"
        )

    # 2. 【修正點】改用 SQL 查詢檢查權限，避免 Lazy Loading 報錯
    # 原本的寫法 (會報錯): if not any(team.id == highlight.team_id for team in current_user.teams):
    
    has_permission = await crud.is_user_in_team(
        db, 
        team_id=highlight.team_id,
        user_id=current_user.id
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission for this highlight",
        )
        
    return highlight
