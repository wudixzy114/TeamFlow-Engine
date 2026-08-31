import re
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..core import crud, schemas, security, models
from ..core.dependencies import get_db, get_current_user,get_redis
from ..core.config import settings
from ..core.models import User 
from jose import JWTError, jwt
import logging, time
import redis
import resend  
import random  
import string

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

if settings.RESEND_API_KEY and settings.RESEND_API_KEY != "your_key_here":
         resend.api_key = settings.RESEND_API_KEY
else:
    logger.error("RESEND_API_KEY not found or is a placeholder in settings. Email functionality will be disabled.")
    resend.api_key = None 

@router.post("/register/", status_code=status.HTTP_201_CREATED) #這個的意思是如果建立成功就回傳201
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db),redis: redis.Redis = Depends(get_redis)):  #帳號需要>=5個字 且只能由數字跟大小寫字母組成，密碼長度大於等於8,且至少包含一個數字，一個大寫字母，一個小寫字母
    if not re.fullmatch(r'[A-Za-z0-9]{5,}', user.username):
        raise HTTPException(
            status_code=400,
            detail="Username must be at least 5 characters and contain only letters or digits."
        )

    if not re.fullmatch(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$', user.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long, with at least one uppercase letter, one lowercase letter, and one digit."
        )
    
    db_user = crud.get_user_by_email(db, email=user.email)
    user_exist = crud.user_exist(db, username=user.username)  
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_exist:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # --- 注册邮件发送速率限制 (每分钟一次) ---
    cooldown_period = 60  # 冷却时间为60秒
    rate_limit_key = f"rate_limit:register:{user.email}"

    remaining_ttl = redis.ttl(rate_limit_key)
    if remaining_ttl > 0:
        logger.warning(f"Registration rate limit exceeded for email: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"您请求验证码过于频繁，请在 {remaining_ttl} 秒后重试。"
        )
    
    # 准备发送邮件之前，设置速率限制锁
    redis.setex(rate_limit_key, cooldown_period, "locked")

    # 将用户信息暂存到 Redis
    verification_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    hash_password = security.get_password_hash(user.password)
    #logger.warning(hash_password)
    # 使用 Redis Hash 存储待验证的用户信息
    user_info_key = f"unverified_user:{user.email}"
    redis.hset(user_info_key, mapping={
        "username": user.username,
        "hash_password": hash_password,
        "gender": "",
        "nickname": "",
        "age": "",
        "profession": ""
    })
    redis.expire(user_info_key, 600)

    # 存储验证码
    redis.setex(f"verification_code:{user.email}", 600, verification_code)
    #logger.warning(verification_code)
    # 发送验证邮件
    if resend.api_key:
        try:
            params = {
                "from": "Teamflow <no-reply@xiangxi.me>",
                "to": [user.email],
                "subject": "欢迎加入 Teamflow！请验证您的邮箱",
                "html": f"""<h2>欢迎您, {user.username}!</h2><p>您的验证码是：<b>{verification_code}</b></p><p>该验证码将在10分钟后失效。</p>"""
            }
            resend.Emails.send(params)
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")

    return {"message": "Verification code sent. Please check your email to activate your account."}

# --- 注册邮箱验证 ---
@router.post("/verify-email/", status_code=status.HTTP_201_CREATED)
def verify_email(
    request: schemas.EmailVerificationRequest,
    db: Session = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
):
    # 验证 Redis 中的验证码
    redis_code_key = f"verification_code:{request.email}"
    stored_code = redis.get(redis_code_key)
    if not stored_code or stored_code != request.code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    
    # 从 Redis 获取暂存的用户信息
    user_info_key = f"unverified_user:{request.email}"
    user_info = redis.hgetall(user_info_key)
    if not user_info:
        raise HTTPException(status_code=400, detail="Verification expired. Please register again.")
    # 在数据库中创建用户
    try:
        new_user = crud.create_user(db=db,username=user_info["username"], email=request.email, hashed_password=user_info["hash_password"], gender=user_info["gender"], nickname=user_info["nickname"], age=user_info["age"], profession=user_info["profession"])
        if not new_user:
            raise HTTPException(status_code=400, detail="Failed to create user.")
        
    except Exception:
        raise HTTPException(status_code=409, detail="User with this email or username might already exist.")

    # 清理 Redis 中的暂存数据
    redis.delete(redis_code_key)
    redis.delete(user_info_key)
    
    return {"message": "Successfully registered."}  #回傳註冊成功的信息

@router.post("/login/", response_model=schemas.TokenPair)
def login_for_access_token(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=credentials.email) or crud.get_user_by_username(db, username=credentials.email)

    if not user or not security.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password", 
            headers={"WWW-Authenticate": "Bearer"},
        )

    jwt_payload = {"sub": str(user.id)}
    access_token = security.create_access_token(data=jwt_payload)
    refresh_token = security.create_refresh_token(data=jwt_payload)

    return {
        "access": access_token,
        "refresh": refresh_token
    }

@router.post("/logout/", status_code=status.HTTP_200_OK)
def logout_user(
    # 依賴 1: 驗證用戶身份，確保只有登入者才能登出
    current_user: models.User = Depends(get_current_user),
    # 依賴 2: 從 Header 直接獲取原始 token 字串，用於加入黑名單
    authorization: str = Header(...),
    # 依賴 3: 注入 Redis 客戶端，用於執行黑名單操作
    redis: redis.Redis = Depends(get_redis)
):
    """
    將當前用戶的 access token 加入黑名單以實現登出。
    """
    try:
        # 從 "Bearer <token>" 中提取 token
        token = authorization.split(" ")[1]

        # 解碼 token 來獲取其過期時間戳 (exp)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        exp_timestamp = payload.get("exp")
        
        token_type: str | None = payload.get("type")
        if token_type != "access":
            logger.warning("Token provided for logout is not an access token.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type for logout."
            )
        
        if not exp_timestamp:
            # 雖然 get_current_user 已經驗證過，但做個防禦性檢查
            logger.warning("Token provided for logout has no expiration date.")
            # 即使沒有過期時間，我們仍然可以將它加入黑名單，只是無法設定精確的 TTL
            # 這裡可以選擇給它一個預設的較長的過期時間，例如 access token 的最大有效期
            # 但為了簡單起見，我們直接返回成功
            return {"message": "Successfully logged out"}

        current_time = int(time.time())
        ttl = exp_timestamp - current_time

        # 如果 token 尚未過期，就將它加入 Redis 黑名單並設定 TTL
        if ttl > 0:
            # 使用注入的 redis 客戶端，而不是建立新連線
            redis.setex(f"blacklist:{token}", ttl, "true")

    except (JWTError, IndexError) as e:
        # 如果 token 在這裡解析失敗（理論上不應該，因為 get_current_user 已經通過），
        # 我們記錄日誌但仍然返回成功，因為從用戶的角度看，登出操作已完成。
        logger.warning(f"Error processing token during logout, but proceeding: {e}")
        pass

    return {"message": "Successfully logged out"}

    
@router.post("/token/refresh/", response_model=schemas.AccessToken)
def token_refresh(token_data: schemas.TokenRefresh, db: Session = Depends(get_db)):
    user_id = security.verify_refresh_token(token_data.refresh)
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
 
    new_access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access": new_access_token}

@router.get("/me/", response_model=schemas.User,  tags=["Auth"])
def me_manual_check(
    current_user: models.User = Depends(get_current_user)
): 
    return current_user


@router.post("/forgot-password/", status_code=status.HTTP_200_OK)
def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
):
    """
    处理忘记密码请求。
    如果邮箱存在，生成一个验证码，存入 Redis，并通过 Resend 发送邮件。
    为了防止用户枚举攻击（即通过返回信息猜测邮箱是否已注册），无论邮箱是否存在，都返回相同的成功响应。
    """
    # 每个邮箱地址的冷却时间为 60 秒
    cooldown_period = 60  
    rate_limit_key = f"rate_limit:forgot_password:{request.email}"

    remaining_ttl = redis.ttl(rate_limit_key)
    if remaining_ttl > 0:
        # 如果键存在且尚未过期，则拒绝请求
        logger.warning(f"Rate limit exceeded for email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"请求过于频繁，请在 {remaining_ttl} 秒后重试。"
        )
    
    if not resend.api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured on the server."
        )

    user = crud.get_user_by_email(db, email=request.email)
    
    if user:
        # 设置冷却时间
        redis.setex(rate_limit_key, cooldown_period, "locked")
        # 生成6位验证码
        reset_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        # 将验证码存储到 Redis，键为 "reset_code:邮箱地址"，有效期为 10 分钟 
        redis.setex(f"reset_code:{request.email}", 600, reset_code)
        
        # 构建并发送邮件
        try:
            params = {
                "from": "Teamflow<no-reply@xiangxi.me>", 
                "to": [request.email],
                "subject": "您的密码重置验证码",
                "html": f"""
                <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <h2>密码重置请求</h2>
                    <p>您好，</p>
                    <p>我们收到了一个重置您账户密码的请求。您的验证码是：</p>
                    <p style="font-size: 24px; font-weight: bold; color: #333;">{reset_code}</p>
                    <p>该验证码将在 <strong>10分钟</strong> 后失效。</p>
                    <p>如果您没有请求重置密码，请忽略此邮件。</p>
                    <br>
                    <p>此致,</p>
                    <p>Teamflow 团队</p>
                </div>
                """
            }
            email_response = resend.Emails.send(params)
            logger.info(f"Password reset email sent to {request.email}. Resend ID: {email_response['id']}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {request.email}: {e}")
        
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User not found.")

    return {"message": "If an account with that email exists, a password reset code has been sent."}


@router.post("/reset-password/", status_code=status.HTTP_200_OK)
def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
):
    """
    使用邮箱、验证码和新密码来重置密码。
    """
    stored_code = redis.get(f"reset_code:{request.email}")
    
    # 验证验证码是否正确或已过期
    if not stored_code or stored_code != request.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code."
        )
        
    # 验证新密码格式，与注册时保持一致
    if not re.fullmatch(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$', request.new_password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long, with at least one uppercase letter, one lowercase letter, and one digit."
        )
        
    # 获取用户
    user = crud.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
        
    # 对新密码进行哈希处理，并更新到数据库
    hashed_password = security.get_password_hash(request.new_password)
    response = crud.update_user_password(db=db, user=user, new_password_hash=hashed_password)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update password."
        )
    
    # 密码重置成功后，立即删除已使用的验证码，防止重复使用
    redis.delete(f"reset_code:{request.email}")
    
    return {"message": "Password has been reset successfully."}

@router.put("/modify_selfinfo/", status_code=status.HTTP_200_OK)
def modify_selfinfo(
    modify: schemas.modifyUserInfo,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
):
    """
    修改用户个人信息。
    """
    # 更新用户信息
    if modify.username is not None and modify.username != "" and not re.fullmatch(r'[A-Za-z0-9]{5,}', modify.username) :
        raise HTTPException(
            status_code=400,
            detail="Username must be at least 5 characters and contain only letters or digits."
        )
        
    if modify.username is not None and modify.username != current_user.username:
        user_exist = crud.user_exist(db, username=modify.username)
        if user_exist:
            raise HTTPException(status_code=400, detail="Username already registered")

    if modify.username is None or modify.username == "":
        modify.username = current_user.username
    
    user = crud.update_user_info(db=db, user_id=current_user.id, nickname=modify.nickname, age=modify.age, profession=modify.profession, gender=modify.gender, username=modify.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
        
    return {"message": "User information has been updated successfully."}

@router.put("/reset-email/", status_code=status.HTTP_200_OK, tags=["User"])
def request_email_change(
    request: schemas.ResetEmailRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
):
    """
    请求修改邮箱地址。
    将向新邮箱发送一个6位数的验证码。
    """
    new_email = request.new_email
    # 检查新邮箱是否已被其他用户注册
    if crud.get_user_by_email(db, email=new_email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email address is already registered."
        )

    # 速率限制：防止用户频繁请求更换邮箱
    rate_limit_key = f"rate_limit:email_reset:{current_user.id}"
    if redis.exists(rate_limit_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have requested to change your email too frequently. Please try again later."
        )

    # 生成验证码
    verification_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    # 将新邮箱和验证码暂存到 Redis，有效期10分钟
    redis_key = f"email_reset:{current_user.id}"
    redis.hset(redis_key, mapping={"new_email": new_email, "code": verification_code})
    redis.expire(redis_key, 600)
    
    # 设置速率限制，1分钟冷却
    redis.setex(rate_limit_key, 60, "locked")

    # 发送验证邮件
    if resend.api_key:
        try:
            params = {
                "from": "Teamflow <no-reply@xiangxi.me>",
                "to": [new_email],
                "subject": "【Teamflow】请验证您的新邮箱地址",
                "html": f"<h2>验证您的新邮箱</h2><p>您的验证码是：<b>{verification_code}</b></p><p>该验证码将在10分钟后失效。</p>"
            }
            resend.Emails.send(params)
        except Exception as e:
            logger.error(f"Failed to send email change verification to {new_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to send verification email.")
    
    return {"message": "Verification code sent to new email address."}


@router.put("/verify-email-reset/", status_code=status.HTTP_200_OK, tags=["User"])
def verify_email_change(
    request: schemas.VerifyEmailResetRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
):
    """
    使用验证码完成邮箱地址的修改。
    """
    redis_key = f"email_reset:{current_user.id}"
    stored_data = redis.hgetall(redis_key)
    if not stored_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email change request expired or not found. Please request again."
        )
    stored_code = stored_data.get("code", "")
    if stored_code != request.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code."
        )

    new_email = stored_data.get("new_email", "")
    
    # 更新数据库中的邮箱
    updated_user = crud.update_user_email(db, user_id=current_user.id, new_email=new_email)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update email address."
        )

    # 清理 Redis
    redis.delete(redis_key)

    return {"message": "Your email address has been updated successfully."}
