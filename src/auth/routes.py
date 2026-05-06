from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from .schemas import (
    UserCreateModel, 
    UserLoginModel, 
    UserBookModel, 
    EmailModel, 
    PwdResetRequestModel, 
    PwdResetConfirmModel
)
from .service import UserService
from .utils import (
    create_access_token, 
    verify_pwd, 
    create_url_safe_token, 
    decode_url_safe_token,
    generate_pwd_hash
)
from src.celery_tasks import send_email
from src.db.main import get_session
from src.db.redis import add_jti_to_blacklist
from src.errors import (
    UserAlreadyExists, 
    InvalidCredentials, 
    InvalidToken, 
    UserNotFound
)
from datetime import timedelta, datetime
from .dependencies import (
    RefreshTokenBear, 
    AccessTokenBear, 
    get_current_user, 
    RoleChecker
)
from src.config import Config

auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(["admin", "user"])

REFRESH_TOKEN_EXPIRY = 2

@auth_router.post("/send_mail")
async def send_mail(emails: EmailModel):
    emails = emails.addresses
    html = "<h1>欢迎光临</h1>"
    subject="欢迎"

    send_email.delay(emails, subject, html)
    
    return JSONResponse(content={"message": "邮件成功发送!"})


@auth_router.get("/verify/{token}")
async def verify_user_account(token: str, session: AsyncSession = Depends(get_session)):
    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")
    if user_email:
        user = await user_service.get_user_by_email(user_email, session)
        if not user:
            raise UserNotFound
        await user_service.update_user(user, {"is_verified": True}, session)
        return JSONResponse(
            content={
                "msg": "邮箱已经成功激活!"
            },
            status_code=status.HTTP_202_ACCEPTED
        )
    return JSONResponse(
        content={"msg": "验证过程中发生了错误..."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@auth_router.post("/sign_up", status_code=status.HTTP_201_CREATED)
async def create_user_account(
    user_data: UserCreateModel,
    bg_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    email = user_data.email
    user_exists = await user_service.user_exists(email, session)
    if user_exists:
        raise UserAlreadyExists()
    new_user = await user_service.create_user(user_data, session)

    token = create_url_safe_token({"email": email})
    link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"
    html = f"""
    <h1>邮箱验证</h1>
    <p>请点击该链接<a href="{link}">验证链接</a>完成邮箱验证</p>
    """
    emails = [email]
    subject="验证你的邮箱"

    send_email.delay(emails, subject, html)

    return {
        "msg": "邮箱激活链接已发送! 请检查您的账户!",
        "user": new_user
    }


@auth_router.post("/login")
async def login_users(login_data: UserLoginModel, session: AsyncSession = Depends(get_session)):
    email = login_data.email
    pwd = login_data.password

    user = await user_service.get_user_by_email(email, session)
    if user is not None:
        pwd_valid = verify_pwd(pwd, user.password_hash)
        if pwd_valid:
            access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid),
                    "role": user.role
                }
            )

            refresh_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid),
                    "role": user.role
                },
                refresh=True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
            )
            return JSONResponse(
                content={
                    "msg": "登录成功！",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "email": user.email,
                        "uid": str(user.uid),
                        "role": user.role
                    }
                }
            )
    raise InvalidCredentials()


@auth_router.get("/refresh_token")
async def get_new_access_token(token_detail:dict = Depends(RefreshTokenBear())):
    expiry_timestamp = token_detail["exp"]
    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(
            user_data=token_detail["user"]
        )
        return JSONResponse(
            content={
                "access_token": new_access_token
            }
        )
    raise InvalidToken()


@auth_router.get("/me", response_model=UserBookModel)
async def get_current_user(
    user = Depends(get_current_user),
    _: bool = Depends(role_checker)
):
    return user


@auth_router.get("/logout")
async def revoke_token(token_detail:dict = Depends(AccessTokenBear())):
    jti = token_detail["jti"]
    await add_jti_to_blacklist(jti)
    return JSONResponse(
        content={
            "msg": "成功退出登录!"
        },
        status_code=status.HTTP_200_OK
    )


@auth_router.post("/pwd-reset-request")
async def pwd_reset_request(email_data: PwdResetRequestModel):
    email = email_data.email
    token = create_url_safe_token({"email": email})
    link = f"http://{Config.DOMAIN}/api/v1/auth/pwd-reset-confirm/{token}"
    html = f"""
    <h1>重置密码</h1>
    <p>请点击该链接<a href="{link}">重置密码链接</a>完成密码重置</p>
    """
    emails = [email]
    subject = "重置你的密码"

    send_email.delay(emails, subject, html)

    return JSONResponse(
        content={
            "msg": "重置密码链接已发送! 请检查您的账户!"
        },
        status_code=status.HTTP_200_OK
    )


@auth_router.post("/pwd-reset-confirm/{token}")
async def reset_account_pwd(token: str, pwds: PwdResetConfirmModel, session: AsyncSession = Depends(get_session)):
    if pwds.new_pwd != pwds.re_new_pwd:
        raise HTTPException(detail="密码不匹配", status_code=status.HTTP_400_BAD_REQUEST)
    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")
    if user_email:
        user = await user_service.get_user_by_email(user_email, session)
        if not user:
            raise UserNotFound
        password_hash = generate_pwd_hash(pwds.new_pwd)
        await user_service.update_user(user, {"password_hash": password_hash}, session)
        return JSONResponse(
            content={
                "msg": "邮箱已经成功重置!"
            },
            status_code=status.HTTP_202_ACCEPTED
        )
    return JSONResponse(
        content={"msg": "密码重置过程中发生了错误..."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
