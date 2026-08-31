from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings
from fastapi import HTTPException, status
from uuid import UUID

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    to_encode.update({"type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=1) 
    to_encode.update({"exp": expire})
    to_encode.update({"type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_refresh_token(token: str) -> str:
    """
    驗證一個 Refresh Token。
    如果 token 合法且未過期，返回其中包含的用戶 UUID。
    如果 token 無效（過期、簽名錯誤等），則拋出 HTTPException。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        token_type: str | None = payload.get("type")
        if token_type != "refresh":
            raise credentials_exception
        
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None :
            raise credentials_exception
            
        user_id = user_id_str
        
    except (JWTError, ValueError):
        # JWTError: token 過期、簽名錯誤、格式錯誤
        # ValueError: payload 中的 'sub' 不是一個合法的 UUID 字串
        raise credentials_exception
        
    return user_id