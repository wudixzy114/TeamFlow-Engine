import re
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..core import crud, schemas, security, models
from fastapi import BackgroundTasks 
from ..core.dependencies import get_db, get_current_user,get_redis
from starlette.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.config import settings
from ..core.models import User 
from jose import JWTError, jwt
import logging, time
import resend  
import asyncio
import random  
import string
from fastapi.responses import ORJSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"],default_response_class=ORJSONResponse) #json格式加速
USERNAME_REGEX = re.compile(r'[A-Za-z0-9]{5,}')
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$')

if settings.RESEND_API_KEY and settings.RESEND_API_KEY != "your_key_here":
         resend.api_key = settings.RESEND_API_KEY
else:
    logger.error("RESEND_API_KEY not found or is a placeholder in settings. Email functionality will be disabled.")
    resend.api_key = None 
    
def send_email_sync(params):
    try:
        resend.Emails.send(params)
        logger.info(f"Email sent to {params.get('to')}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

@router.post("/register/", status_code=status.HTTP_201_CREATED) #這個的意思是如果建立成功就回傳201
async def register_user(user: schemas.UserCreate,background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db),redis: redis.Redis = Depends(get_redis)):  #帳號需要>=5個字 且只能由數字跟大小寫字母組成，密碼長度大於等於8,且至少包含一個數字，一個大寫字母，一個小寫字母
    if not USERNAME_REGEX.fullmatch(user.username):
        raise HTTPException(
            status_code=400,
            detail="Username must be at least 5 characters and contain only letters or digits."
        )

    if not PASSWORD_REGEX.fullmatch(user.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long, with at least one uppercase letter, one lowercase letter, and one digit."
        )
    
    #check_email_task = crud.get_user_by_email(db, email=user.email)
    #check_username_task = crud.user_exist(db, username=user.username)
    
    db_user = await crud.get_user_by_email(db, email=user.email)
    user_exist = await crud.user_exist(db, username=user.username)

    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_exist:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # --- 注册邮件发送速率限制 (每分钟一次) ---
    rate_limit_key = f"rate_limit:register:{user.email}"
    # 這裡必須要讀取，無法 pipeline
    if await redis.exists(rate_limit_key):
        ttl = await redis.ttl(rate_limit_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"請在 {ttl} 秒後重試。"
        )

    verification_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    hash_password = await run_in_threadpool(security.get_password_hash, user.password)
    user_info_key = f"unverified_user:{user.email}"
    code_key = f"verification_code:{user.email}"
    
    # --- 核心優化：Pipeline ---
    async with redis.pipeline(transaction=True) as pipe:
        pipe.setex(rate_limit_key, 60, "locked")
        pipe.hset(user_info_key, mapping={
            "username": user.username,
            "hash_password": hash_password,
            "gender": "",
            "nickname": "",
            "age": "",
            "profession": ""
        })
        
        pipe.expire(user_info_key, 600)
        pipe.setex(code_key, 600, verification_code)
        await pipe.execute()

    # 发送验证邮件
    if resend.api_key:
        params = {
            "from": "Teamflow <no-reply@xiangxi.me>",
            "to": [user.email],
            "subject": "欢迎加入 Teamflow！请验证您的邮箱",
            "html": f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, 'Noto Sans', 'Helvetica Neue', sans-serif; background:#f7f7f8; padding:24px;">
                <div style="max-width:640px; margin:0 auto; background:#ffffff; border-radius:12px; box-shadow:0 2px 10px rgba(0,0,0,0.06); overflow:hidden;">
                    <div style="padding:24px 24px 8px;">
                        <h2 style="margin:0 0 8px; font-size:22px; color:#111827;">欢迎您，{user.username}！</h2>
                        <p style="margin:0; color:#4b5563; font-size:14px;">感谢注册 Teamflow。为完成注册，请验证您的邮箱。</p>
                    </div>

                    <div style="padding:8px 24px 0;">
                        <p style="margin:0 0 12px; color:#374151; font-size:14px;">您的一次性验证码：</p>
                        <div style="display:inline-block; padding:12px 16px; border:1px dashed #c7d2fe; background:#f5f7ff; border-radius:8px;">
                            <span style="font-size:20px; font-weight:700; letter-spacing:2px; color:#1f2937;">{verification_code}</span>
                        </div>
                        <p style="margin:12px 0 0; color:#6b7280; font-size:13px;">验证码有效期 <strong>10 分钟</strong>。请在应用内输入以上验证码完成邮箱验证。</p>
                    </div>

                    <div style="padding:16px 24px 0;">
                        <h3 style="margin:0 0 8px; font-size:16px; color:#111827;">提示</h3>
                        <ul style="margin:0; padding-left:18px; color:#4b5563; font-size:13px; line-height:1.6;">
                            <li>如果这不是您本人的操作，请忽略此邮件。</li>
                            <li>若未收到或验证码过期，可在 60 秒后重新发送。</li>
                            <li>请勿将验证码泄露给他人。</li>
                        </ul>
                    </div>
                </div>
            </div>
            """
        }
        # 將任務加入背景佇列
        background_tasks.add_task(send_email_sync, params)

    return {"message": "Verification code sent. Please check your email to activate your account."}

# --- 注册邮箱验证 ---
@router.post("/verify-email/", status_code=status.HTTP_201_CREATED)
async def verify_email(
    request: schemas.EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
):
    # 验证 Redis 中的验证码
    redis_code_key = f"verification_code:{request.email}"
    stored_code = await redis.get(redis_code_key)
    if not stored_code or stored_code != request.code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    
    # 从 Redis 获取暂存的用户信息
    user_info_key = f"unverified_user:{request.email}"
    user_info = await redis.hgetall(user_info_key)
    if not user_info:
        raise HTTPException(status_code=400, detail="Verification expired. Please register again.")
    # 在数据库中创建用户
    try:
        new_user = await crud.create_user(db=db,username=user_info["username"], email=request.email, hashed_password=user_info["hash_password"], gender=user_info["gender"], nickname=user_info["nickname"], age=user_info["age"], profession=user_info["profession"])
        if not new_user:
            raise HTTPException(status_code=400, detail="Failed to create user.")
        
    except Exception:
        raise HTTPException(status_code=409, detail="User with this email or username might already exist.")

    async with redis.pipeline() as pipe:
        pipe.delete(redis_code_key)
        pipe.delete(user_info_key)
        await pipe.execute()
    
    return {"message": "Successfully registered."}  #回傳註冊成功的信息

@router.post("/login/", response_model=schemas.TokenPair)
async def login_for_access_token(credentials: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email_or_username(db, email_or_username=credentials.email)
    password_valid = False
    if user:
        password_valid = await run_in_threadpool(
            security.verify_password, 
            credentials.password, 
            user.hashed_password
        )

    if not user or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password", 
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. 簽發 Token (CPU 計算量小，直接跑即可)
    jwt_payload = {"sub": str(user.id)}
    access_token = await run_in_threadpool(security.create_access_token, data=jwt_payload)
    refresh_token = await run_in_threadpool(security.create_refresh_token, data=jwt_payload)

    return {
        "access": access_token,
        "refresh": refresh_token
    }

@router.post("/logout/", status_code=status.HTTP_200_OK)  #需要把access和refresh token都加入黑名單
async def logout_user(
    token_data: schemas.TokenPair,
    redis: redis.Redis = Depends(get_redis)  # 依赖注入Redis客户端
):
    """
    將當前用戶的 access token 加入黑名單以實現登出。
    该函数通过将access token加入Redis黑名单来实现用户登出功能，
    确保token在过期前无法再次使用。
    refresh token同樣也加進去
    """
    try:
        token_access = token_data.access
        token_refresh = token_data.refresh
        # 使用SECRET_KEY和ALGORITHM解码token
        payload_access = jwt.decode(
            token_access,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        payload_refresh = jwt.decode(
            token_refresh,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        # 获取token的过期时间戳
        exp_timestamp_access = payload_access.get("exp")
        exp_timestamp_refresh = payload_refresh.get("exp")
        
        # 检查token类型是否为access token
        accesstoken_type: str | None = payload_access.get("type")
        refreshtoken_type: str | None = payload_refresh.get("type")
        if accesstoken_type != "access" or refreshtoken_type != "refresh":
            logger.warning("Token provided for logout is not an valid.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type for logout."
            )
        
        # 如果token没有过期时间，直接返回成功消息
        if not exp_timestamp_access or not exp_timestamp_refresh:
            logger.warning("Token provided for logout has no expiration date.")
            return {"message": "Successfully logged out"}

        # 计算token剩余有效期
        current_time = int(time.time())
        ttl_access = exp_timestamp_access - current_time
        ttl_refresh = exp_timestamp_refresh - current_time
        # 如果token尚未过期，将其加入黑名单，设置过期时间为token的剩余有效期
        async with redis.pipeline() as pipe:
            if ttl_access > 0:
                await pipe.setex(f"blacklist:{token_data.access}", ttl_access, "true")
            if ttl_refresh > 0:
                await pipe.setex(f"blacklist:{token_data.refresh}", ttl_refresh, "true")
            await pipe.execute()

    # 处理token解码错误或格式错误
    except (JWTError, IndexError) as e:
        logger.warning(f"Error processing token during logout, but proceeding: {e}")
        pass

    # 返回登出成功消息
    return {"message": "Successfully logged out"}

    
@router.post("/token/refresh/", response_model=schemas.AccessToken)
async def token_refresh(token_data: schemas.TokenRefresh, db: AsyncSession = Depends(get_db),redis: redis.Redis = Depends(get_redis)):
    if await redis.exists(f"blacklist:{token_data.refresh}"):
        logger.info(f"Attempted to use a blacklisted refresh_token.")
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refreshtoken for refreshing."
            )
        
    user_id = await run_in_threadpool(security.verify_refresh_token, token_data.refresh)
    user = await crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
 
    new_access_token = await run_in_threadpool(security.create_access_token, data={"sub": str(user.id)})
    return {"access": new_access_token}

@router.get("/me/", response_model=schemas.User,  tags=["Auth"])
async def me_manual_check(
    current_user: models.User = Depends(get_current_user)
): 
    return current_user


@router.post("/forgot-password/", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
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

    remaining_ttl = await redis.ttl(rate_limit_key)
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

    user = await crud.get_user_by_email(db, email=request.email)
    
    if user:
        # 设置冷却时间
        await redis.setex(rate_limit_key, cooldown_period, "locked")
        # 生成6位验证码
        reset_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        # 将验证码存储到 Redis，键为 "reset_code:邮箱地址"，有效期为 10 分钟 
        await redis.setex(f"reset_code:{request.email}", 600, reset_code)
        
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
            # email_response = resend.Emails.send(params)
            #email_response = await run_in_threadpool(resend.Emails.send, params)
            background_tasks.add_task(send_email_sync, params)
            # logger.info(f"Password reset email sent to {request.email}. Resend ID: {email_response['id']}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {request.email}: {e}")
        
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User not found.") 

    return {"message": "If an account with that email exists, a password reset code has been sent."}


@router.post("/reset-password/", status_code=status.HTTP_200_OK)
async def reset_password(
    request: schemas.ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
):
    """
    使用邮箱、验证码和新密码来重置密码。
    """
    stored_code = await redis.get(f"reset_code:{request.email}")
    
    # 验证验证码是否正确或已过期
    if not stored_code or stored_code != request.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code."
        )
        
    # 验证新密码格式，与注册时保持一致
    if not PASSWORD_REGEX.fullmatch(request.new_password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long, with at least one uppercase letter, one lowercase letter, and one digit."
        )
        
    # 获取用户
    user = await crud.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
        
    # 对新密码进行哈希处理，并更新到数据库
    hashed_password = await run_in_threadpool(security.get_password_hash, request.new_password)
    response = await crud.update_user_password(db=db, user=user, new_password_hash=hashed_password)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update password."
        )
    
    # 密码重置成功后，立即删除已使用的验证码，防止重复使用
    await redis.delete(f"reset_code:{request.email}")
    
    return {"message": "Password has been reset successfully."}

@router.put("/modify_selfinfo/", status_code=status.HTTP_200_OK)
async def modify_selfinfo(
    modify: schemas.modifyUserInfo,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
):
    """
    修改用户个人信息。
    """
    # 更新用户信息
    if modify.username is not None and modify.username != "" and not USERNAME_REGEX.fullmatch(modify.username):
        raise HTTPException(
            status_code=400,
            detail="Username must be at least 5 characters and contain only letters or digits."
        )
        
    if modify.username is not None and modify.username != current_user.username:
        user_exist = await crud.user_exist(db, username=modify.username)
        if user_exist:
            raise HTTPException(status_code=400, detail="Username already registered")

    if modify.username is None or modify.username == "":
        modify.username = current_user.username
    
    user = await crud.update_user_info(db=db, user_id=current_user.id, nickname=modify.nickname, age=modify.age, profession=modify.profession, gender=modify.gender, username=modify.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    await redis.delete(f"user_cache:{current_user.id}")
    return {"message": "User information has been updated successfully."}

@router.put("/reset-email/", status_code=status.HTTP_200_OK, tags=["User"])
async def request_email_change(
    request: schemas.ResetEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
):
    """
    请求修改邮箱地址。
    将向新邮箱发送一个6位数的验证码。
    """
    new_email = request.new_email
    # 检查新邮箱是否已被其他用户注册
    if await crud.get_user_by_email(db, email=new_email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email address is already registered."
        )

    # 速率限制：防止用户频繁请求更换邮箱
    rate_limit_key = f"rate_limit:email_reset:{current_user.id}"
    if await redis.exists(rate_limit_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have requested to change your email too frequently. Please try again later."
        )

    # 生成验证码
    verification_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    # 将新邮箱和验证码暂存到 Redis，有效期10分钟
    redis_key = f"email_reset:{current_user.id}"
    await redis.hset(redis_key, mapping={"new_email": new_email, "code": verification_code})
    await redis.expire(redis_key, 600)
    
    # 设置速率限制，1分钟冷却
    await redis.setex(rate_limit_key, 60, "locked")

    # 发送验证邮件
    if resend.api_key:
        try:
            params = {
                "from": "Teamflow <no-reply@xiangxi.me>",
                "to": [new_email],
                "subject": "【Teamflow】请验证您的新邮箱地址",
                "html": f"<h2>验证您的新邮箱</h2><p>您的验证码是：<b>{verification_code}</b></p><p>该验证码将在10分钟后失效。</p>"
            }
            # resend.Emails.send(params)
            # await run_in_threadpool(resend.Emails.send, params)
            background_tasks.add_task(send_email_sync, params)
        except Exception as e:
            logger.error(f"Failed to send email change verification to {new_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to send verification email.")
    
    return {"message": "Verification code sent to new email address."}


@router.put("/verify-email-reset/", status_code=status.HTTP_200_OK, tags=["User"])
async def verify_email_change(
    request: schemas.VerifyEmailResetRequest,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
):
    """
    使用验证码完成邮箱地址的修改。
    """
    redis_key = f"email_reset:{current_user.id}"
    stored_data = await redis.hgetall(redis_key)
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
    updated_user = await crud.update_user_email(db, user_id=current_user.id, new_email=new_email)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update email address."
        )

    # 清理 Redis
    await redis.delete(redis_key)
    await redis.delete(f"user_cache:{current_user.id}")

    return {"message": "Your email address has been updated successfully."}
